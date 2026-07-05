"""Typed models for the Affiliate Deals Department.

This department prepares affiliate deal operations without doing real
posting, scraping, ad buying, or WhatsApp automation. All objects are
small frozen+slots dataclasses so the first implementation remains
deterministic and easy to inspect.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any
from uuid import UUID, uuid4


DEFAULT_DISCLOSURE = (
    "🔎 Link de afiliado: posso receber comissão se você comprar por ele."
)


@dataclass(frozen=True, slots=True)
class MarketplaceSource:
    """Marketplace where a deal was found."""

    name: str = "amazon"
    display_name: str = "Amazon"
    country: str = "BR"
    allowed: bool = True
    trust_score: float = 0.85
    supports_affiliate_links: bool = True
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class PriceSnapshot:
    """Current and reference pricing for a product offer."""

    currency: str = "BRL"
    old_price: float | None = None
    current_price: float = 0.0
    payment_terms: str = ""
    shipping_notes: str = ""
    historical_low_price: float | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    @property
    def discount_amount(self) -> float:
        if self.old_price is None:
            return 0.0
        return max(0.0, round(self.old_price - self.current_price, 2))

    @property
    def discount_percent(self) -> float:
        if self.old_price is None or self.old_price <= 0:
            return 0.0
        return round(self.discount_amount / self.old_price * 100.0, 2)


@dataclass(frozen=True, slots=True)
class CouponInfo:
    """Optional coupon attached to an offer."""

    code: str = ""
    description: str = ""
    discount_value: float | None = None
    expires_at: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)

    @property
    def present(self) -> bool:
        return bool(self.code.strip())


@dataclass(frozen=True, slots=True)
class AffiliateLink:
    """Affiliate link information used in offer messages."""

    original_url: str = ""
    affiliate_url: str = ""
    tracking_id: str = ""
    short_url: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)

    @property
    def public_url(self) -> str:
        return self.short_url or self.affiliate_url or self.original_url

    @property
    def has_affiliate_target(self) -> bool:
        return bool(self.affiliate_url or self.short_url)


@dataclass(frozen=True, slots=True)
class ProductOffer:
    """A candidate affiliate deal."""

    offer_id: UUID = field(default_factory=uuid4)
    marketplace: MarketplaceSource = field(default_factory=MarketplaceSource)
    product_name: str = ""
    category: str = ""
    audience: str = ""
    product_url: str = ""
    image_url: str = ""
    price: PriceSnapshot = field(default_factory=PriceSnapshot)
    coupon: CouponInfo = field(default_factory=CouponInfo)
    affiliate: AffiliateLink = field(default_factory=AffiliateLink)
    urgency_level: str = "medium"
    stock_status: str = "unknown"
    source_label: str = ""
    risk_flags: tuple[str, ...] = field(default_factory=tuple)
    metadata: dict[str, Any] = field(default_factory=dict)

    @property
    def discount_percent(self) -> float:
        return self.price.discount_percent

    @property
    def has_coupon(self) -> bool:
        return self.coupon.present


@dataclass(frozen=True, slots=True)
class DealScore:
    """Rule-based deal scoring output."""

    score_total: float = 0.0
    discount_score: float = 0.0
    trust_score: float = 0.0
    coupon_score: float = 0.0
    urgency_score: float = 0.0
    margin_score: float = 0.0
    risk_penalty: float = 0.0
    recommendation: str = "needs_review"
    reasons: tuple[str, ...] = field(default_factory=tuple)


@dataclass(frozen=True, slots=True)
class OfferMessage:
    """Message prepared for Telegram, WhatsApp manual, or a website."""

    channel: str = "telegram"
    title: str = ""
    body: str = ""
    disclosure_text: str = DEFAULT_DISCLOSURE
    hashtags: tuple[str, ...] = field(default_factory=tuple)
    character_count: int = 0
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class OfferCreative:
    """Creative plan for a deal card, post, reel, or ad asset."""

    creative_type: str = "offer_card"
    headline: str = ""
    image_url: str = ""
    layout: str = "price_drop_card"
    color_theme: str = "marketplace_neutral"
    callouts: tuple[str, ...] = field(default_factory=tuple)
    requires_image_enhancement: bool = True
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class PublishingChannel:
    """Destination channel prepared by the department."""

    name: str = "telegram"
    mode: str = "prepared"
    supports_auto_publish: bool = False
    requires_human_approval: bool = True
    notes: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class PublishingPlan:
    """Publication plan produced after scoring and compliance."""

    channel: PublishingChannel = field(default_factory=PublishingChannel)
    status: str = "pending_approval"
    scheduled_window: str = ""
    message_preview: str = ""
    creative_brief: str = ""
    approval_required: bool = True
    blocked_reason: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class ComplianceCheck:
    """Rule-based compliance validation for affiliate offers."""

    passed: bool = False
    issues: tuple[str, ...] = field(default_factory=tuple)
    warnings: tuple[str, ...] = field(default_factory=tuple)
    disclosure_text: str = DEFAULT_DISCLOSURE
    requires_human_approval: bool = True
    automatic_whatsapp_blocked: bool = True
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class AudienceGrowthPlan:
    """Audience acquisition and page warmup plan."""

    primary_funnel: str = "facebook_page_to_telegram"
    warmup_goal_followers: int = 5000
    warmup_days: int = 30
    daily_organic_posts: int = 1
    daily_deal_posts: int = 10
    paid_budget_brl: float = 0.0
    target_channels: tuple[str, ...] = ("facebook_page", "instagram", "telegram")
    stage: str = "warmup"
    metrics_to_track: tuple[str, ...] = (
        "cost_per_follower",
        "cost_per_telegram_member",
        "telegram_click_rate",
        "commission_per_day",
        "roi",
    )
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class FunnelMetrics:
    """Initial deterministic metrics structure for the affiliate funnel."""

    ad_spend_brl: float = 0.0
    followers_gained: int = 0
    telegram_members: int = 0
    offer_clicks: int = 0
    commissions_brl: float = 0.0
    roi_percent: float = 0.0
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class DealCampaign:
    """Campaign context for a batch of affiliate deals."""

    campaign_id: UUID = field(default_factory=uuid4)
    name: str = "Affiliate Deals"
    campaign_type: str = "affiliate_deals"
    niche: str = "tech_gamer"
    target_audience: str = ""
    tone: str = "direct"
    language: str = "pt-BR"
    preferred_marketplaces: tuple[str, ...] = ("amazon", "mercado_livre", "shopee")
    preferred_channels: tuple[str, ...] = ("telegram", "website", "whatsapp_manual")
    disclosure_text: str = DEFAULT_DISCLOSURE
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class AffiliateDealTask:
    """Complete task assigned to AffiliateDealsEmployee."""

    task_id: UUID
    title: str
    campaign: DealCampaign = field(default_factory=DealCampaign)
    offers: tuple[ProductOffer, ...] = field(default_factory=tuple)
    preferred_channel: str = "telegram"
    audience_growth_plan: AudienceGrowthPlan = field(default_factory=AudienceGrowthPlan)
    funnel_metrics: FunnelMetrics = field(default_factory=FunnelMetrics)
    require_human_approval: bool = True
    auto_publish_allowed: bool = False
    disclosure_text: str = DEFAULT_DISCLOSURE
    metadata: dict[str, Any] = field(default_factory=dict)

    @property
    def requires_capabilities(self) -> tuple[str, ...]:
        needed = [
            "web_search",
            "browser_automation",
            "text_generation",
            "image_editing",
            "social_media",
            "storage",
        ]
        if self.metadata.get("requires_document_export"):
            needed.append("document_generation")
        return tuple(dict.fromkeys(needed))


@dataclass(frozen=True, slots=True)
class DealMetrics:
    """Production metrics specific to affiliate deals."""

    offers_analyzed: int = 0
    offers_approved: int = 0
    offers_rejected: int = 0
    pending_approvals: int = 0
    posts_prepared: int = 0
    last_score: float = 0.0
    last_recommendation: str = ""
    marketplace: str = ""
    publishing_channel: str = ""
    audience_funnel: str = ""
    quality_passed: bool = False
