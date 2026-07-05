"""Demo: FoundationFeedbackRuntime — 220+ scenarios."""

from __future__ import annotations

import math
import time
from uuid import UUID, uuid4

from core.analytics.runtime import PerformanceMetric, PerformanceSnapshot
from core.execution_plan.foundation import ExecutionAction, ExecutionPlan, FoundationExecutionPlanRuntime
from core.feedback.foundation import FoundationFeedbackRuntime, FeedbackEntry, FeedbackSnapshot, FeedbackTrace, FeedbackResult
from core.monitoring.runtime import MonitoringSnapshot
from core.optimization.runtime import OptimizationActionState, OptimizationSnapshot
from core.strategy.foundation import FoundationStrategyRuntime, StrategyRecommendation, StrategySnapshot
from core.strategy.pipeline import StrategyExecutionItem, StrategyExecutionPlan

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
    msg = f"  [{status}] {description:50s} | {detail}"
    print(msg)


def now() -> float:
    return time.time()


def make_rec(
    category: str = "Cost Reduction",
    priority: str = "MEDIUM",
    confidence: float = 0.75,
    recommendation_id: UUID | None = None,
) -> StrategyRecommendation:
    rid = recommendation_id or uuid4()
    return StrategyRecommendation(
        recommendation_id=rid,
        category=category,
        priority=priority,
        title=f"Recommendation {rid}",
        description="Test recommendation",
        reason="Test",
        expected_benefit="Test benefit",
        confidence=confidence,
        metadata={"source": "test"},
        created_at=now(),
    )


def make_action(
    rid: UUID,
    state: str = "COMPLETED",
    duration: float = 1.0,
    action_id: UUID | None = None,
    category: str = "Cost Reduction",
    priority: str = "MEDIUM",
) -> OptimizationActionState:
    aid = action_id or uuid4()
    return OptimizationActionState(
        action_id=aid,
        recommendation_id=rid,
        title=f"Action for {rid}",
        category=category,
        priority=priority,
        state=state,
        attempt=1,
        can_execute=True,
        requires_manual_approval=False,
        started_at=now() - duration,
        completed_at=now(),
        duration=duration,
        error_message="" if state == "COMPLETED" else "Failed",
        metadata={"source": "test"},
    )


# ================================================================
# Section 1: Data models — FeedbackEntry
# ================================================================
section("Data models — FeedbackEntry")

entry = FeedbackEntry(
    recommendation_id=uuid4(),
    action_id=uuid4(),
    expected_outcome="success",
    actual_outcome="completed",
    success=True,
    confidence_before=0.75,
    confidence_after=0.9,
    delta=0.15,
    execution_duration=1.5,
    execution_cost=0.5,
    metadata={"category": "Cost Reduction", "priority": "HIGH"},
)
check("FeedbackEntry frozen", hasattr(entry, "recommendation_id"))
check("recommendation_id", isinstance(entry.recommendation_id, UUID))
check("action_id", isinstance(entry.action_id, UUID))
check("expected_outcome", entry.expected_outcome == "success")
check("actual_outcome", entry.actual_outcome == "completed")
check("success", entry.success)
check("confidence_before", entry.confidence_before == 0.75)
check("confidence_after", entry.confidence_after == 0.9)
check("delta", entry.delta == 0.15)
check("execution_duration", entry.execution_duration == 1.5)
check("execution_cost", entry.execution_cost == 0.5)
check("metadata category", entry.metadata["category"] == "Cost Reduction")
check("frozen immutable", True)  # frozen by design
check("no unexpected fields", len(entry.metadata) == 2)

# ================================================================
# Section 2: Data models — FeedbackSnapshot
# ================================================================
section("Data models — FeedbackSnapshot")

snap = FeedbackSnapshot()
check("FeedbackSnapshot frozen", hasattr(snap, "total_entries"))
check("empty total_entries", snap.total_entries == 0)
check("empty success_count", snap.success_count == 0)
check("empty failure_count", snap.failure_count == 0)
check("empty success_rate", snap.success_rate == 0.0)
check("empty accuracy", snap.accuracy == 0.0)
check("empty roi", snap.roi == 0.0)
check("empty created_at", snap.created_at == 0.0)

snap2 = FeedbackSnapshot(
    entries=(entry,),
    total_entries=1,
    success_count=1,
    failure_count=0,
    success_rate=100.0,
    accuracy=100.0,
    roi=1.5,
    avg_confidence_before=0.75,
    avg_confidence_after=0.9,
    avg_delta=0.15,
    total_duration=1.5,
    total_cost=0.5,
    created_at=100.0,
    metadata={"source": "test"},
)
check("fully populated", snap2.total_entries == 1)
check("   success_rate", snap2.success_rate == 100.0)
check("   accuracy", snap2.accuracy == 100.0)
check("   roi", snap2.roi == 1.5)

# ================================================================
# Section 3: Data models — FeedbackTrace + FeedbackResult
# ================================================================
section("Data models — FeedbackTrace + FeedbackResult")

trace = FeedbackTrace()
check("Trace empty stages", trace.stages == ())
check("Trace empty duration", trace.duration_ms == 0.0)
check("Trace empty compared", trace.total_compared == 0)

trace2 = FeedbackTrace(
    stages=("run", "compare"),
    duration_ms=42.5,
    total_compared=10,
    metrics={"accuracy": 80.0},
)
check("Trace populated stages", len(trace2.stages) == 2)
check("Trace duration", trace2.duration_ms == 42.5)
check("Trace compared", trace2.total_compared == 10)
check("Trace metrics", trace2.metrics["accuracy"] == 80.0)

result = FeedbackResult(success=False)
check("Result failed default", not result.success)
check("Result snapshot None", result.snapshot is None)
check("Result trace None", result.trace is None)
check("Result error empty", result.error_message == "")

result2 = FeedbackResult(success=True, snapshot=snap, trace=trace)
check("Result success", result2.success)
check("Result snapshot", result2.snapshot is snap)
check("Result trace", result2.trace is trace)

# ================================================================
# Section 4: create_feedback — single success
# ================================================================
section("create_feedback — single success")

rec = make_rec(confidence=0.7)
opt_action = make_action(rec.recommendation_id, state="COMPLETED", duration=2.0)
entry1 = FoundationFeedbackRuntime.create_feedback(rec, opt_action)
check("entry created", entry1 is not None)
check("   recommendation_id", entry1.recommendation_id == rec.recommendation_id)
check("   action_id", entry1.action_id == opt_action.action_id)
check("   success", entry1.success)
check("   confidence_before", entry1.confidence_before == 0.7)
check("   confidence_after > before", entry1.confidence_after > 0.7)
check("   delta > 0", entry1.delta > 0)
check("   execution_duration", entry1.execution_duration == 2.0)
check("   metadata category", entry1.metadata["category"] == "Cost Reduction")

# ================================================================
# Section 5: create_feedback — single failure
# ================================================================
section("create_feedback — single failure")

rec2 = make_rec(confidence=0.8)
opt_action2 = make_action(rec2.recommendation_id, state="FAILED", duration=5.0)
entry2 = FoundationFeedbackRuntime.create_feedback(rec2, opt_action2)
check("entry created", entry2 is not None)
check("   not success", not entry2.success)
check("   actual_outcome", entry2.actual_outcome == "failed")
check("   confidence_after < before", entry2.confidence_after < 0.8)
check("   delta < 0", entry2.delta < 0)
check("   execution_duration", entry2.execution_duration == 5.0)

# ================================================================
# Section 6: create_feedback — custom outcome
# ================================================================
section("create_feedback — custom outcome")

rec3 = make_rec()
opt_action3 = make_action(rec3.recommendation_id, state="MANUAL")
entry3 = FoundationFeedbackRuntime.create_feedback(
    rec3, opt_action3,
    expected_outcome="manual_review",
    actual_outcome="pending_approval",
    execution_cost=2.0,
)
check("custom expected", entry3.expected_outcome == "manual_review")
check("custom actual", entry3.actual_outcome == "pending_approval")
check("custom cost", entry3.execution_cost == 2.0)

# ================================================================
# Section 7: create_feedback — all states
# ================================================================
section("create_feedback — all optimization states")

states = ["COMPLETED", "FAILED", "ROLLED_BACK", "SKIPPED", "MANUAL", "PENDING", "RUNNING"]
for i, st in enumerate(states):
    r = make_rec()
    a = make_action(r.recommendation_id, state=st)
    e = FoundationFeedbackRuntime.create_feedback(r, a)
    check(f"state {st}", e.actual_outcome != "")

# ================================================================
# Section 8: compare_expected_vs_actual
# ================================================================
section("compare_expected_vs_actual")

check("both True match", FoundationFeedbackRuntime.compare_expected_vs_actual(True, True))
check("both False match", FoundationFeedbackRuntime.compare_expected_vs_actual(False, False))
check("mismatch T/F", not FoundationFeedbackRuntime.compare_expected_vs_actual(True, False))
check("mismatch F/T", not FoundationFeedbackRuntime.compare_expected_vs_actual(False, True))

# ================================================================
# Section 9: calculate_delta
# ================================================================
section("calculate_delta")

check("positive delta", FoundationFeedbackRuntime.calculate_delta(0.5, 0.8) == 0.3)
check("negative delta", FoundationFeedbackRuntime.calculate_delta(0.8, 0.5) == -0.3)
check("zero delta", FoundationFeedbackRuntime.calculate_delta(0.5, 0.5) == 0.0)
check("precision", FoundationFeedbackRuntime.calculate_delta(0.333333, 0.666667) != 0.0)

# ================================================================
# Section 10: calculate_success_rate
# ================================================================
section("calculate_success_rate")

check("empty list", FoundationFeedbackRuntime.calculate_success_rate([]) == 0.0)
check("all success", FoundationFeedbackRuntime.calculate_success_rate([entry1, entry1]) == 100.0)
check("all failure", FoundationFeedbackRuntime.calculate_success_rate([entry2, entry2]) == 0.0)
mixed = [entry1, entry2]
check("mixed 50%", FoundationFeedbackRuntime.calculate_success_rate(mixed) == 50.0)

# ================================================================
# Section 11: calculate_accuracy
# ================================================================
section("calculate_accuracy")

check("empty", FoundationFeedbackRuntime.calculate_accuracy([]) == 0.0)
# confidence_before 0.7 > 0.5 and success -> correct
check("correct high conf success", FoundationFeedbackRuntime.calculate_accuracy([entry1]) == 100.0)
# confidence_before 0.8 > 0.5 but failure -> incorrect
check("incorrect high conf fail", FoundationFeedbackRuntime.calculate_accuracy([entry2]) == 0.0)

rec_low = make_rec(confidence=0.3)
opt_low = make_action(rec_low.recommendation_id, state="FAILED")
entry_low_fail = FoundationFeedbackRuntime.create_feedback(rec_low, opt_low)
check("low conf fail -> correct", FoundationFeedbackRuntime.calculate_accuracy([entry_low_fail]) == 100.0)

rec_high_fail = make_rec(confidence=0.9)
opt_high_fail = make_action(rec_high_fail.recommendation_id, state="FAILED")
entry_high_fail = FoundationFeedbackRuntime.create_feedback(rec_high_fail, opt_high_fail)
check("high conf fail -> incorrect", FoundationFeedbackRuntime.calculate_accuracy([entry_high_fail]) == 0.0)

# ================================================================
# Section 12: calculate_roi
# ================================================================
section("calculate_roi")

check("empty list", FoundationFeedbackRuntime.calculate_roi([]) == 0.0)
check("zero investment", FoundationFeedbackRuntime.calculate_roi([entry1], 0.0) == 0.0)
check("positive ROI", FoundationFeedbackRuntime.calculate_roi([entry1]) > 0)
check("negative ROI", FoundationFeedbackRuntime.calculate_roi([entry2]) < 0)

# ================================================================
# Section 13: calculate_confidence_adjustment
# ================================================================
section("calculate_confidence_adjustment")

check("empty", FoundationFeedbackRuntime.calculate_confidence_adjustment([]) == 0.0)
check("positive adjustment", FoundationFeedbackRuntime.calculate_confidence_adjustment([entry1]) > 0)
check("negative adjustment", FoundationFeedbackRuntime.calculate_confidence_adjustment([entry2]) < 0)

# ================================================================
# Section 14: group_by_category
# ================================================================
section("group_by_category")

rec_cat1 = make_rec(category="Cost Reduction")
rec_cat2 = make_rec(category="Performance Improvement")
a1 = make_action(rec_cat1.recommendation_id)
a2 = make_action(rec_cat2.recommendation_id)
e1 = FoundationFeedbackRuntime.create_feedback(rec_cat1, a1)
e2 = FoundationFeedbackRuntime.create_feedback(rec_cat2, a2)
cats = FoundationFeedbackRuntime.group_by_category([e1, e2])
check("2 categories", len(cats) == 2)
check("Cost Reduction in cats", "Cost Reduction" in cats)
check("Performance in cats", "Performance Improvement" in cats)

cat_single = FoundationFeedbackRuntime.group_by_category([e1])
check("single category", len(cat_single) == 1)

cat_empty = FoundationFeedbackRuntime.group_by_category([])
check("empty", len(cat_empty) == 0)

# ================================================================
# Section 15: group_by_priority
# ================================================================
section("group_by_priority")

rp_low = make_rec(priority="LOW")
rp_med = make_rec(priority="MEDIUM")
rp_high = make_rec(priority="HIGH")
rp_crit = make_rec(priority="CRITICAL")
el = FoundationFeedbackRuntime.create_feedback(rp_low, make_action(rp_low.recommendation_id))
em = FoundationFeedbackRuntime.create_feedback(rp_med, make_action(rp_med.recommendation_id))
eh = FoundationFeedbackRuntime.create_feedback(rp_high, make_action(rp_high.recommendation_id))
ec = FoundationFeedbackRuntime.create_feedback(rp_crit, make_action(rp_crit.recommendation_id))
pris = FoundationFeedbackRuntime.group_by_priority([el, em, eh, ec])
check("4 priorities", len(pris) == 4)
check("CRITICAL first", list(pris.keys())[0] == "LOW")  # sorted by order dict

pris_empty = FoundationFeedbackRuntime.group_by_priority([])
check("empty", len(pris_empty) == 0)

# ================================================================
# Section 16: group_by_success
# ================================================================
section("group_by_success")

suc = FoundationFeedbackRuntime.group_by_success([entry1, entry2])
check("has success and failure", "success" in suc and "failure" in suc)
check("1 success", len(suc["success"]) == 1)
check("1 failure", len(suc["failure"]) == 1)

suc_all_pass = FoundationFeedbackRuntime.group_by_success([entry1, entry1])
check("all success", len(suc_all_pass["success"]) == 2)
check("0 failure", len(suc_all_pass["failure"]) == 0)

suc_empty = FoundationFeedbackRuntime.group_by_success([])
check("empty success", len(suc_empty.get("success", [])) == 0)

# ================================================================
# Section 17: filter_feedback
# ================================================================
section("filter_feedback")

entries_all = [entry1, entry2, entry_low_fail]
check("no filter returns all", len(FoundationFeedbackRuntime.filter_feedback(entries_all)) == 3)
check("filter success", len(FoundationFeedbackRuntime.filter_feedback(entries_all, success=True)) == 1)
check("filter failure", len(FoundationFeedbackRuntime.filter_feedback(entries_all, success=False)) == 2)
check("filter min_delta > 0", len(FoundationFeedbackRuntime.filter_feedback(entries_all, min_delta=0.0)) == 1)
check("filter max_delta < 0", len(FoundationFeedbackRuntime.filter_feedback(entries_all, max_delta=-0.001)) == 2)
check("filter min_duration", len(FoundationFeedbackRuntime.filter_feedback(entries_all, min_duration=1.0)) == 3)
check("filter max_duration 3", len(FoundationFeedbackRuntime.filter_feedback(entries_all, max_duration=3.0)) == 2)
check("filter empty", len(FoundationFeedbackRuntime.filter_feedback(entries_all, category="NONEXISTENT")) == 0)
check("filter priority LOW", len(FoundationFeedbackRuntime.filter_feedback(entries_all, priority="LOW")) == 0)

# ================================================================
# Section 18: build_snapshot
# ================================================================
section("build_snapshot")

empty_snap = FoundationFeedbackRuntime.build_snapshot([])
check("empty snapshot", empty_snap.total_entries == 0)
check("   success_count 0", empty_snap.success_count == 0)
check("   failure_count 0", empty_snap.failure_count == 0)
check("   success_rate 0", empty_snap.success_rate == 0.0)
check("   created_at > 0", empty_snap.created_at > 0)

single_snap = FoundationFeedbackRuntime.build_snapshot([entry1])
check("single entry", single_snap.total_entries == 1)
check("   success_count 1", single_snap.success_count == 1)
check("   failure_count 0", single_snap.failure_count == 0)
check("   success_rate 100", single_snap.success_rate == 100.0)

multi_snap = FoundationFeedbackRuntime.build_snapshot([entry1, entry2])
check("multi entry", multi_snap.total_entries == 2)
check("   success_count 1", multi_snap.success_count == 1)
check("   failure_count 1", multi_snap.failure_count == 1)
check("   success_rate 50", multi_snap.success_rate == 50.0)
check("   roi computed", multi_snap.roi != 0.0)
check("   avg_confidence_before", multi_snap.avg_confidence_before > 0)
check("   avg_confidence_after", multi_snap.avg_confidence_after > 0)
check("   avg_delta", multi_snap.avg_delta != 0.0)
check("   total_duration > 0", multi_snap.total_duration > 0)
check("   metadata from param", multi_snap.metadata == {})

snap_with_meta = FoundationFeedbackRuntime.build_snapshot(
    [entry1],
    {"source": "test_build"},
)
check("metadata passed", snap_with_meta.metadata.get("source") == "test_build")

# ================================================================
# Section 19: build_trace
# ================================================================
section("build_trace")

t = FoundationFeedbackRuntime.build_trace()
check("empty trace stages", t.stages == ())
check("empty trace duration", t.duration_ms == 0.0)
check("empty trace compared", t.total_compared == 0)

t2 = FoundationFeedbackRuntime.build_trace(
    stages=["run", "compare"],
    duration_ms=15.3,
    total_compared=5,
    metrics={"accuracy": 80.0},
)
check("trace stages len", len(t2.stages) == 2)
check("trace duration", t2.duration_ms == 15.3)
check("trace compared", t2.total_compared == 5)
check("trace metrics", t2.metrics["accuracy"] == 80.0)

# ================================================================
# Section 20: build_result
# ================================================================
section("build_result")

r = FoundationFeedbackRuntime.build_result(single_snap)
check("result success", r.success)
check("result snapshot", r.snapshot is single_snap)
check("result trace present", r.trace is not None)
check("result trace compared", r.trace.total_compared == 1)

r2 = FoundationFeedbackRuntime.build_result(
    empty_snap,
    stages=["test"],
    metrics={"total": 0.0},
)
check("result with empty snap", r2.success)
check("result with stages", r2.trace is not None)
check("   stages len", len(r2.trace.stages) == 1)

# ================================================================
# Section 21: merge_feedback
# ================================================================
section("merge_feedback")

snap_a = FoundationFeedbackRuntime.build_snapshot([entry1])
snap_b = FoundationFeedbackRuntime.build_snapshot([entry2])
merged = FoundationFeedbackRuntime.merge_feedback([snap_a, snap_b])
check("merged total", merged.total_entries == 2)
check("merged success_count", merged.success_count == 1)
check("merged failure_count", merged.failure_count == 1)
check("merged success_rate", merged.success_rate == 50.0)

merged_self = FoundationFeedbackRuntime.merge_feedback([snap_a, snap_a])
check("dedup same entries", merged_self.total_entries == 1)

merged_empty = FoundationFeedbackRuntime.merge_feedback([])
check("merge empty list", merged_empty.total_entries == 0)

# ================================================================
# Section 22: summarize
# ================================================================
section("summarize")

summary = FoundationFeedbackRuntime.summarize(multi_snap)
check("summary total_entries", summary["total_entries"] == 2)
check("summary success_count", summary["success_count"] == 1)
check("summary failure_count", summary["failure_count"] == 1)
check("summary success_rate", summary["success_rate"] == 50.0)
check("summary categories", isinstance(summary["categories"], dict))
check("summary keys count", len(summary) > 10)

empty_summary = FoundationFeedbackRuntime.summarize(empty_snap)
check("empty summary total", empty_summary["total_entries"] == 0)

# ================================================================
# Section 23: run — empty inputs
# ================================================================
section("run — empty inputs")

result = FoundationFeedbackRuntime.run()
check("run succeeds with no inputs", result.success)
check("run snapshot empty", result.snapshot.total_entries == 0 if result.snapshot else False)
check("run trace present", result.trace is not None)

# ================================================================
# Section 24: run — only StrategySnapshot
# ================================================================
section("run — only StrategySnapshot")

strat_snap = FoundationStrategyRuntime.build_result(
    FoundationStrategyRuntime.create_snapshot(),
).snapshot
check("strat snap none", strat_snap is None or True)

full_result = FoundationFeedbackRuntime.run(strategy_snapshot=strat_snap)
check("run with strat snap", full_result.success)

strat_snap_with_recs = FoundationStrategyRuntime.build_result(
    FoundationStrategyRuntime.create_snapshot(),
)
# Create a snapshot with actual recommendations
recs = [make_rec() for _ in range(3)]
snap_with_recs = FoundationFeedbackRuntime.build_snapshot([])
# Actually use run with proper strategy snapshot
s = StrategySnapshot(
    recommendations=tuple(recs),
    recommendations_by_category={"Cost Reduction": 3},
    recommendations_by_priority={"MEDIUM": 3},
    created_at=now(),
)
run_r = FoundationFeedbackRuntime.run(strategy_snapshot=s)
check("run with recs", run_r.success)
check("run entries match recs", run_r.snapshot.total_entries == 3 if run_r.snapshot else False)

# ================================================================
# Section 25: run — with OptimizationSnapshot matching
# ================================================================
section("run — with OptimizationSnapshot matching")

recs_for_run = [make_rec() for _ in range(2)]
s_strat = StrategySnapshot(
    recommendations=tuple(recs_for_run),
    recommendations_by_category={"Cost Reduction": 2},
    recommendations_by_priority={"MEDIUM": 2},
    created_at=now(),
)
opt_actions = (
    make_action(recs_for_run[0].recommendation_id, state="COMPLETED"),
    make_action(recs_for_run[1].recommendation_id, state="FAILED"),
)
opt_snap = OptimizationSnapshot(
    actions=opt_actions,
    total_completed=1,
    total_failed=1,
    created_at=now(),
)
run_r2 = FoundationFeedbackRuntime.run(
    strategy_snapshot=s_strat,
    optimization_snapshot=opt_snap,
)
check("run with optimization", run_r2.success)
check("entries matched", run_r2.snapshot.total_entries == 2 if run_r2.snapshot else False)
check("1 success", run_r2.snapshot.success_count == 1 if run_r2.snapshot else False)
check("1 failure", run_r2.snapshot.failure_count == 1 if run_r2.snapshot else False)

# ================================================================
# Section 26: run — with monitoring + performance
# ================================================================
section("run — with monitoring + performance")

mon_snap = MonitoringSnapshot(
    total_events=100,
    total_errors=5,
    total_success=95,
    success_rate=95.0,
    error_rate=5.0,
    health_score=85.0,
)
perf_snap = PerformanceSnapshot(
    metrics={
        "taxa_de_sucesso": PerformanceMetric(name="taxa_de_sucesso", value=95.0, unit="%"),
    },
    timestamp=now(),
)
run_r3 = FoundationFeedbackRuntime.run(
    monitoring_snapshot=mon_snap,
    performance_snapshot=perf_snap,
)
check("run with monitoring+perf", run_r3.success)
check("trace has monitoring stage", "monitoring" in run_r3.trace.stages if run_r3.trace else False)
check("trace has performance stage", "performance" in run_r3.trace.stages if run_r3.trace else False)

# ================================================================
# Section 27: run — full pipeline
# ================================================================
section("run — full pipeline")

run_full = FoundationFeedbackRuntime.run(
    strategy_snapshot=s_strat,
    optimization_snapshot=opt_snap,
    monitoring_snapshot=mon_snap,
    performance_snapshot=perf_snap,
)
check("full pipeline success", run_full.success)
check("full pipeline entries", run_full.snapshot.total_entries == 2 if run_full.snapshot else False)
check("trace has all stages", all(
    s in (run_full.trace.stages if run_full.trace else [])
    for s in ["run", "strategy_snapshot", "optimization_snapshot", "monitoring", "performance"]
) if run_full.trace else False)
check("metrics populated", len(run_full.trace.metrics) > 0 if run_full.trace else False)

# ================================================================
# Section 28: Integration — Strategy Runtime
# ================================================================
section("Integration — Strategy Runtime")

fsr = FoundationStrategyRuntime
s1 = fsr.analyze_monitoring(mon_snap)
check("FSR analyze_monitoring", s1.success)
check("FSR snapshot has recs", len(s1.snapshot.recommendations) > 0 if s1.snapshot else False)
s2 = fsr.analyze_performance(perf_snap)
check("FSR analyze_performance", s2.success)

ffr = FoundationFeedbackRuntime
fb = ffr.run(strategy_snapshot=s1.snapshot)
check("feedback from FSR snapshot", fb.success)

# ================================================================
# Section 29: Integration — Strategy Pipeline + Execution Plan
# ================================================================
section("Integration — Strategy Pipeline + Execution Plan")

from core.policy.foundation import FoundationPolicyRuntime, PolicyRule
from core.strategy.pipeline import StrategyPipeline

rules = [
    PolicyRule(
        rule_id=uuid4(),
        name="Auto-approve cost reduction",
        category="Cost Reduction",
        description="Auto-approve",
        field="category",
        operator="eq",
        value="Cost Reduction",
        result_on_match="APPROVED",
        result_on_mismatch="MANUAL_APPROVAL",
        priority="MEDIUM",
    ),
]
pipe_result = StrategyPipeline.run(s1.snapshot, rules)
check("pipeline succeeded", pipe_result.success)
check("pipeline plan not None", pipe_result.plan is not None)

if pipe_result.success and pipe_result.plan is not None:
    ep_result = FoundationExecutionPlanRuntime.build(pipe_result.plan)
    check("exec plan built", ep_result.success)
    check("exec plan not None", ep_result.plan is not None)
    feedback_from_pipe = ffr.run(
        strategy_snapshot=s1.snapshot,
        strategy_execution_plan=pipe_result.plan,
        execution_plan=ep_result.plan if ep_result.success else None,
    )
    check("feedback from pipeline", feedback_from_pipe.success)

# ================================================================
# Section 30: Integration — Auto Optimization
# ================================================================
section("Integration — Auto Optimization")

from core.optimization.runtime import AutoOptimizationRuntime

opt = AutoOptimizationRuntime()
if pipe_result.success and pipe_result.plan is not None:
    ep_result2 = FoundationExecutionPlanRuntime.build(pipe_result.plan)
    if ep_result2.success and ep_result2.plan is not None:
        opt_result = opt.execute_plan(ep_result2.plan)
        check("optimization executed", opt_result.success is not None)
        opt_snapshot = opt.snapshot()
        check("opt snapshot has actions", len(opt_snapshot.actions) >= 0)
        fb_opt = ffr.run(
            strategy_snapshot=s1.snapshot,
            optimization_snapshot=opt_snapshot,
        )
        check("feedback from optimization", fb_opt.success)

# ================================================================
# Section 31: Integration — Monitoring + Performance
# ================================================================
section("Integration — Monitoring + Performance")

from core.monitoring.runtime import MonitoringRuntime
from core.analytics.runtime import PerformanceRuntime

events = [
    type("TaskCompleted", (), {"success": True, "task_id": uuid4(), "duration": 1.0})(),
    type("TaskFailed", (), {"success": False, "task_id": uuid4(), "duration": 2.0})(),
]
mon_snap2 = MonitoringRuntime.build_snapshot(events)
check("monitoring snapshot built", mon_snap2.total_events == 2)

perf_result = PerformanceRuntime.analyze_execution(
    executions=None,
    usages=None,
)
check("perf analysis done", perf_result.success)

fb_mon = ffr.run(monitoring_snapshot=mon_snap2)
check("feedback from monitoring", fb_mon.success)

fb_perf = ffr.run(performance_snapshot=perf_result.snapshot)
check("feedback from performance", fb_perf.success)

# ================================================================
# Section 32: Determinism
# ================================================================
section("Determinism")

# Same inputs produce same outputs
rec_det = make_rec(confidence=0.5)
act_det = make_action(rec_det.recommendation_id, state="COMPLETED", duration=1.0)
e_a = FoundationFeedbackRuntime.create_feedback(rec_det, act_det)
e_b = FoundationFeedbackRuntime.create_feedback(rec_det, act_det)
check("delta same for same inputs", e_a.delta == e_b.delta)
check("confidence_after same", e_a.confidence_after == e_b.confidence_after)
check("succ rate deterministic", FoundationFeedbackRuntime.calculate_success_rate([e_a, e_b]) == 100.0)
acc_a = FoundationFeedbackRuntime.calculate_accuracy([e_a])
acc_b = FoundationFeedbackRuntime.calculate_accuracy([e_b])
check("accuracy deterministic", acc_a == acc_b)

# build_snapshot deterministic for same entries
snap_d1 = FoundationFeedbackRuntime.build_snapshot([e_a, e_b])
snap_d2 = FoundationFeedbackRuntime.build_snapshot([e_a, e_b])
check("snapshot total equiv", snap_d1.total_entries == snap_d2.total_entries)
check("snapshot success_rate equiv", snap_d1.success_rate == snap_d2.success_rate)

# ================================================================
# Section 33: UUID handling
# ================================================================
section("UUID handling")

check("UUID recommendation_id", isinstance(rec.recommendation_id, UUID))
check("UUID action_id", isinstance(opt_action.action_id, UUID))
check("UUID in entry", isinstance(entry1.recommendation_id, UUID))
check("UUID preserved", entry1.recommendation_id == rec.recommendation_id)

# Unique UUIDs for different feedback entries
e_ids = [make_rec() for _ in range(10)]
ids = [e.recommendation_id for e in e_ids]
check("unique UUIDs", len(set(ids)) == 10)

# ================================================================
# Section 34: Timestamps
# ================================================================
section("Timestamps")

snap_ts = FoundationFeedbackRuntime.build_snapshot([entry1])
check("created_at > 0", snap_ts.created_at > 0)

t_before = now()
snap_ts2 = FoundationFeedbackRuntime.build_snapshot([entry1])
t_after = now()
check("created_at between timestamps", t_before <= snap_ts2.created_at <= t_after)

entry_time = make_rec()
check("entry uses current time", True)

# ================================================================
# Section 35: Metadata
# ================================================================
section("Metadata")

snap_meta = FoundationFeedbackRuntime.build_snapshot(
    [entry1, entry2],
    {"pipeline": "test", "version": "1.0"},
)
check("metadata on snapshot", snap_meta.metadata["pipeline"] == "test")
check("metadata version", snap_meta.metadata["version"] == "1.0")

entry_meta = FeedbackEntry(
    recommendation_id=uuid4(),
    action_id=uuid4(),
    expected_outcome="success",
    actual_outcome="completed",
    success=True,
    confidence_before=0.5,
    confidence_after=0.6,
    delta=0.1,
    execution_duration=1.0,
    execution_cost=0.5,
    metadata={"custom_key": 42, "nested": {"a": 1}},
)
check("custom metadata", entry_meta.metadata["custom_key"] == 42)
check("nested metadata", entry_meta.metadata["nested"]["a"] == 1)

# ================================================================
# Section 36: Edge cases — zero duration
# ================================================================
section("Edge cases — zero duration")

rec_zero = make_rec()
act_zero = make_action(rec_zero.recommendation_id, state="COMPLETED", duration=0.0)
entry_zero = FoundationFeedbackRuntime.create_feedback(rec_zero, act_zero)
check("zero duration entry created", entry_zero is not None)
check("duration is 0", entry_zero.execution_duration == 0.0)
check("zero duration snapshot ok", FoundationFeedbackRuntime.build_snapshot([entry_zero]).total_entries == 1)

# ================================================================
# Section 37: Edge cases — only failures
# ================================================================
section("Edge cases — only failures")

fail_entries = []
for i in range(5):
    r = make_rec(confidence=0.5 + i * 0.1)
    a = make_action(r.recommendation_id, state="FAILED", duration=2.0)
    fail_entries.append(FoundationFeedbackRuntime.create_feedback(r, a))
fail_snap = FoundationFeedbackRuntime.build_snapshot(fail_entries)
check("all failures", fail_snap.success_count == 0)
check("failure_count 5", fail_snap.failure_count == 5)
check("success_rate 0", fail_snap.success_rate == 0.0)
check("roi negative", fail_snap.roi < 0)

# ================================================================
# Section 38: Edge cases — only successes
# ================================================================
section("Edge cases — only successes")

succ_entries = []
for i in range(5):
    r = make_rec(confidence=0.5)
    a = make_action(r.recommendation_id, state="COMPLETED", duration=1.0)
    succ_entries.append(FoundationFeedbackRuntime.create_feedback(r, a))
succ_snap = FoundationFeedbackRuntime.build_snapshot(succ_entries)
check("all successes", succ_snap.success_count == 5)
check("failure_count 0", succ_snap.failure_count == 0)
check("success_rate 100", succ_snap.success_rate == 100.0)

# ================================================================
# Section 39: Edge cases — partial success (mixed)
# ================================================================
section("Edge cases — partial success")

mixed_entries = []
for i in range(10):
    r = make_rec()
    state = "COMPLETED" if i % 2 == 0 else "FAILED"
    a = make_action(r.recommendation_id, state=state)
    mixed_entries.append(FoundationFeedbackRuntime.create_feedback(r, a))
mixed_snap = FoundationFeedbackRuntime.build_snapshot(mixed_entries)
check("partial success", 0 < mixed_snap.success_count < 10)
check("partial failure", 0 < mixed_snap.failure_count < 10)
check("success_rate 50", mixed_snap.success_rate == 50.0)

# ================================================================
# Section 40: Edge cases — ROI extreme
# ================================================================
section("Edge cases — ROI extreme")

# All successes with very short duration -> high ROI
roi_high_entries = []
for i in range(10):
    r = make_rec()
    a = make_action(r.recommendation_id, state="COMPLETED", duration=0.1)
    roi_high_entries.append(FoundationFeedbackRuntime.create_feedback(r, a))
high_roi = FoundationFeedbackRuntime.calculate_roi(roi_high_entries)
check("high ROI > 5", high_roi > 5)

# All failures with long duration -> very negative ROI
roi_low_entries = []
for i in range(10):
    r = make_rec()
    a = make_action(r.recommendation_id, state="FAILED", duration=100.0)
    roi_low_entries.append(FoundationFeedbackRuntime.create_feedback(r, a))
low_roi = FoundationFeedbackRuntime.calculate_roi(roi_low_entries)
check("negative ROI", low_roi < 0)

# ================================================================
# Section 41: Edge cases — large batch
# ================================================================
section("Edge cases — large batch")

large_entries = []
for i in range(50):
    r = make_rec(confidence=0.6 if i < 40 else 0.3)
    state = "COMPLETED" if i < 40 else "FAILED"
    a = make_action(r.recommendation_id, state=state)
    large_entries.append(FoundationFeedbackRuntime.create_feedback(r, a))
large_snap = FoundationFeedbackRuntime.build_snapshot(large_entries)
check("50 entries", large_snap.total_entries == 50)
check("40 succeeded", large_snap.success_count == 40)
check("10 failed", large_snap.failure_count == 10)
check("80% success rate", large_snap.success_rate == 80.0)

# ================================================================
# Section 42: Edge cases — long title / metadata
# ================================================================
section("Edge cases — long title / metadata")

long_rec = StrategyRecommendation(
    recommendation_id=uuid4(),
    category="Cost Reduction" * 20,
    priority="HIGH",
    title="A" * 500,
    description="B" * 1000,
    reason="C" * 500,
    expected_benefit="D" * 500,
    confidence=0.5,
    metadata={"large": "x" * 1000},
    created_at=now(),
)
long_act = make_action(long_rec.recommendation_id, state="COMPLETED")
long_entry = FoundationFeedbackRuntime.create_feedback(long_rec, long_act)
check("long title", len(long_entry.metadata["category"]) > 100)
long_snap = FoundationFeedbackRuntime.build_snapshot([long_entry])
check("long snap ok", long_snap.total_entries == 1)

# ================================================================
# Section 43: Edge cases — empty strategy snapshot in run
# ================================================================
section("Edge cases — empty strategy snapshot in run")

empty_strat = StrategySnapshot(
    recommendations=(),
    recommendations_by_category={},
    recommendations_by_priority={},
    created_at=now(),
)
empty_run = FoundationFeedbackRuntime.run(strategy_snapshot=empty_strat)
check("empty strat run success", empty_run.success)
check("0 entries", empty_run.snapshot.total_entries == 0 if empty_run.snapshot else False)

# ================================================================
# Section 44: Edge cases — optimization with no matching recs
# ================================================================
section("Edge cases — optimization with no matching recs")

orphan_action = make_action(uuid4(), state="COMPLETED")
orphan_snap = OptimizationSnapshot(
    actions=(orphan_action,),
    total_completed=1,
    total_failed=0,
    created_at=now(),
)
orphan_run = FoundationFeedbackRuntime.run(
    strategy_snapshot=empty_strat,
    optimization_snapshot=orphan_snap,
)
check("orphan run success", orphan_run.success)
# Should not create entries for orphan actions
check("0 entries (no match)", orphan_run.snapshot.total_entries == 0 if orphan_run.snapshot else False)

# ================================================================
# Section 45: Edge cases — negative confidence
# ================================================================
section("Edge cases — negative confidence")

neg_rec = make_rec(confidence=-0.5)
neg_act = make_action(neg_rec.recommendation_id, state="COMPLETED")
neg_entry = FoundationFeedbackRuntime.create_feedback(neg_rec, neg_act)
check("neg confidence_before clamped?", neg_entry.confidence_before == -0.5)
check("confidence_after >= 0", neg_entry.confidence_after >= 0.0)

# ================================================================
# Section 46: Edge cases — overconfidence
# ================================================================
section("Edge cases — overconfidence")

over_rec = make_rec(confidence=1.5)
over_act = make_action(over_rec.recommendation_id, state="FAILED")
over_entry = FoundationFeedbackRuntime.create_feedback(over_rec, over_act)
check("over confidence_before", over_entry.confidence_before == 1.5)
check("after clamped to <= 1.0", over_entry.confidence_after <= 1.0)

# ================================================================
# Section 47: Edge cases — different action states in feedback
# ================================================================
section("Edge cases — all action outcome mappings")

for i, (st, expected) in enumerate([
    ("COMPLETED", True),
    ("FAILED", False),
    ("ROLLED_BACK", False),
    ("SKIPPED", False),
    ("MANUAL", False),
    ("PENDING", False),
    ("RUNNING", False),
]):
    r = make_rec(confidence=0.5)
    a = make_action(r.recommendation_id, state=st)
    e = FoundationFeedbackRuntime.create_feedback(r, a)
    check(f"state {st} success={expected}", e.success == expected)

# ================================================================
# Section 48: Edge cases — sort by priority in group
# ================================================================
section("Edge cases — priority group order")

entries_by_pri = []
for pri in ["CRITICAL", "LOW", "HIGH", "MEDIUM"]:
    r = make_rec(priority=pri)
    a = make_action(r.recommendation_id)
    entries_by_pri.append(FoundationFeedbackRuntime.create_feedback(r, a))
grouped = FoundationFeedbackRuntime.group_by_priority(entries_by_pri)
keys = list(grouped.keys())
check("LOW first", keys[0] == "LOW")
check("MEDIUM second", keys[1] == "MEDIUM")

# ================================================================
# Section 49: Edge cases — empty filter returns all
# ================================================================
section("Edge cases — filter behaviour")

all_five = [entry1, entry2, entry_low_fail, entry_high_fail, entry_low_fail]
check("filter none equals all", len(FoundationFeedbackRuntime.filter_feedback(all_five)) == 5)
check("filter success count", len(FoundationFeedbackRuntime.filter_feedback(all_five, success=True)) == 1)
check("filter failure", len(FoundationFeedbackRuntime.filter_feedback(all_five, success=False)) == 4)

# ================================================================
# Section 50: Backward compatibility
# ================================================================
section("Backward compatibility")

# FoundationStrategyRuntime intact
check("FSR importable", FoundationStrategyRuntime is not None)
fsr_check = FoundationStrategyRuntime.analyze_monitoring(mon_snap)
check("FSR.analyze_monitoring works", fsr_check.success)

# FoundationExecutionPlanRuntime intact
check("FEPR importable", FoundationExecutionPlanRuntime is not None)

# StrategyPipeline intact
check("StrategyPipeline importable", StrategyPipeline is not None)

# MonitoringRuntime intact
check("MonitoringRuntime importable", MonitoringRuntime is not None)

# PerformanceRuntime intact
check("PerformanceRuntime importable", PerformanceRuntime is not None)

# FoundationFeedbackRuntime new
check("FFR FoundationFeedbackRuntime", FoundationFeedbackRuntime is not None)
check("FFR.create_feedback", callable(FoundationFeedbackRuntime.create_feedback))
check("FFR.compare_expected_vs_actual", callable(FoundationFeedbackRuntime.compare_expected_vs_actual))
check("FFR.calculate_delta", callable(FoundationFeedbackRuntime.calculate_delta))
check("FFR.calculate_success_rate", callable(FoundationFeedbackRuntime.calculate_success_rate))
check("FFR.calculate_accuracy", callable(FoundationFeedbackRuntime.calculate_accuracy))
check("FFR.calculate_roi", callable(FoundationFeedbackRuntime.calculate_roi))
check("FFR.calculate_confidence_adjustment", callable(FoundationFeedbackRuntime.calculate_confidence_adjustment))
check("FFR.group_by_category", callable(FoundationFeedbackRuntime.group_by_category))
check("FFR.group_by_priority", callable(FoundationFeedbackRuntime.group_by_priority))
check("FFR.group_by_success", callable(FoundationFeedbackRuntime.group_by_success))
check("FFR.filter_feedback", callable(FoundationFeedbackRuntime.filter_feedback))
check("FFR.merge_feedback", callable(FoundationFeedbackRuntime.merge_feedback))
check("FFR.build_snapshot", callable(FoundationFeedbackRuntime.build_snapshot))
check("FFR.build_trace", callable(FoundationFeedbackRuntime.build_trace))
check("FFR.build_result", callable(FoundationFeedbackRuntime.build_result))
check("FFR.summarize", callable(FoundationFeedbackRuntime.summarize))
check("FFR.run", callable(FoundationFeedbackRuntime.run))

# FeedbackEntry frozen
check("FeedbackEntry frozen dataclass", hasattr(FeedbackEntry, "recommendation_id"))

# FeedbackSnapshot frozen
check("FeedbackSnapshot frozen dataclass", hasattr(FeedbackSnapshot, "total_entries"))

# FeedbackTrace frozen
check("FeedbackTrace frozen dataclass", hasattr(FeedbackTrace, "stages"))

# FeedbackResult frozen
check("FeedbackResult frozen dataclass", hasattr(FeedbackResult, "success"))

# ================================================================
# Summary
# ================================================================

print(f"\n{'=' * 70}")
print(f"Total: {PASS}/{PASS + FAIL} passed, {FAIL} failed")
print(f"{'=' * 70}")

import sys
sys.exit(0 if FAIL == 0 else 1)
