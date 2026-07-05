"""Quality Runtime — automatic validation for AI Company executions.

This runtime NEVER executes tasks. It ONLY validates results against
registered rules. Every decision is rule-based, no LLM, no AI.

Flow:
    Employee finishes task
        -> QualityRuntime.validate(execution_result)
            -> passes?  -> deliver
            -> fails?   -> generate_correction() -> return to DM -> retry
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any
from uuid import UUID, uuid4

from core.events.bus import EventBus
from core.events.domain_events import (
    QualityValidationFinished,
    QualityValidationStarted,
)


@dataclass(frozen=True, slots=True)
class QualityRule:
    id: UUID
    name: str
    description: str
    category: str  # "output_completeness" | "output_quality" | "process" | "consistency"
    severity: str  # "critical" | "major" | "minor" | "suggestion"
    criteria: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class QualityIssue:
    rule_id: UUID
    rule_name: str
    severity: str
    message: str
    context: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class QualityResult:
    rule_id: UUID
    rule_name: str
    passed: bool
    issues: tuple[QualityIssue, ...] = field(default_factory=tuple)
    metrics: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class QualityReport:
    report_id: UUID
    execution_id: UUID
    task_id: UUID | None
    timestamp: float
    results: tuple[QualityResult, ...] = field(default_factory=tuple)
    total_rules: int = 0
    passed_rules: int = 0
    failed_rules: int = 0
    passed: bool = False
    metadata: dict[str, Any] = field(default_factory=dict)


class QualityRuntime:
    """Rule-based validation runtime. No AI, no LLM — pure deterministic checks.

    Usage::

        qr = QualityRuntime(event_bus=bus)
        qr.register_rule("Output has no errors", "output_quality", "critical",
                           {"check_empty_error": True})
        report = qr.validate(execution_id, {"success": True, "error": ""})
        if not report.passed:
            corrections = qr.generate_correction(report)
    """

    def __init__(self, event_bus: EventBus | None = None) -> None:
        self._rules: dict[UUID, QualityRule] = {}
        self._reports: list[QualityReport] = []
        self._event_bus = event_bus

    # ------------------------------------------------------------------
    # Rule management
    # ------------------------------------------------------------------

    def register_rule(
        self,
        name: str,
        description: str,
        category: str,
        severity: str,
        criteria: dict[str, Any] | None = None,
    ) -> QualityRule:
        rule = QualityRule(
            id=uuid4(),
            name=name,
            description=description,
            category=category,
            severity=severity,
            criteria=criteria or {},
        )
        self._rules[rule.id] = rule
        return rule

    def unregister_rule(self, rule_id: UUID) -> bool:
        return self._rules.pop(rule_id, None) is not None

    def list_rules(
        self, category: str | None = None
    ) -> tuple[QualityRule, ...]:
        if category is None:
            return tuple(self._rules.values())
        return tuple(
            r for r in self._rules.values() if r.category == category
        )

    # ------------------------------------------------------------------
    # Validation
    # ------------------------------------------------------------------

    def validate(
        self,
        execution_id: UUID,
        execution_result: dict[str, Any],
        task_id: UUID | None = None,
    ) -> QualityReport:
        self._publish(
            QualityValidationStarted(
                execution_id=execution_id,
                task_id=task_id,
                timestamp=datetime.now().timestamp(),
                metadata={},
            )
        )

        results: list[QualityResult] = []
        for rule in self._rules.values():
            result = self._apply_rule(rule, execution_result)
            results.append(result)

        total = len(results)
        passed = sum(1 for r in results if r.passed)
        failed = total - passed

        report = QualityReport(
            report_id=uuid4(),
            execution_id=execution_id,
            task_id=task_id,
            timestamp=datetime.now().timestamp(),
            results=tuple(results),
            total_rules=total,
            passed_rules=passed,
            failed_rules=failed,
            passed=failed == 0,
            metadata={},
        )
        self._reports.append(report)

        self._publish(
            QualityValidationFinished(
                execution_id=execution_id,
                task_id=task_id,
                passed=report.passed,
                total_rules=total,
                passed_rules=passed,
                failed_rules=failed,
                timestamp=report.timestamp,
                metadata={},
            )
        )
        return report

    # ------------------------------------------------------------------
    # Built-in rule checks (deterministic, no AI)
    # ------------------------------------------------------------------

    def _apply_rule(
        self, rule: QualityRule, execution_result: dict[str, Any]
    ) -> QualityResult:
        issues: list[QualityIssue] = []

        if rule.category == "output_completeness":
            issues = self._check_completeness(rule, execution_result)
        elif rule.category == "output_quality":
            issues = self._check_quality(rule, execution_result)
        elif rule.category == "process":
            issues = self._check_process(rule, execution_result)
        elif rule.category == "consistency":
            issues = self._check_consistency(rule, execution_result)

        return QualityResult(
            rule_id=rule.id,
            rule_name=rule.name,
            passed=len(issues) == 0,
            issues=tuple(issues),
            metrics={"issues_count": len(issues)},
        )

    def _check_completeness(
        self, rule: QualityRule, result: dict[str, Any]
    ) -> list[QualityIssue]:
        issues: list[QualityIssue] = []
        required = rule.criteria.get("required_fields", [])
        for field in required:
            if field not in result or result.get(field) is None:
                issues.append(
                    QualityIssue(
                        rule_id=rule.id,
                        rule_name=rule.name,
                        severity=rule.severity,
                        message=f"Campo obrigatório '{field}' está ausente.",
                        context={"field": field},
                    )
                )
        return issues

    def _check_quality(
        self, rule: QualityRule, result: dict[str, Any]
    ) -> list[QualityIssue]:
        issues: list[QualityIssue] = []
        if result.get("error"):
            issues.append(
                QualityIssue(
                    rule_id=rule.id,
                    rule_name=rule.name,
                    severity="critical",
                    message="Execução possui erros.",
                    context={"error": result["error"]},
                )
            )
        if result.get("success") is False:
            issues.append(
                QualityIssue(
                    rule_id=rule.id,
                    rule_name=rule.name,
                    severity="critical",
                    message="Execução falhou.",
                    context={},
                )
            )
        return issues

    def _check_process(
        self, rule: QualityRule, result: dict[str, Any]
    ) -> list[QualityIssue]:
        issues: list[QualityIssue] = []
        max_duration = rule.criteria.get("max_duration_minutes")
        if max_duration is not None:
            duration = result.get("duration_minutes", 0)
            if duration > max_duration:
                issues.append(
                    QualityIssue(
                        rule_id=rule.id,
                        rule_name=rule.name,
                        severity=rule.severity,
                        message=f"Duração {duration}min excede máximo {max_duration}min.",
                        context={
                            "duration": duration,
                            "max": max_duration,
                        },
                    )
                )
        return issues

    def _check_consistency(
        self, rule: QualityRule, result: dict[str, Any]
    ) -> list[QualityIssue]:
        issues: list[QualityIssue] = []
        fields = rule.criteria.get("consistent_fields", [])
        if fields:
            values = [result.get(f) for f in fields]
            seen = {v for v in values if v is not None}
            if len(seen) > 1:
                issues.append(
                    QualityIssue(
                        rule_id=rule.id,
                        rule_name=rule.name,
                        severity=rule.severity,
                        message=f"Campos inconsistentes: {fields}",
                        context={
                            "fields": {f: result.get(f) for f in fields}
                        },
                    )
                )
        return issues

    # ------------------------------------------------------------------
    # Corrections & queries
    # ------------------------------------------------------------------

    def generate_correction(self, report: QualityReport) -> list[str]:
        corrections: list[str] = []
        for result in report.results:
            if not result.passed:
                for issue in result.issues:
                    corrections.append(
                        f"[{issue.severity.upper()}] {issue.message}"
                    )
        return corrections

    def last_report(self) -> QualityReport | None:
        return self._reports[-1] if self._reports else None

    def reports(self) -> tuple[QualityReport, ...]:
        return tuple(self._reports)

    def _publish(self, event: Any) -> None:
        if self._event_bus is not None:
            self._event_bus.publish(event)
