"""Foundation Historical Runtime — 100% stateless temporal comparison engine.

Compares pairs of snapshots (before/after) from any domain and produces
a HistoricalSnapshot showing deltas, percent changes, and detected trends.

100% stateless. All methods are @staticmethod. All models are frozen dataclasses.
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from statistics import mean
from typing import Any
from uuid import UUID

from core.analytics.runtime import PerformanceSnapshot
from core.feedback.foundation import FeedbackSnapshot
from core.learning.foundation import LearningSnapshot
from core.monitoring.runtime import MonitoringSnapshot
from core.skills.foundation import SkillSnapshot
from core.strategy.foundation import StrategySnapshot
from core.workflows.runtime import WorkflowRuntimeSnapshot

# ------------------------------------------------------------------
# Trend constants
# ------------------------------------------------------------------

TREND_IMPROVING = "IMPROVING"
TREND_DECLINING = "DECLINING"
TREND_STABLE = "STABLE"
TREND_UNKNOWN = "UNKNOWN"

# ------------------------------------------------------------------
# Thresholds
# ------------------------------------------------------------------

STABLE_THRESHOLD_PERCENT: float = 5.0  # change <= 5% is stable


@dataclass(frozen=True, slots=True)
class HistoricalEntry:
    """A single metric comparison between two snapshots."""

    snapshot_before: str
    snapshot_after: str
    timestamp_before: float
    timestamp_after: float
    metric_name: str
    old_value: float
    new_value: float
    delta: float
    percent_change: float
    trend: str
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class HistoricalSnapshot:
    """Collection of historical comparisons at a point in time."""

    entries: tuple[HistoricalEntry, ...] = field(default_factory=tuple)
    total_entries: int = 0
    improving_count: int = 0
    declining_count: int = 0
    stable_count: int = 0
    unknown_count: int = 0
    avg_delta: float = 0.0
    avg_percent_change: float = 0.0
    created_at: float = 0.0
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class HistoricalTrend:
    """Metadata about a detected trend."""

    metric_name: str
    trend: str
    percent_change: float
    delta: float


@dataclass(frozen=True, slots=True)
class HistoricalTrace:
    """Metadata about a historical analysis operation."""

    stages: tuple[str, ...] = field(default_factory=tuple)
    duration_ms: float = 0.0
    total_compared: int = 0
    metrics: dict[str, float] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class HistoricalResult:
    """Output of a historical analysis operation."""

    success: bool
    snapshot: HistoricalSnapshot | None = None
    trace: HistoricalTrace | None = None
    error_message: str = ""


# ------------------------------------------------------------------
# Helpers
# ------------------------------------------------------------------


def _now() -> float:
    return time.time()


def _safe_mean(values: list[float]) -> float:
    return mean(values) if values else 0.0


def _detect_trend(delta: float, percent_change: float) -> str:
    """Detect trend based on percent change and delta.

    For most metrics, positive delta = IMPROVING.
    (e.g. success_rate up, health_score up, accuracy up)
    """
    if delta == 0.0 and percent_change == 0.0:
        return TREND_UNKNOWN
    if abs(percent_change) <= STABLE_THRESHOLD_PERCENT:
        return TREND_STABLE
    if delta > 0:
        return TREND_IMPROVING
    if delta < 0:
        return TREND_DECLINING
    return TREND_UNKNOWN


# ------------------------------------------------------------------
# FoundationHistoricalRuntime
# ------------------------------------------------------------------


class FoundationHistoricalRuntime:
    """Stateless historical comparison engine.

    Compares pairs of snapshots (before/after) from any domain
    and produces metrics on deltas, percent changes, and trends.
    """

    # --------------------------------------------------------------
    # Core comparison helpers
    # --------------------------------------------------------------

    @staticmethod
    def calculate_delta(old_value: float, new_value: float) -> float:
        """Calculate the difference between two values."""
        return round(new_value - old_value, 6)

    @staticmethod
    def calculate_percent_change(old_value: float, new_value: float) -> float:
        """Calculate percent change between two values."""
        if old_value == 0.0:
            return 0.0
        return round((new_value - old_value) / abs(old_value) * 100.0, 6)

    @staticmethod
    def detect_trend(delta: float, percent_change: float) -> str:
        """Detect trend direction from delta and percent change."""
        return _detect_trend(delta, percent_change)

    # --------------------------------------------------------------
    # compare methods per domain
    # --------------------------------------------------------------

    @staticmethod
    def compare_monitoring(
        before: MonitoringSnapshot | None,
        after: MonitoringSnapshot | None,
    ) -> list[HistoricalEntry]:
        """Compare two MonitoringSnapshots and return a list of entries."""
        entries: list[HistoricalEntry] = []
        ts_before = before.first_timestamp if before else 0.0
        ts_after = after.first_timestamp if after else 0.0

        if before is None and after is None:
            return entries

        b = before or MonitoringSnapshot(health_score=0.0)
        a = after or MonitoringSnapshot(health_score=0.0)

        metric_fields = [
            ("total_events", float(b.total_events), float(a.total_events)),
            ("total_errors", float(b.total_errors), float(a.total_errors)),
            ("total_success", float(b.total_success), float(a.total_success)),
            ("success_rate", b.success_rate, a.success_rate),
            ("error_rate", b.error_rate, a.error_rate),
            ("event_rate", b.event_rate, a.event_rate),
            ("health_score", b.health_score, a.health_score),
            ("uptime", b.uptime, a.uptime),
        ]
        for name, old_val, new_val in metric_fields:
            delta = FoundationHistoricalRuntime.calculate_delta(old_val, new_val)
            pct = FoundationHistoricalRuntime.calculate_percent_change(old_val, new_val)
            trend = FoundationHistoricalRuntime.detect_trend(delta, pct)
            entries.append(HistoricalEntry(
                snapshot_before="MonitoringSnapshot",
                snapshot_after="MonitoringSnapshot",
                timestamp_before=ts_before,
                timestamp_after=ts_after,
                metric_name=name,
                old_value=round(old_val, 6),
                new_value=round(new_val, 6),
                delta=delta,
                percent_change=pct,
                trend=trend,
                metadata={"domain": "monitoring"},
            ))
        return entries

    @staticmethod
    def compare_performance(
        before: PerformanceSnapshot | None,
        after: PerformanceSnapshot | None,
    ) -> list[HistoricalEntry]:
        """Compare two PerformanceSnapshots and return a list of entries."""
        entries: list[HistoricalEntry] = []
        ts_before = before.timestamp if before else 0.0
        ts_after = after.timestamp if after else 0.0

        if before is None and after is None:
            return entries

        b_metrics = before.metrics if before else {}
        a_metrics = after.metrics if after else {}
        all_keys = set(b_metrics.keys()) | set(a_metrics.keys())

        for key in sorted(all_keys):
            bm = b_metrics.get(key)
            am = a_metrics.get(key)
            old_val = bm.value if bm else 0.0
            new_val = am.value if am else 0.0
            delta = FoundationHistoricalRuntime.calculate_delta(old_val, new_val)
            pct = FoundationHistoricalRuntime.calculate_percent_change(old_val, new_val)
            trend = FoundationHistoricalRuntime.detect_trend(delta, pct)
            entries.append(HistoricalEntry(
                snapshot_before="PerformanceSnapshot",
                snapshot_after="PerformanceSnapshot",
                timestamp_before=ts_before,
                timestamp_after=ts_after,
                metric_name=f"perf_{key}",
                old_value=round(old_val, 6),
                new_value=round(new_val, 6),
                delta=delta,
                percent_change=pct,
                trend=trend,
                metadata={"domain": "performance", "metric_key": key},
            ))

        # Report metric count when one side is provided but no metrics exist
        if not all_keys and (before is not None or after is not None):
            old_count = float(len(b_metrics))
            new_count = float(len(a_metrics))
            delta = FoundationHistoricalRuntime.calculate_delta(old_count, new_count)
            pct = FoundationHistoricalRuntime.calculate_percent_change(old_count, new_count)
            trend = FoundationHistoricalRuntime.detect_trend(delta, pct)
            entries.append(HistoricalEntry(
                snapshot_before="PerformanceSnapshot",
                snapshot_after="PerformanceSnapshot",
                timestamp_before=ts_before,
                timestamp_after=ts_after,
                metric_name="perf_metric_count",
                old_value=old_count,
                new_value=new_count,
                delta=delta,
                percent_change=pct,
                trend=trend,
                metadata={"domain": "performance", "metric_key": "metric_count"},
            ))
        return entries

    @staticmethod
    def compare_strategy(
        before: StrategySnapshot | None,
        after: StrategySnapshot | None,
    ) -> list[HistoricalEntry]:
        """Compare two StrategySnapshots and return a list of entries."""
        entries: list[HistoricalEntry] = []
        ts_before = before.created_at if before else 0.0
        ts_after = after.created_at if after else 0.0

        if before is None and after is None:
            return entries

        b = before or StrategySnapshot()
        a = after or StrategySnapshot()

        # Compare by category counts
        all_cats = set(b.recommendations_by_category.keys()) | set(
            a.recommendations_by_category.keys()
        )
        for cat in sorted(all_cats):
            old_val = float(b.recommendations_by_category.get(cat, 0))
            new_val = float(a.recommendations_by_category.get(cat, 0))
            delta = FoundationHistoricalRuntime.calculate_delta(old_val, new_val)
            pct = FoundationHistoricalRuntime.calculate_percent_change(old_val, new_val)
            trend = FoundationHistoricalRuntime.detect_trend(delta, pct)
            entries.append(HistoricalEntry(
                snapshot_before="StrategySnapshot",
                snapshot_after="StrategySnapshot",
                timestamp_before=ts_before,
                timestamp_after=ts_after,
                metric_name=f"recs_{cat}",
                old_value=old_val,
                new_value=new_val,
                delta=delta,
                percent_change=pct,
                trend=trend,
                metadata={"domain": "strategy", "category": cat},
            ))

        # Compare by priority counts
        all_pris = set(b.recommendations_by_priority.keys()) | set(
            a.recommendations_by_priority.keys()
        )
        for pri in sorted(all_pris):
            old_val = float(b.recommendations_by_priority.get(pri, 0))
            new_val = float(a.recommendations_by_priority.get(pri, 0))
            delta = FoundationHistoricalRuntime.calculate_delta(old_val, new_val)
            pct = FoundationHistoricalRuntime.calculate_percent_change(old_val, new_val)
            trend = FoundationHistoricalRuntime.detect_trend(delta, pct)
            entries.append(HistoricalEntry(
                snapshot_before="StrategySnapshot",
                snapshot_after="StrategySnapshot",
                timestamp_before=ts_before,
                timestamp_after=ts_after,
                metric_name=f"pri_{pri}",
                old_value=old_val,
                new_value=new_val,
                delta=delta,
                percent_change=pct,
                trend=trend,
                metadata={"domain": "strategy", "priority": pri},
            ))

        # Compare total recommendations
        old_total = float(len(b.recommendations))
        new_total = float(len(a.recommendations))
        delta = FoundationHistoricalRuntime.calculate_delta(old_total, new_total)
        pct = FoundationHistoricalRuntime.calculate_percent_change(old_total, new_total)
        trend = FoundationHistoricalRuntime.detect_trend(delta, pct)
        entries.append(HistoricalEntry(
            snapshot_before="StrategySnapshot",
            snapshot_after="StrategySnapshot",
            timestamp_before=ts_before,
            timestamp_after=ts_after,
            metric_name="total_recommendations",
            old_value=old_total,
            new_value=new_total,
            delta=delta,
            percent_change=pct,
            trend=trend,
            metadata={"domain": "strategy"},
        ))
        return entries

    @staticmethod
    def compare_feedback(
        before: FeedbackSnapshot | None,
        after: FeedbackSnapshot | None,
    ) -> list[HistoricalEntry]:
        """Compare two FeedbackSnapshots and return a list of entries."""
        entries: list[HistoricalEntry] = []
        ts_before = before.created_at if before else 0.0
        ts_after = after.created_at if after else 0.0

        if before is None and after is None:
            return entries

        b = before or FeedbackSnapshot()
        a = after or FeedbackSnapshot()

        metric_fields = [
            ("total_entries", float(b.total_entries), float(a.total_entries)),
            ("success_count", float(b.success_count), float(a.success_count)),
            ("failure_count", float(b.failure_count), float(a.failure_count)),
            ("success_rate", b.success_rate, a.success_rate),
            ("accuracy", b.accuracy, a.accuracy),
            ("roi", b.roi, a.roi),
            ("avg_confidence_before", b.avg_confidence_before, a.avg_confidence_before),
            ("avg_confidence_after", b.avg_confidence_after, a.avg_confidence_after),
            ("avg_delta", b.avg_delta, a.avg_delta),
            ("total_duration", b.total_duration, a.total_duration),
            ("total_cost", b.total_cost, a.total_cost),
        ]
        for name, old_val, new_val in metric_fields:
            delta = FoundationHistoricalRuntime.calculate_delta(old_val, new_val)
            pct = FoundationHistoricalRuntime.calculate_percent_change(old_val, new_val)
            trend = FoundationHistoricalRuntime.detect_trend(delta, pct)
            entries.append(HistoricalEntry(
                snapshot_before="FeedbackSnapshot",
                snapshot_after="FeedbackSnapshot",
                timestamp_before=ts_before,
                timestamp_after=ts_after,
                metric_name=name,
                old_value=round(old_val, 6),
                new_value=round(new_val, 6),
                delta=delta,
                percent_change=pct,
                trend=trend,
                metadata={"domain": "feedback"},
            ))
        return entries

    @staticmethod
    def compare_learning(
        before: LearningSnapshot | None,
        after: LearningSnapshot | None,
    ) -> list[HistoricalEntry]:
        """Compare two LearningSnapshots and return a list of entries."""
        entries: list[HistoricalEntry] = []
        ts_before = before.created_at if before else 0.0
        ts_after = after.created_at if after else 0.0

        if before is None and after is None:
            return entries

        b = before or LearningSnapshot()
        a = after or LearningSnapshot()

        old_total = float(len(b.recommendations))
        new_total = float(len(a.recommendations))
        delta = FoundationHistoricalRuntime.calculate_delta(old_total, new_total)
        pct = FoundationHistoricalRuntime.calculate_percent_change(old_total, new_total)
        trend = FoundationHistoricalRuntime.detect_trend(delta, pct)
        entries.append(HistoricalEntry(
            snapshot_before="LearningSnapshot",
            snapshot_after="LearningSnapshot",
            timestamp_before=ts_before,
            timestamp_after=ts_after,
            metric_name="total_recommendations",
            old_value=old_total,
            new_value=new_total,
            delta=delta,
            percent_change=pct,
            trend=trend,
            metadata={"domain": "learning"},
        ))

        # Compare priority distribution if available
        if b.recommendations or a.recommendations:
            all_recs = list(b.recommendations) + list(a.recommendations)
            priorities = sorted(set(r.priority for r in all_recs))
            for pri in priorities:
                old_n = float(sum(1 for r in b.recommendations if r.priority == pri))
                new_n = float(sum(1 for r in a.recommendations if r.priority == pri))
                delta = FoundationHistoricalRuntime.calculate_delta(old_n, new_n)
                pct = FoundationHistoricalRuntime.calculate_percent_change(old_n, new_n)
                trend = FoundationHistoricalRuntime.detect_trend(delta, pct)
                entries.append(HistoricalEntry(
                    snapshot_before="LearningSnapshot",
                    snapshot_after="LearningSnapshot",
                    timestamp_before=ts_before,
                    timestamp_after=ts_after,
                    metric_name=f"recs_priority_{pri}",
                    old_value=old_n,
                    new_value=new_n,
                    delta=delta,
                    percent_change=pct,
                    trend=trend,
                    metadata={"domain": "learning", "priority": pri},
                ))
        return entries

    @staticmethod
    def compare_skills(
        before: SkillSnapshot | None,
        after: SkillSnapshot | None,
    ) -> list[HistoricalEntry]:
        """Compare two SkillSnapshots and return a list of entries."""
        entries: list[HistoricalEntry] = []
        ts_before = before.created_at if before else 0.0
        ts_after = after.created_at if after else 0.0

        if before is None and after is None:
            return entries

        b = before or SkillSnapshot()
        a = after or SkillSnapshot()

        old_total = float(len(b.skills))
        new_total = float(len(a.skills))
        delta = FoundationHistoricalRuntime.calculate_delta(old_total, new_total)
        pct = FoundationHistoricalRuntime.calculate_percent_change(old_total, new_total)
        trend = FoundationHistoricalRuntime.detect_trend(delta, pct)
        entries.append(HistoricalEntry(
            snapshot_before="SkillSnapshot",
            snapshot_after="SkillSnapshot",
            timestamp_before=ts_before,
            timestamp_after=ts_after,
            metric_name="total_skills",
            old_value=old_total,
            new_value=new_total,
            delta=delta,
            percent_change=pct,
            trend=trend,
            metadata={"domain": "skills"},
        ))

        # Compare avg level and XP
        old_levels = [r.level for r in b.skills]
        new_levels = [r.level for r in a.skills]
        old_avg_level = _safe_mean([float(x) for x in old_levels])
        new_avg_level = _safe_mean([float(x) for x in new_levels])
        delta = FoundationHistoricalRuntime.calculate_delta(old_avg_level, new_avg_level)
        pct = FoundationHistoricalRuntime.calculate_percent_change(old_avg_level, new_avg_level)
        trend = FoundationHistoricalRuntime.detect_trend(delta, pct)
        entries.append(HistoricalEntry(
            snapshot_before="SkillSnapshot",
            snapshot_after="SkillSnapshot",
            timestamp_before=ts_before,
            timestamp_after=ts_after,
            metric_name="avg_level",
            old_value=round(old_avg_level, 6),
            new_value=round(new_avg_level, 6),
            delta=delta,
            percent_change=pct,
            trend=trend,
            metadata={"domain": "skills"},
        ))

        old_xp = [r.experience_points for r in b.skills]
        new_xp = [r.experience_points for r in a.skills]
        old_total_xp = float(sum(old_xp))
        new_total_xp = float(sum(new_xp))
        delta = FoundationHistoricalRuntime.calculate_delta(old_total_xp, new_total_xp)
        pct = FoundationHistoricalRuntime.calculate_percent_change(old_total_xp, new_total_xp)
        trend = FoundationHistoricalRuntime.detect_trend(delta, pct)
        entries.append(HistoricalEntry(
            snapshot_before="SkillSnapshot",
            snapshot_after="SkillSnapshot",
            timestamp_before=ts_before,
            timestamp_after=ts_after,
            metric_name="total_xp",
            old_value=round(old_total_xp, 6),
            new_value=round(new_total_xp, 6),
            delta=delta,
            percent_change=pct,
            trend=trend,
            metadata={"domain": "skills"},
        ))
        return entries

    @staticmethod
    def compare_workflow(
        before: list[WorkflowRuntimeSnapshot] | None,
        after: list[WorkflowRuntimeSnapshot] | None,
    ) -> list[HistoricalEntry]:
        """Compare two lists of WorkflowRuntimeSnapshots and return a list of entries."""
        entries: list[HistoricalEntry] = []
        ts_before = 0.0
        ts_after = 0.0

        b = before or []
        a = after or []

        if not b and not a:
            return entries

        old_total = float(len(b))
        new_total = float(len(a))
        delta = FoundationHistoricalRuntime.calculate_delta(old_total, new_total)
        pct = FoundationHistoricalRuntime.calculate_percent_change(old_total, new_total)
        trend = FoundationHistoricalRuntime.detect_trend(delta, pct)
        entries.append(HistoricalEntry(
            snapshot_before="WorkflowRuntimeSnapshot[]",
            snapshot_after="WorkflowRuntimeSnapshot[]",
            timestamp_before=ts_before,
            timestamp_after=ts_after,
            metric_name="total_workflows",
            old_value=old_total,
            new_value=new_total,
            delta=delta,
            percent_change=pct,
            trend=trend,
            metadata={"domain": "workflow"},
        ))

        old_completed = float(sum(1 for w in b if w.state.value == "completed"))
        new_completed = float(sum(1 for w in a if w.state.value == "completed"))
        delta = FoundationHistoricalRuntime.calculate_delta(old_completed, new_completed)
        pct = FoundationHistoricalRuntime.calculate_percent_change(old_completed, new_completed)
        trend = FoundationHistoricalRuntime.detect_trend(delta, pct)
        entries.append(HistoricalEntry(
            snapshot_before="WorkflowRuntimeSnapshot[]",
            snapshot_after="WorkflowRuntimeSnapshot[]",
            timestamp_before=ts_before,
            timestamp_after=ts_after,
            metric_name="completed_workflows",
            old_value=old_completed,
            new_value=new_completed,
            delta=delta,
            percent_change=pct,
            trend=trend,
            metadata={"domain": "workflow"},
        ))

        old_failed = float(sum(1 for w in b if w.state.value == "failed"))
        new_failed = float(sum(1 for w in a if w.state.value == "failed"))
        delta = FoundationHistoricalRuntime.calculate_delta(old_failed, new_failed)
        pct = FoundationHistoricalRuntime.calculate_percent_change(old_failed, new_failed)
        trend = FoundationHistoricalRuntime.detect_trend(delta, pct)
        entries.append(HistoricalEntry(
            snapshot_before="WorkflowRuntimeSnapshot[]",
            snapshot_after="WorkflowRuntimeSnapshot[]",
            timestamp_before=ts_before,
            timestamp_after=ts_after,
            metric_name="failed_workflows",
            old_value=old_failed,
            new_value=new_failed,
            delta=delta,
            percent_change=pct,
            trend=trend,
            metadata={"domain": "workflow"},
        ))

        # Avg progress
        old_progress = _safe_mean([w.progress for w in b])
        new_progress = _safe_mean([w.progress for w in a])
        delta = FoundationHistoricalRuntime.calculate_delta(old_progress, new_progress)
        pct = FoundationHistoricalRuntime.calculate_percent_change(old_progress, new_progress)
        trend = FoundationHistoricalRuntime.detect_trend(delta, pct)
        entries.append(HistoricalEntry(
            snapshot_before="WorkflowRuntimeSnapshot[]",
            snapshot_after="WorkflowRuntimeSnapshot[]",
            timestamp_before=ts_before,
            timestamp_after=ts_after,
            metric_name="avg_progress",
            old_value=round(old_progress, 6),
            new_value=round(new_progress, 6),
            delta=delta,
            percent_change=pct,
            trend=trend,
            metadata={"domain": "workflow"},
        ))
        return entries

    @staticmethod
    def compare(
        before: Any,
        after: Any,
    ) -> list[HistoricalEntry]:
        """Dispatch to the appropriate compare_* method based on type."""
        if isinstance(before, MonitoringSnapshot) or isinstance(after, MonitoringSnapshot):
            return FoundationHistoricalRuntime.compare_monitoring(before, after)
        if isinstance(before, PerformanceSnapshot) or isinstance(after, PerformanceSnapshot):
            return FoundationHistoricalRuntime.compare_performance(before, after)
        if isinstance(before, StrategySnapshot) or isinstance(after, StrategySnapshot):
            return FoundationHistoricalRuntime.compare_strategy(before, after)
        if isinstance(before, FeedbackSnapshot) or isinstance(after, FeedbackSnapshot):
            return FoundationHistoricalRuntime.compare_feedback(before, after)
        if isinstance(before, LearningSnapshot) or isinstance(after, LearningSnapshot):
            return FoundationHistoricalRuntime.compare_learning(before, after)
        if isinstance(before, SkillSnapshot) or isinstance(after, SkillSnapshot):
            return FoundationHistoricalRuntime.compare_skills(before, after)
        if isinstance(before, list) or isinstance(after, list):
            return FoundationHistoricalRuntime.compare_workflow(before, after)
        return []

    # --------------------------------------------------------------
    # Grouping
    # --------------------------------------------------------------

    @staticmethod
    def group_by_trend(
        entries: list[HistoricalEntry] | tuple[HistoricalEntry, ...],
    ) -> dict[str, list[HistoricalEntry]]:
        """Group historical entries by detected trend."""
        groups: dict[str, list[HistoricalEntry]] = {}
        for e in entries:
            groups.setdefault(e.trend, []).append(e)
        return dict(sorted(groups.items()))

    @staticmethod
    def group_by_metric(
        entries: list[HistoricalEntry] | tuple[HistoricalEntry, ...],
    ) -> dict[str, list[HistoricalEntry]]:
        """Group historical entries by metric name."""
        groups: dict[str, list[HistoricalEntry]] = {}
        for e in entries:
            groups.setdefault(e.metric_name, []).append(e)
        return dict(sorted(groups.items()))

    # --------------------------------------------------------------
    # Filtering
    # --------------------------------------------------------------

    @staticmethod
    def filter_history(
        entries: list[HistoricalEntry] | tuple[HistoricalEntry, ...],
        trend: str | None = None,
        metric_name: str | None = None,
        domain: str | None = None,
        min_delta: float | None = None,
        max_delta: float | None = None,
        min_percent_change: float | None = None,
        max_percent_change: float | None = None,
    ) -> list[HistoricalEntry]:
        """Filter historical entries by multiple criteria."""
        result = list(entries)
        if trend is not None:
            result = [e for e in result if e.trend == trend]
        if metric_name is not None:
            result = [e for e in result if e.metric_name == metric_name]
        if domain is not None:
            result = [e for e in result if e.metadata.get("domain") == domain]
        if min_delta is not None:
            result = [e for e in result if e.delta >= min_delta]
        if max_delta is not None:
            result = [e for e in result if e.delta <= max_delta]
        if min_percent_change is not None:
            result = [e for e in result if e.percent_change >= min_percent_change]
        if max_percent_change is not None:
            result = [e for e in result if e.percent_change <= max_percent_change]
        return result

    # --------------------------------------------------------------
    # Merge
    # --------------------------------------------------------------

    @staticmethod
    def merge_history(
        snapshots: list[HistoricalSnapshot],
    ) -> HistoricalSnapshot:
        """Merge multiple HistoricalSnapshots into one deduplicated snapshot."""
        seen: set[str] = set()
        all_entries: list[HistoricalEntry] = []
        merged_metadata: dict[str, Any] = {}

        for snap in snapshots:
            merged_metadata.update(snap.metadata)
            for entry in snap.entries:
                key = f"{entry.metric_name}:{entry.snapshot_before}:{entry.snapshot_after}"
                if key not in seen:
                    seen.add(key)
                    all_entries.append(entry)

        return FoundationHistoricalRuntime.build_snapshot(
            all_entries,
            merged_metadata,
        )

    # --------------------------------------------------------------
    # Snapshot, Trace, Result
    # --------------------------------------------------------------

    @staticmethod
    def build_snapshot(
        entries: list[HistoricalEntry] | tuple[HistoricalEntry, ...],
        metadata: dict[str, Any] | None = None,
    ) -> HistoricalSnapshot:
        """Build a HistoricalSnapshot from a list of entries."""
        entry_list = list(entries)
        total = len(entry_list)
        improving = sum(1 for e in entry_list if e.trend == TREND_IMPROVING)
        declining = sum(1 for e in entry_list if e.trend == TREND_DECLINING)
        stable = sum(1 for e in entry_list if e.trend == TREND_STABLE)
        unknown = sum(1 for e in entry_list if e.trend == TREND_UNKNOWN)
        avg_d = _safe_mean([e.delta for e in entry_list])
        avg_pct = _safe_mean([e.percent_change for e in entry_list])

        return HistoricalSnapshot(
            entries=tuple(entry_list),
            total_entries=total,
            improving_count=improving,
            declining_count=declining,
            stable_count=stable,
            unknown_count=unknown,
            avg_delta=round(avg_d, 6),
            avg_percent_change=round(avg_pct, 6),
            created_at=_now(),
            metadata=metadata or {},
        )

    @staticmethod
    def build_trace(
        stages: list[str] | None = None,
        duration_ms: float = 0.0,
        total_compared: int = 0,
        metrics: dict[str, float] | None = None,
    ) -> HistoricalTrace:
        """Create a HistoricalTrace from raw data."""
        return HistoricalTrace(
            stages=tuple(stages or []),
            duration_ms=duration_ms,
            total_compared=total_compared,
            metrics=metrics or {},
        )

    @staticmethod
    def build_result(
        snapshot: HistoricalSnapshot,
        stages: list[str] | None = None,
        metrics: dict[str, float] | None = None,
    ) -> HistoricalResult:
        """Wrap a HistoricalSnapshot in a HistoricalResult."""
        trace = HistoricalTrace(
            stages=tuple(stages or []),
            duration_ms=0.0,
            total_compared=snapshot.total_entries,
            metrics=metrics or {},
        )
        return HistoricalResult(success=True, snapshot=snapshot, trace=trace)

    # --------------------------------------------------------------
    # Summarize
    # --------------------------------------------------------------

    @staticmethod
    def summarize(
        snapshot: HistoricalSnapshot,
    ) -> dict[str, Any]:
        """Return a human-readable summary of a HistoricalSnapshot."""
        trend_groups = FoundationHistoricalRuntime.group_by_trend(snapshot.entries)
        metric_groups = FoundationHistoricalRuntime.group_by_metric(snapshot.entries)

        return {
            "total_entries": snapshot.total_entries,
            "improving_count": snapshot.improving_count,
            "declining_count": snapshot.declining_count,
            "stable_count": snapshot.stable_count,
            "unknown_count": snapshot.unknown_count,
            "avg_delta": snapshot.avg_delta,
            "avg_percent_change": snapshot.avg_percent_change,
            "trends": {k: len(v) for k, v in trend_groups.items()},
            "metrics": {k: len(v) for k, v in metric_groups.items()},
        }

    # --------------------------------------------------------------
    # Run — full historical analysis
    # --------------------------------------------------------------

    @staticmethod
    def run(
        monitoring_before: MonitoringSnapshot | None = None,
        monitoring_after: MonitoringSnapshot | None = None,
        performance_before: PerformanceSnapshot | None = None,
        performance_after: PerformanceSnapshot | None = None,
        strategy_before: StrategySnapshot | None = None,
        strategy_after: StrategySnapshot | None = None,
        feedback_before: FeedbackSnapshot | None = None,
        feedback_after: FeedbackSnapshot | None = None,
        learning_before: LearningSnapshot | None = None,
        learning_after: LearningSnapshot | None = None,
        skills_before: SkillSnapshot | None = None,
        skills_after: SkillSnapshot | None = None,
        workflow_before: list[WorkflowRuntimeSnapshot] | None = None,
        workflow_after: list[WorkflowRuntimeSnapshot] | None = None,
    ) -> HistoricalResult:
        """Run the full historical analysis across all domains.

        Compares before/after pairs for each domain and produces
        a consolidated HistoricalSnapshot.
        """
        stages: list[str] = ["run"]
        start = _now()
        all_entries: list[HistoricalEntry] = []
        metrics: dict[str, float] = {}

        if monitoring_before is not None or monitoring_after is not None:
            entries = FoundationHistoricalRuntime.compare_monitoring(
                monitoring_before, monitoring_after,
            )
            all_entries.extend(entries)
            stages.append("monitoring")
            metrics["monitoring_entries"] = float(len(entries))

        if performance_before is not None or performance_after is not None:
            entries = FoundationHistoricalRuntime.compare_performance(
                performance_before, performance_after,
            )
            all_entries.extend(entries)
            stages.append("performance")
            metrics["performance_entries"] = float(len(entries))

        if strategy_before is not None or strategy_after is not None:
            entries = FoundationHistoricalRuntime.compare_strategy(
                strategy_before, strategy_after,
            )
            all_entries.extend(entries)
            stages.append("strategy")
            metrics["strategy_entries"] = float(len(entries))

        if feedback_before is not None or feedback_after is not None:
            entries = FoundationHistoricalRuntime.compare_feedback(
                feedback_before, feedback_after,
            )
            all_entries.extend(entries)
            stages.append("feedback")
            metrics["feedback_entries"] = float(len(entries))

        if learning_before is not None or learning_after is not None:
            entries = FoundationHistoricalRuntime.compare_learning(
                learning_before, learning_after,
            )
            all_entries.extend(entries)
            stages.append("learning")
            metrics["learning_entries"] = float(len(entries))

        if skills_before is not None or skills_after is not None:
            entries = FoundationHistoricalRuntime.compare_skills(
                skills_before, skills_after,
            )
            all_entries.extend(entries)
            stages.append("skills")
            metrics["skills_entries"] = float(len(entries))

        if workflow_before is not None or workflow_after is not None:
            entries = FoundationHistoricalRuntime.compare_workflow(
                workflow_before, workflow_after,
            )
            all_entries.extend(entries)
            stages.append("workflow")
            metrics["workflow_entries"] = float(len(entries))

        snapshot = FoundationHistoricalRuntime.build_snapshot(
            all_entries,
            {"source": "FoundationHistoricalRuntime.run"},
        )
        metrics["total_entries"] = float(snapshot.total_entries)
        metrics["improving"] = float(snapshot.improving_count)
        metrics["declining"] = float(snapshot.declining_count)
        metrics["stable"] = float(snapshot.stable_count)

        duration_ms = (_now() - start) * 1000.0
        trace = FoundationHistoricalRuntime.build_trace(
            stages=stages,
            duration_ms=duration_ms,
            total_compared=snapshot.total_entries,
            metrics=metrics,
        )

        return FoundationHistoricalRuntime.build_result(
            snapshot,
            stages=stages,
            metrics=metrics,
        )
