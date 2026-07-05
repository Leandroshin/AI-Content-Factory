"""Deterministic affiliate deals production pipeline."""

from __future__ import annotations

from dataclasses import asdict, is_dataclass
from enum import StrEnum
from typing import Any
from uuid import UUID

from core.departments.affiliate_deals.compliance import review_compliance
from core.departments.affiliate_deals.formatter import (
    build_offer_creative,
    build_offer_message,
)
from core.departments.affiliate_deals.models import (
    AffiliateDealTask,
    AudienceGrowthPlan,
    ComplianceCheck,
    DealScore,
    OfferCreative,
    OfferMessage,
    ProductOffer,
    PublishingChannel,
    PublishingPlan,
)
from core.departments.affiliate_deals.scoring import score_deal
from core.departments.base.pipeline import ProductionPipeline, StageResult


class PipelineStage(StrEnum):
    """Stages of the affiliate deals pipeline."""

    CREATED = "created"
    ANALYZING_BRIEF = "analyzing_brief"
    SCANNING_MARKETPLACE = "scanning_marketplace"
    VALIDATING_OFFER = "validating_offer"
    SCORING_DEAL = "scoring_deal"
    BUILDING_AFFILIATE_LINK = "building_affiliate_link"
    WRITING_OFFER_COPY = "writing_offer_copy"
    PREPARING_CREATIVE = "preparing_creative"
    COMPLIANCE_REVIEW = "compliance_review"
    PLANNING_AUDIENCE_GROWTH = "planning_audience_growth"
    PUBLISHING_PREPARATION = "publishing_preparation"
    DELIVERING = "delivering"
    COMPLETED = "completed"
    FAILED = "failed"


class AffiliateDealsPipeline(ProductionPipeline):
    """Rule-based state machine for affiliate offer operations."""

    def __init__(self, task: AffiliateDealTask) -> None:
        super().__init__()
        self._task = task
        self._stage: str = PipelineStage.CREATED.value
        self._candidate_offers: tuple[ProductOffer, ...] = ()
        self._selected_offer: ProductOffer | None = None
        self._score: DealScore | None = None
        self._message: OfferMessage | None = None
        self._creative: OfferCreative | None = None
        self._compliance: ComplianceCheck | None = None
        self._audience_plan: AudienceGrowthPlan | None = None
        self._publishing_plan: PublishingPlan | None = None

    @property
    def stage(self) -> str:
        return self._stage

    @property
    def task(self) -> AffiliateDealTask:
        return self._task

    @property
    def progress(self) -> float:
        stages = list(PipelineStage)
        try:
            idx = stages.index(PipelineStage(self._stage))
            return round((idx / (len(stages) - 1)) * 100.0, 1)
        except (ValueError, KeyError):
            return 0.0

    def advance(self) -> StageResult:
        handlers = {
            PipelineStage.CREATED: self._stage_created,
            PipelineStage.ANALYZING_BRIEF: self._stage_analyzing_brief,
            PipelineStage.SCANNING_MARKETPLACE: self._stage_scanning_marketplace,
            PipelineStage.VALIDATING_OFFER: self._stage_validating_offer,
            PipelineStage.SCORING_DEAL: self._stage_scoring_deal,
            PipelineStage.BUILDING_AFFILIATE_LINK: self._stage_building_affiliate_link,
            PipelineStage.WRITING_OFFER_COPY: self._stage_writing_offer_copy,
            PipelineStage.PREPARING_CREATIVE: self._stage_preparing_creative,
            PipelineStage.COMPLIANCE_REVIEW: self._stage_compliance_review,
            PipelineStage.PLANNING_AUDIENCE_GROWTH: self._stage_planning_audience_growth,
            PipelineStage.PUBLISHING_PREPARATION: self._stage_publishing_preparation,
            PipelineStage.DELIVERING: self._stage_delivering,
        }

        try:
            current = PipelineStage(self._stage)
        except (ValueError, KeyError):
            result = StageResult(
                stage=self._stage,
                success=False,
                error=f"Unknown stage: {self._stage}",
            )
            self._stages_log.append(result)
            self._stage = PipelineStage.FAILED.value
            return result

        handler = handlers.get(current)
        if handler is None:
            result = StageResult(
                stage=self._stage,
                success=False,
                error=f"No handler for: {self._stage}",
            )
            self._stages_log.append(result)
            self._stage = PipelineStage.FAILED.value
            return result

        result = handler()
        self._stages_log.append(result)
        if result.next_stage:
            self._stage = result.next_stage
        elif result.success:
            self._stage = self._next_stage(current).value
        else:
            self._stage = PipelineStage.FAILED.value
        return result

    def reset(self) -> None:
        super().reset()
        self._stage = PipelineStage.CREATED.value
        self._candidate_offers = ()
        self._selected_offer = None
        self._score = None
        self._message = None
        self._creative = None
        self._compliance = None
        self._audience_plan = None
        self._publishing_plan = None

    # ------------------------------------------------------------------
    # Stage handlers
    # ------------------------------------------------------------------

    def _stage_created(self) -> StageResult:
        return StageResult(
            stage=PipelineStage.CREATED.value,
            success=True,
            summary=f"Affiliate deal task '{self._task.title}' created",
            output={
                "task_id": str(self._task.task_id),
                "campaign_type": self._task.campaign.campaign_type,
                "preferred_channel": self._task.preferred_channel,
            },
            next_stage=PipelineStage.ANALYZING_BRIEF.value,
        )

    def _stage_analyzing_brief(self) -> StageResult:
        campaign = self._task.campaign
        if not campaign.name:
            return StageResult(
                stage=PipelineStage.ANALYZING_BRIEF.value,
                success=False,
                error="Campaign name is required.",
            )
        if self._task.preferred_channel.lower() == "whatsapp_auto":
            return StageResult(
                stage=PipelineStage.ANALYZING_BRIEF.value,
                success=False,
                error="WhatsApp automatic publishing is not allowed in this phase.",
            )
        return StageResult(
            stage=PipelineStage.ANALYZING_BRIEF.value,
            success=True,
            summary=f"Campaign analyzed: {campaign.name} / {campaign.niche}",
            output={
                "campaign_name": campaign.name,
                "niche": campaign.niche,
                "target_audience": campaign.target_audience,
                "preferred_marketplaces": list(campaign.preferred_marketplaces),
            },
            next_stage=PipelineStage.SCANNING_MARKETPLACE.value,
        )

    def _stage_scanning_marketplace(self) -> StageResult:
        offers = self._task.offers
        if not offers:
            return StageResult(
                stage=PipelineStage.SCANNING_MARKETPLACE.value,
                success=False,
                error="At least one provided ProductOffer is required.",
            )
        self._candidate_offers = offers
        marketplaces = tuple(dict.fromkeys(o.marketplace.name for o in offers))
        return StageResult(
            stage=PipelineStage.SCANNING_MARKETPLACE.value,
            success=True,
            summary=f"Marketplace scan simulated: {len(offers)} candidate(s)",
            output={
                "scanner_mode": "provided_offer_feed",
                "candidate_offers": len(offers),
                "marketplaces": list(marketplaces),
            },
            next_stage=PipelineStage.VALIDATING_OFFER.value,
        )

    def _stage_validating_offer(self) -> StageResult:
        offer = _select_first_valid_offer(self._candidate_offers)
        if offer is None:
            return StageResult(
                stage=PipelineStage.VALIDATING_OFFER.value,
                success=False,
                error="No valid offer found with product name, marketplace, and current price.",
            )
        if not offer.marketplace.allowed:
            return StageResult(
                stage=PipelineStage.VALIDATING_OFFER.value,
                success=False,
                error=f"Marketplace not allowed: {offer.marketplace.name}",
            )
        self._selected_offer = offer
        return StageResult(
            stage=PipelineStage.VALIDATING_OFFER.value,
            success=True,
            summary=f"Offer validated: {offer.product_name}",
            output={
                "selected_offer_id": str(offer.offer_id),
                "product_name": offer.product_name,
                "marketplace": offer.marketplace.name,
                "current_price": offer.price.current_price,
                "discount_percent": offer.discount_percent,
            },
            next_stage=PipelineStage.SCORING_DEAL.value,
        )

    def _stage_scoring_deal(self) -> StageResult:
        offer = _require_offer(self._selected_offer)
        self._score = score_deal(offer)
        return StageResult(
            stage=PipelineStage.SCORING_DEAL.value,
            success=True,
            summary=(
                f"Deal scored: {self._score.score_total:.1f} "
                f"({self._score.recommendation})"
            ),
            output={
                "deal_score": _public_dict(self._score),
                "score_total": self._score.score_total,
                "recommendation": self._score.recommendation,
            },
            next_stage=PipelineStage.BUILDING_AFFILIATE_LINK.value,
        )

    def _stage_building_affiliate_link(self) -> StageResult:
        offer = _require_offer(self._selected_offer)
        affiliate_url = offer.affiliate.public_url
        return StageResult(
            stage=PipelineStage.BUILDING_AFFILIATE_LINK.value,
            success=True,
            summary="Affiliate link prepared" if affiliate_url else "Affiliate link missing",
            output={
                "affiliate_url": affiliate_url,
                "has_affiliate_url": offer.affiliate.has_affiliate_target,
                "tracking_id": offer.affiliate.tracking_id,
            },
            next_stage=PipelineStage.WRITING_OFFER_COPY.value,
        )

    def _stage_writing_offer_copy(self) -> StageResult:
        offer = _require_offer(self._selected_offer)
        self._message = build_offer_message(
            offer,
            channel=self._task.preferred_channel,
            disclosure_text=self._task.disclosure_text or self._task.campaign.disclosure_text,
        )
        return StageResult(
            stage=PipelineStage.WRITING_OFFER_COPY.value,
            success=True,
            summary=f"Offer copy written: {self._message.character_count} chars",
            output={
                "offer_message": _public_dict(self._message),
                "message_body": self._message.body,
                "disclosure_text": self._message.disclosure_text,
            },
            next_stage=PipelineStage.PREPARING_CREATIVE.value,
        )

    def _stage_preparing_creative(self) -> StageResult:
        offer = _require_offer(self._selected_offer)
        self._creative = build_offer_creative(offer)
        return StageResult(
            stage=PipelineStage.PREPARING_CREATIVE.value,
            success=True,
            summary=f"Creative prepared: {self._creative.layout}",
            output={
                "creative": _public_dict(self._creative),
                "creative_type": self._creative.creative_type,
                "creative_callouts": list(self._creative.callouts),
            },
            next_stage=PipelineStage.COMPLIANCE_REVIEW.value,
        )

    def _stage_compliance_review(self) -> StageResult:
        offer = _require_offer(self._selected_offer)
        message = _require_message(self._message)
        self._compliance = review_compliance(self._task, offer, message)
        status = "passed" if self._compliance.passed else "blocked"
        return StageResult(
            stage=PipelineStage.COMPLIANCE_REVIEW.value,
            success=True,
            summary=f"Compliance {status}: {len(self._compliance.issues)} issue(s)",
            output={
                "compliance": _public_dict(self._compliance),
                "compliance_passed": self._compliance.passed,
                "compliance_issues": list(self._compliance.issues),
                "compliance_warnings": list(self._compliance.warnings),
            },
            next_stage=PipelineStage.PLANNING_AUDIENCE_GROWTH.value,
        )

    def _stage_planning_audience_growth(self) -> StageResult:
        plan = self._task.audience_growth_plan
        self._audience_plan = plan
        return StageResult(
            stage=PipelineStage.PLANNING_AUDIENCE_GROWTH.value,
            success=True,
            summary=(
                f"Audience plan: {plan.primary_funnel}, "
                f"{plan.warmup_goal_followers} follower warmup"
            ),
            output={
                "audience_growth_plan": _public_dict(plan),
                "primary_funnel": plan.primary_funnel,
                "warmup_goal_followers": plan.warmup_goal_followers,
                "metrics_to_track": list(plan.metrics_to_track),
            },
            next_stage=PipelineStage.PUBLISHING_PREPARATION.value,
        )

    def _stage_publishing_preparation(self) -> StageResult:
        offer = _require_offer(self._selected_offer)
        score = _require_score(self._score)
        message = _require_message(self._message)
        creative = _require_creative(self._creative)
        compliance = _require_compliance(self._compliance)
        self._publishing_plan = _build_publishing_plan(
            task=self._task,
            offer=offer,
            score=score,
            message=message,
            creative=creative,
            compliance=compliance,
        )
        return StageResult(
            stage=PipelineStage.PUBLISHING_PREPARATION.value,
            success=True,
            summary=f"Publishing prepared: {self._publishing_plan.status}",
            output={
                "publishing_plan": _public_dict(self._publishing_plan),
                "publishing_status": self._publishing_plan.status,
                "approval_required": self._publishing_plan.approval_required,
                "blocked_reason": self._publishing_plan.blocked_reason,
            },
            next_stage=PipelineStage.DELIVERING.value,
        )

    def _stage_delivering(self) -> StageResult:
        offer = _require_offer(self._selected_offer)
        score = _require_score(self._score)
        message = _require_message(self._message)
        creative = _require_creative(self._creative)
        compliance = _require_compliance(self._compliance)
        audience_plan = self._audience_plan or self._task.audience_growth_plan
        publishing_plan = _require_publishing_plan(self._publishing_plan)

        delivery = {
            "task_id": str(self._task.task_id),
            "title": self._task.title,
            "campaign_type": self._task.campaign.campaign_type,
            "campaign_name": self._task.campaign.name,
            "niche": self._task.campaign.niche,
            "offers_analyzed": len(self._candidate_offers),
            "product_offer": _public_dict(offer),
            "deal_score": _public_dict(score),
            "score_total": score.score_total,
            "recommendation": score.recommendation,
            "offer_message": _public_dict(message),
            "message_body": message.body,
            "creative": _public_dict(creative),
            "compliance": _public_dict(compliance),
            "compliance_passed": compliance.passed,
            "disclosure_text": compliance.disclosure_text,
            "audience_growth_plan": _public_dict(audience_plan),
            "primary_funnel": audience_plan.primary_funnel,
            "publishing_plan": _public_dict(publishing_plan),
            "publishing_status": publishing_plan.status,
            "requires_human_approval": publishing_plan.approval_required,
            "auto_publish_allowed": self._task.auto_publish_allowed,
        }
        return StageResult(
            stage=PipelineStage.DELIVERING.value,
            success=True,
            summary=(
                f"Delivered affiliate deal plan: {offer.product_name} / "
                f"{score.recommendation} / {publishing_plan.status}"
            ),
            output=delivery,
            next_stage=PipelineStage.COMPLETED.value,
        )

    @staticmethod
    def _next_stage(current: PipelineStage) -> PipelineStage:
        stages = list(PipelineStage)
        idx = stages.index(current)
        if idx + 1 < len(stages):
            return stages[idx + 1]
        return PipelineStage.COMPLETED


def _select_first_valid_offer(offers: tuple[ProductOffer, ...]) -> ProductOffer | None:
    for offer in offers:
        if offer.product_name and offer.marketplace.name and offer.price.current_price > 0:
            return offer
    return None


def _build_publishing_plan(
    *,
    task: AffiliateDealTask,
    offer: ProductOffer,
    score: DealScore,
    message: OfferMessage,
    creative: OfferCreative,
    compliance: ComplianceCheck,
) -> PublishingPlan:
    channel_name = task.preferred_channel.lower()
    channel = PublishingChannel(
        name=channel_name,
        mode="manual" if "whatsapp" in channel_name else "prepared",
        supports_auto_publish=channel_name == "telegram" and task.auto_publish_allowed,
        requires_human_approval=True,
        notes=_channel_notes(channel_name),
    )

    if score.recommendation == "skip":
        status = "rejected"
        blocked_reason = "Deal score recommendation is SKIP."
    elif not compliance.passed:
        status = "blocked"
        blocked_reason = "; ".join(compliance.issues)
    elif task.require_human_approval or channel.requires_human_approval:
        status = "pending_approval"
        blocked_reason = ""
    else:
        status = "ready"
        blocked_reason = ""

    return PublishingPlan(
        channel=channel,
        status=status,
        scheduled_window="same_day_evening" if score.score_total >= 70 else "manual_review",
        message_preview=message.body,
        creative_brief=(
            f"{creative.layout}: {offer.product_name} with "
            f"{offer.discount_percent:.0f}% discount callout"
        ),
        approval_required=True,
        blocked_reason=blocked_reason,
        metadata={
            "score_total": score.score_total,
            "recommendation": score.recommendation,
            "marketplace": offer.marketplace.name,
        },
    )


def _channel_notes(channel: str) -> str:
    if channel == "telegram":
        return "Preferred first automation channel; TelegramAdapter can publish after approval."
    if "whatsapp" in channel:
        return "WhatsApp stays manual/semi-automatic in this phase."
    if channel in ("facebook", "facebook_page", "instagram"):
        return "Use as audience warmup or funnel creative, not direct spam."
    return "Prepared for review."


def _public_dict(value: Any) -> Any:
    if is_dataclass(value):
        return _public_dict(asdict(value))
    if isinstance(value, UUID):
        return str(value)
    if isinstance(value, dict):
        return {str(k): _public_dict(v) for k, v in value.items()}
    if isinstance(value, (tuple, list)):
        return [_public_dict(v) for v in value]
    return value


def _require_offer(offer: ProductOffer | None) -> ProductOffer:
    if offer is None:
        raise RuntimeError("Offer has not been selected.")
    return offer


def _require_score(score: DealScore | None) -> DealScore:
    if score is None:
        raise RuntimeError("Deal has not been scored.")
    return score


def _require_message(message: OfferMessage | None) -> OfferMessage:
    if message is None:
        raise RuntimeError("Offer message has not been created.")
    return message


def _require_creative(creative: OfferCreative | None) -> OfferCreative:
    if creative is None:
        raise RuntimeError("Offer creative has not been created.")
    return creative


def _require_compliance(compliance: ComplianceCheck | None) -> ComplianceCheck:
    if compliance is None:
        raise RuntimeError("Compliance has not been reviewed.")
    return compliance


def _require_publishing_plan(plan: PublishingPlan | None) -> PublishingPlan:
    if plan is None:
        raise RuntimeError("Publishing plan has not been created.")
    return plan
