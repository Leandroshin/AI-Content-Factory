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
from .platforms import (
    AffiliatePlatformEvaluation,
    AffiliatePlatformProfile,
    NoSpendAffiliatePlan,
    build_no_spend_affiliate_plan,
    default_affiliate_platform_profiles,
    evaluate_affiliate_platform,
    rank_affiliate_platforms,
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
    "AffiliatePlatformEvaluation",
    "AffiliatePlatformProfile",
    "AudienceGrowthPlan",
    "ComplianceCheck",
    "CouponInfo",
    "DealCampaign",
    "DealMetrics",
    "DealScore",
    "FunnelMetrics",
    "MarketplaceSource",
    "NoSpendAffiliatePlan",
    "OfferCreative",
    "OfferMessage",
    "PipelineStage",
    "PriceSnapshot",
    "ProductOffer",
    "PublishingChannel",
    "PublishingPlan",
    "build_no_spend_affiliate_plan",
    "default_affiliate_platform_profiles",
    "evaluate_affiliate_platform",
    "rank_affiliate_platforms",
]
