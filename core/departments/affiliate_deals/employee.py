"""AffiliateDealsEmployee specialized in affiliate offer operations."""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Any
from uuid import UUID

from core.company.department_manager import DepartmentManager
from core.company.quality import QualityRuntime
from core.company.specialist_employee import (
    EmployeeSkill,
    EmployeeStatus,
    ReceivedTask,
    TaskAccepted,
    TaskDecision,
)
from core.departments.affiliate_deals.models import (
    AffiliateDealTask,
    AffiliateLink,
    AudienceGrowthPlan,
    CouponInfo,
    DealCampaign,
    DealMetrics,
    FunnelMetrics,
    MarketplaceSource,
    PriceSnapshot,
    ProductOffer,
)
from core.departments.affiliate_deals.pipeline import (
    AffiliateDealsPipeline,
    PipelineStage,
)
from core.departments.base.employee import ProductionEmployee
from core.departments.base.pipeline import ProductionPipeline
from core.events.bus import EventBus
from core.runtime import CompanyRuntime as CoreCompanyRuntime
from core.tools.capabilities import Capability
from core.tools.registry import ToolRegistry
from core.tools.runtime import ToolRuntime


@dataclass(frozen=True, slots=True)
class AffiliateDealCapability:
    """Domain-specific affiliate deal capability metadata."""

    name: str
    proficiency: float = 0.5
    enabled: bool = True


@dataclass(frozen=True, slots=True)
class AffiliateDealProductionMetrics:
    """Metrics accumulated across an affiliate deal production run."""

    total_stages: int = 0
    completed_stages: int = 0
    failed_stages: int = 0
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
    quality_corrections: tuple[str, ...] = field(default_factory=tuple)
    duration_minutes: float = 0.0


class AffiliateDealsEmployee(ProductionEmployee):
    """Specialist employee for affiliate deal curation and growth planning."""

    _DEPARTMENT_KEYWORD = "affiliate_deals"

    def __init__(
        self,
        company_runtime: CoreCompanyRuntime,
        employee_id: UUID,
        skills: tuple[EmployeeSkill, ...] = (),
        *,
        event_bus: EventBus | None = None,
        department_manager: DepartmentManager | None = None,
        tool_runtime: ToolRuntime | None = None,
        tool_registry: ToolRegistry | None = None,
        quality_runtime: QualityRuntime | None = None,
    ) -> None:
        super().__init__(
            company_runtime=company_runtime,
            employee_id=employee_id,
            skills=skills,
            event_bus=event_bus,
            department_manager=department_manager,
            tool_runtime=tool_runtime,
            tool_registry=tool_registry,
            quality_runtime=quality_runtime,
        )
        self._affiliate_capabilities: dict[str, AffiliateDealCapability] = {
            "deal_research": AffiliateDealCapability("deal_research", 0.86),
            "price_validation": AffiliateDealCapability("price_validation", 0.84),
            "deal_scoring": AffiliateDealCapability("deal_scoring", 0.88),
            "affiliate_copywriting": AffiliateDealCapability("affiliate_copywriting", 0.9),
            "creative_briefing": AffiliateDealCapability("creative_briefing", 0.82),
            "affiliate_compliance": AffiliateDealCapability("affiliate_compliance", 0.87),
            "telegram_planning": AffiliateDealCapability("telegram_planning", 0.8),
            "whatsapp_manual_flow": AffiliateDealCapability("whatsapp_manual_flow", 0.72),
            "page_warmup": AffiliateDealCapability("page_warmup", 0.78),
            "traffic_metrics": AffiliateDealCapability("traffic_metrics", 0.76),
            "roi_optimization": AffiliateDealCapability("roi_optimization", 0.74),
        }
        self._current_affiliate_task: AffiliateDealTask | None = None

    @property
    def affiliate_capabilities(self) -> dict[str, AffiliateDealCapability]:
        return dict(self._affiliate_capabilities)

    @property
    def current_affiliate_task(self) -> AffiliateDealTask | None:
        return self._current_affiliate_task

    # ------------------------------------------------------------------
    # Task handling
    # ------------------------------------------------------------------

    def receive_task(self, task: ReceivedTask) -> TaskDecision:
        if not _is_affiliate_department(task.department):
            return super().receive_task(task)

        if self._workload >= self._max_workload:
            return super().receive_task(task)

        self._tasks[task.task_id] = task
        self._current_task_id = task.task_id
        self._workload += 1
        self._status = EmployeeStatus.ANALYZING

        self._current_affiliate_task = _coerce_affiliate_task(task)
        self._pipeline = AffiliateDealsPipeline(self._current_affiliate_task)

        self._publish(
            TaskAccepted(
                employee_id=self._employee_id,
                task_id=task.task_id,
                title=task.title,
                difficulty=0.55,
                estimated_time_minutes=self._estimate_duration(task.context),
                timestamp=time.time(),
            )
        )
        return TaskDecision.ACCEPTED

    def _check_reject(self, task: ReceivedTask) -> str | None:
        if not _is_affiliate_department(task.department):
            return f"Department '{task.department}' is not affiliate_deals"
        if self._workload >= self._max_workload:
            return "Workload limit reached (max 3)"
        return None

    # ------------------------------------------------------------------
    # Pipeline hooks
    # ------------------------------------------------------------------

    def _build_pipeline(self, task: ReceivedTask) -> ProductionPipeline:
        return AffiliateDealsPipeline(self._current_affiliate_task)

    def _estimate_duration(self, ctx: dict[str, Any]) -> int:
        offers = ctx.get("offers", ctx.get("offer", ()))
        offers_count = len(offers) if isinstance(offers, (tuple, list)) else 1
        channel = str(ctx.get("preferred_channel", "telegram")).lower()
        channel_factor = 3 if "whatsapp" in channel else 1
        return max(4, 5 + offers_count * 2 + channel_factor)

    def _get_production_type(self) -> str:
        if self._current_affiliate_task is not None:
            return self._current_affiliate_task.campaign.campaign_type
        return "affiliate_deals"

    def _build_output_from_stages(
        self, final_output: dict[str, Any], summary_parts: list[str],
    ) -> None:
        for slog in self._pipeline.stages_log:
            if slog.stage == PipelineStage.DELIVERING.value:
                final_output.update(slog.output)
                summary_parts.append(slog.summary)
            elif slog.stage in (
                PipelineStage.SCORING_DEAL.value,
                PipelineStage.COMPLIANCE_REVIEW.value,
                PipelineStage.PUBLISHING_PREPARATION.value,
                PipelineStage.PLANNING_AUDIENCE_GROWTH.value,
            ):
                final_output.update(slog.output)

    def _build_metrics(
        self,
        stages_completed: int,
        stages_failed: int,
        final_output: dict[str, Any],
        duration: float,
    ) -> AffiliateDealProductionMetrics:
        recommendation = final_output.get("recommendation", "")
        status = final_output.get("publishing_status", "")
        compliance_passed = final_output.get("compliance_passed", False)
        product = final_output.get("product_offer", {})
        marketplace = product.get("marketplace", {}).get("name", "") if product else ""
        plan = final_output.get("publishing_plan", {})
        channel = plan.get("channel", {}).get("name", "") if plan else ""

        return AffiliateDealProductionMetrics(
            total_stages=stages_completed + stages_failed,
            completed_stages=stages_completed,
            failed_stages=stages_failed,
            offers_analyzed=final_output.get("offers_analyzed", 0),
            offers_approved=1 if recommendation in ("post_now", "needs_review") and compliance_passed else 0,
            offers_rejected=1 if recommendation == "skip" or status in ("rejected", "blocked") else 0,
            pending_approvals=1 if status == "pending_approval" else 0,
            posts_prepared=1 if status in ("pending_approval", "ready") else 0,
            last_score=final_output.get("score_total", 0.0),
            last_recommendation=recommendation,
            marketplace=marketplace,
            publishing_channel=channel,
            audience_funnel=final_output.get("primary_funnel", ""),
            quality_passed=final_output.get("quality_passed", True),
            quality_corrections=tuple(final_output.get("quality_issues", [])),
            duration_minutes=round(duration, 2),
        )

    def _build_summary(self, success: bool, summary_parts: list[str]) -> str:
        if summary_parts:
            return " | ".join(summary_parts)
        return "Affiliate deal production completed" if success else "Affiliate deal production failed"

    # ------------------------------------------------------------------
    # Quality
    # ------------------------------------------------------------------

    def _run_quality_check(self, output: dict[str, Any]) -> tuple[bool, list[str]]:
        if self._quality_runtime is None:
            return True, []

        exec_id = self._current_task_id or UUID(int=0)
        report = self._quality_runtime.validate(
            exec_id,
            {
                "success": output.get("error", "") == "",
                "error": output.get("error", ""),
                "offer_message": output.get("message_body", ""),
                "disclosure_text": output.get("disclosure_text", ""),
                "compliance_passed": output.get("compliance_passed", False),
                "publishing_plan": output.get("publishing_plan", {}),
                "publishing_status": output.get("publishing_status", ""),
                "score_total": output.get("score_total", 0.0),
                "recommendation": output.get("recommendation", ""),
                "channel": output.get("publishing_plan", {}).get("channel", {}).get("name", ""),
                "requires_human_approval": output.get("requires_human_approval", True),
            },
        )

        if report.passed:
            return True, []
        return False, self._quality_runtime.generate_correction(report)

    # ------------------------------------------------------------------
    # Capabilities and state
    # ------------------------------------------------------------------

    def analyze_capability_needs(self) -> tuple[Capability, ...]:
        needed = [
            Capability.WEB_SEARCH,
            Capability.BROWSER_AUTOMATION,
            Capability.TEXT_GENERATION,
            Capability.IMAGE_EDITING,
            Capability.SOCIAL_MEDIA,
            Capability.STORAGE,
        ]
        task = self._current_affiliate_task
        if task is not None and task.metadata.get("requires_document_export"):
            needed.append(Capability.DOCUMENT_GENERATION)
        return tuple(dict.fromkeys(needed))

    def state(self) -> dict[str, Any]:
        base = super().state()
        base["affiliate_capabilities"] = {
            k: {"name": v.name, "proficiency": v.proficiency, "enabled": v.enabled}
            for k, v in self._affiliate_capabilities.items()
        }
        base["current_affiliate_task"] = (
            {
                "title": self._current_affiliate_task.title,
                "campaign_type": self._current_affiliate_task.campaign.campaign_type,
                "niche": self._current_affiliate_task.campaign.niche,
                "preferred_channel": self._current_affiliate_task.preferred_channel,
                "offers": len(self._current_affiliate_task.offers),
            }
            if self._current_affiliate_task else None
        )
        metrics = base["production_metrics"]
        metrics["offers_analyzed"] = getattr(self._production_metrics, "offers_analyzed", 0)
        metrics["offers_approved"] = getattr(self._production_metrics, "offers_approved", 0)
        metrics["offers_rejected"] = getattr(self._production_metrics, "offers_rejected", 0)
        metrics["pending_approvals"] = getattr(self._production_metrics, "pending_approvals", 0)
        metrics["posts_prepared"] = getattr(self._production_metrics, "posts_prepared", 0)
        metrics["last_score"] = getattr(self._production_metrics, "last_score", 0.0)
        metrics["last_recommendation"] = getattr(self._production_metrics, "last_recommendation", "")
        metrics["publishing_channel"] = getattr(self._production_metrics, "publishing_channel", "")
        metrics["audience_funnel"] = getattr(self._production_metrics, "audience_funnel", "")
        return base


# ==================================================================
# Coercion helpers
# ==================================================================


def _is_affiliate_department(department: str) -> bool:
    lowered = department.lower()
    markers = ("affiliate", "deal", "oferta", "afiliada", "growth")
    return any(marker in lowered for marker in markers)


def _coerce_affiliate_task(task: ReceivedTask) -> AffiliateDealTask:
    ctx = task.context
    campaign = _coerce_campaign(ctx.get("campaign"), task, ctx)
    offers = _coerce_offers(ctx.get("offers", ctx.get("offer", ())))
    preferred_channel = ctx.get(
        "preferred_channel",
        (campaign.preferred_channels[0] if campaign.preferred_channels else "telegram"),
    )
    return AffiliateDealTask(
        task_id=task.task_id,
        title=task.title,
        campaign=campaign,
        offers=offers,
        preferred_channel=preferred_channel,
        audience_growth_plan=_coerce_audience_plan(ctx.get("audience_growth_plan")),
        funnel_metrics=_coerce_funnel_metrics(ctx.get("funnel_metrics")),
        require_human_approval=ctx.get("require_human_approval", True),
        auto_publish_allowed=ctx.get("auto_publish_allowed", False),
        disclosure_text=ctx.get("disclosure_text", campaign.disclosure_text),
        metadata=dict(ctx.get("metadata", {})) | {
            k: v for k, v in ctx.items()
            if k in ("requires_document_export", "requires_browser_research")
        },
    )


def _coerce_campaign(raw: Any, task: ReceivedTask, ctx: dict[str, Any]) -> DealCampaign:
    if isinstance(raw, DealCampaign):
        return raw
    data = raw if isinstance(raw, dict) else {}
    return DealCampaign(
        name=data.get("name", ctx.get("campaign_name", task.title)),
        campaign_type=data.get("campaign_type", ctx.get("campaign_type", "affiliate_deals")),
        niche=data.get("niche", ctx.get("niche", "tech_gamer")),
        target_audience=data.get("target_audience", ctx.get("target_audience", "")),
        tone=data.get("tone", ctx.get("tone", "direct")),
        language=data.get("language", ctx.get("language", "pt-BR")),
        preferred_marketplaces=tuple(
            data.get("preferred_marketplaces", ctx.get("preferred_marketplaces", ("amazon", "mercado_livre", "shopee")))
        ),
        preferred_channels=tuple(
            data.get("preferred_channels", ctx.get("preferred_channels", ("telegram", "website", "whatsapp_manual")))
        ),
        disclosure_text=data.get("disclosure_text", ctx.get("disclosure_text", DealCampaign.disclosure_text)),
        metadata=dict(data.get("metadata", {})),
    )


def _coerce_offers(raw: Any) -> tuple[ProductOffer, ...]:
    items = _as_iterable(raw)
    return tuple(
        item if isinstance(item, ProductOffer) else _coerce_offer(item)
        for item in items
        if isinstance(item, (ProductOffer, dict))
    )


def _coerce_offer(data: dict[str, Any]) -> ProductOffer:
    return ProductOffer(
        marketplace=_coerce_marketplace(data.get("marketplace", data.get("source"))),
        product_name=data.get("product_name", data.get("name", "")),
        category=data.get("category", ""),
        audience=data.get("audience", ""),
        product_url=data.get("product_url", data.get("url", "")),
        image_url=data.get("image_url", ""),
        price=_coerce_price(data.get("price", data)),
        coupon=_coerce_coupon(data.get("coupon", data)),
        affiliate=_coerce_affiliate(data.get("affiliate", data)),
        urgency_level=data.get("urgency_level", "medium"),
        stock_status=data.get("stock_status", "unknown"),
        source_label=data.get("source_label", ""),
        risk_flags=tuple(data.get("risk_flags", ())),
        metadata=dict(data.get("metadata", {})),
    )


def _coerce_marketplace(raw: Any) -> MarketplaceSource:
    if isinstance(raw, MarketplaceSource):
        return raw
    if isinstance(raw, str):
        return MarketplaceSource(
            name=raw.lower().replace(" ", "_"),
            display_name=raw,
            trust_score=_trust_for(raw),
        )
    data = raw if isinstance(raw, dict) else {}
    name = data.get("name", "amazon")
    return MarketplaceSource(
        name=str(name).lower().replace(" ", "_"),
        display_name=data.get("display_name", str(name).title()),
        country=data.get("country", "BR"),
        allowed=data.get("allowed", True),
        trust_score=data.get("trust_score", _trust_for(str(name))),
        supports_affiliate_links=data.get("supports_affiliate_links", True),
        metadata=dict(data.get("metadata", {})),
    )


def _coerce_price(raw: Any) -> PriceSnapshot:
    if isinstance(raw, PriceSnapshot):
        return raw
    data = raw if isinstance(raw, dict) else {}
    return PriceSnapshot(
        currency=data.get("currency", "BRL"),
        old_price=_optional_float(data.get("old_price")),
        current_price=float(data.get("current_price", data.get("price", 0.0)) or 0.0),
        payment_terms=data.get("payment_terms", ""),
        shipping_notes=data.get("shipping_notes", ""),
        historical_low_price=_optional_float(data.get("historical_low_price")),
        metadata=dict(data.get("metadata", {})),
    )


def _coerce_coupon(raw: Any) -> CouponInfo:
    if isinstance(raw, CouponInfo):
        return raw
    if isinstance(raw, str):
        return CouponInfo(code=raw)
    data = raw if isinstance(raw, dict) else {}
    return CouponInfo(
        code=data.get("code", data.get("coupon_code", "")),
        description=data.get("description", ""),
        discount_value=_optional_float(data.get("discount_value")),
        expires_at=data.get("expires_at", ""),
        metadata=dict(data.get("metadata", {})),
    )


def _coerce_affiliate(raw: Any) -> AffiliateLink:
    if isinstance(raw, AffiliateLink):
        return raw
    if isinstance(raw, str):
        return AffiliateLink(affiliate_url=raw)
    data = raw if isinstance(raw, dict) else {}
    return AffiliateLink(
        original_url=data.get("original_url", data.get("product_url", data.get("url", ""))),
        affiliate_url=data.get("affiliate_url", ""),
        tracking_id=data.get("tracking_id", ""),
        short_url=data.get("short_url", ""),
        metadata=dict(data.get("metadata", {})),
    )


def _coerce_audience_plan(raw: Any) -> AudienceGrowthPlan:
    if isinstance(raw, AudienceGrowthPlan):
        return raw
    data = raw if isinstance(raw, dict) else {}
    return AudienceGrowthPlan(
        primary_funnel=data.get("primary_funnel", "facebook_page_to_telegram"),
        warmup_goal_followers=data.get("warmup_goal_followers", 5000),
        warmup_days=data.get("warmup_days", 30),
        daily_organic_posts=data.get("daily_organic_posts", 1),
        daily_deal_posts=data.get("daily_deal_posts", 10),
        paid_budget_brl=float(data.get("paid_budget_brl", 0.0) or 0.0),
        target_channels=tuple(data.get("target_channels", ("facebook_page", "instagram", "telegram"))),
        stage=data.get("stage", "warmup"),
        metrics_to_track=tuple(data.get("metrics_to_track", AudienceGrowthPlan.metrics_to_track)),
        metadata=dict(data.get("metadata", {})),
    )


def _coerce_funnel_metrics(raw: Any) -> FunnelMetrics:
    if isinstance(raw, FunnelMetrics):
        return raw
    data = raw if isinstance(raw, dict) else {}
    return FunnelMetrics(
        ad_spend_brl=float(data.get("ad_spend_brl", 0.0) or 0.0),
        followers_gained=int(data.get("followers_gained", 0) or 0),
        telegram_members=int(data.get("telegram_members", 0) or 0),
        offer_clicks=int(data.get("offer_clicks", 0) or 0),
        commissions_brl=float(data.get("commissions_brl", 0.0) or 0.0),
        roi_percent=float(data.get("roi_percent", 0.0) or 0.0),
        metadata=dict(data.get("metadata", {})),
    )


def _trust_for(marketplace: str) -> float:
    return {
        "amazon": 0.92,
        "mercado livre": 0.86,
        "mercado_livre": 0.86,
        "shopee": 0.78,
        "magalu": 0.8,
    }.get(marketplace.lower(), 0.65)


def _optional_float(value: Any) -> float | None:
    if value is None or value == "":
        return None
    return float(value)


def _as_iterable(raw: Any) -> tuple[Any, ...]:
    if raw is None:
        return ()
    if isinstance(raw, tuple):
        return raw
    if isinstance(raw, list):
        return tuple(raw)
    return (raw,)
