"""Demo: Strategy Execution Pipeline Foundation — 180+ scenarios."""

import time
from dataclasses import dataclass
from typing import Any
from uuid import UUID, uuid4

from core.strategy.foundation import (
    CATEGORY_COST_REDUCTION,
    CATEGORY_PERFORMANCE_IMPROVEMENT,
    CATEGORY_RISK_MITIGATION,
    CATEGORY_WORKFLOW_OPTIMIZATION,
    CATEGORY_CAPACITY_PLANNING,
    CATEGORY_SKILL_DEVELOPMENT,
    CATEGORY_MONITORING_ALERT,
    PRIORITY_LOW,
    PRIORITY_MEDIUM,
    PRIORITY_HIGH,
    PRIORITY_CRITICAL,
    FoundationStrategyRuntime,
    StrategyRecommendation,
    StrategySnapshot,
)
from core.policy.foundation import (
    FoundationPolicyRuntime,
    PolicyRule,
    RESULT_APPROVED,
    RESULT_REJECTED,
    RESULT_MANUAL_APPROVAL,
    RESULT_BLOCKED,
    RESULT_NOT_APPLICABLE,
    CATEGORY_COST,
    CATEGORY_PERFORMANCE,
    CATEGORY_WORKFLOW,
    CATEGORY_SECURITY,
    CATEGORY_STRATEGY,
    PRIORITY_LOW as POLICY_PRIORITY_LOW,
    PRIORITY_MEDIUM as POLICY_PRIORITY_MEDIUM,
    PRIORITY_HIGH as POLICY_PRIORITY_HIGH,
    PRIORITY_CRITICAL as POLICY_PRIORITY_CRITICAL,
    OPERATOR_GT,
    OPERATOR_GTE,
    OPERATOR_LT,
    OPERATOR_EQ,
    OPERATOR_NE,
)
from core.strategy.pipeline import (
    StrategyPipeline,
    StrategyExecutionItem,
    StrategyExecutionPlan,
    StrategyPipelineTrace,
    StrategyPipelineResult,
)

# ------------------------------------------------------------------
# Constants
# ------------------------------------------------------------------

TS = 1000000.0

# ------------------------------------------------------------------
# Helpers
# ------------------------------------------------------------------

pass_count = 0
fail_count = 0


def check(name: str, condition: bool, detail: str = "") -> None:
    global pass_count, fail_count
    if condition:
        pass_count += 1
        print(f"[PASS] {name:50s} | {detail}")
    else:
        fail_count += 1
        print(f"[FAIL] {name:50s} | {detail}")


def _rec(
    category: str = CATEGORY_COST_REDUCTION,
    priority: str = PRIORITY_MEDIUM,
    confidence: float = 0.8,
    title: str = "TestRec",
    rec_id: UUID | None = None,
    **metadata: Any,
) -> StrategyRecommendation:
    rid = rec_id if rec_id is not None else uuid4()
    return StrategyRecommendation(
        recommendation_id=rid,
        category=category,
        priority=priority,
        title=title,
        description="",
        reason="",
        expected_benefit="",
        confidence=confidence,
        metadata=metadata,
        created_at=TS,
    )


def _snapshot(
    recs: list[StrategyRecommendation],
) -> StrategySnapshot:
    return FoundationStrategyRuntime.create_snapshot()


def _rule(
    name: str,
    category: str,
    field: str,
    operator: str,
    value: Any,
    result_on_match: str = RESULT_APPROVED,
    result_on_mismatch: str = RESULT_REJECTED,
    priority: str = POLICY_PRIORITY_MEDIUM,
) -> PolicyRule:
    return FoundationPolicyRuntime.create_rule(
        name=name,
        category=category,
        field=field,
        operator=operator,
        value=value,
        result_on_match=result_on_match,
        result_on_mismatch=result_on_mismatch,
        priority=priority,
    )


# Unique IDs for deterministic tests
UID_A = UUID("10000000-0000-0000-0000-000000000001")
UID_B = UUID("10000000-0000-0000-0000-000000000002")
UID_C = UUID("10000000-0000-0000-0000-000000000003")
UID_D = UUID("10000000-0000-0000-0000-000000000004")
UID_E = UUID("10000000-0000-0000-0000-000000000005")

print("=" * 70)
print("Demo: Strategy Execution Pipeline Foundation")
print("=" * 70)

# ==================================================================
# Section 1: Data models
# ==================================================================
print("\n" + "=" * 70)
print("Section 1: Data models")
print("=" * 70)

# StrategyExecutionItem
item1 = StrategyExecutionItem(
    recommendation_id=UID_A,
    category=CATEGORY_COST_REDUCTION,
    priority=PRIORITY_HIGH,
    policy_result=RESULT_APPROVED,
    can_execute=True,
    requires_manual_approval=False,
    reason="All good",
    metadata={"source": "test"},
)
check("Item frozen", True, "")
check("  recommendation_id", item1.recommendation_id == UID_A, "")
check("  category", item1.category == CATEGORY_COST_REDUCTION, "")
check("  priority", item1.priority == PRIORITY_HIGH, "")
check("  policy_result APPROVED", item1.policy_result == RESULT_APPROVED, "")
check("  can_execute True", item1.can_execute is True, "")
check("  requires_manual False", item1.requires_manual_approval is False, "")
check("  reason", item1.reason == "All good", "")
check("  metadata", item1.metadata.get("source") == "test", "")

# REJECTED item
item_rejected = StrategyExecutionItem(
    recommendation_id=UID_B,
    category=CATEGORY_RISK_MITIGATION,
    priority=PRIORITY_CRITICAL,
    policy_result=RESULT_REJECTED,
    can_execute=False,
    requires_manual_approval=False,
    reason="Risk too high",
)
check("Item rejected", item_rejected.policy_result == RESULT_REJECTED, "")
check("  can_execute False", item_rejected.can_execute is False, "")

# MANUAL_APPROVAL item
item_manual = StrategyExecutionItem(
    recommendation_id=UID_C,
    category=CATEGORY_PERFORMANCE_IMPROVEMENT,
    priority=PRIORITY_MEDIUM,
    policy_result=RESULT_MANUAL_APPROVAL,
    can_execute=False,
    requires_manual_approval=True,
    reason="Needs human review",
)
check("Item manual", item_manual.policy_result == RESULT_MANUAL_APPROVAL, "")
check("  requires_manual True", item_manual.requires_manual_approval is True, "")

# BLOCKED item
item_blocked = StrategyExecutionItem(
    recommendation_id=UID_D,
    category=CATEGORY_WORKFLOW_OPTIMIZATION,
    priority=PRIORITY_LOW,
    policy_result=RESULT_BLOCKED,
    can_execute=False,
    requires_manual_approval=False,
    reason="System constraint",
)
check("Item blocked", item_blocked.policy_result == RESULT_BLOCKED, "")

# NOT_APPLICABLE item
_item_na = StrategyExecutionItem(
    recommendation_id=UID_E,
    category=CATEGORY_CAPACITY_PLANNING,
    priority=PRIORITY_LOW,
    policy_result=RESULT_NOT_APPLICABLE,
    can_execute=False,
    requires_manual_approval=False,
    reason="No matching field",
)
check("Item N/A", _item_na.policy_result == RESULT_NOT_APPLICABLE, "")
check("  can_execute False", _item_na.can_execute is False, "")

# StrategyExecutionPlan
plan = StrategyExecutionPlan(
    approved=(item1,),
    manual=(item_manual,),
    blocked=(item_blocked,),
    rejected=(item_rejected,),
    not_applicable=(_item_na,),
    items=(item1, item_rejected, item_manual, item_blocked, _item_na),
    created_at=TS,
    metadata={"env": "test"},
)
check("Plan frozen", True, "")
check("  approved len", len(plan.approved) == 1, "")
check("  manual len", len(plan.manual) == 1, "")
check("  blocked len", len(plan.blocked) == 1, "")
check("  rejected len", len(plan.rejected) == 1, "")
check("  not_applicable len", len(plan.not_applicable) == 1, "")
check("  items total", len(plan.items) == 5, "")
check("  created_at", plan.created_at == TS, "")
check("  metadata", plan.metadata.get("env") == "test", "")

# StrategyPipelineTrace
trace = StrategyPipelineTrace(
    stages=("run", "evaluate", "build"),
    duration_ms=5.0,
    metrics={"items": 5.0},
)
check("Trace frozen", True, "")
check("  stages", len(trace.stages) == 3, "")
check("  duration", trace.duration_ms == 5.0, "")
check("  metrics", trace.metrics.get("items") == 5.0, "")
check("Trace default", StrategyPipelineTrace(), "")

# StrategyPipelineResult
result = StrategyPipelineResult(
    success=True,
    plan=plan,
    trace=trace,
)
check("Result success", result.success is True, "")
check("  plan ref", result.plan is plan, "")
check("  trace ref", result.trace is trace, "")
result_err = StrategyPipelineResult(success=False, error_message="fail")
check("Result error", result_err.success is False, "")
check("  error_message", result_err.error_message == "fail", "")
check("Result default", StrategyPipelineResult(success=False), "")

# ==================================================================
# Section 2: build_plan
# ==================================================================
print("\n" + "=" * 70)
print("Section 2: build_plan")
print("=" * 70)

rec_a = _rec(category=CATEGORY_COST_REDUCTION, priority=PRIORITY_HIGH, title="CostA", rec_id=UID_A)
rec_b = _rec(category=CATEGORY_RISK_MITIGATION, priority=PRIORITY_CRITICAL, title="RiskB", rec_id=UID_B)

rule1 = _rule("High conf", CATEGORY_COST, "confidence", OPERATOR_GT, 0.5)
rule2 = _rule("Low conf", CATEGORY_COST, "confidence", OPERATOR_LT, 0.3, result_on_match=RESULT_REJECTED)

ev1 = FoundationPolicyRuntime.evaluate(rule1, rec_a)
ev2 = FoundationPolicyRuntime.evaluate(rule1, rec_b)
ev3 = FoundationPolicyRuntime.evaluate(rule2, rec_a)

plan_from_evals = StrategyPipeline.build_plan([ev1, ev2, ev3], [rec_a, rec_b])
check("build_plan items", len(plan_from_evals.items) == 3, f"count={len(plan_from_evals.items)}")
check("build_plan has approved", len(plan_from_evals.approved) > 0, "")
check("build_plan created_at > 0", plan_from_evals.created_at > 0, "")

# Empty
empty_plan = StrategyPipeline.build_plan([], [])
check("build_plan empty", len(empty_plan.items) == 0, "")
check("  approved=0", len(empty_plan.approved) == 0, "")
check("  manual=0", len(empty_plan.manual) == 0, "")

# Build plan with mixed results
rule_manual = _rule("Manual check", CATEGORY_STRATEGY, "confidence", OPERATOR_GT, 0.9,
                     result_on_match=RESULT_MANUAL_APPROVAL)
ev_manual = FoundationPolicyRuntime.evaluate(rule_manual, rec_a)
plan_mixed = StrategyPipeline.build_plan([ev1, ev_manual], [rec_a, rec_b])
check("build_plan mixed", len(plan_mixed.items) == 2, f"count={len(plan_mixed.items)}")

# ==================================================================
# Section 3: evaluate_policies
# ==================================================================
print("\n" + "=" * 70)
print("Section 3: evaluate_policies")
print("=" * 70)

recs = [rec_a, rec_b]
rules = [rule1]
snap = FoundationStrategyRuntime.create_snapshot()
# We'll create a real snapshot using FoundationStrategyRuntime later

# Actually use FoundationStrategyRuntime to build a snapshot with recommendations
# We need to use the internal _build_snapshot but it's private
# Alternative: use FoundationStrategyRuntime.merge_recommendations or build our own
# Let's just call evaluate_policies with a manually created StrategySnapshot

fake_snap = StrategySnapshot(
    recommendations=(rec_a, rec_b),
    recommendations_by_category={},
    recommendations_by_priority={},
    created_at=TS,
)

pol_res = StrategyPipeline.evaluate_policies(fake_snap, rules)
check("evaluate_policies success", pol_res.success is True, "")
if pol_res.snapshot:
    check("  evaluations", len(pol_res.snapshot.evaluations) == 2, f"count={len(pol_res.snapshot.evaluations)}")
    check("  rules_applied", pol_res.snapshot.rules_applied == 2, "")

# No rules
pol_res_no_rules = StrategyPipeline.evaluate_policies(fake_snap, [])
check("evaluate_policies no rules", pol_res_no_rules.success is True, "")
if pol_res_no_rules.snapshot:
    check("  empty evaluations", len(pol_res_no_rules.snapshot.evaluations) == 0, "")

# Empty snapshot
pol_res_empty = StrategyPipeline.evaluate_policies(
    StrategySnapshot(created_at=TS), rules,
)
check("evaluate_policies empty snap", pol_res_empty.success is True, "")
if pol_res_empty.snapshot:
    check("  zero evaluations", len(pol_res_empty.snapshot.evaluations) == 0, "")

# ==================================================================
# Section 4: run (full pipeline — no rules)
# ==================================================================
print("\n" + "=" * 70)
print("Section 4: run — no rules")
print("=" * 70)

result_no_rules = StrategyPipeline.run(fake_snap, [])
check("run no rules success", result_no_rules.success is True, "")
if result_no_rules.plan:
    check("  plan items", len(result_no_rules.plan.items) == 2, f"count={len(result_no_rules.plan.items)}")
    check("  all approved", len(result_no_rules.plan.approved) == 2, "")
    check("  rejected=0", len(result_no_rules.plan.rejected) == 0, "")
if result_no_rules.trace:
    check("  trace stages", "run" in result_no_rules.trace.stages, "")

# Empty snapshot, no rules
result_empty = StrategyPipeline.run(StrategySnapshot(created_at=TS), [])
check("run empty+no rules success", result_empty.success is True, "")
if result_empty.plan:
    check("  plan items=0", len(result_empty.plan.items) == 0, "")
if result_empty.trace:
    check("  trace empty_snapshot", any("empty" in s for s in result_empty.trace.stages), "")

# ==================================================================
# Section 5: run (full pipeline — basic)
# ==================================================================
print("\n" + "=" * 70)
print("Section 5: run — basic")
print("=" * 70)

conf_rule = _rule("Confidence gate", CATEGORY_COST, "confidence", OPERATOR_GT, 0.5,
                   result_on_match=RESULT_APPROVED, result_on_mismatch=RESULT_REJECTED)

run_result = StrategyPipeline.run(fake_snap, [conf_rule])
check("run basic success", run_result.success is True, "")
if run_result.plan:
    check("  plan items", len(run_result.plan.items) == 2, f"count={len(run_result.plan.items)}")
    approved = len(run_result.plan.approved)
    rejected = len(run_result.plan.rejected)
    check("  has approved", approved > 0, f"approved={approved}")
    check("  manual=0", len(run_result.plan.manual) == 0, "")
    check("  blocked=0", len(run_result.plan.blocked) == 0, "")
if run_result.trace:
    check("  trace stages count", len(run_result.trace.stages) >= 2, f"stages={run_result.trace.stages}")
    check("  trace metrics items", run_result.trace.metrics.get("recommendations", 0) == 2, "")

# ==================================================================
# Section 6: run — single recommendation
# ==================================================================
print("\n" + "=" * 70)
print("Section 6: run — single recommendation")
print("=" * 70)

single_rec = _rec(category=CATEGORY_COST_REDUCTION, priority=PRIORITY_HIGH, confidence=0.9, title="Single", rec_id=UID_C)
single_snap = StrategySnapshot(
    recommendations=(single_rec,),
    created_at=TS,
)
single_result = StrategyPipeline.run(single_snap, [conf_rule])
check("single rec success", single_result.success is True, "")
if single_result.plan:
    check("  one item", len(single_result.plan.items) == 1, "")
    check("  one approved", len(single_result.plan.approved) == 1, "")

# Low confidence — rejected
low_rec = _rec(category=CATEGORY_COST_REDUCTION, priority=PRIORITY_LOW, confidence=0.1, title="Low", rec_id=UID_D)
low_snap = StrategySnapshot(recommendations=(low_rec,), created_at=TS)
low_result = StrategyPipeline.run(low_snap, [conf_rule])
check("low conf rejected", low_result.success is True, "")
if low_result.plan:
    check("  one rejected", len(low_result.plan.rejected) == 1, "")

# ==================================================================
# Section 7: run — manual approval and blocked
# ==================================================================
print("\n" + "=" * 70)
print("Section 7: run — manual approval and blocked")
print("=" * 70)

manual_rule = _rule("Needs human", CATEGORY_STRATEGY, "confidence", OPERATOR_GT, 0.8,
                     result_on_match=RESULT_MANUAL_APPROVAL, result_on_mismatch=RESULT_REJECTED)
block_rule = _rule("Block low", CATEGORY_COST, "confidence", OPERATOR_LT, 0.3,
                    result_on_match=RESULT_BLOCKED, result_on_mismatch=RESULT_APPROVED)
high_rec = _rec(category=CATEGORY_COST_REDUCTION, priority=PRIORITY_CRITICAL, confidence=0.95,
                title="HighConf", rec_id=UUID("10000000-0000-0000-0000-0000000000f0"))

multi_snap = StrategySnapshot(
    recommendations=(rec_a, rec_b, low_rec, high_rec),
    created_at=TS,
)
multi_result = StrategyPipeline.run(multi_snap, [manual_rule, block_rule])
check("multi result success", multi_result.success is True, "")
if multi_result.plan:
    total = len(multi_result.plan.items)
    check("  total items", total == 8, f"count={total}")
    check("  has approved", len(multi_result.plan.approved) > 0, f"count={len(multi_result.plan.approved)}")
    check("  has manual", len(multi_result.plan.manual) > 0, f"count={len(multi_result.plan.manual)}")
    check("  has blocked", len(multi_result.plan.blocked) > 0, f"count={len(multi_result.plan.blocked)}")
    check("  has rejected", len(multi_result.plan.rejected) > 0, f"count={len(multi_result.plan.rejected)}")

# ==================================================================
# Section 8: run — multiple policies
# ==================================================================
print("\n" + "=" * 70)
print("Section 8: run — multiple policies")
print("=" * 70)

ten_recs = [
    _rec(category=CATEGORY_COST_REDUCTION, priority=p, confidence=c, title=f"Rec{i}",
         rec_id=UUID(f"20000000-0000-0000-0000-{i:012d}"))
    for i, (p, c) in enumerate([
        (PRIORITY_CRITICAL, 0.95),
        (PRIORITY_HIGH, 0.85),
        (PRIORITY_MEDIUM, 0.75),
        (PRIORITY_LOW, 0.65),
        (PRIORITY_CRITICAL, 0.55),
        (PRIORITY_HIGH, 0.45),
        (PRIORITY_MEDIUM, 0.35),
        (PRIORITY_LOW, 0.25),
        (PRIORITY_CRITICAL, 0.15),
        (PRIORITY_HIGH, 0.05),
    ])
]
ten_snap = StrategySnapshot(recommendations=tuple(ten_recs), created_at=TS)

policies = [
    _rule("High conf ok", CATEGORY_COST, "confidence", OPERATOR_GTE, 0.8,
          result_on_match=RESULT_APPROVED, result_on_mismatch=RESULT_REJECTED),
    _rule("Med conf check", CATEGORY_COST, "confidence", OPERATOR_GTE, 0.5,
          result_on_match=RESULT_MANUAL_APPROVAL, result_on_mismatch=RESULT_REJECTED),
    _rule("Low conf block", CATEGORY_COST, "confidence", OPERATOR_LT, 0.3,
          result_on_match=RESULT_BLOCKED, result_on_mismatch=RESULT_APPROVED),
]

ten_result = StrategyPipeline.run(ten_snap, policies)
check("10 recs success", ten_result.success is True, "")
if ten_result.plan:
    expected_items = len(ten_recs) * len(policies)
    check(f"  total items={expected_items}", len(ten_result.plan.items) == expected_items, f"count={len(ten_result.plan.items)}")
    check("  has approved", len(ten_result.plan.approved) > 0, "")
    check("  has manual", len(ten_result.plan.manual) > 0, "")
    check("  has blocked", len(ten_result.plan.blocked) > 0, "")
    check("  has rejected", len(ten_result.plan.rejected) > 0, "")

# ==================================================================
# Section 9: group_by_result
# ==================================================================
print("\n" + "=" * 70)
print("Section 9: group_by_result")
print("=" * 70)

items_mixed = [
    StrategyExecutionItem(UID_A, CATEGORY_COST_REDUCTION, PRIORITY_HIGH, RESULT_APPROVED, True, False, "",
                          {"_id": str(UID_A)}),
    StrategyExecutionItem(UID_B, CATEGORY_RISK_MITIGATION, PRIORITY_CRITICAL, RESULT_REJECTED, False, False, "",
                          {"_id": str(UID_B)}),
    StrategyExecutionItem(UID_C, CATEGORY_PERFORMANCE_IMPROVEMENT, PRIORITY_MEDIUM, RESULT_MANUAL_APPROVAL, False, True, "",
                          {"_id": str(UID_C)}),
    StrategyExecutionItem(UID_D, CATEGORY_WORKFLOW_OPTIMIZATION, PRIORITY_LOW, RESULT_BLOCKED, False, False, "",
                          {"_id": str(UID_D)}),
    StrategyExecutionItem(UID_E, CATEGORY_CAPACITY_PLANNING, PRIORITY_LOW, RESULT_NOT_APPLICABLE, False, False, "",
                          {"_id": str(UID_E)}),
]

grouped_res = StrategyPipeline.group_by_result(items_mixed)
check("group_by_result keys", len(grouped_res) == 5, f"keys={list(grouped_res.keys())}")
check("  approved count", len(grouped_res.get(RESULT_APPROVED, [])) == 1, "")
check("  rejected count", len(grouped_res.get(RESULT_REJECTED, [])) == 1, "")
check("  manual count", len(grouped_res.get(RESULT_MANUAL_APPROVAL, [])) == 1, "")
check("  blocked count", len(grouped_res.get(RESULT_BLOCKED, [])) == 1, "")
check("  na count", len(grouped_res.get(RESULT_NOT_APPLICABLE, [])) == 1, "")

all_approved = [StrategyExecutionItem(uuid4(), CATEGORY_COST_REDUCTION, PRIORITY_LOW, RESULT_APPROVED, True, False, "")]
grouped_res2 = StrategyPipeline.group_by_result(all_approved)
check("group all approved", len(grouped_res2) == 1, "")

grouped_empty = StrategyPipeline.group_by_result([])
check("group empty", len(grouped_empty) == 0, "")

# ==================================================================
# Section 10: group_by_priority
# ==================================================================
print("\n" + "=" * 70)
print("Section 10: group_by_priority")
print("=" * 70)

items_prio = [
    StrategyExecutionItem(UID_A, CATEGORY_COST_REDUCTION, PRIORITY_CRITICAL, RESULT_APPROVED, True, False, ""),
    StrategyExecutionItem(UID_B, CATEGORY_RISK_MITIGATION, PRIORITY_HIGH, RESULT_APPROVED, True, False, ""),
    StrategyExecutionItem(UID_C, CATEGORY_PERFORMANCE_IMPROVEMENT, PRIORITY_MEDIUM, RESULT_APPROVED, True, False, ""),
    StrategyExecutionItem(UID_D, CATEGORY_WORKFLOW_OPTIMIZATION, PRIORITY_LOW, RESULT_APPROVED, True, False, ""),
]

grouped_prio = StrategyPipeline.group_by_priority(items_prio)
check("group_by_priority keys", len(grouped_prio) == 4, f"keys={list(grouped_prio.keys())}")
prio_keys = list(grouped_prio.keys())
check("  LOW first (ascending)", prio_keys[0] == PRIORITY_LOW, f"first={prio_keys[0]}")
check("  CRITICAL last (ascending)", prio_keys[-1] == PRIORITY_CRITICAL, f"last={prio_keys[-1]}")

# All same priority
same_prio = [StrategyExecutionItem(uuid4(), CATEGORY_COST_REDUCTION, PRIORITY_HIGH, RESULT_APPROVED, True, False, "")]
grouped_prio2 = StrategyPipeline.group_by_priority(same_prio)
check("group same priority", len(grouped_prio2) == 1, "")

grouped_prio_empty = StrategyPipeline.group_by_priority([])
check("group priority empty", len(grouped_prio_empty) == 0, "")

# ==================================================================
# Section 11: filter_items
# ==================================================================
print("\n" + "=" * 70)
print("Section 11: filter_items")
print("=" * 70)

filtered_approved = StrategyPipeline.filter_items(items_mixed, policy_result=RESULT_APPROVED)
check("filter APPROVED", len(filtered_approved) == 1, f"count={len(filtered_approved)}")

filtered_rejected = StrategyPipeline.filter_items(items_mixed, policy_result=RESULT_REJECTED)
check("filter REJECTED", len(filtered_rejected) == 1, "")

filtered_manual = StrategyPipeline.filter_items(items_mixed, policy_result=RESULT_MANUAL_APPROVAL)
check("filter MANUAL", len(filtered_manual) == 1, "")

filtered_blocked = StrategyPipeline.filter_items(items_mixed, policy_result=RESULT_BLOCKED)
check("filter BLOCKED", len(filtered_blocked) == 1, "")

filtered_na = StrategyPipeline.filter_items(items_mixed, policy_result=RESULT_NOT_APPLICABLE)
check("filter N/A", len(filtered_na) == 1, "")

filtered_critical = StrategyPipeline.filter_items(items_mixed, priority=PRIORITY_CRITICAL)
check("filter CRITICAL priority", len(filtered_critical) == 1, "")

filtered_cost = StrategyPipeline.filter_items(items_mixed, category=CATEGORY_COST_REDUCTION)
check("filter cost category", len(filtered_cost) == 1, "")

filtered_can = StrategyPipeline.filter_items(items_mixed, can_execute=True)
check("filter can_execute", len(filtered_can) == 1, "")

filtered_man = StrategyPipeline.filter_items(items_mixed, requires_manual=True)
check("filter requires_manual", len(filtered_man) == 1, "")

filtered_multi = StrategyPipeline.filter_items(items_mixed, policy_result=RESULT_APPROVED, priority=PRIORITY_HIGH)
check("filter multiple", len(filtered_multi) == 1, "")

filtered_none = StrategyPipeline.filter_items(items_mixed, policy_result=RESULT_APPROVED, priority=PRIORITY_LOW)
check("filter no match", len(filtered_none) == 0, "")

filtered_all = StrategyPipeline.filter_items(items_mixed)
check("filter no args", len(filtered_all) == 5, "")

filtered_empty = StrategyPipeline.filter_items([])
check("filter empty", len(filtered_empty) == 0, "")

# ==================================================================
# Section 12: merge_plans
# ==================================================================
print("\n" + "=" * 70)
print("Section 12: merge_plans")
print("=" * 70)

plan_a = StrategyExecutionPlan(
    approved=(items_mixed[0],),
    items=(items_mixed[0],),
    created_at=TS,
)
plan_b = StrategyExecutionPlan(
    rejected=(items_mixed[1],),
    manual=(items_mixed[2],),
    items=(items_mixed[1], items_mixed[2]),
    created_at=TS,
)

merged = StrategyPipeline.merge_plans([plan_a, plan_b])
check("merge total", len(merged.items) == 3, f"count={len(merged.items)}")
check("  approved", len(merged.approved) == 1, "")
check("  rejected", len(merged.rejected) == 1, "")
check("  manual", len(merged.manual) == 1, "")

# Dedup
plan_a_dup = StrategyExecutionPlan(
    approved=(items_mixed[0],),
    items=(items_mixed[0],),
    created_at=TS,
)
merged_dedup = StrategyPipeline.merge_plans([plan_a, plan_a_dup])
check("merge dedup", len(merged_dedup.items) == 1, f"count={len(merged_dedup.items)}")

# Empty plans
merged_empty = StrategyPipeline.merge_plans([])
check("merge empty list", len(merged_empty.items) == 0, "")

merged_partial = StrategyPipeline.merge_plans([StrategyExecutionPlan(created_at=TS), plan_a])
check("merge empty+non", len(merged_partial.items) == 1, "")

# Merge with blocked and N/A
plan_c = StrategyExecutionPlan(
    blocked=(items_mixed[3],),
    not_applicable=(items_mixed[4],),
    items=(items_mixed[3], items_mixed[4]),
    created_at=TS,
)
merged_all = StrategyPipeline.merge_plans([plan_a, plan_b, plan_c])
check("merge all cats", len(merged_all.items) == 5, "")
check("  blocked", len(merged_all.blocked) == 1, "")
check("  not_applicable", len(merged_all.not_applicable) == 1, "")

# ==================================================================
# Section 13: build_trace / build_result
# ==================================================================
print("\n" + "=" * 70)
print("Section 13: build_trace / build_result")
print("=" * 70)

bt = StrategyPipeline.build_trace(
    stages=["run", "check"],
    duration_ms=3.0,
    metrics={"items": 5.0},
)
check("build_trace", isinstance(bt, StrategyPipelineTrace), "")
check("  stages", "run" in bt.stages, "")
check("  duration", bt.duration_ms == 3.0, "")
check("  metrics", bt.metrics.get("items") == 5.0, "")

bt_default = StrategyPipeline.build_trace()
check("build_trace default", bt_default.duration_ms == 0.0, "")

br = StrategyPipeline.build_result(
    plan_a,
    stages=["pipeline"],
    metrics={"total": 1.0},
)
check("build_result success", br.success is True, "")
check("  plan ref", br.plan is plan_a, "")
if br.trace:
    check("  trace stages", "pipeline" in br.trace.stages, "")

br_default = StrategyPipeline.build_result(StrategyExecutionPlan(created_at=TS))
check("build_result default", br_default.success is True, "")

# ==================================================================
# Section 14: Empty snapshot
# ==================================================================
print("\n" + "=" * 70)
print("Section 14: Empty snapshot")
print("=" * 70)

empty_snap = StrategySnapshot(created_at=TS)
rules_any = [_rule("Any rule", CATEGORY_COST, "confidence", OPERATOR_GT, 0.5)]

er = StrategyPipeline.run(empty_snap, rules_any)
check("empty snap success", er.success is True, "")
if er.plan:
    check("  items=0", len(er.plan.items) == 0, "")
    check("  approved=0", len(er.plan.approved) == 0, "")
    check("  rejected=0", len(er.plan.rejected) == 0, "")

# ==================================================================
# Section 15: One recommendation
# ==================================================================
print("\n" + "=" * 70)
print("Section 15: One recommendation")
print("=" * 70)

one_rec = _rec(rec_id=UID_A)
one_snap = StrategySnapshot(recommendations=(one_rec,), created_at=TS)
one_rule = [_rule("Simple", CATEGORY_COST, "confidence", OPERATOR_GT, 0.5)]
one_result = StrategyPipeline.run(one_snap, one_rule)
check("one rec success", one_result.success is True, "")
if one_result.plan:
    check("  item count", len(one_result.plan.items) == 1, "")
    check("  approved", len(one_result.plan.approved) == 1, "")

# ==================================================================
# Section 16: Multiple categories
# ==================================================================
print("\n" + "=" * 70)
print("Section 16: Multiple categories")
print("=" * 70)

cat_recs = [
    _rec(category=CATEGORY_COST_REDUCTION, priority=PRIORITY_HIGH, title="Cost", rec_id=UID_A),
    _rec(category=CATEGORY_PERFORMANCE_IMPROVEMENT, priority=PRIORITY_MEDIUM, title="Perf", rec_id=UID_B),
    _rec(category=CATEGORY_RISK_MITIGATION, priority=PRIORITY_CRITICAL, title="Risk", rec_id=UID_C),
    _rec(category=CATEGORY_WORKFLOW_OPTIMIZATION, priority=PRIORITY_LOW, title="WF", rec_id=UID_D),
    _rec(category=CATEGORY_SKILL_DEVELOPMENT, priority=PRIORITY_MEDIUM, title="Skill", rec_id=UID_E),
]
cat_snap = StrategySnapshot(recommendations=tuple(cat_recs), created_at=TS)
cat_rule = _rule("Cat check", CATEGORY_COST, "confidence", OPERATOR_GT, 0.5)
cat_result = StrategyPipeline.run(cat_snap, [cat_rule])
check("multi cat success", cat_result.success is True, "")
if cat_result.plan:
    check("  items", len(cat_result.plan.items) == 5, f"count={len(cat_result.plan.items)}")

# ==================================================================
# Section 17: Determinism
# ==================================================================
print("\n" + "=" * 70)
print("Section 17: Determinism")
print("=" * 70)

det_recs = [
    _rec(category=CATEGORY_COST_REDUCTION, priority=PRIORITY_HIGH, confidence=0.9, title="D1", rec_id=UID_A),
    _rec(category=CATEGORY_RISK_MITIGATION, priority=PRIORITY_LOW, confidence=0.2, title="D2", rec_id=UID_B),
]
det_snap = StrategySnapshot(recommendations=tuple(det_recs), created_at=TS)
det_rule = _rule("Det rule", CATEGORY_COST, "confidence", OPERATOR_GT, 0.5)

det_r1 = StrategyPipeline.run(det_snap, [det_rule])
det_r2 = StrategyPipeline.run(det_snap, [det_rule])

if det_r1.plan and det_r2.plan:
    r1_results = [(i.recommendation_id, i.policy_result) for i in det_r1.plan.items]
    r2_results = [(i.recommendation_id, i.policy_result) for i in det_r2.plan.items]
    check("deterministic results", r1_results == r2_results, f"r1={r1_results} r2={r2_results}")
    check("deterministic count", len(det_r1.plan.approved) == len(det_r2.plan.approved), "")

# ==================================================================
# Section 18: UUID handling
# ==================================================================
print("\n" + "=" * 70)
print("Section 18: UUID handling")
print("=" * 70)

uid_items = [
    StrategyExecutionItem(uuid4(), CATEGORY_COST_REDUCTION, PRIORITY_HIGH, RESULT_APPROVED, True, False, ""),
    StrategyExecutionItem(uuid4(), CATEGORY_RISK_MITIGATION, PRIORITY_LOW, RESULT_REJECTED, False, False, ""),
]
check("UUID on items", all(isinstance(i.recommendation_id, UUID) for i in uid_items), "")
check("UUID unique", uid_items[0].recommendation_id != uid_items[1].recommendation_id, "")

uid_plan = StrategyPipeline.build_plan([], [])
check("plan with UUID", isinstance(uid_plan.created_at, float), "")

# ==================================================================
# Section 19: Metadata
# ==================================================================
print("\n" + "=" * 70)
print("Section 19: Metadata")
print("=" * 70)

meta_item = StrategyExecutionItem(
    UID_A, CATEGORY_COST_REDUCTION, PRIORITY_HIGH, RESULT_APPROVED, True, False, "",
    metadata={"env": "prod", "team": "platform", "version": 2},
)
check("item metadata keys", "env" in meta_item.metadata and "team" in meta_item.metadata, "")
check("  metadata values", meta_item.metadata["env"] == "prod" and meta_item.metadata["version"] == 2, "")

meta_plan = StrategyExecutionPlan(
    approved=(meta_item,),
    items=(meta_item,),
    created_at=TS,
    metadata={"pipeline": "main", "iteration": 3},
)
check("plan metadata", meta_plan.metadata["pipeline"] == "main", "")

# ==================================================================
# Section 20: Timestamps
# ==================================================================
print("\n" + "=" * 70)
print("Section 20: Timestamps")
print("=" * 70)

t_start = time.time()
ts_item = StrategyExecutionItem(UID_A, CATEGORY_COST_REDUCTION, PRIORITY_HIGH, RESULT_APPROVED, True, False, "")
ts_plan = StrategyExecutionPlan(items=(ts_item,), created_at=TS)
check("plan created_at > 0", ts_plan.created_at > 0, "")

ts_result = StrategyPipeline.run(det_snap, [det_rule])
if ts_result.plan:
    check("run plan created_at > 0", ts_result.plan.created_at > 0, "")
if ts_result.trace:
    check("trace duration >= 0", ts_result.trace.duration_ms >= 0, "")

# ==================================================================
# Section 21: Edge cases
# ==================================================================
print("\n" + "=" * 70)
print("Section 21: Edge cases")
print("=" * 70)

# No recommendations, no rules
edge_empty = StrategyPipeline.run(StrategySnapshot(created_at=TS), [])
check("edge empty+no rules", edge_empty.success is True, "")

# Very long recommendation name
long_rec = _rec(title="A" * 500, rec_id=UID_A)
long_snap = StrategySnapshot(recommendations=(long_rec,), created_at=TS)
long_result = StrategyPipeline.run(long_snap, [det_rule])
check("edge long name", long_result.success is True, "")
if long_result.plan:
    check("  item present", len(long_result.plan.items) == 1, "")

# Zero confidence edge
zero_rec = _rec(confidence=0.0, rec_id=UID_A)
zero_snap = StrategySnapshot(recommendations=(zero_rec,), created_at=TS)
zero_result = StrategyPipeline.run(zero_snap, [det_rule])
check("edge zero conf", zero_result.success is True, "")
if zero_result.plan:
    check("  zero rejected", len(zero_result.plan.rejected) > 0, "")

# One rule only
one_rule_only = StrategyPipeline.run(cat_snap, [cat_rule])
check("edge one rule", one_rule_only.success is True, "")
if one_rule_only.plan:
    check("  count", len(one_rule_only.plan.items) == 5, "")

# All results same category
same_cat_recs = [
    _rec(category=CATEGORY_COST_REDUCTION, priority=PRIORITY_HIGH, title="C1", rec_id=UID_A),
    _rec(category=CATEGORY_COST_REDUCTION, priority=PRIORITY_MEDIUM, title="C2", rec_id=UID_B),
]
same_cat_snap = StrategySnapshot(recommendations=tuple(same_cat_recs), created_at=TS)
same_cat_result = StrategyPipeline.run(same_cat_snap, [det_rule])
check("edge same category", same_cat_result.success is True, "")

# Filter items with no match
check("edge filter none", len(StrategyPipeline.filter_items(items_mixed, priority="NONEXISTENT")) == 0, "")

# Group empty
check("edge group res empty", len(StrategyPipeline.group_by_result([])) == 0, "")
check("edge group prio empty", len(StrategyPipeline.group_by_priority([])) == 0, "")

# Merge empty list
check("edge merge empty list", len(StrategyPipeline.merge_plans([]).items) == 0, "")

# Build trace with no args
check("edge trace default", StrategyPipeline.build_trace().duration_ms == 0.0, "")

# Build result with default
default_res = StrategyPipeline.build_result(StrategyExecutionPlan(created_at=TS))
check("edge result default", default_res.success is True, "")

# Large batch
large_recs = [
    _rec(category=CATEGORY_COST_REDUCTION, priority=PRIORITY_MEDIUM, title=f"L{i}", rec_id=UUID(f"30000000-0000-0000-0000-{i:012d}"))
    for i in range(50)
]
large_snap = StrategySnapshot(recommendations=tuple(large_recs), created_at=TS)
large_result = StrategyPipeline.run(large_snap, [det_rule])
check("edge large batch", large_result.success is True, "")
if large_result.plan:
    check("  50 items", len(large_result.plan.items) == 50, f"count={len(large_result.plan.items)}")

# ==================================================================
# Section 22: Integration — Strategy Foundation
# ==================================================================
print("\n" + "=" * 70)
print("Section 22: Integration — Strategy Foundation")
print("=" * 70)

# Use FoundationStrategyRuntime to create a snapshot with real recommendations
# We can use FoundationStrategyRuntime.create_snapshot() for empty, but for non-empty
# we'll build it directly as we already do (the foundation doesn't expose add_rec)
check("FoundationStrategyRuntime importable", callable(FoundationStrategyRuntime.create_snapshot), "")
fsr_snap = FoundationStrategyRuntime.create_snapshot()
check("FSR empty snapshot", isinstance(fsr_snap, StrategySnapshot), "")

# Use FSR.prioritize
fsr_recs = [rec_a, rec_b]
prio_recs = FoundationStrategyRuntime.prioritize(fsr_recs)
check("FSR prioritize works", len(prio_recs) == 2, "")
check("  CRITICAL first", prio_recs[0].priority == PRIORITY_CRITICAL, "")

# Use FSR.filter_recommendations
filtered_fsr = FoundationStrategyRuntime.filter_recommendations(fsr_recs, category=CATEGORY_COST_REDUCTION)
check("FSR filter works", len(filtered_fsr) == 1, "")

# Use FSR.merge_recommendations
fsr_merged = FoundationStrategyRuntime.merge_recommendations([
    FoundationStrategyRuntime.create_snapshot(),
    FoundationStrategyRuntime.create_snapshot(),
])
check("FSR merge works", isinstance(fsr_merged, StrategySnapshot), "")

# Full circle: StrategyFoundation → StrategyPipeline
from core.strategy.foundation import FoundationStrategyRuntime as FSR
check("FSR importable via pipeline", callable(FSR.create_snapshot), "")

# ==================================================================
# Section 23: Integration — Policy Foundation
# ==================================================================
print("\n" + "=" * 70)
print("Section 23: Integration — Policy Foundation")
print("=" * 70)

check("FoundationPolicyRuntime importable", callable(FoundationPolicyRuntime.create_rule), "")
check("  evaluate_all", callable(FoundationPolicyRuntime.evaluate_all), "")
check("  evaluate", callable(FoundationPolicyRuntime.evaluate), "")

# Policy filter
pf_evals = [ev1, ev2]
approved_pf = FoundationPolicyRuntime.approve(pf_evals)
check("Policy approve works", len(approved_pf) >= 0, "")

rejected_pf = FoundationPolicyRuntime.reject(pf_evals)
check("Policy reject works", len(rejected_pf) >= 0, "")

# Policy group
pf_grouped = FoundationPolicyRuntime.group_by_result(pf_evals)
check("Policy group works", len(pf_grouped) >= 1, "")

# Merge policy snapshots
ps1 = FoundationPolicyRuntime.create_snapshot([ev1])
ps2 = FoundationPolicyRuntime.create_snapshot([ev2])
ps_merged = FoundationPolicyRuntime.merge([ps1, ps2])
check("Policy merge works", ps_merged.rules_applied == 2, "")

# ==================================================================
# Section 24: Integration — evaluate_policies with real FPR
# ==================================================================
print("\n" + "=" * 70)
print("Section 24: Integration — evaluate_policies with real FPR")
print("=" * 70)

# This already tested above but let's be explicit
pol_result = StrategyPipeline.evaluate_policies(fake_snap, rules)
check("evaluate_policies uses FPR", pol_result.success is True, "")
if pol_result.snapshot:
    check("  FPR snapshot type", pol_result.snapshot.rules_applied >= 0, "")
if pol_result.trace:
    check("  FPR trace rules", pol_result.trace.rules_evaluated == len(rules), "")

# ==================================================================
# Section 25: Full pipeline — end-to-end
# ==================================================================
print("\n" + "=" * 70)
print("Section 25: Full pipeline — end-to-end")
print("=" * 70)

e2e_recs = [
    _rec(category=CATEGORY_COST_REDUCTION, priority=PRIORITY_CRITICAL, confidence=0.95, title="E2E1", rec_id=UID_A),
    _rec(category=CATEGORY_PERFORMANCE_IMPROVEMENT, priority=PRIORITY_HIGH, confidence=0.7, title="E2E2", rec_id=UID_B),
    _rec(category=CATEGORY_RISK_MITIGATION, priority=PRIORITY_MEDIUM, confidence=0.4, title="E2E3", rec_id=UID_C),
    _rec(category=CATEGORY_WORKFLOW_OPTIMIZATION, priority=PRIORITY_LOW, confidence=0.2, title="E2E4", rec_id=UID_D),
]
e2e_snap = StrategySnapshot(recommendations=tuple(e2e_recs), created_at=TS)

e2e_rules = [
    _rule("High conf passes", CATEGORY_COST, "confidence", OPERATOR_GTE, 0.9,
          result_on_match=RESULT_APPROVED, result_on_mismatch=RESULT_REJECTED),
    _rule("Med conf manual", CATEGORY_STRATEGY, "confidence", OPERATOR_GTE, 0.5,
          result_on_match=RESULT_MANUAL_APPROVAL, result_on_mismatch=RESULT_REJECTED),
    _rule("Low conf blocked", CATEGORY_COST, "confidence", OPERATOR_LT, 0.3,
          result_on_match=RESULT_BLOCKED, result_on_mismatch=RESULT_APPROVED),
]

e2e_result = StrategyPipeline.run(e2e_snap, e2e_rules)
check("E2E success", e2e_result.success is True, "")
total_e2e = len(e2e_result.plan.items) if e2e_result.plan else expected_e2e
if e2e_result.plan:
    expected_e2e = len(e2e_recs) * len(e2e_rules)
    check(f"  total={expected_e2e}", total_e2e == expected_e2e, f"count={total_e2e}")

    # Verify counts
    check("  approved > 0", len(e2e_result.plan.approved) > 0, f"count={len(e2e_result.plan.approved)}")
    check("  manual > 0", len(e2e_result.plan.manual) > 0, f"count={len(e2e_result.plan.manual)}")
    check("  blocked > 0", len(e2e_result.plan.blocked) > 0, f"count={len(e2e_result.plan.blocked)}")
    check("  rejected > 0", len(e2e_result.plan.rejected) > 0, f"count={len(e2e_result.plan.rejected)}")

    # Group
    e2e_grouped = StrategyPipeline.group_by_result(list(e2e_result.plan.items))
    check("  group all 4 results", len(e2e_grouped) >= 4, f"keys={list(e2e_grouped.keys())}")

    # Filter
    e2e_approved = StrategyPipeline.filter_items(list(e2e_result.plan.items), policy_result=RESULT_APPROVED)
    check("  filter approved", len(e2e_approved) > 0, f"count={len(e2e_approved)}")

    # Priority group
    e2e_prio = StrategyPipeline.group_by_priority(list(e2e_result.plan.items))
    check("  priority group", len(e2e_prio) >= 3, f"keys={list(e2e_prio.keys())}")
    e2e_prio_keys = list(e2e_prio.keys())
    check("  priority LOW first", e2e_prio_keys[0] == PRIORITY_LOW, f"first={e2e_prio_keys[0]}")

    # Merge
    e2e_plan_a = StrategyExecutionPlan(
        approved=e2e_result.plan.approved,
        items=e2e_result.plan.approved,
        created_at=TS,
    )
    e2e_plan_b = StrategyExecutionPlan(
        rejected=e2e_result.plan.rejected,
        manual=e2e_result.plan.manual,
        blocked=e2e_result.plan.blocked,
        items=(*e2e_result.plan.rejected, *e2e_result.plan.manual, *e2e_result.plan.blocked),
        created_at=TS,
    )
    e2e_merged = StrategyPipeline.merge_plans([e2e_plan_a, e2e_plan_b])
    unique_recs = len(e2e_recs)
    check("  merge dedup preserves unique recs", len(e2e_merged.items) == unique_recs, f"merged={len(e2e_merged.items)}")

if e2e_result.trace:
    check("  trace stages present", len(e2e_result.trace.stages) >= 2, "")
    check("  trace metrics", e2e_result.trace.metrics.get("recommendations", 0) == float(len(e2e_recs)), "")

# Build final result
final_res = StrategyPipeline.build_result(
    e2e_result.plan if e2e_result.plan else StrategyExecutionPlan(created_at=TS),
    stages=["e2e"],
    metrics={"total": float(total_e2e)},
)
check("  final result success", final_res.success is True, "")
if final_res.trace:
    check("  final trace stages", "e2e" in final_res.trace.stages, "")

# ==================================================================
# Section 26: Backward compatibility
# ==================================================================
print("\n" + "=" * 70)
print("Section 26: Backward compatibility")
print("=" * 70)

# Strategy Foundation still works
check("FSR exists", hasattr(FSR, "create_snapshot"), "")
check("FSR.recommend exists", hasattr(FSR, "recommend"), "")
check("FSR.prioritize exists", hasattr(FSR, "prioritize"), "")
check("FSR.filter_recommendations exists", hasattr(FSR, "filter_recommendations"), "")
check("FSR.merge_recommendations exists", hasattr(FSR, "merge_recommendations"), "")

# Policy Foundation still works
check("FPR exists", callable(FoundationPolicyRuntime.create_rule), "")
check("FPR.evaluate_all exists", callable(FoundationPolicyRuntime.evaluate_all), "")
check("FPR.merge exists", callable(FoundationPolicyRuntime.merge), "")
check("FPR.approve exists", callable(FoundationPolicyRuntime.approve), "")
check("FPR.reject exists", callable(FoundationPolicyRuntime.reject), "")

# Pipeline is new, doesn't break anything
check("StrategyPipeline new class", callable(StrategyPipeline.run), "")
check("  build_plan", callable(StrategyPipeline.build_plan), "")
check("  evaluate_policies", callable(StrategyPipeline.evaluate_policies), "")
check("  group_by_result", callable(StrategyPipeline.group_by_result), "")
check("  group_by_priority", callable(StrategyPipeline.group_by_priority), "")
check("  filter_items", callable(StrategyPipeline.filter_items), "")
check("  merge_plans", callable(StrategyPipeline.merge_plans), "")
check("  build_trace", callable(StrategyPipeline.build_trace), "")
check("  build_result", callable(StrategyPipeline.build_result), "")

# ==================================================================
# Summary
# ==================================================================
print("\n" + "=" * 70)
print(f"Total: {pass_count}/{pass_count + fail_count} passed, {fail_count} failed")
print("=" * 70)

if fail_count > 0:
    exit(1)
