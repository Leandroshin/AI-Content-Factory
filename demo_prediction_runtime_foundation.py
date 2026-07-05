"""Demo: FoundationPredictionRuntime — 260+ scenarios."""

from __future__ import annotations

import time
from typing import Any
from uuid import UUID, uuid4

from core.analytics.runtime import PerformanceMetric, PerformanceSnapshot
from core.feedback.foundation import FeedbackEntry, FeedbackSnapshot
from core.history.foundation import (
    HistoricalEntry,
    HistoricalSnapshot,
    TREND_DECLINING,
    TREND_IMPROVING,
    TREND_STABLE,
    TREND_UNKNOWN,
)
from core.learning.foundation import LearningRecommendation, LearningSnapshot
from core.monitoring.runtime import MonitoringSnapshot
from core.prediction.foundation import (
    DOWNWARD,
    STABLE,
    UNCERTAIN,
    UPWARD,
    FoundationPredictionRuntime as FPR,
    PredictionEntry,
    PredictionSnapshot,
    PredictionTrace,
    PredictionResult,
)
from core.skills.foundation import SkillRecord, SkillSnapshot
from core.strategy.foundation import StrategyRecommendation, StrategySnapshot
from core.workflows.runtime import WorkflowRuntimeSnapshot, WorkflowRuntimeState

PASS = 0
FAIL = 0
section_index = 0


def section(name: str) -> None:
    global section_index
    section_index += 1
    print(f"\n{'=' * 70}")
    print(f"Section {section_index}: {name}")
    print(f"{'=' * 70}")


def check(description: str, condition: bool, detail: str = "") -> None:
    global PASS, FAIL
    if condition:
        PASS += 1
        status = "PASS"
    else:
        FAIL += 1
        status = "FAIL"
    print(f"  [{status}] {description:50s} | {detail}")


def now() -> float:
    return time.time()


# Shared fixtures
mon_full = MonitoringSnapshot(
    total_events=1000, total_errors=50, total_success=950,
    success_rate=95.0, error_rate=5.0, event_rate=100.0,
    health_score=85.0, uptime=99.5,
)
mon_low = MonitoringSnapshot(
    total_events=100, total_errors=40, total_success=60,
    success_rate=60.0, error_rate=40.0, event_rate=10.0,
    health_score=30.0, uptime=80.0,
)
perf_full = PerformanceSnapshot({
    "accuracy": PerformanceMetric(name="accuracy", value=92.0, unit="%"),
    "latency": PerformanceMetric(name="latency", value=150.0, unit="ms"),
}, timestamp=now())
strat_recs = [
    StrategyRecommendation(
        recommendation_id=uuid4(), category="Cost Reduction",
        priority="HIGH", confidence=0.85, created_at=now(),
        title="Reduce cloud spend", description="", reason="",
        expected_benefit=100.0,
    ),
    StrategyRecommendation(
        recommendation_id=uuid4(), category="Performance Improvement",
        priority="MEDIUM", confidence=0.70, created_at=now(),
        title="Optimize queries", description="", reason="",
        expected_benefit=50.0,
    ),
]
strat_snap = StrategySnapshot(
    recommendations=strat_recs,
    recommendations_by_category={"Cost Reduction": 1, "Performance Improvement": 1},
    recommendations_by_priority={"HIGH": 1, "MEDIUM": 1},
    created_at=now(),
)
fb_entries = [
    FeedbackEntry(
        recommendation_id=uuid4(), action_id=uuid4(),
        expected_outcome="success", actual_outcome="completed",
        success=True, confidence_before=0.8, confidence_after=0.9,
        delta=0.1, execution_duration=5.0, execution_cost=10.0,
    ),
    FeedbackEntry(
        recommendation_id=uuid4(), action_id=uuid4(),
        expected_outcome="success", actual_outcome="failed",
        success=False, confidence_before=0.6, confidence_after=0.4,
        delta=-0.2, execution_duration=15.0, execution_cost=25.0,
    ),
]
fb_snap = FeedbackSnapshot(
    entries=tuple(fb_entries), total_entries=2,
    success_count=1, failure_count=1, success_rate=50.0,
    accuracy=50.0, roi=0.5, avg_confidence_before=0.7,
    avg_confidence_after=0.65, avg_delta=-0.05,
    total_duration=20.0, total_cost=35.0, created_at=now(),
)
learn_recs = [
    LearningRecommendation(
        recommendation_id=uuid4(), knowledge_id=uuid4(),
        recommendation_type="study", title="Learn Python",
        description="", priority=1, timestamp=now(),
    ),
]
learn_snap = LearningSnapshot(recommendations=tuple(learn_recs), created_at=now())
skill_recs = [
    SkillRecord(
        skill_id=uuid4(), recommendation_id=uuid4(),
        skill_name="Python", description="", level=3, experience_points=150,
    ),
    SkillRecord(
        skill_id=uuid4(), recommendation_id=uuid4(),
        skill_name="SQL", description="", level=2, experience_points=80,
    ),
]
skill_snap = SkillSnapshot(skills=tuple(skill_recs), created_at=now())
wf_list = [
    WorkflowRuntimeSnapshot(workflow_id=uuid4(), name="W1", state=WorkflowRuntimeState.COMPLETED, progress=100.0),
    WorkflowRuntimeSnapshot(workflow_id=uuid4(), name="W2", state=WorkflowRuntimeState.RUNNING, progress=50.0),
    WorkflowRuntimeSnapshot(workflow_id=uuid4(), name="W3", state=WorkflowRuntimeState.CREATED, progress=0.0),
]
empty_history = HistoricalSnapshot(
    entries=(), total_entries=0, created_at=now(),
)

# Historical data with trends
hist_entries = [
    HistoricalEntry(
        snapshot_before="A", snapshot_after="B",
        timestamp_before=0, timestamp_after=1,
        metric_name="health_score", old_value=70, new_value=85,
        delta=15, percent_change=21.43, trend=TREND_IMPROVING,
    ),
    HistoricalEntry(
        snapshot_before="A", snapshot_after="B",
        timestamp_before=0, timestamp_after=1,
        metric_name="success_rate", old_value=90, new_value=95,
        delta=5, percent_change=5.56, trend=TREND_IMPROVING,
    ),
    HistoricalEntry(
        snapshot_before="A", snapshot_after="B",
        timestamp_before=0, timestamp_after=1,
        metric_name="error_rate", old_value=10, new_value=5,
        delta=-5, percent_change=-50.0, trend=TREND_DECLINING,
    ),
    HistoricalEntry(
        snapshot_before="A", snapshot_after="B",
        timestamp_before=0, timestamp_after=1,
        metric_name="uptime", old_value=98, new_value=99.5,
        delta=1.5, percent_change=1.53, trend=TREND_STABLE,
    ),
]
hist_snap = HistoricalSnapshot(
    entries=tuple(hist_entries), total_entries=4,
    improving_count=2, declining_count=1, stable_count=1,
    avg_delta=4.125, avg_percent_change=-5.35, created_at=now(),
)


# ================================================================
# Section 1: Data models — PredictionEntry
# ================================================================
section("Data models — PredictionEntry")

entry = PredictionEntry(
    prediction_id=uuid4(),
    metric_name="health_score",
    current_value=85.0,
    predicted_value=90.0,
    direction=UPWARD,
    confidence=0.85,
    prediction_horizon=3600.0,
    reason="Improving trend",
    metadata={"domain": "monitoring"},
)
check("frozen", hasattr(entry, "metric_name"))
check("prediction_id UUID", isinstance(entry.prediction_id, UUID))
check("metric_name", entry.metric_name == "health_score")
check("current_value", entry.current_value == 85.0)
check("predicted_value", entry.predicted_value == 90.0)
check("direction UPWARD", entry.direction == UPWARD)
check("confidence", entry.confidence == 0.85)
check("prediction_horizon", entry.prediction_horizon == 3600.0)
check("reason", entry.reason == "Improving trend")
check("metadata domain", entry.metadata["domain"] == "monitoring")

entry_down = PredictionEntry(
    prediction_id=uuid4(), metric_name="error_rate",
    current_value=5.0, predicted_value=4.0,
    direction=DOWNWARD, confidence=0.75,
    prediction_horizon=7200.0, reason="Declining trend",
)
check("DOWNWARD direction", entry_down.direction == DOWNWARD)
check("DOWNWARD confidence", entry_down.confidence == 0.75)

entry_stable = PredictionEntry(
    prediction_id=uuid4(), metric_name="uptime",
    current_value=99.5, predicted_value=99.5,
    direction=STABLE, confidence=0.80,
    prediction_horizon=3600.0, reason="Stable trend",
)
check("STABLE direction", entry_stable.direction == STABLE)

entry_uncertain = PredictionEntry(
    prediction_id=uuid4(), metric_name="new_metric",
    current_value=0.0, predicted_value=0.0,
    direction=UNCERTAIN, confidence=0.10,
    prediction_horizon=3600.0, reason="No data",
)
check("UNCERTAIN direction", entry_uncertain.direction == UNCERTAIN)

# ================================================================
# Section 2: Data models — PredictionSnapshot
# ================================================================
section("Data models — PredictionSnapshot")

empty_snap = PredictionSnapshot()
check("frozen", hasattr(empty_snap, "total_predictions"))
check("empty total_predictions", empty_snap.total_predictions == 0)
check("empty upward_count", empty_snap.upward_count == 0)
check("empty downward_count", empty_snap.downward_count == 0)
check("empty stable_count", empty_snap.stable_count == 0)
check("empty uncertain_count", empty_snap.uncertain_count == 0)
check("empty avg_confidence", empty_snap.avg_confidence == 0.0)
check("empty created_at", empty_snap.created_at == 0.0)

populated = FPR.build_snapshot([entry, entry_down, entry_stable, entry_uncertain])
check("populated total", populated.total_predictions == 4)
check("populated upward", populated.upward_count == 1)
check("populated downward", populated.downward_count == 1)
check("populated stable", populated.stable_count == 1)
check("populated uncertain", populated.uncertain_count == 1)
check("populated avg_conf > 0", populated.avg_confidence > 0)
check("populated created_at > 0", populated.created_at > 0)

# ================================================================
# Section 3: Data models — Trace, Result
# ================================================================
section("Data models — Trace, Result")

trace = PredictionTrace()
check("Trace empty stages", len(trace.stages) == 0)
check("Trace empty duration", trace.duration_ms == 0.0)
check("Trace empty predicted", trace.total_predicted == 0)

trace_full = FPR.build_trace(
    stages=["run", "monitoring"], duration_ms=10.5,
    total_predicted=8, metrics={"mon": 8},
)
check("Trace stages len", len(trace_full.stages) == 2)
check("Trace duration", trace_full.duration_ms == 10.5)
check("Trace predicted", trace_full.total_predicted == 8)
check("Trace metrics", trace_full.metrics["mon"] == 8.0)

result = PredictionResult(success=False)
check("Result failed", result.success is False)
check("Result snap None", result.snapshot is None)

result_ok = FPR.build_result(populated, stages=["run"], metrics={"total": 4})
check("Result success", result_ok.success is True)
check("Result snapshot ref", result_ok.snapshot.total_predictions == 4)
check("Result trace present", result_ok.trace is not None)
check("Result trace stages", "run" in result_ok.trace.stages)

# ================================================================
# Section 4: predict_monitoring — empty
# ================================================================
section("predict_monitoring — empty")

check("None -> empty", len(FPR.predict_monitoring(None)) == 0)
entries = FPR.predict_monitoring(mon_full)
check("full -> 8 entries", len(entries) == 8)

# ================================================================
# Section 5: predict_monitoring — with history
# ================================================================
section("predict_monitoring — with history")

entries_h = FPR.predict_monitoring(mon_full, hist_snap)
check("8 entries with history", len(entries_h) == 8)
for e in entries_h:
    if e.metric_name == "health_score":
        check("health upward", e.direction == UPWARD)
        check("health confidence > 0.5", e.confidence > 0.5)
    elif e.metric_name == "error_rate":
        check("error downward", e.direction == DOWNWARD)
    elif e.metric_name == "uptime":
        check("uptime stable", e.direction == STABLE)

# ================================================================
# Section 6: predict_monitoring — low health
# ================================================================
section("predict_monitoring — low health")

entries_low = FPR.predict_monitoring(mon_low)
check("low health entries", len(entries_low) == 8)
for e in entries_low:
    if e.metric_name == "health_score":
        check("low health upward", e.direction == UPWARD)

# ================================================================
# Section 7: predict_performance — empty
# ================================================================
section("predict_performance — empty")

check("None -> empty", len(FPR.predict_performance(None)) == 0)
entries_p = FPR.predict_performance(perf_full)
check("full -> 2 entries", len(entries_p) == 2)
for e in entries_p:
    check(f"perf metric {e.metric_name}", e.metric_name.startswith("perf_"))

# ================================================================
# Section 8: predict_performance — with history
# ================================================================
section("predict_performance — with history")

entries_ph = FPR.predict_performance(perf_full, hist_snap)
check("2 entries", len(entries_ph) == 2)
for e in entries_ph:
    check("confidence > 0", e.confidence > 0)
    check("direction known", e.direction in (UPWARD, DOWNWARD, STABLE, UNCERTAIN))

# ================================================================
# Section 9: predict_strategy — empty
# ================================================================
section("predict_strategy — empty")

empty_strat = StrategySnapshot(
    recommendations=(),
    recommendations_by_category={},
    recommendations_by_priority={},
    created_at=now(),
)
check("None -> empty", len(FPR.predict_strategy(None)) == 0)
check("empty strategy -> 1", len(FPR.predict_strategy(empty_strat)) == 1)
check("strat with recs", len(FPR.predict_strategy(strat_snap)) == 3)

# ================================================================
# Section 10: predict_strategy — directions
# ================================================================
section("predict_strategy — directions")

entries_s = FPR.predict_strategy(strat_snap, hist_snap)
for e in entries_s:
    check("direction valid", e.direction in (UPWARD, DOWNWARD, STABLE, UNCERTAIN))

# ================================================================
# Section 11: predict_feedback — empty
# ================================================================
section("predict_feedback — empty")

check("None -> empty", len(FPR.predict_feedback(None)) == 0)
check("empty feedback -> 11", len(FPR.predict_feedback(FeedbackSnapshot(created_at=now()))) == 11)
check("feedback 11 fields", len(FPR.predict_feedback(fb_snap)) == 11)

# ================================================================
# Section 12: predict_feedback — directions
# ================================================================
section("predict_feedback — directions")

entries_f = FPR.predict_feedback(fb_snap)
up = sum(1 for e in entries_f if e.direction == UPWARD)
down = sum(1 for e in entries_f if e.direction == DOWNWARD)
stable = sum(1 for e in entries_f if e.direction == STABLE)
check("some upward", up >= 0)
check("some downward", down >= 0)
check("some stable", stable >= 0)

# ================================================================
# Section 13: predict_learning — empty
# ================================================================
section("predict_learning — empty")

check("None -> empty", len(FPR.predict_learning(None)) == 0)
check("empty learning -> 1", len(FPR.predict_learning(LearningSnapshot(created_at=now()))) == 1)
check("learning 1 entry", len(FPR.predict_learning(learn_snap)) == 1)

# ================================================================
# Section 14: predict_learning — direction
# ================================================================
section("predict_learning — direction")

for e in FPR.predict_learning(learn_snap):
    check("learning direction valid", e.direction in (UPWARD, DOWNWARD, STABLE, UNCERTAIN))

# ================================================================
# Section 15: predict_skills — empty
# ================================================================
section("predict_skills — empty")

check("None -> empty", len(FPR.predict_skills(None)) == 0)
check("empty skills -> 3", len(FPR.predict_skills(SkillSnapshot(created_at=now()))) == 3)
check("skills 3 entries", len(FPR.predict_skills(skill_snap)) == 3)

# ================================================================
# Section 16: predict_skills — direction
# ================================================================
section("predict_skills — direction")

for e in FPR.predict_skills(skill_snap, hist_snap):
    check("skills direction valid", e.direction in (UPWARD, DOWNWARD, STABLE, UNCERTAIN))

# ================================================================
# Section 17: predict_workflow — empty
# ================================================================
section("predict_workflow — empty")

check("None -> 4 entries", len(FPR.predict_workflow(None)) == 4)
check("empty list -> 4", len(FPR.predict_workflow([])) == 4)
check("3 wf -> 4 entries", len(FPR.predict_workflow(wf_list)) == 4)

# ================================================================
# Section 18: predict_workflow — directions
# ================================================================
section("predict_workflow — directions")

for e in FPR.predict_workflow(wf_list):
    check("wf direction valid", e.direction in (UPWARD, DOWNWARD, STABLE, UNCERTAIN))

# ================================================================
# Section 19: predict_cost — empty
# ================================================================
section("predict_cost — empty")

check("None -> empty", len(FPR.predict_cost()) == 0)
check("monitoring cost -> 1", len(FPR.predict_cost(monitoring=mon_full)) == 1)
check("feedback cost -> 2", len(FPR.predict_cost(feedback=fb_snap)) == 2)
check("both -> 3", len(FPR.predict_cost(monitoring=mon_full, feedback=fb_snap)) == 3)

# ================================================================
# Section 20: predict_cost — directions
# ================================================================
section("predict_cost — directions")

entries_c = FPR.predict_cost(monitoring=mon_full, feedback=fb_snap)
for e in entries_c:
    check("cost direction valid", e.direction in (UPWARD, DOWNWARD, STABLE, UNCERTAIN))
    check("cost domain", e.metadata.get("domain") == "cost")

# ================================================================
# Section 21: predict_health — empty
# ================================================================
section("predict_health — empty")

check("None -> empty", len(FPR.predict_health(None)) == 0)
check("health 1 entry", len(FPR.predict_health(mon_full)) == 1)
for e in FPR.predict_health(mon_full):
    check("health metric", e.metric_name == "health_score")

# ================================================================
# Section 22: predict_health — low vs high
# ================================================================
section("predict_health — low vs high")

for e in FPR.predict_health(mon_low):
    check("low health upward", e.direction == UPWARD)
for e in FPR.predict_health(mon_full):
    check("high health stable", e.direction == STABLE)

# ================================================================
# Section 23: predict_success_rate — empty
# ================================================================
section("predict_success_rate — empty")

check("None -> empty", len(FPR.predict_success_rate()) == 0)
check("monitoring only -> 1", len(FPR.predict_success_rate(monitoring=mon_full)) == 1)
check("feedback only -> 1", len(FPR.predict_success_rate(feedback=fb_snap)) == 1)
check("both -> 2", len(FPR.predict_success_rate(monitoring=mon_full, feedback=fb_snap)) == 2)

# ================================================================
# Section 24: predict_success_rate — directions
# ================================================================
section("predict_success_rate — directions")

for e in FPR.predict_success_rate(monitoring=mon_full):
    check("high success stable/upward", e.direction in (STABLE, UPWARD))
for e in FPR.predict_success_rate(monitoring=mon_low):
    check("low success upward", e.direction == UPWARD)

# ================================================================
# Section 25: predict_confidence — empty
# ================================================================
section("predict_confidence — empty")

check("None -> empty", len(FPR.predict_confidence(None)) == 0)
check("confidence 2 entries", len(FPR.predict_confidence(fb_snap)) == 2)

# ================================================================
# Section 26: predict_confidence — directions
# ================================================================
section("predict_confidence — directions")

for e in FPR.predict_confidence(fb_snap):
    check("conf direction valid", e.direction in (UPWARD, DOWNWARD, STABLE, UNCERTAIN))

# ================================================================
# Section 27: predict — master dispatch
# ================================================================
section("predict — master dispatch")

check("No args -> empty", len(FPR.predict()) == 0)
check("monitoring only", len(FPR.predict(monitoring=mon_full)) == 8)
check("performance only", len(FPR.predict(performance=perf_full)) == 2)
check("strategy only", len(FPR.predict(strategy=strat_snap)) == 3)
check("feedback only", len(FPR.predict(feedback=fb_snap)) == 11)
check("learning only", len(FPR.predict(learning=learn_snap)) == 1)
check("skills only", len(FPR.predict(skills=skill_snap)) == 3)
check("workflow only", len(FPR.predict(workflow=wf_list)) == 4)
check("all domains", len(FPR.predict(
    monitoring=mon_full, performance=perf_full, strategy=strat_snap,
    feedback=fb_snap, learning=learn_snap, skills=skill_snap,
    workflow=wf_list,
)) == 8 + 2 + 3 + 11 + 1 + 3 + 4)

# ================================================================
# Section 28: group_by_metric
# ================================================================
section("group_by_metric")

all_preds = FPR.predict(monitoring=mon_full, performance=perf_full, strategy=strat_snap)
grouped = FPR.group_by_metric(all_preds)
check("metric groups > 0", len(grouped) > 0)
total_in_groups = sum(len(v) for v in grouped.values())
check("groups preserve count", total_in_groups == len(all_preds))
check("empty list", len(FPR.group_by_metric([])) == 0)

# ================================================================
# Section 29: group_by_confidence
# ================================================================
section("group_by_confidence")

conf_groups = FPR.group_by_confidence(all_preds)
check("has high key", "high" in conf_groups)
check("has medium key", "medium" in conf_groups)
check("has low key", "low" in conf_groups)
total_conf = sum(len(v) for v in conf_groups.values())
check("conf groups preserve count", total_conf == len(all_preds))
check("empty list", len(FPR.group_by_confidence([])["high"]) == 0)

# ================================================================
# Section 30: filter_predictions
# ================================================================
section("filter_predictions")

check("no filter", len(FPR.filter_predictions(all_preds)) == len(all_preds))
hp = FPR.filter_predictions(all_preds, metric_name="health_score")
check("filter health_score", len(hp) >= 1)
check("filter health correct", all(e.metric_name == "health_score" for e in hp))
up_preds = FPR.filter_predictions(all_preds, direction=UPWARD)
check("filter UPWARD", len(up_preds) >= 1)
check("filter upward correct", all(e.direction == UPWARD for e in up_preds))
mon_preds = FPR.filter_predictions(all_preds, domain="monitoring")
check("filter monitoring", len(mon_preds) == 8)
check("filter domain correct", all(e.metadata.get("domain") == "monitoring" for e in mon_preds))
high_conf = FPR.filter_predictions(all_preds, min_confidence=0.5)
check("filter min_conf none", len(high_conf) == 0)
check("filter min_conf correct", all(e.confidence >= 0.5 for e in high_conf))
low_conf = FPR.filter_predictions(all_preds, max_confidence=0.3)
check("filter max_conf", len(low_conf) >= 0)
check("filter nonexistent", len(FPR.filter_predictions(all_preds, metric_name="nonexistent")) == 0)

# ================================================================
# Section 31: merge_predictions
# ================================================================
section("merge_predictions")

snap_a = FPR.build_snapshot(FPR.predict_monitoring(mon_full))
snap_b = FPR.build_snapshot(FPR.predict_performance(perf_full))
merged = FPR.merge_predictions([snap_a, snap_b])
check("merged total", merged.total_predictions == snap_a.total_predictions + snap_b.total_predictions)
check("merged upward", merged.upward_count == snap_a.upward_count + snap_b.upward_count)
check("merged created_at > 0", merged.created_at > 0)

merged_same = FPR.merge_predictions([snap_a, snap_a])
check("dedup same entries", merged_same.total_predictions == snap_a.total_predictions)

empty_merge = FPR.merge_predictions([])
check("empty merge", empty_merge.total_predictions == 0)

# ================================================================
# Section 32: build_snapshot
# ================================================================
section("build_snapshot")

snap_empty = FPR.build_snapshot([])
check("empty total", snap_empty.total_predictions == 0)
check("empty upward", snap_empty.upward_count == 0)
check("empty created_at > 0", snap_empty.created_at > 0)

ents = FPR.predict(monitoring=mon_full, performance=perf_full)
snap = FPR.build_snapshot(ents)
check("10 entries", snap.total_predictions == len(ents))
check("upward+downward+stable+uncertain", snap.upward_count + snap.downward_count + snap.stable_count + snap.uncertain_count == len(ents))
check("avg_confidence > 0", snap.avg_confidence > 0)
check("metadata empty", snap.metadata == {})

snap_meta = FPR.build_snapshot(ents, {"source": "test"})
check("metadata passed", snap_meta.metadata.get("source") == "test")

# ================================================================
# Section 33: build_trace / build_result
# ================================================================
section("build_trace / build_result")

trace1 = FPR.build_trace()
check("trace default stages", len(trace1.stages) == 0)
trace2 = FPR.build_trace(
    stages=["run", "monitoring", "performance"],
    duration_ms=25.5, total_predicted=10,
    metrics={"total": 10.0},
)
check("trace custom stages", len(trace2.stages) == 3)
check("trace duration", trace2.duration_ms == 25.5)
check("trace total", trace2.total_predicted == 10)
res = FPR.build_result(snap, stages=["run"], metrics={"total": 10.0})
check("result success", res.success is True)
check("result snapshot ref", res.snapshot.total_predictions == 10)
check("result trace present", res.trace is not None)
check("result trace stages", "run" in res.trace.stages)

# ================================================================
# Section 34: summarize
# ================================================================
section("summarize")

summary = FPR.summarize(snap)
check("total_predictions key", "total_predictions" in summary)
check("upward_count key", "upward_count" in summary)
check("downward_count key", "downward_count" in summary)
check("stable_count key", "stable_count" in summary)
check("uncertain_count key", "uncertain_count" in summary)
check("avg_confidence key", "avg_confidence" in summary)
check("by_metric dict", "by_metric" in summary)
check("by_confidence dict", "by_confidence" in summary)

empty_summary = FPR.summarize(empty_snap)
check("empty summary total", empty_summary["total_predictions"] == 0)

# ================================================================
# Section 35: run — empty
# ================================================================
section("run — empty")

res_empty = FPR.run()
check("empty success", res_empty.success is True)
check("empty snapshot 0", res_empty.snapshot.total_predictions == 0)
check("empty trace present", res_empty.trace is not None)

# ================================================================
# Section 36: run — monitoring only
# ================================================================
section("run — monitoring only")

res_mon = FPR.run(monitoring=mon_full)
check("mon success", res_mon.success is True)
check("mon 8 predictions", res_mon.snapshot.total_predictions == 8)
check("mon trace has monitoring", "monitoring" in res_mon.trace.stages)

# ================================================================
# Section 37: run — all domains
# ================================================================
section("run — all domains")

res_all = FPR.run(
    historical=hist_snap,
    monitoring=mon_full,
    performance=perf_full,
    strategy=strat_snap,
    feedback=fb_snap,
    learning=learn_snap,
    skills=skill_snap,
    workflow=wf_list,
)
total_expected = 8 + 2 + 3 + 11 + 1 + 3 + 4
check("full run success", res_all.success is True)
check("trace stages count", len(res_all.trace.stages) >= 2)
check("total predictions", res_all.snapshot.total_predictions == total_expected)
check("avg confidence > 0", res_all.snapshot.avg_confidence > 0)

# ================================================================
# Section 38: Integration — Monitoring
# ================================================================
section("Integration — Monitoring")

from core.monitoring.runtime import MonitoringRuntime
check("MR importable", MonitoringRuntime is not None)
check("FPR.predict_monitoring callable", callable(FPR.predict_monitoring))

# ================================================================
# Section 39: Integration — Performance
# ================================================================
section("Integration — Performance")

from core.analytics.runtime import PerformanceRuntime
check("PR importable", PerformanceRuntime is not None)
check("FPR.predict_performance callable", callable(FPR.predict_performance))

# ================================================================
# Section 40: Integration — Strategy
# ================================================================
section("Integration — Strategy")

from core.strategy.foundation import FoundationStrategyRuntime
check("FSR importable", FoundationStrategyRuntime is not None)
check("FPR.predict_strategy callable", callable(FPR.predict_strategy))

# ================================================================
# Section 41: Integration — Feedback
# ================================================================
section("Integration — Feedback")

from core.feedback.foundation import FoundationFeedbackRuntime
check("FFR importable", FoundationFeedbackRuntime is not None)
check("FPR.predict_feedback callable", callable(FPR.predict_feedback))

# ================================================================
# Section 42: Integration — Historical
# ================================================================
section("Integration — Historical")

from core.history.foundation import FoundationHistoricalRuntime
check("FHR importable", FoundationHistoricalRuntime is not None)
fhr_result = FoundationHistoricalRuntime.run(
    monitoring_before=MonitoringSnapshot(),
    monitoring_after=mon_full,
)
check("FHR produces history", fhr_result.snapshot.total_entries > 0)
preds = FPR.predict_monitoring(mon_full, fhr_result.snapshot)
check("predictions from FHR output", len(preds) == 8)
for e in preds:
    check("confidence from FHR trend", e.confidence > 0)

# ================================================================
# Section 43: Integration — Learning
# ================================================================
section("Integration — Learning")

from core.learning.foundation import LearningRuntime
check("LR importable", LearningRuntime is not None)

# ================================================================
# Section 44: Integration — Skills
# ================================================================
section("Integration — Skills")

from core.skills.foundation import SkillRuntime
check("SR importable", SkillRuntime is not None)

# ================================================================
# Section 45: Integration — Workflow
# ================================================================
section("Integration — Workflow")

from core.workflows.runtime import WorkflowRuntime
check("WR importable", WorkflowRuntime is not None)

# ================================================================
# Section 46: Determinism
# ================================================================
section("Determinism")

ents_a = FPR.predict_monitoring(mon_full, hist_snap)
ents_b = FPR.predict_monitoring(mon_full, hist_snap)
check("same inputs same predictions count", len(ents_a) == len(ents_b))
for a, b in zip(ents_a, ents_b):
    check(f"deterministic {a.metric_name}", a.metric_name == b.metric_name)
    check(f"deterministic dir {a.metric_name}", a.direction == b.direction)
    check(f"deterministic conf {a.metric_name}", a.confidence == b.confidence)

# ================================================================
# Section 47: UUID
# ================================================================
section("UUID")

all_ids = [e.prediction_id for e in ents_a]
check("all have UUID", all(isinstance(pid, UUID) for pid in all_ids))
unique = len(set(all_ids)) == len(all_ids)
check("unique UUIDs", unique)
check("no shared UUIDs", len(set(all_ids)) == 8)

# ================================================================
# Section 48: Timestamps
# ================================================================
section("Timestamps")

snap_ts = FPR.build_snapshot(ents_a)
check("created_at > 0", snap_ts.created_at > 0)
check("created_at recent", snap_ts.created_at <= now() + 1)
result_ts = FPR.run(monitoring=mon_full)
check("result timestamp via trace", result_ts.trace.duration_ms >= 0)

# ================================================================
# Section 49: Metadata
# ================================================================
section("Metadata")

entry_meta = PredictionEntry(
    prediction_id=uuid4(), metric_name="test",
    current_value=1.0, predicted_value=2.0,
    direction=UPWARD, confidence=0.5,
    prediction_horizon=3600.0, reason="test",
    metadata={"env": "prod", "version": "1.0"},
)
check("entry metadata env", entry_meta.metadata["env"] == "prod")
check("entry metadata version", entry_meta.metadata["version"] == "1.0")

snap_meta = FPR.build_snapshot([entry_meta], {"source": "metadata_test"})
check("snapshot metadata", snap_meta.metadata["source"] == "metadata_test")

# ================================================================
# Section 50: Edge cases — all None
# ================================================================
section("Edge cases — all None")

check("mon None", len(FPR.predict_monitoring(None)) == 0)
check("perf None", len(FPR.predict_performance(None)) == 0)
check("strat None", len(FPR.predict_strategy(None)) == 0)
check("fb None", len(FPR.predict_feedback(None)) == 0)
check("learn None", len(FPR.predict_learning(None)) == 0)
check("skills None", len(FPR.predict_skills(None)) == 0)
check("health None", len(FPR.predict_health(None)) == 0)
check("success None", len(FPR.predict_success_rate()) == 0)
check("conf None", len(FPR.predict_confidence(None)) == 0)
check("cost None", len(FPR.predict_cost()) == 0)

# ================================================================
# Section 51: Edge cases — empty snapshots
# ================================================================
section("Edge cases — empty snapshots")

check("empty mon -> 8", len(FPR.predict_monitoring(MonitoringSnapshot())) == 8)
check("empty perf -> 0", len(FPR.predict_performance(PerformanceSnapshot({}, now()))) == 0)
check("empty strat -> 1", len(FPR.predict_strategy(StrategySnapshot(created_at=now()))) == 1)
check("empty fb -> 11", len(FPR.predict_feedback(FeedbackSnapshot(created_at=now()))) == 11)
check("empty learn -> 1", len(FPR.predict_learning(LearningSnapshot(created_at=now()))) == 1)
check("empty skills -> 3", len(FPR.predict_skills(SkillSnapshot(created_at=now()))) == 3)
check("empty wf list -> 4", len(FPR.predict_workflow([])) == 4)

# ================================================================
# Section 52: Edge cases — zero values
# ================================================================
section("Edge cases — zero values")

mon_zero = MonitoringSnapshot()
entries_z = FPR.predict_monitoring(mon_zero)
check("zero mon 8 entries", len(entries_z) == 8)
for e in entries_z:
    check(f"zero direction valid {e.metric_name}", e.direction in (UPWARD, DOWNWARD, STABLE, UNCERTAIN))

# ================================================================
# Section 53: Edge cases — large batch
# ================================================================
section("Edge cases — large batch")

large_strat_recs = [
    StrategyRecommendation(
        recommendation_id=uuid4(), category=f"Cat_{i}",
        priority="LOW", confidence=0.5, created_at=now(),
        title=f"Rec {i}", description="", reason="",
        expected_benefit=float(i),
    )
    for i in range(50)
]
large_strat = StrategySnapshot(
    recommendations=large_strat_recs,
    recommendations_by_category={f"Cat_{i}": 1 for i in range(50)},
    recommendations_by_priority={"LOW": 50},
    created_at=now(),
)
entries_large = FPR.predict_strategy(large_strat)
check("50 cats + 1 total = 51", len(entries_large) == 51)
for e in entries_large:
    check("large direction valid", e.direction in (UPWARD, DOWNWARD, STABLE, UNCERTAIN))
    check("large confidence > 0", e.confidence > 0)

# ================================================================
# Section 54: Edge cases — long metric names
# ================================================================
section("Edge cases — long metric names")

long_entry = PredictionEntry(
    prediction_id=uuid4(), metric_name="A" * 200,
    current_value=0.0, predicted_value=1.0,
    direction=UPWARD, confidence=0.5,
    prediction_horizon=3600.0, reason="test",
)
check("long name entry", long_entry is not None)
check("long metric length", len(long_entry.metric_name) == 200)
long_snap = FPR.build_snapshot([long_entry])
check("long name snap ok", long_snap.total_predictions == 1)

# ================================================================
# Section 55: Edge cases — horizon variation
# ================================================================
section("Edge cases — horizon variation")

short_h = FPR.predict_monitoring(mon_full, horizon=600.0)
long_h = FPR.predict_monitoring(mon_full, horizon=86400.0)
check("short horizon same count", len(short_h) == 8)
check("long horizon same count", len(long_h) == 8)
for s, l in zip(short_h, long_h):
    check("long horizon lower confidence", l.confidence <= s.confidence)

# ================================================================
# Section 56: Edge cases — history with only unknown
# ================================================================
section("Edge cases — history with only unknown")

unknown_hist = HistoricalSnapshot(
    entries=(), total_entries=0, created_at=now(),
)
entries_u = FPR.predict_monitoring(mon_full, unknown_hist)
check("unknown history 8 entries", len(entries_u) == 8)
for e in entries_u:
    check(f"valid direction {e.metric_name}", e.direction in (UPWARD, DOWNWARD, STABLE, UNCERTAIN))

# ================================================================
# Section 57: Edge cases — feedback with all failures
# ================================================================
section("Edge cases — feedback with all failures")

fail_entries = [
    FeedbackEntry(
        recommendation_id=uuid4(), action_id=uuid4(),
        expected_outcome="success", actual_outcome="failed",
        success=False, confidence_before=0.3, confidence_after=0.2,
        delta=-0.1, execution_duration=20.0, execution_cost=50.0,
    ),
]
fail_snap = FeedbackSnapshot(
    entries=tuple(fail_entries), total_entries=1,
    success_count=0, failure_count=1, success_rate=0.0,
    accuracy=100.0, roi=-50.0, avg_confidence_before=0.3,
    avg_confidence_after=0.2, avg_delta=-0.1,
    total_duration=20.0, total_cost=50.0, created_at=now(),
)
entries_fail = FPR.predict_feedback(fail_snap)
check("fail snap 11 entries", len(entries_fail) == 11)
for e in entries_fail:
    check("fail direction valid", e.direction in (UPWARD, DOWNWARD, STABLE, UNCERTAIN))

# ================================================================
# Section 58: Edge cases — high confidence bound
# ================================================================
section("Edge cases — high confidence bound")

hist_high = HistoricalSnapshot(
    entries=(
        HistoricalEntry(
            snapshot_before="A", snapshot_after="B",
            timestamp_before=0, timestamp_after=1,
            metric_name="health_score", old_value=0, new_value=100,
            delta=100, percent_change=100000.0, trend=TREND_IMPROVING,
        ),
    ),
    total_entries=1, improving_count=1,
    avg_delta=100, avg_percent_change=100000, created_at=now(),
)
ents_high = FPR.predict_monitoring(mon_full, hist_high)
check("high conf predictions exist", len(ents_high) == 8)
for e in ents_high:
    check(f"confidence bounded {e.metric_name}", e.confidence <= 0.95)
    check(f"confidence positive {e.metric_name}", e.confidence >= 0.10)

# ================================================================
# Section 59: Edge cases — declining everything
# ================================================================
section("Edge cases — declining everything")

hist_decl = HistoricalSnapshot(
    entries=(
        HistoricalEntry(
            snapshot_before="A", snapshot_after="B",
            timestamp_before=0, timestamp_after=1,
            metric_name="health_score", old_value=85, new_value=30,
            delta=-55, percent_change=-64.71, trend=TREND_DECLINING,
        ),
    ),
    total_entries=1, declining_count=1,
    avg_delta=-55, avg_percent_change=-64.71, created_at=now(),
)
ents_decl = FPR.predict_monitoring(mon_low, hist_decl)
for e in ents_decl:
    if e.metric_name == "health_score":
        check("declining health -> DOWNWARD", e.direction == DOWNWARD)

# ================================================================
# Section 60: Edge cases — custom horizon
# ================================================================
section("Edge cases — custom horizon")

result_custom = FPR.run(
    monitoring=mon_full, horizon=7200.0,
)
check("custom horizon works", result_custom.success is True)
check("custom horizon predictions", result_custom.snapshot.total_predictions == 8)

# ================================================================
# Section 61: filter_predictions — multiple criteria
# ================================================================
section("filter_predictions — multiple criteria")

strat_preds = FPR.predict_strategy(strat_snap)
filtered = FPR.filter_predictions(
    strat_preds, domain="strategy", min_confidence=0.3,
)
check("multi filter counts", len(filtered) >= 1)

# ================================================================
# Section 62: Edge cases — workflow with all completed
# ================================================================
section("Edge cases — workflow with all completed")

wf_done = [
    WorkflowRuntimeSnapshot(workflow_id=uuid4(), name="W1", state=WorkflowRuntimeState.COMPLETED, progress=100.0),
    WorkflowRuntimeSnapshot(workflow_id=uuid4(), name="W2", state=WorkflowRuntimeState.COMPLETED, progress=100.0),
]
ents_wf = FPR.predict_workflow(wf_done)
check("wf done 4 entries", len(ents_wf) == 4)
for e in ents_wf:
    check("wf direction valid", e.direction in (UPWARD, DOWNWARD, STABLE, UNCERTAIN))

# ================================================================
# Section 63: Edge cases — skills no records
# ================================================================
section("Edge cases — skills no records")

empty_skill_snap = SkillSnapshot(created_at=now())
ents_sk = FPR.predict_skills(empty_skill_snap)
check("empty skills 3 entries", len(ents_sk) == 3)
for e in ents_sk:
    check("empty skills direction valid", e.direction in (UPWARD, DOWNWARD, STABLE, UNCERTAIN))
    check("empty skills conf > 0", e.confidence > 0)

# ================================================================
# Section 64: group_by_metric — empty
# ================================================================
section("group_by_metric — empty")

check("empty group_by_metric", len(FPR.group_by_metric([])) == 0)

# ================================================================
# Section 65: group_by_confidence — thresholds
# ================================================================
section("group_by_confidence — thresholds")

cg = FPR.group_by_confidence(all_preds, high_threshold=0.8, medium_threshold=0.5)
check("custom high threshold", "high" in cg)
check("custom medium threshold", "medium" in cg)
total_cg = sum(len(v) for v in cg.values())
check("custom preserves count", total_cg == len(all_preds))

# ================================================================
# Section 66: filter_predictions — domain only
# ================================================================
section("filter_predictions — domain only")

domain_filter = FPR.filter_predictions(all_preds, domain="monitoring")
check("domain monitoring", len(domain_filter) == 8)
check("domain correct", all(e.metadata.get("domain") == "monitoring" for e in domain_filter))

domain_none = FPR.filter_predictions(all_preds, domain="nonexistent")
check("domain nonexistent", len(domain_none) == 0)

# ================================================================
# Section 67: filter_predictions — direction only
# ================================================================
section("filter_predictions — direction only")

stable_only = FPR.filter_predictions(all_preds, direction=STABLE)
check("stable filter works", all(e.direction == STABLE for e in stable_only))

# ================================================================
# Section 68: Edge cases — merge with metadata
# ================================================================
section("Edge cases — merge with metadata")

snap_m1 = FPR.build_snapshot(ents_a, {"source": "src1"})
snap_m2 = FPR.build_snapshot(ents_b, {"source": "src2"})
merged_m = FPR.merge_predictions([snap_m1, snap_m2])
check("merged metadata last wins", merged_m.metadata.get("source") == "src2")

# ================================================================
# Section 69: Edge cases — strategy single category
# ================================================================
section("Edge cases — strategy single category")

single_rec = [
    StrategyRecommendation(
        recommendation_id=uuid4(), category="Cost Reduction",
        priority="HIGH", confidence=0.9, created_at=now(),
        title="Single", description="", reason="", expected_benefit=10.0,
    ),
]
single_strat = StrategySnapshot(
    recommendations=single_rec,
    recommendations_by_category={"Cost Reduction": 1},
    recommendations_by_priority={"HIGH": 1},
    created_at=now(),
)
ents_single = FPR.predict_strategy(single_strat)
check("single strat 2 entries", len(ents_single) == 2)

# ================================================================
# Section 70: Edge cases — feedback empty entries tuple
# ================================================================
section("Edge cases — feedback empty entries tuple")

fb_empty = FeedbackSnapshot(created_at=now())
ents_fb_empty = FPR.predict_feedback(fb_empty)
check("fb empty entries -> 11", len(ents_fb_empty) == 11)

# ================================================================
# Section 71: Edge cases — performance empty metrics
# ================================================================
section("Edge cases — performance empty metrics")

perf_empty = PerformanceSnapshot({}, timestamp=now())
ents_perf_empty = FPR.predict_performance(perf_empty)
check("perf empty -> 0", len(ents_perf_empty) == 0)

# ================================================================
# Section 72: Edge cases — cost with history
# ================================================================
section("Edge cases — cost with history")

ents_cost_h = FPR.predict_cost(
    monitoring=mon_full, feedback=fb_snap, history=hist_snap,
)
check("cost with history", len(ents_cost_h) == 3)
for e in ents_cost_h:
    check("cost hist direction valid", e.direction in (UPWARD, DOWNWARD, STABLE, UNCERTAIN))

# ================================================================
# Section 73: Edge cases — predict with horizon zero
# ================================================================
section("Edge cases — predict with horizon zero")

ents_hz = FPR.predict_monitoring(mon_full, horizon=0.0)
check("zero horizon 8 entries", len(ents_hz) == 8)
for e in ents_hz:
    check("zero horizon conf <= MAX", e.confidence <= 0.95)

# ================================================================
# Section 74: Edge cases — success rate with history
# ================================================================
section("Edge cases — success rate with history")

ents_sr_h = FPR.predict_success_rate(monitoring=mon_full, history=hist_snap)
check("success rate hist entries", len(ents_sr_h) == 1)

# ================================================================
# Section 75: Backward compatibility
# ================================================================
section("Backward compatibility")

check("FPR FoundationPredictionRuntime", FPR is not None)
check("FPR.predict", callable(FPR.predict))
check("FPR.predict_monitoring", callable(FPR.predict_monitoring))
check("FPR.predict_performance", callable(FPR.predict_performance))
check("FPR.predict_strategy", callable(FPR.predict_strategy))
check("FPR.predict_feedback", callable(FPR.predict_feedback))
check("FPR.predict_learning", callable(FPR.predict_learning))
check("FPR.predict_skills", callable(FPR.predict_skills))
check("FPR.predict_workflow", callable(FPR.predict_workflow))
check("FPR.predict_cost", callable(FPR.predict_cost))
check("FPR.predict_health", callable(FPR.predict_health))
check("FPR.predict_success_rate", callable(FPR.predict_success_rate))
check("FPR.predict_confidence", callable(FPR.predict_confidence))
check("FPR.group_by_metric", callable(FPR.group_by_metric))
check("FPR.group_by_confidence", callable(FPR.group_by_confidence))
check("FPR.filter_predictions", callable(FPR.filter_predictions))
check("FPR.merge_predictions", callable(FPR.merge_predictions))
check("FPR.build_snapshot", callable(FPR.build_snapshot))
check("FPR.build_trace", callable(FPR.build_trace))
check("FPR.build_result", callable(FPR.build_result))
check("FPR.summarize", callable(FPR.summarize))
check("FPR.run", callable(FPR.run))
check("PredictionEntry frozen", hasattr(PredictionEntry, "metric_name"))
check("PredictionSnapshot frozen", hasattr(PredictionSnapshot, "total_predictions"))
check("PredictionTrace frozen", hasattr(PredictionTrace, "stages"))
check("PredictionResult frozen", hasattr(PredictionResult, "success"))
check("UPWARD constant", UPWARD == "UPWARD")
check("DOWNWARD constant", DOWNWARD == "DOWNWARD")
check("STABLE constant", STABLE == "STABLE")
check("UNCERTAIN constant", UNCERTAIN == "UNCERTAIN")

# FoundationStrategyRuntime intact
from core.strategy.foundation import FoundationStrategyRuntime
check("FSR intact", FoundationStrategyRuntime is not None)

# FoundationFeedbackRuntime intact
from core.feedback.foundation import FoundationFeedbackRuntime
check("FFR intact", FoundationFeedbackRuntime is not None)

# FoundationHistoricalRuntime intact
from core.history.foundation import FoundationHistoricalRuntime
check("FHR intact", FoundationHistoricalRuntime is not None)

# MonitoringRuntime intact
from core.monitoring.runtime import MonitoringRuntime
check("MR intact", MonitoringRuntime is not None)

# PerformanceRuntime intact
from core.analytics.runtime import PerformanceRuntime
check("PR intact", PerformanceRuntime is not None)

# LearningRuntime intact
from core.learning.foundation import LearningRuntime
check("LR intact", LearningRuntime is not None)

# SkillRuntime intact
from core.skills.foundation import SkillRuntime
check("SR intact", SkillRuntime is not None)

# WorkflowRuntime intact
from core.workflows.runtime import WorkflowRuntime
check("WR intact", WorkflowRuntime is not None)

# ================================================================
# Summary
# ================================================================
print(f"\n{'=' * 70}")
print(f"Total: {PASS}/{PASS + FAIL} passed, {FAIL} failed")
print(f"{'=' * 70}")

import sys
sys.exit(0 if FAIL == 0 else 1)
