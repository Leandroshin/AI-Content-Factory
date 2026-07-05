"""Foundation demo for the Policy Engine — no Runtime dependencies.

This demonstration uses only plain Python objects to construct
PolicyContext, Constraint definitions, and Rule definitions.
"""

from __future__ import annotations

from uuid import uuid4

from core.policies.runtime import (
    Constraint,
    PolicyContext,
    PolicyEngine,
    Rule,
)


def make_context(
    action: str,
    actor_id: str,
    actor_role: str = "employee",
    target_type: str = "",
    budget: float = 0.0,
    amount: float = 0.0,
) -> PolicyContext:
    """Helper to build a PolicyContext for demo scenarios."""
    attrs: dict[str, object] = {"role": actor_role}
    if actor_role == "manager":
        attrs["budget_limit"] = budget

    target_attrs: dict[str, object] = {}
    if target_type:
        target_attrs["type"] = target_type

    if amount > 0:
        target_attrs["amount"] = amount

    return PolicyContext(
        action=action,
        actor_id=actor_id,
        actor_attributes=attrs,
        target_id=f"target-{uuid4()}",
        target_attributes=target_attrs,
        snapshots={},
        metadata={"demo": True},
    )


# ------------------------------------------------------------------
# Demo: execution allowed
# ------------------------------------------------------------------


def demo_execution_allowed() -> None:
    """Scenario: Employee executes against an allowed action with no rules set."""
    context = make_context("read_report", "emp-001", actor_role="employee")

    result = PolicyEngine.evaluate(
        context,
        constraints=[],
        rules=[],
        policy_id="policy-demo-allow",
    )

    assert result.approved, "Expected approval — no constraints or rules"
    assert result.violation_code == ""
    assert result.trace.execution_order == ["constraints", "rules"]
    print(f"[PASS] demo_execution_allowed         | {result.approved}")


# ------------------------------------------------------------------
# Demo: execution denied by constraint
# ------------------------------------------------------------------


def demo_execution_denied_constraint() -> None:
    """Scenario: Employee tries to write to a restricted system.

    Hard constraint blocks the action regardless of rules.
    """
    context = make_context("write_production_db", "emp-001", actor_role="employee")

    def _no_production_write(ctx: PolicyContext) -> tuple[bool, str]:
        if ctx.action == "write_production_db":
            return False, "Employees cannot write to production databases"
        return True, ""

    constraints = [
        Constraint(
            constraint_id="no_prod_write",
            description="Block production database writes by non-admin",
            check=_no_production_write,
        )
    ]

    result = PolicyEngine.evaluate(context, constraints=constraints, rules=[])

    assert not result.approved, "Expected denial — constraint blocks production writes"
    assert result.violation_code == "no_prod_write"
    assert result.trace.constraints_checked["no_prod_write"] is False
    print(f"[PASS] demo_execution_denied_constraint | {result.approved}  (violation={result.violation_code})")


# ------------------------------------------------------------------
# Demo: execution blocked by rule
# ------------------------------------------------------------------


def demo_execution_blocked_by_rule() -> None:
    """Scenario: Manager tries to approve expense above their budget limit.

    Constraints pass, but a priority rule blocks the action.
    """
    context = make_context(
        "approve_expense", "mgr-001",
        actor_role="manager", budget=5000.0, amount=7500.0,
    )

    def _budget_limit_check(ctx: PolicyContext) -> tuple[bool, str]:
        limit = ctx.actor_attributes.get("budget_limit", 0)
        amount = ctx.target_attributes.get("amount", 0)
        if amount > limit:
            return False, f"Amount {amount} exceeds budget limit {limit}"
        return True, f"Amount {amount} within limit {limit}"

    rules = [
        Rule(
            rule_id="budget_limit",
            description="Manager must not approve expenses above their budget limit",
            check=_budget_limit_check,
            priority=10,
        )
    ]

    result = PolicyEngine.evaluate(context, constraints=[], rules=rules)

    assert not result.approved, "Expected denial — amount exceeds budget limit"
    assert result.violation_code == "budget_limit"
    assert result.trace.rules_evaluated["budget_limit"] is False
    print(f"[PASS] demo_execution_blocked_by_rule   | {result.approved}  (violation={result.violation_code})")


# ------------------------------------------------------------------
# Demo: multiple rules, all pass
# ------------------------------------------------------------------


def demo_multiple_rules_pass() -> None:
    """Scenario: Manager approves within budget for an allowed action.

    All constraints and rules pass.
    """
    context = make_context(
        "approve_expense", "mgr-002",
        actor_role="manager", budget=10000.0, amount=3000.0,
    )

    def _budget_limit_check(ctx: PolicyContext) -> tuple[bool, str]:
        limit = ctx.actor_attributes.get("budget_limit", 0)
        amount = ctx.target_attributes.get("amount", 0)
        if amount > limit:
            return False, f"Amount {amount} exceeds limit {limit}"
        return True, f"Amount {amount} within limit {limit}"

    def _expense_requires_approval(ctx: PolicyContext) -> tuple[bool, str]:
        if ctx.action == "approve_expense":
            return True, "Expense approval action recognized"
        return False, "Action must be approve_expense"

    rules = [
        Rule(rule_id="expense_must_approve", description="Action must be expense approval", check=_expense_requires_approval, priority=5),
        Rule(rule_id="budget_limit", description="Budget limit check", check=_budget_limit_check, priority=10),
    ]

    result = PolicyEngine.evaluate(context, constraints=[], rules=rules)

    assert result.approved, "Expected approval — all rules pass"
    assert result.violation_code == ""
    assert len(result.trace.rules_evaluated) == 2
    print(f"[PASS] demo_multiple_rules_pass         | {result.approved}")


# ------------------------------------------------------------------
# Demo: rule priority respected
# ------------------------------------------------------------------


def demo_rule_priority() -> None:
    """Scenario: Rules are evaluated in priority order.

    Lower priority numbers run first.
    """
    context = make_context("any_action", "actor-001")
    execution_order: list[str] = []

    def _make_check(rule_id: str) -> object:
        def check(ctx: PolicyContext) -> tuple[bool, str]:
            execution_order.append(rule_id)
            return True, ""
        return check

    rules = [
        Rule(rule_id="high_priority", description="Priority 100", check=_make_check("high_priority"), priority=100),
        Rule(rule_id="low_priority", description="Priority 0", check=_make_check("low_priority"), priority=0),
        Rule(rule_id="mid_priority", description="Priority 50", check=_make_check("mid_priority"), priority=50),
    ]

    PolicyEngine.evaluate(context, constraints=[], rules=rules)

    # Expected order: low (0), mid (50), high (100)
    assert execution_order == ["low_priority", "mid_priority", "high_priority"], (
        f"Expected [low, mid, high] got {execution_order}"
    )
    print(f"[PASS] demo_rule_priority                | order={execution_order}")


# ------------------------------------------------------------------
# Demo: constraint before rules (fail fast)
# ------------------------------------------------------------------


def demo_constraint_before_rules() -> None:
    """Scenario: Constraint fails first so rules are never evaluated."""
    context = make_context("delete_system_logs", "emp-001", actor_role="employee")
    rule_was_evaluated: list[bool] = []

    def _block_deletion(ctx: PolicyContext) -> tuple[bool, str]:
        return False, "System log deletion is always blocked"

    def _rule_should_not_run(ctx: PolicyContext) -> tuple[bool, str]:
        rule_was_evaluated.append(True)
        return True, ""

    constraints = [
        Constraint(constraint_id="no_delete_logs", description="Block log deletion", check=_block_deletion),
    ]
    rules = [
        Rule(rule_id="should_not_run", description="Should never run", check=_rule_should_not_run),
    ]

    result = PolicyEngine.evaluate(context, constraints=constraints, rules=rules)

    assert not result.approved
    assert result.violation_code == "no_delete_logs"
    assert len(rule_was_evaluated) == 0, "Rules should not be evaluated when constraints fail"
    print(f"[PASS] demo_constraint_before_rules      | constraint blocked, rules skipped ({len(rule_was_evaluated)} evaluated)")


# ------------------------------------------------------------------
# Demo: evaluation trace completeness
# ------------------------------------------------------------------


def demo_trace_completeness() -> None:
    """Scenario: Verify complete PolicyTrace structure."""
    context = make_context("read_report", "emp-003")

    def _always_pass(ctx: PolicyContext) -> tuple[bool, str]:
        return True, "OK"

    constraints = [
        Constraint(constraint_id="c1", description="C1", check=_always_pass),
    ]
    rules = [
        Rule(rule_id="r1", description="R1", check=_always_pass),
    ]

    result = PolicyEngine.evaluate(context, constraints=constraints, rules=rules, policy_id="trace-check")

    assert result.approved
    assert isinstance(result.evaluation_id, uuid4().__class__)
    assert result.policy_id == "trace-check"
    assert result.violation_code == ""
    assert result.violation_detail == ""
    assert len(result.trace.constraints_checked) == 1
    assert len(result.trace.rules_evaluated) == 1
    assert len(result.trace.execution_order) == 2
    assert result.trace.execution_order == ["constraints", "rules"]
    assert result.trace.execution_time_ms >= 0
    print(f"[PASS] demo_trace_completeness            | trace has all fields populated")


# ------------------------------------------------------------------
# Main
# ------------------------------------------------------------------


def main() -> None:
    print("=" * 60)
    print("Policy Engine Foundation Demo")
    print("=" * 60)
    print()

    demo_execution_allowed()
    demo_execution_denied_constraint()
    demo_execution_blocked_by_rule()
    demo_multiple_rules_pass()
    demo_rule_priority()
    demo_constraint_before_rules()
    demo_trace_completeness()

    print()
    print("=" * 60)
    print("All demo scenarios passed.")
    print("=" * 60)


if __name__ == "__main__":
    main()
