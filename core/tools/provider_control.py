"""Provider budget and usage controls for REAL tool execution."""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True, slots=True)
class ProviderBudget:
    """Safety limits for one external provider."""

    provider: str
    owner_approved: bool = False
    max_cost_usd: float = 0.0
    max_units: int = 0
    max_requests: int = 0
    notes: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class ProviderPricing:
    """Pricing estimate for one provider operation."""

    provider: str
    operation: str
    unit_name: str
    unit_cost_usd: float = 0.0
    pricing_note: str = ""


@dataclass(frozen=True, slots=True)
class ProviderBudgetDecision:
    """Decision returned before a REAL provider call."""

    provider: str
    operation: str
    allowed: bool
    reason: str
    units: int
    unit_name: str
    estimated_cost_usd: float
    spent_usd: float
    remaining_cost_usd: float | None
    used_units: int
    remaining_units: int | None
    request_count: int
    remaining_requests: int | None
    owner_approved: bool

    def to_dict(self) -> dict[str, Any]:
        """Return a JSON-safe representation for adapter outputs."""
        return {
            "provider": self.provider,
            "operation": self.operation,
            "allowed": self.allowed,
            "reason": self.reason,
            "units": self.units,
            "unit_name": self.unit_name,
            "estimated_cost_usd": self.estimated_cost_usd,
            "spent_usd": self.spent_usd,
            "remaining_cost_usd": self.remaining_cost_usd,
            "used_units": self.used_units,
            "remaining_units": self.remaining_units,
            "request_count": self.request_count,
            "remaining_requests": self.remaining_requests,
            "owner_approved": self.owner_approved,
        }


@dataclass(frozen=True, slots=True)
class ProviderUsageRecord:
    """Usage record for one provider execution attempt."""

    provider: str
    operation: str
    mode: str
    units: int
    unit_name: str
    estimated_cost_usd: float
    success: bool
    billable: bool
    timestamp: float = 0.0
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class ProviderUsageSummary:
    """Aggregated provider usage for UI/reporting."""

    provider: str
    requests: int
    successes: int
    failures: int
    billable_units: int
    estimated_cost_usd: float
    max_cost_usd: float = 0.0
    max_units: int = 0
    max_requests: int = 0
    owner_approved: bool = False


class ProviderBudgetGuard:
    """Pre-flight budget guard for REAL external provider usage."""

    def __init__(
        self,
        budgets: tuple[ProviderBudget, ...] = (),
        pricing: tuple[ProviderPricing, ...] = (),
    ) -> None:
        self._budgets: dict[str, ProviderBudget] = {}
        self._pricing: dict[tuple[str, str], ProviderPricing] = {}
        self._records: list[ProviderUsageRecord] = []
        for budget in budgets:
            self.configure_budget(budget)
        for price in pricing:
            self.configure_pricing(price)

    def configure_budget(self, budget: ProviderBudget) -> None:
        """Set or replace the budget for a provider."""
        self._budgets[self._key(budget.provider)] = budget

    def configure_pricing(self, pricing: ProviderPricing) -> None:
        """Set or replace pricing for a provider operation."""
        key = (self._key(pricing.provider), self._key(pricing.operation))
        self._pricing[key] = pricing

    def check(
        self,
        *,
        provider: str,
        operation: str,
        units: int,
        unit_name: str,
    ) -> ProviderBudgetDecision:
        """Return whether a provider operation is allowed before execution."""
        provider_key = self._key(provider)
        operation_key = self._key(operation)
        budget = self._budgets.get(provider_key)
        pricing = self._pricing.get((provider_key, operation_key))

        normalized_units = max(0, int(units))
        unit_cost = pricing.unit_cost_usd if pricing is not None else 0.0
        estimate = round(normalized_units * unit_cost, 6)
        spent = self.spent_usd(provider)
        used_units = self.used_units(provider)
        request_count = self.request_count(provider)

        if budget is None:
            return self._decision(
                provider, operation, False, "Provider budget is not configured.",
                normalized_units, unit_name, estimate, spent, None,
                used_units, None, request_count, None, False,
            )

        remaining_cost = (
            round(max(0.0, budget.max_cost_usd - spent), 6)
            if budget.max_cost_usd > 0 else None
        )
        remaining_units = (
            max(0, budget.max_units - used_units)
            if budget.max_units > 0 else None
        )
        remaining_requests = (
            max(0, budget.max_requests - request_count)
            if budget.max_requests > 0 else None
        )

        if not budget.owner_approved:
            return self._decision(
                provider, operation, False, "Owner approval is required for REAL provider usage.",
                normalized_units, unit_name, estimate, spent, remaining_cost,
                used_units, remaining_units, request_count, remaining_requests,
                False,
            )
        if budget.max_requests > 0 and request_count + 1 > budget.max_requests:
            return self._decision(
                provider, operation, False, "Provider request budget exceeded.",
                normalized_units, unit_name, estimate, spent, remaining_cost,
                used_units, remaining_units, request_count, remaining_requests,
                True,
            )
        if budget.max_units > 0 and used_units + normalized_units > budget.max_units:
            return self._decision(
                provider, operation, False, "Provider unit budget exceeded.",
                normalized_units, unit_name, estimate, spent, remaining_cost,
                used_units, remaining_units, request_count, remaining_requests,
                True,
            )
        if budget.max_cost_usd > 0 and spent + estimate > budget.max_cost_usd:
            return self._decision(
                provider, operation, False, "Provider cost budget exceeded.",
                normalized_units, unit_name, estimate, spent, remaining_cost,
                used_units, remaining_units, request_count, remaining_requests,
                True,
            )

        return self._decision(
            provider, operation, True, "Provider usage approved within budget.",
            normalized_units, unit_name, estimate, spent, remaining_cost,
            used_units, remaining_units, request_count, remaining_requests,
            True,
        )

    def record_usage(
        self,
        *,
        provider: str,
        operation: str,
        mode: str,
        units: int,
        unit_name: str,
        success: bool,
        billable: bool,
        metadata: dict[str, Any] | None = None,
    ) -> ProviderUsageRecord:
        """Record one provider execution attempt."""
        pricing = self._pricing.get((self._key(provider), self._key(operation)))
        unit_cost = pricing.unit_cost_usd if pricing is not None else 0.0
        estimated_cost = round(max(0, int(units)) * unit_cost, 6) if billable else 0.0
        record = ProviderUsageRecord(
            provider=provider,
            operation=operation,
            mode=mode,
            units=max(0, int(units)),
            unit_name=unit_name,
            estimated_cost_usd=estimated_cost,
            success=success,
            billable=billable,
            timestamp=time.time(),
            metadata=dict(metadata) if metadata else {},
        )
        self._records.append(record)
        return record

    def records(self) -> tuple[ProviderUsageRecord, ...]:
        """Return all usage records."""
        return tuple(self._records)

    def records_for(self, provider: str) -> tuple[ProviderUsageRecord, ...]:
        """Return usage records for one provider."""
        key = self._key(provider)
        return tuple(r for r in self._records if self._key(r.provider) == key)

    def spent_usd(self, provider: str) -> float:
        """Return billable estimated cost for one provider."""
        return round(sum(r.estimated_cost_usd for r in self.records_for(provider) if r.billable), 6)

    def used_units(self, provider: str) -> int:
        """Return billable units for one provider."""
        return sum(r.units for r in self.records_for(provider) if r.billable)

    def request_count(self, provider: str) -> int:
        """Return execution attempts for one provider."""
        return len(self.records_for(provider))

    def summary(self, provider: str) -> ProviderUsageSummary:
        """Aggregate usage for one provider."""
        records = self.records_for(provider)
        budget = self._budgets.get(self._key(provider))
        return ProviderUsageSummary(
            provider=provider,
            requests=len(records),
            successes=sum(1 for r in records if r.success),
            failures=sum(1 for r in records if not r.success),
            billable_units=sum(r.units for r in records if r.billable),
            estimated_cost_usd=round(sum(r.estimated_cost_usd for r in records if r.billable), 6),
            max_cost_usd=budget.max_cost_usd if budget is not None else 0.0,
            max_units=budget.max_units if budget is not None else 0,
            max_requests=budget.max_requests if budget is not None else 0,
            owner_approved=budget.owner_approved if budget is not None else False,
        )

    @staticmethod
    def _key(value: str) -> str:
        return value.strip().lower().replace(" ", "_")

    @staticmethod
    def _decision(
        provider: str,
        operation: str,
        allowed: bool,
        reason: str,
        units: int,
        unit_name: str,
        estimated_cost_usd: float,
        spent_usd: float,
        remaining_cost_usd: float | None,
        used_units: int,
        remaining_units: int | None,
        request_count: int,
        remaining_requests: int | None,
        owner_approved: bool,
    ) -> ProviderBudgetDecision:
        return ProviderBudgetDecision(
            provider=provider,
            operation=operation,
            allowed=allowed,
            reason=reason,
            units=units,
            unit_name=unit_name,
            estimated_cost_usd=estimated_cost_usd,
            spent_usd=spent_usd,
            remaining_cost_usd=remaining_cost_usd,
            used_units=used_units,
            remaining_units=remaining_units,
            request_count=request_count,
            remaining_requests=remaining_requests,
            owner_approved=owner_approved,
        )
