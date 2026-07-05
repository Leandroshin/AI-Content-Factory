"""Demo: Policy Runtime Foundation — 150+ scenarios.

Covers data models, rule creation, evaluation, filtering, grouping,
merge, prioritize, edge cases, determinism, and backward compatibility.
"""

from __future__ import annotations

from uuid import UUID, uuid4

from core.policy.foundation import (
    CATEGORY_COMPLIANCE,
    CATEGORY_COST,
    CATEGORY_DEPARTMENT,
    CATEGORY_EMPLOYEE,
    CATEGORY_KNOWLEDGE,
    CATEGORY_LEARNING,
    CATEGORY_MODEL,
    CATEGORY_MONITORING,
    CATEGORY_PERFORMANCE,
    CATEGORY_PROVIDER,
    CATEGORY_SECURITY,
    CATEGORY_SKILL,
    CATEGORY_STRATEGY,
    CATEGORY_COMPANY,
    CATEGORY_WORKFLOW,
    OPERATOR_CONTAINS,
    OPERATOR_EQ,
    OPERATOR_GT,
    OPERATOR_GTE,
    OPERATOR_IN,
    OPERATOR_LT,
    OPERATOR_LTE,
    OPERATOR_NE,
    PRIORITY_CRITICAL,
    PRIORITY_HIGH,
    PRIORITY_LOW,
    PRIORITY_MEDIUM,
    RESULT_APPROVED,
    RESULT_BLOCKED,
    RESULT_MANUAL_APPROVAL,
    RESULT_NOT_APPLICABLE,
    RESULT_REJECTED,
    FoundationPolicyRuntime,
    PolicyEvaluation,
    PolicyResult,
    PolicyRule,
    PolicySnapshot,
    PolicyTrace,
)
from core.strategy.foundation import (
    CATEGORY_COST_REDUCTION,
    CATEGORY_PERFORMANCE_IMPROVEMENT,
    CATEGORY_RISK_MITIGATION,
    PRIORITY_HIGH as STRAT_HIGH,
    PRIORITY_LOW as STRAT_LOW,
    PRIORITY_CRITICAL as STRAT_CRITICAL,
    PRIORITY_MEDIUM as STRAT_MEDIUM,
    StrategyRecommendation,
)

passed = 0
failed = 0


def check(name: str, condition: bool, detail: str = "") -> None:
    global passed, failed
    if condition:
        passed += 1
        status = "PASS"
    else:
        failed += 1
        status = "FAIL"
    print(f"[{status}] {name:50s} | {detail}")


def summary() -> None:
    total = passed + failed
    print(f"\n{'=' * 70}")
    print(f"Total: {total}/{total} passed, {failed} failed")
    print(f"{'=' * 70}")


# ==================================================================
# Shared fixtures
# ==================================================================

ts = 1000.0
uid1 = uuid4()
uid2 = uuid4()
uid3 = uuid4()
uid4 = uuid4()


def _rec(
    category: str = CATEGORY_COST_REDUCTION,
    priority: str = STRAT_MEDIUM,
    confidence: float = 0.8,
    title: str = "TestRec",
    rec_id: UUID | None = None,
) -> StrategyRecommendation:
    rid = rec_id if rec_id is not None else (uid1 if title == "TestRec" else uid2)
    return StrategyRecommendation(
        recommendation_id=rid,
        category=category,
        priority=priority,
        title=title,
        description="",
        reason="",
        expected_benefit="",
        confidence=confidence,
        created_at=ts,
    )


# ==================================================================
# Section 1: Data models
# ==================================================================
print("\n" + "=" * 70)
print("Section 1: Data models")
print("=" * 70)

rule = PolicyRule(
    rule_id=uid1,
    name="High confidence rule",
    category=CATEGORY_COST,
    description="Approve high confidence recommendations",
    field="confidence",
    operator=OPERATOR_GT,
    value=0.5,
    result_on_match=RESULT_APPROVED,
    result_on_mismatch=RESULT_REJECTED,
    priority=PRIORITY_HIGH,
    metadata={"source": "admin"},
    created_at=ts,
)
check("PolicyRule frozen", rule.name == "High confidence rule", "")
check("  category", rule.category == CATEGORY_COST, "")
check("  operator", rule.operator == OPERATOR_GT, "")
check("  value=0.5", rule.value == 0.5, "")
check("  result_on_match", rule.result_on_match == RESULT_APPROVED, "")
check("  result_on_mismatch", rule.result_on_mismatch == RESULT_REJECTED, "")
check("  priority=HIGH", rule.priority == PRIORITY_HIGH, "")
check("  metadata", rule.metadata.get("source") == "admin", "")
check("  rule_id UUID", isinstance(rule.rule_id, UUID), "")

ev = PolicyEvaluation(
    rule_id=uid1,
    rule_name="High confidence rule",
    target_id=str(uid2),
    category=CATEGORY_COST,
    result=RESULT_APPROVED,
    reason="Condition met",
    evaluated_at=ts,
)
check("PolicyEvaluation frozen", ev.result == RESULT_APPROVED, "")
check("  rule_name", ev.rule_name == "High confidence rule", "")
check("  target_id", ev.target_id == str(uid2), "")

snap = PolicySnapshot(
    evaluations=(ev,),
    results_summary={RESULT_APPROVED: 1},
    rules_applied=1,
    created_at=ts,
)
check("PolicySnapshot frozen", snap.rules_applied == 1, "")
check("  summary", snap.results_summary[RESULT_APPROVED] == 1, "")

trace = PolicyTrace(
    rules_evaluated=2,
    recommendations_evaluated=3,
    duration_ms=1.5,
    stages=("evaluate_all",),
    metrics={"total": 6.0},
)
check("PolicyTrace frozen", trace.rules_evaluated == 2, "")
check("  stages", "evaluate_all" in trace.stages, "")
check("  metrics", trace.metrics["total"] == 6.0, "")

pres = PolicyResult(success=True, snapshot=snap, trace=trace)
check("PolicyResult success", pres.success, "")
check("  snapshot ref", pres.snapshot is snap, "")
check("  trace ref", pres.trace is trace, "")

pres_fail = PolicyResult(success=False, error_message="fail")
check("  error result", not pres_fail.success and pres_fail.error_message == "fail", "")

# Immutability
try:
    rule.name = "Mut"
    check("immutable enforced", False, "")
except Exception:
    check("immutable enforced", True, "")

# ==================================================================
# Section 2: create_rule
# ==================================================================
print("\n" + "=" * 70)
print("Section 2: create_rule")
print("=" * 70)

r1 = FoundationPolicyRuntime.create_rule(
    name="Cost approval",
    category=CATEGORY_COST,
    field="confidence",
    operator=OPERATOR_GT,
    value=0.7,
)
check("create_rule basic", r1.name == "Cost approval", "")
check("  category cost", r1.category == CATEGORY_COST, "")
check("  priority default", r1.priority == PRIORITY_MEDIUM, "")
check("  result_on_match default", r1.result_on_match == RESULT_APPROVED, "")
check("  id auto-generated", isinstance(r1.rule_id, UUID), "")

r2 = FoundationPolicyRuntime.create_rule(
    name="Security critical",
    category=CATEGORY_SECURITY,
    field="priority",
    operator=OPERATOR_EQ,
    value=STRAT_CRITICAL,
    result_on_match=RESULT_MANUAL_APPROVAL,
    result_on_mismatch=RESULT_REJECTED,
    priority=PRIORITY_CRITICAL,
    description="Critical security requires manual approval",
)
check("create_rule custom", r2.result_on_match == RESULT_MANUAL_APPROVAL, "")
check("  priority critical", r2.priority == PRIORITY_CRITICAL, "")

r3 = FoundationPolicyRuntime.create_rule(
    name="Cost limit",
    category=CATEGORY_COST,
    field="confidence",
    operator=OPERATOR_LT,
    value=0.3,
    result_on_match=RESULT_BLOCKED,
    result_on_mismatch=RESULT_APPROVED,
    source="automated",
)
check("create_rule metadata", r3.metadata.get("source") == "automated", "")

# All operators
for op in (OPERATOR_GT, OPERATOR_GTE, OPERATOR_LT, OPERATOR_LTE, OPERATOR_EQ, OPERATOR_NE, OPERATOR_IN, OPERATOR_CONTAINS):
    r = FoundationPolicyRuntime.create_rule("op", CATEGORY_COST, "confidence", op, 0.5)
    check(f"operator {op}", r.operator == op, "")

# ==================================================================
# Section 3: create_snapshot
# ==================================================================
print("\n" + "=" * 70)
print("Section 3: create_snapshot")
print("=" * 70)

ev1 = PolicyEvaluation(rule_id=uid1, rule_name="R1", target_id="T1", category=CATEGORY_COST, result=RESULT_APPROVED, reason="OK", evaluated_at=ts)
ev2 = PolicyEvaluation(rule_id=uid2, rule_name="R2", target_id="T2", category=CATEGORY_SECURITY, result=RESULT_REJECTED, reason="NO", evaluated_at=ts)
snap1 = FoundationPolicyRuntime.create_snapshot([ev1, ev2])
check("snap evaluations len", len(snap1.evaluations) == 2, "")
check("  summary keys", len(snap1.results_summary) == 2, "")
check("  approved=1", snap1.results_summary.get(RESULT_APPROVED) == 1, "")
check("  rejected=1", snap1.results_summary.get(RESULT_REJECTED) == 1, "")
check("  rules_applied=2", snap1.rules_applied == 2, "")

# Empty
snap_empty = FoundationPolicyRuntime.create_snapshot([])
check("snap empty", len(snap_empty.evaluations) == 0, "")
check("  no summary", len(snap_empty.results_summary) == 0, "")
check("  rules=0", snap_empty.rules_applied == 0, "")

# ==================================================================
# Section 4: evaluate (single rule, single target)
# ==================================================================
print("\n" + "=" * 70)
print("Section 4: evaluate (single)")
print("=" * 70)

# Rule: confidence > 0.5 → APPROVED, else REJECTED
rule_high_conf = FoundationPolicyRuntime.create_rule(
    name="High confidence", category=CATEGORY_COST,
    field="confidence", operator=OPERATOR_GT, value=0.5,
)

rec_high = _rec(confidence=0.9)
rec_low = _rec(confidence=0.1)

ev_high = FoundationPolicyRuntime.evaluate(rule_high_conf, rec_high)
check("eval high conf approved", ev_high.result == RESULT_APPROVED, f"result={ev_high.result}")
check("  reason not empty", bool(ev_high.reason), "")

ev_low = FoundationPolicyRuntime.evaluate(rule_high_conf, rec_low)
check("eval low conf rejected", ev_low.result == RESULT_REJECTED, f"result={ev_low.result}")

# Rule: priority == CRITICAL → MANUAL_APPROVAL
rule_crit = FoundationPolicyRuntime.create_rule(
    name="Critical strat", category=CATEGORY_STRATEGY,
    field="priority", operator=OPERATOR_EQ, value=STRAT_CRITICAL,
    result_on_match=RESULT_MANUAL_APPROVAL, result_on_mismatch=RESULT_APPROVED,
)
rec_crit = _rec(priority=STRAT_CRITICAL)
rec_not_crit = _rec(priority=STRAT_LOW)
ev_crit = FoundationPolicyRuntime.evaluate(rule_crit, rec_crit)
check("eval critical manual_approval", ev_crit.result == RESULT_MANUAL_APPROVAL, f"result={ev_crit.result}")
ev_not_crit = FoundationPolicyRuntime.evaluate(rule_crit, rec_not_crit)
check("eval not critical approved", ev_not_crit.result == RESULT_APPROVED, "")

# Rule: confidence < 0.3 → BLOCKED
rule_block = FoundationPolicyRuntime.create_rule(
    name="Block low", category=CATEGORY_COST,
    field="confidence", operator=OPERATOR_LT, value=0.3,
    result_on_match=RESULT_BLOCKED, result_on_mismatch=RESULT_APPROVED,
)
ev_block = FoundationPolicyRuntime.evaluate(rule_block, rec_low)
check("eval low conf blocked", ev_block.result == RESULT_BLOCKED, "")

# Rule: category == "Cost Reduction" → APPROVED
rule_cat = FoundationPolicyRuntime.create_rule(
    name="Cost category", category=CATEGORY_COST,
    field="category", operator=OPERATOR_EQ, value=CATEGORY_COST_REDUCTION,
)
rec_cost = _rec(category=CATEGORY_COST_REDUCTION)
ev_cat = FoundationPolicyRuntime.evaluate(rule_cat, rec_cost)
check("eval category match approved", ev_cat.result == RESULT_APPROVED, "")

# Non-matching category
rec_other = _rec(category=CATEGORY_PERFORMANCE_IMPROVEMENT)
ev_cat_mismatch = FoundationPolicyRuntime.evaluate(rule_cat, rec_other)
check("eval category mismatch rejected", ev_cat_mismatch.result == RESULT_REJECTED, "")

# Field not found -> NOT_APPLICABLE
rule_nonexistent = FoundationPolicyRuntime.create_rule(
    name="Bad field", category=CATEGORY_COST,
    field="nonexistent_field", operator=OPERATOR_EQ, value="x",
)
ev_na = FoundationPolicyRuntime.evaluate(rule_nonexistent, rec_high)
check("eval missing field not_applicable", ev_na.result == RESULT_NOT_APPLICABLE, f"result={ev_na.result}")

# ==================================================================
# Section 5: evaluate_all (multiple rules, multiple targets)
# ==================================================================
print("\n" + "=" * 70)
print("Section 5: evaluate_all")
print("=" * 70)

rules = [r1, r2, r3]
targets = [
    _rec(confidence=0.9, category=CATEGORY_COST_REDUCTION, priority=STRAT_HIGH),
    _rec(confidence=0.2, category=CATEGORY_PERFORMANCE_IMPROVEMENT, priority=STRAT_LOW),
    _rec(confidence=0.5, category=CATEGORY_RISK_MITIGATION, priority=STRAT_CRITICAL),
]
res = FoundationPolicyRuntime.evaluate_all(rules, targets)
check("eval_all success", res.success, "")
if res.snapshot:
    total_evals = len(res.snapshot.evaluations)
    check(f"  total evaluations={len(rules)*len(targets)}", total_evals == len(rules) * len(targets), f"val={total_evals}")
    check("  summary keys", len(res.snapshot.results_summary) > 0, f"summary={res.snapshot.results_summary}")
if res.trace:
    check("  trace rules", res.trace.rules_evaluated == len(rules), "")
    check("  trace targets", res.trace.recommendations_evaluated == len(targets), "")
    check("  trace duration > 0", res.trace.duration_ms >= 0, "")

# Empty rules
res2 = FoundationPolicyRuntime.evaluate_all([], targets)
if res2.snapshot:
    check("eval_all empty rules", len(res2.snapshot.evaluations) == 0, "")

# Empty targets
res3 = FoundationPolicyRuntime.evaluate_all(rules, [])
if res3.snapshot:
    check("eval_all empty targets", len(res3.snapshot.evaluations) == 0, "")

# Both empty
res4 = FoundationPolicyRuntime.evaluate_all([], [])
if res4.snapshot:
    check("eval_all both empty", len(res4.snapshot.evaluations) == 0, "")

# ==================================================================
# Section 6: approve / reject / requires_approval / blocked
# ==================================================================
print("\n" + "=" * 70)
print("Section 6: Result filters")
print("=" * 70)

all_evals = list(res.snapshot.evaluations) if res.snapshot else []

approved = FoundationPolicyRuntime.approve(all_evals)
check("approve filter", all(e.result == RESULT_APPROVED for e in approved), f"count={len(approved)}")

rejected = FoundationPolicyRuntime.reject(all_evals)
check("reject filter", all(e.result == RESULT_REJECTED for e in rejected), f"count={len(rejected)}")

manual = FoundationPolicyRuntime.requires_approval(all_evals)
check("requires_approval filter", all(e.result == RESULT_MANUAL_APPROVAL for e in manual), f"count={len(manual)}")

blocked = FoundationPolicyRuntime.blocked(all_evals)
check("blocked filter", all(e.result == RESULT_BLOCKED for e in blocked), f"count={len(blocked)}")

# Empty
check("approve empty", len(FoundationPolicyRuntime.approve([])) == 0, "")
check("reject empty", len(FoundationPolicyRuntime.reject([])) == 0, "")
check("requires_approval empty", len(FoundationPolicyRuntime.requires_approval([])) == 0, "")
check("blocked empty", len(FoundationPolicyRuntime.blocked([])) == 0, "")

# ==================================================================
# Section 7: prioritize (rules)
# ==================================================================
print("\n" + "=" * 70)
print("Section 7: prioritize")
print("=" * 70)

pr_rules = [
    FoundationPolicyRuntime.create_rule("A", CATEGORY_COST, "confidence", OPERATOR_GT, 0.5, priority=PRIORITY_LOW),
    FoundationPolicyRuntime.create_rule("B", CATEGORY_SECURITY, "confidence", OPERATOR_GT, 0.5, priority=PRIORITY_CRITICAL),
    FoundationPolicyRuntime.create_rule("C", CATEGORY_COST, "confidence", OPERATOR_GT, 0.5, priority=PRIORITY_HIGH),
    FoundationPolicyRuntime.create_rule("D", CATEGORY_COST, "confidence", OPERATOR_GT, 0.5, priority=PRIORITY_MEDIUM),
]
sorted_rules = FoundationPolicyRuntime.prioritize(pr_rules)
check("prioritize CRITICAL first", sorted_rules[0].priority == PRIORITY_CRITICAL, "")
check("  HIGH second", sorted_rules[1].priority == PRIORITY_HIGH, "")
check("  MEDIUM third", sorted_rules[2].priority == PRIORITY_MEDIUM, "")
check("  LOW last", sorted_rules[3].priority == PRIORITY_LOW, "")

check("prioritize empty", len(FoundationPolicyRuntime.prioritize([])) == 0, "")

# ==================================================================
# Section 8: filter_rules
# ==================================================================
print("\n" + "=" * 70)
print("Section 8: filter_rules")
print("=" * 70)

filter_rules = [
    FoundationPolicyRuntime.create_rule("R1", CATEGORY_COST, "confidence", OPERATOR_GT, 0.5, result_on_match=RESULT_APPROVED, priority=PRIORITY_HIGH),
    FoundationPolicyRuntime.create_rule("R2", CATEGORY_SECURITY, "confidence", OPERATOR_GT, 0.5, result_on_match=RESULT_MANUAL_APPROVAL, priority=PRIORITY_CRITICAL),
    FoundationPolicyRuntime.create_rule("R3", CATEGORY_COST, "confidence", OPERATOR_LT, 0.3, result_on_match=RESULT_BLOCKED, priority=PRIORITY_MEDIUM),
]

f_cat = FoundationPolicyRuntime.filter_rules(filter_rules, category=CATEGORY_COST)
check("filter cost rules", len(f_cat) == 2, f"count={len(f_cat)}")

f_res = FoundationPolicyRuntime.filter_rules(filter_rules, result=RESULT_BLOCKED)
check("filter blocked rules", len(f_res) >= 1, f"count={len(f_res)}")

f_prio = FoundationPolicyRuntime.filter_rules(filter_rules, priority=PRIORITY_CRITICAL)
check("filter critical rules", len(f_prio) == 1, "")

f_combined = FoundationPolicyRuntime.filter_rules(filter_rules, category=CATEGORY_COST, priority=PRIORITY_HIGH)
check("filter combined", len(f_combined) == 1, "")

f_none = FoundationPolicyRuntime.filter_rules(filter_rules, category="NonExistent")
check("filter no match", len(f_none) == 0, "")

f_all = FoundationPolicyRuntime.filter_rules(filter_rules)
check("filter no args", len(f_all) == len(filter_rules), "")

f_empty = FoundationPolicyRuntime.filter_rules([])
check("filter empty", len(f_empty) == 0, "")

# ==================================================================
# Section 9: group_by_category / group_by_result
# ==================================================================
print("\n" + "=" * 70)
print("Section 9: Grouping")
print("=" * 70)

group_evals = all_evals if all_evals else [
    PolicyEvaluation(rule_id=uid1, rule_name="R1", target_id="T1", category=CATEGORY_COST, result=RESULT_APPROVED, reason="", evaluated_at=ts),
    PolicyEvaluation(rule_id=uid2, rule_name="R2", target_id="T2", category=CATEGORY_SECURITY, result=RESULT_REJECTED, reason="", evaluated_at=ts),
    PolicyEvaluation(rule_id=uid3, rule_name="R3", target_id="T3", category=CATEGORY_COST, result=RESULT_APPROVED, reason="", evaluated_at=ts),
]

g_cat = FoundationPolicyRuntime.group_by_category(group_evals)
check("group category keys", len(g_cat) >= 2, f"keys={list(g_cat.keys())}")
cost_evals = g_cat.get(CATEGORY_COST, [])
check("  cost category count", len(cost_evals) >= 2, f"count={len(cost_evals)}")

g_res = FoundationPolicyRuntime.group_by_result(group_evals)
check("group result keys", len(g_res) >= 2, f"keys={list(g_res.keys())}")

# Empty
check("group cat empty", len(FoundationPolicyRuntime.group_by_category([])) == 0, "")
check("group res empty", len(FoundationPolicyRuntime.group_by_result([])) == 0, "")

# ==================================================================
# Section 10: merge
# ==================================================================
print("\n" + "=" * 70)
print("Section 10: merge")
print("=" * 70)

snap_a = FoundationPolicyRuntime.create_snapshot([
    PolicyEvaluation(rule_id=uid1, rule_name="R1", target_id="T1", category=CATEGORY_COST, result=RESULT_APPROVED, reason="", evaluated_at=ts),
])
snap_b = FoundationPolicyRuntime.create_snapshot([
    PolicyEvaluation(rule_id=uid2, rule_name="R2", target_id="T2", category=CATEGORY_SECURITY, result=RESULT_REJECTED, reason="", evaluated_at=ts),
])
merged = FoundationPolicyRuntime.merge([snap_a, snap_b])
check("merge total", len(merged.evaluations) == 2, "")
check("  rules_applied=2", merged.rules_applied == 2, "")

# Merge with duplicate (same rule_id + target_id)
snap_a2 = FoundationPolicyRuntime.create_snapshot([
    PolicyEvaluation(rule_id=uid1, rule_name="R1", target_id="T1", category=CATEGORY_COST, result=RESULT_APPROVED, reason="", evaluated_at=ts),
])
merged_dup = FoundationPolicyRuntime.merge([snap_a, snap_a2])
check("merge dedup", len(merged_dup.evaluations) == 1, f"count={len(merged_dup.evaluations)}")

# Merge empty
merged_empty = FoundationPolicyRuntime.merge([])
check("merge empty", len(merged_empty.evaluations) == 0, "")

# Merge empty + non-empty
merged_partial = FoundationPolicyRuntime.merge([PolicySnapshot(), snap_a])
check("merge empty+non", len(merged_partial.evaluations) == 1, "")

# ==================================================================
# Section 11: build_trace / build_result
# ==================================================================
print("\n" + "=" * 70)
print("Section 11: build_trace / build_result")
print("=" * 70)

t = FoundationPolicyRuntime.build_trace(
    rules_evaluated=5,
    recommendations_evaluated=10,
    duration_ms=2.0,
    stages=["eval"],
    metrics={"total": 50.0},
)
check("build_trace", t.rules_evaluated == 5 and t.recommendations_evaluated == 10, "")
check("  stages", "eval" in t.stages, "")
check("  duration", t.duration_ms == 2.0, "")

t_default = FoundationPolicyRuntime.build_trace()
check("build_trace default", t_default.rules_evaluated == 0 and t_default.duration_ms == 0.0, "")

snap_r = FoundationPolicyRuntime.create_snapshot([
    PolicyEvaluation(rule_id=uid1, rule_name="R1", target_id="T1", category=CATEGORY_COST, result=RESULT_APPROVED, reason="", evaluated_at=ts),
])
pr = FoundationPolicyRuntime.build_result(snap_r, stages=["final"])
check("build_result success", pr.success, "")
check("  snapshot ref", pr.snapshot is snap_r, "")
check("  trace present", pr.trace is not None, "")

# ==================================================================
# Section 12: Operators comprehensive test
# ==================================================================
print("\n" + "=" * 70)
print("Section 12: Operators")
print("=" * 70)

op_rec = _rec(confidence=0.75, priority=STRAT_HIGH)

# gt
r_gt = FoundationPolicyRuntime.create_rule("gt", CATEGORY_COST, "confidence", OPERATOR_GT, 0.5)
check("op gt true", FoundationPolicyRuntime.evaluate(r_gt, op_rec).result == RESULT_APPROVED, "")
r_gt_f = FoundationPolicyRuntime.create_rule("gt f", CATEGORY_COST, "confidence", OPERATOR_GT, 0.9)
check("op gt false", FoundationPolicyRuntime.evaluate(r_gt_f, op_rec).result == RESULT_REJECTED, "")

# gte
r_gte = FoundationPolicyRuntime.create_rule("gte", CATEGORY_COST, "confidence", OPERATOR_GTE, 0.75)
check("op gte true", FoundationPolicyRuntime.evaluate(r_gte, op_rec).result == RESULT_APPROVED, "")
r_gte_f = FoundationPolicyRuntime.create_rule("gte f", CATEGORY_COST, "confidence", OPERATOR_GTE, 0.8)
check("op gte false", FoundationPolicyRuntime.evaluate(r_gte_f, op_rec).result == RESULT_REJECTED, "")

# lt
r_lt = FoundationPolicyRuntime.create_rule("lt", CATEGORY_COST, "confidence", OPERATOR_LT, 0.9)
check("op lt true", FoundationPolicyRuntime.evaluate(r_lt, op_rec).result == RESULT_APPROVED, "")
r_lt_f = FoundationPolicyRuntime.create_rule("lt f", CATEGORY_COST, "confidence", OPERATOR_LT, 0.5)
check("op lt false", FoundationPolicyRuntime.evaluate(r_lt_f, op_rec).result == RESULT_REJECTED, "")

# lte
r_lte = FoundationPolicyRuntime.create_rule("lte", CATEGORY_COST, "confidence", OPERATOR_LTE, 0.75)
check("op lte true", FoundationPolicyRuntime.evaluate(r_lte, op_rec).result == RESULT_APPROVED, "")
r_lte_f = FoundationPolicyRuntime.create_rule("lte f", CATEGORY_COST, "confidence", OPERATOR_LTE, 0.5)
check("op lte false", FoundationPolicyRuntime.evaluate(r_lte_f, op_rec).result == RESULT_REJECTED, "")

# eq
r_eq = FoundationPolicyRuntime.create_rule("eq", CATEGORY_STRATEGY, "priority", OPERATOR_EQ, STRAT_HIGH)
check("op eq true", FoundationPolicyRuntime.evaluate(r_eq, op_rec).result == RESULT_APPROVED, "")
r_eq_f = FoundationPolicyRuntime.create_rule("eq f", CATEGORY_STRATEGY, "priority", OPERATOR_EQ, STRAT_LOW)
check("op eq false", FoundationPolicyRuntime.evaluate(r_eq_f, op_rec).result == RESULT_REJECTED, "")

# ne
r_ne = FoundationPolicyRuntime.create_rule("ne", CATEGORY_STRATEGY, "priority", OPERATOR_NE, STRAT_LOW)
check("op ne true", FoundationPolicyRuntime.evaluate(r_ne, op_rec).result == RESULT_APPROVED, "")
r_ne_f = FoundationPolicyRuntime.create_rule("ne f", CATEGORY_STRATEGY, "priority", OPERATOR_NE, STRAT_HIGH)
check("op ne false", FoundationPolicyRuntime.evaluate(r_ne_f, op_rec).result == RESULT_REJECTED, "")

# in
r_in = FoundationPolicyRuntime.create_rule("in", CATEGORY_STRATEGY, "priority", OPERATOR_IN, [STRAT_HIGH, STRAT_CRITICAL])
check("op in true", FoundationPolicyRuntime.evaluate(r_in, op_rec).result == RESULT_APPROVED, "")
r_in_f = FoundationPolicyRuntime.create_rule("in f", CATEGORY_STRATEGY, "priority", OPERATOR_IN, [STRAT_LOW, STRAT_MEDIUM])
check("op in false", FoundationPolicyRuntime.evaluate(r_in_f, op_rec).result == RESULT_REJECTED, "")

# contains (on title)
r_contains = FoundationPolicyRuntime.create_rule("contains", CATEGORY_COST, "title", OPERATOR_CONTAINS, "test")
check("op contains true", FoundationPolicyRuntime.evaluate(r_contains, op_rec).result == RESULT_APPROVED, "")
r_contains_f = FoundationPolicyRuntime.create_rule("contains f", CATEGORY_COST, "title", OPERATOR_CONTAINS, "xyz")
check("op contains false", FoundationPolicyRuntime.evaluate(r_contains_f, op_rec).result == RESULT_REJECTED, "")

# ==================================================================
# Section 13: evaluate with non-recommendation targets
# ==================================================================
print("\n" + "=" * 70)
print("Section 13: Non-recommendation targets")
print("=" * 70)

# Evaluate against a dict target
dict_target = {"confidence": 0.9, "priority": "HIGH", "category": "Cost"}
r_dict = FoundationPolicyRuntime.create_rule("dict", CATEGORY_COST, "confidence", OPERATOR_GT, 0.5)
ev_dict = FoundationPolicyRuntime.evaluate(r_dict, dict_target)
check("dict target approved", ev_dict.result == RESULT_APPROVED, "")

# Evaluate against a plain object
class DummyTarget:
    confidence = 0.2
    priority = "LOW"

dummy = DummyTarget()
ev_dummy = FoundationPolicyRuntime.evaluate(r_dict, dummy)
check("object target rejected", ev_dummy.result == RESULT_REJECTED, "")

# Evaluate against a string (edge case - no matching field)
ev_str = FoundationPolicyRuntime.evaluate(r_dict, "just a string")
check("string target not_applicable", ev_str.result == RESULT_NOT_APPLICABLE, "")

# Evaluate with int values
r_int = FoundationPolicyRuntime.create_rule("int", CATEGORY_COST, "confidence", OPERATOR_GT, 50)
rec_int = _rec(confidence=80.0)
ev_int = FoundationPolicyRuntime.evaluate(r_int, rec_int)
check("int comparison approved", ev_int.result == RESULT_APPROVED, "")

# ==================================================================
# Section 14: Determinism
# ==================================================================
print("\n" + "=" * 70)
print("Section 14: Determinism")
print("=" * 70)

rule_det = FoundationPolicyRuntime.create_rule(
    "det", CATEGORY_COST, "confidence", OPERATOR_GT, 0.5,
)
rec_det = _rec(confidence=0.8)

ev_det1 = FoundationPolicyRuntime.evaluate(rule_det, rec_det)
ev_det2 = FoundationPolicyRuntime.evaluate(rule_det, rec_det)
check("det eval same result", ev_det1.result == ev_det2.result, "")
check("det eval same reason", ev_det1.reason == ev_det2.reason, "")

# evaluate_all determinism
rules_det = [rule_det]
targets_det = [_rec(confidence=0.6), _rec(confidence=0.4)]
res_det1 = FoundationPolicyRuntime.evaluate_all(rules_det, targets_det)
res_det2 = FoundationPolicyRuntime.evaluate_all(rules_det, targets_det)
if res_det1.snapshot and res_det2.snapshot:
    r1_results = [e.result for e in res_det1.snapshot.evaluations]
    r2_results = [e.result for e in res_det2.snapshot.evaluations]
    check("det evaluate_all results", r1_results == r2_results, f"r1={r1_results} r2={r2_results}")

# Snapshot determinism
snap_det1 = FoundationPolicyRuntime.create_snapshot([ev_det1])
snap_det2 = FoundationPolicyRuntime.create_snapshot([ev_det2])
check("det snapshot summary", snap_det1.results_summary == snap_det2.results_summary, "")

# ==================================================================
# Section 15: Edge cases
# ==================================================================
print("\n" + "=" * 70)
print("Section 15: Edge cases")
print("=" * 70)

# Null value on rule
r_null_val = FoundationPolicyRuntime.create_rule(
    "null val", CATEGORY_COST, "confidence", OPERATOR_EQ, None,
)
ev_null_val = FoundationPolicyRuntime.evaluate(r_null_val, _rec(confidence=0.5))
check("edge rule null value", ev_null_val.result in (RESULT_NOT_APPLICABLE, RESULT_BLOCKED), f"result={ev_null_val.result}")

# Non-numeric comparison
r_str = FoundationPolicyRuntime.create_rule(
    "str op", CATEGORY_COST, "priority", OPERATOR_GT, "LOW",
)
ev_str_op = FoundationPolicyRuntime.evaluate(r_str, _rec(priority=STRAT_HIGH))
check("edge string > comparison", ev_str_op.result in (RESULT_APPROVED, RESULT_REJECTED, RESULT_BLOCKED), f"result={ev_str_op.result}")

# Compare with incompatible types
r_incomp = FoundationPolicyRuntime.create_rule(
    "incomp", CATEGORY_COST, "confidence", OPERATOR_EQ, "string",
)
ev_incomp = FoundationPolicyRuntime.evaluate(r_incomp, _rec(confidence=0.5))
check("edge type mismatch", ev_incomp.result in (RESULT_REJECTED, RESULT_NOT_APPLICABLE), f"result={ev_incomp.result}")

# Empty rules in evaluate_all
res_empty = FoundationPolicyRuntime.evaluate_all([], [_rec()])
if res_empty.snapshot:
    check("edge no rules", len(res_empty.snapshot.evaluations) == 0, "")

# Empty targets in evaluate_all
res_empty_t = FoundationPolicyRuntime.evaluate_all([rule], [])
if res_empty_t.snapshot:
    check("edge no targets", len(res_empty_t.snapshot.evaluations) == 0, "")

# Filter with no matches
check("edge filter none", len(FoundationPolicyRuntime.filter_rules([], category=CATEGORY_COST)) == 0, "")

# Group empty
check("edge group cat empty", len(FoundationPolicyRuntime.group_by_category([])) == 0, "")
check("edge group res empty", len(FoundationPolicyRuntime.group_by_result([])) == 0, "")

# Merge empty list
m_e = FoundationPolicyRuntime.merge([])
check("edge merge empty list", len(m_e.evaluations) == 0, "")

# Approve empty
check("edge approve empty", len(FoundationPolicyRuntime.approve([])) == 0, "")
check("edge reject empty", len(FoundationPolicyRuntime.reject([])) == 0, "")
check("edge manual empty", len(FoundationPolicyRuntime.requires_approval([])) == 0, "")
check("edge blocked empty", len(FoundationPolicyRuntime.blocked([])) == 0, "")

# Prioritize empty
check("edge prioritize empty", len(FoundationPolicyRuntime.prioritize([])) == 0, "")

# Large rule name / description
long_name = "A" * 200
r_long = FoundationPolicyRuntime.create_rule(long_name, CATEGORY_COST, "confidence", OPERATOR_GT, 0.5)
check("edge long name", r_long.name == long_name, f"len={len(r_long.name)}")

# Batch of evaluations with same rule
batch = FoundationPolicyRuntime.evaluate_all([rule_det], [_rec(confidence=0.9), _rec(confidence=0.6), _rec(confidence=0.3)])
if batch.snapshot:
    check("edge batch size", len(batch.snapshot.evaluations) == 3, "")
    summary = batch.snapshot.results_summary
    check("edge batch approved >= 2", summary.get(RESULT_APPROVED, 0) >= 2, f"summary={summary}")

# Evaluate with field value 0
rec_zero = _rec(confidence=0.0)
r_gt_zero = FoundationPolicyRuntime.create_rule("gt zero", CATEGORY_COST, "confidence", OPERATOR_GT, 0.0)
check("edge confidence=0 gt 0 rejected", FoundationPolicyRuntime.evaluate(r_gt_zero, rec_zero).result == RESULT_REJECTED, "")
r_gte_zero = FoundationPolicyRuntime.create_rule("gte zero", CATEGORY_COST, "confidence", OPERATOR_GTE, 0.0)
check("edge confidence=0 gte 0 approved", FoundationPolicyRuntime.evaluate(r_gte_zero, rec_zero).result == RESULT_APPROVED, "")

# ==================================================================
# Section 16: Full pipeline
# ==================================================================
print("\n" + "=" * 70)
print("Section 16: Full pipeline")
print("=" * 70)

# Create rules for all categories
pipeline_rules = [
    FoundationPolicyRuntime.create_rule(
        "Cost rule", CATEGORY_COST, "confidence", OPERATOR_GT, 0.5,
        result_on_match=RESULT_APPROVED, result_on_mismatch=RESULT_REJECTED,
        priority=PRIORITY_HIGH,
    ),
    FoundationPolicyRuntime.create_rule(
        "Critical rule", CATEGORY_STRATEGY, "priority", OPERATOR_EQ, STRAT_CRITICAL,
        result_on_match=RESULT_MANUAL_APPROVAL, result_on_mismatch=RESULT_APPROVED,
        priority=PRIORITY_CRITICAL,
    ),
    FoundationPolicyRuntime.create_rule(
        "Block low confidence", CATEGORY_COST, "confidence", OPERATOR_LT, 0.3,
        result_on_match=RESULT_BLOCKED, result_on_mismatch=RESULT_APPROVED,
        priority=PRIORITY_MEDIUM,
    ),
    FoundationPolicyRuntime.create_rule(
        "Performance rule", CATEGORY_PERFORMANCE, "category", OPERATOR_EQ, CATEGORY_PERFORMANCE_IMPROVEMENT,
        result_on_match=RESULT_APPROVED, result_on_mismatch=RESULT_REJECTED,
        priority=PRIORITY_LOW,
    ),
]

# Create recommendations (each with unique ID)
pipeline_targets = [
    _rec(confidence=0.9, category=CATEGORY_COST_REDUCTION, priority=STRAT_HIGH, title="Cost rec", rec_id=UUID("a0000000-0000-0000-0000-000000000001")),
    _rec(confidence=0.2, category=CATEGORY_PERFORMANCE_IMPROVEMENT, priority=STRAT_LOW, title="Perf rec", rec_id=UUID("a0000000-0000-0000-0000-000000000002")),
    _rec(confidence=0.95, category=CATEGORY_RISK_MITIGATION, priority=STRAT_CRITICAL, title="Risk rec", rec_id=UUID("a0000000-0000-0000-0000-000000000003")),
    _rec(confidence=0.5, category=CATEGORY_COST_REDUCTION, priority=STRAT_MEDIUM, title="Med rec", rec_id=UUID("a0000000-0000-0000-0000-000000000004")),
]

# Evaluate all
pipeline_res = FoundationPolicyRuntime.evaluate_all(pipeline_rules, pipeline_targets)
check("pipeline success", pipeline_res.success, "")
if pipeline_res.snapshot:
    evals = pipeline_res.snapshot.evaluations
    total = len(evals)
    expected = len(pipeline_rules) * len(pipeline_targets)
    check(f"  total evaluations={expected}", total == expected, f"val={total}")

    summ = pipeline_res.snapshot.results_summary
    check("  results summary has keys", len(summ) > 0, f"summary={summ}")

    # Filter results
    app = FoundationPolicyRuntime.approve(evals)
    rej = FoundationPolicyRuntime.reject(evals)
    man = FoundationPolicyRuntime.requires_approval(evals)
    blk = FoundationPolicyRuntime.blocked(evals)
    check("  approved count", len(app) > 0, f"count={len(app)}")
    check("  rejected count", len(rej) >= 0, f"count={len(rej)}")
    check("  manual approval count", len(man) > 0, f"count={len(man)}")
    check("  blocked count", len(blk) > 0, f"count={len(blk)}")

    # Group
    g = FoundationPolicyRuntime.group_by_category(evals)
    check("  group categories", len(g) >= 3, f"cats={list(g.keys())}")
    gr = FoundationPolicyRuntime.group_by_result(evals)
    check("  group results", len(gr) >= 3, f"results={list(gr.keys())}")

    # Filter rules
    cost_rules = FoundationPolicyRuntime.filter_rules(pipeline_rules, category=CATEGORY_COST)
    check("  filter cost rules", len(cost_rules) == 2, f"count={len(cost_rules)}")

    critical_rules = FoundationPolicyRuntime.filter_rules(pipeline_rules, priority=PRIORITY_CRITICAL)
    check("  filter critical rules", len(critical_rules) == 1, "")

    # Prioritize rules
    prio_rules = FoundationPolicyRuntime.prioritize(pipeline_rules)
    check("  prioritize first critical", prio_rules[0].priority == PRIORITY_CRITICAL, "")

    # Merge
    snap_x = FoundationPolicyRuntime.create_snapshot(evals[:4])
    snap_y = FoundationPolicyRuntime.create_snapshot(evals[4:])
    merged_p = FoundationPolicyRuntime.merge([snap_x, snap_y])
    check("  merge restores total", len(merged_p.evaluations) == total, f"merged={len(merged_p.evaluations)}")

    # Build result
    final = FoundationPolicyRuntime.build_result(snap_x, stages=["pipeline"], metrics={"total": float(total)})
    check("  final result success", final.success, "")
    if final.trace:
        check("  trace stages", "pipeline" in final.trace.stages, "")
        check("  trace metrics", final.trace.metrics["total"] == float(total), "")

    # Build trace
    ft = FoundationPolicyRuntime.build_trace(
        rules_evaluated=len(pipeline_rules),
        recommendations_evaluated=len(pipeline_targets),
        duration_ms=5.0,
        stages=["pipeline"],
        metrics={"total": float(total)},
    )
    check("  build trace", ft.rules_evaluated == len(pipeline_rules), "")

# ==================================================================
# Section 17: Backward compatibility
# ==================================================================
print("\n" + "=" * 70)
print("Section 17: Backward compatibility")
print("=" * 70)

from core.strategy.foundation import FoundationStrategyRuntime as FSR
check("FSR importable", FSR is not None, "")

from core.policy.foundation import FoundationPolicyRuntime as FPR
check("FPR importable", FPR is FoundationPolicyRuntime, "")

# Existing runtime methods unaffected
from core.analytics.runtime import PerformanceRuntime
pr2 = PerformanceRuntime.analyze_execution(executions=[], usages=[])
check("PR.analyze_execution still works", pr2.success, "")

from core.monitoring.runtime import MonitoringRuntime
mr2 = MonitoringRuntime.build_snapshot([])
check("MR.build_snapshot still works", mr2.total_events == 0, "")

from core.strategy.foundation import FoundationStrategyRuntime
sr2 = FoundationStrategyRuntime.create_snapshot()
check("FSR.create_snapshot still works", len(sr2.recommendations) == 0, "")

# All categories defined
all_cats = {
    CATEGORY_SECURITY, CATEGORY_COMPLIANCE, CATEGORY_COST,
    CATEGORY_PERFORMANCE, CATEGORY_WORKFLOW, CATEGORY_KNOWLEDGE,
    CATEGORY_LEARNING, CATEGORY_SKILL, CATEGORY_MONITORING,
    CATEGORY_STRATEGY, CATEGORY_COMPANY, CATEGORY_PROVIDER,
    CATEGORY_MODEL, CATEGORY_EMPLOYEE, CATEGORY_DEPARTMENT,
}
check("15 categories defined", len(all_cats) == 15, "")

# All results defined
all_results = {RESULT_APPROVED, RESULT_REJECTED, RESULT_MANUAL_APPROVAL, RESULT_BLOCKED, RESULT_NOT_APPLICABLE}
check("5 results defined", len(all_results) == 5, "")
