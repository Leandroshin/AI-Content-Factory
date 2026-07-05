"""Company execution flow demo: Orchestrator → Decision Engine → Execution Runtime.

Full pipeline with fake snapshots and a FakeProviderAdapter.
No real HTTP, no API key, no external dependencies.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any
from uuid import UUID, uuid4

from core.decision.runtime import DecisionContextBuilder, DecisionEngine
from core.execution import ExecutionResult
from core.llm import (
    LLMGateway,
    LLMRequest,
    LLMResponse,
    PromptBuilder,
    PromptTemplate,
    ProviderAdapter,
    ProviderRegistry,
)
from core.llm.request_builder import LLMRequestBuilder
from core.orchestrator import OrchestratorExecutionResult
from core.orchestrator.runtime import OrchestratorRuntime


# ------------------------------------------------------------------
# Plain snapshot-like objects
# ------------------------------------------------------------------


@dataclass
class TaskSnapshot:
    task_id: UUID
    name: str
    metadata: object = None


@dataclass
class TaskMetadata:
    tags: list[str] = field(default_factory=list)


@dataclass
class EmployeeSnapshot:
    employee_id: UUID
    name: str
    state: str = "idle"
    role: str = "generic"


@dataclass
class DepartmentSnapshot:
    department_id: UUID
    name: str
    employees: dict[UUID, object] = field(default_factory=dict)


@dataclass
class DepartmentEmployeeLink:
    employee_id: UUID
    state: str = "idle"


@dataclass
class SkillSnapshot:
    skill_id: UUID
    name: str
    employee_ids: set[UUID] = field(default_factory=set)


# ------------------------------------------------------------------
# Fake provider
# ------------------------------------------------------------------


class FakeProviderAdapter(ProviderAdapter):
    def __init__(
        self,
        content: str = "Generated AI content for the task.",
        finish_reason: str = "stop",
        provider_name: str = "fake",
    ) -> None:
        self._content = content
        self._finish_reason = finish_reason
        self._provider_name = provider_name

    def generate(self, request: LLMRequest) -> LLMResponse:
        return LLMResponse(
            request_id=request.request_id,
            provider=self._provider_name,
            model=request.model,
            content=self._content,
            input_tokens=15,
            output_tokens=25,
            total_tokens=40,
            finish_reason=self._finish_reason,
        )


# ------------------------------------------------------------------
# Helpers
# ------------------------------------------------------------------


def _make_orchestrator() -> OrchestratorRuntime:
    """Create a minimal OrchestratorRuntime for test purposes.

    The existing OrchestratorRuntime requires CompanyRuntime and
    DepartmentRuntime via constructor injection. For our demo we
    only need the execute_task method, so we provide minimal stubs.
    """
    from core.events.bus import EventBus
    from core.runtime import CompanyRuntime

    bus = EventBus()
    company = CompanyRuntime(event_bus=bus)
    dept_runtime = _FakeDepartmentRuntime()
    return OrchestratorRuntime(company, dept_runtime, bus)


class _FakeDepartmentRuntime:
    """Minimal stub so OrchestratorRuntime can be instantiated."""

    def department(self, department_id: UUID) -> Any:
        return object()

    def sync_employee_state(self, department_id: UUID, event: Any) -> None:
        pass


def _build_llm_request(prompt_text: str = "Write content about {topic}.") -> LLMRequest:
    template = PromptTemplate.create(
        name="content_gen",
        template=prompt_text,
        required_placeholders=["topic"],
    )
    render = PromptBuilder.render(template, {"topic": "AI in business"})
    return LLMRequestBuilder.build(render, model="gpt-4o", temperature=0.5)


# ------------------------------------------------------------------
# Scenario 1: Full successful flow
# ------------------------------------------------------------------


def scenario_full_successful_flow() -> None:
    """Complete cycle: decide → execute → result with all components."""
    alice_id = uuid4()
    task = TaskSnapshot(task_id=uuid4(), name="Write Article")
    dept = DepartmentSnapshot(
        department_id=uuid4(), name="Content",
        employees={alice_id: DepartmentEmployeeLink(alice_id)},
    )
    alice = EmployeeSnapshot(employee_id=alice_id, name="Alice", state="idle")
    skill = SkillSnapshot(skill_id=uuid4(), name="Writing", employee_ids={alice_id})

    registry = ProviderRegistry()
    registry.register("openai", FakeProviderAdapter(content="Article about AI.", provider_name="openai"))
    gateway = LLMGateway(registry)

    orchestrator = _make_orchestrator()
    result = orchestrator.execute_task(
        task_snapshot=task,
        candidate_snapshots=[alice],
        department_snapshot=dept,
        skill_snapshots=[skill],
        llm_request=_build_llm_request(),
        gateway=gateway,
        gateway_provider="openai",
    )

    assert isinstance(result, OrchestratorExecutionResult)
    assert result.success is True
    assert result.decision_result.approved is True
    assert result.execution_result is not None
    assert result.execution_result.success is True
    assert result.execution_result.output == "Article about AI."
    assert result.execution_result.trace.provider_used == "openai"
    print(f"[PASS] full_successful_flow            | success={result.success} "
          f"chosen={result.decision_result.chosen_candidate_id.hex[:8]} "
          f"output='{result.execution_result.output[:20]}...'")


# ------------------------------------------------------------------
# Scenario 2: No candidates available
# ------------------------------------------------------------------


def scenario_no_candidates() -> None:
    """When no candidates match department/availability, execution is skipped."""
    alice_id = uuid4()
    task = TaskSnapshot(task_id=uuid4(), name="Task without candidates")
    dept = DepartmentSnapshot(
        department_id=uuid4(), name="Engineering",
        employees={alice_id: DepartmentEmployeeLink(alice_id)},
    )
    alice = EmployeeSnapshot(employee_id=alice_id, name="Alice", state="busy")

    orchestrator = _make_orchestrator()
    result = orchestrator.execute_task(
        task_snapshot=task,
        candidate_snapshots=[alice],
        department_snapshot=dept,
    )

    assert result.success is False
    assert result.decision_result.approved is False
    assert result.decision_result.decision_code == "NO_AVAILABLE_CANDIDATE"
    assert result.execution_result is None
    print(f"[PASS] no_candidates                   | success={result.success} "
          f"code={result.decision_result.decision_code}")


# ------------------------------------------------------------------
# Scenario 3: Policy blocks the candidate
# ------------------------------------------------------------------


def scenario_policy_blocks() -> None:
    """Hard constraint blocks the only candidate, execution is skipped."""
    alice_id = uuid4()

    def _block_all(ctx: object) -> tuple[bool, str]:
        return False, "All candidates blocked by global policy"

    from core.policies.runtime import Constraint

    task = TaskSnapshot(task_id=uuid4(), name="Restricted Task")
    dept = DepartmentSnapshot(
        department_id=uuid4(), name="Restricted",
        employees={alice_id: DepartmentEmployeeLink(alice_id)},
    )
    alice = EmployeeSnapshot(employee_id=alice_id, name="Alice", state="idle")

    orchestrator = _make_orchestrator()
    result = orchestrator.execute_task(
        task_snapshot=task,
        candidate_snapshots=[alice],
        department_snapshot=dept,
        policy_constraints=[
            Constraint(constraint_id="global_block", description="Block all", check=_block_all),
        ],
    )

    assert result.success is False
    assert result.decision_result.approved is False
    assert result.decision_result.decision_code == "POLICY_DENIED"
    assert result.execution_result is None
    print(f"[PASS] policy_blocks                   | success={result.success} "
          f"code={result.decision_result.decision_code}")


# ------------------------------------------------------------------
# Scenario 4: Best candidate chosen correctly
# ------------------------------------------------------------------


def scenario_best_candidate_chosen() -> None:
    """Multiple candidates; the one with the best skill match is selected."""
    alice_id = uuid4()
    bob_id = uuid4()
    skill_id = uuid4()

    task = TaskSnapshot(
        task_id=uuid4(), name="Python Review",
        metadata=TaskMetadata(tags=["python"]),
    )
    dept = DepartmentSnapshot(
        department_id=uuid4(), name="Engineering",
        employees={
            alice_id: DepartmentEmployeeLink(alice_id),
            bob_id: DepartmentEmployeeLink(bob_id),
        },
    )
    alice = EmployeeSnapshot(employee_id=alice_id, name="Alice", state="idle")
    bob = EmployeeSnapshot(employee_id=bob_id, name="Bob", state="idle")
    skill = SkillSnapshot(skill_id=skill_id, name="Python Development", employee_ids={alice_id})

    registry = ProviderRegistry()
    registry.register("openai", FakeProviderAdapter(content="Done.", provider_name="openai"))
    gateway = LLMGateway(registry)

    orchestrator = _make_orchestrator()
    result = orchestrator.execute_task(
        task_snapshot=task,
        candidate_snapshots=[alice, bob],
        department_snapshot=dept,
        skill_snapshots=[skill],
        llm_request=_build_llm_request(),
        gateway=gateway,
        gateway_provider="openai",
    )

    assert result.success is True
    assert result.decision_result.chosen_candidate_id == alice_id
    assert result.decision_result.decision_code == "BEST_SKILL_MATCH"
    print(f"[PASS] best_candidate_chosen           | chosen={result.decision_result.chosen_candidate_id.hex[:8]} "
          f"code={result.decision_result.decision_code}")


# ------------------------------------------------------------------
# Scenario 5: No skill match (fallback candidate chosen)
# ------------------------------------------------------------------


def scenario_no_skill_match() -> None:
    """No candidate has the required skill; execution still proceeds."""
    alice_id = uuid4()
    skill_id = uuid4()

    task = TaskSnapshot(
        task_id=uuid4(), name="Rust Code Review",
        metadata=TaskMetadata(tags=["rust"]),
    )
    dept = DepartmentSnapshot(
        department_id=uuid4(), name="Engineering",
        employees={alice_id: DepartmentEmployeeLink(alice_id)},
    )
    alice = EmployeeSnapshot(employee_id=alice_id, name="Alice", state="idle")
    skill = SkillSnapshot(skill_id=skill_id, name="Python Development", employee_ids={alice_id})

    registry = ProviderRegistry()
    registry.register("openai", FakeProviderAdapter(content="Rust review output.", provider_name="openai"))
    gateway = LLMGateway(registry)

    orchestrator = _make_orchestrator()
    result = orchestrator.execute_task(
        task_snapshot=task,
        candidate_snapshots=[alice],
        department_snapshot=dept,
        skill_snapshots=[skill],
        llm_request=_build_llm_request(),
        gateway=gateway,
        gateway_provider="openai",
    )

    assert result.success is True
    assert result.decision_result.decision_code == "NO_SKILL_MATCH"
    assert result.execution_result is not None
    assert result.execution_result.success is True
    print(f"[PASS] no_skill_match                  | code={result.decision_result.decision_code} "
          f"executed={result.execution_result.success}")


# ------------------------------------------------------------------
# Scenario 6: Non-existent provider
# ------------------------------------------------------------------


def scenario_nonexistent_provider() -> None:
    """Execution fails when the gateway has no matching provider."""
    alice_id = uuid4()
    task = TaskSnapshot(task_id=uuid4(), name="Task with bad provider")
    dept = DepartmentSnapshot(
        department_id=uuid4(), name="Engineering",
        employees={alice_id: DepartmentEmployeeLink(alice_id)},
    )
    alice = EmployeeSnapshot(employee_id=alice_id, name="Alice", state="idle")

    registry = ProviderRegistry()
    gateway = LLMGateway(registry)

    orchestrator = _make_orchestrator()
    result = orchestrator.execute_task(
        task_snapshot=task,
        candidate_snapshots=[alice],
        department_snapshot=dept,
        llm_request=_build_llm_request(),
        gateway=gateway,
        gateway_provider="nonexistent",
    )

    assert result.success is False
    assert result.decision_result.approved is True  # decision passed
    assert result.execution_result is not None
    assert result.execution_result.success is False
    print(f"[PASS] nonexistent_provider            | decision_approved={result.decision_result.approved} "
          f"execution_success={result.execution_result.success}")


# ------------------------------------------------------------------
# Scenario 7: Invalid prompt (missing placeholder)
# ------------------------------------------------------------------


def scenario_missing_llm_request() -> None:
    """No LLM request provided — orchestration skips execution after decision."""
    alice_id = uuid4()
    task = TaskSnapshot(task_id=uuid4(), name="Task without LLM request")
    dept = DepartmentSnapshot(
        department_id=uuid4(), name="Engineering",
        employees={alice_id: DepartmentEmployeeLink(alice_id)},
    )
    alice = EmployeeSnapshot(employee_id=alice_id, name="Alice", state="idle")

    registry = ProviderRegistry()
    registry.register("openai", FakeProviderAdapter(provider_name="openai"))
    gateway = LLMGateway(registry)

    orchestrator = _make_orchestrator()
    result = orchestrator.execute_task(
        task_snapshot=task,
        candidate_snapshots=[alice],
        department_snapshot=dept,
        llm_request=None,  # no LLM request
        gateway=gateway,
        gateway_provider="openai",
    )

    assert result.success is False
    assert result.decision_result.approved is True
    assert result.execution_result is None
    assert "request" in result.error_message.lower()
    print(f"[PASS] missing_llm_request             | decision={result.decision_result.approved} "
          f"execution={result.execution_result} error='{result.error_message}'")


# ------------------------------------------------------------------
# Scenario 8: Provider returns error response
# ------------------------------------------------------------------


def scenario_provider_error_response() -> None:
    """Provider returns an error finish reason; execution fails."""
    alice_id = uuid4()
    task = TaskSnapshot(task_id=uuid4(), name="Failing task")
    dept = DepartmentSnapshot(
        department_id=uuid4(), name="Engineering",
        employees={alice_id: DepartmentEmployeeLink(alice_id)},
    )
    alice = EmployeeSnapshot(employee_id=alice_id, name="Alice", state="idle")

    registry = ProviderRegistry()
    registry.register("failing", FakeProviderAdapter(
        content="Model refused",
        finish_reason="error",
        provider_name="failing",
    ))
    gateway = LLMGateway(registry)

    orchestrator = _make_orchestrator()
    result = orchestrator.execute_task(
        task_snapshot=task,
        candidate_snapshots=[alice],
        department_snapshot=dept,
        llm_request=_build_llm_request(),
        gateway=gateway,
        gateway_provider="failing",
    )

    assert result.decision_result.approved is True
    assert result.execution_result is not None
    assert result.execution_result.success is False
    assert "reason" in result.execution_result.error_message.lower() or "error" in result.execution_result.error_message.lower()
    print(f"[PASS] provider_error_response         | decision={result.decision_result.approved} "
          f"execution={result.execution_result.success} "
          f"error='{result.execution_result.error_message}'")


# ------------------------------------------------------------------
# Scenario 9: Result propagated correctly through the chain
# ------------------------------------------------------------------


def scenario_result_propagated() -> None:
    """OrchestratorExecutionResult correctly wraps both sub-results."""
    alice_id = uuid4()
    task = TaskSnapshot(task_id=uuid4(), name="Propagation Test")
    dept = DepartmentSnapshot(
        department_id=uuid4(), name="Engineering",
        employees={alice_id: DepartmentEmployeeLink(alice_id)},
    )
    alice = EmployeeSnapshot(employee_id=alice_id, name="Alice", state="idle")
    skill = SkillSnapshot(skill_id=uuid4(), name="General", employee_ids={alice_id})

    registry = ProviderRegistry()
    registry.register("openai", FakeProviderAdapter(content="Propagated result.", provider_name="openai"))
    gateway = LLMGateway(registry)

    orchestrator = _make_orchestrator()
    result = orchestrator.execute_task(
        task_snapshot=task,
        candidate_snapshots=[alice],
        department_snapshot=dept,
        skill_snapshots=[skill],
        llm_request=_build_llm_request(),
        gateway=gateway,
        gateway_provider="openai",
    )

    assert isinstance(result.orchestrator_id, UUID)
    assert isinstance(result.decision_result, object)
    assert isinstance(result.execution_result, ExecutionResult)
    assert result.decision_result.decision_id is not None
    assert result.execution_result.execution_id is not None
    assert result.decision_result.chosen_candidate_id == alice_id
    assert result.execution_result.trace.provider_used == "openai"
    print(f"[PASS] result_propagated               | orchestrator_id={result.orchestrator_id.hex[:8]} "
          f"decision_id={result.decision_result.decision_id.hex[:8]} "
          f"execution_id={result.execution_result.execution_id.hex[:8]}")


# ------------------------------------------------------------------
# Scenario 10: No gateway provided
# ------------------------------------------------------------------


def scenario_no_gateway_provided() -> None:
    """Decision passes but no gateway means execution is skipped."""
    alice_id = uuid4()
    task = TaskSnapshot(task_id=uuid4(), name="No gateway")
    dept = DepartmentSnapshot(
        department_id=uuid4(), name="Engineering",
        employees={alice_id: DepartmentEmployeeLink(alice_id)},
    )
    alice = EmployeeSnapshot(employee_id=alice_id, name="Alice", state="idle")

    orchestrator = _make_orchestrator()
    result = orchestrator.execute_task(
        task_snapshot=task,
        candidate_snapshots=[alice],
        department_snapshot=dept,
        llm_request=_build_llm_request(),
        gateway=None,
    )

    assert result.success is False
    assert result.decision_result.approved is True
    assert result.execution_result is None
    assert "gateway" in result.error_message.lower()
    print(f"[PASS] no_gateway_provided             | decision={result.decision_result.approved} "
          f"execution_skipped={result.execution_result is None} "
          f"error='{result.error_message}'")


# ------------------------------------------------------------------
# Scenario 11: Determinism within the same orchestrator
# ------------------------------------------------------------------


def scenario_determinism() -> None:
    """Same inputs produce consistent decision outcomes."""
    alice_id = uuid4()
    task = TaskSnapshot(task_id=uuid4(), name="Deterministic Task")
    dept = DepartmentSnapshot(
        department_id=uuid4(), name="Engineering",
        employees={alice_id: DepartmentEmployeeLink(alice_id)},
    )
    alice = EmployeeSnapshot(employee_id=alice_id, name="Alice", state="idle")
    skill = SkillSnapshot(skill_id=uuid4(), name="General", employee_ids={alice_id})

    registry = ProviderRegistry()
    registry.register("openai", FakeProviderAdapter(content="Same output.", provider_name="openai"))
    gateway = LLMGateway(registry)

    orchestrator = _make_orchestrator()

    r1 = orchestrator.execute_task(
        task, [alice], dept, [skill], llm_request=_build_llm_request(),
        gateway=gateway, gateway_provider="openai",
    )
    r2 = orchestrator.execute_task(
        task, [alice], dept, [skill], llm_request=_build_llm_request(),
        gateway=gateway, gateway_provider="openai",
    )

    assert r1.decision_result.chosen_candidate_id == r2.decision_result.chosen_candidate_id
    assert r1.decision_result.decision_code == r2.decision_result.decision_code
    assert r1.execution_result.output == r2.execution_result.output
    print(f"[PASS] determinism                     | code={r1.decision_result.decision_code} "
          f"output='{r1.execution_result.output}' (identical)")


# ------------------------------------------------------------------
# Main
# ------------------------------------------------------------------


def main() -> None:
    print("=" * 62)
    print("Company Execution Flow Demo")
    print("=" * 62)
    print()

    scenario_full_successful_flow()
    scenario_no_candidates()
    scenario_policy_blocks()
    scenario_best_candidate_chosen()
    scenario_no_skill_match()
    scenario_nonexistent_provider()
    scenario_missing_llm_request()
    scenario_provider_error_response()
    scenario_result_propagated()
    scenario_no_gateway_provided()
    scenario_determinism()

    print()
    print("=" * 62)
    print("All company execution flow scenarios passed.")
    print("=" * 62)


if __name__ == "__main__":
    main()
