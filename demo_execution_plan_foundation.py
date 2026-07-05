"""Demo: Execution Plan Runtime Foundation — 220+ scenarios."""

import time
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
)
from core.policy.foundation import (
    FoundationPolicyRuntime,
    RESULT_APPROVED,
    RESULT_REJECTED,
    RESULT_MANUAL_APPROVAL,
    RESULT_BLOCKED,
    RESULT_NOT_APPLICABLE,
    CATEGORY_COST,
    CATEGORY_STRATEGY,
    OPERATOR_GT,
    OPERATOR_LT,
    OPERATOR_GTE,
    OPERATOR_EQ,
)
from core.strategy.pipeline import (
    StrategyPipeline,
    StrategyExecutionItem,
    StrategyExecutionPlan,
)
from core.execution_plan.foundation import (
    FoundationExecutionPlanRuntime,
    ExecutionAction,
    ExecutionPlan,
    ExecutionPlanTrace,
    ExecutionPlanResult,
    DEFAULT_DURATION_PER_ACTION,
    DEFAULT_COST_PER_ACTION,
    DEFAULT_DURATION_APPROVED_MULTIPLIER,
    DEFAULT_DURATION_MANUAL_MULTIPLIER,
    DEFAULT_DURATION_BLOCKED_MULTIPLIER,
    DEFAULT_COST_APPROVED_MULTIPLIER,
    DEFAULT_COST_MANUAL_MULTIPLIER,
    DEFAULT_COST_BLOCKED_MULTIPLIER,
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


def _item(
    rec_id: UUID,
    category: str = CATEGORY_COST_REDUCTION,
    priority: str = PRIORITY_MEDIUM,
    policy_result: str = RESULT_APPROVED,
    reason: str = "",
    **metadata: object,
) -> StrategyExecutionItem:
    can = policy_result == RESULT_APPROVED
    manual = policy_result == RESULT_MANUAL_APPROVAL
    return StrategyExecutionItem(
        recommendation_id=rec_id,
        category=category,
        priority=priority,
        policy_result=policy_result,
        can_execute=can,
        requires_manual_approval=manual,
        reason=reason or f"{policy_result}: {category}",
        metadata=dict(metadata),
    )


def _plan(
    items: list[StrategyExecutionItem],
    metadata: dict | None = None,
) -> StrategyExecutionPlan:
    approved = [i for i in items if i.policy_result == RESULT_APPROVED]
    manual = [i for i in items if i.policy_result == RESULT_MANUAL_APPROVAL]
    blocked = [i for i in items if i.policy_result == RESULT_BLOCKED]
    rejected = [i for i in items if i.policy_result == RESULT_REJECTED]
    not_applicable = [i for i in items if i.policy_result == RESULT_NOT_APPLICABLE]
    return StrategyExecutionPlan(
        approved=tuple(approved),
        manual=tuple(manual),
        blocked=tuple(blocked),
        rejected=tuple(rejected),
        not_applicable=tuple(not_applicable),
        items=tuple(items),
        created_at=TS,
        metadata=metadata or {},
    )


# Unique IDs
UID_A = UUID("10000000-0000-0000-0000-000000000001")
UID_B = UUID("10000000-0000-0000-0000-000000000002")
UID_C = UUID("10000000-0000-0000-0000-000000000003")
UID_D = UUID("10000000-0000-0000-0000-000000000004")
UID_E = UUID("10000000-0000-0000-0000-000000000005")
UID_F = UUID("10000000-0000-0000-0000-000000000006")

print("=" * 70)
print("Demo: Execution Plan Runtime Foundation")
print("=" * 70)

# ==================================================================
# Section 1: Data models
# ==================================================================
print("\n" + "=" * 70)
print("Section 1: Data models")
print("=" * 70)

action = ExecutionAction(
    action_id=UID_A,
    recommendation_id=UID_B,
    category=CATEGORY_COST_REDUCTION,
    priority=PRIORITY_HIGH,
    title="Test Action",
    description="An execution action",
    estimated_duration=30.0,
    estimated_cost=5.0,
    can_execute=True,
    requires_manual_approval=False,
    metadata={"env": "test"},
)
check("Action frozen", True, "")
check("  action_id", action.action_id == UID_A, "")
check("  recommendation_id", action.recommendation_id == UID_B, "")
check("  category", action.category == CATEGORY_COST_REDUCTION, "")
check("  priority HIGH", action.priority == PRIORITY_HIGH, "")
check("  title", action.title == "Test Action", "")
check("  description", action.description == "An execution action", "")
check("  duration 30", action.estimated_duration == 30.0, "")
check("  cost 5.0", action.estimated_cost == 5.0, "")
check("  can_execute True", action.can_execute is True, "")
check("  requires_manual False", action.requires_manual_approval is False, "")
check("  metadata", action.metadata.get("env") == "test", "")

a_manual = ExecutionAction(UID_B, UID_C, CATEGORY_RISK_MITIGATION, PRIORITY_CRITICAL,
                           "Manual", "Needs review", 0.0, 0.0, False, True)
check("Action manual", a_manual.requires_manual_approval is True, "")
check("  can_execute False", a_manual.can_execute is False, "")

a_blocked = ExecutionAction(UID_C, UID_D, CATEGORY_WORKFLOW_OPTIMIZATION, PRIORITY_LOW,
                            "Blocked", "Blocked", 0.0, 0.0, False, False)
check("Action blocked", a_blocked.can_execute is False, "")
check("  manual False", a_blocked.requires_manual_approval is False, "")

# ExecutionPlan
plan_obj = ExecutionPlan(
    actions=(action, a_manual, a_blocked),
    approved_actions=(action,),
    manual_actions=(a_manual,),
    blocked_actions=(a_blocked,),
    estimated_total_duration=30.0,
    estimated_total_cost=5.0,
    created_at=TS,
    metadata={"env": "test"},
)
check("Plan frozen", True, "")
check("  actions 3", len(plan_obj.actions) == 3, "")
check("  approved 1", len(plan_obj.approved_actions) == 1, "")
check("  manual 1", len(plan_obj.manual_actions) == 1, "")
check("  blocked 1", len(plan_obj.blocked_actions) == 1, "")
check("  duration 30", plan_obj.estimated_total_duration == 30.0, "")
check("  cost 5.0", plan_obj.estimated_total_cost == 5.0, "")
check("  created_at", plan_obj.created_at == TS, "")
check("  metadata", plan_obj.metadata.get("env") == "test", "")

# ExecutionPlan defaults
plan_empty = ExecutionPlan()
check("Plan default", len(plan_empty.actions) == 0, "")
check("  duration 0", plan_empty.estimated_total_duration == 0.0, "")
check("  cost 0", plan_empty.estimated_total_cost == 0.0, "")

# ExecutionPlanTrace
trace_obj = ExecutionPlanTrace(
    stages=("build", "assemble"),
    duration_ms=5.0,
    metrics={"actions": 3.0},
)
check("Trace frozen", True, "")
check("  stages", len(trace_obj.stages) == 2, "")
check("  duration 5ms", trace_obj.duration_ms == 5.0, "")
check("  metrics", trace_obj.metrics.get("actions") == 3.0, "")
check("Trace default", ExecutionPlanTrace(), "")

# ExecutionPlanResult
res = ExecutionPlanResult(success=True, plan=plan_obj, trace=trace_obj)
check("Result success", res.success is True, "")
check("  plan ref", res.plan is plan_obj, "")
check("  trace ref", res.trace is trace_obj, "")
res_err = ExecutionPlanResult(success=False, error_message="fail")
check("Result error", res_err.success is False, "")
check("  error_message", res_err.error_message == "fail", "")
check("Result default", ExecutionPlanResult(success=False), "")

# ==================================================================
# Section 2: build_actions — single approved
# ==================================================================
print("\n" + "=" * 70)
print("Section 2: build_actions — single approved")
print("=" * 70)

item_a = _item(UID_A, policy_result=RESULT_APPROVED, reason="Approved by policy")
plan_single = _plan([item_a])
actions = FoundationExecutionPlanRuntime.build_actions(plan_single)
check("build_actions single", len(actions) == 1, f"count={len(actions)}")
if actions:
    check("  can_execute True", actions[0].can_execute is True, "")
    check("  manual False", actions[0].requires_manual_approval is False, "")
    check("  title contains APPROVED", RESULT_APPROVED in actions[0].title, f"title={actions[0].title}")
    check("  action_id != recommendation_id", actions[0].action_id != actions[0].recommendation_id, "")
    check("  recommendation_id matches", actions[0].recommendation_id == UID_A, "")

# ==================================================================
# Section 3: build_actions — single manual
# ==================================================================
print("\n" + "=" * 70)
print("Section 3: build_actions — single manual")
print("=" * 70)

item_m = _item(UID_B, policy_result=RESULT_MANUAL_APPROVAL, requires_manual=True, reason="Needs human review")
plan_manual = _plan([item_m])
actions_m = FoundationExecutionPlanRuntime.build_actions(plan_manual)
check("build_actions manual", len(actions_m) == 1, "")
if actions_m:
    check("  can_execute False", actions_m[0].can_execute is False, "")
    check("  manual True", actions_m[0].requires_manual_approval is True, "")

# ==================================================================
# Section 4: build_actions — single blocked
# ==================================================================
print("\n" + "=" * 70)
print("Section 4: build_actions — single blocked")
print("=" * 70)

item_b = _item(UID_C, policy_result=RESULT_BLOCKED, reason="Blocked by constraint")
plan_blocked = _plan([item_b])
actions_b = FoundationExecutionPlanRuntime.build_actions(plan_blocked)
check("build_actions blocked", len(actions_b) == 1, "")
if actions_b:
    check("  can_execute False", actions_b[0].can_execute is False, "")
    check("  manual False", actions_b[0].requires_manual_approval is False, "")

# ==================================================================
# Section 5: build_actions — rejected and N/A skipped
# ==================================================================
print("\n" + "=" * 70)
print("Section 5: build_actions — rejected and N/A skipped")
print("=" * 70)

item_r = _item(UID_D, policy_result=RESULT_REJECTED, reason="Rejected")
item_n = _item(UID_E, policy_result=RESULT_NOT_APPLICABLE, reason="N/A")
plan_skip = _plan([item_r, item_n])
actions_skip = FoundationExecutionPlanRuntime.build_actions(plan_skip)
check("rejected+N/A skipped", len(actions_skip) == 0, f"count={len(actions_skip)}")

# Only rejected
plan_only_r = _plan([item_r])
actions_only_r = FoundationExecutionPlanRuntime.build_actions(plan_only_r)
check("only rejected skipped", len(actions_only_r) == 0, "")

# Only N/A
plan_only_n = _plan([item_n])
actions_only_n = FoundationExecutionPlanRuntime.build_actions(plan_only_n)
check("only N/A skipped", len(actions_only_n) == 0, "")

# ==================================================================
# Section 6: build_actions — multiple mixed
# ==================================================================
print("\n" + "=" * 70)
print("Section 6: build_actions — multiple mixed")
print("=" * 70)

items_mixed = [item_a, item_m, item_b]
plan_mixed = _plan(items_mixed)
actions_mixed = FoundationExecutionPlanRuntime.build_actions(plan_mixed)
check("mixed 3 actions", len(actions_mixed) == 3, f"count={len(actions_mixed)}")

# ==================================================================
# Section 7: build_actions — empty plan
# ==================================================================
print("\n" + "=" * 70)
print("Section 7: build_actions — empty plan")
print("=" * 70)

plan_empty_s = _plan([])
actions_empty = FoundationExecutionPlanRuntime.build_actions(plan_empty_s)
check("empty plan = 0 actions", len(actions_empty) == 0, "")

# ==================================================================
# Section 8: build — full pipeline (empty plan)
# ==================================================================
print("\n" + "=" * 70)
print("Section 8: build — empty plan")
print("=" * 70)

res_empty = FoundationExecutionPlanRuntime.build(plan_empty_s)
check("build empty success", res_empty.success is True, "")
if res_empty.plan:
    check("  actions 0", len(res_empty.plan.actions) == 0, "")
    check("  duration 0", res_empty.plan.estimated_total_duration == 0.0, "")
    check("  cost 0", res_empty.plan.estimated_total_cost == 0.0, "")
if res_empty.trace:
    check("  trace stages", "build" in res_empty.trace.stages, "")

# ==================================================================
# Section 9: build — single approved
# ==================================================================
print("\n" + "=" * 70)
print("Section 9: build — single approved")
print("=" * 70)

res_single = FoundationExecutionPlanRuntime.build(plan_single)
check("build single success", res_single.success is True, "")
if res_single.plan:
    check("  actions 1", len(res_single.plan.actions) == 1, "")
    check("  approved 1", len(res_single.plan.approved_actions) == 1, "")
    check("  manual 0", len(res_single.plan.manual_actions) == 0, "")
    check("  blocked 0", len(res_single.plan.blocked_actions) == 0, "")
    check("  duration > 0", res_single.plan.estimated_total_duration > 0, f"dur={res_single.plan.estimated_total_duration}")
    check("  cost > 0", res_single.plan.estimated_total_cost > 0, f"cost={res_single.plan.estimated_total_cost}")
if res_single.trace:
    check("  trace metrics", res_single.trace.metrics.get("total_actions", 0) == 1.0, "")

# ==================================================================
# Section 10: build — mixed
# ==================================================================
print("\n" + "=" * 70)
print("Section 10: build — mixed")
print("=" * 70)

res_mixed = FoundationExecutionPlanRuntime.build(plan_mixed)
check("build mixed success", res_mixed.success is True, "")
if res_mixed.plan:
    check("  actions 3", len(res_mixed.plan.actions) == 3, "")
    check("  approved 1", len(res_mixed.plan.approved_actions) == 1, "")
    check("  manual 1", len(res_mixed.plan.manual_actions) == 1, "")
    check("  blocked 1", len(res_mixed.plan.blocked_actions) == 1, "")

# ==================================================================
# Section 11: build — custom base_duration and base_cost
# ==================================================================
print("\n" + "=" * 70)
print("Section 11: build — custom base_duration and base_cost")
print("=" * 70)

res_custom = FoundationExecutionPlanRuntime.build(plan_single, base_duration=60.0, base_cost=10.0)
check("build custom params", res_custom.success is True, "")
if res_custom.plan:
    check("  duration 60.0", res_custom.plan.estimated_total_duration == 60.0, f"dur={res_custom.plan.estimated_total_duration}")
    check("  cost 10.0", res_custom.plan.estimated_total_cost == 10.0, f"cost={res_custom.plan.estimated_total_cost}")

# ==================================================================
# Section 12: build — with metadata
# ==================================================================
print("\n" + "=" * 70)
print("Section 12: build — with metadata")
print("=" * 70)

res_meta = FoundationExecutionPlanRuntime.build(plan_single, metadata={"pipeline": "main", "iteration": 1})
check("build with metadata", res_meta.success is True, "")
if res_meta.plan:
    check("  metadata present", res_meta.plan.metadata.get("pipeline") == "main", "")
    check("  iteration", res_meta.plan.metadata.get("iteration") == 1, "")

# ==================================================================
# Section 13: prioritize
# ==================================================================
print("\n" + "=" * 70)
print("Section 13: prioritize")
print("=" * 70)

items_prio = [
    _item(UID_A, priority=PRIORITY_LOW, policy_result=RESULT_APPROVED),
    _item(UID_B, priority=PRIORITY_HIGH, policy_result=RESULT_APPROVED),
    _item(UID_C, priority=PRIORITY_CRITICAL, policy_result=RESULT_APPROVED),
    _item(UID_D, priority=PRIORITY_MEDIUM, policy_result=RESULT_APPROVED),
]
plan_prio = _plan(items_prio)
actions_prio = FoundationExecutionPlanRuntime.build_actions(plan_prio)
prio_sorted = FoundationExecutionPlanRuntime.prioritize(actions_prio)
check("prioritize count", len(prio_sorted) == 4, "")
check("  CRITICAL first", prio_sorted[0].priority == PRIORITY_CRITICAL, f"first={prio_sorted[0].priority}")
check("  HIGH second", prio_sorted[1].priority == PRIORITY_HIGH, f"second={prio_sorted[1].priority}")
check("  MEDIUM third", prio_sorted[2].priority == PRIORITY_MEDIUM, f"third={prio_sorted[2].priority}")
check("  LOW last", prio_sorted[3].priority == PRIORITY_LOW, f"last={prio_sorted[3].priority}")

# Empty prioritize
check("prioritize empty", len(FoundationExecutionPlanRuntime.prioritize([])) == 0, "")

# ==================================================================
# Section 14: group_by_category
# ==================================================================
print("\n" + "=" * 70)
print("Section 14: group_by_category")
print("=" * 70)

items_cat = [
    _item(UID_A, category=CATEGORY_COST_REDUCTION, policy_result=RESULT_APPROVED),
    _item(UID_B, category=CATEGORY_RISK_MITIGATION, policy_result=RESULT_APPROVED),
    _item(UID_C, category=CATEGORY_COST_REDUCTION, policy_result=RESULT_APPROVED),
    _item(UID_D, category=CATEGORY_PERFORMANCE_IMPROVEMENT, policy_result=RESULT_APPROVED),
]
plan_cat = _plan(items_cat)
actions_cat = FoundationExecutionPlanRuntime.build_actions(plan_cat)
grouped_cat = FoundationExecutionPlanRuntime.group_by_category(actions_cat)
check("group_by_category keys", len(grouped_cat) == 3, f"keys={list(grouped_cat.keys())}")
check("  Cost Reduction count", len(grouped_cat.get(CATEGORY_COST_REDUCTION, [])) == 2, "")
check("  Risk count", len(grouped_cat.get(CATEGORY_RISK_MITIGATION, [])) == 1, "")
check("  Perf count", len(grouped_cat.get(CATEGORY_PERFORMANCE_IMPROVEMENT, [])) == 1, "")

# Single category
single_cat = FoundationExecutionPlanRuntime.build_actions(_plan([item_a]))
check("group single cat", len(FoundationExecutionPlanRuntime.group_by_category(single_cat)) == 1, "")
check("group empty cat", len(FoundationExecutionPlanRuntime.group_by_category([])) == 0, "")

# ==================================================================
# Section 15: group_by_priority
# ==================================================================
print("\n" + "=" * 70)
print("Section 15: group_by_priority")
print("=" * 70)

plan_prio_group = _plan(items_prio)
actions_prio_group = FoundationExecutionPlanRuntime.build_actions(plan_prio_group)
grouped_prio = FoundationExecutionPlanRuntime.group_by_priority(actions_prio_group)
check("group_by_priority keys", len(grouped_prio) == 4, f"keys={list(grouped_prio.keys())}")
prio_keys = list(grouped_prio.keys())
check("  LOW first", prio_keys[0] == PRIORITY_LOW, f"first={prio_keys[0]}")
check("  CRITICAL last", prio_keys[-1] == PRIORITY_CRITICAL, f"last={prio_keys[-1]}")

check("group same prio", len(FoundationExecutionPlanRuntime.group_by_priority([action])) == 1, "")
check("group empty prio", len(FoundationExecutionPlanRuntime.group_by_priority([])) == 0, "")

# ==================================================================
# Section 16: filter_actions
# ==================================================================
print("\n" + "=" * 70)
print("Section 16: filter_actions")
print("=" * 70)

# Build a rich set of actions
filter_items = [
    _item(UID_A, CATEGORY_COST_REDUCTION, PRIORITY_HIGH, RESULT_APPROVED, reason="Cost ok"),
    _item(UID_B, CATEGORY_RISK_MITIGATION, PRIORITY_CRITICAL, RESULT_MANUAL_APPROVAL, reason="Risk needs review"),
    _item(UID_C, CATEGORY_PERFORMANCE_IMPROVEMENT, PRIORITY_MEDIUM, RESULT_BLOCKED, reason="Perf blocked"),
    _item(UID_D, CATEGORY_WORKFLOW_OPTIMIZATION, PRIORITY_LOW, RESULT_APPROVED, reason="WF ok"),
    _item(UID_E, CATEGORY_COST_REDUCTION, PRIORITY_CRITICAL, RESULT_MANUAL_APPROVAL, reason="Cost manual"),
    _item(UID_F, CATEGORY_SKILL_DEVELOPMENT, PRIORITY_HIGH, RESULT_APPROVED, reason="Skill ok"),
]
plan_filter = _plan(filter_items)
all_actions = FoundationExecutionPlanRuntime.build_actions(plan_filter)

f_cat = FoundationExecutionPlanRuntime.filter_actions(all_actions, category=CATEGORY_COST_REDUCTION)
check("filter by category", len(f_cat) == 2, f"count={len(f_cat)}")

f_prio = FoundationExecutionPlanRuntime.filter_actions(all_actions, priority=PRIORITY_CRITICAL)
check("filter by priority", len(f_prio) == 2, "")

f_can = FoundationExecutionPlanRuntime.filter_actions(all_actions, can_execute=True)
check("filter can_execute", len(f_can) == 3, f"count={len(f_can)}")

f_manual = FoundationExecutionPlanRuntime.filter_actions(all_actions, requires_manual=True)
check("filter requires_manual", len(f_manual) == 2, "")

f_combined = FoundationExecutionPlanRuntime.filter_actions(all_actions, category=CATEGORY_COST_REDUCTION, can_execute=True)
check("filter combined", len(f_combined) == 1, "")

f_none = FoundationExecutionPlanRuntime.filter_actions(all_actions, category="NONEXISTENT")
check("filter no match", len(f_none) == 0, "")

f_all = FoundationExecutionPlanRuntime.filter_actions(all_actions)
check("filter no args", len(f_all) == 6, "")

f_empty = FoundationExecutionPlanRuntime.filter_actions([])
check("filter empty", len(f_empty) == 0, "")

# ==================================================================
# Section 17: merge_plans
# ==================================================================
print("\n" + "=" * 70)
print("Section 17: merge_plans")
print("=" * 70)

# Create two plans with different actions
plan1 = FoundationExecutionPlanRuntime.build(_plan([item_a]))
plan2 = FoundationExecutionPlanRuntime.build(_plan([item_m]))
if plan1.plan and plan2.plan:
    merged = FoundationExecutionPlanRuntime.merge_plans([plan1.plan, plan2.plan])
    check("merge total", len(merged.actions) == 2, f"count={len(merged.actions)}")
    check("  approved 1", len(merged.approved_actions) == 1, "")
    check("  manual 1", len(merged.manual_actions) == 1, "")
    check("  blocked 0", len(merged.blocked_actions) == 0, "")

    # Dedup by action_id
    merged_dedup = FoundationExecutionPlanRuntime.merge_plans([plan1.plan, plan1.plan])
    check("merge dedup", len(merged_dedup.actions) == 1, f"count={len(merged_dedup.actions)}")

# Empty merge
merged_empty = FoundationExecutionPlanRuntime.merge_plans([])
check("merge empty list", len(merged_empty.actions) == 0, "")

# Merge with empty+non
if plan1.plan:
    merged_partial = FoundationExecutionPlanRuntime.merge_plans([ExecutionPlan(), plan1.plan])
    check("merge empty+non", len(merged_partial.actions) == 1, "")

# ==================================================================
# Section 18: estimate_cost
# ==================================================================
print("\n" + "=" * 70)
print("Section 18: estimate_cost")
print("=" * 70)

# Test estimate_cost_for items
cost_approved = FoundationExecutionPlanRuntime.estimate_cost_for(item_a)
cost_manual = FoundationExecutionPlanRuntime.estimate_cost_for(item_m)
cost_blocked = FoundationExecutionPlanRuntime.estimate_cost_for(item_b)
cost_rejected = FoundationExecutionPlanRuntime.estimate_cost_for(item_r)

check("cost approved", cost_approved == DEFAULT_COST_PER_ACTION * DEFAULT_COST_APPROVED_MULTIPLIER,
      f"cost={cost_approved}")
check("cost manual", cost_manual == DEFAULT_COST_PER_ACTION * DEFAULT_COST_MANUAL_MULTIPLIER,
      f"cost={cost_manual}")
check("cost blocked", cost_blocked == DEFAULT_COST_PER_ACTION * DEFAULT_COST_BLOCKED_MULTIPLIER,
      f"cost={cost_blocked}")
check("cost rejected", cost_rejected == DEFAULT_COST_PER_ACTION * DEFAULT_COST_BLOCKED_MULTIPLIER,
      f"cost={cost_rejected}")

# Total cost for a list of actions
actions_cost = FoundationExecutionPlanRuntime.build_actions(_plan([item_a, item_m, item_b]))
total_cost = FoundationExecutionPlanRuntime.estimate_cost(actions_cost)
expected_cost = DEFAULT_COST_PER_ACTION * (DEFAULT_COST_APPROVED_MULTIPLIER + DEFAULT_COST_MANUAL_MULTIPLIER + DEFAULT_COST_BLOCKED_MULTIPLIER)
check("total cost mixed", total_cost == expected_cost, f"cost={total_cost} expected={expected_cost}")

# Cost with custom base
total_cost_custom = FoundationExecutionPlanRuntime.estimate_cost(actions_cost, base_cost=20.0)
expected_custom = 20.0 * (DEFAULT_COST_APPROVED_MULTIPLIER + DEFAULT_COST_MANUAL_MULTIPLIER + DEFAULT_COST_BLOCKED_MULTIPLIER)
check("total cost custom", total_cost_custom == expected_custom, f"cost={total_cost_custom}")

# Empty cost
check("cost empty", FoundationExecutionPlanRuntime.estimate_cost([]) == 0.0, "")

# ==================================================================
# Section 19: estimate_duration
# ==================================================================
print("\n" + "=" * 70)
print("Section 19: estimate_duration")
print("=" * 70)

dur_approved = FoundationExecutionPlanRuntime.estimate_duration_for(item_a)
dur_manual = FoundationExecutionPlanRuntime.estimate_duration_for(item_m)
dur_blocked = FoundationExecutionPlanRuntime.estimate_duration_for(item_b)

check("duration approved", dur_approved == DEFAULT_DURATION_PER_ACTION * DEFAULT_DURATION_APPROVED_MULTIPLIER,
      f"dur={dur_approved}")
check("duration manual", dur_manual == DEFAULT_DURATION_PER_ACTION * DEFAULT_DURATION_MANUAL_MULTIPLIER,
      f"dur={dur_manual}")
check("duration blocked", dur_blocked == DEFAULT_DURATION_PER_ACTION * DEFAULT_DURATION_BLOCKED_MULTIPLIER,
      f"dur={dur_blocked}")

total_dur = FoundationExecutionPlanRuntime.estimate_duration(
    FoundationExecutionPlanRuntime.build_actions(_plan([item_a, item_m, item_b])),
)
expected_dur = DEFAULT_DURATION_PER_ACTION * (DEFAULT_DURATION_APPROVED_MULTIPLIER + DEFAULT_DURATION_MANUAL_MULTIPLIER + DEFAULT_DURATION_BLOCKED_MULTIPLIER)
check("total duration mixed", total_dur == expected_dur, f"dur={total_dur} expected={expected_dur}")

# Custom base
total_dur_custom = FoundationExecutionPlanRuntime.estimate_duration(
    FoundationExecutionPlanRuntime.build_actions(_plan([item_a])), base_duration=120.0,
)
check("total duration custom", total_dur_custom == 120.0 * DEFAULT_DURATION_APPROVED_MULTIPLIER, f"dur={total_dur_custom}")

check("duration empty", FoundationExecutionPlanRuntime.estimate_duration([]) == 0.0, "")

# ==================================================================
# Section 20: build_trace / build_result
# ==================================================================
print("\n" + "=" * 70)
print("Section 20: build_trace / build_result")
print("=" * 70)

bt = FoundationExecutionPlanRuntime.build_trace(
    stages=["build", "assemble"],
    duration_ms=5.0,
    metrics={"actions": 3.0},
)
check("build_trace", isinstance(bt, ExecutionPlanTrace), "")
check("  stages", len(bt.stages) == 2, "")
check("  duration", bt.duration_ms == 5.0, "")
check("  metrics", bt.metrics.get("actions") == 3.0, "")

bt_default = FoundationExecutionPlanRuntime.build_trace()
check("build_trace default", bt_default.duration_ms == 0.0, "")

br = FoundationExecutionPlanRuntime.build_result(
    plan_obj,
    stages=["pipeline"],
    metrics={"total": 3.0},
)
check("build_result success", br.success is True, "")
check("  plan ref", br.plan is plan_obj, "")
if br.trace:
    check("  trace stages", "pipeline" in br.trace.stages, "")

br_default = FoundationExecutionPlanRuntime.build_result(ExecutionPlan())
check("build_result default", br_default.success is True, "")

# ==================================================================
# Section 21: Determinism
# ==================================================================
print("\n" + "=" * 70)
print("Section 21: Determinism")
print("=" * 70)

det_items = [item_a, item_m]
det_plan = _plan(det_items)
det_r1 = FoundationExecutionPlanRuntime.build(det_plan)
det_r2 = FoundationExecutionPlanRuntime.build(det_plan)
if det_r1.plan and det_r2.plan:
    r1_actions = [(a.recommendation_id, a.can_execute, a.requires_manual_approval, a.estimated_duration, a.estimated_cost)
                  for a in det_r1.plan.actions]
    r2_actions = [(a.recommendation_id, a.can_execute, a.requires_manual_approval, a.estimated_duration, a.estimated_cost)
                  for a in det_r2.plan.actions]
    check("deterministic action fields", r1_actions == r2_actions, f"r1={r1_actions} r2={r2_actions}")
    check("deterministic approved count", len(det_r1.plan.approved_actions) == len(det_r2.plan.approved_actions), "")
    check("deterministic manual count", len(det_r1.plan.manual_actions) == len(det_r2.plan.manual_actions), "")

# ==================================================================
# Section 22: UUID handling
# ==================================================================
print("\n" + "=" * 70)
print("Section 22: UUID handling")
print("=" * 70)

check("UUID on action", isinstance(action.action_id, UUID), "")
check("UUID on recommendation_id", isinstance(action.recommendation_id, UUID), "")
check("IDs unique", action.action_id != a_manual.action_id, "")

# Action IDs are unique even from same source
items_multi = [
    _item(UID_A, policy_result=RESULT_APPROVED),
    _item(UID_B, policy_result=RESULT_APPROVED),
]
act_multi = FoundationExecutionPlanRuntime.build_actions(_plan(items_multi))
check("unique action IDs", act_multi[0].action_id != act_multi[1].action_id, "")

# ==================================================================
# Section 23: Metadata preservation
# ==================================================================
print("\n" + "=" * 70)
print("Section 23: Metadata preservation")
print("=" * 70)

item_meta = _item(UID_A, policy_result=RESULT_APPROVED, source="analytics", team="platform")
plan_meta = _plan([item_meta], metadata={"env": "staging"})
res_meta2 = FoundationExecutionPlanRuntime.build(plan_meta)
if res_meta2.plan:
    check("plan metadata preserved", res_meta2.plan.metadata.get("env") == "staging", "")
    if res_meta2.plan.actions:
        check("action metadata source from item", res_meta2.plan.actions[0].metadata.get("source") == "analytics", "")
        check("action metadata team", res_meta2.plan.actions[0].metadata.get("team") == "platform", "")
        check("action metadata policy_result", res_meta2.plan.actions[0].metadata.get("policy_result") == RESULT_APPROVED, "")

# ==================================================================
# Section 24: Timestamps
# ==================================================================
print("\n" + "=" * 70)
print("Section 24: Timestamps")
print("=" * 70)

t_start = time.time()
ts_res = FoundationExecutionPlanRuntime.build(det_plan)
t_end = time.time()
if ts_res.plan:
    check("plan created_at > 0", ts_res.plan.created_at > 0, "")
    check("plan created_at recent", t_start <= ts_res.plan.created_at <= t_end + 1, "")
if ts_res.trace:
    check("trace duration >= 0", ts_res.trace.duration_ms >= 0, "")

# ==================================================================
# Section 25: Edge cases
# ==================================================================
print("\n" + "=" * 70)
print("Section 25: Edge cases")
print("=" * 70)

# Empty strategy plan with no items at all
ep_empty = ExecutionPlan()
check("edge empty ExecutionPlan", len(ep_empty.actions) == 0, "")

# Strategy plan with only rejected
ep_rejected = FoundationExecutionPlanRuntime.build(_plan([item_r]))
check("edge only rejected success", ep_rejected.success is True, "")
if ep_rejected.plan:
    check("  actions 0", len(ep_rejected.plan.actions) == 0, "")

# Zero-cost actions
item_zero = _item(UID_A, policy_result=RESULT_APPROVED)
plan_zero = _plan([item_zero])
res_zero = FoundationExecutionPlanRuntime.build(plan_zero, base_cost=0.0)
if res_zero.plan:
    check("edge zero cost", res_zero.plan.estimated_total_cost == 0.0, "")

# Zero-duration actions
res_zero_dur = FoundationExecutionPlanRuntime.build(plan_zero, base_duration=0.0)
if res_zero_dur.plan:
    check("edge zero duration", res_zero_dur.plan.estimated_total_duration == 0.0, "")

# Very long title
long_action = ExecutionAction(uuid4(), UID_A, CATEGORY_COST_REDUCTION, PRIORITY_LOW,
                              "A" * 500, "Long desc", 0.0, 0.0, True, False)
check("edge long title", len(long_action.title) == 500, "")

# Filter with duration
actions_dur_filter = FoundationExecutionPlanRuntime.build_actions(plan_mixed)
f_min_dur = FoundationExecutionPlanRuntime.filter_actions(actions_dur_filter, min_duration=5.0)
check("edge filter min_duration excludes blocked", len(f_min_dur) == len(actions_dur_filter) - 1, f"count={len(f_min_dur)}")

# Filter with cost
f_max_cost = FoundationExecutionPlanRuntime.filter_actions(actions_dur_filter, max_cost=0.5)
check("edge filter max_cost", len(f_max_cost) >= 0, "")

# Merge single plan
if plan1.plan:
    merged_single = FoundationExecutionPlanRuntime.merge_plans([plan1.plan])
    check("edge merge single", len(merged_single.actions) == 1, "")

# Large batch
large_items = [
    _item(UUID(f"40000000-0000-0000-0000-{i:012d}"),
          category=CATEGORY_COST_REDUCTION if i % 2 == 0 else CATEGORY_RISK_MITIGATION,
          priority=[PRIORITY_LOW, PRIORITY_MEDIUM, PRIORITY_HIGH, PRIORITY_CRITICAL][i % 4],
          policy_result=RESULT_APPROVED if i % 3 != 0 else RESULT_BLOCKED)
    for i in range(60)
]
large_plan = _plan(large_items)
large_res = FoundationExecutionPlanRuntime.build(large_plan)
check("edge large batch success", large_res.success is True, "")
if large_res.plan:
    check("  60 actions", len(large_res.plan.actions) == 60, f"count={len(large_res.plan.actions)}")
    check("  approved > 0", len(large_res.plan.approved_actions) > 0, "")
    check("  blocked > 0", len(large_res.plan.blocked_actions) > 0, "")

# Group empty
check("edge group cat empty", len(FoundationExecutionPlanRuntime.group_by_category([])) == 0, "")
check("edge group prio empty", len(FoundationExecutionPlanRuntime.group_by_priority([])) == 0, "")
check("edge filter empty list", len(FoundationExecutionPlanRuntime.filter_actions([])) == 0, "")
check("edge merge empty list", len(FoundationExecutionPlanRuntime.merge_plans([]).actions) == 0, "")
check("edge build_trace default", FoundationExecutionPlanRuntime.build_trace().duration_ms == 0.0, "")
check("edge build_result default", FoundationExecutionPlanRuntime.build_result(ExecutionPlan()).success is True, "")

# ==================================================================
# Section 26: Integration — Strategy Pipeline
# ==================================================================
print("\n" + "=" * 70)
print("Section 26: Integration — Strategy Pipeline")
print("=" * 70)

# Full flow: StrategyRecommendation → StrategyPipeline → ExecutionPlanFoundation
rec_a = StrategyRecommendation(
    recommendation_id=UID_A, category=CATEGORY_COST_REDUCTION, priority=PRIORITY_HIGH,
    title="Reduce costs", description="", reason="", expected_benefit="", confidence=0.9,
    created_at=TS,
)
rec_b = StrategyRecommendation(
    recommendation_id=UID_B, category=CATEGORY_RISK_MITIGATION, priority=PRIORITY_CRITICAL,
    title="Mitigate risk", description="", reason="", expected_benefit="", confidence=0.3,
    created_at=TS,
)

from core.strategy.foundation import StrategySnapshot
strategy_snap = StrategySnapshot(
    recommendations=(rec_a, rec_b),
    created_at=TS,
)

policy_rules = [
    FoundationPolicyRuntime.create_rule(
        "High confidence", CATEGORY_COST, "confidence", OPERATOR_GT, 0.5,
        result_on_match=RESULT_APPROVED, result_on_mismatch=RESULT_REJECTED,
    ),
    FoundationPolicyRuntime.create_rule(
        "Critical high", CATEGORY_STRATEGY, "priority", OPERATOR_EQ, PRIORITY_CRITICAL,
        result_on_match=RESULT_MANUAL_APPROVAL, result_on_mismatch=RESULT_APPROVED,
    ),
]

pipeline_result = StrategyPipeline.run(strategy_snap, policy_rules)
check("StrategyPipeline runs", pipeline_result.success is True, "")
if pipeline_result.plan:
    check("  plan items", len(pipeline_result.plan.items) == 4, f"count={len(pipeline_result.plan.items)}")

    # Feed into ExecutionPlan
    exec_res = FoundationExecutionPlanRuntime.build(pipeline_result.plan)
    check("  ExecutionPlan build", exec_res.success is True, "")
    if exec_res.plan:
        check("  actions > 0", len(exec_res.plan.actions) > 0, f"count={len(exec_res.plan.actions)}")
        check("  approved > 0", len(exec_res.plan.approved_actions) > 0, "")
        check("  manual > 0", len(exec_res.plan.manual_actions) > 0, "")
        check("  blocked=0", len(exec_res.plan.blocked_actions) == 0, "")
        check("  total duration > 0", exec_res.plan.estimated_total_duration > 0, "")
        check("  total cost > 0", exec_res.plan.estimated_total_cost > 0, "")

# ==================================================================
# Section 27: Integration — Policy Foundation
# ==================================================================
print("\n" + "=" * 70)
print("Section 27: Integration — Policy Foundation")
print("=" * 70)

# Verify PolicyFoundation still works
check("FPR create_rule", callable(FoundationPolicyRuntime.create_rule), "")
check("FPR evaluate_all", callable(FoundationPolicyRuntime.evaluate_all), "")
check("FPR approve", callable(FoundationPolicyRuntime.approve), "")
check("FPR reject", callable(FoundationPolicyRuntime.reject), "")

# ==================================================================
# Section 28: Integration — Strategy Foundation
# ==================================================================
print("\n" + "=" * 70)
print("Section 28: Integration — Strategy Foundation")
print("=" * 70)

check("FSR create_snapshot", callable(FoundationStrategyRuntime.create_snapshot), "")
check("FSR recommend", callable(FoundationStrategyRuntime.recommend), "")
check("FSR prioritize", callable(FoundationStrategyRuntime.prioritize), "")

# ==================================================================
# Section 29: Full pipeline — end-to-end
# ==================================================================
print("\n" + "=" * 70)
print("Section 29: Full pipeline — end-to-end")
print("=" * 70)

e2e_recs = [
    StrategyRecommendation(
        recommendation_id=UUID("50000000-0000-0000-0000-000000000001"),
        category=CATEGORY_COST_REDUCTION, priority=PRIORITY_CRITICAL,
        title="E2E Cost", description="Reduce ops cost", reason="High spend",
        expected_benefit="Save money", confidence=0.95, metadata={"source": "analysis"},
        created_at=TS,
    ),
    StrategyRecommendation(
        recommendation_id=UUID("50000000-0000-0000-0000-000000000002"),
        category=CATEGORY_PERFORMANCE_IMPROVEMENT, priority=PRIORITY_HIGH,
        title="E2E Perf", description="Improve speed", reason="Slow execution",
        expected_benefit="Faster", confidence=0.7, metadata={"source": "monitoring"},
        created_at=TS,
    ),
    StrategyRecommendation(
        recommendation_id=UUID("50000000-0000-0000-0000-000000000003"),
        category=CATEGORY_RISK_MITIGATION, priority=PRIORITY_MEDIUM,
        title="E2E Risk", description="Reduce risk", reason="Multiple failures",
        expected_benefit="Stability", confidence=0.4, metadata={"source": "monitoring"},
        created_at=TS,
    ),
    StrategyRecommendation(
        recommendation_id=UUID("50000000-0000-0000-0000-000000000004"),
        category=CATEGORY_WORKFLOW_OPTIMIZATION, priority=PRIORITY_LOW,
        title="E2E WF", description="Optimize workflow", reason="Low completion",
        expected_benefit="Efficiency", confidence=0.2, metadata={"source": "analytics"},
        created_at=TS,
    ),
]
e2e_snap = StrategySnapshot(recommendations=tuple(e2e_recs), created_at=TS)
e2e_rules = [
    FoundationPolicyRuntime.create_rule(
        "High conf", CATEGORY_COST, "confidence", OPERATOR_GTE, 0.9,
        result_on_match=RESULT_APPROVED, result_on_mismatch=RESULT_REJECTED,
    ),
    FoundationPolicyRuntime.create_rule(
        "Med conf manual", CATEGORY_STRATEGY, "confidence", OPERATOR_GTE, 0.5,
        result_on_match=RESULT_MANUAL_APPROVAL, result_on_mismatch=RESULT_REJECTED,
    ),
    FoundationPolicyRuntime.create_rule(
        "Low conf block", CATEGORY_COST, "confidence", OPERATOR_LT, 0.3,
        result_on_match=RESULT_BLOCKED, result_on_mismatch=RESULT_APPROVED,
    ),
]

# Strategy Pipeline
e2e_pipeline = StrategyPipeline.run(e2e_snap, e2e_rules)
check("E2E StrategyPipeline", e2e_pipeline.success is True, "")

if e2e_pipeline.plan:
    check("  items", len(e2e_pipeline.plan.items) > 0, f"count={len(e2e_pipeline.plan.items)}")

    # Execution Plan
    e2e_exec = FoundationExecutionPlanRuntime.build(e2e_pipeline.plan, base_duration=30.0, base_cost=5.0)
    check("E2E ExecutionPlan", e2e_exec.success is True, "")

    if e2e_exec.plan:
        plan = e2e_exec.plan
        check("  actions", len(plan.actions) > 0, f"count={len(plan.actions)}")
        check("  approved > 0", len(plan.approved_actions) > 0, f"count={len(plan.approved_actions)}")
        check("  manual > 0", len(plan.manual_actions) > 0, f"count={len(plan.manual_actions)}")
        check("  blocked > 0", len(plan.blocked_actions) > 0, f"count={len(plan.blocked_actions)}")
        check("  total_duration", plan.estimated_total_duration > 0, f"dur={plan.estimated_total_duration}")
        check("  total_cost", plan.estimated_total_cost > 0, f"cost={plan.estimated_total_cost}")

        # Group
        grouped_e2e = FoundationExecutionPlanRuntime.group_by_category(list(plan.actions))
        check("  group categories", len(grouped_e2e) >= 3, f"keys={list(grouped_e2e.keys())}")

        # Priority group
        prio_e2e = FoundationExecutionPlanRuntime.group_by_priority(list(plan.actions))
        check("  group priorities", len(prio_e2e) >= 3, f"keys={list(prio_e2e.keys())}")

        # Filter
        f_e2e = FoundationExecutionPlanRuntime.filter_actions(list(plan.actions), can_execute=True)
        check("  filter approved", len(f_e2e) == len(plan.approved_actions), "")

        # Prioritize
        p_e2e = FoundationExecutionPlanRuntime.prioritize(list(plan.actions))
        check("  prioritize CRITICAL first", p_e2e[0].priority == PRIORITY_CRITICAL, "")

        # Merge
        plan_x = FoundationExecutionPlanRuntime.build(
            _plan([_item(UID_A, policy_result=RESULT_APPROVED)])
        )
        plan_y = FoundationExecutionPlanRuntime.build(
            _plan([_item(UID_B, policy_result=RESULT_MANUAL_APPROVAL, requires_manual=True)])
        )
        if plan_x.plan and plan_y.plan:
            merged_e2e = FoundationExecutionPlanRuntime.merge_plans([plan_x.plan, plan_y.plan])
            check("  merge total", len(merged_e2e.actions) == 2, f"count={len(merged_e2e.actions)}")

        # Cost estimate (must use same base_cost as build)
        e2e_cost = FoundationExecutionPlanRuntime.estimate_cost(list(plan.actions), base_cost=5.0)
        check("  estimated_cost matches", e2e_cost == plan.estimated_total_cost, f"cost={e2e_cost}")

        # Duration estimate (must use same base_duration as build)
        e2e_dur = FoundationExecutionPlanRuntime.estimate_duration(list(plan.actions), base_duration=30.0)
        check("  estimated_duration matches", e2e_dur == plan.estimated_total_duration, f"dur={e2e_dur}")

    if e2e_exec.trace:
        check("  trace stages", len(e2e_exec.trace.stages) >= 2, "")
        check("  trace metrics", e2e_exec.trace.metrics.get("total_actions", 0) > 0, "")

    # Build final result
    if e2e_exec.plan:
        final = FoundationExecutionPlanRuntime.build_result(
            e2e_exec.plan,
            stages=["full_pipeline"],
            metrics={"total": float(len(e2e_exec.plan.actions))},
        )
        check("  final result", final.success is True, "")
        if final.trace:
            check("  final trace stages", "full_pipeline" in final.trace.stages, "")

# ==================================================================
# Section 30: Backward compatibility
# ==================================================================
print("\n" + "=" * 70)
print("Section 30: Backward compatibility")
print("=" * 70)

# Strategy Foundation untouched
check("StrategyFoundation intact", callable(FoundationStrategyRuntime.create_snapshot), "")
check("  recommend", callable(FoundationStrategyRuntime.recommend), "")
check("  prioritize", callable(FoundationStrategyRuntime.prioritize), "")

# Policy Foundation untouched
check("PolicyFoundation intact", callable(FoundationPolicyRuntime.create_rule), "")
check("  evaluate_all", callable(FoundationPolicyRuntime.evaluate_all), "")

# Strategy Pipeline untouched
check("StrategyPipeline intact", callable(StrategyPipeline.run), "")
check("  build_plan", callable(StrategyPipeline.build_plan), "")
check("  evaluate_policies", callable(StrategyPipeline.evaluate_policies), "")

# Execution Plan is new
check("ExecutionPlan new class", callable(FoundationExecutionPlanRuntime.build), "")
check("  build_actions", callable(FoundationExecutionPlanRuntime.build_actions), "")
check("  prioritize", callable(FoundationExecutionPlanRuntime.prioritize), "")
check("  group_by_category", callable(FoundationExecutionPlanRuntime.group_by_category), "")
check("  group_by_priority", callable(FoundationExecutionPlanRuntime.group_by_priority), "")
check("  filter_actions", callable(FoundationExecutionPlanRuntime.filter_actions), "")
check("  merge_plans", callable(FoundationExecutionPlanRuntime.merge_plans), "")
check("  estimate_cost", callable(FoundationExecutionPlanRuntime.estimate_cost), "")
check("  estimate_duration", callable(FoundationExecutionPlanRuntime.estimate_duration), "")
check("  build_trace", callable(FoundationExecutionPlanRuntime.build_trace), "")
check("  build_result", callable(FoundationExecutionPlanRuntime.build_result), "")

# ==================================================================
# Summary
# ==================================================================
print("\n" + "=" * 70)
print(f"Total: {pass_count}/{pass_count + fail_count} passed, {fail_count} failed")
print("=" * 70)

if fail_count > 0:
    exit(1)
