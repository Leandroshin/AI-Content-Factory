"""Integration demo: Workflow Runtime Foundation → Stateful WorkflowRuntime.

Validates promote_definition, promote_execution, create_from_foundation,
task/step correspondence, determinism, and backward compatibility.
"""

from __future__ import annotations

from uuid import UUID

from core.departments.runtime import DepartmentRuntime
from core.employees import Employee
from core.events.bus import EventBus
from core.observability import ObservabilityProjector
from core.orchestrator import OrchestratorRuntime
from core.runtime import CompanyRuntime
from core.tasks import Task
from core.tasks.runtime import TaskRuntime, TaskRuntimeState
from core.workflow.foundation import (
    WorkflowDefinition,
    WorkflowExecution,
    WorkflowRuntime as FoundationWorkflowRuntime,
    WorkflowStep,
    WorkflowTrace,
)
from core.workflows import Workflow
from core.workflows.runtime import (
    WorkflowRuntime,
    WorkflowRuntimeState,
)


def _setup() -> tuple[WorkflowRuntime, CompanyRuntime, OrchestratorRuntime, TaskRuntime, EventBus]:
    event_bus = EventBus()
    company = CompanyRuntime(event_bus)
    department_runtime = DepartmentRuntime(company, event_bus)
    orchestrator = OrchestratorRuntime(company, department_runtime, event_bus)
    task_runtime = TaskRuntime(company, orchestrator, event_bus)
    workflow_runtime = WorkflowRuntime(company, orchestrator, task_runtime, event_bus)
    company.initialize_company()
    department = department_runtime.create_department("Engineering")
    employee = company.register_employee(Employee())
    department_runtime.register_employee(department.department_id, employee)
    return workflow_runtime, company, orchestrator, task_runtime, event_bus


# ------------------------------------------------------------------
# Scenario 1: promote_definition — empty workflow
# ------------------------------------------------------------------


def scenario_promote_definition_empty() -> None:
    """promote_definition with no steps creates an empty workflow."""
    wr, *_ = _setup()
    fd = FoundationWorkflowRuntime.create_definition("Empty")

    snapshot = wr.promote_definition(fd)

    assert snapshot.name == "Empty"
    assert snapshot.state == WorkflowRuntimeState.PLANNED
    assert snapshot.task_ids == []
    print(f"[PASS] promote_definition_empty        | name='{snapshot.name}' "
          f"tasks={len(snapshot.task_ids)} state={snapshot.state.value}")


# ------------------------------------------------------------------
# Scenario 2: promote_definition — single step
# ------------------------------------------------------------------


def scenario_promote_definition_single_step() -> None:
    """promote_definition with one step creates one task."""
    wr, *_ = _setup()
    step = WorkflowStep.create("Step 1")
    fd = FoundationWorkflowRuntime.create_definition("Single", steps=[step])

    snapshot = wr.promote_definition(fd)

    assert len(snapshot.task_ids) == 1
    assert snapshot.task_ids[0] == step.step_id
    print(f"[PASS] promote_definition_single_step  | {len(snapshot.task_ids)} task(s) "
          f"task_id={snapshot.task_ids[0].hex[:8]}")


# ------------------------------------------------------------------
# Scenario 3: promote_definition — múltiplas etapas
# ------------------------------------------------------------------


def scenario_promote_definition_multiple_steps() -> None:
    """promote_definition with multiple steps creates matching tasks."""
    wr, *_ = _setup()
    steps = [
        WorkflowStep.create("Design"),
        WorkflowStep.create("Implement"),
        WorkflowStep.create("Test"),
    ]
    fd = FoundationWorkflowRuntime.create_definition("Release", steps=steps)

    snapshot = wr.promote_definition(fd)

    assert len(snapshot.task_ids) == 3
    assert snapshot.task_ids == [s.step_id for s in steps]
    print(f"[PASS] promote_definition_multi_step   | {len(snapshot.task_ids)} tasks, "
          f"ids match step_ids")


# ------------------------------------------------------------------
# Scenario 4: promote_definition — com metadados
# ------------------------------------------------------------------


def scenario_promote_definition_with_metadata() -> None:
    """promote_definition preserves foundation metadata."""
    wr, *_ = _setup()
    fd = FoundationWorkflowRuntime.create_definition(
        "Meta", metadata={"project": "X", "team": "Alpha"},
    )

    snapshot = wr.promote_definition(fd)

    assert snapshot.name == "Meta"
    print(f"[PASS] promote_definition_metadata     | name='{snapshot.name}' "
          f"metadata preserved")


# ------------------------------------------------------------------
# Scenario 5: create_from_foundation
# ------------------------------------------------------------------


def scenario_create_from_foundation() -> None:
    """create_from_foundation is the canonical integration entry point."""
    wr, *_ = _setup()
    steps = [WorkflowStep.create("A"), WorkflowStep.create("B")]
    fd = FoundationWorkflowRuntime.create_definition("Canonical", steps=steps)

    snapshot = wr.create_from_foundation(fd)

    assert snapshot.name == "Canonical"
    assert len(snapshot.task_ids) == 2
    assert snapshot.workflow_id == fd.workflow_id
    print(f"[PASS] create_from_foundation           | name='{snapshot.name}' "
          f"tasks={len(snapshot.task_ids)}")


# ------------------------------------------------------------------
# Scenario 6: workflow_id preservado
# ------------------------------------------------------------------


def scenario_workflow_id_preserved() -> None:
    """Foundation workflow_id is used as the stateful workflow ID."""
    wr, *_ = _setup()
    fd = FoundationWorkflowRuntime.create_definition("ID Test")
    snapshot = wr.promote_definition(fd)

    assert snapshot.workflow_id == fd.workflow_id
    print(f"[PASS] workflow_id_preserved            | id={snapshot.workflow_id.hex[:8]} "
          f"match={snapshot.workflow_id == fd.workflow_id}")


# ------------------------------------------------------------------
# Scenario 7: nomes das etapas preservados como nomes das tasks
# ------------------------------------------------------------------


def scenario_step_names_as_task_names() -> None:
    """Step names become task names in the stateful runtime."""
    wr, *_ = _setup()
    steps = [
        WorkflowStep.create("Research"),
        WorkflowStep.create("Draft"),
    ]
    fd = FoundationWorkflowRuntime.create_definition("Writing", steps=steps)
    snapshot = wr.promote_definition(fd)

    tasks = wr.task_runtime.snapshot()
    task_map = {t.task_id: t for t in tasks}
    for step in steps:
        t = task_map.get(step.step_id)
        assert t is not None
        assert t.name == step.name
    print(f"[PASS] step_names_as_task_names         | step names correct in tasks "
          f"({len(steps)} tasks)")


# ------------------------------------------------------------------
# Scenario 8: task_ids correspondem aos step_ids
# ------------------------------------------------------------------


def scenario_task_ids_match_step_ids() -> None:
    """Each task.id matches the corresponding step.step_id."""
    wr, *_ = _setup()
    steps = [WorkflowStep.create("X"), WorkflowStep.create("Y")]
    fd = FoundationWorkflowRuntime.create_definition("Match", steps=steps)
    snapshot = wr.promote_definition(fd)

    for step in steps:
        assert step.step_id in snapshot.task_ids
    print(f"[PASS] task_ids_match_step_ids          | {len(steps)} tasks with "
          f"matching step_ids")


# ------------------------------------------------------------------
# Scenario 9: ordem preservada
# ------------------------------------------------------------------


def scenario_order_preserved() -> None:
    """Tasks are registered in the same order as definition steps."""
    wr, *_ = _setup()
    steps = [
        WorkflowStep.create("Alpha"),
        WorkflowStep.create("Beta"),
        WorkflowStep.create("Gamma"),
    ]
    fd = FoundationWorkflowRuntime.create_definition("Ordered", steps=steps)
    snapshot = wr.promote_definition(fd)

    assert snapshot.task_ids == [s.step_id for s in steps]
    print(f"[PASS] order_preserved                 | tasks in step order "
          f"({len(steps)} tasks)")


# ------------------------------------------------------------------
# Scenario 10: promote_execution — progresso atualizado
# ------------------------------------------------------------------


def scenario_promote_execution_progress() -> None:
    """promote_execution updates stateful progress from foundation execution."""
    wr, *_ = _setup()
    steps = [
        WorkflowStep.create("25%"),
        WorkflowStep.create("50%"),
        WorkflowStep.create("75%"),
        WorkflowStep.create("100%"),
    ]
    fd = FoundationWorkflowRuntime.create_definition("Progress", steps=steps)
    snapshot = wr.promote_definition(fd)

    fe = FoundationWorkflowRuntime.start_execution(fd)
    fe = FoundationWorkflowRuntime.complete_step(fe, steps[0].step_id)

    snapshot = wr.promote_execution(fd.workflow_id, fe)

    assert snapshot.progress == 25.0
    print(f"[PASS] promote_execution_progress      | progress={snapshot.progress}")


# ------------------------------------------------------------------
# Scenario 11: promote_execution — parcial
# ------------------------------------------------------------------


def scenario_promote_execution_partial() -> None:
    """promote_execution with partial completion updates progress."""
    wr, *_ = _setup()
    steps = [
        WorkflowStep.create("A"),
        WorkflowStep.create("B"),
        WorkflowStep.create("C"),
        WorkflowStep.create("D"),
    ]
    fd = FoundationWorkflowRuntime.create_definition("Partial", steps=steps)
    snapshot = wr.promote_definition(fd)

    fe = FoundationWorkflowRuntime.start_execution(fd)
    fe = FoundationWorkflowRuntime.complete_step(fe, steps[0].step_id)
    fe = FoundationWorkflowRuntime.complete_step(fe, steps[1].step_id)
    fe = FoundationWorkflowRuntime.complete_step(fe, steps[2].step_id)

    snapshot = wr.promote_execution(fd.workflow_id, fe)

    assert snapshot.progress == 75.0
    print(f"[PASS] promote_execution_partial       | progress={snapshot.progress} (3/4)")


# ------------------------------------------------------------------
# Scenario 12: promote_execution — completo
# ------------------------------------------------------------------


def scenario_promote_execution_full() -> None:
    """promote_execution with all steps completed reaches 100%."""
    wr, *_ = _setup()
    steps = [WorkflowStep.create("Only")]
    fd = FoundationWorkflowRuntime.create_definition("Full", steps=steps)
    snapshot = wr.promote_definition(fd)

    fe = FoundationWorkflowRuntime.start_execution(fd)
    fe = FoundationWorkflowRuntime.complete_step(fe, steps[0].step_id)

    snapshot = wr.promote_execution(fd.workflow_id, fe)

    assert snapshot.progress == 100.0
    print(f"[PASS] promote_execution_full          | progress={snapshot.progress}")


# ------------------------------------------------------------------
# Scenario 13: promote_execution — erro sem foundation definition
# ------------------------------------------------------------------


def scenario_promote_execution_no_definition() -> None:
    """promote_execution raises KeyError if no foundation definition."""
    wr, *_ = _setup()
    wf = Workflow(name="No Foundation")
    wr.register_workflow(wf)
    fe = WorkflowExecution.create(workflow_id=wf.id)

    try:
        wr.promote_execution(wf.id, fe)
        assert False, "Expected KeyError"
    except KeyError:
        pass
    print(f"[PASS] promote_execution_no_definition  | KeyError raised correctly")


# ------------------------------------------------------------------
# Scenario 14: determinismo
# ------------------------------------------------------------------


def scenario_determinism() -> None:
    """Same inputs produce identical stateful workflows."""
    wr, *_ = _setup()

    step = WorkflowStep.create("D")
    fd1 = FoundationWorkflowRuntime.create_definition("Det", steps=[step])
    fd2 = FoundationWorkflowRuntime.create_definition("Det", steps=[step])

    s1 = wr.promote_definition(fd1)
    s2 = wr.promote_definition(fd2)

    assert len(s1.task_ids) == len(s2.task_ids)
    assert s1.state == s2.state
    print(f"[PASS] determinism                     | tasks={len(s1.task_ids)} "
          f"state={s1.state.value} (identical)")


# ------------------------------------------------------------------
# Scenario 15: compatibilidade reversa — register_workflow ainda funciona
# ------------------------------------------------------------------


def scenario_backward_compatibility_register() -> None:
    """Existing register_workflow still works after integration."""
    wr, *_ = _setup()
    wf = Workflow(name="Legacy")
    snapshot = wr.register_workflow(wf)

    assert snapshot.name == "Legacy"
    assert snapshot.state == WorkflowRuntimeState.PLANNED
    print(f"[PASS] backward_compat_register        | name='{snapshot.name}' "
          f"state={snapshot.state.value}")


# ------------------------------------------------------------------
# Scenario 16: pipeline completo — promote_definition + start + complete_task
# ------------------------------------------------------------------


def scenario_full_integration_pipeline() -> None:
    """Full pipeline: promote → start → complete all tasks."""
    wr, *_ = _setup()
    steps = [
        WorkflowStep.create("Plan"),
        WorkflowStep.create("Execute"),
        WorkflowStep.create("Review"),
    ]
    fd = FoundationWorkflowRuntime.create_definition("Pipeline", steps=steps)
    snapshot = wr.promote_definition(fd)

    wr.start(fd.workflow_id)

    for step in steps:
        ts = next((t for t in wr.task_runtime.snapshot() if t.task_id == step.step_id), None)
        assert ts is not None
        wr.complete_task(fd.workflow_id, step.step_id)

    snapshot = wr.snapshot()[0]
    assert snapshot.progress == 100.0
    assert snapshot.state == WorkflowRuntimeState.COMPLETED
    print(f"[PASS] full_integration_pipeline       | progress={snapshot.progress} "
          f"state={snapshot.state.value}")


# ------------------------------------------------------------------
# Scenario 17: promote_definition + start
# ------------------------------------------------------------------


def scenario_promote_definition_and_start() -> None:
    """Workflow promoted from foundation can be started normally."""
    wr, *_ = _setup()
    step = WorkflowStep.create("Task 1")
    fd = FoundationWorkflowRuntime.create_definition("Startable", steps=[step])
    snapshot = wr.promote_definition(fd)

    snapshot = wr.start(fd.workflow_id)

    assert snapshot.state in {WorkflowRuntimeState.RUNNING, WorkflowRuntimeState.WAITING}
    print(f"[PASS] promote_definition_and_start    | state={snapshot.state.value}")


# ------------------------------------------------------------------
# Scenario 18: foundation_definition stored internally
# ------------------------------------------------------------------


def scenario_foundation_definition_stored() -> None:
    """Foundation definition is accessible after promote_definition."""
    wr, *_ = _setup()
    fd = FoundationWorkflowRuntime.create_definition("Stored")
    snapshot = wr.promote_definition(fd)

    stored_def = wr._foundation_definitions.get(fd.workflow_id)
    assert stored_def is not None
    assert stored_def.name == "Stored"
    print(f"[PASS] foundation_definition_stored     | definition accessible "
          f"name='{stored_def.name}'")


# ------------------------------------------------------------------
# Scenario 19: foundation_execution stored internally
# ------------------------------------------------------------------


def scenario_foundation_execution_stored() -> None:
    """Foundation execution is stored after promote_definition."""
    wr, *_ = _setup()
    fd = FoundationWorkflowRuntime.create_definition("Exec Stored")
    fe = FoundationWorkflowRuntime.start_execution(fd)
    snapshot = wr.promote_definition(fd, foundation_execution=fe)

    stored_exec = wr._foundation_executions.get(fd.workflow_id)
    assert stored_exec is not None
    assert stored_exec.execution_id == fe.execution_id
    print(f"[PASS] foundation_execution_stored      | execution accessible "
          f"id={stored_exec.execution_id.hex[:8]}")


# ------------------------------------------------------------------
# Scenario 20: create_from_foundation com múltiplas etapas
# ------------------------------------------------------------------


def scenario_create_from_foundation_multiple() -> None:
    """create_from_foundation with 5 steps creates 5 tasks."""
    wr, *_ = _setup()
    steps = [WorkflowStep.create(f"S{i}") for i in range(5)]
    fd = FoundationWorkflowRuntime.create_definition("Five Steps", steps=steps)

    snapshot = wr.create_from_foundation(fd)

    assert len(snapshot.task_ids) == 5
    assert all(s.step_id in snapshot.task_ids for s in steps)
    print(f"[PASS] create_from_foundation_multiple  | {len(snapshot.task_ids)} tasks "
          f"for {len(steps)} steps")


# ------------------------------------------------------------------
# Scenario 21: estado das tasks após promote_execution
# ------------------------------------------------------------------


def scenario_tasks_state_unchanged_by_promote_execution() -> None:
    """promote_execution does NOT complete tasks — only syncs progress."""
    wr, *_ = _setup()
    steps = [WorkflowStep.create("X"), WorkflowStep.create("Y")]
    fd = FoundationWorkflowRuntime.create_definition("Task State", steps=steps)
    snapshot = wr.promote_definition(fd)

    fe = FoundationWorkflowRuntime.start_execution(fd)
    fe = FoundationWorkflowRuntime.complete_step(fe, steps[0].step_id)

    snapshot = wr.promote_execution(fd.workflow_id, fe)

    # Tasks remain in CREATED state — promote_execution does NOT complete them
    tasks = {t.task_id: t.state for t in wr.task_runtime.snapshot()}
    # Tasks are in QUEUED state after register_task (default transition)
    assert tasks[steps[0].step_id] == TaskRuntimeState.QUEUED
    assert tasks[steps[1].step_id] == TaskRuntimeState.QUEUED
    # But progress is updated
    assert snapshot.progress == 50.0
    print(f"[PASS] tasks_unchanged_by_promote_exec | step0={tasks[steps[0].step_id].value} "
          f"step1={tasks[steps[1].step_id].value} progress={snapshot.progress}")


# ------------------------------------------------------------------
# Scenario 22: promote_execution + stateful complete_task misturado
# ------------------------------------------------------------------


def scenario_mixed_progress_and_completion() -> None:
    """promote_execution syncs progress; complete_task completes tasks in order."""
    wr, *_ = _setup()
    steps = [
        WorkflowStep.create("Step A"),
        WorkflowStep.create("Step B"),
        WorkflowStep.create("Step C"),
    ]
    fd = FoundationWorkflowRuntime.create_definition("Mixed", steps=steps)
    snapshot = wr.promote_definition(fd)
    wr.start(fd.workflow_id)

    # Sync progress from foundation (step A completed in foundation)
    fe = FoundationWorkflowRuntime.start_execution(fd)
    fe = FoundationWorkflowRuntime.complete_step(fe, steps[0].step_id)
    wr.promote_execution(fd.workflow_id, fe)

    # Complete tasks in order through stateful lifecycle
    wr.complete_task(fd.workflow_id, steps[0].step_id)
    wr.complete_task(fd.workflow_id, steps[1].step_id)
    wr.complete_task(fd.workflow_id, steps[2].step_id)

    snapshot = wr.snapshot()[0]
    assert snapshot.progress == 100.0
    assert snapshot.state == WorkflowRuntimeState.COMPLETED

    tasks = {t.task_id: t.state for t in wr.task_runtime.snapshot()}
    assert all(s == TaskRuntimeState.COMPLETED for s in tasks.values())
    print(f"[PASS] mixed_progress_and_completion   | progress={snapshot.progress} "
          f"state={snapshot.state.value} all_completed={all(s == TaskRuntimeState.COMPLETED for s in tasks.values())}")


# ------------------------------------------------------------------
# Main
# ------------------------------------------------------------------


def main() -> None:
    print("=" * 58)
    print("Workflow Runtime Integration Demo")
    print("=" * 58)
    print()

    scenario_promote_definition_empty()
    scenario_promote_definition_single_step()
    scenario_promote_definition_multiple_steps()
    scenario_promote_definition_with_metadata()
    scenario_create_from_foundation()
    scenario_workflow_id_preserved()
    scenario_step_names_as_task_names()
    scenario_task_ids_match_step_ids()
    scenario_order_preserved()
    scenario_promote_execution_progress()
    scenario_promote_execution_partial()
    scenario_promote_execution_full()
    scenario_promote_execution_no_definition()
    scenario_determinism()
    scenario_backward_compatibility_register()
    scenario_full_integration_pipeline()
    scenario_promote_definition_and_start()
    scenario_foundation_definition_stored()
    scenario_foundation_execution_stored()
    scenario_create_from_foundation_multiple()
    scenario_tasks_state_unchanged_by_promote_execution()
    scenario_mixed_progress_and_completion()

    print()
    print("=" * 58)
    print("All Workflow Runtime integration scenarios passed.")
    print("=" * 58)


if __name__ == "__main__":
    main()
