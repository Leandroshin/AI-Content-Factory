"""Runtime implementation for the Policy Engine foundation.

Stateless, deterministic policy engine that receives a context
and returns a policy verdict without mutating any runtime state.

Pipeline order: ConstraintValidator -> RuleEvaluator -> PolicyResult

This module has zero dependencies on other runtime modules.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable
from uuid import UUID, uuid4
import time


# ------------------------------------------------------------------
# Policy definition types (plain data, no persistence)
# ------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class Constraint:
    """A hard-block constraint definition.

    Constraints are evaluated first. If any constraint fails,
    the action is rejected immediately.
    """

    constraint_id: str
    description: str
    check: Callable[[Any], tuple[bool, str]]
    severity: str = "hard"  # hard | compliance | operational


@dataclass(frozen=True, slots=True)
class Rule:
    """A declarative Boolean rule definition.

    Rules are evaluated after constraints pass. Each rule
    checks a condition and returns pass/fail with explanation.
    """

    rule_id: str
    description: str
    check: Callable[[Any], tuple[bool, str]]
    priority: int = 0
    on_fail: str = "block"  # block | warn | log


# ------------------------------------------------------------------
# Immutable context, trace, and result
# ------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class PolicyContext:
    """Immutable input for policy evaluation.

    Contains only snapshots — never runtime objects.
    """

    action: str
    actor_id: str
    actor_attributes: dict[str, Any] = field(default_factory=dict)
    target_id: str = ""
    target_attributes: dict[str, Any] = field(default_factory=dict)
    snapshots: dict[str, Any] = field(default_factory=dict)
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class PolicyTrace:
    """Structured execution trace for a policy evaluation."""

    constraints_checked: dict[str, bool] = field(default_factory=dict)
    constraint_details: dict[str, str] = field(default_factory=dict)
    rules_evaluated: dict[str, bool] = field(default_factory=dict)
    rule_details: dict[str, str] = field(default_factory=dict)
    rejection_reasons: dict[str, str] = field(default_factory=dict)
    execution_order: list[str] = field(default_factory=list)
    execution_time_ms: float = 0.0


@dataclass(frozen=True, slots=True)
class PolicyResult:
    """Outcome of a Policy Engine evaluation."""

    evaluation_id: UUID
    approved: bool
    policy_id: str
    violation_code: str
    violation_detail: str
    trace: PolicyTrace


# ------------------------------------------------------------------
# Stateless sub-components
# ------------------------------------------------------------------


class ConstraintValidator:
    """Evaluates hard-block constraints against the PolicyContext.

    Runs first in the pipeline. Constraints are evaluated in order.
    If any constraint fails, the action is rejected immediately.
    """

    @staticmethod
    def validate(
        context: PolicyContext,
        constraints: list[Constraint],
    ) -> tuple[bool, dict[str, bool], dict[str, str], dict[str, str]]:
        """Evaluate all constraints. Returns (passed, results, details, rejections).

        Args:
            context: The immutable policy context.
            constraints: Ordered list of constraints to evaluate.

        Returns:
            A tuple of (all_passed, constraint_results, constraint_details, rejection_reasons).
        """
        results: dict[str, bool] = {}
        details: dict[str, str] = {}
        rejections: dict[str, str] = {}

        for constraint in constraints:
            passed, detail = constraint.check(context)
            results[constraint.constraint_id] = passed
            details[constraint.constraint_id] = detail
            if not passed:
                rejections[constraint.constraint_id] = detail

        all_passed = len(rejections) == 0
        return all_passed, results, details, rejections


class RuleEvaluator:
    """Executes declarative Boolean rules against the PolicyContext.

    Runs after constraint validation. Rules are evaluated in priority order.
    """

    @staticmethod
    def evaluate(
        context: PolicyContext,
        rules: list[Rule],
    ) -> tuple[bool, dict[str, bool], dict[str, str], dict[str, str]]:
        """Evaluate all rules. Returns (all_passed, results, details, rejections).

        Args:
            context: The immutable policy context.
            rules: List of rules to evaluate, ordered by priority.

        Returns:
            A tuple of (all_passed, rule_results, rule_details, rejection_reasons).
        """
        sorted_rules = sorted(rules, key=lambda r: r.priority)
        results: dict[str, bool] = {}
        details: dict[str, str] = {}
        rejections: dict[str, str] = {}

        for rule in sorted_rules:
            passed, detail = rule.check(context)
            results[rule.rule_id] = passed
            details[rule.rule_id] = detail
            if not passed and rule.on_fail == "block":
                rejections[rule.rule_id] = detail

        all_passed = len(rejections) == 0
        return all_passed, results, details, rejections


# ------------------------------------------------------------------
# Policy Engine (orchestrator)
# ------------------------------------------------------------------


class PolicyEngine:
    """Stateless orchestrator for policy evaluation.

    Pipeline:
      1. ConstraintValidator  (hard blocks — fail fast)
      2. RuleEvaluator         (Boolean rules — sorted by priority)
      3. PolicyResult          (assemble trace and verdict)
    """

    @staticmethod
    def evaluate(
        context: PolicyContext,
        constraints: list[Constraint],
        rules: list[Rule],
        policy_id: str = "default",
    ) -> PolicyResult:
        """Execute the full policy evaluation pipeline.

        Args:
            context: Immutable context with action, actor, target, snapshots.
            constraints: Hard-block constraints evaluated first.
            rules: Declarative rules evaluated after constraints.
            policy_id: Identifier for the policy being evaluated.

        Returns:
            A PolicyResult with verdict, violation details, and full trace.
        """
        start_time = time.perf_counter()
        trace = PolicyTrace()

        # --- Stage 1: ConstraintValidator ---
        trace.execution_order.append("constraints")
        constraints_passed, c_results, c_details, c_rejections = (
            ConstraintValidator.validate(context, constraints)
        )
        trace = _replace(trace,
            constraints_checked=c_results,
            constraint_details=c_details,
            rejection_reasons=c_rejections,
        )

        # Fail fast: hard constraint violation stops immediately
        if not constraints_passed:
            first_failure = next(iter(c_rejections.items()))
            elapsed = (time.perf_counter() - start_time) * 1000
            trace = _replace(trace, execution_time_ms=elapsed)
            return PolicyResult(
                evaluation_id=uuid4(),
                approved=False,
                policy_id=policy_id,
                violation_code=first_failure[0],
                violation_detail=first_failure[1],
                trace=trace,
            )

        # --- Stage 2: RuleEvaluator ---
        trace.execution_order.append("rules")
        rules_passed, r_results, r_details, r_rejections = (
            RuleEvaluator.evaluate(context, rules)
        )
        trace = _replace(trace,
            rules_evaluated=r_results,
            rule_details=r_details,
            rejection_reasons={**c_rejections, **r_rejections},
        )

        elapsed = (time.perf_counter() - start_time) * 1000
        trace = _replace(trace, execution_time_ms=elapsed)

        if not rules_passed:
            first_failure = next(iter(r_rejections.items()))
            return PolicyResult(
                evaluation_id=uuid4(),
                approved=False,
                policy_id=policy_id,
                violation_code=first_failure[0],
                violation_detail=first_failure[1],
                trace=trace,
            )

        # --- All passed ---
        return PolicyResult(
            evaluation_id=uuid4(),
            approved=True,
            policy_id=policy_id,
            violation_code="",
            violation_detail="",
            trace=trace,
        )


def _replace(trace: PolicyTrace, **changes: Any) -> PolicyTrace:
    """Return a new PolicyTrace with the given fields replaced."""
    kwargs = {
        "constraints_checked": trace.constraints_checked,
        "constraint_details": trace.constraint_details,
        "rules_evaluated": trace.rules_evaluated,
        "rule_details": trace.rule_details,
        "rejection_reasons": trace.rejection_reasons,
        "execution_order": trace.execution_order,
        "execution_time_ms": trace.execution_time_ms,
    }
    kwargs.update(changes)
    return PolicyTrace(**kwargs)
