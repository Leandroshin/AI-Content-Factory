"""Strategy Execution Pipeline — connects Strategy Foundation to Policy Foundation.

Takes a StrategySnapshot (recommendations), evaluates each against
defined policy rules via FoundationPolicyRuntime, and produces
a validated StrategyExecutionPlan organized by result category.

100% stateless. All methods are @staticmethod. All models are frozen dataclasses.
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any
from uuid import UUID

from core.policy.foundation import (
    FoundationPolicyRuntime,
    PolicyEvaluation,
    PolicyResult,
    PolicyRule,
    RESULT_APPROVED,
    RESULT_MANUAL_APPROVAL,
)

if TYPE_CHECKING:
    from core.strategy.foundation import StrategyRecommendation, StrategySnapshot

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
class StrategyExecutionItem:
    """A single recommendation after policy evaluation."""

    recommendation_id: UUID
    category: str
    priority: str
    policy_result: str
    can_execute: bool
    requires_manual_approval: bool
    reason: str
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class StrategyExecutionPlan:
    """Validated execution plan organizing recommendations by policy result."""

    approved: tuple[StrategyExecutionItem, ...] = field(default_factory=tuple)
    manual: tuple[StrategyExecutionItem, ...] = field(default_factory=tuple)
    blocked: tuple[StrategyExecutionItem, ...] = field(default_factory=tuple)
    rejected: tuple[StrategyExecutionItem, ...] = field(default_factory=tuple)
    not_applicable: tuple[StrategyExecutionItem, ...] = field(default_factory=tuple)
    items: tuple[StrategyExecutionItem, ...] = field(default_factory=tuple)
    created_at: float = 0.0
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class StrategyPipelineTrace:
    """Metadata about a strategy pipeline execution."""

    stages: tuple[str, ...] = field(default_factory=tuple)
    duration_ms: float = 0.0
    metrics: dict[str, float] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class StrategyPipelineResult:
    """Output of a strategy pipeline execution."""

    success: bool
    plan: StrategyExecutionPlan | None = None
    trace: StrategyPipelineTrace | None = None
    error_message: str = ""


# ------------------------------------------------------------------
# Helpers
# ------------------------------------------------------------------


def _now() -> float:
    return time.time()


def _item_from_evaluation(
    evaluation: PolicyEvaluation,
    recommendation: StrategyRecommendation,
) -> StrategyExecutionItem:
    """Convert a PolicyEvaluation + its source recommendation into an ExecutionItem."""
    policy_result = evaluation.result
    can_execute = policy_result == RESULT_APPROVED
    requires_manual = policy_result == RESULT_MANUAL_APPROVAL
    return StrategyExecutionItem(
        recommendation_id=recommendation.recommendation_id,
        category=recommendation.category,
        priority=recommendation.priority,
        policy_result=policy_result,
        can_execute=can_execute,
        requires_manual_approval=requires_manual,
        reason=evaluation.reason,
        metadata={
            **recommendation.metadata,
            "rule_id": str(evaluation.rule_id),
            "rule_name": evaluation.rule_name,
            "target_id": evaluation.target_id,
        },
    )


def _build_plan(
    evaluations: list[PolicyEvaluation],
    recommendations: list[StrategyRecommendation],
    metadata: dict[str, Any] | None = None,
) -> StrategyExecutionPlan:
    """Build an execution plan from evaluations and their source recommendations."""
    rec_by_target_id: dict[str, StrategyRecommendation] = {
        str(r.recommendation_id): r for r in recommendations
    }

    items: list[StrategyExecutionItem] = []
    approved: list[StrategyExecutionItem] = []
    manual: list[StrategyExecutionItem] = []
    blocked: list[StrategyExecutionItem] = []
    rejected: list[StrategyExecutionItem] = []
    not_applicable: list[StrategyExecutionItem] = []

    for ev in evaluations:
        rec = rec_by_target_id.get(ev.target_id)
        if rec is None:
            continue

        item = _item_from_evaluation(ev, rec)
        items.append(item)

        if item.policy_result == RESULT_APPROVED:
            approved.append(item)
        elif item.policy_result == RESULT_MANUAL_APPROVAL:
            manual.append(item)
        elif item.policy_result == "BLOCKED":
            blocked.append(item)
        elif item.policy_result == "REJECTED":
            rejected.append(item)
        else:
            not_applicable.append(item)

    return StrategyExecutionPlan(
        approved=tuple(approved),
        manual=tuple(manual),
        blocked=tuple(blocked),
        rejected=tuple(rejected),
        not_applicable=tuple(not_applicable),
        items=tuple(items),
        created_at=_now(),
        metadata=metadata or {},
    )


# ------------------------------------------------------------------
# StrategyPipeline
# ------------------------------------------------------------------


class StrategyPipeline:
    """Stateless strategy execution pipeline.

    Connects Strategy Foundation → Policy Foundation by evaluating
    strategic recommendations against policy rules and organizing
    the results into a validated execution plan.
    """

    # --------------------------------------------------------------
    # Core
    # --------------------------------------------------------------

    @staticmethod
    def run(
        snapshot: StrategySnapshot,
        rules: list[PolicyRule],
    ) -> StrategyPipelineResult:
        """Execute the full pipeline: evaluate policies → build plan → result.

        Args:
            snapshot: A StrategySnapshot containing recommendations.
            rules: Policy rules to evaluate recommendations against.

        Returns:
            A StrategyPipelineResult with the validated execution plan.
        """
        stages: list[str] = []
        metrics: dict[str, float] = {}
        start = _now()

        if not snapshot.recommendations:
            plan = StrategyExecutionPlan(created_at=_now())
            duration = (_now() - start) * 1000.0
            trace = StrategyPipelineTrace(
                stages=("run", "empty_snapshot"),
                duration_ms=duration,
                metrics={"recommendations": 0.0, "rules": float(len(rules)), "evaluations": 0.0},
            )
            return StrategyPipelineResult(success=True, plan=plan, trace=trace)

        if not rules:
            stages.append("run")
            items: list[StrategyExecutionItem] = []
            approved: list[StrategyExecutionItem] = []
            for rec in snapshot.recommendations:
                item = StrategyExecutionItem(
                    recommendation_id=rec.recommendation_id,
                    category=rec.category,
                    priority=rec.priority,
                    policy_result=RESULT_APPROVED,
                    can_execute=True,
                    requires_manual_approval=False,
                    reason="No rules defined — all recommendations approved by default",
                    metadata={"source": "no_rules"},
                )
                items.append(item)
                approved.append(item)

            plan = StrategyExecutionPlan(
                approved=tuple(approved),
                manual=(),
                blocked=(),
                rejected=(),
                not_applicable=(),
                items=tuple(items),
                created_at=_now(),
            )
            duration = (_now() - start) * 1000.0
            trace = StrategyPipelineTrace(
                stages=tuple(stages),
                duration_ms=duration,
                metrics={
                    "recommendations": float(len(snapshot.recommendations)),
                    "rules": 0.0,
                    "evaluations": 0.0,
                },
            )
            return StrategyPipelineResult(success=True, plan=plan, trace=trace)

        stages.append("run")
        policy_result = StrategyPipeline.evaluate_policies(snapshot, rules)
        stages.append("evaluate_policies")

        if not policy_result.success or policy_result.snapshot is None:
            duration = (_now() - start) * 1000.0
            trace = StrategyPipelineTrace(
                stages=tuple(stages),
                duration_ms=duration,
                metrics={"error": 1.0},
            )
            return StrategyPipelineResult(
                success=False,
                error_message=policy_result.error_message or "Policy evaluation failed",
                trace=trace,
            )

        evals = list(policy_result.snapshot.evaluations)
        recs = list(snapshot.recommendations)

        plan = _build_plan(evals, recs, {"source": "strategy_pipeline"})
        stages.append("build_plan")

        duration = (_now() - start) * 1000.0
        trace = StrategyPipelineTrace(
            stages=tuple(stages),
            duration_ms=duration,
            metrics={
                "recommendations": float(len(recs)),
                "rules": float(len(rules)),
                "evaluations": float(len(evals)),
                "approved": float(len(plan.approved)),
                "manual": float(len(plan.manual)),
                "blocked": float(len(plan.blocked)),
                "rejected": float(len(plan.rejected)),
                "not_applicable": float(len(plan.not_applicable)),
            },
        )
        return StrategyPipelineResult(success=True, plan=plan, trace=trace)

    @staticmethod
    def build_plan(
        evaluations: list[PolicyEvaluation],
        recommendations: list[StrategyRecommendation],
        metadata: dict[str, Any] | None = None,
    ) -> StrategyExecutionPlan:
        """Build an execution plan from policy evaluations and source recommendations."""
        return _build_plan(evaluations, recommendations, metadata)

    @staticmethod
    def evaluate_policies(
        snapshot: StrategySnapshot,
        rules: list[PolicyRule],
    ) -> PolicyResult:
        """Evaluate all recommendations in a snapshot against policy rules.

        Delegates to FoundationPolicyRuntime.evaluate_all().
        """
        targets = list(snapshot.recommendations)
        return FoundationPolicyRuntime.evaluate_all(rules, targets)

    # --------------------------------------------------------------
    # Grouping
    # --------------------------------------------------------------

    @staticmethod
    def group_by_result(
        items: list[StrategyExecutionItem] | tuple[StrategyExecutionItem, ...],
    ) -> dict[str, list[StrategyExecutionItem]]:
        """Group execution items by their policy result."""
        groups: dict[str, list[StrategyExecutionItem]] = {}
        for item in items:
            groups.setdefault(item.policy_result, []).append(item)
        return dict(sorted(groups.items()))

    @staticmethod
    def group_by_priority(
        items: list[StrategyExecutionItem] | tuple[StrategyExecutionItem, ...],
    ) -> dict[str, list[StrategyExecutionItem]]:
        """Group execution items by priority."""
        groups: dict[str, list[StrategyExecutionItem]] = {}
        for item in items:
            groups.setdefault(item.priority, []).append(item)
        return dict(sorted(groups.items(), key=lambda x: _PRIORITY_ORDER.get(x[0], 0)))

    # --------------------------------------------------------------
    # Filtering
    # --------------------------------------------------------------

    @staticmethod
    def filter_items(
        items: list[StrategyExecutionItem] | tuple[StrategyExecutionItem, ...],
        policy_result: str | None = None,
        priority: str | None = None,
        category: str | None = None,
        can_execute: bool | None = None,
        requires_manual: bool | None = None,
    ) -> list[StrategyExecutionItem]:
        """Filter execution items by multiple criteria."""
        result = list(items)
        if policy_result is not None:
            result = [i for i in result if i.policy_result == policy_result]
        if priority is not None:
            result = [i for i in result if i.priority == priority]
        if category is not None:
            result = [i for i in result if i.category == category]
        if can_execute is not None:
            result = [i for i in result if i.can_execute == can_execute]
        if requires_manual is not None:
            result = [i for i in result if i.requires_manual_approval == requires_manual]
        return result

    # --------------------------------------------------------------
    # Merge
    # --------------------------------------------------------------

    @staticmethod
    def merge_plans(
        plans: list[StrategyExecutionPlan],
    ) -> StrategyExecutionPlan:
        """Merge multiple execution plans into one deduplicated plan."""
        seen_ids: set[UUID] = set()
        all_items: list[StrategyExecutionItem] = []
        approved: list[StrategyExecutionItem] = []
        manual: list[StrategyExecutionItem] = []
        blocked: list[StrategyExecutionItem] = []
        rejected: list[StrategyExecutionItem] = []
        not_applicable: list[StrategyExecutionItem] = []
        merged_metadata: dict[str, Any] = {}

        for plan in plans:
            merged_metadata.update(plan.metadata)
            for item in plan.items:
                if item.recommendation_id not in seen_ids:
                    seen_ids.add(item.recommendation_id)
                    all_items.append(item)
                    if item.policy_result == RESULT_APPROVED:
                        approved.append(item)
                    elif item.policy_result == RESULT_MANUAL_APPROVAL:
                        manual.append(item)
                    elif item.policy_result == "BLOCKED":
                        blocked.append(item)
                    elif item.policy_result == "REJECTED":
                        rejected.append(item)
                    else:
                        not_applicable.append(item)

        return StrategyExecutionPlan(
            approved=tuple(approved),
            manual=tuple(manual),
            blocked=tuple(blocked),
            rejected=tuple(rejected),
            not_applicable=tuple(not_applicable),
            items=tuple(all_items),
            created_at=_now(),
            metadata=merged_metadata,
        )

    # --------------------------------------------------------------
    # Trace & Result
    # --------------------------------------------------------------

    @staticmethod
    def build_trace(
        stages: list[str] | None = None,
        duration_ms: float = 0.0,
        metrics: dict[str, float] | None = None,
    ) -> StrategyPipelineTrace:
        """Create a StrategyPipelineTrace from raw data."""
        return StrategyPipelineTrace(
            stages=tuple(stages or []),
            duration_ms=duration_ms,
            metrics=metrics or {},
        )

    @staticmethod
    def build_result(
        plan: StrategyExecutionPlan,
        stages: list[str] | None = None,
        metrics: dict[str, float] | None = None,
    ) -> StrategyPipelineResult:
        """Wrap an execution plan in a StrategyPipelineResult."""
        now = _now()
        trace = StrategyPipelineTrace(
            stages=tuple(stages or []),
            duration_ms=0.0,
            metrics=metrics or {},
        )
        return StrategyPipelineResult(success=True, plan=plan, trace=trace)
