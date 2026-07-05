"""Foundation Prediction Runtime — 100% stateless deterministic projection engine.

Projects future behavior based on historical trends and current snapshots
using heuristic rules (no ML). Produces PredictionSnapshot with direction,
confidence, and horizon for each predicted metric.

100% stateless. All methods are @staticmethod. All models are frozen dataclasses.
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from statistics import mean
from typing import Any
from uuid import UUID, uuid4

from core.analytics.runtime import PerformanceSnapshot
from core.feedback.foundation import FeedbackSnapshot
from core.history.foundation import (
    HistoricalEntry,
    HistoricalSnapshot,
    TREND_DECLINING,
    TREND_IMPROVING,
    TREND_STABLE,
    TREND_UNKNOWN,
)
from core.learning.foundation import LearningSnapshot
from core.monitoring.runtime import MonitoringSnapshot
from core.skills.foundation import SkillSnapshot
from core.strategy.foundation import StrategySnapshot
from core.workflows.runtime import WorkflowRuntimeSnapshot

# ------------------------------------------------------------------
# Direction constants
# ------------------------------------------------------------------

UPWARD = "UPWARD"
DOWNWARD = "DOWNWARD"
STABLE = "STABLE"
UNCERTAIN = "UNCERTAIN"

# ------------------------------------------------------------------
# Defaults
# ------------------------------------------------------------------

DEFAULT_HORIZON: float = 3600.0  # 1 hour
MAX_CONFIDENCE: float = 0.95
MIN_CONFIDENCE: float = 0.10
HEALTHY_HEALTH_SCORE: float = 70.0
HEALTHY_SUCCESS_RATE: float = 80.0

# ------------------------------------------------------------------
# Data models
# ------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class PredictionEntry:
    """A single prediction for a metric."""

    prediction_id: UUID
    metric_name: str
    current_value: float
    predicted_value: float
    direction: str
    confidence: float
    prediction_horizon: float
    reason: str
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class PredictionSnapshot:
    """Collection of predictions at a point in time."""

    entries: tuple[PredictionEntry, ...] = field(default_factory=tuple)
    total_predictions: int = 0
    upward_count: int = 0
    downward_count: int = 0
    stable_count: int = 0
    uncertain_count: int = 0
    avg_confidence: float = 0.0
    created_at: float = 0.0
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class PredictionTrace:
    """Metadata about a prediction operation."""

    stages: tuple[str, ...] = field(default_factory=tuple)
    duration_ms: float = 0.0
    total_predicted: int = 0
    metrics: dict[str, float] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class PredictionResult:
    """Output of a prediction operation."""

    success: bool
    snapshot: PredictionSnapshot | None = None
    trace: PredictionTrace | None = None
    error_message: str = ""


# ------------------------------------------------------------------
# Helpers
# ------------------------------------------------------------------


def _now() -> float:
    return time.time()


def _safe_mean(values: list[float]) -> float:
    return mean(values) if values else 0.0


def _clamp(value: float, lo: float = 0.0, hi: float = 1.0) -> float:
    return max(lo, min(hi, value))


def _adjust_confidence_for_horizon(confidence: float, horizon: float) -> float:
    horizon_hours = horizon / 3600.0
    penalty = 1.0 / (1.0 + horizon_hours * 0.10)
    return _clamp(confidence * penalty, MIN_CONFIDENCE, MAX_CONFIDENCE)


def _infer_direction_from_trend(trend: str, is_cost_metric: bool = False) -> str:
    if trend == TREND_IMPROVING:
        return DOWNWARD if is_cost_metric else UPWARD
    if trend == TREND_DECLINING:
        return UPWARD if is_cost_metric else DOWNWARD
    if trend == TREND_STABLE:
        return STABLE
    return UNCERTAIN


def _base_confidence_from_trend(trend: str, percent_change: float) -> float:
    if trend == TREND_IMPROVING or trend == TREND_DECLINING:
        strength = min(abs(percent_change) / 100.0, 1.0)
        return _clamp(0.5 + strength * 0.4, MIN_CONFIDENCE, MAX_CONFIDENCE)
    if trend == TREND_STABLE:
        return 0.80
    return 0.55


def _predict_current_value(
    current: float,
    direction: str,
    horizon: float,
) -> float:
    if direction == UPWARD:
        return round(current * (1.0 + horizon / 7200.0 * 0.1), 6)
    if direction == DOWNWARD:
        return round(current * (1.0 - horizon / 7200.0 * 0.1), 6)
    return current


# ------------------------------------------------------------------
# FoundationPredictionRuntime
# ------------------------------------------------------------------


class FoundationPredictionRuntime:
    """Stateless deterministic prediction engine.

    Uses historical trends and current snapshots to project future
    metric values with heuristic-based confidence scores.
    """

    # --------------------------------------------------------------
    # Domain prediction methods
    # --------------------------------------------------------------

    @staticmethod
    def predict_monitoring(
        monitoring: MonitoringSnapshot | None = None,
        history: HistoricalSnapshot | None = None,
        horizon: float = DEFAULT_HORIZON,
    ) -> list[PredictionEntry]:
        """Predict future monitoring metrics."""
        entries: list[PredictionEntry] = []
        if monitoring is None:
            return entries

        fields = [
            ("total_events", float(monitoring.total_events)),
            ("total_errors", float(monitoring.total_errors)),
            ("total_success", float(monitoring.total_success)),
            ("success_rate", monitoring.success_rate),
            ("error_rate", monitoring.error_rate),
            ("event_rate", monitoring.event_rate),
            ("health_score", monitoring.health_score),
            ("uptime", monitoring.uptime),
        ]
        cost_metrics = {"total_errors", "error_rate"}

        for name, current in fields:
            trend, pct = FoundationPredictionRuntime._find_trend_for_metric(
                history, name,
            )
            direction = _infer_direction_from_trend(trend)
            base_conf = _base_confidence_from_trend(trend, pct)

            if trend == TREND_UNKNOWN:
                direction = UPWARD if current < HEALTHY_HEALTH_SCORE else STABLE
                base_conf = 0.50

            confidence = _adjust_confidence_for_horizon(base_conf, horizon)
            predicted = _predict_current_value(current, direction, horizon)
            reason = FoundationPredictionRuntime._build_reason(
                "monitoring", name, trend, direction, confidence,
            )

            entries.append(PredictionEntry(
                prediction_id=uuid4(),
                metric_name=name,
                current_value=current,
                predicted_value=predicted,
                direction=direction,
                confidence=confidence,
                prediction_horizon=horizon,
                reason=reason,
                metadata={"domain": "monitoring"},
            ))
        return entries

    @staticmethod
    def predict_performance(
        performance: PerformanceSnapshot | None = None,
        history: HistoricalSnapshot | None = None,
        horizon: float = DEFAULT_HORIZON,
    ) -> list[PredictionEntry]:
        """Predict future performance metrics."""
        entries: list[PredictionEntry] = []
        if performance is None:
            return entries

        for key, metric in sorted(performance.metrics.items()):
            name = f"perf_{key}"
            current = metric.value
            trend, pct = FoundationPredictionRuntime._find_trend_for_metric(
                history, name,
            )
            direction = _infer_direction_from_trend(trend)
            base_conf = _base_confidence_from_trend(trend, pct)
            if trend == TREND_UNKNOWN:
                direction = STABLE
                base_conf = 0.40
            confidence = _adjust_confidence_for_horizon(base_conf, horizon)
            predicted = _predict_current_value(current, direction, horizon)
            reason = FoundationPredictionRuntime._build_reason(
                "performance", key, trend, direction, confidence,
            )
            entries.append(PredictionEntry(
                prediction_id=uuid4(),
                metric_name=name,
                current_value=current,
                predicted_value=predicted,
                direction=direction,
                confidence=confidence,
                prediction_horizon=horizon,
                reason=reason,
                metadata={"domain": "performance", "metric_key": key},
            ))
        return entries

    @staticmethod
    def predict_strategy(
        strategy: StrategySnapshot | None = None,
        history: HistoricalSnapshot | None = None,
        horizon: float = DEFAULT_HORIZON,
    ) -> list[PredictionEntry]:
        """Predict future strategy metrics."""
        entries: list[PredictionEntry] = []
        if strategy is None:
            return entries

        total_recs = float(len(strategy.recommendations))
        direction: str = STABLE
        base_conf = 0.50
        if history is not None:
            trend, pct = FoundationPredictionRuntime._find_trend_for_metric(
                history, "total_recommendations",
            )
            direction = _infer_direction_from_trend(trend)
            base_conf = _base_confidence_from_trend(trend, pct)
        confidence = _adjust_confidence_for_horizon(base_conf, horizon)
        predicted = _predict_current_value(total_recs, direction, horizon)
        reason = FoundationPredictionRuntime._build_reason(
            "strategy", "total_recommendations", "N/A", direction, confidence,
        )
        entries.append(PredictionEntry(
            prediction_id=uuid4(),
            metric_name="total_recommendations",
            current_value=total_recs,
            predicted_value=predicted,
            direction=direction,
            confidence=confidence,
            prediction_horizon=horizon,
            reason=reason,
            metadata={"domain": "strategy"},
        ))

        for cat in sorted(strategy.recommendations_by_category.keys()):
            current = float(strategy.recommendations_by_category[cat])
            metric = f"recs_{cat}"
            trend, pct = FoundationPredictionRuntime._find_trend_for_metric(
                history, metric,
            )
            d = _infer_direction_from_trend(trend)
            bc = _base_confidence_from_trend(trend, pct)
            if trend == TREND_UNKNOWN:
                d = STABLE
                bc = 0.40
            c = _adjust_confidence_for_horizon(bc, horizon)
            p = _predict_current_value(current, d, horizon)
            r = FoundationPredictionRuntime._build_reason(
                "strategy", metric, trend, d, c,
            )
            entries.append(PredictionEntry(
                prediction_id=uuid4(),
                metric_name=metric,
                current_value=current,
                predicted_value=p,
                direction=d,
                confidence=c,
                prediction_horizon=horizon,
                reason=r,
                metadata={"domain": "strategy", "category": cat},
            ))

        return entries

    @staticmethod
    def predict_feedback(
        feedback: FeedbackSnapshot | None = None,
        history: HistoricalSnapshot | None = None,
        horizon: float = DEFAULT_HORIZON,
    ) -> list[PredictionEntry]:
        """Predict future feedback metrics."""
        entries: list[PredictionEntry] = []
        if feedback is None:
            return entries

        fields = [
            ("total_entries", float(feedback.total_entries)),
            ("success_count", float(feedback.success_count)),
            ("failure_count", float(feedback.failure_count)),
            ("success_rate", feedback.success_rate),
            ("accuracy", feedback.accuracy),
            ("roi", feedback.roi),
            ("avg_confidence_before", feedback.avg_confidence_before),
            ("avg_confidence_after", feedback.avg_confidence_after),
            ("avg_delta", feedback.avg_delta),
            ("total_duration", feedback.total_duration),
            ("total_cost", feedback.total_cost),
        ]
        cost_metrics = {"total_duration", "total_cost", "failure_count"}

        for name, current in fields:
            trend, pct = FoundationPredictionRuntime._find_trend_for_metric(
                history, name,
            )
            is_cost = name in cost_metrics
            direction = _infer_direction_from_trend(trend, is_cost)
            base_conf = _base_confidence_from_trend(trend, pct)
            if trend == TREND_UNKNOWN:
                direction = STABLE
                base_conf = 0.35
            confidence = _adjust_confidence_for_horizon(base_conf, horizon)
            predicted = _predict_current_value(current, direction, horizon)
            reason = FoundationPredictionRuntime._build_reason(
                "feedback", name, trend, direction, confidence,
            )
            entries.append(PredictionEntry(
                prediction_id=uuid4(),
                metric_name=name,
                current_value=current,
                predicted_value=predicted,
                direction=direction,
                confidence=confidence,
                prediction_horizon=horizon,
                reason=reason,
                metadata={"domain": "feedback"},
            ))
        return entries

    @staticmethod
    def predict_learning(
        learning: LearningSnapshot | None = None,
        history: HistoricalSnapshot | None = None,
        horizon: float = DEFAULT_HORIZON,
    ) -> list[PredictionEntry]:
        """Predict future learning metrics."""
        entries: list[PredictionEntry] = []
        if learning is None:
            return entries

        total_recs = float(len(learning.recommendations))
        trend, pct = FoundationPredictionRuntime._find_trend_for_metric(
            history, "total_recommendations",
        )
        direction = _infer_direction_from_trend(trend)
        base_conf = _base_confidence_from_trend(trend, pct)
        if trend == TREND_UNKNOWN:
            direction = STABLE
            base_conf = 0.40
        confidence = _adjust_confidence_for_horizon(base_conf, horizon)
        predicted = _predict_current_value(total_recs, direction, horizon)
        reason = FoundationPredictionRuntime._build_reason(
            "learning", "total_recommendations", trend, direction, confidence,
        )
        entries.append(PredictionEntry(
            prediction_id=uuid4(),
            metric_name="total_recommendations",
            current_value=total_recs,
            predicted_value=predicted,
            direction=direction,
            confidence=confidence,
            prediction_horizon=horizon,
            reason=reason,
            metadata={"domain": "learning"},
        ))
        return entries

    @staticmethod
    def predict_skills(
        skills: SkillSnapshot | None = None,
        history: HistoricalSnapshot | None = None,
        horizon: float = DEFAULT_HORIZON,
    ) -> list[PredictionEntry]:
        """Predict future skills metrics."""
        entries: list[PredictionEntry] = []
        if skills is None:
            return entries

        fields = [
            ("total_skills", float(len(skills.skills))),
        ]
        levels = [r.level for r in skills.skills]
        xp = [r.experience_points for r in skills.skills]
        avg_level = _safe_mean([float(x) for x in levels])
        total_xp = float(sum(xp))

        fields.append(("avg_level", avg_level))
        fields.append(("total_xp", total_xp))

        for name, current in fields:
            trend, pct = FoundationPredictionRuntime._find_trend_for_metric(
                history, name,
            )
            direction = _infer_direction_from_trend(trend)
            base_conf = _base_confidence_from_trend(trend, pct)
            if trend == TREND_UNKNOWN:
                direction = UPWARD if current <= 1.0 else STABLE
                base_conf = 0.35
            confidence = _adjust_confidence_for_horizon(base_conf, horizon)
            predicted = _predict_current_value(current, direction, horizon)
            reason = FoundationPredictionRuntime._build_reason(
                "skills", name, trend, direction, confidence,
            )
            entries.append(PredictionEntry(
                prediction_id=uuid4(),
                metric_name=name,
                current_value=current,
                predicted_value=predicted,
                direction=direction,
                confidence=confidence,
                prediction_horizon=horizon,
                reason=reason,
                metadata={"domain": "skills"},
            ))
        return entries

    @staticmethod
    def predict_workflow(
        workflow: list[WorkflowRuntimeSnapshot] | None = None,
        history: HistoricalSnapshot | None = None,
        horizon: float = DEFAULT_HORIZON,
    ) -> list[PredictionEntry]:
        """Predict future workflow metrics."""
        entries: list[PredictionEntry] = []
        wf_list = workflow or []
        total = float(len(wf_list))
        completed = float(sum(1 for w in wf_list if w.state.value == "completed"))
        failed = float(sum(1 for w in wf_list if w.state.value == "failed"))
        avg_progress = _safe_mean([w.progress for w in wf_list])

        metric_fields = [
            ("total_workflows", total),
            ("completed_workflows", completed),
            ("failed_workflows", failed),
            ("avg_progress", avg_progress),
        ]
        cost_metrics = {"failed_workflows"}

        for name, current in metric_fields:
            trend, pct = FoundationPredictionRuntime._find_trend_for_metric(
                history, name,
            )
            is_cost = name in cost_metrics
            direction = _infer_direction_from_trend(trend, is_cost)
            base_conf = _base_confidence_from_trend(trend, pct)
            if trend == TREND_UNKNOWN:
                direction = STABLE
                base_conf = 0.35
            confidence = _adjust_confidence_for_horizon(base_conf, horizon)
            predicted = _predict_current_value(current, direction, horizon)
            reason = FoundationPredictionRuntime._build_reason(
                "workflow", name, trend, direction, confidence,
            )
            entries.append(PredictionEntry(
                prediction_id=uuid4(),
                metric_name=name,
                current_value=current,
                predicted_value=predicted,
                direction=direction,
                confidence=confidence,
                prediction_horizon=horizon,
                reason=reason,
                metadata={"domain": "workflow"},
            ))
        return entries

    @staticmethod
    def predict_cost(
        monitoring: MonitoringSnapshot | None = None,
        performance: PerformanceSnapshot | None = None,
        feedback: FeedbackSnapshot | None = None,
        history: HistoricalSnapshot | None = None,
        horizon: float = DEFAULT_HORIZON,
    ) -> list[PredictionEntry]:
        """Predict future cost-related metrics."""
        entries: list[PredictionEntry] = []

        if monitoring is not None:
            error_rate = monitoring.error_rate
            trend, pct = FoundationPredictionRuntime._find_trend_for_metric(
                history, "error_rate",
            )
            direction = _infer_direction_from_trend(trend, is_cost_metric=True)
            base_conf = _base_confidence_from_trend(trend, pct)
            if trend == TREND_UNKNOWN:
                direction = STABLE if error_rate < 10.0 else DOWNWARD
                base_conf = 0.35
            confidence = _adjust_confidence_for_horizon(base_conf, horizon)
            predicted = _predict_current_value(error_rate, direction, horizon)
            reason = FoundationPredictionRuntime._build_reason(
                "cost", "error_rate", trend, direction, confidence,
            )
            entries.append(PredictionEntry(
                prediction_id=uuid4(),
                metric_name="cost_error_rate",
                current_value=error_rate,
                predicted_value=predicted,
                direction=direction,
                confidence=confidence,
                prediction_horizon=horizon,
                reason=reason,
                metadata={"domain": "cost", "source": "monitoring"},
            ))

        if feedback is not None:
            for name, current in [
                ("cost_total_duration", feedback.total_duration),
                ("cost_total_cost", feedback.total_cost),
            ]:
                trend, pct = FoundationPredictionRuntime._find_trend_for_metric(
                    history, name,
                )
                direction = _infer_direction_from_trend(trend, is_cost_metric=True)
                base_conf = _base_confidence_from_trend(trend, pct)
                if trend == TREND_UNKNOWN:
                    direction = STABLE
                    base_conf = 0.30
                confidence = _adjust_confidence_for_horizon(base_conf, horizon)
                predicted = _predict_current_value(current, direction, horizon)
                reason = FoundationPredictionRuntime._build_reason(
                    "cost", name, trend, direction, confidence,
                )
                entries.append(PredictionEntry(
                    prediction_id=uuid4(),
                    metric_name=name,
                    current_value=current,
                    predicted_value=predicted,
                    direction=direction,
                    confidence=confidence,
                    prediction_horizon=horizon,
                    reason=reason,
                    metadata={"domain": "cost", "source": "feedback"},
                ))
        return entries

    @staticmethod
    def predict_health(
        monitoring: MonitoringSnapshot | None = None,
        history: HistoricalSnapshot | None = None,
        horizon: float = DEFAULT_HORIZON,
    ) -> list[PredictionEntry]:
        """Predict future health score."""
        entries: list[PredictionEntry] = []
        if monitoring is None:
            return entries

        current = monitoring.health_score
        trend, pct = FoundationPredictionRuntime._find_trend_for_metric(
            history, "health_score",
        )
        direction = _infer_direction_from_trend(trend)
        base_conf = _base_confidence_from_trend(trend, pct)
        if trend == TREND_UNKNOWN:
            direction = UPWARD if current < HEALTHY_HEALTH_SCORE else STABLE
            base_conf = 0.50
        confidence = _adjust_confidence_for_horizon(base_conf, horizon)
        predicted = _predict_current_value(current, direction, horizon)
        reason = FoundationPredictionRuntime._build_reason(
            "health", "health_score", trend, direction, confidence,
        )
        entries.append(PredictionEntry(
            prediction_id=uuid4(),
            metric_name="health_score",
            current_value=current,
            predicted_value=predicted,
            direction=direction,
            confidence=confidence,
            prediction_horizon=horizon,
            reason=reason,
            metadata={"domain": "health"},
        ))
        return entries

    @staticmethod
    def predict_success_rate(
        monitoring: MonitoringSnapshot | None = None,
        feedback: FeedbackSnapshot | None = None,
        history: HistoricalSnapshot | None = None,
        horizon: float = DEFAULT_HORIZON,
    ) -> list[PredictionEntry]:
        """Predict future success rate."""
        entries: list[PredictionEntry] = []

        if monitoring is not None:
            current = monitoring.success_rate
            trend, pct = FoundationPredictionRuntime._find_trend_for_metric(
                history, "success_rate",
            )
            direction = _infer_direction_from_trend(trend)
            base_conf = _base_confidence_from_trend(trend, pct)
            if trend == TREND_UNKNOWN:
                direction = UPWARD if current < HEALTHY_SUCCESS_RATE else STABLE
                base_conf = 0.40
            confidence = _adjust_confidence_for_horizon(base_conf, horizon)
            predicted = _predict_current_value(current, direction, horizon)
            reason = FoundationPredictionRuntime._build_reason(
                "success_rate", "success_rate", trend, direction, confidence,
            )
            entries.append(PredictionEntry(
                prediction_id=uuid4(),
                metric_name="success_rate",
                current_value=current,
                predicted_value=predicted,
                direction=direction,
                confidence=confidence,
                prediction_horizon=horizon,
                reason=reason,
                metadata={"domain": "success_rate", "source": "monitoring"},
            ))

        if feedback is not None:
            current = feedback.success_rate
            trend, pct = FoundationPredictionRuntime._find_trend_for_metric(
                history, "feedback_success_rate",
            )
            direction = _infer_direction_from_trend(trend)
            base_conf = _base_confidence_from_trend(trend, pct)
            if trend == TREND_UNKNOWN:
                direction = UPWARD if current < HEALTHY_SUCCESS_RATE else STABLE
                base_conf = 0.35
            confidence = _adjust_confidence_for_horizon(base_conf, horizon)
            predicted = _predict_current_value(current, direction, horizon)
            reason = FoundationPredictionRuntime._build_reason(
                "success_rate", "feedback_success_rate", trend, direction, confidence,
            )
            entries.append(PredictionEntry(
                prediction_id=uuid4(),
                metric_name="feedback_success_rate",
                current_value=current,
                predicted_value=predicted,
                direction=direction,
                confidence=confidence,
                prediction_horizon=horizon,
                reason=reason,
                metadata={"domain": "success_rate", "source": "feedback"},
            ))
        return entries

    @staticmethod
    def predict_confidence(
        feedback: FeedbackSnapshot | None = None,
        history: HistoricalSnapshot | None = None,
        horizon: float = DEFAULT_HORIZON,
    ) -> list[PredictionEntry]:
        """Predict future confidence metrics."""
        entries: list[PredictionEntry] = []
        if feedback is None:
            return entries

        for name, current in [
            ("avg_confidence_before", feedback.avg_confidence_before),
            ("avg_confidence_after", feedback.avg_confidence_after),
        ]:
            trend, pct = FoundationPredictionRuntime._find_trend_for_metric(
                history, name,
            )
            direction = _infer_direction_from_trend(trend)
            base_conf = _base_confidence_from_trend(trend, pct)
            if trend == TREND_UNKNOWN:
                direction = UPWARD if current < 0.5 else STABLE
                base_conf = 0.35
            confidence = _adjust_confidence_for_horizon(base_conf, horizon)
            predicted = _predict_current_value(current, direction, horizon)
            reason = FoundationPredictionRuntime._build_reason(
                "confidence", name, trend, direction, confidence,
            )
            entries.append(PredictionEntry(
                prediction_id=uuid4(),
                metric_name=name,
                current_value=current,
                predicted_value=predicted,
                direction=direction,
                confidence=confidence,
                prediction_horizon=horizon,
                reason=reason,
                metadata={"domain": "confidence"},
            ))
        return entries

    # --------------------------------------------------------------
    # Master predict — dispatch by type
    # --------------------------------------------------------------

    @staticmethod
    def predict(
        monitoring: MonitoringSnapshot | None = None,
        performance: PerformanceSnapshot | None = None,
        strategy: StrategySnapshot | None = None,
        feedback: FeedbackSnapshot | None = None,
        learning: LearningSnapshot | None = None,
        skills: SkillSnapshot | None = None,
        workflow: list[WorkflowRuntimeSnapshot] | None = None,
        history: HistoricalSnapshot | None = None,
        horizon: float = DEFAULT_HORIZON,
    ) -> list[PredictionEntry]:
        """Dispatch predict_* based on provided snapshot types."""
        all_entries: list[PredictionEntry] = []
        if monitoring is not None:
            all_entries.extend(
                FoundationPredictionRuntime.predict_monitoring(monitoring, history, horizon),
            )
        if performance is not None:
            all_entries.extend(
                FoundationPredictionRuntime.predict_performance(performance, history, horizon),
            )
        if strategy is not None:
            all_entries.extend(
                FoundationPredictionRuntime.predict_strategy(strategy, history, horizon),
            )
        if feedback is not None:
            all_entries.extend(
                FoundationPredictionRuntime.predict_feedback(feedback, history, horizon),
            )
        if learning is not None:
            all_entries.extend(
                FoundationPredictionRuntime.predict_learning(learning, history, horizon),
            )
        if skills is not None:
            all_entries.extend(
                FoundationPredictionRuntime.predict_skills(skills, history, horizon),
            )
        if workflow is not None:
            all_entries.extend(
                FoundationPredictionRuntime.predict_workflow(workflow, history, horizon),
            )
        return all_entries

    # --------------------------------------------------------------
    # Grouping
    # --------------------------------------------------------------

    @staticmethod
    def group_by_metric(
        entries: list[PredictionEntry] | tuple[PredictionEntry, ...],
    ) -> dict[str, list[PredictionEntry]]:
        """Group prediction entries by metric name."""
        groups: dict[str, list[PredictionEntry]] = {}
        for e in entries:
            groups.setdefault(e.metric_name, []).append(e)
        return dict(sorted(groups.items()))

    @staticmethod
    def group_by_confidence(
        entries: list[PredictionEntry] | tuple[PredictionEntry, ...],
        high_threshold: float = 0.7,
        medium_threshold: float = 0.4,
    ) -> dict[str, list[PredictionEntry]]:
        """Group prediction entries by confidence band."""
        groups: dict[str, list[PredictionEntry]] = {"high": [], "medium": [], "low": []}
        for e in entries:
            if e.confidence >= high_threshold:
                groups["high"].append(e)
            elif e.confidence >= medium_threshold:
                groups["medium"].append(e)
            else:
                groups["low"].append(e)
        return dict(sorted(groups.items()))

    # --------------------------------------------------------------
    # Filtering
    # --------------------------------------------------------------

    @staticmethod
    def filter_predictions(
        entries: list[PredictionEntry] | tuple[PredictionEntry, ...],
        metric_name: str | None = None,
        direction: str | None = None,
        domain: str | None = None,
        min_confidence: float | None = None,
        max_confidence: float | None = None,
    ) -> list[PredictionEntry]:
        """Filter prediction entries by multiple criteria."""
        result = list(entries)
        if metric_name is not None:
            result = [e for e in result if e.metric_name == metric_name]
        if direction is not None:
            result = [e for e in result if e.direction == direction]
        if domain is not None:
            result = [e for e in result if e.metadata.get("domain") == domain]
        if min_confidence is not None:
            result = [e for e in result if e.confidence >= min_confidence]
        if max_confidence is not None:
            result = [e for e in result if e.confidence <= max_confidence]
        return result

    # --------------------------------------------------------------
    # Merge
    # --------------------------------------------------------------

    @staticmethod
    def merge_predictions(
        snapshots: list[PredictionSnapshot],
    ) -> PredictionSnapshot:
        """Merge multiple PredictionSnapshots into one deduplicated snapshot."""
        seen: set[UUID] = set()
        all_entries: list[PredictionEntry] = []
        merged_metadata: dict[str, Any] = {}

        for snap in snapshots:
            merged_metadata.update(snap.metadata)
            for entry in snap.entries:
                if entry.prediction_id not in seen:
                    seen.add(entry.prediction_id)
                    all_entries.append(entry)

        return FoundationPredictionRuntime.build_snapshot(
            all_entries,
            merged_metadata,
        )

    # --------------------------------------------------------------
    # Snapshot, Trace, Result
    # --------------------------------------------------------------

    @staticmethod
    def build_snapshot(
        entries: list[PredictionEntry] | tuple[PredictionEntry, ...],
        metadata: dict[str, Any] | None = None,
    ) -> PredictionSnapshot:
        """Build a PredictionSnapshot from a list of prediction entries."""
        entry_list = list(entries)
        total = len(entry_list)
        upward = sum(1 for e in entry_list if e.direction == UPWARD)
        downward = sum(1 for e in entry_list if e.direction == DOWNWARD)
        stable = sum(1 for e in entry_list if e.direction == STABLE)
        uncertain = sum(1 for e in entry_list if e.direction == UNCERTAIN)
        avg_conf = _safe_mean([e.confidence for e in entry_list])

        return PredictionSnapshot(
            entries=tuple(entry_list),
            total_predictions=total,
            upward_count=upward,
            downward_count=downward,
            stable_count=stable,
            uncertain_count=uncertain,
            avg_confidence=round(avg_conf, 6),
            created_at=_now(),
            metadata=metadata or {},
        )

    @staticmethod
    def build_trace(
        stages: list[str] | None = None,
        duration_ms: float = 0.0,
        total_predicted: int = 0,
        metrics: dict[str, float] | None = None,
    ) -> PredictionTrace:
        """Create a PredictionTrace from raw data."""
        return PredictionTrace(
            stages=tuple(stages or []),
            duration_ms=duration_ms,
            total_predicted=total_predicted,
            metrics=metrics or {},
        )

    @staticmethod
    def build_result(
        snapshot: PredictionSnapshot,
        stages: list[str] | None = None,
        metrics: dict[str, float] | None = None,
    ) -> PredictionResult:
        """Wrap a PredictionSnapshot in a PredictionResult."""
        trace = PredictionTrace(
            stages=tuple(stages or []),
            duration_ms=0.0,
            total_predicted=snapshot.total_predictions,
            metrics=metrics or {},
        )
        return PredictionResult(success=True, snapshot=snapshot, trace=trace)

    # --------------------------------------------------------------
    # Summarize
    # --------------------------------------------------------------

    @staticmethod
    def summarize(
        snapshot: PredictionSnapshot,
    ) -> dict[str, Any]:
        """Return a human-readable summary of a PredictionSnapshot."""
        metric_groups = FoundationPredictionRuntime.group_by_metric(snapshot.entries)
        conf_groups = FoundationPredictionRuntime.group_by_confidence(snapshot.entries)

        return {
            "total_predictions": snapshot.total_predictions,
            "upward_count": snapshot.upward_count,
            "downward_count": snapshot.downward_count,
            "stable_count": snapshot.stable_count,
            "uncertain_count": snapshot.uncertain_count,
            "avg_confidence": snapshot.avg_confidence,
            "by_metric": {k: len(v) for k, v in metric_groups.items()},
            "by_confidence": {k: len(v) for k, v in conf_groups.items()},
        }

    # --------------------------------------------------------------
    # Run — full prediction pipeline
    # --------------------------------------------------------------

    @staticmethod
    def run(
        historical: HistoricalSnapshot | None = None,
        monitoring: MonitoringSnapshot | None = None,
        performance: PerformanceSnapshot | None = None,
        strategy: StrategySnapshot | None = None,
        feedback: FeedbackSnapshot | None = None,
        learning: LearningSnapshot | None = None,
        skills: SkillSnapshot | None = None,
        workflow: list[WorkflowRuntimeSnapshot] | None = None,
        horizon: float = DEFAULT_HORIZON,
    ) -> PredictionResult:
        """Run the full prediction pipeline across all domains.

        Produces a consolidated PredictionResult with predictions
        for every provided domain.
        """
        stages: list[str] = ["run"]
        start = _now()
        all_entries: list[PredictionEntry] = []
        metrics: dict[str, float] = {}

        if monitoring is not None:
            entries = FoundationPredictionRuntime.predict_monitoring(
                monitoring, historical, horizon,
            )
            all_entries.extend(entries)
            stages.append("monitoring")
            metrics["monitoring_predictions"] = float(len(entries))

        if performance is not None:
            entries = FoundationPredictionRuntime.predict_performance(
                performance, historical, horizon,
            )
            all_entries.extend(entries)
            stages.append("performance")
            metrics["performance_predictions"] = float(len(entries))

        if strategy is not None:
            entries = FoundationPredictionRuntime.predict_strategy(
                strategy, historical, horizon,
            )
            all_entries.extend(entries)
            stages.append("strategy")
            metrics["strategy_predictions"] = float(len(entries))

        if feedback is not None:
            entries = FoundationPredictionRuntime.predict_feedback(
                feedback, historical, horizon,
            )
            all_entries.extend(entries)
            stages.append("feedback")
            metrics["feedback_predictions"] = float(len(entries))

        if learning is not None:
            entries = FoundationPredictionRuntime.predict_learning(
                learning, historical, horizon,
            )
            all_entries.extend(entries)
            stages.append("learning")
            metrics["learning_predictions"] = float(len(entries))

        if skills is not None:
            entries = FoundationPredictionRuntime.predict_skills(
                skills, historical, horizon,
            )
            all_entries.extend(entries)
            stages.append("skills")
            metrics["skills_predictions"] = float(len(entries))

        if workflow is not None:
            entries = FoundationPredictionRuntime.predict_workflow(
                workflow, historical, horizon,
            )
            all_entries.extend(entries)
            stages.append("workflow")
            metrics["workflow_predictions"] = float(len(entries))

        snapshot = FoundationPredictionRuntime.build_snapshot(
            all_entries,
            {"source": "FoundationPredictionRuntime.run"},
        )
        metrics["total_predictions"] = float(snapshot.total_predictions)
        metrics["avg_confidence"] = snapshot.avg_confidence
        metrics["upward"] = float(snapshot.upward_count)
        metrics["downward"] = float(snapshot.downward_count)
        metrics["stable"] = float(snapshot.stable_count)
        metrics["uncertain"] = float(snapshot.uncertain_count)

        duration_ms = (_now() - start) * 1000.0
        trace = FoundationPredictionRuntime.build_trace(
            stages=stages,
            duration_ms=duration_ms,
            total_predicted=snapshot.total_predictions,
            metrics=metrics,
        )

        return FoundationPredictionRuntime.build_result(
            snapshot,
            stages=stages,
            metrics=metrics,
        )

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _find_trend_for_metric(
        history: HistoricalSnapshot | None,
        metric_name: str,
    ) -> tuple[str, float]:
        """Find the most recent trend and percent change for a metric."""
        if history is None or not history.entries:
            return TREND_UNKNOWN, 0.0
        matches = [e for e in history.entries if e.metric_name == metric_name]
        if not matches:
            return TREND_UNKNOWN, 0.0
        latest = max(matches, key=lambda e: e.timestamp_after)
        return latest.trend, latest.percent_change

    @staticmethod
    def _build_reason(
        domain: str,
        metric: str,
        trend: str,
        direction: str,
        confidence: float,
    ) -> str:
        base = f"{domain}:{metric} trend={trend} dir={direction} conf={confidence:.2f}"
        if trend == TREND_UNKNOWN:
            return f"No historical trend for {domain}/{metric}. Direction={direction}."
        return base
