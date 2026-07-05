"""Typed models for the Product Research Department."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any
from uuid import UUID, uuid4


@dataclass(frozen=True, slots=True)
class MarketplaceSignal:
    """One observed market signal for a product candidate."""

    name: str
    value: float = 0.0
    weight: float = 1.0
    source: str = ""
    note: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)

    @property
    def weighted_value(self) -> float:
        return max(0.0, self.value) * max(0.0, self.weight)


@dataclass(frozen=True, slots=True)
class ProductCandidate:
    """A raw or semi-enriched product idea before affiliate production."""

    candidate_id: UUID = field(default_factory=uuid4)
    product_name: str = ""
    marketplace: str = ""
    category: str = ""
    niche: str = ""
    source_url: str = ""
    affiliate_url: str = ""
    image_url: str = ""
    current_price: float = 0.0
    old_price: float | None = None
    commission_percent: float = 0.0
    marketplace_trust: float = 0.65
    demand_signals: tuple[MarketplaceSignal, ...] = field(default_factory=tuple)
    creative_signals: tuple[MarketplaceSignal, ...] = field(default_factory=tuple)
    competition_level: str = "medium"
    saturation_level: str = "medium"
    risk_flags: tuple[str, ...] = field(default_factory=tuple)
    notes: tuple[str, ...] = field(default_factory=tuple)
    metadata: dict[str, Any] = field(default_factory=dict)

    @property
    def discount_percent(self) -> float:
        if self.old_price is None or self.old_price <= 0:
            return 0.0
        return round(max(0.0, self.old_price - self.current_price) / self.old_price * 100.0, 2)

    @property
    def has_affiliate_target(self) -> bool:
        return bool(self.affiliate_url.strip())


@dataclass(frozen=True, slots=True)
class ProductResearchBrief:
    """Research assignment for product discovery."""

    task_id: UUID
    title: str
    objective: str = "Find winning product candidates for affiliate content."
    target_market: str = "BR"
    niches: tuple[str, ...] = field(default_factory=tuple)
    source_platforms: tuple[str, ...] = field(default_factory=tuple)
    candidates: tuple[ProductCandidate, ...] = field(default_factory=tuple)
    shortlist_size: int = 5
    require_affiliate_url: bool = False
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class ProductResearchFinding:
    """Scored result for one product candidate."""

    candidate: ProductCandidate
    score_total: float = 0.0
    demand_score: float = 0.0
    margin_score: float = 0.0
    creative_score: float = 0.0
    competition_score: float = 0.0
    trust_score: float = 0.0
    risk_penalty: float = 0.0
    recommendation: str = "needs_review"
    reasons: tuple[str, ...] = field(default_factory=tuple)

    def to_public_dict(self) -> dict[str, Any]:
        c = self.candidate
        return {
            "candidate_id": str(c.candidate_id),
            "product_name": c.product_name,
            "marketplace": c.marketplace,
            "category": c.category,
            "niche": c.niche,
            "source_url": c.source_url,
            "affiliate_url": c.affiliate_url,
            "image_url": c.image_url,
            "current_price": c.current_price,
            "old_price": c.old_price,
            "discount_percent": c.discount_percent,
            "commission_percent": c.commission_percent,
            "score_total": self.score_total,
            "demand_score": self.demand_score,
            "margin_score": self.margin_score,
            "creative_score": self.creative_score,
            "competition_score": self.competition_score,
            "trust_score": self.trust_score,
            "risk_penalty": self.risk_penalty,
            "recommendation": self.recommendation,
            "reasons": list(self.reasons),
            "risk_flags": list(c.risk_flags),
            "notes": list(c.notes),
            "metadata": dict(c.metadata),
        }


@dataclass(frozen=True, slots=True)
class ProductResearchReport:
    """Final report delivered by the Product Research Department."""

    brief_title: str
    total_candidates: int = 0
    shortlisted: tuple[ProductResearchFinding, ...] = field(default_factory=tuple)
    findings: tuple[ProductResearchFinding, ...] = field(default_factory=tuple)
    rejected_count: int = 0
    needs_review_count: int = 0
    next_actions: tuple[str, ...] = field(default_factory=tuple)
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_public_dict(self) -> dict[str, Any]:
        return {
            "brief_title": self.brief_title,
            "total_candidates": self.total_candidates,
            "shortlisted": [f.to_public_dict() for f in self.shortlisted],
            "findings": [f.to_public_dict() for f in self.findings],
            "rejected_count": self.rejected_count,
            "needs_review_count": self.needs_review_count,
            "next_actions": list(self.next_actions),
            "metadata": dict(self.metadata),
        }


@dataclass(frozen=True, slots=True)
class ProductResearchMetrics:
    """Metrics accumulated across product research."""

    total_stages: int = 0
    completed_stages: int = 0
    failed_stages: int = 0
    candidates_analyzed: int = 0
    shortlisted_count: int = 0
    rejected_count: int = 0
    average_score: float = 0.0
    top_score: float = 0.0
    top_marketplace: str = ""
    top_niche: str = ""
    quality_passed: bool = False
    quality_corrections: tuple[str, ...] = field(default_factory=tuple)
    duration_minutes: float = 0.0
