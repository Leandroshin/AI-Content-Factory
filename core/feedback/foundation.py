"""Foundation Feedback Runtime — 100% stateless feedback measurement engine.

Compares expected outcomes (from StrategyRecommendation) with actual
outcomes (from OptimizationSnapshot, ExecutionPlan, etc.) and produces
a FeedbackSnapshot indicating recommendation quality.

100% stateless. All methods are @staticmethod. All models are frozen dataclasses.
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from statistics import mean
from typing import TYPE_CHECKING, Any
from uuid import UUID

from core.analytics.runtime import PerformanceSnapshot
from core.monitoring.runtime import MonitoringSnapshot
from core.optimization.runtime import (
    ACTION_STATE_COMPLETED,
    ACTION_STATE_FAILED,
    OptimizationActionState,
    OptimizationSnapshot,
)

if TYPE_CHECKING:
    from core.execution_plan.foundation import ExecutionAction, ExecutionPlan
    from core.strategy.foundation import StrategyRecommendation, StrategySnapshot
    from core.strategy.pipeline import StrategyExecutionItem, StrategyExecutionPlan

# ------------------------------------------------------------------
# Category constants
# ------------------------------------------------------------------

CATEGORY_COST_REDUCTION = "Cost Reduction"
CATEGORY_PERFORMANCE_IMPROVEMENT = "Performance Improvement"
CATEGORY_RISK_MITIGATION = "Risk Mitigation"
CATEGORY_WORKFLOW_OPTIMIZATION = "Workflow Optimization"
CATEGORY_EMPLOYEE_TRAINING = "Employee Training"
CATEGORY_SKILL_DEVELOPMENT = "Skill Development"
CATEGORY_KNOWLEDGE_EXPANSION = "Knowledge Expansion"
CATEGORY_MONITORING_ALERT = "Monitoring Alert"

# ------------------------------------------------------------------
# Priority constants
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
class FeedbackEntry:
    """Single measurement comparing expected vs actual outcome."""

    recommendation_id: UUID
    action_id: UUID
    expected_outcome: str
    actual_outcome: str
    success: bool
    confidence_before: float
    confidence_after: float
    delta: float
    execution_duration: float
    execution_cost: float
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class FeedbackSnapshot:
    """Collection of feedback entries at a point in time."""

    entries: tuple[FeedbackEntry, ...] = field(default_factory=tuple)
    total_entries: int = 0
    success_count: int = 0
    failure_count: int = 0
    success_rate: float = 0.0
    accuracy: float = 0.0
    roi: float = 0.0
    avg_confidence_before: float = 0.0
    avg_confidence_after: float = 0.0
    avg_delta: float = 0.0
    total_duration: float = 0.0
    total_cost: float = 0.0
    created_at: float = 0.0
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class FeedbackTrace:
    """Metadata about a feedback analysis operation."""

    stages: tuple[str, ...] = field(default_factory=tuple)
    duration_ms: float = 0.0
    total_compared: int = 0
    metrics: dict[str, float] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class FeedbackResult:
    """Output of a feedback analysis operation."""

    success: bool
    snapshot: FeedbackSnapshot | None = None
    trace: FeedbackTrace | None = None
    error_message: str = ""


# ------------------------------------------------------------------
# Helpers
# ------------------------------------------------------------------


def _now() -> float:
    return time.time()


def _safe_mean(values: list[float]) -> float:
    return mean(values) if values else 0.0


def _infer_category_from_rec(
    rec: StrategyRecommendation,
) -> str:
    return rec.category


def _infer_priority_from_rec(
    rec: StrategyRecommendation,
) -> str:
    return rec.priority


def _map_optimization_state_to_outcome(state: str) -> str:
    mapping = {
        ACTION_STATE_COMPLETED: "completed",
        ACTION_STATE_FAILED: "failed",
        "ROLLED_BACK": "rolled_back",
        "SKIPPED": "skipped",
        "MANUAL": "manual",
        "PENDING": "pending",
        "RUNNING": "running",
    }
    return mapping.get(state, state)


def _map_optimization_state_to_success(state: str) -> bool:
    return state == ACTION_STATE_COMPLETED


def _find_recommendation_by_id(
    snapshots: list[StrategySnapshot],
    recommendation_id: UUID,
) -> StrategyRecommendation | None:
    for snap in snapshots:
        for rec in snap.recommendations:
            if rec.recommendation_id == recommendation_id:
                return rec
    return None


# ------------------------------------------------------------------
# FoundationFeedbackRuntime
# ------------------------------------------------------------------


class FoundationFeedbackRuntime:
    """Stateless feedback measurement engine.

    Compares expected outcomes from strategic recommendations with
    actual outcomes from execution, producing quality metrics.
    """

    # --------------------------------------------------------------
    # Core
    # --------------------------------------------------------------

    @staticmethod
    def create_feedback(
        recommendation: StrategyRecommendation,
        actual_action: OptimizationActionState,
        expected_outcome: str = "success",
        actual_outcome: str | None = None,
        execution_cost: float = 0.0,
    ) -> FeedbackEntry:
        """Create a single FeedbackEntry from a recommendation and actual result."""
        actual = actual_outcome or _map_optimization_state_to_outcome(actual_action.state)
        success = _map_optimization_state_to_success(actual_action.state)
        confidence_before = recommendation.confidence
        confidence_after = confidence_before * (1.2 if success else 0.8)
        confidence_after = max(0.0, min(1.0, confidence_after))
        delta = confidence_after - confidence_before

        return FeedbackEntry(
            recommendation_id=recommendation.recommendation_id,
            action_id=actual_action.action_id,
            expected_outcome=expected_outcome,
            actual_outcome=actual,
            success=success,
            confidence_before=round(confidence_before, 6),
            confidence_after=round(confidence_after, 6),
            delta=round(delta, 6),
            execution_duration=actual_action.duration,
            execution_cost=execution_cost,
            metadata={
                "category": recommendation.category,
                "priority": recommendation.priority,
                "state": actual_action.state,
                "attempt": actual_action.attempt,
            },
        )

    # --------------------------------------------------------------
    # Comparison
    # --------------------------------------------------------------

    @staticmethod
    def compare_expected_vs_actual(
        expected_success: bool,
        actual_success: bool,
    ) -> bool:
        """Compare expected vs actual success, return True if they match."""
        return expected_success == actual_success

    @staticmethod
    def calculate_delta(
        confidence_before: float,
        confidence_after: float,
    ) -> float:
        """Calculate the delta between two confidence values."""
        return round(confidence_after - confidence_before, 6)

    # --------------------------------------------------------------
    # Statistics
    # --------------------------------------------------------------

    @staticmethod
    def calculate_success_rate(
        entries: list[FeedbackEntry] | tuple[FeedbackEntry, ...],
    ) -> float:
        """Calculate the success rate from a list of feedback entries."""
        if not entries:
            return 0.0
        success_count = sum(1 for e in entries if e.success)
        return round(success_count / len(entries) * 100.0, 6)

    @staticmethod
    def calculate_accuracy(
        entries: list[FeedbackEntry] | tuple[FeedbackEntry, ...],
    ) -> float:
        """Calculate prediction accuracy.

        Accuracy measures how often confidence_before > 0.5 predicts
        success (or confidence_before <= 0.5 predicts failure).
        """
        if not entries:
            return 0.0
        correct = sum(
            1 for e in entries
            if (e.confidence_before > 0.5 and e.success)
            or (e.confidence_before <= 0.5 and not e.success)
        )
        return round(correct / len(entries) * 100.0, 6)

    @staticmethod
    def calculate_roi(
        entries: list[FeedbackEntry] | tuple[FeedbackEntry, ...],
        base_investment: float = 1.0,
    ) -> float:
        """Calculate return on investment from feedback entries.

        ROI = (total_value_of_successes - total_cost) / base_investment

        Each success is worth 1.0, each failure costs 1.0.
        Duration savings add marginal value.
        """
        if not entries or base_investment <= 0:
            return 0.0
        total_value = 0.0
        total_cost = 0.0
        for e in entries:
            if e.success:
                duration_saving = max(0.0, 10.0 - e.execution_duration) / 10.0
                total_value += 1.0 + duration_saving
            else:
                total_cost += 1.0 + e.execution_cost
        net_return = total_value - total_cost
        return round(net_return / base_investment, 6)

    @staticmethod
    def calculate_confidence_adjustment(
        entries: list[FeedbackEntry] | tuple[FeedbackEntry, ...],
    ) -> float:
        """Calculate the recommended confidence adjustment.

        Positive means confidence should increase on average.
        Negative means confidence should decrease on average.
        """
        if not entries:
            return 0.0
        deltas = [e.delta for e in entries]
        return round(_safe_mean(deltas), 6)

    # --------------------------------------------------------------
    # Grouping
    # --------------------------------------------------------------

    @staticmethod
    def group_by_category(
        entries: list[FeedbackEntry] | tuple[FeedbackEntry, ...],
    ) -> dict[str, list[FeedbackEntry]]:
        """Group feedback entries by category (from metadata)."""
        groups: dict[str, list[FeedbackEntry]] = {}
        for e in entries:
            cat = e.metadata.get("category", "Unknown")
            groups.setdefault(cat, []).append(e)
        return dict(sorted(groups.items()))

    @staticmethod
    def group_by_priority(
        entries: list[FeedbackEntry] | tuple[FeedbackEntry, ...],
    ) -> dict[str, list[FeedbackEntry]]:
        """Group feedback entries by priority (from metadata)."""
        groups: dict[str, list[FeedbackEntry]] = {}
        for e in entries:
            pri = e.metadata.get("priority", "LOW")
            groups.setdefault(pri, []).append(e)
        return dict(sorted(groups.items(), key=lambda x: _PRIORITY_ORDER.get(x[0], 0)))

    @staticmethod
    def group_by_success(
        entries: list[FeedbackEntry] | tuple[FeedbackEntry, ...],
    ) -> dict[str, list[FeedbackEntry]]:
        """Group feedback entries by whether they succeeded."""
        groups: dict[str, list[FeedbackEntry]] = {"success": [], "failure": []}
        for e in entries:
            key = "success" if e.success else "failure"
            groups[key].append(e)
        return dict(sorted(groups.items()))

    # --------------------------------------------------------------
    # Filtering
    # --------------------------------------------------------------

    @staticmethod
    def filter_feedback(
        entries: list[FeedbackEntry] | tuple[FeedbackEntry, ...],
        category: str | None = None,
        priority: str | None = None,
        success: bool | None = None,
        min_confidence_before: float | None = None,
        max_confidence_before: float | None = None,
        min_delta: float | None = None,
        max_delta: float | None = None,
        min_duration: float | None = None,
        max_duration: float | None = None,
    ) -> list[FeedbackEntry]:
        """Filter feedback entries by multiple criteria."""
        result = list(entries)
        if category is not None:
            result = [e for e in result if e.metadata.get("category") == category]
        if priority is not None:
            result = [e for e in result if e.metadata.get("priority") == priority]
        if success is not None:
            result = [e for e in result if e.success == success]
        if min_confidence_before is not None:
            result = [e for e in result if e.confidence_before >= min_confidence_before]
        if max_confidence_before is not None:
            result = [e for e in result if e.confidence_before <= max_confidence_before]
        if min_delta is not None:
            result = [e for e in result if e.delta >= min_delta]
        if max_delta is not None:
            result = [e for e in result if e.delta <= max_delta]
        if min_duration is not None:
            result = [e for e in result if e.execution_duration >= min_duration]
        if max_duration is not None:
            result = [e for e in result if e.execution_duration <= max_duration]
        return result

    # --------------------------------------------------------------
    # Merge
    # --------------------------------------------------------------

    @staticmethod
    def merge_feedback(
        snapshots: list[FeedbackSnapshot],
    ) -> FeedbackSnapshot:
        """Merge multiple FeedbackSnapshots into one deduplicated snapshot."""
        seen: set[tuple[UUID, UUID]] = set()
        all_entries: list[FeedbackEntry] = []
        merged_metadata: dict[str, Any] = {}

        for snap in snapshots:
            merged_metadata.update(snap.metadata)
            for entry in snap.entries:
                key = (entry.recommendation_id, entry.action_id)
                if key not in seen:
                    seen.add(key)
                    all_entries.append(entry)

        return FoundationFeedbackRuntime.build_snapshot(
            all_entries,
            merged_metadata,
        )

    # --------------------------------------------------------------
    # Snapshot, Trace, Result
    # --------------------------------------------------------------

    @staticmethod
    def build_snapshot(
        entries: list[FeedbackEntry] | tuple[FeedbackEntry, ...],
        metadata: dict[str, Any] | None = None,
    ) -> FeedbackSnapshot:
        """Build a FeedbackSnapshot from a list of feedback entries."""
        entry_list = list(entries)
        total = len(entry_list)
        success_count = sum(1 for e in entry_list if e.success)
        failure_count = total - success_count
        success_rate = FoundationFeedbackRuntime.calculate_success_rate(entry_list)
        accuracy = FoundationFeedbackRuntime.calculate_accuracy(entry_list)
        roi = FoundationFeedbackRuntime.calculate_roi(entry_list)
        conf_before = _safe_mean([e.confidence_before for e in entry_list])
        conf_after = _safe_mean([e.confidence_after for e in entry_list])
        avg_delta = _safe_mean([e.delta for e in entry_list])
        total_dur = sum(e.execution_duration for e in entry_list)
        total_cst = sum(e.execution_cost for e in entry_list)

        return FeedbackSnapshot(
            entries=tuple(entry_list),
            total_entries=total,
            success_count=success_count,
            failure_count=failure_count,
            success_rate=round(success_rate, 6),
            accuracy=round(accuracy, 6),
            roi=round(roi, 6),
            avg_confidence_before=round(conf_before, 6),
            avg_confidence_after=round(conf_after, 6),
            avg_delta=round(avg_delta, 6),
            total_duration=round(total_dur, 6),
            total_cost=round(total_cst, 6),
            created_at=_now(),
            metadata=metadata or {},
        )

    @staticmethod
    def build_trace(
        stages: list[str] | None = None,
        duration_ms: float = 0.0,
        total_compared: int = 0,
        metrics: dict[str, float] | None = None,
    ) -> FeedbackTrace:
        """Create a FeedbackTrace from raw data."""
        return FeedbackTrace(
            stages=tuple(stages or []),
            duration_ms=duration_ms,
            total_compared=total_compared,
            metrics=metrics or {},
        )

    @staticmethod
    def build_result(
        snapshot: FeedbackSnapshot,
        stages: list[str] | None = None,
        metrics: dict[str, float] | None = None,
    ) -> FeedbackResult:
        """Wrap a FeedbackSnapshot in a FeedbackResult."""
        trace = FeedbackTrace(
            stages=tuple(stages or []),
            duration_ms=0.0,
            total_compared=snapshot.total_entries,
            metrics=metrics or {},
        )
        return FeedbackResult(success=True, snapshot=snapshot, trace=trace)

    # --------------------------------------------------------------
    # Summarize
    # --------------------------------------------------------------

    @staticmethod
    def summarize(
        snapshot: FeedbackSnapshot,
    ) -> dict[str, Any]:
        """Return a human-readable summary of a FeedbackSnapshot."""
        groups = FoundationFeedbackRuntime.group_by_success(snapshot.entries)
        cat_groups = FoundationFeedbackRuntime.group_by_category(snapshot.entries)

        return {
            "total_entries": snapshot.total_entries,
            "success_count": snapshot.success_count,
            "failure_count": snapshot.failure_count,
            "success_rate": snapshot.success_rate,
            "accuracy": snapshot.accuracy,
            "roi": snapshot.roi,
            "avg_confidence_before": snapshot.avg_confidence_before,
            "avg_confidence_after": snapshot.avg_confidence_after,
            "avg_delta": snapshot.avg_delta,
            "total_duration": snapshot.total_duration,
            "total_cost": snapshot.total_cost,
            "successful_entries": len(groups.get("success", [])),
            "failed_entries": len(groups.get("failure", [])),
            "categories": {k: len(v) for k, v in cat_groups.items()},
        }

    # --------------------------------------------------------------
    # Run — full feedback pipeline
    # --------------------------------------------------------------

    @staticmethod
    def run(
        strategy_snapshot: StrategySnapshot | None = None,
        strategy_execution_plan: StrategyExecutionPlan | None = None,
        execution_plan: ExecutionPlan | None = None,
        optimization_snapshot: OptimizationSnapshot | None = None,
        monitoring_snapshot: MonitoringSnapshot | None = None,
        performance_snapshot: PerformanceSnapshot | None = None,
    ) -> FeedbackResult:
        """Run the full feedback pipeline.

        Compares expected outcomes (from strategy recommendations) with
        actual outcomes (from optimization results) and produces a
        FeedbackResult with quality metrics.

        Args:
            strategy_snapshot: Strategic recommendations made.
            strategy_execution_plan: Validated execution plan (policy results).
            execution_plan: Concrete execution actions.
            optimization_snapshot: Actual execution results.
            monitoring_snapshot: Platform health metrics.
            performance_snapshot: Performance metrics.

        Returns:
            A FeedbackResult with the comparative analysis.
        """
        stages: list[str] = ["run"]
        start = _now()
        all_entries: list[FeedbackEntry] = []
        metrics: dict[str, float] = {}

        strategy_snaps: list[StrategySnapshot] = []
        if strategy_snapshot is not None:
            strategy_snaps.append(strategy_snapshot)
            stages.append("strategy_snapshot")

        if strategy_execution_plan is not None:
            stages.append("strategy_execution_plan")
            metrics["strategy_items"] = float(len(strategy_execution_plan.items))

        if execution_plan is not None:
            stages.append("execution_plan")
            metrics["execution_actions"] = float(len(execution_plan.actions))

        if optimization_snapshot is not None:
            stages.append("optimization_snapshot")
            opt_actions = list(optimization_snapshot.actions)
            metrics["optimization_actions"] = float(len(opt_actions))
            metrics["optimization_completed"] = float(optimization_snapshot.total_completed)
            metrics["optimization_failed"] = float(optimization_snapshot.total_failed)

            # Match optimization actions with strategy recommendations
            for opt_action in opt_actions:
                rec = _find_recommendation_by_id(
                    strategy_snaps, opt_action.recommendation_id,
                )
                if rec is not None:
                    entry = FoundationFeedbackRuntime.create_feedback(
                        recommendation=rec,
                        actual_action=opt_action,
                        execution_cost=opt_action.duration * 0.1,
                    )
                    all_entries.append(entry)

        if monitoring_snapshot is not None:
            stages.append("monitoring")
            metrics["monitoring_events"] = float(monitoring_snapshot.total_events)
            metrics["monitoring_health"] = monitoring_snapshot.health_score

        if performance_snapshot is not None:
            stages.append("performance")
            metrics["performance_metrics"] = float(len(performance_snapshot.metrics))

        # If no optimization actions matched, create placeholder feedback
        if not all_entries and strategy_snapshot is not None:
            for rec in strategy_snapshot.recommendations:
                all_entries.append(FeedbackEntry(
                    recommendation_id=rec.recommendation_id,
                    action_id=UUID(int=0),
                    expected_outcome="success",
                    actual_outcome="unknown",
                    success=False,
                    confidence_before=rec.confidence,
                    confidence_after=rec.confidence,
                    delta=0.0,
                    execution_duration=0.0,
                    execution_cost=0.0,
                    metadata={
                        "category": rec.category,
                        "priority": rec.priority,
                        "state": "no_execution_data",
                    },
                ))

        snapshot = FoundationFeedbackRuntime.build_snapshot(
            all_entries,
            {"source": "FoundationFeedbackRuntime.run"},
        )
        metrics["total_entries"] = float(snapshot.total_entries)
        metrics["success_rate"] = snapshot.success_rate
        metrics["accuracy"] = snapshot.accuracy
        metrics["roi"] = snapshot.roi

        duration_ms = (_now() - start) * 1000.0
        trace = FoundationFeedbackRuntime.build_trace(
            stages=stages,
            duration_ms=duration_ms,
            total_compared=snapshot.total_entries,
            metrics=metrics,
        )

        return FoundationFeedbackRuntime.build_result(
            snapshot,
            stages=stages,
            metrics=metrics,
        )
