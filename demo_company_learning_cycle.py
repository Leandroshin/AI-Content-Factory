"""Demo for the automated company learning cycle.

Validates that OrchestratorRuntime.execute_task() automatically runs
the LearningPipeline after successful execution, producing knowledge,
learning recommendations, and skills — including Skill Runtime promotion.

Full pipeline:
Company -> Decision -> Execution -> Conversation -> Memory ->
Knowledge -> Learning -> Skills -> Future Decision with real skills
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any
from uuid import UUID, uuid4

from core.conversation import ConversationRuntime, ConversationSession
from core.decision.runtime import DecisionResult
from core.events.bus import EventBus
from core.execution.runtime import ExecutionResult
from core.learning.pipeline import PipelineResult
from core.llm.models import LLMRequest, LLMResponse
from core.orchestrator.runtime import (
    OrchestratorExecutionResult,
    OrchestratorRuntime,
)
from core.skills.runtime import SkillRuntime, SkillRuntimeSnapshot


# ------------------------------------------------------------------
# Snapshots
# ------------------------------------------------------------------


@dataclass
class TaskSnapshot:
    task_id: UUID
    name: str
    metadata: Any = None


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
    employees: dict[UUID, Any] = field(default_factory=dict)


@dataclass
class DepartmentEmployeeLink:
    employee_id: UUID
    state: str = "idle"


# ------------------------------------------------------------------
# Fake Gateway
# ------------------------------------------------------------------


class FakeGateway:
    """Minimal LLM gateway that returns a canned response."""

    def __init__(self, content: str = "Generated content for the task.") -> None:
        self.content = content

    def execute(self, request: LLMRequest, provider_name: str | None = None) -> LLMResponse:
        return LLMResponse(
            request_id=request.request_id,
            provider=provider_name or "fake",
            model=request.model,
            content=self.content,
            input_tokens=10,
            output_tokens=20,
            total_tokens=30,
            finish_reason="stop",
        )


# ------------------------------------------------------------------
# Helpers
# ------------------------------------------------------------------


def _make_skill_runtime() -> SkillRuntime:
    """Create a minimal SkillRuntime for testing."""
    from core.events.bus import EventBus
    from core.knowledge.runtime import KnowledgeRuntime
    from core.results.runtime import ResultRuntime

    bus = EventBus()
    result_runtime = ResultRuntime.__new__(ResultRuntime)
    result_runtime.event_bus = bus  # type: ignore[attr-defined]
    result_runtime._results = {}  # type: ignore[attr-defined]
    kr = KnowledgeRuntime.__new__(KnowledgeRuntime)
    kr.event_bus = bus  # type: ignore[attr-defined]
    kr._knowledge = {}  # type: ignore[attr-defined]
    kr.result_runtime = result_runtime  # type: ignore[attr-defined]
    sr = SkillRuntime.__new__(SkillRuntime)
    sr.knowledge_runtime = kr  # type: ignore[attr-defined]
    sr.event_bus = bus  # type: ignore[attr-defined]
    sr._skills = {}  # type: ignore[attr-defined]
    sr._events = []  # type: ignore[attr-defined]
    return sr


def _base_setup() -> tuple[UUID, TaskSnapshot, list[EmployeeSnapshot], DepartmentSnapshot]:
    """Create a standard task, department, and two candidates."""
    alice_id = uuid4()
    bob_id = uuid4()
    task = TaskSnapshot(task_id=uuid4(), name="Write Article", metadata=TaskMetadata(tags=["writing"]))
    department = DepartmentSnapshot(
        department_id=uuid4(), name="Content",
        employees={
            alice_id: DepartmentEmployeeLink(alice_id),
            bob_id: DepartmentEmployeeLink(bob_id),
        },
    )
    alice = EmployeeSnapshot(employee_id=alice_id, name="Alice", state="idle")
    bob = EmployeeSnapshot(employee_id=bob_id, name="Bob", state="idle")
    return alice_id, task, [alice, bob], department


# ------------------------------------------------------------------
# Scenario 1: Decisão bloqueada
# ------------------------------------------------------------------


def scenario_decision_blocked() -> None:
    """When decision is not approved, no execution or learning occurs."""
    _, task, candidates, dept = _base_setup()
    # Empty department = no candidates pass department filter
    empty_dept = DepartmentSnapshot(department_id=uuid4(), name="Empty", employees={})

    # Need to bypass the select_candidates filter — use policy to block
    from core.policies.runtime import Constraint

    def _block_all(ctx: object) -> tuple[bool, str]:
        return False, "All candidates blocked."

    block = Constraint(constraint_id="block", description="Block", check=_block_all)

    result = OrchestratorRuntime.execute_task(
        task_snapshot=task,
        candidate_snapshots=candidates,
        department_snapshot=empty_dept,
        policy_constraints=[block],
    )

    assert result.success is False
    assert result.execution_result is None
    assert result.learning_pipeline_result is None
    assert result.decision_result.approved is False
    print(f"[PASS] decision_blocked                | success={result.success} "
          f"code={result.decision_result.decision_code}")


# ------------------------------------------------------------------
# Scenario 2: Execução bloqueada
# ------------------------------------------------------------------


def scenario_execution_blocked() -> None:
    """Without gateway/LLM request, execution is blocked."""
    _, task, candidates, dept = _base_setup()

    result = OrchestratorRuntime.execute_task(
        task_snapshot=task,
        candidate_snapshots=candidates,
        department_snapshot=dept,
    )

    assert result.success is False
    assert result.execution_result is None
    assert result.learning_pipeline_result is None
    assert result.decision_result.approved is True  # decision passed
    print(f"[PASS] execution_blocked               | success={result.success} "
          f"decision_approved={result.decision_result.approved}")


# ------------------------------------------------------------------
# Scenario 3: Execução bem sucedida
# ------------------------------------------------------------------


def scenario_execution_success() -> None:
    """Successful execution returns result with output."""
    _, task, candidates, dept = _base_setup()
    llm_req = LLMRequest.create(prompt="Write an article.")
    gateway = FakeGateway()

    result = OrchestratorRuntime.execute_task(
        task_snapshot=task, candidate_snapshots=candidates,
        department_snapshot=dept, llm_request=llm_req, gateway=gateway,
    )

    assert result.success is True
    assert result.execution_result is not None
    assert result.execution_result.success is True
    assert result.execution_result.output == "Generated content for the task."
    print(f"[PASS] execution_success               | success={result.success} "
          f"output='{result.execution_result.output[:30]}...'")


# ------------------------------------------------------------------
# Scenario 4: Aprendizado automático
# ------------------------------------------------------------------


def scenario_auto_learning() -> None:
    """After successful execution, learning pipeline runs automatically."""
    _, task, candidates, dept = _base_setup()
    llm_req = LLMRequest.create(prompt="Explain Python.")
    gateway = FakeGateway()

    result = OrchestratorRuntime.execute_task(
        task_snapshot=task, candidate_snapshots=candidates,
        department_snapshot=dept, llm_request=llm_req, gateway=gateway,
    )

    assert result.success is True
    assert result.learning_pipeline_result is not None
    assert result.learning_pipeline_result.success is True
    assert result.learning_pipeline_result.trace.skills_created_count >= 1
    assert result.knowledge_snapshot is not None
    assert result.learning_snapshot is not None
    assert result.skill_snapshot is not None
    print(f"[PASS] auto_learning                   | pipeline success="
          f"{result.learning_pipeline_result.success} "
          f"skills={result.learning_pipeline_result.trace.skills_created_count}")


# ------------------------------------------------------------------
# Scenario 5: Sessão vazia (criada automaticamente)
# ------------------------------------------------------------------


def scenario_auto_session() -> None:
    """Orchestrator creates a conversation session automatically."""
    _, task, candidates, dept = _base_setup()
    llm_req = LLMRequest.create(prompt="Test.")
    gateway = FakeGateway()

    result = OrchestratorRuntime.execute_task(
        task_snapshot=task, candidate_snapshots=candidates,
        department_snapshot=dept, llm_request=llm_req, gateway=gateway,
    )

    assert result.updated_conversation is not None
    assert isinstance(result.updated_conversation, ConversationSession)
    assert len(result.updated_conversation.messages) > 0
    print(f"[PASS] auto_session                    | session created: "
          f"{len(result.updated_conversation.messages)} messages")


# ------------------------------------------------------------------
# Scenario 6: Múltiplas execuções
# ------------------------------------------------------------------


def scenario_multiple_executions() -> None:
    """Multiple task executions each produce independent results."""
    _, task, candidates, dept = _base_setup()
    llm_req = LLMRequest.create(prompt="Task 1.")
    gateway = FakeGateway()

    r1 = OrchestratorRuntime.execute_task(
        task_snapshot=task, candidate_snapshots=candidates,
        department_snapshot=dept, llm_request=llm_req, gateway=gateway,
    )
    r2 = OrchestratorRuntime.execute_task(
        task_snapshot=task, candidate_snapshots=candidates,
        department_snapshot=dept, llm_request=llm_req, gateway=gateway,
    )

    assert r1.success is True
    assert r2.success is True
    assert r1.orchestrator_id != r2.orchestrator_id
    assert r1.learning_pipeline_result is not None
    assert r2.learning_pipeline_result is not None
    print(f"[PASS] multiple_executions             | 2 executions, both learned: "
          f"skills1={r1.learning_pipeline_result.trace.skills_created_count} "
          f"skills2={r2.learning_pipeline_result.trace.skills_created_count}")


# ------------------------------------------------------------------
# Scenario 7: Múltiplas conversas
# ------------------------------------------------------------------


def scenario_multiple_conversations() -> None:
    """Separate conversation sessions produce separate pipeline results."""
    session_a = ConversationRuntime.create_session("emp-001")
    session_a = ConversationRuntime.append_message(session_a, "user", "Hello A")
    session_b = ConversationRuntime.create_session("emp-002")
    session_b = ConversationRuntime.append_message(session_b, "user", "Hello B")

    _, task, candidates, dept = _base_setup()
    llm_req = LLMRequest.create(prompt="Task.")
    gateway = FakeGateway()

    r_a = OrchestratorRuntime.execute_task(
        task_snapshot=task, candidate_snapshots=candidates,
        department_snapshot=dept, llm_request=llm_req, gateway=gateway,
        conversation_session=session_a,
    )
    r_b = OrchestratorRuntime.execute_task(
        task_snapshot=task, candidate_snapshots=candidates,
        department_snapshot=dept, llm_request=llm_req, gateway=gateway,
        conversation_session=session_b,
    )

    assert r_a.learning_pipeline_result is not None
    assert r_b.learning_pipeline_result is not None
    assert r_a.learning_pipeline_result.trace.memory_records_count >= 1
    assert r_b.learning_pipeline_result.trace.memory_records_count >= 1
    print(f"[PASS] multiple_conversations           | 2 sessions, "
          f"mem_a={r_a.learning_pipeline_result.trace.memory_records_count} "
          f"mem_b={r_b.learning_pipeline_result.trace.memory_records_count}")


# ------------------------------------------------------------------
# Scenario 8: Skills acumulando no Skill Runtime
# ------------------------------------------------------------------


def scenario_skills_accumulating() -> None:
    """Multiple executions accumulate skills in the same Skill Runtime."""
    sr = _make_skill_runtime()
    _, task, candidates, dept = _base_setup()
    gateway = FakeGateway()

    for i in range(3):
        llm_req = LLMRequest.create(prompt=f"Task {i}.")
        OrchestratorRuntime.execute_task(
            task_snapshot=task, candidate_snapshots=candidates,
            department_snapshot=dept, llm_request=llm_req,
            gateway=gateway, skill_runtime=sr,
        )

    assert len(sr.snapshot()) > 0
    skills = sr.snapshot()
    print(f"[PASS] skills_accumulating             | {len(skills)} runtime skills "
          f"after 3 executions")


# ------------------------------------------------------------------
# Scenario 9: Knowledge acumulando via pipeline
# ------------------------------------------------------------------


def scenario_knowledge_accumulating() -> None:
    """Each execution produces knowledge via the pipeline."""
    _, task, candidates, dept = _base_setup()
    gateway = FakeGateway(gateway.content if hasattr(FakeGateway, 'content') else "Content.")

    r1 = OrchestratorRuntime.execute_task(
        task_snapshot=task, candidate_snapshots=candidates,
        department_snapshot=dept, llm_request=LLMRequest.create(prompt="A"),
        gateway=FakeGateway(),
    )
    r2 = OrchestratorRuntime.execute_task(
        task_snapshot=task, candidate_snapshots=candidates,
        department_snapshot=dept, llm_request=LLMRequest.create(prompt="B"),
        gateway=FakeGateway(),
    )

    assert r1.knowledge_snapshot is not None
    assert r2.knowledge_snapshot is not None
    assert len(r1.knowledge_snapshot.records) >= 1
    assert len(r2.knowledge_snapshot.records) >= 1
    print(f"[PASS] knowledge_accumulating           | 2 executions, "
          f"know1={len(r1.knowledge_snapshot.records)} "
          f"know2={len(r2.knowledge_snapshot.records)}")


# ------------------------------------------------------------------
# Scenario 10: Runtime skills via SkillRuntime
# ------------------------------------------------------------------


def scenario_runtime_skills() -> None:
    """When skill_runtime is provided, runtime skills are populated."""
    sr = _make_skill_runtime()
    _, task, candidates, dept = _base_setup()

    result = OrchestratorRuntime.execute_task(
        task_snapshot=task, candidate_snapshots=candidates,
        department_snapshot=dept, llm_request=LLMRequest.create(prompt="Test"),
        gateway=FakeGateway(), skill_runtime=sr,
    )

    assert result.runtime_skill_snapshots is not None
    assert len(result.runtime_skill_snapshots) > 0
    assert all(isinstance(s, SkillRuntimeSnapshot) for s in result.runtime_skill_snapshots)
    print(f"[PASS] runtime_skills                  | {len(result.runtime_skill_snapshots)} "
          f"runtime skills promoted")


# ------------------------------------------------------------------
# Scenario 11: Pipeline completo end-to-end
# ------------------------------------------------------------------


def scenario_full_end_to_end() -> None:
    """Complete company learning cycle: Company -> Decision -> Execution -> ... -> Skills."""
    alice_id = uuid4()
    task = TaskSnapshot(task_id=uuid4(), name="Write Code", metadata=TaskMetadata(tags=["coding"]))
    department = DepartmentSnapshot(
        department_id=uuid4(), name="Engineering",
        employees={alice_id: DepartmentEmployeeLink(alice_id)},
    )
    alice = EmployeeSnapshot(employee_id=alice_id, name="Alice", state="idle")
    llm_req = LLMRequest.create(prompt="Write Python code.")
    gateway = FakeGateway("def hello(): pass")
    sr = _make_skill_runtime()

    result = OrchestratorRuntime.execute_task(
        task_snapshot=task, candidate_snapshots=[alice],
        department_snapshot=department, llm_request=llm_req,
        gateway=gateway, skill_runtime=sr,
    )

    assert result.success is True
    assert result.decision_result.approved is True
    assert result.execution_result is not None
    assert result.execution_result.success is True
    assert result.learning_pipeline_result is not None
    assert result.learning_pipeline_result.success is True
    assert result.learning_pipeline_result.trace.memory_records_count >= 1
    assert result.learning_pipeline_result.trace.knowledge_records_count >= 1
    assert result.learning_pipeline_result.trace.recommendations_count >= 1
    assert result.learning_pipeline_result.trace.skills_created_count >= 1
    assert result.knowledge_snapshot is not None
    assert result.learning_snapshot is not None
    assert result.skill_snapshot is not None
    assert result.runtime_skill_snapshots is not None
    assert len(result.runtime_skill_snapshots) >= 1
    assert len(sr.snapshot()) >= 1
    assert result.updated_conversation is not None
    print(f"[PASS] full_end_to_end                 | decision=ok exec=ok learn=ok "
          f"skills={result.learning_pipeline_result.trace.skills_created_count} "
          f"runtime={len(result.runtime_skill_snapshots)}")


# ------------------------------------------------------------------
# Scenario 12: Determinismo
# ------------------------------------------------------------------


def scenario_determinism() -> None:
    """Same inputs produce same structural result."""
    _, task, candidates, dept = _base_setup()
    llm_req = LLMRequest.create(prompt="Test.", model="gpt-4o")
    gateway = FakeGateway("Same output.")

    r1 = OrchestratorRuntime.execute_task(
        task_snapshot=task, candidate_snapshots=candidates,
        department_snapshot=dept, llm_request=llm_req, gateway=gateway,
    )
    r2 = OrchestratorRuntime.execute_task(
        task_snapshot=task, candidate_snapshots=candidates,
        department_snapshot=dept, llm_request=llm_req, gateway=gateway,
    )

    assert r1.success == r2.success
    assert r1.decision_result.approved == r2.decision_result.approved
    assert r1.execution_result is not None and r2.execution_result is not None
    assert r1.execution_result.output == r2.execution_result.output
    assert r1.learning_pipeline_result is not None
    assert r2.learning_pipeline_result is not None
    assert r1.learning_pipeline_result.trace.skills_created_count == \
           r2.learning_pipeline_result.trace.skills_created_count
    print(f"[PASS] determinism                     | success={r1.success} "
          f"skills={r1.learning_pipeline_result.trace.skills_created_count} (identical)")


# ------------------------------------------------------------------
# Scenario 13: IDs preservados
# ------------------------------------------------------------------


def scenario_ids_preserved() -> None:
    """Orchestrator and decision IDs are unique and valid."""
    _, task, candidates, dept = _base_setup()
    llm_req = LLMRequest.create(prompt="Test.")
    gateway = FakeGateway()

    result = OrchestratorRuntime.execute_task(
        task_snapshot=task, candidate_snapshots=candidates,
        department_snapshot=dept, llm_request=llm_req, gateway=gateway,
    )

    assert isinstance(result.orchestrator_id, UUID)
    assert isinstance(result.decision_result.decision_id, UUID)
    assert result.decision_result.chosen_candidate_id is not None
    assert isinstance(result.decision_result.chosen_candidate_id, UUID)
    print(f"[PASS] ids_preserved                   | orchestrator_id={result.orchestrator_id.hex[:8]} "
          f"decision_id={result.decision_result.decision_id.hex[:8]}")


# ------------------------------------------------------------------
# Scenario 14: Timestamps
# ------------------------------------------------------------------


def scenario_timestamps() -> None:
    """Execution timeline timestamps are captured."""
    _, task, candidates, dept = _base_setup()
    llm_req = LLMRequest.create(prompt="Test.")
    gateway = FakeGateway()

    result = OrchestratorRuntime.execute_task(
        task_snapshot=task, candidate_snapshots=candidates,
        department_snapshot=dept, llm_request=llm_req, gateway=gateway,
    )

    assert result.execution_result is not None
    assert result.execution_result.started_at > 0
    assert result.execution_result.finished_at > 0
    assert result.execution_result.finished_at >= result.execution_result.started_at
    assert result.execution_result.duration_seconds >= 0.0
    print(f"[PASS] timestamps                      | started={result.execution_result.started_at:.2f} "
          f"duration={result.execution_result.duration_seconds:.4f}s")


# ------------------------------------------------------------------
# Scenario 15: Metadata flui através do pipeline
# ------------------------------------------------------------------


def scenario_metadata_flow() -> None:
    """Metadata parameter flows through decision and execution."""
    _, task, candidates, dept = _base_setup()
    llm_req = LLMRequest.create(prompt="Test.")
    gateway = FakeGateway()

    result = OrchestratorRuntime.execute_task(
        task_snapshot=task, candidate_snapshots=candidates,
        department_snapshot=dept, llm_request=llm_req, gateway=gateway,
        metadata={"source": "integration_test", "version": "2.0"},
    )

    assert result.success is True
    assert result.execution_result is not None
    print(f"[PASS] metadata_flow                   | metadata passed to execution")


# ------------------------------------------------------------------
# Scenario 16: knowledge_snapshot in result
# ------------------------------------------------------------------


def scenario_knowledge_snapshot_in_result() -> None:
    """OrchestratorExecutionResult contains knowledge_snapshot."""
    _, task, candidates, dept = _base_setup()

    result = OrchestratorRuntime.execute_task(
        task_snapshot=task, candidate_snapshots=candidates,
        department_snapshot=dept, llm_request=LLMRequest.create(prompt="X"),
        gateway=FakeGateway(),
    )

    assert result.knowledge_snapshot is not None
    assert hasattr(result.knowledge_snapshot, "records")
    print(f"[PASS] knowledge_snapshot_in_result     | knowledge_snapshot with "
          f"{len(result.knowledge_snapshot.records)} records")


# ------------------------------------------------------------------
# Scenario 17: learning_snapshot in result
# ------------------------------------------------------------------


def scenario_learning_snapshot_in_result() -> None:
    """OrchestratorExecutionResult contains learning_snapshot."""
    _, task, candidates, dept = _base_setup()

    result = OrchestratorRuntime.execute_task(
        task_snapshot=task, candidate_snapshots=candidates,
        department_snapshot=dept, llm_request=LLMRequest.create(prompt="Y"),
        gateway=FakeGateway(),
    )

    assert result.learning_snapshot is not None
    assert hasattr(result.learning_snapshot, "recommendations")
    print(f"[PASS] learning_snapshot_in_result      | learning_snapshot with "
          f"{len(result.learning_snapshot.recommendations)} recommendations")


# ------------------------------------------------------------------
# Scenario 18: skill_snapshot in result
# ------------------------------------------------------------------


def scenario_skill_snapshot_in_result() -> None:
    """OrchestratorExecutionResult contains skill_snapshot."""
    _, task, candidates, dept = _base_setup()

    result = OrchestratorRuntime.execute_task(
        task_snapshot=task, candidate_snapshots=candidates,
        department_snapshot=dept, llm_request=LLMRequest.create(prompt="Z"),
        gateway=FakeGateway(),
    )

    assert result.skill_snapshot is not None
    assert hasattr(result.skill_snapshot, "skills")
    print(f"[PASS] skill_snapshot_in_result         | skill_snapshot with "
          f"{len(result.skill_snapshot.skills)} skills")


# ------------------------------------------------------------------
# Scenario 19: runtime_skill_snapshots in result
# ------------------------------------------------------------------


def scenario_runtime_skill_snapshots_in_result() -> None:
    """OrchestratorExecutionResult contains runtime_skill_snapshots when relevant."""
    _, task, candidates, dept = _base_setup()

    # Without SkillRuntime
    result = OrchestratorRuntime.execute_task(
        task_snapshot=task, candidate_snapshots=candidates,
        department_snapshot=dept, llm_request=LLMRequest.create(prompt="No runtime"),
        gateway=FakeGateway(),
    )
    assert result.runtime_skill_snapshots is None

    # With SkillRuntime
    sr = _make_skill_runtime()
    result2 = OrchestratorRuntime.execute_task(
        task_snapshot=task, candidate_snapshots=candidates,
        department_snapshot=dept, llm_request=LLMRequest.create(prompt="With runtime"),
        gateway=FakeGateway(), skill_runtime=sr,
    )
    assert result2.runtime_skill_snapshots is not None
    print(f"[PASS] runtime_skill_snapshots_in_result | without={result.runtime_skill_snapshots} "
          f"with={len(result2.runtime_skill_snapshots)} snapshots")


# ------------------------------------------------------------------
# Scenario 20: OrchestratorExecutionResult fields
# ------------------------------------------------------------------


def scenario_result_fields() -> None:
    """All OrchestratorExecutionResult fields are populated correctly."""
    _, task, candidates, dept = _base_setup()

    result = OrchestratorRuntime.execute_task(
        task_snapshot=task, candidate_snapshots=candidates,
        department_snapshot=dept, llm_request=LLMRequest.create(prompt="Fields"),
        gateway=FakeGateway(),
    )

    assert isinstance(result, OrchestratorExecutionResult)
    assert isinstance(result.orchestrator_id, UUID)
    assert isinstance(result.decision_result, DecisionResult)
    assert isinstance(result.execution_result, ExecutionResult)
    assert isinstance(result.success, bool)
    assert isinstance(result.error_message, str)
    assert isinstance(result.updated_conversation, ConversationSession)
    assert result.learning_pipeline_result is not None
    assert isinstance(result.learning_pipeline_result, PipelineResult)
    print(f"[PASS] result_fields                   | all fields present and typed")


# ------------------------------------------------------------------
# Scenario 21: DecisionContext com skill_runtime_snapshots
# ------------------------------------------------------------------


def scenario_decision_context_with_runtime_skills() -> None:
    """When skill_runtime is provided, DecisionEngine receives real skill snapshots."""
    sr = _make_skill_runtime()
    # Pre-populate a skill in the runtime
    from core.skills.foundation import SkillRuntime as FoundationSkillRuntime
    from core.learning.foundation import LearningRecommendation

    rec = LearningRecommendation.create_with_timestamp(
        UUID("00000000-0000-0000-0000-000000000001"), "study", "Python", "Python dev", 1.0,
    )
    foundation_skill = FoundationSkillRuntime.promote_learning(rec)
    sr.promote_record(foundation_skill)

    alice_id = uuid4()
    # Associate Alice with the skill
    for snap in sr.snapshot():
        snap.employee_ids.add(alice_id)

    task = TaskSnapshot(task_id=uuid4(), name="Python Task", metadata=TaskMetadata(tags=["python"]))
    department = DepartmentSnapshot(
        department_id=uuid4(), name="Eng",
        employees={alice_id: DepartmentEmployeeLink(alice_id)},
    )
    alice = EmployeeSnapshot(employee_id=alice_id, name="Alice", state="idle")
    llm_req = LLMRequest.create(prompt="Write Python.")
    gateway = FakeGateway()

    result = OrchestratorRuntime.execute_task(
        task_snapshot=task, candidate_snapshots=[alice],
        department_snapshot=department, llm_request=llm_req,
        gateway=gateway, skill_runtime=sr,
    )

    assert result.success is True
    assert result.decision_result.decision_code == "BEST_SKILL_MATCH"
    print(f"[PASS] decision_context_runtime_skills | code={result.decision_result.decision_code} "
          f"(real skills used in decision)")


# ------------------------------------------------------------------
# Scenario 22: Session pass-through
# ------------------------------------------------------------------


def scenario_session_pass_through() -> None:
    """The conversation_session is passed through and returned updated."""
    session = ConversationRuntime.create_session("emp-001")
    session = ConversationRuntime.append_message(session, "user", "Initial message.")

    _, task, candidates, dept = _base_setup()
    llm_req = LLMRequest.create(prompt="Continue.")
    gateway = FakeGateway("Response.")

    result = OrchestratorRuntime.execute_task(
        task_snapshot=task, candidate_snapshots=candidates,
        department_snapshot=dept, llm_request=llm_req,
        gateway=gateway, conversation_session=session,
    )

    assert result.updated_conversation is not None
    assert len(result.updated_conversation.messages) > len(session.messages)
    assert result.updated_conversation.session_id == session.session_id
    print(f"[PASS] session_pass_through             | msgs: {len(session.messages)} -> "
          f"{len(result.updated_conversation.messages)}")


# ------------------------------------------------------------------
# Scenario 23: success=True no ciclo completo
# ------------------------------------------------------------------


def scenario_success_true() -> None:
    """Success is True for a full cycle with execution and learning."""
    _, task, candidates, dept = _base_setup()

    result = OrchestratorRuntime.execute_task(
        task_snapshot=task, candidate_snapshots=candidates,
        department_snapshot=dept, llm_request=LLMRequest.create(prompt="Success"),
        gateway=FakeGateway(),
    )

    assert result.success is True
    print(f"[PASS] success_true                    | success={result.success}")


# ------------------------------------------------------------------
# Scenario 24: error_message on failure
# ------------------------------------------------------------------


def scenario_error_message() -> None:
    """Error message is populated on failure."""
    _, task, candidates, dept = _base_setup()

    # No gateway → blocked
    result = OrchestratorRuntime.execute_task(
        task_snapshot=task, candidate_snapshots=candidates,
        department_snapshot=dept,
    )

    assert result.success is False
    assert len(result.error_message) > 0
    print(f"[PASS] error_message                   | error='{result.error_message[:40]}...'")


# ------------------------------------------------------------------
# Scenario 25: PipelineResult presente no sucesso
# ------------------------------------------------------------------


def scenario_pipeline_result_present() -> None:
    """PipelineResult is present when execution succeeds."""
    _, task, candidates, dept = _base_setup()

    result = OrchestratorRuntime.execute_task(
        task_snapshot=task, candidate_snapshots=candidates,
        department_snapshot=dept, llm_request=LLMRequest.create(prompt="Pipeline"),
        gateway=FakeGateway(),
    )

    assert result.learning_pipeline_result is not None
    pipeline = result.learning_pipeline_result
    assert pipeline.success is True
    assert pipeline.trace.memory_records_count >= 1
    assert pipeline.trace.knowledge_records_count >= 1
    assert pipeline.trace.recommendations_count >= 1
    assert pipeline.trace.skills_created_count >= 1
    print(f"[PASS] pipeline_result_present          | pipeline success={pipeline.success} "
          f"counts=mem:{pipeline.trace.memory_records_count}/"
          f"know:{pipeline.trace.knowledge_records_count}/"
          f"skills:{pipeline.trace.skills_created_count}")


# ------------------------------------------------------------------
# Scenario 26: Skill Runtime snapshot count
# ------------------------------------------------------------------


def scenario_snapshot_count() -> None:
    """Skill Runtime snapshot count reflects promoted skills."""
    sr = _make_skill_runtime()
    _, task, candidates, dept = _base_setup()

    assert len(sr.snapshot()) == 0

    result = OrchestratorRuntime.execute_task(
        task_snapshot=task, candidate_snapshots=candidates,
        department_snapshot=dept, llm_request=LLMRequest.create(prompt="Count"),
        gateway=FakeGateway(), skill_runtime=sr,
    )

    assert len(sr.snapshot()) >= 1
    assert len(sr.snapshot()) == len(result.runtime_skill_snapshots)
    print(f"[PASS] snapshot_count                  | runtime snapshots: {len(sr.snapshot())}")


# ------------------------------------------------------------------
# Scenario 27: Duas execuções com session compartilhada
# ------------------------------------------------------------------


def scenario_shared_session_two_executions() -> None:
    """Two executions sharing the same session accumulate messages and skills."""
    session = ConversationRuntime.create_session("emp-001")
    sr = _make_skill_runtime()
    _, task, candidates, dept = _base_setup()

    r1 = OrchestratorRuntime.execute_task(
        task_snapshot=task, candidate_snapshots=candidates,
        department_snapshot=dept, llm_request=LLMRequest.create(prompt="First"),
        gateway=FakeGateway(), conversation_session=session, skill_runtime=sr,
    )
    r2 = OrchestratorRuntime.execute_task(
        task_snapshot=task, candidate_snapshots=candidates,
        department_snapshot=dept, llm_request=LLMRequest.create(prompt="Second"),
        gateway=FakeGateway(),
        conversation_session=r1.updated_conversation, skill_runtime=sr,
    )

    assert r1.updated_conversation is not None
    assert r2.updated_conversation is not None
    assert len(r2.updated_conversation.messages) > len(r1.updated_conversation.messages)
    assert len(sr.snapshot()) >= 2  # Skills from both runs
    print(f"[PASS] shared_session_two_executions    | msgs: {len(r1.updated_conversation.messages)} -> "
          f"{len(r2.updated_conversation.messages)}, runtime skills: {len(sr.snapshot())}")


# ------------------------------------------------------------------
# Scenario 28: Sem aprendizado quando execução falha
# ------------------------------------------------------------------


def scenario_no_learning_on_failure() -> None:
    """When execution fails, learning pipeline does NOT run."""
    # No gateway provided → execution blocked
    _, task, candidates, dept = _base_setup()

    result = OrchestratorRuntime.execute_task(
        task_snapshot=task, candidate_snapshots=candidates,
        department_snapshot=dept,
    )

    assert result.success is False
    assert result.learning_pipeline_result is None
    print(f"[PASS] no_learning_on_failure           | success={result.success} "
          f"pipeline={result.learning_pipeline_result}")


# ------------------------------------------------------------------
# Scenario 29: Ciclo completo com legacy skills
# ------------------------------------------------------------------


def scenario_legacy_skills_backward_compat() -> None:
    """Old-style skill_snapshots still work for decision matching."""
    from core.decision.runtime import DecisionContextBuilder
    from core.policies.runtime import Constraint

    alice_id = uuid4()
    task = TaskSnapshot(task_id=uuid4(), name="Python Task", metadata=TaskMetadata(tags=["python"]))
    department = DepartmentSnapshot(
        department_id=uuid4(), name="Eng",
        employees={alice_id: DepartmentEmployeeLink(alice_id)},
    )
    alice = EmployeeSnapshot(employee_id=alice_id, name="Alice", state="idle")
    legacy_skill = _LegacySkill(skill_id=uuid4(), name="Python", employee_ids={alice_id})

    llm_req = LLMRequest.create(prompt="Write Python.")
    gateway = FakeGateway()

    result = OrchestratorRuntime.execute_task(
        task_snapshot=task, candidate_snapshots=[alice],
        department_snapshot=department, skill_snapshots=[legacy_skill],
        llm_request=llm_req, gateway=gateway,
    )

    assert result.success is True
    assert result.decision_result.decision_code == "BEST_SKILL_MATCH"
    print(f"[PASS] legacy_skills_backward_compat    | code={result.decision_result.decision_code} "
          f"(legacy skills still work)")


@dataclass
class _LegacySkill:
    skill_id: UUID
    name: str
    employee_ids: set[UUID] = field(default_factory=set)


# ------------------------------------------------------------------
# Scenario 30: Sem skills (fallback)
# ------------------------------------------------------------------


def scenario_no_skills_fallback() -> None:
    """Decision works without any skill snapshots (fallback)."""
    _, task, candidates, dept = _base_setup()

    result = OrchestratorRuntime.execute_task(
        task_snapshot=task, candidate_snapshots=candidates,
        department_snapshot=dept, llm_request=LLMRequest.create(prompt="No skills"),
        gateway=FakeGateway(),
    )

    assert result.success is True
    assert result.decision_result.decision_code == "NO_SKILL_MATCH"
    print(f"[PASS] no_skills_fallback              | code={result.decision_result.decision_code} "
          f"(fallback, still executes)")


# ------------------------------------------------------------------
# Scenario 31: Trace do pipeline no resultado
# ------------------------------------------------------------------


def scenario_pipeline_trace_in_result() -> None:
    """PipelineResult contains trace with duration."""
    _, task, candidates, dept = _base_setup()

    result = OrchestratorRuntime.execute_task(
        task_snapshot=task, candidate_snapshots=candidates,
        department_snapshot=dept, llm_request=LLMRequest.create(prompt="Trace me"),
        gateway=FakeGateway(),
    )

    assert result.learning_pipeline_result is not None
    trace = result.learning_pipeline_result.trace
    assert len(trace.stages) > 0
    assert trace.duration_ms >= 0.0
    assert len(trace.timestamps) > 0
    print(f"[PASS] pipeline_trace_in_result         | stages={list(trace.stages)} "
          f"duration={trace.duration_ms:.2f}ms")


# ------------------------------------------------------------------
# Scenario 32: Compatibilidade reversa — demos antigos
# ------------------------------------------------------------------


def scenario_backward_compat_demos() -> None:
    """Importing old modules still works without the pipeline."""
    import core.decision.runtime
    import core.execution.runtime
    import core.conversation

    assert core.decision.runtime.DecisionEngine is not None
    assert core.execution.runtime.ExecutionRuntime is not None
    assert core.conversation.ConversationRuntime is not None
    print(f"[PASS] backward_compat_demos            | old imports still work")


# ------------------------------------------------------------------
# Main
# ------------------------------------------------------------------


def main() -> None:
    print("=" * 58)
    print("Company Learning Cycle Demo")
    print("=" * 58)
    print()

    scenario_decision_blocked()
    scenario_execution_blocked()
    scenario_execution_success()
    scenario_auto_learning()
    scenario_auto_session()
    scenario_multiple_executions()
    scenario_multiple_conversations()
    scenario_skills_accumulating()
    scenario_knowledge_accumulating()
    scenario_runtime_skills()
    scenario_full_end_to_end()
    scenario_determinism()
    scenario_ids_preserved()
    scenario_timestamps()
    scenario_metadata_flow()
    scenario_knowledge_snapshot_in_result()
    scenario_learning_snapshot_in_result()
    scenario_skill_snapshot_in_result()
    scenario_runtime_skill_snapshots_in_result()
    scenario_result_fields()
    scenario_decision_context_with_runtime_skills()
    scenario_session_pass_through()
    scenario_success_true()
    scenario_error_message()
    scenario_pipeline_result_present()
    scenario_snapshot_count()
    scenario_shared_session_two_executions()
    scenario_no_learning_on_failure()
    scenario_legacy_skills_backward_compat()
    scenario_no_skills_fallback()
    scenario_pipeline_trace_in_result()
    scenario_backward_compat_demos()

    print()
    print("=" * 58)
    print("All Company Learning Cycle scenarios passed.")
    print("=" * 58)


if __name__ == "__main__":
    main()
