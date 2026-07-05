"""Affiliate Deals Department - affiliate offer curation and growth planning."""

from __future__ import annotations

from .employee import (
    AffiliateDealCapability,
    AffiliateDealProductionMetrics,
    AffiliateDealsEmployee,
)
from .models import (
    DEFAULT_DISCLOSURE,
    AffiliateDealTask,
    AffiliateLink,
    AudienceGrowthPlan,
    ComplianceCheck,
    CouponInfo,
    DealCampaign,
    DealMetrics,
    DealScore,
    FunnelMetrics,
    MarketplaceSource,
    OfferCreative,
    OfferMessage,
    PriceSnapshot,
    ProductOffer,
    PublishingChannel,
    PublishingPlan,
)
from .pipeline import AffiliateDealsPipeline, PipelineStage

__all__ = [
    "DEFAULT_DISCLOSURE",
    "AffiliateDealCapability",
    "AffiliateDealProductionMetrics",
    "AffiliateDealTask",
    "AffiliateDealsEmployee",
    "AffiliateDealsPipeline",
    "AffiliateLink",
    "AudienceGrowthPlan",
    "ComplianceCheck",
    "CouponInfo",
    "DealCampaign",
    "DealMetrics",
    "DealScore",
    "FunnelMetrics",
    "MarketplaceSource",
    "OfferCreative",
    "OfferMessage",
    "PipelineStage",
    "PriceSnapshot",
    "ProductOffer",
    "PublishingChannel",
    "PublishingPlan",
]
