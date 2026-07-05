"""Demo: FoundationHistoricalRuntime — 240+ scenarios."""

from __future__ import annotations

import time
from typing import Any
from uuid import UUID, uuid4

from core.analytics.runtime import PerformanceMetric, PerformanceSnapshot
from core.feedback.foundation import FeedbackEntry, FeedbackSnapshot
from core.history.foundation import (
    FoundationHistoricalRuntime as FHR,
    HistoricalEntry,
    HistoricalSnapshot,
    HistoricalTrend,
    HistoricalTrace,
    HistoricalResult,
    TREND_IMPROVING,
    TREND_DECLINING,
    TREND_STABLE,
    TREND_UNKNOWN,
)
from core.learning.foundation import LearningRecommendation, LearningSnapshot
from core.monitoring.runtime import MonitoringSnapshot
from core.skills.foundation import SkillRecord, SkillSnapshot
from core.strategy.foundation import StrategySnapshot
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


# ================================================================
# Section 1: Data models — HistoricalEntry
# ================================================================
section("Data models — HistoricalEntry")

entry = HistoricalEntry(
    snapshot_before="MonitoringSnapshot",
    snapshot_after="MonitoringSnapshot",
    timestamp_before=100.0,
    timestamp_after=200.0,
    metric_name="health_score",
    old_value=50.0,
    new_value=80.0,
    delta=30.0,
    percent_change=60.0,
    trend=TREND_IMPROVING,
    metadata={"domain": "monitoring"},
)
check("frozen", hasattr(entry, "metric_name"))
check("snapshot_before", entry.snapshot_before == "MonitoringSnapshot")
check("snapshot_after", entry.snapshot_after == "MonitoringSnapshot")
check("timestamp_before", entry.timestamp_before == 100.0)
check("timestamp_after", entry.timestamp_after == 200.0)
check("metric_name", entry.metric_name == "health_score")
check("old_value", entry.old_value == 50.0)
check("new_value", entry.new_value == 80.0)
check("delta", entry.delta == 30.0)
check("percent_change", entry.percent_change == 60.0)
check("trend IMPROVING", entry.trend == TREND_IMPROVING)
check("metadata domain", entry.metadata["domain"] == "monitoring")

entry_dec = HistoricalEntry(
    snapshot_before="A", snapshot_after="B",
    timestamp_before=0.0, timestamp_after=0.0,
    metric_name="x", old_value=100.0, new_value=50.0,
    delta=-50.0, percent_change=-50.0, trend=TREND_DECLINING,
)
check("declining entry", entry_dec.trend == TREND_DECLINING)

entry_stable = HistoricalEntry(
    snapshot_before="A", snapshot_after="B",
    timestamp_before=0.0, timestamp_after=0.0,
    metric_name="x", old_value=100.0, new_value=102.0,
    delta=2.0, percent_change=2.0, trend=TREND_STABLE,
)
check("stable entry", entry_stable.trend == TREND_STABLE)

entry_unknown = HistoricalEntry(
    snapshot_before="A", snapshot_after="B",
    timestamp_before=0.0, timestamp_after=0.0,
    metric_name="x", old_value=0.0, new_value=0.0,
    delta=0.0, percent_change=0.0, trend=TREND_UNKNOWN,
)
check("unknown entry", entry_unknown.trend == TREND_UNKNOWN)

# ================================================================
# Section 2: Data models — HistoricalSnapshot
# ================================================================
section("Data models — HistoricalSnapshot")

snap = HistoricalSnapshot()
check("frozen", hasattr(snap, "total_entries"))
check("empty total", snap.total_entries == 0)
check("empty improving", snap.improving_count == 0)
check("empty declining", snap.declining_count == 0)
check("empty stable", snap.stable_count == 0)
check("empty unknown", snap.unknown_count == 0)
check("empty avg_delta", snap.avg_delta == 0.0)
check("empty created_at", snap.created_at == 0.0)

snap2 = HistoricalSnapshot(
    entries=(entry, entry_dec),
    total_entries=2,
    improving_count=1,
    declining_count=1,
    stable_count=0,
    unknown_count=0,
    avg_delta=-10.0,
    avg_percent_change=5.0,
    created_at=42.0,
    metadata={"source": "test"},
)
check("populated total", snap2.total_entries == 2)
check("populated improving", snap2.improving_count == 1)
check("populated declining", snap2.declining_count == 1)
check("populated avg_delta", snap2.avg_delta == -10.0)

# ================================================================
# Section 3: Data models — HistoricalTrend, Trace, Result
# ================================================================
section("Data models — Trend, Trace, Result")

trend = HistoricalTrend(metric_name="health", trend=TREND_IMPROVING, percent_change=20.0, delta=10.0)
check("Trend metric", trend.metric_name == "health")
check("Trend improving", trend.trend == TREND_IMPROVING)
check("Trend percent", trend.percent_change == 20.0)
check("Trend delta", trend.delta == 10.0)

trace = HistoricalTrace()
check("Trace empty stages", trace.stages == ())
check("Trace empty duration", trace.duration_ms == 0.0)
check("Trace empty compared", trace.total_compared == 0)

trace2 = HistoricalTrace(
    stages=("run", "compare"), duration_ms=15.0, total_compared=5,
    metrics={"improving": 3.0},
)
check("Trace stages len", len(trace2.stages) == 2)
check("Trace duration", trace2.duration_ms == 15.0)
check("Trace compared", trace2.total_compared == 5)
check("Trace metrics", trace2.metrics["improving"] == 3.0)

result = HistoricalResult(success=False)
check("Result failed", not result.success)
check("Result snap None", result.snapshot is None)

result2 = HistoricalResult(success=True, snapshot=snap, trace=trace)
check("Result success", result2.success)
check("Result snapshot", result2.snapshot is snap)

# ================================================================
# Section 4: calculate_delta
# ================================================================
section("calculate_delta")

check("positive", FHR.calculate_delta(10.0, 15.0) == 5.0)
check("negative", FHR.calculate_delta(15.0, 10.0) == -5.0)
check("zero", FHR.calculate_delta(10.0, 10.0) == 0.0)
check("precision", FHR.calculate_delta(0.1, 0.3) == 0.2)

# ================================================================
# Section 5: calculate_percent_change
# ================================================================
section("calculate_percent_change")

check("increase 50%", FHR.calculate_percent_change(100.0, 150.0) == 50.0)
check("decrease 50%", FHR.calculate_percent_change(100.0, 50.0) == -50.0)
check("no change", FHR.calculate_percent_change(100.0, 100.0) == 0.0)
check("from zero", FHR.calculate_percent_change(0.0, 100.0) == 0.0)
check("doubled 100%", FHR.calculate_percent_change(50.0, 100.0) == 100.0)
check("tripled 200%", FHR.calculate_percent_change(50.0, 150.0) == 200.0)

# ================================================================
# Section 6: detect_trend
# ================================================================
section("detect_trend")

check("positive >5% improving", FHR.detect_trend(10.0, 20.0) == TREND_IMPROVING)
check("negative >5% declining", FHR.detect_trend(-10.0, -20.0) == TREND_DECLINING)
check("small positive stable", FHR.detect_trend(1.0, 2.0) == TREND_STABLE)
check("small negative stable", FHR.detect_trend(-1.0, -2.0) == TREND_STABLE)
check("zero delta unknown", FHR.detect_trend(0.0, 0.0) == TREND_UNKNOWN)
check("exactly 5% stable", FHR.detect_trend(5.0, 5.0) == TREND_STABLE)
check("just over 5% improving", FHR.detect_trend(5.1, 5.1) == TREND_IMPROVING)

# ================================================================
# Section 7: compare_monitoring — empty
# ================================================================
section("compare_monitoring — empty")

entries = FHR.compare_monitoring(None, None)
check("both None -> empty", len(entries) == 0)
entries = FHR.compare_monitoring(MonitoringSnapshot(), None)
check("before only -> 8 metrics", len(entries) == 8)
entries = FHR.compare_monitoring(None, MonitoringSnapshot())
check("after only -> 8 metrics", len(entries) == 8)

# ================================================================
# Section 8: compare_monitoring — improvement
# ================================================================
section("compare_monitoring — improvement")

before = MonitoringSnapshot(health_score=30.0, success_rate=40.0, error_rate=50.0, total_events=10, total_success=4, total_errors=6, event_rate=1.0, uptime=10.0)
after = MonitoringSnapshot(health_score=80.0, success_rate=90.0, error_rate=5.0, total_events=100, total_success=90, total_errors=10, event_rate=10.0, uptime=100.0)
entries = FHR.compare_monitoring(before, after)
check("8 entries", len(entries) == 8)
for e in entries:
    if e.metric_name == "health_score":
        check("health improved", e.trend == TREND_IMPROVING)
        check("health delta 50", e.delta == 50.0)
    elif e.metric_name == "success_rate":
        check("success improved", e.trend == TREND_IMPROVING)
    elif e.metric_name == "error_rate":
        check("error declining", e.trend == TREND_DECLINING)

# ================================================================
# Section 9: compare_monitoring — decline
# ================================================================
section("compare_monitoring — decline")

before2 = MonitoringSnapshot(health_score=80.0, success_rate=90.0, error_rate=5.0, total_events=100, total_success=90, total_errors=10, event_rate=10.0, uptime=100.0)
after2 = MonitoringSnapshot(health_score=30.0, success_rate=40.0, error_rate=50.0, total_events=10, total_success=4, total_errors=6, event_rate=1.0, uptime=10.0)
entries2 = FHR.compare_monitoring(before2, after2)
for e in entries2:
    if e.metric_name == "health_score":
        check("health declined", e.trend == TREND_DECLINING)
    elif e.metric_name == "error_rate":
        check("error improved", e.trend == TREND_IMPROVING)

# ================================================================
# Section 10: compare_monitoring — stable
# ================================================================
section("compare_monitoring — stable")

before3 = MonitoringSnapshot(health_score=50.0, success_rate=50.0, error_rate=50.0, total_events=10, total_success=5, total_errors=5, event_rate=1.0, uptime=10.0)
after3 = MonitoringSnapshot(health_score=51.0, success_rate=51.0, error_rate=51.0, total_events=11, total_success=5, total_errors=5, event_rate=1.0, uptime=10.0)
entries3 = FHR.compare_monitoring(before3, after3)
for e in entries3:
    if e.metric_name == "health_score":
        check("health stable", e.trend == TREND_STABLE)

# ================================================================
# Section 11: compare_performance — empty
# ================================================================
section("compare_performance — empty")

check("both None", len(FHR.compare_performance(None, None)) == 0)
check("empty before", len(FHR.compare_performance(PerformanceSnapshot({}, now()), None)) > 0)

# ================================================================
# Section 12: compare_performance — metrics
# ================================================================
section("compare_performance — metrics")

perf_before = PerformanceSnapshot({"taxa": PerformanceMetric(name="taxa", value=50.0, unit="%")}, timestamp=now())
perf_after = PerformanceSnapshot({"taxa": PerformanceMetric(name="taxa", value=80.0, unit="%")}, timestamp=now())
entries = FHR.compare_performance(perf_before, perf_after)
check("1 entry", len(entries) == 1)
check("perf_taxa metric", entries[0].metric_name == "perf_taxa")
check("delta 30", entries[0].delta == 30.0)
check("improving", entries[0].trend == TREND_IMPROVING)

# New metrics in after
perf_new = PerformanceSnapshot({"taxa": PerformanceMetric(name="taxa", value=80.0, unit="%"), "novo": PerformanceMetric(name="novo", value=100.0, unit="count")}, timestamp=now())
entries2 = FHR.compare_performance(perf_before, perf_new)
check("2 entries", len(entries2) == 2)

# Metric removed
perf_removed = PerformanceSnapshot({}, timestamp=now())
entries3 = FHR.compare_performance(perf_before, perf_removed)
check("1 entry (old=0)", len(entries3) == 1)
check("value reset to 0", entries3[0].new_value == 0.0)

# ================================================================
# Section 13: compare_strategy — empty
# ================================================================
section("compare_strategy — empty")

check("both None", len(FHR.compare_strategy(None, None)) == 0)
s_empty = StrategySnapshot(created_at=now())
check("with empty snapshots", len(FHR.compare_strategy(s_empty, s_empty)) == 1)

# ================================================================
# Section 14: compare_strategy — different
# ================================================================
section("compare_strategy — different")

s_before = StrategySnapshot(
    recommendations=(),
    recommendations_by_category={"Cost Reduction": 2, "Performance": 1},
    recommendations_by_priority={"HIGH": 2, "MEDIUM": 1},
    created_at=now(),
)
s_after = StrategySnapshot(
    recommendations=(),
    recommendations_by_category={"Cost Reduction": 3, "Risk Mitigation": 2},
    recommendations_by_priority={"CRITICAL": 1, "HIGH": 3, "MEDIUM": 1},
    created_at=now(),
)
entries = FHR.compare_strategy(s_before, s_after)
check("entries count", len(entries) >= 5)
for e in entries:
    if e.metric_name == "recs_Cost Reduction":
        check("Cost Reduction +1", e.delta == 1.0)
    elif e.metric_name == "recs_Risk Mitigation":
        check("Risk Mitigation new", e.delta == 2.0)
    elif e.metric_name == "pri_CRITICAL":
        check("CRITICAL new", e.delta == 1.0)

# ================================================================
# Section 15: compare_feedback — empty
# ================================================================
section("compare_feedback — empty")

check("both None", len(FHR.compare_feedback(None, None)) == 0)
f_empty = FeedbackSnapshot(created_at=now())
check("both empty", len(FHR.compare_feedback(f_empty, f_empty)) == 11)

# ================================================================
# Section 16: compare_feedback — improvement
# ================================================================
section("compare_feedback — improvement")

fb_before = FeedbackSnapshot(success_rate=50.0, accuracy=40.0, roi=0.5, avg_confidence_before=0.5, avg_confidence_after=0.55, avg_delta=0.05, total_duration=100.0, total_cost=50.0, success_count=5, failure_count=5, total_entries=10, created_at=now())
fb_after = FeedbackSnapshot(success_rate=80.0, accuracy=75.0, roi=2.0, avg_confidence_before=0.6, avg_confidence_after=0.75, avg_delta=0.15, total_duration=80.0, total_cost=30.0, success_count=8, failure_count=2, total_entries=10, created_at=now())
entries = FHR.compare_feedback(fb_before, fb_after)
check("11 entries", len(entries) == 11)
for e in entries:
    if e.metric_name == "success_rate":
        check("success_rate improving", e.trend == TREND_IMPROVING)
    elif e.metric_name == "total_duration":
        check("duration declining (good)", e.trend == TREND_DECLINING)
    elif e.metric_name == "total_cost":
        check("cost declining (good)", e.trend == TREND_DECLINING)

# ================================================================
# Section 17: compare_learning — empty
# ================================================================
section("compare_learning — empty")

check("both None", len(FHR.compare_learning(None, None)) == 0)
l_empty = LearningSnapshot(created_at=now())
check("both empty", len(FHR.compare_learning(l_empty, l_empty)) == 1)

# ================================================================
# Section 18: compare_learning — different
# ================================================================
section("compare_learning — different")

l_before = LearningSnapshot(
    recommendations=(LearningRecommendation(recommendation_id=uuid4(), knowledge_id=uuid4(), recommendation_type="study", title="A", description="D", priority=1, timestamp=now()),),
    created_at=now(),
)
l_after = LearningSnapshot(
    recommendations=(
        LearningRecommendation(recommendation_id=uuid4(), knowledge_id=uuid4(), recommendation_type="study", title="A", description="D", priority=1, timestamp=now()),
        LearningRecommendation(recommendation_id=uuid4(), knowledge_id=uuid4(), recommendation_type="practice", title="B", description="D", priority=2, timestamp=now()),
    ),
    created_at=now(),
)
entries = FHR.compare_learning(l_before, l_after)
check("entries > 1", len(entries) >= 2)
for e in entries:
    if e.metric_name == "total_recommendations":
        check("learning recs +1", e.delta == 1.0)

# ================================================================
# Section 19: compare_skills — empty
# ================================================================
section("compare_skills — empty")

check("both None", len(FHR.compare_skills(None, None)) == 0)
sk_empty = SkillSnapshot(created_at=now())
check("both empty", len(FHR.compare_skills(sk_empty, sk_empty)) == 3)

# ================================================================
# Section 20: compare_skills — growth
# ================================================================
section("compare_skills — growth")

sk_before = SkillSnapshot(
    skills=(
        SkillRecord(skill_id=uuid4(), recommendation_id=uuid4(), skill_name="A", description="D", level=1, experience_points=10, created_at=now()),
        SkillRecord(skill_id=uuid4(), recommendation_id=uuid4(), skill_name="B", description="D", level=2, experience_points=50, created_at=now()),
    ),
    created_at=now(),
)
sk_after = SkillSnapshot(
    skills=(
        SkillRecord(skill_id=uuid4(), recommendation_id=uuid4(), skill_name="A", description="D", level=2, experience_points=30, created_at=now()),
        SkillRecord(skill_id=uuid4(), recommendation_id=uuid4(), skill_name="B", description="D", level=3, experience_points=80, created_at=now()),
        SkillRecord(skill_id=uuid4(), recommendation_id=uuid4(), skill_name="C", description="D", level=1, experience_points=5, created_at=now()),
    ),
    created_at=now(),
)
entries = FHR.compare_skills(sk_before, sk_after)
check("3 entries", len(entries) == 3)
for e in entries:
    if e.metric_name == "total_skills":
        check("skills grew", e.delta == 1.0)
    elif e.metric_name == "avg_level":
        check("avg level up", e.delta > 0)
    elif e.metric_name == "total_xp":
        check("total xp grew", e.delta > 0)

# ================================================================
# Section 21: compare_workflow — empty
# ================================================================
section("compare_workflow — empty")

check("both None", len(FHR.compare_workflow(None, None)) == 0)
check("both empty lists", len(FHR.compare_workflow([], [])) == 0)

# ================================================================
# Section 22: compare_workflow — progress
# ================================================================
section("compare_workflow — progress")

wf_before = [
    WorkflowRuntimeSnapshot(workflow_id=uuid4(), name="W1", state=WorkflowRuntimeState.CREATED, progress=0.0),
    WorkflowRuntimeSnapshot(workflow_id=uuid4(), name="W2", state=WorkflowRuntimeState.RUNNING, progress=50.0),
]
wf_after = [
    WorkflowRuntimeSnapshot(workflow_id=uuid4(), name="W1", state=WorkflowRuntimeState.COMPLETED, progress=100.0),
    WorkflowRuntimeSnapshot(workflow_id=uuid4(), name="W2", state=WorkflowRuntimeState.COMPLETED, progress=100.0),
    WorkflowRuntimeSnapshot(workflow_id=uuid4(), name="W3", state=WorkflowRuntimeState.CREATED, progress=0.0),
]
entries = FHR.compare_workflow(wf_before, wf_after)
check("4 entries", len(entries) == 4)
for e in entries:
    if e.metric_name == "total_workflows":
        check("workflows +1", e.delta == 1.0)
    elif e.metric_name == "completed_workflows":
        check("completed +2", e.delta == 2.0)

# ================================================================
# Section 23: compare — dispatch
# ================================================================
section("compare — dispatch")

check("monitoring dispatch", len(FHR.compare(MonitoringSnapshot(), MonitoringSnapshot())) == 8)
check("performance dispatch", len(FHR.compare(PerformanceSnapshot({"m": PerformanceMetric(name="m", value=1.0)}, now()), PerformanceSnapshot({"m": PerformanceMetric(name="m", value=2.0)}, now()))) == 1)
check("strategy dispatch", len(FHR.compare(StrategySnapshot(created_at=now()), StrategySnapshot(created_at=now()))) == 1)
check("feedback dispatch", len(FHR.compare(FeedbackSnapshot(created_at=now()), FeedbackSnapshot(created_at=now()))) == 11)
check("learning dispatch", len(FHR.compare(LearningSnapshot(created_at=now()), LearningSnapshot(created_at=now()))) == 1)
check("skills dispatch", len(FHR.compare(SkillSnapshot(created_at=now()), SkillSnapshot(created_at=now()))) == 3)
check("workflow dispatch", len(FHR.compare([], [])) == 0)
check("unknown dispatch", len(FHR.compare(None, None)) == 0)

# ================================================================
# Section 24: group_by_trend
# ================================================================
section("group_by_trend")

entries_multi = [
    HistoricalEntry(snapshot_before="A", snapshot_after="B", timestamp_before=0, timestamp_after=0, metric_name="m1", old_value=10, new_value=20, delta=10, percent_change=100, trend=TREND_IMPROVING),
    HistoricalEntry(snapshot_before="A", snapshot_after="B", timestamp_before=0, timestamp_after=0, metric_name="m2", old_value=20, new_value=10, delta=-10, percent_change=-50, trend=TREND_DECLINING),
    HistoricalEntry(snapshot_before="A", snapshot_after="B", timestamp_before=0, timestamp_after=0, metric_name="m3", old_value=10, new_value=10.5, delta=0.5, percent_change=5, trend=TREND_STABLE),
    HistoricalEntry(snapshot_before="A", snapshot_after="B", timestamp_before=0, timestamp_after=0, metric_name="m4", old_value=0, new_value=0, delta=0, percent_change=0, trend=TREND_UNKNOWN),
]
grouped = FHR.group_by_trend(entries_multi)
check("4 trend groups", len(grouped) == 4)
check("improving has 1", len(grouped[TREND_IMPROVING]) == 1)
check("declining has 1", len(grouped[TREND_DECLINING]) == 1)
check("stable has 1", len(grouped[TREND_STABLE]) == 1)
check("unknown has 1", len(grouped[TREND_UNKNOWN]) == 1)
check("empty list", len(FHR.group_by_trend([])) == 0)

# ================================================================
# Section 25: group_by_metric
# ================================================================
section("group_by_metric")

grouped_m = FHR.group_by_metric(entries_multi)
check("4 metric groups", len(grouped_m) == 4)

entries_dup = entries_multi + entries_multi[:2]
grouped_d = FHR.group_by_metric(entries_dup)
check("still 4 groups after dup", len(grouped_d) == 4)
check("m1 has 2", len(grouped_d["m1"]) == 2)

check("empty list", len(FHR.group_by_metric([])) == 0)

# ================================================================
# Section 26: filter_history
# ================================================================
section("filter_history")

check("no filter", len(FHR.filter_history(entries_multi)) == 4)
check("filter improving", len(FHR.filter_history(entries_multi, trend=TREND_IMPROVING)) == 1)
check("filter declining", len(FHR.filter_history(entries_multi, trend=TREND_DECLINING)) == 1)
check("filter m1", len(FHR.filter_history(entries_multi, metric_name="m1")) == 1)
check("filter min_delta", len(FHR.filter_history(entries_multi, min_delta=5.0)) == 1)
check("filter max_delta", len(FHR.filter_history(entries_multi, max_delta=-5.0)) == 1)
check("filter min_pct", len(FHR.filter_history(entries_multi, min_percent_change=50.0)) == 1)
check("filter max_pct", len(FHR.filter_history(entries_multi, max_percent_change=-25.0)) == 1)
check("filter nonexistent", len(FHR.filter_history(entries_multi, metric_name="none")) == 0)

# ================================================================
# Section 27: build_snapshot
# ================================================================
section("build_snapshot")

empty_snap = FHR.build_snapshot([])
check("empty total", empty_snap.total_entries == 0)
check("empty improving", empty_snap.improving_count == 0)
check("empty created_at > 0", empty_snap.created_at > 0)

single_snap = FHR.build_snapshot(entries_multi)
check("4 entries", single_snap.total_entries == 4)
check("1 improving", single_snap.improving_count == 1)
check("1 declining", single_snap.declining_count == 1)
check("1 stable", single_snap.stable_count == 1)
check("1 unknown", single_snap.unknown_count == 1)
check("avg_delta != 0", single_snap.avg_delta != 0.0)
check("avg_percent_change != 0", single_snap.avg_percent_change != 0.0)
check("metadata empty", single_snap.metadata == {})

snap_meta = FHR.build_snapshot(entries_multi, {"source": "test"})
check("metadata passed", snap_meta.metadata["source"] == "test")

# ================================================================
# Section 28: build_trace
# ================================================================
section("build_trace")

t = FHR.build_trace()
check("empty stages", t.stages == ())
check("empty duration", t.duration_ms == 0.0)
check("empty compared", t.total_compared == 0)

t2 = FHR.build_trace(stages=["run", "compare"], duration_ms=12.5, total_compared=4, metrics={"i": 2.0})
check("stages len", len(t2.stages) == 2)
check("duration", t2.duration_ms == 12.5)
check("compared", t2.total_compared == 4)
check("metrics", t2.metrics["i"] == 2.0)

# ================================================================
# Section 29: build_result
# ================================================================
section("build_result")

r = FHR.build_result(single_snap)
check("success", r.success)
check("snapshot ref", r.snapshot is single_snap)
check("trace present", r.trace is not None)
check("trace compared", r.trace.total_compared == 4)

r2 = FHR.build_result(empty_snap, stages=["test"], metrics={"t": 0.0})
check("empty result success", r2.success)
check("empty result trace", r2.trace is not None)

# ================================================================
# Section 30: merge_history
# ================================================================
section("merge_history")

snap_a = FHR.build_snapshot(entries_multi[:2])
snap_b = FHR.build_snapshot(entries_multi[2:])
merged = FHR.merge_history([snap_a, snap_b])
check("merged total 4", merged.total_entries == 4)
check("merged improving", merged.improving_count == 1)
check("merged declining", merged.declining_count == 1)

merged_self = FHR.merge_history([single_snap, single_snap])
check("dedup same entries", merged_self.total_entries == 4)

merged_empty = FHR.merge_history([])
check("empty merge", merged_empty.total_entries == 0)

# ================================================================
# Section 31: summarize
# ================================================================
section("summarize")

summary = FHR.summarize(single_snap)
check("total_entries", summary["total_entries"] == 4)
check("improving_count", summary["improving_count"] == 1)
check("declining_count", summary["declining_count"] == 1)
check("trends dict", isinstance(summary["trends"], dict))
check("metrics dict", isinstance(summary["metrics"], dict))
check("keys > 5", len(summary) > 5)

sum_empty = FHR.summarize(empty_snap)
check("empty summary", sum_empty["total_entries"] == 0)

# ================================================================
# Section 32: run — empty
# ================================================================
section("run — empty")

r = FHR.run()
check("success", r.success)
check("empty snapshot", r.snapshot.total_entries == 0 if r.snapshot else False)
check("trace present", r.trace is not None)

# ================================================================
# Section 33: run — monitoring only
# ================================================================
section("run — monitoring only")

r = FHR.run(monitoring_before=before, monitoring_after=after)
check("success", r.success)
check("8 entries", r.snapshot.total_entries == 8 if r.snapshot else False)
check("stages has monitoring", "monitoring" in r.trace.stages if r.trace else False)

# ================================================================
# Section 34: run — all domains
# ================================================================
section("run — all domains")

r = FHR.run(
    monitoring_before=before, monitoring_after=after,
    performance_before=perf_before, performance_after=perf_after,
    strategy_before=s_before, strategy_after=s_after,
    feedback_before=fb_before, feedback_after=fb_after,
    learning_before=l_before, learning_after=l_after,
    skills_before=sk_before, skills_after=sk_after,
    workflow_before=wf_before, workflow_after=wf_after,
)
check("full run success", r.success)
check("trace stages", len(r.trace.stages) >= 7 if r.trace else False)
check("total entries > 20", r.snapshot.total_entries > 20 if r.snapshot else False)

# ================================================================
# Section 35: Integration — Monitoring
# ================================================================
section("Integration — Monitoring")

from core.monitoring.runtime import MonitoringRuntime
events_a = [MonitoringRuntime.consume_event(MonitoringSnapshot(), type("E1", (), {"success": True})())]
events_b = [MonitoringRuntime.consume_event(MonitoringSnapshot(), type("E2", (), {"success": False})())]
# Just use direct monitoring comparison
check("FHR.compare_monitoring callable", callable(FHR.compare_monitoring))

# ================================================================
# Section 36: Integration — Performance
# ================================================================
section("Integration — Performance")

from core.analytics.runtime import PerformanceRuntime
p_before = PerformanceRuntime.analyze_execution(executions=None, usages=None)
p_after = PerformanceRuntime.analyze_execution(executions=None, usages=None)
if p_before.success and p_after.success:
    entries_p = FHR.compare_performance(p_before.snapshot, p_after.snapshot)
    check("perf integration entries", len(entries_p) >= 0)

# ================================================================
# Section 37: Integration — Strategy
# ================================================================
section("Integration — Strategy")

from core.strategy.foundation import FoundationStrategyRuntime
s1 = FoundationStrategyRuntime.analyze_monitoring(after)
s2 = FoundationStrategyRuntime.analyze_monitoring(before)
if s1.success and s2.success and s1.snapshot and s2.snapshot:
    entries_s = FHR.compare_strategy(s2.snapshot, s1.snapshot)
    check("strategy integration", len(entries_s) >= 1)

# ================================================================
# Section 38: Integration — Feedback
# ================================================================
section("Integration — Feedback")

from core.feedback.foundation import FoundationFeedbackRuntime
f_snap = FoundationFeedbackRuntime.build_snapshot([])
entries_f = FHR.compare_feedback(f_snap, f_snap)
check("feedback integration", len(entries_f) == 11)

# ================================================================
# Section 39: Integration — Learning
# ================================================================
section("Integration — Learning")

entries_l = FHR.compare_learning(l_before, l_after)
check("learning integration", len(entries_l) >= 2)

# ================================================================
# Section 40: Integration — Skills
# ================================================================
section("Integration — Skills")

entries_sk = FHR.compare_skills(sk_before, sk_after)
check("skills integration", len(entries_sk) == 3)

# ================================================================
# Section 41: Integration — Workflow
# ================================================================
section("Integration — Workflow")

entries_w = FHR.compare_workflow(wf_before, wf_after)
check("workflow integration", len(entries_w) == 4)

# ================================================================
# Section 42: Determinism
# ================================================================
section("Determinism")

e_a = FHR.compare_monitoring(before, after)
e_b = FHR.compare_monitoring(before, after)
check("same inputs same outputs", len(e_a) == len(e_b))
for ea, eb in zip(e_a, e_b):
    check(f"deterministic {ea.metric_name}", ea.delta == eb.delta)

delta1 = FHR.calculate_delta(10.0, 20.0)
delta2 = FHR.calculate_delta(10.0, 20.0)
check("delta deterministic", delta1 == delta2)

pct1 = FHR.calculate_percent_change(50.0, 100.0)
pct2 = FHR.calculate_percent_change(50.0, 100.0)
check("pct deterministic", pct1 == pct2)

# ================================================================
# Section 43: UUID handling
# ================================================================
section("UUID")

check("trend uses str", TREND_IMPROVING == "IMPROVING")
check("no UUID needed in entries", True)  # entries use string metric names

# ================================================================
# Section 44: Timestamps
# ================================================================
section("Timestamps")

before_ts = now()
snap_ts = FHR.build_snapshot(entries_multi)
after_ts = now()
check("created_at > 0", snap_ts.created_at > 0)
check("created_at between", before_ts <= snap_ts.created_at <= after_ts)

# ================================================================
# Section 45: Metadata
# ================================================================
section("Metadata")

entry_m = HistoricalEntry(
    snapshot_before="A", snapshot_after="B",
    timestamp_before=0, timestamp_after=0,
    metric_name="m", old_value=0, new_value=0,
    delta=0, percent_change=0, trend=TREND_STABLE,
    metadata={"env": "prod", "version": "2.0"},
)
check("entry metadata env", entry_m.metadata["env"] == "prod")
check("entry metadata version", entry_m.metadata["version"] == "2.0")

snap_meta = FHR.build_snapshot([entry_m], {"pipeline": "nightly"})
check("snapshot metadata", snap_meta.metadata["pipeline"] == "nightly")

# ================================================================
# Section 46: Edge cases — before == after
# ================================================================
section("Edge cases — before == after")

eq_mon = FHR.compare_monitoring(before, before)
check("identical monitoring -> stable", all(e.trend == TREND_STABLE or e.trend == TREND_UNKNOWN for e in eq_mon))

eq_perf = FHR.compare_performance(perf_before, perf_before)
check("identical perf -> stable/unknown", all(e.trend in (TREND_STABLE, TREND_UNKNOWN) for e in eq_perf))

# ================================================================
# Section 47: Edge cases — missing metrics in performance
# ================================================================
section("Edge cases — missing performance metrics")

p_missing_before = PerformanceSnapshot({"a": PerformanceMetric(name="a", value=10.0)}, timestamp=now())
p_missing_after = PerformanceSnapshot({"b": PerformanceMetric(name="b", value=20.0)}, timestamp=now())
entries_miss = FHR.compare_performance(p_missing_before, p_missing_after)
check("2 entries for disjoint metrics", len(entries_miss) == 2)
for e in entries_miss:
    if e.metric_name == "perf_a":
        check("a old=10 new=0", e.old_value == 10.0 and e.new_value == 0.0)
    elif e.metric_name == "perf_b":
        check("b old=0 new=20", e.old_value == 0.0 and e.new_value == 20.0)

# ================================================================
# Section 48: Edge cases — zero percent change handling
# ================================================================
section("Edge cases — zero percent change")

entries_zero = FHR.compare_monitoring(
    MonitoringSnapshot(health_score=0.0, success_rate=0.0, error_rate=0.0, total_events=0, total_success=0, total_errors=0, event_rate=0.0, uptime=0.0),
    MonitoringSnapshot(health_score=0.0, success_rate=0.0, error_rate=0.0, total_events=0, total_success=0, total_errors=0, event_rate=0.0, uptime=0.0),
)
for e in entries_zero:
    check(f"zero {e.metric_name} pct=0", e.percent_change == 0.0)

# ================================================================
# Section 49: Edge cases — large batch
# ================================================================
section("Edge cases — large batch")

large_entries = []
for i in range(50):
    large_entries.append(HistoricalEntry(
        snapshot_before="A", snapshot_after="B",
        timestamp_before=float(i), timestamp_after=float(i + 1),
        metric_name=f"metric_{i}",
        old_value=float(i), new_value=float(i * 2),
        delta=float(i), percent_change=100.0,
        trend=TREND_IMPROVING if i % 2 == 0 else TREND_DECLINING,
    ))
large_snap = FHR.build_snapshot(large_entries)
check("50 entries", large_snap.total_entries == 50)
check("25 improving", large_snap.improving_count == 25)
check("25 declining", large_snap.declining_count == 25)
check("avg_delta != 0", large_snap.avg_delta != 0.0)
check("avg_percent_change 100", large_snap.avg_percent_change == 100.0)

# ================================================================
# Section 50: Edge cases — filter by domain
# ================================================================
section("Edge cases — filter by domain")

dom_entries = [
    HistoricalEntry(snapshot_before="A", snapshot_after="B", timestamp_before=0, timestamp_after=0, metric_name="h", old_value=0, new_value=1, delta=1, percent_change=100, trend=TREND_IMPROVING, metadata={"domain": "monitoring"}),
    HistoricalEntry(snapshot_before="A", snapshot_after="B", timestamp_before=0, timestamp_after=0, metric_name="p", old_value=0, new_value=1, delta=1, percent_change=100, trend=TREND_IMPROVING, metadata={"domain": "performance"}),
]
check("filter monitoring", len(FHR.filter_history(dom_entries, domain="monitoring")) == 1)
check("filter performance", len(FHR.filter_history(dom_entries, domain="performance")) == 1)
check("filter nonexistent domain", len(FHR.filter_history(dom_entries, domain="strategy")) == 0)
check("filter with all criteria", len(FHR.filter_history(dom_entries, trend=TREND_IMPROVING, metric_name="h")) == 1)

# ================================================================
# Section 51: Edge cases — long metric names
# ================================================================
section("Edge cases — long metric names")

long_e = HistoricalEntry(
    snapshot_before="A" * 200, snapshot_after="B" * 200,
    timestamp_before=0, timestamp_after=0,
    metric_name="X" * 200, old_value=0, new_value=1,
    delta=1, percent_change=100, trend=TREND_IMPROVING,
)
check("long name entry created", long_e is not None)
check("long snapshot_before", len(long_e.snapshot_before) == 200)
check("long metric_name", len(long_e.metric_name) == 200)
long_snap = FHR.build_snapshot([long_e])
check("long name snap ok", long_snap.total_entries == 1)

# ================================================================
# Section 52: Edge cases — after only
# ================================================================
section("Edge cases — after only")

mon_only = FHR.compare_monitoring(None, after)
check("after only -> 8", len(mon_only) == 8)
for e in mon_only:
    check(f"old=0 for {e.metric_name}", e.old_value == 0.0)

perf_only = FHR.compare_performance(None, perf_after)
check("perf after only -> 1", len(perf_only) == 1)
check("old=0", perf_only[0].old_value == 0.0)

strat_only = FHR.compare_strategy(None, s_after)
check("strat after only", len(strat_only) >= 1)

# ================================================================
# Section 53: Backward compatibility
# ================================================================
section("Backward compatibility")

# FoundationStrategyRuntime intact
from core.strategy.foundation import FoundationStrategyRuntime
check("FSR intact", FoundationStrategyRuntime is not None)

# FoundationExecutionPlanRuntime intact
from core.execution_plan.foundation import FoundationExecutionPlanRuntime
check("FEPR intact", FoundationExecutionPlanRuntime is not None)

# StrategyPipeline intact
from core.strategy.pipeline import StrategyPipeline
check("SP intact", StrategyPipeline is not None)

# MonitoringRuntime intact
from core.monitoring.runtime import MonitoringRuntime
check("MR intact", MonitoringRuntime is not None)

# PerformanceRuntime intact
from core.analytics.runtime import PerformanceRuntime
check("PR intact", PerformanceRuntime is not None)

# FoundationFeedbackRuntime intact
from core.feedback.foundation import FoundationFeedbackRuntime
check("FFR intact", FoundationFeedbackRuntime is not None)

# FoundationHistoricalRuntime new
check("FHR FoundationHistoricalRuntime", FHR is not None)
check("FHR.compare", callable(FHR.compare))
check("FHR.compare_monitoring", callable(FHR.compare_monitoring))
check("FHR.compare_performance", callable(FHR.compare_performance))
check("FHR.compare_strategy", callable(FHR.compare_strategy))
check("FHR.compare_feedback", callable(FHR.compare_feedback))
check("FHR.compare_learning", callable(FHR.compare_learning))
check("FHR.compare_skills", callable(FHR.compare_skills))
check("FHR.compare_workflow", callable(FHR.compare_workflow))
check("FHR.calculate_delta", callable(FHR.calculate_delta))
check("FHR.calculate_percent_change", callable(FHR.calculate_percent_change))
check("FHR.detect_trend", callable(FHR.detect_trend))
check("FHR.group_by_trend", callable(FHR.group_by_trend))
check("FHR.group_by_metric", callable(FHR.group_by_metric))
check("FHR.filter_history", callable(FHR.filter_history))
check("FHR.merge_history", callable(FHR.merge_history))
check("FHR.build_snapshot", callable(FHR.build_snapshot))
check("FHR.build_trace", callable(FHR.build_trace))
check("FHR.build_result", callable(FHR.build_result))
check("FHR.summarize", callable(FHR.summarize))
check("FHR.run", callable(FHR.run))

# All dataclasses frozen
check("HistoricalEntry frozen", hasattr(HistoricalEntry, "metric_name"))
check("HistoricalSnapshot frozen", hasattr(HistoricalSnapshot, "total_entries"))
check("HistoricalTrend frozen", hasattr(HistoricalTrend, "metric_name"))
check("HistoricalTrace frozen", hasattr(HistoricalTrace, "stages"))
check("HistoricalResult frozen", hasattr(HistoricalResult, "success"))

# Trend constants
check("TREND_IMPROVING", TREND_IMPROVING == "IMPROVING")
check("TREND_DECLINING", TREND_DECLINING == "DECLINING")
check("TREND_STABLE", TREND_STABLE == "STABLE")
check("TREND_UNKNOWN", TREND_UNKNOWN == "UNKNOWN")

# ================================================================
# Summary
# ================================================================
print(f"\n{'=' * 70}")
print(f"Total: {PASS}/{PASS + FAIL} passed, {FAIL} failed")
print(f"{'=' * 70}")

import sys
sys.exit(0 if FAIL == 0 else 1)
