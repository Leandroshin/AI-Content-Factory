"""Cognitive Employee Foundation.

Stateless, deterministic cognitive planning for employees.
No AI, no IO, no async, no threads — pure step orchestration.

Pipeline: receive_task → analyze_task → build_plan →
          prioritize_steps → execute_next_step → build_result
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Any
from uuid import UUID, uuid4


# ------------------------------------------------------------------
# Thought
# ------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class Thought:
    """A single cognitive unit produced during step execution.

    Attributes:
        thought_id: Unique identifier for this thought.
        step_id: The step that produced this thought (None for free thoughts).
        content: The cognitive content of the thought.
        created_at: Unix timestamp of creation.
    """

    thought_id: UUID
    step_id: UUID | None
    content: str
    created_at: float

    @staticmethod
    def create(
        content: str,
        step_id: UUID | None = None,
    ) -> Thought:
        """Factory that auto-generates thought_id and timestamp."""
        return Thought(
            thought_id=uuid4(),
            step_id=step_id,
            content=content,
            created_at=time.time(),
        )

    @staticmethod
    def create_with_timestamp(
        content: str,
        created_at: float,
        step_id: UUID | None = None,
    ) -> Thought:
        """Factory with explicit timestamp (for determinism in tests)."""
        return Thought(
            thought_id=uuid4(),
            step_id=step_id,
            content=content,
            created_at=created_at,
        )


# ------------------------------------------------------------------
# ThoughtStep
# ------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class ThoughtStep:
    """A single step within a cognitive plan.

    Attributes:
        step_id: Unique identifier for this step.
        name: Human-readable step name.
        description: Optional description of the step.
        order: Sequential position (0-based).
        effort_estimate: Estimated effort (0.0 to 1.0).
        metadata: Optional extra data.
    """

    step_id: UUID
    name: str
    description: str = ""
    order: int = 0
    effort_estimate: float = 0.5
    metadata: dict[str, Any] = field(default_factory=dict)

    @staticmethod
    def create(
        name: str,
        description: str = "",
        order: int = 0,
        effort_estimate: float = 0.5,
        metadata: dict[str, Any] | None = None,
    ) -> ThoughtStep:
        """Factory that auto-generates step_id."""
        return ThoughtStep(
            step_id=uuid4(),
            name=name,
            description=description,
            order=order,
            effort_estimate=effort_estimate,
            metadata=dict(metadata) if metadata else {},
        )


# ------------------------------------------------------------------
# ThoughtPlan
# ------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class ThoughtPlan:
    """A cognitive plan containing ordered steps.

    Attributes:
        plan_id: Unique identifier for this plan.
        task_name: Name of the task this plan addresses.
        steps: Ordered tuple of ThoughtStep instances.
        created_at: Unix timestamp of creation.
        metadata: Optional extra data.
    """

    plan_id: UUID
    task_name: str
    steps: tuple[ThoughtStep, ...] = ()
    created_at: float = 0.0
    metadata: dict[str, Any] = field(default_factory=dict)

    @staticmethod
    def create(
        task_name: str,
        steps: tuple[ThoughtStep, ...] | list[ThoughtStep] | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> ThoughtPlan:
        """Factory that auto-generates plan_id and timestamp."""
        return ThoughtPlan(
            plan_id=uuid4(),
            task_name=task_name,
            steps=tuple(steps) if steps else (),
            created_at=time.time(),
            metadata=dict(metadata) if metadata else {},
        )

    @staticmethod
    def create_with_timestamp(
        task_name: str,
        created_at: float,
        steps: tuple[ThoughtStep, ...] | list[ThoughtStep] | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> ThoughtPlan:
        """Factory with explicit timestamp (for determinism in tests)."""
        return ThoughtPlan(
            plan_id=uuid4(),
            task_name=task_name,
            steps=tuple(steps) if steps else (),
            created_at=created_at,
            metadata=dict(metadata) if metadata else {},
        )


# ------------------------------------------------------------------
# ThoughtContext
# ------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class ThoughtContext:
    """Cognitive context for processing a task.

    Attributes:
        task_id: The task being processed.
        task_name: Human-readable task name.
        employee_id: Optional employee performing the task.
        complexity: Task complexity ("simple", "medium", "complex").
        domain: Knowledge domain of the task.
        requirements: Explicit requirements for the task.
        metadata: Optional extra data.
    """

    task_id: UUID
    task_name: str
    employee_id: UUID | None = None
    complexity: str = "simple"
    domain: str = "general"
    requirements: tuple[str, ...] = ()
    metadata: dict[str, Any] = field(default_factory=dict)

    @staticmethod
    def create(
        task_name: str,
        employee_id: UUID | None = None,
        complexity: str = "simple",
        domain: str = "general",
        requirements: tuple[str, ...] | list[str] | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> ThoughtContext:
        """Factory that auto-generates task_id."""
        return ThoughtContext(
            task_id=uuid4(),
            task_name=task_name,
            employee_id=employee_id,
            complexity=complexity,
            domain=domain,
            requirements=tuple(requirements) if requirements else (),
            metadata=dict(metadata) if metadata else {},
        )

    @staticmethod
    def create_with_id(
        task_id: UUID,
        task_name: str,
        employee_id: UUID | None = None,
        complexity: str = "simple",
        domain: str = "general",
        requirements: tuple[str, ...] | list[str] | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> ThoughtContext:
        """Factory with explicit task_id."""
        return ThoughtContext(
            task_id=task_id,
            task_name=task_name,
            employee_id=employee_id,
            complexity=complexity,
            domain=domain,
            requirements=tuple(requirements) if requirements else (),
            metadata=dict(metadata) if metadata else {},
        )


# ------------------------------------------------------------------
# ThoughtTrace
# ------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class ThoughtTrace:
    """Execution trace for cognitive processing.

    Attributes:
        stages: Ordered stage names that were executed.
        steps_planned: Number of steps in the plan.
        steps_prioritized: Number of steps after prioritization.
        thoughts_generated: Number of thoughts produced.
        timestamps: Dict mapping stage name to Unix timestamp.
        total_effort: Sum of effort_estimates across all steps.
    """

    stages: tuple[str, ...] = ()
    steps_planned: int = 0
    steps_prioritized: int = 0
    thoughts_generated: int = 0
    timestamps: dict[str, float] = field(default_factory=dict)
    total_effort: float = 0.0


# ------------------------------------------------------------------
# ThoughtResult
# ------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class ThoughtResult:
    """Outcome of a cognitive processing cycle.

    Attributes:
        success: True if the cycle completed without errors.
        plan: The cognitive plan (None if planning failed).
        context: The cognitive context used.
        trace: Execution trace with timing and metrics.
        executed_thoughts: Thoughts produced during execution.
        error_message: Human-readable error (empty on success).
    """

    success: bool
    plan: ThoughtPlan | None = None
    context: ThoughtContext | None = None
    trace: ThoughtTrace | None = None
    executed_thoughts: tuple[Thought, ...] = ()
    error_message: str = ""


# ------------------------------------------------------------------
# ThoughtRuntime
# ------------------------------------------------------------------


_CONSTANTS = {
    "simple": {"min_steps": 1, "max_steps": 2, "keywords": []},
    "medium": {"min_steps": 3, "max_steps": 4, "keywords": ["analyze", "review", "design", "plan"]},
    "complex": {"min_steps": 5, "max_steps": 6, "keywords": ["architect", "optimize", "migrate", "integrate", "transform"]},
}


def _infer_complexity(task_name: str, requirements: tuple[str, ...]) -> str:
    """Infer task complexity from name and requirements."""
    req_count = len(requirements)
    if req_count >= 5:
        return "complex"
    name_lower = task_name.lower()
    for kw in _CONSTANTS["complex"]["keywords"]:
        if kw in name_lower:
            return "complex"
    if req_count >= 3:
        return "medium"
    for kw in _CONSTANTS["medium"]["keywords"]:
        if kw in name_lower:
            return "medium"
    return "simple"


def _infer_domain(task_name: str, requirements: tuple[str, ...]) -> str:
    """Infer knowledge domain from task name and requirements."""
    all_text = f"{task_name} {' '.join(requirements)}".lower()
    domain_map: list[tuple[list[str], str]] = [
        (["code", "develop", "program", "software", "python", "api"], "engineering"),
        (["design", "ui", "ux", "layout", "visual"], "design"),
        (["data", "analytics", "report", "metric", "dashboard"], "data"),
        (["write", "content", "article", "doc", "manual"], "content"),
        (["test", "qa", "quality", "validate"], "testing"),
        (["deploy", "release", "ci", "cd", "infra"], "devops"),
        (["research", "study", "investigate", "survey"], "research"),
    ]
    for keywords, domain in domain_map:
        if any(kw in all_text for kw in keywords):
            return domain
    return "general"


class ThoughtRuntime:
    """Stateless runtime for cognitive planning.

    All methods are deterministic pure functions — they take inputs
    and return outputs without mutating any internal state.
    """

    # ------------------------------------------------------------------
    # Pipeline: receive_task
    # ------------------------------------------------------------------

    @staticmethod
    def receive_task(
        task_name: str,
        employee_id: UUID | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> ThoughtContext:
        """Receive a task and create initial cognitive context.

        Args:
            task_name: Human-readable task name.
            employee_id: Optional employee performing the task.
            metadata: Optional extra metadata.

        Returns:
            A new ThoughtContext with default values.
        """
        return ThoughtContext.create(
            task_name=task_name,
            employee_id=employee_id,
            complexity="simple",
            domain="general",
            metadata=dict(metadata) if metadata else {},
        )

    # ------------------------------------------------------------------
    # Pipeline: analyze_task
    # ------------------------------------------------------------------

    @staticmethod
    def analyze_task(
        context: ThoughtContext,
        requirements: tuple[str, ...] | list[str] | None = None,
    ) -> ThoughtContext:
        """Analyze a task and enrich the context with complexity, domain,
        and requirements.

        Args:
            context: The current cognitive context.
            requirements: Explicit requirements for the task.

        Returns:
            An enriched ThoughtContext.
        """
        reqs = tuple(requirements) if requirements else context.requirements
        complexity = _infer_complexity(context.task_name, reqs)
        domain = _infer_domain(context.task_name, reqs)
        return ThoughtContext(
            task_id=context.task_id,
            task_name=context.task_name,
            employee_id=context.employee_id,
            complexity=complexity,
            domain=domain,
            requirements=reqs,
            metadata=dict(context.metadata),
        )

    # ------------------------------------------------------------------
    # Pipeline: build_plan
    # ------------------------------------------------------------------

    @staticmethod
    def build_plan(
        context: ThoughtContext,
        custom_steps: tuple[ThoughtStep, ...] | list[ThoughtStep] | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> ThoughtPlan:
        """Build a cognitive plan from the analyzed context.

        The number of steps is determined by complexity:
        - simple: 1-2 steps
        - medium: 3-4 steps
        - complex: 5-6 steps

        Args:
            context: The analyzed cognitive context.
            custom_steps: Optional explicit steps (bypasses auto-generation).
            metadata: Optional plan-level metadata.

        Returns:
            A new ThoughtPlan.
        """
        if custom_steps is not None:
            steps = list(custom_steps)
        else:
            steps = ThoughtRuntime._generate_steps(context)

        merged_meta = dict(metadata) if metadata else {}
        merged_meta["complexity"] = context.complexity
        merged_meta["domain"] = context.domain

        return ThoughtPlan.create(
            task_name=context.task_name,
            steps=steps,
            metadata=merged_meta,
        )

    @staticmethod
    def _generate_steps(context: ThoughtContext) -> list[ThoughtStep]:
        """Generate default steps based on context complexity and domain."""
        steps: list[ThoughtStep] = []
        complexity = context.complexity
        cfg = _CONSTANTS.get(complexity, _CONSTANTS["simple"])
        num_steps = cfg["max_steps"]

        # Common base steps adjusted by complexity
        base = [
            ("Understand", "Comprehend the task requirements", 0.3),
            ("Research", "Gather relevant information", 0.5),
            ("Plan", "Outline the approach and strategy", 0.4),
        ]

        if complexity == "simple":
            base = base[:1]
        elif complexity == "medium":
            base = base[:3]
        else:
            base = base[:3]

        domain_suffix = context.domain.capitalize()
        specialized = []
        if complexity == "medium":
            specialized = [
                (f"Execute in {domain_suffix}", f"Carry out the work in {context.domain}", 0.7),
            ]
        elif complexity == "complex":
            specialized = [
                (f"Execute in {domain_suffix}", f"Carry out the work in {context.domain}", 0.6),
                ("Review", "Review the output for quality", 0.4),
                ("Optimize", "Optimize and refine the result", 0.5),
            ]

        all_steps = base + specialized

        for i, (name, desc, effort) in enumerate(all_steps[:num_steps]):
            steps.append(ThoughtStep.create(
                name=name,
                description=desc if "," not in desc else desc,
                order=i,
                effort_estimate=effort,
                metadata={"source": "auto_generated", "complexity": complexity},
            ))

        return steps

    # ------------------------------------------------------------------
    # Pipeline: prioritize_steps
    # ------------------------------------------------------------------

    @staticmethod
    def prioritize_steps(plan: ThoughtPlan) -> ThoughtPlan:
        """Reorder steps by priority: quick wins first (lower effort),
        then original order for ties.

        Args:
            plan: The current cognitive plan.

        Returns:
            A new ThoughtPlan with reordered steps.
        """
        sorted_steps = sorted(
            plan.steps,
            key=lambda s: (s.effort_estimate, s.order),
        )
        reordered = tuple(
            ThoughtStep(
                step_id=s.step_id,
                name=s.name,
                description=s.description,
                order=i,
                effort_estimate=s.effort_estimate,
                metadata=dict(s.metadata),
            )
            for i, s in enumerate(sorted_steps)
        )
        return ThoughtPlan(
            plan_id=plan.plan_id,
            task_name=plan.task_name,
            steps=reordered,
            created_at=plan.created_at,
            metadata=dict(plan.metadata),
        )

    # ------------------------------------------------------------------
    # Pipeline: execute_next_step
    # ------------------------------------------------------------------

    @staticmethod
    def execute_next_step(
        plan: ThoughtPlan,
        context: ThoughtContext,
        thought_content: str | None = None,
    ) -> tuple[ThoughtPlan, Thought | None]:
        """Execute (simulate) the next pending step.

        Removes the first step from the plan and produces a Thought.

        Args:
            plan: The current cognitive plan.
            context: The cognitive context.
            thought_content: Optional explicit thought content.
                If omitted, a default message is generated.

        Returns:
            A tuple of (updated plan without the executed step, the Thought).
            If no steps remain, returns (plan, None).
        """
        if not plan.steps:
            return plan, None

        step = plan.steps[0]
        remaining = plan.steps[1:]

        if thought_content is not None:
            content = thought_content
        else:
            content = (
                f"Cognitive step '{step.name}' for task "
                f"'{context.task_name}': {step.description}"
            )

        thought = Thought.create(content=content, step_id=step.step_id)

        updated_plan = ThoughtPlan(
            plan_id=plan.plan_id,
            task_name=plan.task_name,
            steps=remaining,
            created_at=plan.created_at,
            metadata=dict(plan.metadata),
        )

        return updated_plan, thought

    # ------------------------------------------------------------------
    # Pipeline: build_trace
    # ------------------------------------------------------------------

    @staticmethod
    def build_trace(
        stages: tuple[str, ...] | list[str],
        plan: ThoughtPlan | None = None,
        original_planned_count: int | None = None,
        prioritized_count: int = 0,
        thoughts_generated: int = 0,
        timestamps: dict[str, float] | None = None,
    ) -> ThoughtTrace:
        """Assemble a ThoughtTrace from pipeline stage data.

        Args:
            stages: Ordered stage names that were executed.
            plan: The plan (or None if planning failed).
            original_planned_count: Original step count before execution.
                If omitted, defaults to remaining steps in plan.
            prioritized_count: Number of steps after prioritization.
            thoughts_generated: Number of thoughts produced.
            timestamps: Optional dict of stage timestamps.

        Returns:
            A new ThoughtTrace.
        """
        if original_planned_count is not None:
            steps_planned = original_planned_count
        else:
            steps_planned = len(plan.steps) if plan else 0
        total_effort = sum(s.effort_estimate for s in plan.steps) if plan else 0.0

        return ThoughtTrace(
            stages=tuple(stages),
            steps_planned=steps_planned,
            steps_prioritized=prioritized_count,
            thoughts_generated=thoughts_generated,
            timestamps=dict(timestamps) if timestamps else {},
            total_effort=total_effort,
        )

    # ------------------------------------------------------------------
    # Pipeline: build_result
    # ------------------------------------------------------------------

    @staticmethod
    def build_result(
        context: ThoughtContext,
        plan: ThoughtPlan | None = None,
        trace: ThoughtTrace | None = None,
        executed_thoughts: tuple[Thought, ...] | list[Thought] | None = None,
        success: bool = True,
        error_message: str = "",
    ) -> ThoughtResult:
        """Assemble a ThoughtResult from pipeline data.

        Args:
            context: The cognitive context used.
            plan: The cognitive plan (None if planning failed).
            trace: Execution trace.
            executed_thoughts: Thoughts produced.
            success: Whether the cycle succeeded.
            error_message: Error description (empty on success).

        Returns:
            A new ThoughtResult.
        """
        return ThoughtResult(
            success=success,
            plan=plan,
            context=context,
            trace=trace,
            executed_thoughts=tuple(executed_thoughts) if executed_thoughts else (),
            error_message=error_message,
        )

    @staticmethod
    def full_pipeline(
        task_name: str,
        *,
        employee_id: UUID | None = None,
        requirements: tuple[str, ...] | list[str] | None = None,
        metadata: dict[str, Any] | None = None,
        custom_steps: tuple[ThoughtStep, ...] | list[ThoughtStep] | None = None,
        thought_contents: list[str] | None = None,
    ) -> ThoughtResult:
        """Run the full cognitive pipeline end-to-end.

        Convenience method that calls all stages in order.

        Args:
            task_name: Human-readable task name.
            employee_id: Optional employee performing the task.
            requirements: Explicit requirements.
            metadata: Optional metadata.
            custom_steps: Optional explicit steps (bypasses auto-generation).
            thought_contents: Optional explicit thought contents per step.

        Returns:
            A ThoughtResult from the completed pipeline.
        """
        ts: dict[str, float] = {}

        ctx = ThoughtRuntime.receive_task(task_name, employee_id, metadata)
        ts["receive_task"] = time.time()

        ctx = ThoughtRuntime.analyze_task(ctx, requirements)
        ts["analyze_task"] = time.time()

        plan = ThoughtRuntime.build_plan(ctx, custom_steps)
        original_step_count = len(plan.steps)
        ts["build_plan"] = time.time()

        plan = ThoughtRuntime.prioritize_steps(plan)
        prioritized_count = len(plan.steps)
        ts["prioritize_steps"] = time.time()

        thoughts: list[Thought] = []
        step_idx = 0
        while plan.steps:
            content = thought_contents[step_idx] if thought_contents and step_idx < len(thought_contents) else None
            plan, thought = ThoughtRuntime.execute_next_step(plan, ctx, content)
            ts[f"execute_step_{step_idx}"] = time.time()
            if thought is not None:
                thoughts.append(thought)
            step_idx += 1

        trace = ThoughtRuntime.build_trace(
            stages=["receive_task", "analyze_task", "build_plan", "prioritize_steps"] +
                   [f"execute_step_{i}" for i in range(len(thoughts))],
            plan=plan,
            original_planned_count=original_step_count,
            prioritized_count=prioritized_count,
            thoughts_generated=len(thoughts),
            timestamps=ts,
        )

        return ThoughtRuntime.build_result(
            context=ctx,
            plan=plan,
            trace=trace,
            executed_thoughts=thoughts,
            success=True,
        )

    # ------------------------------------------------------------------
    # Queries
    # ------------------------------------------------------------------

    @staticmethod
    def get_next_step(plan: ThoughtPlan) -> ThoughtStep | None:
        """Get the next pending step, or None if the plan is empty."""
        if not plan.steps:
            return None
        return plan.steps[0]

    @staticmethod
    def is_complete(plan: ThoughtPlan) -> bool:
        """Check whether the plan has no remaining steps."""
        return len(plan.steps) == 0

    @staticmethod
    def calculate_total_effort(plan: ThoughtPlan) -> float:
        """Calculate total effort across all steps."""
        return sum(s.effort_estimate for s in plan.steps)

    @staticmethod
    def steps_remaining(plan: ThoughtPlan) -> int:
        """Count remaining steps in the plan."""
        return len(plan.steps)

    @staticmethod
    def steps_completed(original_total: int, plan: ThoughtPlan) -> int:
        """Calculate completed steps."""
        return original_total - len(plan.steps)
