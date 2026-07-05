"""Policy Runtime Foundation — rule-based policy evaluation engine.

Evaluates strategic recommendations and platform snapshots against
defined policy rules to determine approval, rejection, or escalation.

100% stateless. All methods are @staticmethod. All models are frozen dataclasses.
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Any
from uuid import UUID, uuid4


# ------------------------------------------------------------------
# Constants
# ------------------------------------------------------------------

RESULT_APPROVED = "APPROVED"
RESULT_REJECTED = "REJECTED"
RESULT_MANUAL_APPROVAL = "MANUAL_APPROVAL"
RESULT_BLOCKED = "BLOCKED"
RESULT_NOT_APPLICABLE = "NOT_APPLICABLE"

CATEGORY_SECURITY = "Security"
CATEGORY_COMPLIANCE = "Compliance"
CATEGORY_COST = "Cost"
CATEGORY_PERFORMANCE = "Performance"
CATEGORY_WORKFLOW = "Workflow"
CATEGORY_KNOWLEDGE = "Knowledge"
CATEGORY_LEARNING = "Learning"
CATEGORY_SKILL = "Skill"
CATEGORY_MONITORING = "Monitoring"
CATEGORY_STRATEGY = "Strategy"
CATEGORY_COMPANY = "Company"
CATEGORY_PROVIDER = "Provider"
CATEGORY_MODEL = "Model"
CATEGORY_EMPLOYEE = "Employee"
CATEGORY_DEPARTMENT = "Department"

OPERATOR_GT = "gt"
OPERATOR_GTE = "gte"
OPERATOR_LT = "lt"
OPERATOR_LTE = "lte"
OPERATOR_EQ = "eq"
OPERATOR_NE = "ne"
OPERATOR_IN = "in"
OPERATOR_CONTAINS = "contains"

PRIORITY_LOW = "LOW"
PRIORITY_MEDIUM = "MEDIUM"
PRIORITY_HIGH = "HIGH"
PRIORITY_CRITICAL = "CRITICAL"

_PRIORITY_ORDER = {PRIORITY_LOW: 0, PRIORITY_MEDIUM: 1, PRIORITY_HIGH: 2, PRIORITY_CRITICAL: 3}

_RESULT_ORDER = {
    RESULT_BLOCKED: 0,
    RESULT_REJECTED: 1,
    RESULT_MANUAL_APPROVAL: 2,
    RESULT_APPROVED: 3,
    RESULT_NOT_APPLICABLE: 4,
}


# ------------------------------------------------------------------
# Data models
# ------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class PolicyRule:
    """A single policy rule that defines evaluation conditions."""

    rule_id: UUID
    name: str
    category: str
    description: str
    field: str
    operator: str
    value: Any
    result_on_match: str
    result_on_mismatch: str
    priority: str = PRIORITY_MEDIUM
    metadata: dict[str, Any] = field(default_factory=dict)
    created_at: float = 0.0


@dataclass(frozen=True, slots=True)
class PolicyEvaluation:
    """Outcome of evaluating a single rule against a single target."""

    rule_id: UUID
    rule_name: str
    target_id: str
    category: str
    result: str
    reason: str
    metadata: dict[str, Any] = field(default_factory=dict)
    evaluated_at: float = 0.0


@dataclass(frozen=True, slots=True)
class PolicySnapshot:
    """Snapshot of all policy evaluations at a point in time."""

    evaluations: tuple[PolicyEvaluation, ...] = field(default_factory=tuple)
    results_summary: dict[str, int] = field(default_factory=dict)
    rules_applied: int = 0
    created_at: float = 0.0
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class PolicyTrace:
    """Metadata about a policy evaluation operation."""

    rules_evaluated: int = 0
    recommendations_evaluated: int = 0
    duration_ms: float = 0.0
    stages: tuple[str, ...] = field(default_factory=tuple)
    metrics: dict[str, float] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class PolicyResult:
    """Output of a policy evaluation operation."""

    success: bool
    snapshot: PolicySnapshot | None = None
    trace: PolicyTrace | None = None
    error_message: str = ""


# ------------------------------------------------------------------
# Helpers
# ------------------------------------------------------------------


def _now() -> float:
    return time.time()


def _build_snapshot(
    evaluations: list[PolicyEvaluation],
    metadata: dict[str, Any] | None = None,
) -> PolicySnapshot:
    """Build a PolicySnapshot from a list of evaluations."""
    summary: dict[str, int] = {}
    for ev in evaluations:
        summary[ev.result] = summary.get(ev.result, 0) + 1
    return PolicySnapshot(
        evaluations=tuple(evaluations),
        results_summary=dict(sorted(summary.items(), key=lambda x: _RESULT_ORDER.get(x[0], 99))),
        rules_applied=len(evaluations),
        created_at=_now(),
        metadata=metadata or {},
    )


def _extract_field(target: Any, field: str) -> Any:
    """Extract a field value from a target object using attribute access or dict lookup."""
    if isinstance(target, dict):
        return target.get(field)
    return getattr(target, field, None)


def _check_condition(value: Any, operator: str, threshold: Any) -> bool:
    """Check whether a field value satisfies a condition."""
    if value is None:
        return False
    try:
        if operator == OPERATOR_GT:
            return bool(value > threshold)
        elif operator == OPERATOR_GTE:
            return bool(value >= threshold)
        elif operator == OPERATOR_LT:
            return bool(value < threshold)
        elif operator == OPERATOR_LTE:
            return bool(value <= threshold)
        elif operator == OPERATOR_EQ:
            return bool(value == threshold)
        elif operator == OPERATOR_NE:
            return bool(value != threshold)
        elif operator == OPERATOR_IN:
            if hasattr(threshold, "__iter__") and not isinstance(threshold, str):
                return value in threshold
            return bool(value == threshold)
        elif operator == OPERATOR_CONTAINS:
            if isinstance(value, str) and isinstance(threshold, str):
                return threshold.lower() in value.lower()
            return False
        return False
    except (TypeError, ValueError):
        return False


def _safe_str_id(target: Any) -> str:
    """Get a string identifier for any target object."""
    if isinstance(target, UUID):
        return str(target)
    for attr in ("recommendation_id", "rule_id", "task_id", "workflow_id",
                 "snapshot_id", "evaluation_id", "id"):
        val = getattr(target, attr, None)
        if val is not None:
            return str(val)
    return str(id(target))


# ------------------------------------------------------------------
# FoundationPolicyRuntime
# ------------------------------------------------------------------


class FoundationPolicyRuntime:
    """Stateless policy evaluation runtime.

    Evaluates recommendations and snapshots against policy rules
    and produces deterministic approval/rejection outcomes.
    """

    # --------------------------------------------------------------
    # Core
    # --------------------------------------------------------------

    @staticmethod
    def create_rule(
        name: str,
        category: str,
        field: str,
        operator: str,
        value: Any,
        result_on_match: str = RESULT_APPROVED,
        result_on_mismatch: str = RESULT_REJECTED,
        priority: str = PRIORITY_MEDIUM,
        description: str = "",
        **metadata: Any,
    ) -> PolicyRule:
        """Create a new PolicyRule."""
        return PolicyRule(
            rule_id=uuid4(),
            name=name,
            category=category,
            description=description or f"{category}: {name}",
            field=field,
            operator=operator,
            value=value,
            result_on_match=result_on_match,
            result_on_mismatch=result_on_mismatch,
            priority=priority,
            metadata=metadata or {},
            created_at=_now(),
        )

    @staticmethod
    def create_snapshot(
        evaluations: list[PolicyEvaluation],
    ) -> PolicySnapshot:
        """Create a PolicySnapshot from a list of evaluations."""
        return _build_snapshot(evaluations)

    # --------------------------------------------------------------
    # Evaluation
    # --------------------------------------------------------------

    @staticmethod
    def evaluate(
        rule: PolicyRule,
        target: Any,
    ) -> PolicyEvaluation:
        """Evaluate a single rule against a single target."""
        target_id = _safe_str_id(target)
        now = _now()

        if rule.value is None:
            return PolicyEvaluation(
                rule_id=rule.rule_id,
                rule_name=rule.name,
                target_id=target_id,
                category=rule.category,
                result=RESULT_NOT_APPLICABLE,
                reason=f"Rule '{rule.name}' has no comparison value (value is None)",
                evaluated_at=now,
            )

        field_value = _extract_field(target, rule.field)
        if field_value is None:
            return PolicyEvaluation(
                rule_id=rule.rule_id,
                rule_name=rule.name,
                target_id=target_id,
                category=rule.category,
                result=RESULT_NOT_APPLICABLE,
                reason=f"Field '{rule.field}' not found or is None on target {target_id}",
                evaluated_at=now,
            )

        try:
            condition_met = _check_condition(field_value, rule.operator, rule.value)
        except Exception as exc:
            return PolicyEvaluation(
                rule_id=rule.rule_id,
                rule_name=rule.name,
                target_id=target_id,
                category=rule.category,
                result=RESULT_BLOCKED,
                reason=f"Condition evaluation error: {exc}",
                evaluated_at=now,
            )

        if condition_met:
            result = rule.result_on_match
            reason = f"Condition met: {rule.field} {rule.operator} {rule.value} (actual: {field_value})"
        else:
            result = rule.result_on_mismatch
            reason = f"Condition not met: {rule.field} {rule.operator} {rule.value} (actual: {field_value})"

        return PolicyEvaluation(
            rule_id=rule.rule_id,
            rule_name=rule.name,
            target_id=target_id,
            category=rule.category,
            result=result,
            reason=reason,
            evaluated_at=now,
        )

    @staticmethod
    def evaluate_all(
        rules: list[PolicyRule],
        targets: list[Any],
    ) -> PolicyResult:
        """Evaluate all rules against all targets (cartesian product)."""
        start = _now()
        evaluations: list[PolicyEvaluation] = []
        stages = ["evaluate_all"]

        for target in targets:
            for rule in rules:
                ev = FoundationPolicyRuntime.evaluate(rule, target)
                evaluations.append(ev)

        snapshot = _build_snapshot(evaluations)
        duration = (_now() - start) * 1000.0
        trace = PolicyTrace(
            rules_evaluated=len(rules),
            recommendations_evaluated=len(targets),
            duration_ms=duration,
            stages=tuple(stages),
            metrics={
                "total_evaluations": float(len(evaluations)),
                "total_rules": float(len(rules)),
                "total_targets": float(len(targets)),
            },
        )
        return PolicyResult(success=True, snapshot=snapshot, trace=trace)

    # --------------------------------------------------------------
    # Filtering
    # --------------------------------------------------------------

    @staticmethod
    def approve(
        evaluations: list[PolicyEvaluation],
    ) -> list[PolicyEvaluation]:
        """Filter evaluations that were APPROVED."""
        return [e for e in evaluations if e.result == RESULT_APPROVED]

    @staticmethod
    def reject(
        evaluations: list[PolicyEvaluation],
    ) -> list[PolicyEvaluation]:
        """Filter evaluations that were REJECTED."""
        return [e for e in evaluations if e.result == RESULT_REJECTED]

    @staticmethod
    def requires_approval(
        evaluations: list[PolicyEvaluation],
    ) -> list[PolicyEvaluation]:
        """Filter evaluations that require MANUAL_APPROVAL."""
        return [e for e in evaluations if e.result == RESULT_MANUAL_APPROVAL]

    @staticmethod
    def blocked(
        evaluations: list[PolicyEvaluation],
    ) -> list[PolicyEvaluation]:
        """Filter evaluations that are BLOCKED."""
        return [e for e in evaluations if e.result == RESULT_BLOCKED]

    # --------------------------------------------------------------
    # Prioritize & filter rules
    # --------------------------------------------------------------

    @staticmethod
    def prioritize(
        rules: list[PolicyRule],
    ) -> list[PolicyRule]:
        """Sort rules by priority (CRITICAL first)."""
        def sort_key(r: PolicyRule) -> int:
            return -_PRIORITY_ORDER.get(r.priority, 0)
        return sorted(rules, key=sort_key)

    @staticmethod
    def filter_rules(
        rules: list[PolicyRule],
        category: str | None = None,
        result: str | None = None,
        priority: str | None = None,
    ) -> list[PolicyRule]:
        """Filter rules by category, expected result, or priority."""
        result_list = list(rules)
        if category is not None:
            result_list = [r for r in result_list if r.category == category]
        if result is not None:
            result_list = [r for r in result_list
                          if r.result_on_match == result or r.result_on_mismatch == result]
        if priority is not None:
            result_list = [r for r in result_list if r.priority == priority]
        return result_list

    # --------------------------------------------------------------
    # Grouping
    # --------------------------------------------------------------

    @staticmethod
    def group_by_category(
        evaluations: list[PolicyEvaluation],
    ) -> dict[str, list[PolicyEvaluation]]:
        """Group evaluations by their rule category."""
        groups: dict[str, list[PolicyEvaluation]] = {}
        for e in evaluations:
            groups.setdefault(e.category, []).append(e)
        return dict(sorted(groups.items()))

    @staticmethod
    def group_by_result(
        evaluations: list[PolicyEvaluation],
    ) -> dict[str, list[PolicyEvaluation]]:
        """Group evaluations by their result."""
        groups: dict[str, list[PolicyEvaluation]] = {}
        for e in evaluations:
            groups.setdefault(e.result, []).append(e)
        return dict(sorted(groups.items(), key=lambda x: _RESULT_ORDER.get(x[0], 99)))

    # --------------------------------------------------------------
    # Merge
    # --------------------------------------------------------------

    @staticmethod
    def merge(
        snapshots: list[PolicySnapshot],
    ) -> PolicySnapshot:
        """Merge multiple PolicySnapshots into one deduplicated snapshot."""
        all_evals: list[PolicyEvaluation] = []
        merged_metadata: dict[str, Any] = {}
        seen: set[tuple[UUID, str]] = set()
        for s in snapshots:
            for ev in s.evaluations:
                key = (ev.rule_id, ev.target_id)
                if key not in seen:
                    all_evals.append(ev)
                    seen.add(key)
            merged_metadata.update(s.metadata)
        return _build_snapshot(all_evals, merged_metadata)

    # --------------------------------------------------------------
    # Trace & Result
    # --------------------------------------------------------------

    @staticmethod
    def build_trace(
        rules_evaluated: int = 0,
        recommendations_evaluated: int = 0,
        duration_ms: float = 0.0,
        stages: list[str] | None = None,
        metrics: dict[str, float] | None = None,
    ) -> PolicyTrace:
        """Create a PolicyTrace from raw data."""
        return PolicyTrace(
            rules_evaluated=rules_evaluated,
            recommendations_evaluated=recommendations_evaluated,
            duration_ms=duration_ms,
            stages=tuple(stages or []),
            metrics=metrics or {},
        )

    @staticmethod
    def build_result(
        snapshot: PolicySnapshot,
        stages: list[str] | None = None,
        metrics: dict[str, float] | None = None,
    ) -> PolicyResult:
        """Wrap a snapshot in a PolicyResult."""
        now = _now()
        trace = PolicyTrace(
            rules_evaluated=snapshot.rules_applied,
            recommendations_evaluated=len(snapshot.evaluations),
            stages=tuple(stages or []),
            metrics=metrics or {},
        )
        return PolicyResult(success=True, snapshot=snapshot, trace=trace)
