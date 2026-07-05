"""Foundation demo for the Workflow Runtime.

Validates WorkflowStep, WorkflowDefinition, WorkflowExecution creation,
step coordination, progress calculation, immutability, determinism,
trace, and the complete execution lifecycle.
"""

from __future__ import annotations

from uuid import UUID

from core.workflow.foundation import (
    WorkflowDefinition,
    WorkflowExecution,
    WorkflowResult,
    WorkflowRuntime,
    WorkflowStep,
    WorkflowTrace,
)


# ------------------------------------------------------------------
# Scenario 1: Workflow vazio
# ------------------------------------------------------------------


def scenario_empty_workflow() -> None:
    """A workflow definition with no steps."""
    wf = WorkflowRuntime.create_definition("Empty")

    assert isinstance(wf, WorkflowDefinition)
    assert wf.steps == ()
    assert wf.created_at > 0
    assert wf.name == "Empty"
    print(f"[PASS] empty_workflow                  | name='{wf.name}' steps={len(wf.steps)}")


# ------------------------------------------------------------------
# Scenario 2: Uma etapa
# ------------------------------------------------------------------


def scenario_single_step() -> None:
    """A workflow definition with one step."""
    step = WorkflowStep.create(name="Step 1", description="First step", order=0)
    wf = WorkflowRuntime.create_definition("Single", steps=[step])

    assert len(wf.steps) == 1
    assert wf.steps[0].name == "Step 1"
    assert wf.steps[0].order == 0
    print(f"[PASS] single_step                     | name='{wf.steps[0].name}' order={wf.steps[0].order}")


# ------------------------------------------------------------------
# Scenario 3: Múltiplas etapas
# ------------------------------------------------------------------


def scenario_multiple_steps() -> None:
    """A workflow definition with multiple steps."""
    steps = [
        WorkflowStep.create("Design", "Design phase"),
        WorkflowStep.create("Implement", "Implementation phase"),
        WorkflowStep.create("Test", "Testing phase"),
        WorkflowStep.create("Deploy", "Deployment phase"),
    ]
    wf = WorkflowRuntime.create_definition("Release", steps=steps)

    assert len(wf.steps) == 4
    assert wf.steps[0].name == "Design"
    assert wf.steps[1].name == "Implement"
    assert wf.steps[2].name == "Test"
    assert wf.steps[3].name == "Deploy"
    print(f"[PASS] multiple_steps                  | {len(wf.steps)} steps -> "
          f"names=[{', '.join(s.name for s in wf.steps)}]")


# ------------------------------------------------------------------
# Scenario 4: add_step
# ------------------------------------------------------------------


def scenario_add_step() -> None:
    """add_step appends a step and assigns the next order."""
    wf = WorkflowRuntime.create_definition("Growing")
    step_a = WorkflowStep.create(name="A")
    step_b = WorkflowStep.create(name="B")

    wf = WorkflowRuntime.add_step(wf, step_a)
    assert len(wf.steps) == 1
    assert wf.steps[0].order == 0

    wf = WorkflowRuntime.add_step(wf, step_b)
    assert len(wf.steps) == 2
    assert wf.steps[0].order == 0
    assert wf.steps[1].order == 1
    assert wf.steps[1].name == "B"
    print(f"[PASS] add_step                        | {len(wf.steps)} steps, "
          f"orders=[{wf.steps[0].order}, {wf.steps[1].order}]")


# ------------------------------------------------------------------
# Scenario 5: start_execution
# ------------------------------------------------------------------


def scenario_start_execution() -> None:
    """start_execution creates an execution with no completed steps."""
    step = WorkflowStep.create("Do something")
    wf = WorkflowRuntime.create_definition("Task", steps=[step])

    exec_ = WorkflowRuntime.start_execution(wf)

    assert isinstance(exec_, WorkflowExecution)
    assert exec_.workflow_id == wf.workflow_id
    assert len(exec_.completed_step_ids) == 0
    assert exec_.started_at > 0
    print(f"[PASS] start_execution                | execution_id={exec_.execution_id.hex[:8]} "
          f"completed=0")


# ------------------------------------------------------------------
# Scenario 6: complete_step
# ------------------------------------------------------------------


def scenario_complete_step() -> None:
    """complete_step marks a step as completed."""
    step = WorkflowStep.create("Do something")
    wf = WorkflowRuntime.create_definition("Task", steps=[step])
    exec_ = WorkflowRuntime.start_execution(wf)

    exec_ = WorkflowRuntime.complete_step(exec_, step.step_id)

    assert step.step_id in exec_.completed_step_ids
    assert len(exec_.completed_step_ids) == 1
    print(f"[PASS] complete_step                  | completed={len(exec_.completed_step_ids)} "
          f"step_id={step.step_id.hex[:8]}")


# ------------------------------------------------------------------
# Scenario 7: Execução parcial
# ------------------------------------------------------------------


def scenario_partial_execution() -> None:
    """A workflow partially executed has some steps completed."""
    steps = [
        WorkflowStep.create("Step 1"),
        WorkflowStep.create("Step 2"),
        WorkflowStep.create("Step 3"),
    ]
    wf = WorkflowRuntime.create_definition("Three Steps", steps=steps)
    exec_ = WorkflowRuntime.start_execution(wf)

    # Complete first two steps
    exec_ = WorkflowRuntime.complete_step(exec_, steps[0].step_id)
    exec_ = WorkflowRuntime.complete_step(exec_, steps[1].step_id)

    assert len(exec_.completed_step_ids) == 2
    assert steps[0].step_id in exec_.completed_step_ids
    assert steps[1].step_id in exec_.completed_step_ids
    assert steps[2].step_id not in exec_.completed_step_ids
    print(f"[PASS] partial_execution              | {len(exec_.completed_step_ids)}/3 completed")


# ------------------------------------------------------------------
# Scenario 8: Execução completa
# ------------------------------------------------------------------


def scenario_full_execution() -> None:
    """All steps completed."""
    steps = [
        WorkflowStep.create("A"),
        WorkflowStep.create("B"),
    ]
    wf = WorkflowRuntime.create_definition("Two Steps", steps=steps)
    exec_ = WorkflowRuntime.start_execution(wf)

    exec_ = WorkflowRuntime.complete_step(exec_, steps[0].step_id)
    exec_ = WorkflowRuntime.complete_step(exec_, steps[1].step_id)

    assert len(exec_.completed_step_ids) == 2
    assert WorkflowRuntime.is_complete(wf, exec_) is True
    print(f"[PASS] full_execution                 | completed={len(exec_.completed_step_ids)}/2 "
          f"is_complete=True")


# ------------------------------------------------------------------
# Scenario 9: get_next_step
# ------------------------------------------------------------------


def scenario_get_next_step() -> None:
    """get_next_step returns the next pending step in order."""
    steps = [
        WorkflowStep.create("First"),
        WorkflowStep.create("Second"),
        WorkflowStep.create("Third"),
    ]
    wf = WorkflowRuntime.create_definition("Ordered", steps=steps)
    exec_ = WorkflowRuntime.start_execution(wf)

    # First step should be "First"
    next_ = WorkflowRuntime.get_next_step(wf, exec_)
    assert next_ is not None
    assert next_.name == "First"

    # Complete first step, next should be "Second"
    exec_ = WorkflowRuntime.complete_step(exec_, steps[0].step_id)
    next_ = WorkflowRuntime.get_next_step(wf, exec_)
    assert next_ is not None
    assert next_.name == "Second"

    # Complete second step, next should be "Third"
    exec_ = WorkflowRuntime.complete_step(exec_, steps[1].step_id)
    next_ = WorkflowRuntime.get_next_step(wf, exec_)
    assert next_ is not None
    assert next_.name == "Third"

    # Complete third step, next should be None
    exec_ = WorkflowRuntime.complete_step(exec_, steps[2].step_id)
    next_ = WorkflowRuntime.get_next_step(wf, exec_)
    assert next_ is None
    print(f"[PASS] get_next_step                   | steps=[First, Second, Third, None]")


# ------------------------------------------------------------------
# Scenario 10: is_complete
# ------------------------------------------------------------------


def scenario_is_complete() -> None:
    """is_complete correctly reflects execution state."""
    step = WorkflowStep.create("Only")
    wf = WorkflowRuntime.create_definition("Single", steps=[step])
    exec_ = WorkflowRuntime.start_execution(wf)

    assert WorkflowRuntime.is_complete(wf, exec_) is False

    exec_ = WorkflowRuntime.complete_step(exec_, step.step_id)
    assert WorkflowRuntime.is_complete(wf, exec_) is True

    # Empty workflow is always complete
    empty_wf = WorkflowRuntime.create_definition("Empty")
    empty_exec = WorkflowRuntime.start_execution(empty_wf)
    assert WorkflowRuntime.is_complete(empty_wf, empty_exec) is True
    print(f"[PASS] is_complete                    | single=False->True, empty=True")


# ------------------------------------------------------------------
# Scenario 11: Etapas pendentes
# ------------------------------------------------------------------


def scenario_pending_steps() -> None:
    """get_pending_steps returns uncompleted steps in order."""
    steps = [
        WorkflowStep.create("A"),
        WorkflowStep.create("B"),
        WorkflowStep.create("C"),
    ]
    wf = WorkflowRuntime.create_definition("ABC", steps=steps)
    exec_ = WorkflowRuntime.start_execution(wf)

    pending = WorkflowRuntime.get_pending_steps(wf, exec_)
    assert len(pending) == 3
    assert [s.name for s in pending] == ["A", "B", "C"]

    exec_ = WorkflowRuntime.complete_step(exec_, steps[0].step_id)
    pending = WorkflowRuntime.get_pending_steps(wf, exec_)
    assert len(pending) == 2
    assert [s.name for s in pending] == ["B", "C"]

    exec_ = WorkflowRuntime.complete_step(exec_, steps[2].step_id)
    pending = WorkflowRuntime.get_pending_steps(wf, exec_)
    assert len(pending) == 1
    assert [s.name for s in pending] == ["B"]
    print(f"[PASS] pending_steps                   | 3->2->1 pending steps")


# ------------------------------------------------------------------
# Scenario 12: Progresso
# ------------------------------------------------------------------


def scenario_progress() -> None:
    """calculate_progress returns correct ratio."""
    steps = [
        WorkflowStep.create("25%"),
        WorkflowStep.create("50%"),
        WorkflowStep.create("75%"),
        WorkflowStep.create("100%"),
    ]
    wf = WorkflowRuntime.create_definition("Progress", steps=steps)
    exec_ = WorkflowRuntime.start_execution(wf)

    assert WorkflowRuntime.calculate_progress(wf, exec_) == 0.0

    exec_ = WorkflowRuntime.complete_step(exec_, steps[0].step_id)
    assert WorkflowRuntime.calculate_progress(wf, exec_) == 0.25

    exec_ = WorkflowRuntime.complete_step(exec_, steps[1].step_id)
    assert WorkflowRuntime.calculate_progress(wf, exec_) == 0.5

    exec_ = WorkflowRuntime.complete_step(exec_, steps[2].step_id)
    assert WorkflowRuntime.calculate_progress(wf, exec_) == 0.75

    exec_ = WorkflowRuntime.complete_step(exec_, steps[3].step_id)
    assert WorkflowRuntime.calculate_progress(wf, exec_) == 1.0
    print(f"[PASS] progress                        | 0.0 -> 0.25 -> 0.5 -> 0.75 -> 1.0")


# ------------------------------------------------------------------
# Scenario 13: Ordem preservada
# ------------------------------------------------------------------


def scenario_order_preserved() -> None:
    """Steps remain in definition order after mutations."""
    steps = [
        WorkflowStep.create("Z", order=99),
        WorkflowStep.create("A", order=0),
        WorkflowStep.create("M", order=50),
    ]
    wf = WorkflowRuntime.create_definition("Unordered", steps=steps)

    names = [s.name for s in wf.steps]
    assert names == ["Z", "A", "M"]  # order passed in is preserved
    # After add_step, order is reassigned
    wf2 = WorkflowRuntime.create_definition("Reordered")
    for s in steps:
        wf2 = WorkflowRuntime.add_step(wf2, s)
    assert wf2.steps[0].order == 0
    assert wf2.steps[1].order == 1
    assert wf2.steps[2].order == 2
    print(f"[PASS] order_preserved                | add_step assigns sequential orders")


# ------------------------------------------------------------------
# Scenario 14: Determinismo
# ------------------------------------------------------------------


def scenario_determinism() -> None:
    """Same inputs produce identical outputs."""
    step = WorkflowStep.create("Deterministic")
    wf = WorkflowRuntime.create_definition("Det", steps=[step])
    exec_ = WorkflowRuntime.start_execution(wf)
    exec_ = WorkflowRuntime.complete_step(exec_, step.step_id)

    wf2 = WorkflowRuntime.create_definition("Det", steps=[step])
    exec2 = WorkflowRuntime.start_execution(wf2)
    exec2 = WorkflowRuntime.complete_step(exec2, step.step_id)

    # Structure should be identical (IDs differ due to uuid4)
    assert WorkflowRuntime.is_complete(wf, exec_) == WorkflowRuntime.is_complete(wf2, exec2)
    assert WorkflowRuntime.calculate_progress(wf, exec_) == WorkflowRuntime.calculate_progress(wf2, exec2)
    assert len(exec_.completed_step_ids) == len(exec2.completed_step_ids)
    print(f"[PASS] determinism                    | is_complete={WorkflowRuntime.is_complete(wf, exec_)} "
          f"progress={WorkflowRuntime.calculate_progress(wf, exec_)} (identical)")


# ------------------------------------------------------------------
# Scenario 15: Imutabilidade
# ------------------------------------------------------------------


def scenario_immutability() -> None:
    """Original definition and execution are never mutated."""
    step = WorkflowStep.create("Immutable")
    wf = WorkflowRuntime.create_definition("Imm", steps=[step])
    exec_ = WorkflowRuntime.start_execution(wf)

    _ = WorkflowRuntime.complete_step(exec_, step.step_id)

    assert len(exec_.completed_step_ids) == 0  # original unchanged
    assert len(wf.steps) == 1
    assert wf.steps[0].name == "Immutable"
    print(f"[PASS] immutability                   | original execution untouched "
          f"(completed={len(exec_.completed_step_ids)})")


# ------------------------------------------------------------------
# Scenario 16: Trace correto
# ------------------------------------------------------------------


def scenario_trace_correct() -> None:
    """WorkflowTrace contains accurate progress and step lists."""
    steps = [
        WorkflowStep.create("Plan"),
        WorkflowStep.create("Execute"),
        WorkflowStep.create("Review"),
    ]
    wf = WorkflowRuntime.create_definition("Project", steps=steps)
    exec_ = WorkflowRuntime.start_execution(wf)
    exec_ = WorkflowRuntime.complete_step(exec_, steps[0].step_id)
    exec_ = WorkflowRuntime.complete_step(exec_, steps[1].step_id)

    trace = WorkflowRuntime.build_trace(
        wf, exec_, timestamps={"start": 1.0, "mid": 2.0},
    )

    assert isinstance(trace, WorkflowTrace)
    assert trace.steps_total == 3
    assert trace.steps_completed == 2
    assert trace.progress == 2.0 / 3.0
    assert list(trace.completed_step_names) == ["Plan", "Execute"]
    assert list(trace.pending_step_names) == ["Review"]
    assert trace.timestamps["start"] == 1.0
    print(f"[PASS] trace_correct                  | {trace.steps_completed}/{trace.steps_total} "
          f"progress={trace.progress:.2f} "
          f"completed={list(trace.completed_step_names)}")


# ------------------------------------------------------------------
# Scenario 17: Resultado correto
# ------------------------------------------------------------------


def scenario_result_correct() -> None:
    """WorkflowResult contains execution, trace, and success flag."""
    step = WorkflowStep.create("Single step")
    wf = WorkflowRuntime.create_definition("Result Test", steps=[step])
    exec_ = WorkflowRuntime.start_execution(wf)
    exec_ = WorkflowRuntime.complete_step(exec_, step.step_id)

    result = WorkflowRuntime.build_result(
        wf, exec_, timestamps={"end": 3.0}, success=True,
    )

    assert isinstance(result, WorkflowResult)
    assert result.success is True
    assert result.execution is exec_
    assert result.trace.progress == 1.0
    assert result.error_message == ""
    print(f"[PASS] result_correct                 | success={result.success} "
          f"progress={result.trace.progress}")


# ------------------------------------------------------------------
# Scenario 18: WorkflowResult com erro
# ------------------------------------------------------------------


def scenario_result_with_error() -> None:
    """WorkflowResult can represent failure with error_message."""
    wf = WorkflowRuntime.create_definition("Failing")
    exec_ = WorkflowRuntime.start_execution(wf)

    result = WorkflowRuntime.build_result(
        wf, exec_, success=False,
        error_message="Step 1 failed: insufficient data",
    )

    assert result.success is False
    assert result.error_message == "Step 1 failed: insufficient data"
    assert result.trace.steps_completed == 0
    print(f"[PASS] result_with_error              | success={result.success} "
          f"error='{result.error_message}'")


# ------------------------------------------------------------------
# Scenario 19: complete_step — step já completado (idempotente)
# ------------------------------------------------------------------


def scenario_complete_step_idempotent() -> None:
    """Completing an already-completed step is a no-op."""
    step = WorkflowStep.create("Idempotent")
    wf = WorkflowRuntime.create_definition("Idem", steps=[step])
    exec_ = WorkflowRuntime.start_execution(wf)

    exec_ = WorkflowRuntime.complete_step(exec_, step.step_id)
    assert len(exec_.completed_step_ids) == 1

    exec_ = WorkflowRuntime.complete_step(exec_, step.step_id)
    assert len(exec_.completed_step_ids) == 1  # unchanged
    print(f"[PASS] complete_step_idempotent        | completed={len(exec_.completed_step_ids)} "
          f"(idempotent)")


# ------------------------------------------------------------------
# Scenario 20: WorkflowDefinition factory methods
# ------------------------------------------------------------------


def scenario_definition_factories() -> None:
    """create and create_with_timestamp produce valid definitions."""
    step = WorkflowStep.create("Factory step")
    wf1 = WorkflowDefinition.create(
        name="Factory Test",
        steps=[step],
        metadata={"env": "test"},
    )
    assert wf1.name == "Factory Test"
    assert len(wf1.steps) == 1
    assert wf1.metadata == {"env": "test"}

    wf2 = WorkflowDefinition.create_with_timestamp(
        name="Timed", created_at=500.0,
    )
    assert wf2.created_at == 500.0
    assert len(wf2.steps) == 0

    print(f"[PASS] definition_factories           | create() steps={len(wf1.steps)} "
          f"create_with_timestamp() time={wf2.created_at}")


# ------------------------------------------------------------------
# Scenario 21: WorkflowExecution factory methods
# ------------------------------------------------------------------


def scenario_execution_factories() -> None:
    """WorkflowExecution.create and create_with_timestamp produce valid executions."""
    wf = WorkflowRuntime.create_definition("Exec Factory")

    e1 = WorkflowExecution.create(workflow_id=wf.workflow_id)
    assert e1.workflow_id == wf.workflow_id
    assert len(e1.completed_step_ids) == 0

    e2 = WorkflowExecution.create_with_timestamp(
        workflow_id=wf.workflow_id, started_at=1000.0,
    )
    assert e2.started_at == 1000.0

    print(f"[PASS] execution_factories            | create() id={e1.execution_id.hex[:8]} "
          f"create_with_timestamp() time={e2.started_at}")


# ------------------------------------------------------------------
# Scenario 22: get_completed_steps
# ------------------------------------------------------------------


def scenario_get_completed_steps() -> None:
    """get_completed_steps returns completed steps in order."""
    steps = [
        WorkflowStep.create("Alpha"),
        WorkflowStep.create("Beta"),
        WorkflowStep.create("Gamma"),
    ]
    wf = WorkflowRuntime.create_definition("Greek", steps=steps)
    exec_ = WorkflowRuntime.start_execution(wf)

    # Complete Alpha and Gamma (out of order)
    exec_ = WorkflowRuntime.complete_step(exec_, steps[0].step_id)
    exec_ = WorkflowRuntime.complete_step(exec_, steps[2].step_id)

    completed = WorkflowRuntime.get_completed_steps(wf, exec_)
    assert len(completed) == 2
    assert [s.name for s in completed] == ["Alpha", "Gamma"]
    print(f"[PASS] get_completed_steps            | completed={[s.name for s in completed]}")


# ------------------------------------------------------------------
# Scenario 23: Progresso — workflow vazio
# ------------------------------------------------------------------


def scenario_progress_empty() -> None:
    """Empty workflow has progress 1.0."""
    wf = WorkflowRuntime.create_definition("Empty")
    exec_ = WorkflowRuntime.start_execution(wf)

    progress = WorkflowRuntime.calculate_progress(wf, exec_)
    assert progress == 1.0
    print(f"[PASS] progress_empty                  | progress={progress}")


# ------------------------------------------------------------------
# Scenario 24: get_next_step — workflow vazio
# ------------------------------------------------------------------


def scenario_next_step_empty() -> None:
    """Empty workflow has no next step."""
    wf = WorkflowRuntime.create_definition("Empty")
    exec_ = WorkflowRuntime.start_execution(wf)

    next_ = WorkflowRuntime.get_next_step(wf, exec_)
    assert next_ is None
    print(f"[PASS] next_step_empty                | next_step={next_}")


# ------------------------------------------------------------------
# Scenario 25: WorkflowStep factory
# ------------------------------------------------------------------


def scenario_step_factory() -> None:
    """WorkflowStep.create produces a valid step."""
    step = WorkflowStep.create(
        name="Custom Step",
        description="A custom step for testing",
        order=5,
        metadata={"key": "value"},
    )
    assert isinstance(step, WorkflowStep)
    assert step.name == "Custom Step"
    assert step.description == "A custom step for testing"
    assert step.order == 5
    assert step.metadata == {"key": "value"}
    print(f"[PASS] step_factory                    | name='{step.name}' order={step.order}")


# ------------------------------------------------------------------
# Scenario 26: Múltiplas execuções do mesmo workflow
# ------------------------------------------------------------------


def scenario_multiple_executions_same_workflow() -> None:
    """Multiple independent executions of the same definition."""
    step = WorkflowStep.create("Single step")
    wf = WorkflowRuntime.create_definition("Multi Exec", steps=[step])

    e1 = WorkflowRuntime.start_execution(wf)
    e1 = WorkflowRuntime.complete_step(e1, step.step_id)

    e2 = WorkflowRuntime.start_execution(wf)
    # e2 has no completed steps

    assert WorkflowRuntime.is_complete(wf, e1) is True
    assert WorkflowRuntime.is_complete(wf, e2) is False
    assert e1.execution_id != e2.execution_id
    print(f"[PASS] multiple_executions_same_wf     | exec1 complete={WorkflowRuntime.is_complete(wf, e1)} "
          f"exec2 complete={WorkflowRuntime.is_complete(wf, e2)}")


# ------------------------------------------------------------------
# Scenario 27: build_trace sem timestamps
# ------------------------------------------------------------------


def scenario_trace_no_timestamps() -> None:
    """build_trace works without timestamps."""
    step = WorkflowStep.create("Solitary")
    wf = WorkflowRuntime.create_definition("No TS", steps=[step])
    exec_ = WorkflowRuntime.start_execution(wf)

    trace = WorkflowRuntime.build_trace(wf, exec_)

    assert trace.steps_total == 1
    assert trace.steps_completed == 0
    assert trace.timestamps == {}
    print(f"[PASS] trace_no_timestamps            | steps_total={trace.steps_total} "
          f"timestamps={trace.timestamps}")


# ------------------------------------------------------------------
# Scenario 28: Múltiplos steps com add_step em sequência
# ------------------------------------------------------------------


def scenario_add_step_sequential() -> None:
    """add_step called multiple times preserves order."""
    wf = WorkflowRuntime.create_definition("Sequential")
    names = ["Init", "Process", "Finalize", "Archive"]

    for i, name in enumerate(names):
        step = WorkflowStep.create(name=name, description=f"Step {i}")
        wf = WorkflowRuntime.add_step(wf, step)

    assert len(wf.steps) == 4
    for i, s in enumerate(wf.steps):
        assert s.name == names[i]
        assert s.order == i
    print(f"[PASS] add_step_sequential             | {len(wf.steps)} steps with "
          f"orders=[{', '.join(str(s.order) for s in wf.steps)}]")


# ------------------------------------------------------------------
# Scenario 29: Dataclasses são frozen
# ------------------------------------------------------------------


def scenario_frozen_dataclasses() -> None:
    """All dataclasses raise TypeError on mutation attempt."""
    step = WorkflowStep.create("Frozen")
    wf = WorkflowRuntime.create_definition("Frozen WF", steps=[step])
    exec_ = WorkflowRuntime.start_execution(wf)

    for obj, attr in [
        (step, "name"),
        (wf, "name"),
        (exec_, "completed_step_ids"),
    ]:
        try:
            setattr(obj, attr, "mutated")  # type: ignore[assignment]
            assert False, f"Should have raised TypeError for {type(obj).__name__}.{attr}"
        except AttributeError:
            pass

    print(f"[PASS] frozen_dataclasses             | WorkflowStep, WorkflowDefinition, "
          f"WorkflowExecution are frozen")


# ------------------------------------------------------------------
# Scenario 30: Pipeline completo — criar, executar, completar, traçar
# ------------------------------------------------------------------


def scenario_full_lifecycle() -> None:
    """Complete workflow lifecycle: create → add → execute → complete → trace."""
    wf = WorkflowRuntime.create_definition("Lifecycle")
    steps = [
        WorkflowStep.create("Research"),
        WorkflowStep.create("Draft"),
        WorkflowStep.create("Review"),
        WorkflowStep.create("Publish"),
    ]
    for s in steps:
        wf = WorkflowRuntime.add_step(wf, s)

    exec_ = WorkflowRuntime.start_execution(wf)

    # Execute all steps sequentially
    for step in wf.steps:
        assert not WorkflowRuntime.is_complete(wf, exec_)
        exec_ = WorkflowRuntime.complete_step(exec_, step.step_id)

    assert WorkflowRuntime.is_complete(wf, exec_) is True
    assert WorkflowRuntime.calculate_progress(wf, exec_) == 1.0
    assert len(WorkflowRuntime.get_pending_steps(wf, exec_)) == 0

    result = WorkflowRuntime.build_result(wf, exec_, timestamps={"done": 99.0})

    assert result.success is True
    assert result.trace.steps_total == 4
    assert result.trace.steps_completed == 4
    assert result.trace.progress == 1.0
    assert list(result.trace.completed_step_names) == [
        "Research", "Draft", "Review", "Publish",
    ]
    print(f"[PASS] full_lifecycle                 | {result.trace.steps_completed}/"
          f"{result.trace.steps_total} steps, "
          f"progress={result.trace.progress}, "
          f"success={result.success}")


# ------------------------------------------------------------------
# Scenario 31: Progresso incremental via complete_step
# ------------------------------------------------------------------


def scenario_incremental_progress() -> None:
    """Progress updates correctly after each complete_step."""
    steps = [WorkflowStep.create(f"S{i}") for i in range(5)]
    wf = WorkflowRuntime.create_definition("Incremental", steps=steps)
    exec_ = WorkflowRuntime.start_execution(wf)

    progresses = []
    for i, step in enumerate(wf.steps):
        exec_ = WorkflowRuntime.complete_step(exec_, step.step_id)
        progresses.append(WorkflowRuntime.calculate_progress(wf, exec_))

    assert progresses == [0.2, 0.4, 0.6, 0.8, 1.0]
    print(f"[PASS] incremental_progress            | progresses={progresses}")


# ------------------------------------------------------------------
# Scenario 32: WorkflowTrace pending_step_names
# ------------------------------------------------------------------


def scenario_trace_pending_names() -> None:
    """WorkflowTrace correctly lists pending step names."""
    steps = [
        WorkflowStep.create("Research"),
        WorkflowStep.create("Draft"),
        WorkflowStep.create("Review"),
    ]
    wf = WorkflowRuntime.create_definition("Writing", steps=steps)
    exec_ = WorkflowRuntime.start_execution(wf)
    exec_ = WorkflowRuntime.complete_step(exec_, steps[0].step_id)

    trace = WorkflowRuntime.build_trace(wf, exec_)

    assert list(trace.pending_step_names) == ["Draft", "Review"]
    assert list(trace.completed_step_names) == ["Research"]
    print(f"[PASS] trace_pending_names             | pending={list(trace.pending_step_names)} "
          f"completed={list(trace.completed_step_names)}")


# ------------------------------------------------------------------
# Main
# ------------------------------------------------------------------


def main() -> None:
    print("=" * 58)
    print("Workflow Runtime Foundation Demo")
    print("=" * 58)
    print()

    scenario_empty_workflow()
    scenario_single_step()
    scenario_multiple_steps()
    scenario_add_step()
    scenario_start_execution()
    scenario_complete_step()
    scenario_partial_execution()
    scenario_full_execution()
    scenario_get_next_step()
    scenario_is_complete()
    scenario_pending_steps()
    scenario_progress()
    scenario_order_preserved()
    scenario_determinism()
    scenario_immutability()
    scenario_trace_correct()
    scenario_result_correct()
    scenario_result_with_error()
    scenario_complete_step_idempotent()
    scenario_definition_factories()
    scenario_execution_factories()
    scenario_get_completed_steps()
    scenario_progress_empty()
    scenario_next_step_empty()
    scenario_step_factory()
    scenario_multiple_executions_same_workflow()
    scenario_trace_no_timestamps()
    scenario_add_step_sequential()
    scenario_frozen_dataclasses()
    scenario_full_lifecycle()
    scenario_incremental_progress()
    scenario_trace_pending_names()

    print()
    print("=" * 58)
    print("All Workflow Runtime scenarios passed.")
    print("=" * 58)


if __name__ == "__main__":
    main()
