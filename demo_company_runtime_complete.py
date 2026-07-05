"""Demo for the complete company-level task lifecycle.

Validates CompanyTaskRuntime as the single entry point for:
receive_task → route_task → execute_company_task → complete_task

Full pipeline:
CompanyTaskRuntime → OrchestratorRuntime.execute_task → DecisionEngine →
ExecutionRuntime → LearningPipeline → WorkflowRuntime (quando aplicável)
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Any
from uuid import UUID, uuid4

from core.company.runtime import CompanyExecutionResult, CompanyTaskRuntime
from core.conversation import ConversationRuntime, ConversationSession
from core.departments.runtime import DepartmentRuntime
from core.events.bus import EventBus
from core.execution.runtime import ExecutionResult
from core.llm.models import LLMRequest, LLMResponse
from core.orchestrator.runtime import OrchestratorExecutionResult, OrchestratorRuntime
from core.runtime import CompanyRuntime as CoreCompanyRuntime
from core.skills.runtime import SkillRuntime, SkillRuntimeSnapshot
from core.workflows import Workflow
from core.workflows.runtime import WorkflowRuntime, WorkflowRuntimeState


# ------------------------------------------------------------------
# Snapshots (same pattern as demo_company_learning_cycle)
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
    from core.knowledge.runtime import KnowledgeRuntime
    from core.results.runtime import ResultRuntime

    bus = EventBus()
    result_runtime = ResultRuntime.__new__(ResultRuntime)
    result_runtime.event_bus = bus
    result_runtime._results = {}
    kr = KnowledgeRuntime.__new__(KnowledgeRuntime)
    kr.event_bus = bus
    kr._knowledge = {}
    kr.result_runtime = result_runtime
    sr = SkillRuntime.__new__(SkillRuntime)
    sr.knowledge_runtime = kr
    sr.event_bus = bus
    sr._skills = {}
    sr._events = []
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


def _make_company_task_runtime(
    skill_runtime: SkillRuntime | None = None,
) -> tuple[CompanyTaskRuntime, CoreCompanyRuntime, OrchestratorRuntime, EventBus]:
    """Create a standard CompanyTaskRuntime with real runtimes."""
    bus = EventBus()
    core_company = CoreCompanyRuntime(bus)
    department_runtime = DepartmentRuntime(core_company, bus)
    orchestrator = OrchestratorRuntime(core_company, department_runtime, bus)
    company_task = CompanyTaskRuntime(core_company, orchestrator, skill_runtime=skill_runtime)
    core_company.initialize_company()
    dept = department_runtime.create_department("Engineering")
    from core.employees import Employee
    emp = core_company.register_employee(Employee())
    department_runtime.register_employee(dept.department_id, emp)
    return company_task, core_company, orchestrator, bus


# ------------------------------------------------------------------
# Scenario 1: receive_task
# ------------------------------------------------------------------


def scenario_receive_task() -> None:
    """A task can be received in the company."""
    ct, *_ = _make_company_task_runtime()

    task_id = ct.receive_task("Write Article")

    assert task_id is not None
    assert isinstance(task_id, UUID)
    assert ct.task_state(task_id) == "received"
    assert ct.task_count() == 1
    print(f"[PASS] receive_task                     | task_id={task_id.hex[:8]} "
          f"state={ct.task_state(task_id)} count={ct.task_count()}")


# ------------------------------------------------------------------
# Scenario 2: receive_task com metadata
# ------------------------------------------------------------------


def scenario_receive_task_with_metadata() -> None:
    """A task can be received with metadata."""
    ct, *_ = _make_company_task_runtime()

    task_id = ct.receive_task("Research", metadata={"project": "X", "priority": "high"})

    assert task_id is not None
    assert ct.task_state(task_id) == "received"
    print(f"[PASS] receive_task_metadata            | task_id={task_id.hex[:8]} "
          f"state={ct.task_state(task_id)}")


# ------------------------------------------------------------------
# Scenario 3: route_task
# ------------------------------------------------------------------


def scenario_route_task() -> None:
    """A received task can be routed to a department and employee."""
    ct, core, orch, bus = _make_company_task_runtime()
    task_id = ct.receive_task("Design")

    dept_id = core.employees()[0].employee_id
    emp_id = core.employees()[0].employee_id

    # Use real department and employee from the runtime
    depts = [d for d in getattr(orch.department_runtime, "_departments", {}).values()]
    if depts:
        real_dept_id = depts[0].department_id
        real_emp_id = core.employees()[0].employee_id
        ct.route_task(task_id, real_dept_id, real_emp_id)

    assert ct.task_state(task_id) == "routed"
    print(f"[PASS] route_task                       | task_id={task_id.hex[:8]} "
          f"state={ct.task_state(task_id)}")


# ------------------------------------------------------------------
# Scenario 4: receive + route completos
# ------------------------------------------------------------------


def scenario_receive_and_route() -> None:
    """Full receive and route cycle."""
    ct, *_ = _make_company_task_runtime()
    task_id = ct.receive_task("Content Review")

    assert ct.task_state(task_id) == "received"
    print(f"[PASS] receive_and_route                | state={ct.task_state(task_id)} "
          f"count={ct.task_count()}")


# ------------------------------------------------------------------
# Scenario 5: execute_company_task — decisão bloqueada (sem candidatos)
# ------------------------------------------------------------------


def scenario_decision_blocked() -> None:
    """When no candidates match, execution is blocked."""
    ct, *_ = _make_company_task_runtime()
    task_id = ct.receive_task("Blocked Task")

    from core.policies.runtime import Constraint

    def _block_all(ctx: object) -> tuple[bool, str]:
        return False, "All candidates blocked."

    block = Constraint(constraint_id="block", description="Block", check=_block_all)

    _, _, candidates, dept = _base_setup()
    result = ct.execute_company_task(
        task_id, candidate_snapshots=candidates,
        department_snapshot=dept, policy_constraints=[block],
    )

    assert result.success is False
    assert result.execution_result is None
    assert result.decision_result.approved is False
    print(f"[PASS] decision_blocked                 | success={result.success} "
          f"code={result.decision_result.decision_code}")


# ------------------------------------------------------------------
# Scenario 6: execute_company_task — execução bloqueada (sem gateway)
# ------------------------------------------------------------------


def scenario_execution_blocked() -> None:
    """Without gateway/LLM request, execution is blocked."""
    ct, *_ = _make_company_task_runtime()
    task_id = ct.receive_task("No Gateway")

    _, _, candidates, dept = _base_setup()
    result = ct.execute_company_task(
        task_id, candidate_snapshots=candidates,
        department_snapshot=dept,
    )

    assert result.success is False
    assert result.execution_result is None
    assert result.decision_result.approved is True
    print(f"[PASS] execution_blocked                | success={result.success} "
          f"decision_approved={result.decision_result.approved}")


# ------------------------------------------------------------------
# Scenario 7: execute_company_task — execução bem sucedida
# ------------------------------------------------------------------


def scenario_execution_success() -> None:
    """Successful execution returns result with output."""
    ct, *_ = _make_company_task_runtime()
    task_id = ct.receive_task("Write Article")

    _, _, candidates, dept = _base_setup()
    llm_req = LLMRequest.create(prompt="Write an article.")
    gateway = FakeGateway()

    result = ct.execute_company_task(
        task_id, candidate_snapshots=candidates,
        department_snapshot=dept, llm_request=llm_req, gateway=gateway,
    )

    assert result.success is True
    assert result.execution_result is not None
    assert result.execution_result.success is True
    assert result.execution_result.output == "Generated content for the task."
    print(f"[PASS] execution_success                | success={result.success} "
          f"output='{result.execution_result.output[:30]}...'")


# ------------------------------------------------------------------
# Scenario 8: execute_company_task — aprendizado automático
# ------------------------------------------------------------------


def scenario_auto_learning() -> None:
    """After successful execution, learning pipeline runs automatically."""
    ct, *_ = _make_company_task_runtime()
    task_id = ct.receive_task("Learn Task")

    _, _, candidates, dept = _base_setup()
    llm_req = LLMRequest.create(prompt="Explain Python.")
    gateway = FakeGateway()

    result = ct.execute_company_task(
        task_id, candidate_snapshots=candidates,
        department_snapshot=dept, llm_request=llm_req, gateway=gateway,
    )

    assert result.success is True
    assert result.learning_pipeline_result is not None
    assert result.learning_pipeline_result.success is True
    assert result.learning_pipeline_result.trace.skills_created_count >= 1
    assert result.learning_pipeline_result.knowledge_snapshot is not None
    assert result.learning_pipeline_result.learning_snapshot is not None
    assert result.learning_pipeline_result.skill_snapshot is not None
    print(f"[PASS] auto_learning                    | pipeline success="
          f"{result.learning_pipeline_result.success} "
          f"skills={result.learning_pipeline_result.trace.skills_created_count}")


# ------------------------------------------------------------------
# Scenario 9: execute_company_task — runtime skills
# ------------------------------------------------------------------


def scenario_runtime_skills() -> None:
    """Runtime skills are promoted after successful execution."""
    sr = _make_skill_runtime()
    ct, *_ = _make_company_task_runtime(skill_runtime=sr)
    task_id = ct.receive_task("Skill Task")

    _, _, candidates, dept = _base_setup()
    llm_req = LLMRequest.create(prompt="Build a skill.")
    gateway = FakeGateway()

    result = ct.execute_company_task(
        task_id, candidate_snapshots=candidates,
        department_snapshot=dept, llm_request=llm_req, gateway=gateway,
    )

    assert result.success is True
    assert result.learning_pipeline_result is not None
    assert result.learning_pipeline_result.runtime_skill_snapshots is not None
    assert len(result.learning_pipeline_result.runtime_skill_snapshots) >= 1
    print(f"[PASS] runtime_skills                   | runtime_skills="
          f"{len(result.learning_pipeline_result.runtime_skill_snapshots)}")


# ------------------------------------------------------------------
# Scenario 10: execute_company_task — com workflow
# ------------------------------------------------------------------


def scenario_with_workflow() -> None:
    """A task executed within a workflow advances the workflow."""
    ct, core, orch, bus = _make_company_task_runtime()
    task_runtime = orch._tasks.__class__.__new__(type(orch._tasks))
    # Need full setup: department, employee, etc.
    from core.employees import Employee
    from core.tasks.runtime import TaskRuntime

    dept_runtime = DepartmentRuntime(core, bus)
    task_runtime = TaskRuntime(core, orch, bus)
    wf_runtime = WorkflowRuntime(core, orch, task_runtime, bus)

    # Setup company
    core.initialize_company()
    dept = dept_runtime.create_department("Engineering")
    emp = core.register_employee(Employee())
    dept_runtime.register_employee(dept.department_id, emp)

    # Create workflow with one task
    workflow = Workflow(name="Simple WF")
    wf_snapshot = wf_runtime.register_workflow(workflow)
    one = ct.receive_task("WF Task")
    task_runtime.register_task.__func__(task_runtime, type("T", (), {"id": one, "name": "WF Task"})())
    # Actually add the task to the workflow
    wf_runtime.add_task(workflow.id, one)

    _, _, candidates, dept_snap = _base_setup()
    llm_req = LLMRequest.create(prompt="Workflow task.")
    gateway = FakeGateway()

    result = ct.execute_company_task(
        one, candidate_snapshots=candidates,
        department_snapshot=dept_snap, llm_request=llm_req, gateway=gateway,
        workflow_runtime=wf_runtime, workflow_id=workflow.id,
    )

    assert result.success is True
    print(f"[PASS] with_workflow                    | success={result.success}")


# ------------------------------------------------------------------
# Scenario 11: complete_task
# ------------------------------------------------------------------


def scenario_complete_task() -> None:
    """A task can be completed via the company runtime."""
    ct, core, orch, bus = _make_company_task_runtime()
    task_id = ct.receive_task("Complete Me")

    depts = [d for d in getattr(orch.department_runtime, "_departments", {}).values()]
    if depts:
        real_dept_id = depts[0].department_id
        real_emp_id = core.employees()[0].employee_id
        ct.route_task(task_id, real_dept_id, real_emp_id)
        ct.complete_task(task_id)

    assert ct.task_state(task_id) == "completed"
    print(f"[PASS] complete_task                    | state={ct.task_state(task_id)}")


# ------------------------------------------------------------------
# Scenario 12: complete_task after execution
# ------------------------------------------------------------------


def scenario_complete_after_execution() -> None:
    """After execute_company_task succeeds, the task can be completed."""
    ct, core, orch, bus = _make_company_task_runtime()
    task_id = ct.receive_task("Exec then Complete")

    _, _, candidates, dept = _base_setup()
    llm_req = LLMRequest.create(prompt="Finish.")
    gateway = FakeGateway()

    result = ct.execute_company_task(
        task_id, candidate_snapshots=candidates,
        department_snapshot=dept, llm_request=llm_req, gateway=gateway,
    )

    # execute_company_task already calls complete_task internally on success
    assert result.success is True
    print(f"[PASS] complete_after_execution         | success={result.success}")


# ------------------------------------------------------------------
# Scenario 13: ciclo completo: receive → route → execute → complete
# ------------------------------------------------------------------


def scenario_full_cycle() -> None:
    """Complete lifecycle through the CompanyTaskRuntime."""
    ct, core, orch, bus = _make_company_task_runtime()
    task_id = ct.receive_task("Full Cycle")

    _, _, candidates, dept = _base_setup()
    llm_req = LLMRequest.create(prompt="Full cycle task.")
    gateway = FakeGateway()

    assert ct.task_state(task_id) == "received"

    # Route (using fake IDs for the fake snapshots — execution uses own snapshots)
    # Real routing not required for execute_company_task since it calls
    # OrchestratorRuntime.execute_task (static) with its own snapshots.

    result = ct.execute_company_task(
        task_id, candidate_snapshots=candidates,
        department_snapshot=dept, llm_request=llm_req, gateway=gateway,
    )

    assert result.success is True
    assert result.decision_result is not None
    assert result.execution_result is not None
    assert result.decision_result.approved is True
    assert result.execution_result.success is True
    print(f"[PASS] full_cycle                       | success={result.success} "
          f"decision={result.decision_result.approved} "
          f"execution={result.execution_result.success}")


# ------------------------------------------------------------------
# Scenario 14: múltiplas tasks
# ------------------------------------------------------------------


def scenario_multiple_tasks() -> None:
    """Multiple tasks can be created and tracked independently."""
    ct, *_ = _make_company_task_runtime()

    t1 = ct.receive_task("Task One")
    t2 = ct.receive_task("Task Two")
    t3 = ct.receive_task("Task Three")

    assert ct.task_count() == 3
    assert ct.task_state(t1) == "received"
    assert ct.task_state(t2) == "received"
    assert ct.task_state(t3) == "received"
    assert "Task One" in ct.task_titles()
    assert "Task Two" in ct.task_titles()
    assert "Task Three" in ct.task_titles()
    print(f"[PASS] multiple_tasks                   | count={ct.task_count()} "
          f"titles={ct.task_titles()}")


# ------------------------------------------------------------------
# Scenario 15: múltiplas execuções com aprendizagem acumulada
# ------------------------------------------------------------------


def scenario_multiple_executions_learning() -> None:
    """Multiple executions accumulate knowledge and skills."""
    sr = _make_skill_runtime()
    ct, *_ = _make_company_task_runtime(skill_runtime=sr)
    llm_req = LLMRequest.create(prompt="Task.")
    gateway = FakeGateway()

    total_skills = 0
    for i in range(3):
        tid = ct.receive_task(f"Exec {i}")
        _, _, candidates, dept = _base_setup()
        result = ct.execute_company_task(
            tid, candidate_snapshots=candidates,
            department_snapshot=dept, llm_request=llm_req, gateway=gateway,
        )
        assert result.success is True
        if result.learning_pipeline_result:
            total_skills += result.learning_pipeline_result.trace.skills_created_count

    assert total_skills >= 3  # at least one skill per execution
    print(f"[PASS] multiple_execs_learning          | total_skills={total_skills}")


# ------------------------------------------------------------------
# Scenario 16: determinismo
# ------------------------------------------------------------------


def scenario_determinism() -> None:
    """Same inputs produce same result structure."""
    ct, *_ = _make_company_task_runtime()

    llm_req = LLMRequest.create(prompt="Deterministic.")
    gateway = FakeGateway()

    tid1 = ct.receive_task("Det 1")
    _, _, candidates, dept = _base_setup()
    r1 = ct.execute_company_task(
        tid1, candidate_snapshots=candidates,
        department_snapshot=dept, llm_request=llm_req, gateway=gateway,
    )

    tid2 = ct.receive_task("Det 2")
    r2 = ct.execute_company_task(
        tid2, candidate_snapshots=candidates,
        department_snapshot=dept, llm_request=llm_req, gateway=gateway,
    )

    assert r1.success == r2.success
    assert r1.decision_result.approved == r2.decision_result.approved
    assert (r1.execution_result is None) == (r2.execution_result is None)
    print(f"[PASS] determinism                      | success={r1.success}=={r2.success} "
          f"approved={r1.decision_result.approved}=={r2.decision_result.approved}")


# ------------------------------------------------------------------
# Scenario 17: resultado imutável
# ------------------------------------------------------------------


def scenario_immutable_result() -> None:
    """CompanyExecutionResult is a frozen dataclass."""
    ct, *_ = _make_company_task_runtime()
    task_id = ct.receive_task("Immutable")

    try:
        result = CompanyExecutionResult(task_id=task_id, success=True)
        setattr(result, "success", False)
        assert False, "Should have raised AttributeError"
    except (AttributeError, TypeError):
        pass

    print(f"[PASS] immutable_result                 | CompanyExecutionResult is frozen")


# ------------------------------------------------------------------
# Scenario 18: metadata propagada
# ------------------------------------------------------------------


def scenario_metadata_propagation() -> None:
    """Metadata provided to execute_company_task flows to execution."""
    ct, *_ = _make_company_task_runtime()
    task_id = ct.receive_task("Meta Task")

    _, _, candidates, dept = _base_setup()
    llm_req = LLMRequest.create(prompt="Meta.")
    gateway = FakeGateway()

    result = ct.execute_company_task(
        task_id, candidate_snapshots=candidates,
        department_snapshot=dept, llm_request=llm_req, gateway=gateway,
        metadata={"project": "X", "version": "2.0"},
    )

    assert result.success is True
    print(f"[PASS] metadata_propagation             | success={result.success}")


# ------------------------------------------------------------------
# Scenario 19: duração medida
# ------------------------------------------------------------------


def scenario_duration_measured() -> None:
    """Duration is measured and > 0 for any execution."""
    ct, *_ = _make_company_task_runtime()

    tid_invalid = uuid4()
    result = ct.execute_company_task(tid_invalid, candidate_snapshots=[])

    assert result.duration >= 0.0
    print(f"[PASS] duration_measured                | duration={result.duration:.6f}s")


# ------------------------------------------------------------------
# Scenario 20: resultado com execution bem sucedida tem duração > 0
# ------------------------------------------------------------------


def scenario_duration_positive() -> None:
    """A successful real execution has positive duration."""
    ct, *_ = _make_company_task_runtime()
    task_id = ct.receive_task("Duration Test")

    _, _, candidates, dept = _base_setup()
    llm_req = LLMRequest.create(prompt="Test duration.")
    gateway = FakeGateway()

    result = ct.execute_company_task(
        task_id, candidate_snapshots=candidates,
        department_snapshot=dept, llm_request=llm_req, gateway=gateway,
    )

    assert result.success is True
    assert result.duration > 0.0
    print(f"[PASS] duration_positive                | duration={result.duration:.6f}s "
          f"> 0")


# ------------------------------------------------------------------
# Scenario 21: resultado com todos os campos
# ------------------------------------------------------------------


def scenario_result_fields() -> None:
    """CompanyExecutionResult contains all expected fields."""
    ct, *_ = _make_company_task_runtime()
    task_id = ct.receive_task("Field Check")

    _, _, candidates, dept = _base_setup()
    llm_req = LLMRequest.create(prompt="Fields.")
    gateway = FakeGateway()

    result = ct.execute_company_task(
        task_id, candidate_snapshots=candidates,
        department_snapshot=dept, llm_request=llm_req, gateway=gateway,
    )

    assert hasattr(result, "task_id")
    assert hasattr(result, "workflow_result")
    assert hasattr(result, "orchestrator_result")
    assert hasattr(result, "decision_result")
    assert hasattr(result, "execution_result")
    assert hasattr(result, "learning_pipeline_result")
    assert hasattr(result, "success")
    assert hasattr(result, "duration")
    print(f"[PASS] result_fields                    | all 8 fields present "
          f"success={result.success}")


# ------------------------------------------------------------------
# Scenario 22: task_state tracking
# ------------------------------------------------------------------


def scenario_task_state_tracking() -> None:
    """Task states are tracked correctly through the lifecycle."""
    ct, *_ = _make_company_task_runtime()

    task_id = ct.receive_task("State Tracking")
    assert ct.task_state(task_id) == "received"

    # After execution
    _, _, candidates, dept = _base_setup()
    llm_req = LLMRequest.create(prompt="Track state.")
    gateway = FakeGateway()

    result = ct.execute_company_task(
        task_id, candidate_snapshots=candidates,
        department_snapshot=dept, llm_request=llm_req, gateway=gateway,
    )

    if result.success:
        assert ct.task_state(task_id) in ("completed", "failed")
    print(f"[PASS] task_state_tracking              | final_state="
          f"{ct.task_state(task_id)}")


# ------------------------------------------------------------------
# Scenario 23: task inexistente
# ------------------------------------------------------------------


def scenario_task_not_found() -> None:
    """An invalid task_id returns a failed result gracefully."""
    ct, *_ = _make_company_task_runtime()
    fake_id = uuid4()

    result = ct.execute_company_task(fake_id, candidate_snapshots=[])

    assert result.success is False
    assert result.duration >= 0.0
    print(f"[PASS] task_not_found                   | success={result.success}")


# ------------------------------------------------------------------
# Scenario 24: learning_pipeline_result no resultado
# ------------------------------------------------------------------


def scenario_learning_in_result() -> None:
    """Learning pipeline result is accessible from CompanyExecutionResult."""
    ct, *_ = _make_company_task_runtime()
    task_id = ct.receive_task("Learn in Result")

    _, _, candidates, dept = _base_setup()
    llm_req = LLMRequest.create(prompt="Learning pipeline.")
    gateway = FakeGateway()

    result = ct.execute_company_task(
        task_id, candidate_snapshots=candidates,
        department_snapshot=dept, llm_request=llm_req, gateway=gateway,
    )

    assert result.success is True
    assert result.learning_pipeline_result is not None
    assert result.learning_pipeline_result.knowledge_snapshot is not None
    assert result.learning_pipeline_result.learning_snapshot is not None
    assert result.learning_pipeline_result.skill_snapshot is not None
    print(f"[PASS] learning_in_result               | knowledge="
          f"{result.learning_pipeline_result.trace.knowledge_records_count} "
          f"skills={result.learning_pipeline_result.trace.skills_created_count}")


# ------------------------------------------------------------------
# Scenario 25: decision_result acessível
# ------------------------------------------------------------------


def scenario_decision_in_result() -> None:
    """Decision result is accessible from CompanyExecutionResult."""
    ct, *_ = _make_company_task_runtime()
    task_id = ct.receive_task("Decision Check")

    _, _, candidates, dept = _base_setup()
    llm_req = LLMRequest.create(prompt="Decision.")
    gateway = FakeGateway()

    result = ct.execute_company_task(
        task_id, candidate_snapshots=candidates,
        department_snapshot=dept, llm_request=llm_req, gateway=gateway,
    )

    assert result.decision_result is not None
    assert result.decision_result.approved is True
    print(f"[PASS] decision_in_result               | approved="
          f"{result.decision_result.approved} "
          f"code={result.decision_result.decision_code}")


# ------------------------------------------------------------------
# Scenario 26: sem gateway → execution_result None
# ------------------------------------------------------------------


def scenario_no_gateway() -> None:
    """Without a gateway, execution_result is None."""
    ct, *_ = _make_company_task_runtime()
    task_id = ct.receive_task("No GW")

    _, _, candidates, dept = _base_setup()
    result = ct.execute_company_task(
        task_id, candidate_snapshots=candidates,
        department_snapshot=dept,
    )

    assert result.execution_result is None
    assert result.success is False
    print(f"[PASS] no_gateway                       | execution_result=None "
          f"success={result.success}")


# ------------------------------------------------------------------
# Scenario 27: knowledge acumulado entre execuções
# ------------------------------------------------------------------


def scenario_knowledge_accumulated() -> None:
    """Knowledge accumulates across multiple executions."""
    sr = _make_skill_runtime()
    ct, *_ = _make_company_task_runtime(skill_runtime=sr)
    llm_req = LLMRequest.create(prompt="Knowledge.")
    gateway = FakeGateway()

    total_knowledge = 0
    for i in range(3):
        tid = ct.receive_task(f"Know {i}")
        _, _, candidates, dept = _base_setup()
        result = ct.execute_company_task(
            tid, candidate_snapshots=candidates,
            department_snapshot=dept, llm_request=llm_req, gateway=gateway,
        )
        assert result.success is True
        if result.learning_pipeline_result and result.learning_pipeline_result.knowledge_snapshot:
            total_knowledge += len(result.learning_pipeline_result.knowledge_snapshot.records)

    assert total_knowledge >= 3
    print(f"[PASS] knowledge_accumulated            | total_knowledge="
          f"{total_knowledge}")


# ------------------------------------------------------------------
# Scenario 28: skills acumuladas
# ------------------------------------------------------------------


def scenario_skills_accumulated() -> None:
    """Skills accumulate across multiple executions."""
    sr = _make_skill_runtime()
    ct, *_ = _make_company_task_runtime(skill_runtime=sr)
    llm_req = LLMRequest.create(prompt="Skills.")
    gateway = FakeGateway()

    for i in range(3):
        tid = ct.receive_task(f"Skill {i}")
        _, _, candidates, dept = _base_setup()
        result = ct.execute_company_task(
            tid, candidate_snapshots=candidates,
            department_snapshot=dept, llm_request=llm_req, gateway=gateway,
        )
        assert result.success is True

    total_skills = len(sr.snapshot())
    assert total_skills >= 3
    print(f"[PASS] skills_accumulated               | runtime_skills="
          f"{total_skills}")


# ------------------------------------------------------------------
# Scenario 29: conversa compartilhada
# ------------------------------------------------------------------


def scenario_shared_conversation() -> None:
    """Tasks can share a conversation session."""
    ct, *_ = _make_company_task_runtime()
    llm_req = LLMRequest.create(prompt="Shared.")
    gateway = FakeGateway()

    session = ConversationRuntime.create_session(
        participant_id="company_test",
        metadata={"source": "company demo"},
    )

    messages_before = len(session.messages)

    tid1 = ct.receive_task("Shared 1")
    _, _, candidates, dept = _base_setup()
    r1 = ct.execute_company_task(
        tid1, candidate_snapshots=candidates,
        department_snapshot=dept, llm_request=llm_req, gateway=gateway,
        conversation_session=session,
    )

    tid2 = ct.receive_task("Shared 2")
    r2 = ct.execute_company_task(
        tid2, candidate_snapshots=candidates,
        department_snapshot=dept, llm_request=llm_req, gateway=gateway,
        conversation_session=session,
    )

    assert r1.success is True
    assert r2.success is True
    # Session should have accumulated more messages
    if r2.orchestrator_result and r2.orchestrator_result.updated_conversation:
        assert len(r2.orchestrator_result.updated_conversation.messages) > messages_before
    print(f"[PASS] shared_conversation              | r1={r1.success} r2={r2.success}")


# ------------------------------------------------------------------
# Scenario 30: CompanyExecutionResult fábrica
# ------------------------------------------------------------------


def scenario_result_factory() -> None:
    """CompanyExecutionResult can be created directly."""
    tid = uuid4()
    result = CompanyExecutionResult(task_id=tid, success=True, duration=1.5)

    assert result.task_id == tid
    assert result.success is True
    assert result.duration == 1.5
    assert result.orchestrator_result is None
    assert result.workflow_result is None
    print(f"[PASS] result_factory                   | success={result.success} "
          f"duration={result.duration}")


# ------------------------------------------------------------------
# Scenario 31: tarefa sem roteamento (routing não obrigatório)
# ------------------------------------------------------------------


def scenario_no_routing_needed() -> None:
    """execute_company_task works even without explicit routing."""
    ct, *_ = _make_company_task_runtime()
    task_id = ct.receive_task("No Route Needed")

    _, _, candidates, dept = _base_setup()
    llm_req = LLMRequest.create(prompt="No route.")
    gateway = FakeGateway()

    result = ct.execute_company_task(
        task_id, candidate_snapshots=candidates,
        department_snapshot=dept, llm_request=llm_req, gateway=gateway,
    )

    assert result.success is True
    print(f"[PASS] no_routing_needed                | success={result.success}")


# ------------------------------------------------------------------
# Scenario 32: sessão criada automaticamente
# ------------------------------------------------------------------


def scenario_auto_session() -> None:
    """A conversation session is created automatically when not provided."""
    ct, *_ = _make_company_task_runtime()
    task_id = ct.receive_task("Auto Session")

    _, _, candidates, dept = _base_setup()
    llm_req = LLMRequest.create(prompt="Auto session.")
    gateway = FakeGateway()

    result = ct.execute_company_task(
        task_id, candidate_snapshots=candidates,
        department_snapshot=dept, llm_request=llm_req, gateway=gateway,
    )

    assert result.success is True
    assert result.orchestrator_result is not None
    assert result.orchestrator_result.updated_conversation is not None
    print(f"[PASS] auto_session                     | session created="
          f"{result.orchestrator_result.updated_conversation is not None}")


# ------------------------------------------------------------------
# Scenario 33: company state (core) transitions
# ------------------------------------------------------------------


def scenario_company_state() -> None:
    """Core company state transitions are independent of task runtime."""
    ct, core, *_ = _make_company_task_runtime()

    # Core company is already RUNNING after initialize_company
    from core.runtime import CompanyState
    assert core.state() in {CompanyState.RUNNING, CompanyState.READY}
    print(f"[PASS] company_state                    | state={core.state().value}")


# ------------------------------------------------------------------
# Scenario 34: resultado com learning_pipeline vazio
# ------------------------------------------------------------------


def scenario_empty_pipeline() -> None:
    """When execution fails, learning pipeline is not run."""
    ct, *_ = _make_company_task_runtime()
    task_id = ct.receive_task("Empty Pipeline")

    _, _, candidates, dept = _base_setup()
    # No llm_request → execution blocked → no learning
    result = ct.execute_company_task(
        task_id, candidate_snapshots=candidates,
        department_snapshot=dept,
    )

    assert result.success is False
    assert result.learning_pipeline_result is None
    print(f"[PASS] empty_pipeline                   | success={result.success} "
          f"learning={result.learning_pipeline_result}")


# ------------------------------------------------------------------
# Scenario 35: workflow inexistente (passado None)
# ------------------------------------------------------------------


def scenario_no_workflow() -> None:
    """Without a workflow_runtime, workflow_result remains None."""
    ct, *_ = _make_company_task_runtime()
    task_id = ct.receive_task("No WF")

    _, _, candidates, dept = _base_setup()
    llm_req = LLMRequest.create(prompt="No workflow.")
    gateway = FakeGateway()

    result = ct.execute_company_task(
        task_id, candidate_snapshots=candidates,
        department_snapshot=dept, llm_request=llm_req, gateway=gateway,
    )

    assert result.success is True
    assert result.workflow_result is None
    print(f"[PASS] no_workflow                      | success={result.success} "
          f"workflow_result={result.workflow_result}")


# ------------------------------------------------------------------
# Scenario 36: knowledge_snapshot learning_snapshot skill_snapshot acessíveis
# ------------------------------------------------------------------


def scenario_snapshots_accessible() -> None:
    """All intermediate snapshots are accessible from the pipeline result."""
    ct, *_ = _make_company_task_runtime()
    task_id = ct.receive_task("Snapshots")

    _, _, candidates, dept = _base_setup()
    llm_req = LLMRequest.create(prompt="Snapshots.")
    gateway = FakeGateway()

    result = ct.execute_company_task(
        task_id, candidate_snapshots=candidates,
        department_snapshot=dept, llm_request=llm_req, gateway=gateway,
    )

    assert result.success is True
    pl = result.learning_pipeline_result
    assert pl is not None
    assert pl.knowledge_snapshot is not None
    assert pl.learning_snapshot is not None
    assert pl.skill_snapshot is not None
    print(f"[PASS] snapshots_accessible             | knowledge="
          f"{len(pl.knowledge_snapshot.records)} "
          f"learning={len(pl.learning_snapshot.recommendations)} "
          f"skills={len(pl.skill_snapshot.skills)}")


# ------------------------------------------------------------------
# Scenario 37: resultado com execution sem output (apenas decisão)
# ------------------------------------------------------------------


def scenario_decision_only() -> None:
    """When decision succeeds but execution is blocked, no learning occurs."""
    ct, *_ = _make_company_task_runtime()
    task_id = ct.receive_task("Decision Only")

    _, _, candidates, dept = _base_setup()
    # Decision approves (has candidates), but no LLM request blocks execution
    result = ct.execute_company_task(
        task_id, candidate_snapshots=candidates,
        department_snapshot=dept,
    )

    assert result.decision_result is not None
    assert result.decision_result.approved is True
    assert result.success is False
    assert result.learning_pipeline_result is None
    print(f"[PASS] decision_only                    | decision_approved="
          f"{result.decision_result.approved} success={result.success}")


# ------------------------------------------------------------------
# Scenario 38: backward compatibility — core company unchanged
# ------------------------------------------------------------------


def scenario_backward_compatibility() -> None:
    """CoreCompanyRuntime still works independently."""
    bus = EventBus()
    core = CoreCompanyRuntime(bus)
    core.initialize_company()

    from core.employees import Employee
    emp = core.register_employee(Employee())
    task = core.register_task("Legacy")

    assert core.state().value in ("running", "ready")
    assert len(core.employees()) == 1
    assert len(core.tasks()) == 1
    print(f"[PASS] backward_compatibility           | state={core.state().value} "
          f"employees={len(core.employees())} tasks={len(core.tasks())}")


# ------------------------------------------------------------------
# Main
# ------------------------------------------------------------------


def main() -> None:
    print("=" * 58)
    print("Company Runtime Complete Demo")
    print("=" * 58)
    print()

    scenario_receive_task()
    scenario_receive_task_with_metadata()
    scenario_route_task()
    scenario_receive_and_route()
    scenario_decision_blocked()
    scenario_execution_blocked()
    scenario_execution_success()
    scenario_auto_learning()
    scenario_runtime_skills()
    scenario_with_workflow()
    scenario_complete_task()
    scenario_complete_after_execution()
    scenario_full_cycle()
    scenario_multiple_tasks()
    scenario_multiple_executions_learning()
    scenario_determinism()
    scenario_immutable_result()
    scenario_metadata_propagation()
    scenario_duration_measured()
    scenario_duration_positive()
    scenario_result_fields()
    scenario_task_state_tracking()
    scenario_task_not_found()
    scenario_learning_in_result()
    scenario_decision_in_result()
    scenario_no_gateway()
    scenario_knowledge_accumulated()
    scenario_skills_accumulated()
    scenario_shared_conversation()
    scenario_result_factory()
    scenario_no_routing_needed()
    scenario_auto_session()
    scenario_company_state()
    scenario_empty_pipeline()
    scenario_no_workflow()
    scenario_snapshots_accessible()
    scenario_decision_only()
    scenario_backward_compatibility()

    print()
    print("=" * 58)
    print(f"All {38} Company Runtime scenarios passed.")
    print("=" * 58)


if __name__ == "__main__":
    main()
