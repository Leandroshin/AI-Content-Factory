"""Demo for the Cognitive Employee Foundation.

Validates ThoughtRuntime stateless pipeline:
receive_task → analyze_task → build_plan → prioritize_steps →
execute_next_step → build_result

All operations are deterministic, frozen, and side-effect free.
"""

from __future__ import annotations

from uuid import UUID, uuid4

from core.employees.cognition import (
    Thought,
    ThoughtContext,
    ThoughtPlan,
    ThoughtResult,
    ThoughtRuntime,
    ThoughtStep,
    ThoughtTrace,
)


# ------------------------------------------------------------------
# Scenario 1: receive_task
# ------------------------------------------------------------------


def scenario_receive_task() -> None:
    """receive_task creates a basic cognitive context."""
    ctx = ThoughtRuntime.receive_task("Write article")

    assert isinstance(ctx, ThoughtContext)
    assert ctx.task_name == "Write article"
    assert ctx.complexity == "simple"
    assert ctx.domain == "general"
    assert ctx.requirements == ()
    assert ctx.employee_id is None
    print(f"[PASS] receive_task                     | task='{ctx.task_name}' "
          f"complexity={ctx.complexity} domain={ctx.domain}")


# ------------------------------------------------------------------
# Scenario 2: receive_task com employee_id
# ------------------------------------------------------------------


def scenario_receive_task_with_employee() -> None:
    """receive_task accepts an optional employee_id."""
    emp_id = uuid4()
    ctx = ThoughtRuntime.receive_task("Review PR", employee_id=emp_id)

    assert ctx.employee_id == emp_id
    print(f"[PASS] receive_task_with_employee       | employee_id={emp_id.hex[:8]}")


# ------------------------------------------------------------------
# Scenario 3: receive_task com metadata
# ------------------------------------------------------------------


def scenario_receive_task_with_metadata() -> None:
    """receive_task stores metadata in the context."""
    ctx = ThoughtRuntime.receive_task(
        "Analyze data",
        metadata={"project": "X", "priority": "high"},
    )

    assert ctx.metadata["project"] == "X"
    assert ctx.metadata["priority"] == "high"
    print(f"[PASS] receive_task_with_metadata       | metadata={ctx.metadata}")


# ------------------------------------------------------------------
# Scenario 4: analyze_task — tarefa simples
# ------------------------------------------------------------------


def scenario_analyze_simple() -> None:
    """analyze_task infers simple complexity for basic tasks."""
    ctx = ThoughtRuntime.receive_task("Fix typo")
    ctx = ThoughtRuntime.analyze_task(ctx, requirements=["correct spelling"])

    assert ctx.complexity == "simple"
    assert ctx.domain == "general"
    assert len(ctx.requirements) == 1
    print(f"[PASS] analyze_simple                   | complexity={ctx.complexity} "
          f"domain={ctx.domain}")


# ------------------------------------------------------------------
# Scenario 5: analyze_task — tarefa média
# ------------------------------------------------------------------


def scenario_analyze_medium() -> None:
    """analyze_task infers medium complexity for tasks with 3+ requirements."""
    ctx = ThoughtRuntime.receive_task("Design component")
    ctx = ThoughtRuntime.analyze_task(ctx, requirements=[
        "create layout", "choose colors", "define typography",
    ])

    assert ctx.complexity == "medium"
    print(f"[PASS] analyze_medium                   | complexity={ctx.complexity} "
          f"reqs={len(ctx.requirements)}")


# ------------------------------------------------------------------
# Scenario 6: analyze_task — tarefa complexa
# ------------------------------------------------------------------


def scenario_analyze_complex() -> None:
    """analyze_task infers complex complexity for 5+ requirements."""
    ctx = ThoughtRuntime.receive_task("Architect system")
    ctx = ThoughtRuntime.analyze_task(ctx, requirements=[
        "design database", "plan API", "define schemas",
        "choose tech stack", "document architecture",
    ])

    assert ctx.complexity == "complex"
    print(f"[PASS] analyze_complex                  | complexity={ctx.complexity} "
          f"reqs={len(ctx.requirements)}")


# ------------------------------------------------------------------
# Scenario 7: analyze_task — domínio inferido
# ------------------------------------------------------------------


def scenario_analyze_domain() -> None:
    """analyze_task infers domain from task name and requirements."""
    ctx = ThoughtRuntime.receive_task("Write Python API")
    ctx = ThoughtRuntime.analyze_task(ctx, requirements=["develop endpoints"])

    assert ctx.domain == "engineering"
    print(f"[PASS] analyze_domain                   | domain={ctx.domain}")


# ------------------------------------------------------------------
# Scenario 8: build_plan — tarefa simples
# ------------------------------------------------------------------


def scenario_build_plan_simple() -> None:
    """build_plan creates 1-2 steps for simple tasks."""
    ctx = ThoughtRuntime.receive_task("Fix typo")
    ctx = ThoughtRuntime.analyze_task(ctx)
    plan = ThoughtRuntime.build_plan(ctx)

    assert isinstance(plan, ThoughtPlan)
    assert plan.task_name == "Fix typo"
    assert 1 <= len(plan.steps) <= 2
    print(f"[PASS] build_plan_simple                | steps={len(plan.steps)} "
          f"task='{plan.task_name}'")


# ------------------------------------------------------------------
# Scenario 9: build_plan — tarefa complexa
# ------------------------------------------------------------------


def scenario_build_plan_complex() -> None:
    """build_plan creates 5-6 steps for complex tasks."""
    ctx = ThoughtRuntime.receive_task("Optimize database")
    ctx = ThoughtRuntime.analyze_task(ctx, requirements=[
        "analyze queries", "add indexes", "refactor schema",
        "test performance", "document changes",
    ])
    plan = ThoughtRuntime.build_plan(ctx)

    assert 5 <= len(plan.steps) <= 6
    print(f"[PASS] build_plan_complex               | steps={len(plan.steps)} "
          f"complexity={ctx.complexity}")


# ------------------------------------------------------------------
# Scenario 10: build_plan — steps com effort_estimate
# ------------------------------------------------------------------


def scenario_build_plan_effort() -> None:
    """build_plan steps have effort_estimates between 0 and 1."""
    ctx = ThoughtRuntime.receive_task("Research topic")
    ctx = ThoughtRuntime.analyze_task(ctx)
    plan = ThoughtRuntime.build_plan(ctx)

    for step in plan.steps:
        assert 0.0 <= step.effort_estimate <= 1.0
    print(f"[PASS] build_plan_effort                | all {len(plan.steps)} steps "
          f"have valid effort estimates")


# ------------------------------------------------------------------
# Scenario 11: prioritize_steps — ordenação por effort
# ------------------------------------------------------------------


def scenario_prioritize_by_effort() -> None:
    """prioritize_steps sorts steps by effort (quick wins first)."""
    ctx = ThoughtRuntime.receive_task("Complex task")
    ctx = ThoughtRuntime.analyze_task(ctx, requirements=["a", "b", "c"])
    plan = ThoughtRuntime.build_plan(ctx)

    # Manually set up steps with known effort order
    steps = [
        ThoughtStep.create("Hard step", effort_estimate=0.9, order=2),
        ThoughtStep.create("Easy step", effort_estimate=0.2, order=1),
        ThoughtStep.create("Medium step", effort_estimate=0.5, order=0),
    ]
    plan = ThoughtPlan.create(
        task_name="Priority Test",
        steps=steps,
        metadata={"test": "priority"},
    )

    prioritized = ThoughtRuntime.prioritize_steps(plan)

    names = [s.name for s in prioritized.steps]
    assert names == ["Easy step", "Medium step", "Hard step"]
    print(f"[PASS] prioritize_by_effort             | order={names}")


# ------------------------------------------------------------------
# Scenario 12: prioritize_steps — ordem original como tiebreaker
# ------------------------------------------------------------------


def scenario_prioritize_tiebreaker() -> None:
    """Steps with equal effort keep original order as tiebreaker."""
    steps = [
        ThoughtStep.create("First", effort_estimate=0.5, order=0),
        ThoughtStep.create("Second", effort_estimate=0.5, order=1),
        ThoughtStep.create("Third", effort_estimate=0.5, order=2),
    ]
    plan = ThoughtPlan.create(task_name="Tie Test", steps=steps)
    prioritized = ThoughtRuntime.prioritize_steps(plan)

    names = [s.name for s in prioritized.steps]
    assert names == ["First", "Second", "Third"]
    print(f"[PASS] prioritize_tiebreaker            | order={names}")


# ------------------------------------------------------------------
# Scenario 13: execute_next_step
# ------------------------------------------------------------------


def scenario_execute_next_step() -> None:
    """execute_next_step removes the first step and returns a Thought."""
    step = ThoughtStep.create("Analyze")
    plan = ThoughtPlan.create(task_name="Test", steps=[step])
    ctx = ThoughtRuntime.receive_task("Test")
    ctx = ThoughtRuntime.analyze_task(ctx)

    updated_plan, thought = ThoughtRuntime.execute_next_step(plan, ctx)

    assert len(updated_plan.steps) == 0
    assert thought is not None
    assert isinstance(thought, Thought)
    assert thought.step_id == step.step_id
    assert "Analyze" in thought.content
    print(f"[PASS] execute_next_step                | steps_remaining="
          f"{len(updated_plan.steps)} thought='{thought.content[:30]}...'")


# ------------------------------------------------------------------
# Scenario 14: execute_next_step — plano vazio
# ------------------------------------------------------------------


def scenario_execute_empty_plan() -> None:
    """execute_next_step on an empty plan returns (plan, None)."""
    plan = ThoughtPlan.create(task_name="Empty")
    ctx = ThoughtRuntime.receive_task("Empty")

    updated_plan, thought = ThoughtRuntime.execute_next_step(plan, ctx)

    assert thought is None
    assert updated_plan is plan  # same reference
    print(f"[PASS] execute_empty_plan               | thought={thought}")


# ------------------------------------------------------------------
# Scenario 15: execute_next_step — conteúdo personalizado
# ------------------------------------------------------------------


def scenario_execute_custom_content() -> None:
    """execute_next_step accepts custom thought content."""
    step = ThoughtStep.create("Custom step")
    plan = ThoughtPlan.create(task_name="Custom", steps=[step])
    ctx = ThoughtRuntime.receive_task("Custom")

    _, thought = ThoughtRuntime.execute_next_step(
        plan, ctx, thought_content="Custom cognitive output",
    )

    assert thought is not None
    assert thought.content == "Custom cognitive output"
    print(f"[PASS] execute_custom_content           | content='{thought.content}'")


# ------------------------------------------------------------------
# Scenario 16: get_next_step
# ------------------------------------------------------------------


def scenario_get_next_step() -> None:
    """get_next_step returns the first pending step."""
    steps = [
        ThoughtStep.create("First step"),
        ThoughtStep.create("Second step"),
    ]
    plan = ThoughtPlan.create(task_name="Next", steps=steps)

    next_ = ThoughtRuntime.get_next_step(plan)
    assert next_ is not None
    assert next_.name == "First step"

    # Remove one step
    ctx = ThoughtRuntime.receive_task("Next")
    plan, _ = ThoughtRuntime.execute_next_step(plan, ctx)
    next_ = ThoughtRuntime.get_next_step(plan)
    assert next_ is not None
    assert next_.name == "Second step"

    # Remove all steps
    plan, _ = ThoughtRuntime.execute_next_step(plan, ctx)
    next_ = ThoughtRuntime.get_next_step(plan)
    assert next_ is None
    print(f"[PASS] get_next_step                    | steps=[First step, "
          f"Second step, None]")


# ------------------------------------------------------------------
# Scenario 17: is_complete
# ------------------------------------------------------------------


def scenario_is_complete() -> None:
    """is_complete checks whether the plan has no remaining steps."""
    plan = ThoughtPlan.create(task_name="Complete Test")
    assert ThoughtRuntime.is_complete(plan) is True

    step = ThoughtStep.create("Only step")
    plan = ThoughtPlan.create(task_name="Not done", steps=[step])
    assert ThoughtRuntime.is_complete(plan) is False

    print(f"[PASS] is_complete                     | empty=True steps=1=False")


# ------------------------------------------------------------------
# Scenario 18: calculate_total_effort
# ------------------------------------------------------------------


def scenario_calculate_total_effort() -> None:
    """calculate_total_effort sums effort_estimates."""
    steps = [
        ThoughtStep.create("A", effort_estimate=0.2),
        ThoughtStep.create("B", effort_estimate=0.3),
        ThoughtStep.create("C", effort_estimate=0.5),
    ]
    plan = ThoughtPlan.create(task_name="Effort", steps=steps)

    total = ThoughtRuntime.calculate_total_effort(plan)
    assert total == 1.0
    print(f"[PASS] calculate_total_effort           | total={total}")


# ------------------------------------------------------------------
# Scenario 19: steps_remaining / steps_completed
# ------------------------------------------------------------------


def scenario_steps_counts() -> None:
    """steps_remaining and steps_completed track progress."""
    steps = [ThoughtStep.create(f"S{i}") for i in range(5)]
    plan = ThoughtPlan.create(task_name="Counts", steps=steps)
    ctx = ThoughtRuntime.receive_task("Counts")

    assert ThoughtRuntime.steps_remaining(plan) == 5
    assert ThoughtRuntime.steps_completed(5, plan) == 0

    plan, _ = ThoughtRuntime.execute_next_step(plan, ctx)
    assert ThoughtRuntime.steps_remaining(plan) == 4
    assert ThoughtRuntime.steps_completed(5, plan) == 1

    plan, _ = ThoughtRuntime.execute_next_step(plan, ctx)
    assert ThoughtRuntime.steps_remaining(plan) == 3
    assert ThoughtRuntime.steps_completed(5, plan) == 2
    print(f"[PASS] steps_counts                     | remaining=3 completed=2")


# ------------------------------------------------------------------
# Scenario 20: build_trace
# ------------------------------------------------------------------


def scenario_build_trace() -> None:
    """build_trace produces an accurate ThoughtTrace."""
    steps = [ThoughtStep.create("A"), ThoughtStep.create("B")]
    plan = ThoughtPlan.create(task_name="Trace", steps=steps)

    trace = ThoughtRuntime.build_trace(
        stages=["receive", "analyze", "build_plan"],
        plan=plan,
        prioritized_count=2,
        thoughts_generated=2,
        timestamps={"start": 1.0, "end": 2.0},
    )

    assert isinstance(trace, ThoughtTrace)
    assert trace.steps_planned == 2
    assert trace.steps_prioritized == 2
    assert trace.thoughts_generated == 2
    assert trace.timestamps["start"] == 1.0
    print(f"[PASS] build_trace                      | planned={trace.steps_planned} "
          f"prioritized={trace.steps_prioritized}")


# ------------------------------------------------------------------
# Scenario 21: build_result
# ------------------------------------------------------------------


def scenario_build_result() -> None:
    """build_result produces a complete ThoughtResult."""
    ctx = ThoughtRuntime.receive_task("Result Test")
    ctx = ThoughtRuntime.analyze_task(ctx)
    plan = ThoughtRuntime.build_plan(ctx)
    trace = ThoughtRuntime.build_trace(
        stages=["receive", "analyze", "build_plan"],
        plan=plan, prioritized_count=0, thoughts_generated=0,
    )

    result = ThoughtRuntime.build_result(
        context=ctx, plan=plan, trace=trace, success=True,
    )

    assert isinstance(result, ThoughtResult)
    assert result.success is True
    assert result.plan is plan
    assert result.context is ctx
    assert result.trace is trace
    assert result.error_message == ""
    print(f"[PASS] build_result                     | success={result.success} "
          f"plan={'yes' if result.plan else 'no'}")


# ------------------------------------------------------------------
# Scenario 22: build_result com erro
# ------------------------------------------------------------------


def scenario_build_result_error() -> None:
    """build_result can represent failure with error_message."""
    ctx = ThoughtRuntime.receive_task("Failing Task")
    result = ThoughtRuntime.build_result(
        context=ctx, success=False,
        error_message="Analysis failed: insufficient data",
    )

    assert result.success is False
    assert result.error_message == "Analysis failed: insufficient data"
    assert result.plan is None
    print(f"[PASS] build_result_error               | success={result.success} "
          f"error='{result.error_message}'")


# ------------------------------------------------------------------
# Scenario 23: full_pipeline — tarefa simples
# ------------------------------------------------------------------


def scenario_full_pipeline_simple() -> None:
    """full_pipeline runs the complete cycle for a simple task."""
    result = ThoughtRuntime.full_pipeline("Fix typo")

    assert result.success is True
    assert result.context is not None
    assert result.plan is not None
    assert result.trace is not None
    assert len(result.executed_thoughts) >= 1
    print(f"[PASS] full_pipeline_simple             | success={result.success} "
          f"steps_planned={result.trace.steps_planned} "
          f"thoughts={result.trace.thoughts_generated}")


# ------------------------------------------------------------------
# Scenario 24: full_pipeline — tarefa complexa
# ------------------------------------------------------------------


def scenario_full_pipeline_complex() -> None:
    """full_pipeline handles complex tasks with more steps."""
    result = ThoughtRuntime.full_pipeline(
        "Architect microservices",
        requirements=[
            "design", "plan", "implement", "test",
            "deploy", "monitor",
        ],
    )

    assert result.success is True
    assert result.context.complexity == "complex"
    assert result.trace.steps_planned >= 1
    print(f"[PASS] full_pipeline_complex            | complexity="
          f"{result.context.complexity} steps={result.trace.steps_planned} "
          f"thoughts={result.trace.thoughts_generated}")


# ------------------------------------------------------------------
# Scenario 25: full_pipeline — conteúdos personalizados
# ------------------------------------------------------------------


def scenario_full_pipeline_custom_contents() -> None:
    """full_pipeline accepts custom thought contents."""
    result = ThoughtRuntime.full_pipeline(
        "Test",
        requirements=["req"],
        thought_contents=["Step 1 thought", "Step 2 thought", "Step 3 thought"],
    )

    assert result.success is True
    executed = result.executed_thoughts
    if len(executed) >= 1:
        assert executed[0].content == "Step 1 thought"
    print(f"[PASS] full_pipeline_custom_contents    | "
          f"thoughts={len(executed)} "
          f"first='{executed[0].content if executed else 'N/A'}'")


# ------------------------------------------------------------------
# Scenario 26: determinismo
# ------------------------------------------------------------------


def scenario_determinism() -> None:
    """Same inputs produce identical outputs."""
    ctx1 = ThoughtRuntime.receive_task("Det Test")
    ctx1 = ThoughtRuntime.analyze_task(ctx1, requirements=["x"])
    plan1 = ThoughtRuntime.build_plan(ctx1)

    ctx2 = ThoughtRuntime.receive_task("Det Test")
    ctx2 = ThoughtRuntime.analyze_task(ctx2, requirements=["x"])
    plan2 = ThoughtRuntime.build_plan(ctx2)

    assert len(plan1.steps) == len(plan2.steps)
    assert plan1.task_name == plan2.task_name
    for s1, s2 in zip(plan1.steps, plan2.steps):
        assert s1.name == s2.name
        assert s1.effort_estimate == s2.effort_estimate
    print(f"[PASS] determinism                      | steps={len(plan1.steps)} "
          f"structure identical")


# ------------------------------------------------------------------
# Scenario 27: imutabilidade — dataclasses frozen
# ------------------------------------------------------------------


def scenario_frozen_dataclasses() -> None:
    """All cognition dataclasses are frozen and cannot be mutated."""
    step = ThoughtStep.create("Frozen")
    plan = ThoughtPlan.create(task_name="Frozen", steps=[step])
    thought = Thought.create("Frozen thought")
    ctx = ThoughtRuntime.receive_task("Frozen")
    result = ThoughtRuntime.build_result(ctx, success=True)

    for obj, attr in [
        (step, "name"),
        (plan, "task_name"),
        (thought, "content"),
        (ctx, "task_name"),
        (result, "success"),
    ]:
        try:
            setattr(obj, attr, "mutated")
            assert False, f"Should have raised TypeError for {type(obj).__name__}"
        except (AttributeError, TypeError):
            pass

    print(f"[PASS] frozen_dataclasses              | ThoughtStep, ThoughtPlan, "
          f"Thought, ThoughtContext, ThoughtResult are frozen")


# ------------------------------------------------------------------
# Scenario 28: Thought factories — create / create_with_timestamp
# ------------------------------------------------------------------


def scenario_thought_factories() -> None:
    """Thought.create and create_with_timestamp produce valid thoughts."""
    t1 = Thought.create("Test thought")
    assert t1.content == "Test thought"
    assert t1.created_at > 0

    t2 = Thought.create_with_timestamp("Timed thought", created_at=500.0)
    assert t2.created_at == 500.0
    assert t2.step_id is None

    print(f"[PASS] thought_factories               | create() ts={t1.created_at:.1f} "
          f"create_with_timestamp() ts={t2.created_at}")


# ------------------------------------------------------------------
# Scenario 29: ThoughtStep factory
# ------------------------------------------------------------------


def scenario_thought_step_factory() -> None:
    """ThoughtStep.create produces a valid step."""
    step = ThoughtStep.create(
        name="Research",
        description="Gather information",
        order=1,
        effort_estimate=0.7,
        metadata={"source": "demo"},
    )
    assert step.name == "Research"
    assert step.description == "Gather information"
    assert step.order == 1
    assert step.effort_estimate == 0.7
    assert step.metadata == {"source": "demo"}
    print(f"[PASS] thought_step_factory            | name='{step.name}' "
          f"order={step.order} effort={step.effort_estimate}")


# ------------------------------------------------------------------
# Scenario 30: ThoughtPlan factory
# ------------------------------------------------------------------


def scenario_thought_plan_factory() -> None:
    """ThoughtPlan.create and create_with_timestamp produce valid plans."""
    step = ThoughtStep.create("Step 1")
    plan1 = ThoughtPlan.create("Plan Test", steps=[step], metadata={"v": "1"})
    assert plan1.task_name == "Plan Test"
    assert len(plan1.steps) == 1
    assert plan1.metadata == {"v": "1"}

    plan2 = ThoughtPlan.create_with_timestamp("Timed Plan", created_at=1000.0)
    assert plan2.created_at == 1000.0
    assert len(plan2.steps) == 0

    print(f"[PASS] thought_plan_factory            | create() steps={len(plan1.steps)} "
          f"create_with_timestamp() ts={plan2.created_at}")


# ------------------------------------------------------------------
# Scenario 31: ThoughtContext factory
# ------------------------------------------------------------------


def scenario_thought_context_factory() -> None:
    """ThoughtContext.create and create_with_id produce valid contexts."""
    ctx1 = ThoughtContext.create(
        task_name="Test",
        complexity="complex",
        domain="engineering",
        requirements=["r1", "r2"],
        metadata={"env": "test"},
    )
    assert ctx1.task_name == "Test"
    assert ctx1.complexity == "complex"
    assert ctx1.domain == "engineering"
    assert ctx1.requirements == ("r1", "r2")

    task_id = uuid4()
    ctx2 = ThoughtContext.create_with_id(task_id=task_id, task_name="Explicit")
    assert ctx2.task_id == task_id
    assert ctx2.task_name == "Explicit"

    print(f"[PASS] thought_context_factory          | create() reqs={ctx1.requirements} "
          f"create_with_id() id={ctx2.task_id.hex[:8]}")


# ------------------------------------------------------------------
# Scenario 32: execute_next_step — múltiplas etapas em sequência
# ------------------------------------------------------------------


def scenario_execute_multiple_steps() -> None:
    """Multiple execute_next_step calls consume all steps."""
    steps = [
        ThoughtStep.create("A", effort_estimate=0.2),
        ThoughtStep.create("B", effort_estimate=0.3),
        ThoughtStep.create("C", effort_estimate=0.5),
    ]
    plan = ThoughtPlan.create(task_name="Sequential", steps=steps)
    ctx = ThoughtRuntime.receive_task("Sequential")

    thoughts = []
    while plan.steps:
        plan, thought = ThoughtRuntime.execute_next_step(plan, ctx)
        if thought is not None:
            thoughts.append(thought)

    assert len(thoughts) == 3
    assert [t.step_id for t in thoughts] == [s.step_id for s in steps]
    print(f"[PASS] execute_multiple_steps           | {len(thoughts)} thoughts "
          f"consumed all steps")


# ------------------------------------------------------------------
# Scenario 33: trace com todas as etapas
# ------------------------------------------------------------------


def scenario_trace_all_stages() -> None:
    """Trace can represent all pipeline stages."""
    stages = [
        "receive_task", "analyze_task", "build_plan",
        "prioritize_steps", "execute_step_0", "execute_step_1",
        "build_trace", "build_result",
    ]
    step_a = ThoughtStep.create("Step A", effort_estimate=0.3)
    step_b = ThoughtStep.create("Step B", effort_estimate=0.4)
    plan = ThoughtPlan.create(task_name="Full", steps=[step_a, step_b])
    trace = ThoughtRuntime.build_trace(
        stages=stages,
        plan=plan,
        original_planned_count=2,
        prioritized_count=2,
        thoughts_generated=2,
        timestamps={s: float(i) for i, s in enumerate(stages)},
    )

    assert len(trace.stages) == 8
    assert trace.steps_planned == 2
    assert trace.thoughts_generated == 2
    assert trace.total_effort == 0.7
    print(f"[PASS] trace_all_stages                 | stages={len(trace.stages)} "
          f"effort={trace.total_effort:.1f}")


# ------------------------------------------------------------------
# Scenario 34: plano vazio
# ------------------------------------------------------------------


def scenario_empty_plan() -> None:
    """An empty plan has no steps, is complete, and has zero effort."""
    plan = ThoughtPlan.create(task_name="Empty")

    assert ThoughtRuntime.is_complete(plan) is True
    assert ThoughtRuntime.get_next_step(plan) is None
    assert ThoughtRuntime.steps_remaining(plan) == 0
    assert ThoughtRuntime.calculate_total_effort(plan) == 0.0
    print(f"[PASS] empty_plan                       | is_complete=True "
          f"remaining=0 effort=0.0")


# ------------------------------------------------------------------
# Scenario 35: full_pipeline — sem requirements
# ------------------------------------------------------------------


def scenario_full_pipeline_no_requirements() -> None:
    """full_pipeline works without explicit requirements."""
    result = ThoughtRuntime.full_pipeline("Simple task")

    assert result.success is True
    assert result.context.complexity == "simple"
    print(f"[PASS] full_pipeline_no_requirements    | complexity="
          f"{result.context.complexity} success={result.success}")


# ------------------------------------------------------------------
# Scenario 36: build_trace sem timestamps
# ------------------------------------------------------------------


def scenario_trace_no_timestamps() -> None:
    """build_trace works without timestamps."""
    trace = ThoughtRuntime.build_trace(
        stages=["receive"],
        plan=ThoughtPlan.create(task_name="No TS"),
        original_planned_count=0,
        prioritized_count=0,
        thoughts_generated=0,
    )

    assert trace.timestamps == {}
    print(f"[PASS] trace_no_timestamps             | timestamps={trace.timestamps}")


# ------------------------------------------------------------------
# Scenario 37: custom_steps no full_pipeline
# ------------------------------------------------------------------


def scenario_full_pipeline_custom_steps() -> None:
    """full_pipeline accepts custom explicit steps."""
    steps = [
        ThoughtStep.create("Custom 1", effort_estimate=0.5),
        ThoughtStep.create("Custom 2", effort_estimate=0.3),
    ]
    result = ThoughtRuntime.full_pipeline(
        "Custom Pipeline",
        requirements=["r1"],
        custom_steps=steps,
    )

    assert result.success is True
    assert result.trace is not None
    # With 2 custom steps, should have 2 executed thoughts
    assert len(result.executed_thoughts) == 2
    print(f"[PASS] full_pipeline_custom_steps       | thoughts="
          f"{len(result.executed_thoughts)} steps=2")


# ------------------------------------------------------------------
# Scenario 38: result with executed_thoughts
# ------------------------------------------------------------------


def scenario_result_with_thoughts() -> None:
    """ThoughtResult stores executed thoughts."""
    thought = Thought.create("Processed thought", step_id=uuid4())
    ctx = ThoughtRuntime.receive_task("Thought in result")
    trace = ThoughtRuntime.build_trace(
        stages=["execute"],
        plan=ThoughtPlan.create(task_name="T"),
        prioritized_count=0,
        thoughts_generated=1,
    )

    result = ThoughtRuntime.build_result(
        context=ctx, trace=trace, success=True,
        executed_thoughts=[thought],
    )

    assert len(result.executed_thoughts) == 1
    assert result.executed_thoughts[0].content == "Processed thought"
    print(f"[PASS] result_with_thoughts             | thoughts="
          f"{len(result.executed_thoughts)} "
          f"content='{result.executed_thoughts[0].content}'")


# ------------------------------------------------------------------
# Main
# ------------------------------------------------------------------


def main() -> None:
    print("=" * 58)
    print("Employee Cognitive Foundation Demo")
    print("=" * 58)
    print()

    scenario_receive_task()
    scenario_receive_task_with_employee()
    scenario_receive_task_with_metadata()
    scenario_analyze_simple()
    scenario_analyze_medium()
    scenario_analyze_complex()
    scenario_analyze_domain()
    scenario_build_plan_simple()
    scenario_build_plan_complex()
    scenario_build_plan_effort()
    scenario_prioritize_by_effort()
    scenario_prioritize_tiebreaker()
    scenario_execute_next_step()
    scenario_execute_empty_plan()
    scenario_execute_custom_content()
    scenario_get_next_step()
    scenario_is_complete()
    scenario_calculate_total_effort()
    scenario_steps_counts()
    scenario_build_trace()
    scenario_build_result()
    scenario_build_result_error()
    scenario_full_pipeline_simple()
    scenario_full_pipeline_complex()
    scenario_full_pipeline_custom_contents()
    scenario_determinism()
    scenario_frozen_dataclasses()
    scenario_thought_factories()
    scenario_thought_step_factory()
    scenario_thought_plan_factory()
    scenario_thought_context_factory()
    scenario_execute_multiple_steps()
    scenario_trace_all_stages()
    scenario_empty_plan()
    scenario_full_pipeline_no_requirements()
    scenario_trace_no_timestamps()
    scenario_full_pipeline_custom_steps()
    scenario_result_with_thoughts()

    print()
    print("=" * 58)
    print(f"All {38} Employee Cognition scenarios passed.")
    print("=" * 58)


if __name__ == "__main__":
    main()
