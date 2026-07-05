"""Execution Plan Runtime Foundation — transforms validated plans into executable actions.

Consumes a StrategyExecutionPlan (from Strategy Pipeline) and produces
a deterministic ExecutionPlan with concrete ExecutionActions organized
by approval state, estimated costs, and estimated durations.

100% stateless. All methods are @staticmethod. All models are frozen dataclasses.
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any
from uuid import UUID, uuid4

from core.policy.foundation import RESULT_APPROVED, RESULT_MANUAL_APPROVAL

if TYPE_CHECKING:
    from core.strategy.pipeline import StrategyExecutionItem, StrategyExecutionPlan

# ------------------------------------------------------------------
# Constants
# ------------------------------------------------------------------

PRIORITY_LOW = "LOW"
PRIORITY_MEDIUM = "MEDIUM"
PRIORITY_HIGH = "HIGH"
PRIORITY_CRITICAL = "CRITICAL"

_PRIORITY_ORDER = {PRIORITY_LOW: 0, PRIORITY_MEDIUM: 1, PRIORITY_HIGH: 2, PRIORITY_CRITICAL: 3}

# ------------------------------------------------------------------
# Data models
# ------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class ExecutionAction:
    """A single concrete action derived from a validated strategy item."""

    action_id: UUID
    recommendation_id: UUID
    category: str
    priority: str
    title: str
    description: str
    estimated_duration: float
    estimated_cost: float
    can_execute: bool
    requires_manual_approval: bool
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class ExecutionPlan:
    """Collection of actions organized by execution readiness."""

    actions: tuple[ExecutionAction, ...] = field(default_factory=tuple)
    approved_actions: tuple[ExecutionAction, ...] = field(default_factory=tuple)
    manual_actions: tuple[ExecutionAction, ...] = field(default_factory=tuple)
    blocked_actions: tuple[ExecutionAction, ...] = field(default_factory=tuple)
    estimated_total_duration: float = 0.0
    estimated_total_cost: float = 0.0
    created_at: float = 0.0
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class ExecutionPlanTrace:
    """Metadata about an execution plan build operation."""

    stages: tuple[str, ...] = field(default_factory=tuple)
    duration_ms: float = 0.0
    metrics: dict[str, float] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class ExecutionPlanResult:
    """Output of an execution plan build operation."""

    success: bool
    plan: ExecutionPlan | None = None
    trace: ExecutionPlanTrace | None = None
    error_message: str = ""


# ------------------------------------------------------------------
# Constants for default estimates
# ------------------------------------------------------------------

DEFAULT_DURATION_PER_ACTION: float = 10.0
DEFAULT_COST_PER_ACTION: float = 1.0
DEFAULT_COST_APPROVED_MULTIPLIER: float = 1.0
DEFAULT_COST_MANUAL_MULTIPLIER: float = 0.5
DEFAULT_COST_BLOCKED_MULTIPLIER: float = 0.0
DEFAULT_DURATION_APPROVED_MULTIPLIER: float = 1.0
DEFAULT_DURATION_MANUAL_MULTIPLIER: float = 2.5  # manual review takes longer
DEFAULT_DURATION_BLOCKED_MULTIPLIER: float = 0.0


# ------------------------------------------------------------------
# Helpers
# ------------------------------------------------------------------


def _now() -> float:
    return time.time()


def _action_from_item(
    item: StrategyExecutionItem,
    action_id: UUID | None = None,
    estimated_duration: float = DEFAULT_DURATION_PER_ACTION,
    estimated_cost: float = DEFAULT_COST_PER_ACTION,
) -> ExecutionAction:
    """Convert a StrategyExecutionItem into an ExecutionAction."""
    return ExecutionAction(
        action_id=action_id or uuid4(),
        recommendation_id=item.recommendation_id,
        category=item.category,
        priority=item.priority,
        title=f"{item.category} — {item.policy_result}",
        description=item.reason,
        estimated_duration=estimated_duration,
        estimated_cost=estimated_cost,
        can_execute=item.can_execute,
        requires_manual_approval=item.requires_manual_approval,
        metadata={
            "source": "execution_plan_foundation",
            "policy_result": item.policy_result,
            **item.metadata,
        },
    )


def _action_cost_multiplier(can_execute: bool, requires_manual: bool) -> float:
    if not can_execute and not requires_manual:
        return DEFAULT_COST_BLOCKED_MULTIPLIER
    if requires_manual:
        return DEFAULT_COST_MANUAL_MULTIPLIER
    return DEFAULT_COST_APPROVED_MULTIPLIER


def _action_duration_multiplier(can_execute: bool, requires_manual: bool) -> float:
    if not can_execute and not requires_manual:
        return DEFAULT_DURATION_BLOCKED_MULTIPLIER
    if requires_manual:
        return DEFAULT_DURATION_MANUAL_MULTIPLIER
    return DEFAULT_DURATION_APPROVED_MULTIPLIER


def _estimate_cost_for_action(
    action: ExecutionAction,
    base_cost: float = DEFAULT_COST_PER_ACTION,
) -> float:
    return base_cost * _action_cost_multiplier(action.can_execute, action.requires_manual_approval)


def _estimate_duration_for_action(
    action: ExecutionAction,
    base_duration: float = DEFAULT_DURATION_PER_ACTION,
) -> float:
    return base_duration * _action_duration_multiplier(action.can_execute, action.requires_manual_approval)


def _build_execution_plan(
    actions: list[ExecutionAction],
    metadata: dict[str, Any] | None = None,
) -> ExecutionPlan:
    """Build an ExecutionPlan from a list of actions."""
    approved: list[ExecutionAction] = []
    manual: list[ExecutionAction] = []
    blocked: list[ExecutionAction] = []

    for a in actions:
        if a.can_execute and not a.requires_manual_approval:
            approved.append(a)
        elif a.requires_manual_approval:
            manual.append(a)
        else:
            blocked.append(a)

    total_duration = sum(a.estimated_duration for a in actions)
    total_cost = sum(a.estimated_cost for a in actions)

    return ExecutionPlan(
        actions=tuple(actions),
        approved_actions=tuple(approved),
        manual_actions=tuple(manual),
        blocked_actions=tuple(blocked),
        estimated_total_duration=total_duration,
        estimated_total_cost=total_cost,
        created_at=_now(),
        metadata=metadata or {},
    )


# ------------------------------------------------------------------
# FoundationExecutionPlanRuntime
# ------------------------------------------------------------------


class FoundationExecutionPlanRuntime:
    """Stateless execution plan runtime.

    Consumes a StrategyExecutionPlan and transforms validated items
    into concrete ExecutionActions organized by approval state,
    with estimated costs and durations.
    """

    # --------------------------------------------------------------
    # Core
    # --------------------------------------------------------------

    @staticmethod
    def build(
        strategy_plan: StrategyExecutionPlan,
        base_duration: float = DEFAULT_DURATION_PER_ACTION,
        base_cost: float = DEFAULT_COST_PER_ACTION,
        metadata: dict[str, Any] | None = None,
    ) -> ExecutionPlanResult:
        """Build an ExecutionPlan from a StrategyExecutionPlan.

        Args:
            strategy_plan: The validated strategy execution plan.
            base_duration: Default duration per action in seconds.
            base_cost: Default cost per action in currency units.
            metadata: Optional metadata to attach to the plan.

        Returns:
            An ExecutionPlanResult with the built plan and trace.
        """
        stages: list[str] = []
        start = _now()
        stages.append("build")

        actions = FoundationExecutionPlanRuntime.build_actions(
            strategy_plan,
            base_duration=base_duration,
            base_cost=base_cost,
        )
        stages.append("build_actions")

        merged_metadata = dict(strategy_plan.metadata)
        if metadata:
            merged_metadata.update(metadata)
        plan = _build_execution_plan(actions, merged_metadata)
        stages.append("assemble_plan")

        duration = (_now() - start) * 1000.0
        metrics: dict[str, float] = {
            "total_actions": float(len(plan.actions)),
            "approved_actions": float(len(plan.approved_actions)),
            "manual_actions": float(len(plan.manual_actions)),
            "blocked_actions": float(len(plan.blocked_actions)),
            "estimated_total_duration": plan.estimated_total_duration,
            "estimated_total_cost": plan.estimated_total_cost,
        }
        trace = ExecutionPlanTrace(
            stages=tuple(stages),
            duration_ms=duration,
            metrics=metrics,
        )
        return ExecutionPlanResult(success=True, plan=plan, trace=trace)

    @staticmethod
    def build_actions(
        strategy_plan: StrategyExecutionPlan,
        base_duration: float = DEFAULT_DURATION_PER_ACTION,
        base_cost: float = DEFAULT_COST_PER_ACTION,
    ) -> list[ExecutionAction]:
        """Convert a StrategyExecutionPlan into a list of ExecutionActions.

        Rules:
        - APPROVED → action with can_execute=True
        - MANUAL_APPROVAL → action with requires_manual_approval=True
        - BLOCKED → action with can_execute=False, requires_manual=False
        - REJECTED → skipped (not included)
        - NOT_APPLICABLE → skipped (not included)
        """
        actions: list[ExecutionAction] = []

        for item in strategy_plan.items:
            if not item.can_execute and not item.requires_manual_approval:
                if item.policy_result in ("REJECTED", "NOT_APPLICABLE"):
                    continue

            dur = FoundationExecutionPlanRuntime.estimate_duration_for(
                item, base_duration,
            )
            cost = FoundationExecutionPlanRuntime.estimate_cost_for(
                item, base_cost,
            )
            action = _action_from_item(item, estimated_duration=dur, estimated_cost=cost)
            actions.append(action)

        return actions

    # --------------------------------------------------------------
    # Prioritize
    # --------------------------------------------------------------

    @staticmethod
    def prioritize(
        actions: list[ExecutionAction] | tuple[ExecutionAction, ...],
    ) -> list[ExecutionAction]:
        """Sort actions by priority (CRITICAL first) then cost descending."""
        def sort_key(a: ExecutionAction) -> tuple[int, float]:
            return -_PRIORITY_ORDER.get(a.priority, 0), -a.estimated_cost
        return sorted(actions, key=sort_key)

    # --------------------------------------------------------------
    # Grouping
    # --------------------------------------------------------------

    @staticmethod
    def group_by_category(
        actions: list[ExecutionAction] | tuple[ExecutionAction, ...],
    ) -> dict[str, list[ExecutionAction]]:
        """Group actions by category."""
        groups: dict[str, list[ExecutionAction]] = {}
        for a in actions:
            groups.setdefault(a.category, []).append(a)
        return dict(sorted(groups.items()))

    @staticmethod
    def group_by_priority(
        actions: list[ExecutionAction] | tuple[ExecutionAction, ...],
    ) -> dict[str, list[ExecutionAction]]:
        """Group actions by priority."""
        groups: dict[str, list[ExecutionAction]] = {}
        for a in actions:
            groups.setdefault(a.priority, []).append(a)
        return dict(sorted(groups.items(), key=lambda x: _PRIORITY_ORDER.get(x[0], 0)))

    # --------------------------------------------------------------
    # Filtering
    # --------------------------------------------------------------

    @staticmethod
    def filter_actions(
        actions: list[ExecutionAction] | tuple[ExecutionAction, ...],
        category: str | None = None,
        priority: str | None = None,
        can_execute: bool | None = None,
        requires_manual: bool | None = None,
        min_duration: float | None = None,
        max_duration: float | None = None,
        min_cost: float | None = None,
        max_cost: float | None = None,
    ) -> list[ExecutionAction]:
        """Filter actions by multiple criteria."""
        result = list(actions)
        if category is not None:
            result = [a for a in result if a.category == category]
        if priority is not None:
            result = [a for a in result if a.priority == priority]
        if can_execute is not None:
            result = [a for a in result if a.can_execute == can_execute]
        if requires_manual is not None:
            result = [a for a in result if a.requires_manual_approval == requires_manual]
        if min_duration is not None:
            result = [a for a in result if a.estimated_duration >= min_duration]
        if max_duration is not None:
            result = [a for a in result if a.estimated_duration <= max_duration]
        if min_cost is not None:
            result = [a for a in result if a.estimated_cost >= min_cost]
        if max_cost is not None:
            result = [a for a in result if a.estimated_cost <= max_cost]
        return result

    # --------------------------------------------------------------
    # Merge
    # --------------------------------------------------------------

    @staticmethod
    def merge_plans(
        plans: list[ExecutionPlan],
    ) -> ExecutionPlan:
        """Merge multiple ExecutionPlans into one deduplicated plan."""
        seen_ids: set[UUID] = set()
        all_actions: list[ExecutionAction] = []
        merged_metadata: dict[str, Any] = {}

        for plan in plans:
            merged_metadata.update(plan.metadata)
            for action in plan.actions:
                if action.action_id not in seen_ids:
                    seen_ids.add(action.action_id)
                    all_actions.append(action)

        return _build_execution_plan(all_actions, merged_metadata)

    # --------------------------------------------------------------
    # Estimates
    # --------------------------------------------------------------

    @staticmethod
    def estimate_cost(
        actions: list[ExecutionAction] | tuple[ExecutionAction, ...],
        base_cost: float = DEFAULT_COST_PER_ACTION,
    ) -> float:
        """Calculate total estimated cost for a set of actions."""
        if not actions:
            return 0.0
        return sum(
            _estimate_cost_for_action(a, base_cost) for a in actions
        )

    @staticmethod
    def estimate_duration(
        actions: list[ExecutionAction] | tuple[ExecutionAction, ...],
        base_duration: float = DEFAULT_DURATION_PER_ACTION,
    ) -> float:
        """Calculate total estimated duration for a set of actions."""
        if not actions:
            return 0.0
        return sum(
            _estimate_duration_for_action(a, base_duration) for a in actions
        )

    @staticmethod
    def estimate_cost_for(
        item: StrategyExecutionItem,
        base_cost: float = DEFAULT_COST_PER_ACTION,
    ) -> float:
        """Estimate cost for a single StrategyExecutionItem."""
        multiplier = _action_cost_multiplier(item.can_execute, item.requires_manual_approval)
        return base_cost * multiplier

    @staticmethod
    def estimate_duration_for(
        item: StrategyExecutionItem,
        base_duration: float = DEFAULT_DURATION_PER_ACTION,
    ) -> float:
        """Estimate duration for a single StrategyExecutionItem."""
        multiplier = _action_duration_multiplier(item.can_execute, item.requires_manual_approval)
        return base_duration * multiplier

    # --------------------------------------------------------------
    # Trace & Result
    # --------------------------------------------------------------

    @staticmethod
    def build_trace(
        stages: list[str] | None = None,
        duration_ms: float = 0.0,
        metrics: dict[str, float] | None = None,
    ) -> ExecutionPlanTrace:
        """Create an ExecutionPlanTrace from raw data."""
        return ExecutionPlanTrace(
            stages=tuple(stages or []),
            duration_ms=duration_ms,
            metrics=metrics or {},
        )

    @staticmethod
    def build_result(
        plan: ExecutionPlan,
        stages: list[str] | None = None,
        metrics: dict[str, float] | None = None,
    ) -> ExecutionPlanResult:
        """Wrap an ExecutionPlan in an ExecutionPlanResult."""
        trace = ExecutionPlanTrace(
            stages=tuple(stages or []),
            duration_ms=0.0,
            metrics=metrics or {},
        )
        return ExecutionPlanResult(success=True, plan=plan, trace=trace)
