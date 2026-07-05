"""Orchestrator + Conversation integration demo.

Validates that OrchestratorRuntime automatically creates and
propagates a ConversationSession across executions, always
returning a new instance without mutating the original.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any
from uuid import UUID, uuid4

from core.conversation import ConversationRuntime, ConversationSession
from core.execution import ExecutionResult
from core.llm import LLMGateway, LLMRequest, LLMResponse, ProviderAdapter, ProviderRegistry
from core.orchestrator import OrchestratorExecutionResult
from core.orchestrator.runtime import OrchestratorRuntime


# ------------------------------------------------------------------
# Plain snapshot-like objects (same pattern as company flow demo)
# ------------------------------------------------------------------


@dataclass
class TaskSnapshot:
    task_id: UUID
    name: str
    metadata: object = None


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
        content: str = "Generated content.",
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
            input_tokens=10,
            output_tokens=20,
            total_tokens=30,
            finish_reason=self._finish_reason,
        )


# ------------------------------------------------------------------
# Helpers
# ------------------------------------------------------------------


def _make_orchestrator() -> OrchestratorRuntime:
    from core.events.bus import EventBus
    from core.runtime import CompanyRuntime

    bus = EventBus()
    company = CompanyRuntime(event_bus=bus)
    dept_runtime = _FakeDepartmentRuntime()
    return OrchestratorRuntime(company, dept_runtime, bus)


class _FakeDepartmentRuntime:
    def department(self, department_id: UUID) -> Any:
        return object()

    def sync_employee_state(self, department_id: UUID, event: Any) -> None:
        pass


def _build_llm_request(prompt_text: str = "Write about {topic}.") -> LLMRequest:
    from core.llm import PromptBuilder, PromptTemplate
    from core.llm.request_builder import LLMRequestBuilder

    template = PromptTemplate.create(
        name="content_gen",
        template=prompt_text,
        required_placeholders=["topic"],
    )
    render = PromptBuilder.render(template, {"topic": "AI"})
    return LLMRequestBuilder.build(render, model="gpt-4o", temperature=0.5)


# ------------------------------------------------------------------
# Scenario 1: First execution creates a session
# ------------------------------------------------------------------


def scenario_first_execution_creates_session() -> None:
    """When no session is passed, one is auto-created."""
    alice_id = uuid4()
    task = TaskSnapshot(task_id=uuid4(), name="First Task")
    dept = DepartmentSnapshot(
        department_id=uuid4(), name="Content",
        employees={alice_id: DepartmentEmployeeLink(alice_id)},
    )
    alice = EmployeeSnapshot(employee_id=alice_id, name="Alice", state="idle")
    skill = SkillSnapshot(skill_id=uuid4(), name="Writing", employee_ids={alice_id})

    registry = ProviderRegistry()
    registry.register("openai", FakeProviderAdapter(provider_name="openai"))
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

    assert result.updated_conversation is not None
    assert len(result.updated_conversation.messages) == 2
    assert isinstance(result.updated_conversation.session_id, UUID)
    print(f"[PASS] first_exec_creates_session     | session_id={result.updated_conversation.session_id.hex[:8]} "
          f"messages={len(result.updated_conversation.messages)}")


# ------------------------------------------------------------------
# Scenario 2: Second execution reuses session
# ------------------------------------------------------------------


def scenario_second_execution_reuses_session() -> None:
    """Passing the previous session chains history."""
    alice_id = uuid4()
    task = TaskSnapshot(task_id=uuid4(), name="Chain Task")
    dept = DepartmentSnapshot(
        department_id=uuid4(), name="Content",
        employees={alice_id: DepartmentEmployeeLink(alice_id)},
    )
    alice = EmployeeSnapshot(employee_id=alice_id, name="Alice", state="idle")
    skill = SkillSnapshot(skill_id=uuid4(), name="Writing", employee_ids={alice_id})

    registry = ProviderRegistry()
    registry.register("openai", FakeProviderAdapter(provider_name="openai"))
    gateway = LLMGateway(registry)

    orchestrator = _make_orchestrator()

    r1 = orchestrator.execute_task(
        task, [alice], dept, [skill],
        llm_request=_build_llm_request(), gateway=gateway, gateway_provider="openai",
    )
    assert r1.updated_conversation is not None
    assert len(r1.updated_conversation.messages) == 2

    r2 = orchestrator.execute_task(
        task, [alice], dept, [skill],
        llm_request=_build_llm_request(), gateway=gateway, gateway_provider="openai",
        conversation_session=r1.updated_conversation,
    )
    assert r2.updated_conversation is not None
    assert len(r2.updated_conversation.messages) == 4
    assert r2.updated_conversation.session_id == r1.updated_conversation.session_id
    print(f"[PASS] second_exec_reuses_session     | session_id={r2.updated_conversation.session_id.hex[:8]} "
          f"messages={len(r2.updated_conversation.messages)} (grew from 2)")


# ------------------------------------------------------------------
# Scenario 3: History grows correctly
# ------------------------------------------------------------------


def scenario_history_grows_correctly() -> None:
    """Multiple chained executions accumulate messages in order."""
    alice_id = uuid4()
    task = TaskSnapshot(task_id=uuid4(), name="Growth Task")
    dept = DepartmentSnapshot(
        department_id=uuid4(), name="Content",
        employees={alice_id: DepartmentEmployeeLink(alice_id)},
    )
    alice = EmployeeSnapshot(employee_id=alice_id, name="Alice", state="idle")
    skill = SkillSnapshot(skill_id=uuid4(), name="Writing", employee_ids={alice_id})

    registry = ProviderRegistry()
    registry.register("openai", FakeProviderAdapter(provider_name="openai"))
    gateway = LLMGateway(registry)

    orchestrator = _make_orchestrator()
    session = None

    for i in range(1, 4):
        req = _build_llm_request(f"Step {i} about {{topic}}.")
        result = orchestrator.execute_task(
            task, [alice], dept, [skill],
            llm_request=req, gateway=gateway, gateway_provider="openai",
            conversation_session=session,
        )
        assert result.updated_conversation is not None
        assert len(result.updated_conversation.messages) == i * 2
        session = result.updated_conversation

    assert len(session.messages) == 6
    assert session.messages[0].role == "user"
    assert session.messages[1].role == "assistant"
    assert session.messages[2].content == "Step 2 about AI."
    assert session.messages[4].content == "Step 3 about AI."
    print(f"[PASS] history_grows_correctly        | 3 executions -> "
          f"{len(session.messages)} messages, all in order")


# ------------------------------------------------------------------
# Scenario 4: Original session remains immutable
# ------------------------------------------------------------------


def scenario_original_session_immutable() -> None:
    """The session passed in is never mutated by the orchestrator."""
    original = ConversationRuntime.create_session("emp-001")
    alice_id = uuid4()
    task = TaskSnapshot(task_id=uuid4(), name="Immutable Test")
    dept = DepartmentSnapshot(
        department_id=uuid4(), name="Content",
        employees={alice_id: DepartmentEmployeeLink(alice_id)},
    )
    alice = EmployeeSnapshot(employee_id=alice_id, name="Alice", state="idle")
    skill = SkillSnapshot(skill_id=uuid4(), name="Writing", employee_ids={alice_id})

    registry = ProviderRegistry()
    registry.register("openai", FakeProviderAdapter(provider_name="openai"))
    gateway = LLMGateway(registry)

    orchestrator = _make_orchestrator()
    _ = orchestrator.execute_task(
        task, [alice], dept, [skill],
        llm_request=_build_llm_request(), gateway=gateway, gateway_provider="openai",
        conversation_session=original,
    )

    assert len(original.messages) == 0
    print(f"[PASS] original_session_immutable     | original untouched "
          f"(messages={len(original.messages)})")


# ------------------------------------------------------------------
# Scenario 5: Multiple executions of the same task
# ------------------------------------------------------------------


def scenario_multiple_executions_same_task() -> None:
    """Repeated execution of the same task accumulates history."""
    alice_id = uuid4()
    task = TaskSnapshot(task_id=uuid4(), name="Repeat Task")
    dept = DepartmentSnapshot(
        department_id=uuid4(), name="Content",
        employees={alice_id: DepartmentEmployeeLink(alice_id)},
    )
    alice = EmployeeSnapshot(employee_id=alice_id, name="Alice", state="idle")
    skill = SkillSnapshot(skill_id=uuid4(), name="Writing", employee_ids={alice_id})

    registry = ProviderRegistry()
    registry.register("openai", FakeProviderAdapter(provider_name="openai"))
    gateway = LLMGateway(registry)

    orchestrator = _make_orchestrator()
    session = None

    for _ in range(3):
        r = orchestrator.execute_task(
            task, [alice], dept, [skill],
            llm_request=_build_llm_request(), gateway=gateway, gateway_provider="openai",
            conversation_session=session,
        )
        session = r.updated_conversation

    assert session is not None
    assert len(session.messages) == 6
    print(f"[PASS] multiple_exec_same_task        | same task 3x -> "
          f"{len(session.messages)} messages")


# ------------------------------------------------------------------
# Scenario 6: Multiple independent tasks
# ------------------------------------------------------------------


def scenario_multiple_independent_tasks() -> None:
    """Different tasks get independent session chains."""
    alice_id = uuid4()
    task_a = TaskSnapshot(task_id=uuid4(), name="Task A")
    task_b = TaskSnapshot(task_id=uuid4(), name="Task B")
    dept = DepartmentSnapshot(
        department_id=uuid4(), name="Content",
        employees={alice_id: DepartmentEmployeeLink(alice_id)},
    )
    alice = EmployeeSnapshot(employee_id=alice_id, name="Alice", state="idle")
    skill = SkillSnapshot(skill_id=uuid4(), name="Writing", employee_ids={alice_id})

    registry = ProviderRegistry()
    registry.register("openai", FakeProviderAdapter(provider_name="openai"))
    gateway = LLMGateway(registry)

    orchestrator = _make_orchestrator()

    session_a = orchestrator.execute_task(
        task_a, [alice], dept, [skill],
        llm_request=_build_llm_request(), gateway=gateway, gateway_provider="openai",
    ).updated_conversation

    session_b = orchestrator.execute_task(
        task_b, [alice], dept, [skill],
        llm_request=_build_llm_request(), gateway=gateway, gateway_provider="openai",
    ).updated_conversation

    assert session_a is not None
    assert session_b is not None
    assert session_a.session_id != session_b.session_id
    assert len(session_a.messages) == 2
    assert len(session_b.messages) == 2
    print(f"[PASS] multiple_independent_tasks     | session_a={session_a.session_id.hex[:8]} "
          f"session_b={session_b.session_id.hex[:8]} (different)")


# ------------------------------------------------------------------
# Scenario 7: Multiple employees independent sessions
# ------------------------------------------------------------------


def scenario_multiple_employees() -> None:
    """Different employees produce independent conversation histories."""
    alice_id = uuid4()
    bob_id = uuid4()
    task = TaskSnapshot(task_id=uuid4(), name="Shared Task")
    dept = DepartmentSnapshot(
        department_id=uuid4(), name="Content",
        employees={
            alice_id: DepartmentEmployeeLink(alice_id),
            bob_id: DepartmentEmployeeLink(bob_id),
        },
    )
    alice = EmployeeSnapshot(employee_id=alice_id, name="Alice", state="idle")
    bob = EmployeeSnapshot(employee_id=bob_id, name="Bob", state="idle")
    skill = SkillSnapshot(skill_id=uuid4(), name="Writing", employee_ids={alice_id, bob_id})

    registry = ProviderRegistry()
    registry.register("openai", FakeProviderAdapter(provider_name="openai"))
    gateway = LLMGateway(registry)

    orchestrator = _make_orchestrator()

    session_alice = orchestrator.execute_task(
        task, [alice], dept, [skill],
        llm_request=_build_llm_request(), gateway=gateway, gateway_provider="openai",
    ).updated_conversation

    session_bob = orchestrator.execute_task(
        task, [bob], dept, [skill],
        llm_request=_build_llm_request(), gateway=gateway, gateway_provider="openai",
    ).updated_conversation

    assert session_alice is not None
    assert session_bob is not None
    assert len(session_alice.messages) == 2
    assert len(session_bob.messages) == 2
    print(f"[PASS] multiple_employees             | alice_msgs={len(session_alice.messages)} "
          f"bob_msgs={len(session_bob.messages)} (independent)")


# ------------------------------------------------------------------
# Scenario 8: Execution blocked by Decision Engine
# ------------------------------------------------------------------


def scenario_blocked_by_decision_engine() -> None:
    """When decision blocks, session is returned unchanged (no LLM call)."""
    alice_id = uuid4()
    task = TaskSnapshot(task_id=uuid4(), name="Blocked Task")
    dept = DepartmentSnapshot(
        department_id=uuid4(), name="Engineering",
        employees={alice_id: DepartmentEmployeeLink(alice_id)},
    )
    alice = EmployeeSnapshot(employee_id=alice_id, name="Alice", state="busy")

    session = ConversationRuntime.create_session("emp-test")
    prior_msg_count = len(session.messages)

    orchestrator = _make_orchestrator()
    result = orchestrator.execute_task(
        task, [alice], dept,
        conversation_session=session,
    )

    assert result.success is False
    assert result.decision_result.approved is False
    assert result.updated_conversation is not None
    assert len(result.updated_conversation.messages) == prior_msg_count
    assert result.updated_conversation.session_id == session.session_id
    assert result.execution_result is None
    print(f"[PASS] blocked_by_decision            | approved={result.decision_result.approved} "
          f"session messages={len(result.updated_conversation.messages)} (unchanged)")


# ------------------------------------------------------------------
# Scenario 9: Execution blocked by Policy Engine
# ------------------------------------------------------------------


def scenario_blocked_by_policy_engine() -> None:
    """Policy constraint blocks execution; session is returned unchanged."""
    alice_id = uuid4()

    def _block_all(ctx: object) -> tuple[bool, str]:
        return False, "Blocked by test policy"

    from core.policies.runtime import Constraint

    task = TaskSnapshot(task_id=uuid4(), name="Restricted Task")
    dept = DepartmentSnapshot(
        department_id=uuid4(), name="Restricted",
        employees={alice_id: DepartmentEmployeeLink(alice_id)},
    )
    alice = EmployeeSnapshot(employee_id=alice_id, name="Alice", state="idle")

    session = ConversationRuntime.create_session("emp-test")
    prior_msg_count = len(session.messages)

    orchestrator = _make_orchestrator()
    result = orchestrator.execute_task(
        task, [alice], dept,
        policy_constraints=[
            Constraint(constraint_id="block", description="Block all", check=_block_all),
        ],
        conversation_session=session,
    )

    assert result.success is False
    assert result.decision_result.approved is False
    assert result.updated_conversation is not None
    assert len(result.updated_conversation.messages) == prior_msg_count
    assert result.updated_conversation.session_id == session.session_id
    assert result.execution_result is None
    print(f"[PASS] blocked_by_policy              | approved={result.decision_result.approved} "
          f"code={result.decision_result.decision_code} "
          f"session unchanged ({len(result.updated_conversation.messages)} msgs)")


# ------------------------------------------------------------------
# Scenario 10: Successful execution
# ------------------------------------------------------------------


def scenario_successful_execution() -> None:
    """Full successful flow produces a session with user + assistant messages."""
    alice_id = uuid4()
    task = TaskSnapshot(task_id=uuid4(), name="Success Task")
    dept = DepartmentSnapshot(
        department_id=uuid4(), name="Content",
        employees={alice_id: DepartmentEmployeeLink(alice_id)},
    )
    alice = EmployeeSnapshot(employee_id=alice_id, name="Alice", state="idle")
    skill = SkillSnapshot(skill_id=uuid4(), name="Writing", employee_ids={alice_id})

    registry = ProviderRegistry()
    registry.register("openai", FakeProviderAdapter(
        content="Success output.", provider_name="openai"))
    gateway = LLMGateway(registry)

    orchestrator = _make_orchestrator()
    result = orchestrator.execute_task(
        task, [alice], dept, [skill],
        llm_request=_build_llm_request(), gateway=gateway, gateway_provider="openai",
    )

    assert result.success is True
    assert result.updated_conversation is not None
    assert len(result.updated_conversation.messages) == 2
    assert result.updated_conversation.messages[0].role == "user"
    assert result.updated_conversation.messages[1].role == "assistant"
    assert result.updated_conversation.messages[1].content == "Success output."
    assert result.execution_result is not None
    assert result.execution_result.success is True
    print(f"[PASS] successful_execution           | success={result.success} "
          f"execution_output='{result.execution_result.output}' "
          f"conversation_msgs={len(result.updated_conversation.messages)}")


# ------------------------------------------------------------------
# Scenario 11: Determinism
# ------------------------------------------------------------------


def scenario_determinism() -> None:
    """Same inputs produce identical conversation structures."""
    alice_id = uuid4()
    task = TaskSnapshot(task_id=uuid4(), name="Deterministic")
    dept = DepartmentSnapshot(
        department_id=uuid4(), name="Content",
        employees={alice_id: DepartmentEmployeeLink(alice_id)},
    )
    alice = EmployeeSnapshot(employee_id=alice_id, name="Alice", state="idle")
    skill = SkillSnapshot(skill_id=uuid4(), name="Writing", employee_ids={alice_id})

    registry = ProviderRegistry()
    registry.register("openai", FakeProviderAdapter(
        content="Deterministic.", provider_name="openai"))
    gateway = LLMGateway(registry)

    orchestrator = _make_orchestrator()

    req = _build_llm_request()
    session = ConversationRuntime.create_session("emp-test")

    r1 = orchestrator.execute_task(
        task, [alice], dept, [skill],
        llm_request=req, gateway=gateway, gateway_provider="openai",
        conversation_session=session,
    )
    r2 = orchestrator.execute_task(
        task, [alice], dept, [skill],
        llm_request=req, gateway=gateway, gateway_provider="openai",
        conversation_session=session,
    )

    assert r1.updated_conversation is not None
    assert r2.updated_conversation is not None
    assert r1.updated_conversation.messages[0].role == r2.updated_conversation.messages[0].role
    assert r1.updated_conversation.messages[0].content == r2.updated_conversation.messages[0].content
    assert r1.updated_conversation.messages[1].role == r2.updated_conversation.messages[1].role
    assert r1.updated_conversation.messages[1].content == r2.updated_conversation.messages[1].content
    print(f"[PASS] determinism                    | identical structure "
          f"(user='{r1.updated_conversation.messages[0].content}', "
          f"assistant='{r1.updated_conversation.messages[1].content}')")


# ------------------------------------------------------------------
# Scenario 12: Complete integration (auto-creation + execution + output)
# ------------------------------------------------------------------


def scenario_complete_integration() -> None:
    """End-to-end: no session in -> session created -> execution -> updated session out."""
    alice_id = uuid4()
    task = TaskSnapshot(task_id=uuid4(), name="Integration")
    dept = DepartmentSnapshot(
        department_id=uuid4(), name="Content",
        employees={alice_id: DepartmentEmployeeLink(alice_id)},
    )
    alice = EmployeeSnapshot(employee_id=alice_id, name="Alice", state="idle")
    skill = SkillSnapshot(skill_id=uuid4(), name="Writing", employee_ids={alice_id})

    registry = ProviderRegistry()
    registry.register("openai", FakeProviderAdapter(
        content="Integration result.", provider_name="openai"))
    gateway = LLMGateway(registry)

    orchestrator = _make_orchestrator()

    # No session passed -> auto-created
    result = orchestrator.execute_task(
        task, [alice], dept, [skill],
        llm_request=_build_llm_request(), gateway=gateway, gateway_provider="openai",
    )

    assert result.updated_conversation is not None
    assert len(result.updated_conversation.messages) == 2
    assert result.updated_conversation.messages[0].role == "user"
    assert result.updated_conversation.messages[1].role == "assistant"
    assert result.updated_conversation.messages[1].content == "Integration result."
    assert result.execution_result is not None
    assert result.execution_result.output == "Integration result."

    # Chain a second execution using the returned session
    result2 = orchestrator.execute_task(
        task, [alice], dept, [skill],
        llm_request=_build_llm_request(), gateway=gateway, gateway_provider="openai",
        conversation_session=result.updated_conversation,
    )

    assert result2.updated_conversation is not None
    assert len(result2.updated_conversation.messages) == 4
    assert result2.updated_conversation.session_id == result.updated_conversation.session_id
    assert result2.updated_conversation.messages[2].role == "user"
    assert result2.updated_conversation.messages[3].role == "assistant"
    print(f"[PASS] complete_integration           | 2 executions -> "
          f"{len(result2.updated_conversation.messages)} messages "
          f"(auto-create + chain)")


# ------------------------------------------------------------------
# Scenario 13: Auto-created session has task metadata
# ------------------------------------------------------------------


def scenario_session_metadata() -> None:
    """Auto-created session carries task metadata."""
    alice_id = uuid4()
    task = TaskSnapshot(task_id=uuid4(), name="Metadata Task")
    dept = DepartmentSnapshot(
        department_id=uuid4(), name="Content",
        employees={alice_id: DepartmentEmployeeLink(alice_id)},
    )
    alice = EmployeeSnapshot(employee_id=alice_id, name="Alice", state="idle")
    skill = SkillSnapshot(skill_id=uuid4(), name="Writing", employee_ids={alice_id})

    registry = ProviderRegistry()
    registry.register("openai", FakeProviderAdapter(provider_name="openai"))
    gateway = LLMGateway(registry)

    orchestrator = _make_orchestrator()
    result = orchestrator.execute_task(
        task, [alice], dept, [skill],
        llm_request=_build_llm_request(), gateway=gateway, gateway_provider="openai",
    )

    assert result.updated_conversation is not None
    meta = result.updated_conversation.metadata
    assert "task_id" in meta
    assert meta["task_id"] == str(task.task_id)
    assert "task_name" in meta
    assert meta["task_name"] == "Metadata Task"
    print(f"[PASS] session_metadata               | task_id={meta['task_id'][:8]} "
          f"task_name='{meta['task_name']}'")


# ------------------------------------------------------------------
# Main
# ------------------------------------------------------------------


def main() -> None:
    print("=" * 66)
    print("Orchestrator + Conversation Integration Demo")
    print("=" * 66)
    print()

    scenario_first_execution_creates_session()
    scenario_second_execution_reuses_session()
    scenario_history_grows_correctly()
    scenario_original_session_immutable()
    scenario_multiple_executions_same_task()
    scenario_multiple_independent_tasks()
    scenario_multiple_employees()
    scenario_blocked_by_decision_engine()
    scenario_blocked_by_policy_engine()
    scenario_successful_execution()
    scenario_determinism()
    scenario_complete_integration()
    scenario_session_metadata()

    print()
    print("=" * 66)
    print("All Orchestrator + Conversation scenarios passed.")
    print("=" * 66)


if __name__ == "__main__":
    main()
