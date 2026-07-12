"""Concrete affiliate commerce workflow.

Coordinates the real departments already present in the factory:

Strategy Intelligence -> Product Research -> Creative Review ->
Affiliate Deals -> HITL Approval -> Telegram.

This is intentionally domain-specific. It does not introduce a generic
runtime and it keeps publishing behind a human approval gate.
"""

from __future__ import annotations

from dataclasses import dataclass, field, replace
from typing import Any
from uuid import UUID, uuid4

from core.approval import ApprovalRequest, ApprovalRuntime, TelegramApprovalGateway
from core.company.specialist_employee import ReceivedTask, TaskDecision
from core.content_factory.models import ContentWorkflowStepResult
from core.content_factory.product_url_intake import (
    ProductUrlIntake,
    ProductUrlIntakeResult,
)
from core.departments.affiliate_deals import (
    DEFAULT_DISCLOSURE,
    AffiliateDealsEmployee,
    AffiliateLink,
    AudienceGrowthPlan,
    CouponInfo,
    DealCampaign,
    MarketplaceSource,
    PriceSnapshot,
    ProductOffer,
)
from core.departments.creative_review import CreativeAsset, CreativeReviewEmployee
from core.departments.product_research import ProductCandidate, ProductResearchEmployee
from core.departments.strategy_intelligence import (
    StrategyIntelligenceEmployee,
    StrategySource,
)
from core.tools import AdapterExecutionResult, TelegramAdapter


@dataclass(frozen=True, slots=True)
class AffiliateFactoryEmployees:
    """Employees required by the affiliate commerce workflow."""

    strategy_intelligence: StrategyIntelligenceEmployee
    product_research: ProductResearchEmployee
    creative_review: CreativeReviewEmployee
    affiliate_deals: AffiliateDealsEmployee


@dataclass(frozen=True, slots=True)
class AffiliatePublicationPackage:
    """Final package prepared by the affiliate commerce workflow."""

    package_id: UUID = field(default_factory=uuid4)
    workflow: str = "strategy_to_telegram_affiliate_offer"
    selected_product_name: str = ""
    product_research_score: float = 0.0
    creative_action: str = ""
    creative_score: float = 0.0
    deal_score: float = 0.0
    recommendation: str = ""
    publishing_status: str = ""
    message_body: str = ""
    approval_id: UUID | None = None
    approval_status: str = ""
    telegram_status: str = ""
    telegram_message_id: int = 0
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class AffiliateFactoryWorkflowResult:
    """Overall result for the affiliate commerce workflow."""

    success: bool
    package: AffiliatePublicationPackage | None = None
    steps: tuple[ContentWorkflowStepResult, ...] = field(default_factory=tuple)
    approval_request: ApprovalRequest | None = None
    approval_notification: AdapterExecutionResult | None = None
    pending_publication: AdapterExecutionResult | None = None
    publication_result: AdapterExecutionResult | None = None
    product_intake_results: tuple[ProductUrlIntakeResult, ...] = field(default_factory=tuple)
    summary: str = ""
    error: str = ""

    def output_for(self, department: str) -> dict[str, Any]:
        """Return the output for a department name, or an empty dict."""
        key = department.lower()
        for step in self.steps:
            if step.department.lower() == key:
                return dict(step.output)
        return {}


class AffiliateCommerceWorkflow:
    """Concrete affiliate workflow from strategy sources to Telegram gate."""

    def __init__(
        self,
        approval_runtime: ApprovalRuntime,
        telegram_adapter: TelegramAdapter,
        *,
        owner_chat_id: str,
        telegram_chat_id: str | None = None,
    ) -> None:
        self._approval_runtime = approval_runtime
        self._telegram_adapter = telegram_adapter
        self._owner_chat_id = owner_chat_id
        self._telegram_chat_id = telegram_chat_id or owner_chat_id
        self._gateway = TelegramApprovalGateway(
            approval_runtime,
            telegram_adapter,
            owner_chat_id=owner_chat_id,
        )

    def run_offer_pipeline_from_urls(
        self,
        *,
        title: str,
        employees: AffiliateFactoryEmployees,
        strategy_sources: tuple[StrategySource, ...],
        product_urls: tuple[str, ...],
        product_intake: ProductUrlIntake,
        affiliate_urls: dict[str, str] | None = None,
        overrides_by_url: dict[str, dict[str, Any]] | None = None,
        creative_assets: tuple[CreativeAsset, ...] = (),
        campaign: DealCampaign | None = None,
        audience_growth_plan: AudienceGrowthPlan | None = None,
        shortlist_size: int = 3,
        auto_approve: bool = False,
        approved_by: str = "owner",
    ) -> AffiliateFactoryWorkflowResult:
        """Collect product evidence, then enter the existing affiliate flow."""
        batch = product_intake.intake_many(
            product_urls,
            affiliate_urls=affiliate_urls,
            overrides_by_url=overrides_by_url,
        )
        if not batch.candidates:
            return AffiliateFactoryWorkflowResult(
                success=False,
                product_intake_results=batch.results,
                summary="Product URL intake produced no usable candidates",
                error="Provide a supported product URL or complete the manual fallback fields.",
            )
        result = self.run_offer_pipeline(
            title=title,
            employees=employees,
            strategy_sources=strategy_sources,
            product_candidates=batch.candidates,
            creative_assets=creative_assets,
            campaign=campaign,
            audience_growth_plan=audience_growth_plan,
            shortlist_size=shortlist_size,
            auto_approve=auto_approve,
            approved_by=approved_by,
        )
        return replace(result, product_intake_results=batch.results)

    def run_offer_pipeline(
        self,
        *,
        title: str,
        employees: AffiliateFactoryEmployees,
        strategy_sources: tuple[StrategySource, ...],
        product_candidates: tuple[ProductCandidate, ...],
        creative_assets: tuple[CreativeAsset, ...] = (),
        campaign: DealCampaign | None = None,
        audience_growth_plan: AudienceGrowthPlan | None = None,
        shortlist_size: int = 3,
        auto_approve: bool = False,
        approved_by: str = "owner",
    ) -> AffiliateFactoryWorkflowResult:
        """Run the full affiliate workflow.

        auto_approve is intended for demos/tests. In production-like use, keep
        it False so the workflow stops after the approval notification.
        """
        steps: list[ContentWorkflowStepResult] = []

        strategy_step = self._execute(
            employees.strategy_intelligence,
            self._strategy_task(title, strategy_sources),
        )
        steps.append(strategy_step)
        if not strategy_step.success:
            return self._failed(steps, strategy_step.error or "Strategy intelligence failed")

        research_step = self._execute(
            employees.product_research,
            self._product_research_task(title, product_candidates, shortlist_size),
        )
        steps.append(research_step)
        if not research_step.success:
            return self._failed(steps, research_step.error or "Product research failed")

        shortlisted = tuple(research_step.output.get("shortlisted", ()))
        if not shortlisted:
            return self._failed(steps, "Product research returned no shortlisted products.")

        review_assets = creative_assets or self._assets_from_shortlist(shortlisted)
        creative_step = self._execute(
            employees.creative_review,
            self._creative_review_task(title, review_assets),
        )
        steps.append(creative_step)
        if not creative_step.success:
            return self._failed(steps, creative_step.error or "Creative review failed")

        selected_finding = self._select_publishable_creative(creative_step.output)
        if selected_finding is None:
            return self._failed(
                steps,
                "Creative review found no asset ready for publishing. Improve or replace assets first.",
            )

        selected_product = self._match_product(shortlisted, selected_finding)
        offer = self._offer_from_product(selected_product)
        deal_campaign = campaign or self._campaign_from_strategy(title, strategy_step.output)
        growth_plan = audience_growth_plan or AudienceGrowthPlan(primary_funnel="facebook_warmup_to_telegram")

        affiliate_step = self._execute(
            employees.affiliate_deals,
            self._affiliate_task(title, offer, deal_campaign, growth_plan),
        )
        steps.append(affiliate_step)
        if not affiliate_step.success:
            return self._failed(steps, affiliate_step.error or "Affiliate deal production failed")

        if affiliate_step.output.get("publishing_status") not in ("pending_approval", "ready"):
            return self._failed(
                steps,
                f"Affiliate deal is not publishable: {affiliate_step.output.get('publishing_status', '')}",
            )

        approval = self._request_publication_approval(title, affiliate_step.output)
        notification = self._gateway.send_approval_request(approval)
        pending_publication = self._gateway.publish_if_approved(approval.approval_id)

        publication: AdapterExecutionResult | None = None
        if auto_approve:
            self._approval_runtime.approve(
                approval.approval_id,
                decided_by=approved_by,
                reason="Workflow demo approval.",
                metadata={"workflow": "affiliate_commerce"},
            )
            approval = self._approval_runtime.require(approval.approval_id)
            publication = self._gateway.publish_if_approved(approval.approval_id)

        package = self._package(
            selected_product=selected_product,
            selected_finding=selected_finding,
            affiliate_output=affiliate_step.output,
            approval=approval,
            publication=publication,
        )
        success = (
            notification.success
            and (
                publication.success if auto_approve and publication is not None
                else approval.status.value == "pending"
            )
        )
        summary = (
            "Affiliate workflow published after approval"
            if publication is not None and publication.success
            else "Affiliate workflow prepared and waiting for owner approval"
        )
        return AffiliateFactoryWorkflowResult(
            success=success,
            package=package,
            steps=tuple(steps),
            approval_request=approval,
            approval_notification=notification,
            pending_publication=pending_publication,
            publication_result=publication,
            summary=summary,
            error="" if success else "Approval notification or publication failed.",
        )

    # ------------------------------------------------------------------
    # Task builders
    # ------------------------------------------------------------------

    def _strategy_task(self, title: str, sources: tuple[StrategySource, ...]) -> ReceivedTask:
        return ReceivedTask(
            task_id=uuid4(),
            title=f"Extract strategy: {title}",
            description="Extract reusable strategy before product and offer production.",
            department="Strategy Intelligence",
            required_skills=("source_triage", "metric_extraction"),
            context={
                "objective": "Learn reusable commerce strategy and handoff rules.",
                "focus_areas": ("affiliate", "product_research", "creative", "publishing"),
                "sources": sources,
                "max_patterns": 8,
            },
        )

    def _product_research_task(
        self,
        title: str,
        candidates: tuple[ProductCandidate, ...],
        shortlist_size: int,
    ) -> ReceivedTask:
        return ReceivedTask(
            task_id=uuid4(),
            title=f"Rank products: {title}",
            description="Score and shortlist candidate products for affiliate production.",
            department="Product Research",
            required_skills=("web_search", "risk_triage"),
            context={
                "objective": "Find products worth sending to AffiliateDealsEmployee.",
                "target_market": "BR",
                "niches": tuple(dict.fromkeys(candidate.niche for candidate in candidates if candidate.niche)),
                "source_platforms": ("strategy_intelligence", "manual_candidates", "marketplace"),
                "candidates": candidates,
                "shortlist_size": shortlist_size,
                "require_affiliate_url": True,
            },
        )

    def _creative_review_task(
        self,
        title: str,
        assets: tuple[CreativeAsset, ...],
    ) -> ReceivedTask:
        return ReceivedTask(
            task_id=uuid4(),
            title=f"Review creatives: {title}",
            description="Decide which product image or offer card can enter publishing.",
            department="Creative Review",
            required_skills=("image_readiness", "thumbnail_formula_review"),
            context={
                "objective": "Use good assets as-is and stop risky assets before publishing.",
                "target_platforms": ("telegram", "tiktok_shop", "youtube"),
                "ready_threshold": 72.0,
                "assets": assets,
            },
        )

    def _affiliate_task(
        self,
        title: str,
        offer: ProductOffer,
        campaign: DealCampaign,
        audience_growth_plan: AudienceGrowthPlan,
    ) -> ReceivedTask:
        return ReceivedTask(
            task_id=uuid4(),
            title=f"Prepare Telegram offer: {offer.product_name}",
            description=f"Score, copy, compliance, and publishing plan for {title}.",
            department="Affiliate Deals",
            required_skills=("text_generation", "social_media", "affiliate_compliance"),
            context={
                "campaign": campaign,
                "offers": (offer,),
                "preferred_channel": "telegram",
                "audience_growth_plan": audience_growth_plan,
                "require_human_approval": True,
                "auto_publish_allowed": False,
                "disclosure_text": DEFAULT_DISCLOSURE,
            },
        )

    # ------------------------------------------------------------------
    # Selection and conversion
    # ------------------------------------------------------------------

    def _assets_from_shortlist(self, shortlisted: tuple[dict[str, Any], ...]) -> tuple[CreativeAsset, ...]:
        assets: list[CreativeAsset] = []
        for item in shortlisted:
            metadata = dict(item.get("metadata", {}))
            assets.append(CreativeAsset(
                title=str(item.get("product_name", "")),
                asset_type="product_image",
                product_name=str(item.get("product_name", "")),
                platform=str(item.get("marketplace", "")),
                image_url=str(item.get("image_url", "")),
                source_url=str(item.get("source_url", "")),
                use_case="affiliate_post",
                visual_quality=float(metadata.get("visual_quality", 7.0) or 7.0),
                product_visibility=float(metadata.get("product_visibility", 7.0) or 7.0),
                resolution_score=float(metadata.get("resolution_score", 7.0) or 7.0),
                text_clutter=float(metadata.get("text_clutter", 2.0) or 2.0),
                watermark_risk=float(metadata.get("watermark_risk", 0.0) or 0.0),
                brand_safety=float(metadata.get("brand_safety", 8.0) or 8.0),
                risk_flags=tuple(item.get("risk_flags", ())),
                metadata={"source": "product_research_shortlist", **metadata},
            ))
        return tuple(assets)

    def _select_publishable_creative(self, creative_output: dict[str, Any]) -> dict[str, Any] | None:
        findings = [
            finding for finding in creative_output.get("findings", [])
            if isinstance(finding, dict)
        ]
        publishable = [
            finding for finding in findings
            if finding.get("recommended_action") == "use_as_is"
        ]
        if not publishable:
            return None
        publishable.sort(key=lambda finding: float(finding.get("score_total", 0.0)), reverse=True)
        return dict(publishable[0])

    def _match_product(
        self,
        shortlisted: tuple[dict[str, Any], ...],
        creative_finding: dict[str, Any],
    ) -> dict[str, Any]:
        product_name = str(creative_finding.get("product_name", ""))
        for item in shortlisted:
            if str(item.get("product_name", "")) == product_name:
                return dict(item)
        return dict(shortlisted[0])

    def _offer_from_product(self, item: dict[str, Any]) -> ProductOffer:
        metadata = dict(item.get("metadata", {}))
        marketplace_name = str(item.get("marketplace", "amazon"))
        return ProductOffer(
            marketplace=MarketplaceSource(
                name=marketplace_name.lower().replace(" ", "_"),
                display_name=str(metadata.get("marketplace_display_name", marketplace_name.title())),
                trust_score=float(metadata.get("marketplace_trust", _trust_for(marketplace_name)) or 0.65),
                supports_affiliate_links=True,
            ),
            product_name=str(item.get("product_name", "")),
            category=str(item.get("category", "")),
            audience=str(metadata.get("audience", item.get("niche", ""))),
            product_url=str(item.get("source_url", "")),
            image_url=str(item.get("image_url", "")),
            price=PriceSnapshot(
                old_price=_optional_float(item.get("old_price")),
                current_price=float(item.get("current_price", 0.0) or 0.0),
                payment_terms=str(metadata.get("payment_terms", "")),
                shipping_notes=str(metadata.get("shipping_notes", "")),
                historical_low_price=_optional_float(metadata.get("historical_low_price")),
            ),
            coupon=CouponInfo(
                code=str(metadata.get("coupon_code", "")),
                description=str(metadata.get("coupon_description", "")),
            ),
            affiliate=AffiliateLink(
                original_url=str(item.get("source_url", "")),
                affiliate_url=str(item.get("affiliate_url", "")),
                tracking_id=str(metadata.get("tracking_id", "")),
                short_url=str(metadata.get("short_url", "")),
            ),
            urgency_level=str(metadata.get("urgency_level", "high")),
            stock_status=str(metadata.get("stock_status", "unknown")),
            source_label=str(metadata.get("source_label", "product_research")),
            risk_flags=tuple(item.get("risk_flags", ())),
            metadata={
                "product_research_score": item.get("score_total", 0.0),
                "commission_percent": item.get("commission_percent", 0.0),
                **metadata,
            },
        )

    def _campaign_from_strategy(self, title: str, strategy_output: dict[str, Any]) -> DealCampaign:
        pattern_ids = tuple(
            pattern.get("pattern_id", "")
            for pattern in strategy_output.get("patterns", [])
            if isinstance(pattern, dict)
        )
        return DealCampaign(
            name=f"Affiliate Factory - {title}",
            niche="tech_gamer",
            target_audience="compradores brasileiros buscando ofertas reais e bem filtradas",
            preferred_marketplaces=("amazon", "mercado_livre", "shopee", "tiktok_shop"),
            preferred_channels=("telegram", "facebook_page", "whatsapp_manual"),
            metadata={
                "strategy_patterns": pattern_ids,
                "source": "strategy_intelligence",
            },
        )

    # ------------------------------------------------------------------
    # Approval and packaging
    # ------------------------------------------------------------------

    def _request_publication_approval(
        self,
        title: str,
        affiliate_output: dict[str, Any],
    ) -> ApprovalRequest:
        message = str(affiliate_output.get("message_body", ""))
        product = affiliate_output.get("product_offer", {})
        product_name = product.get("product_name", title) if isinstance(product, dict) else title
        return self._approval_runtime.request_approval(
            title=f"Publicar oferta no Telegram: {product_name}",
            preview_text=message,
            payload={
                "telegram_text": message,
                "chat_id": self._telegram_chat_id,
                "publishing_status": affiliate_output.get("publishing_status", ""),
                "score_total": affiliate_output.get("score_total", 0.0),
                "recommendation": affiliate_output.get("recommendation", ""),
            },
            requester="AffiliateDealsEmployee",
            source="affiliate_factory_workflow",
            subject_type="telegram_publication",
            subject_id=str(affiliate_output.get("task_id", "")),
            risk_level="medium",
            metadata={
                "workflow": "strategy_to_telegram_affiliate_offer",
                "campaign_name": affiliate_output.get("campaign_name", ""),
            },
        )

    def _package(
        self,
        *,
        selected_product: dict[str, Any],
        selected_finding: dict[str, Any],
        affiliate_output: dict[str, Any],
        approval: ApprovalRequest,
        publication: AdapterExecutionResult | None,
    ) -> AffiliatePublicationPackage:
        output = publication.output if publication is not None else {}
        return AffiliatePublicationPackage(
            selected_product_name=str(selected_product.get("product_name", "")),
            product_research_score=float(selected_product.get("score_total", 0.0) or 0.0),
            creative_action=str(selected_finding.get("recommended_action", "")),
            creative_score=float(selected_finding.get("score_total", 0.0) or 0.0),
            deal_score=float(affiliate_output.get("score_total", 0.0) or 0.0),
            recommendation=str(affiliate_output.get("recommendation", "")),
            publishing_status=str(affiliate_output.get("publishing_status", "")),
            message_body=str(affiliate_output.get("message_body", "")),
            approval_id=approval.approval_id,
            approval_status=approval.status.value,
            telegram_status=str(output.get("status", "")),
            telegram_message_id=int(output.get("message_id", 0) or 0),
            metadata={
                "approval_public_status": approval.public_dict(),
                "telegram_text_length": output.get("text_length", 0),
                "primary_funnel": affiliate_output.get("primary_funnel", ""),
            },
        )

    # ------------------------------------------------------------------
    # Execution helpers
    # ------------------------------------------------------------------

    def _execute(self, employee: Any, task: ReceivedTask) -> ContentWorkflowStepResult:
        decision = employee.receive_task(task)
        if decision != TaskDecision.ACCEPTED:
            return ContentWorkflowStepResult(
                department=task.department,
                task_id=task.task_id,
                success=False,
                error=f"Task rejected by {task.department}",
            )

        result = employee.execute_task(task.task_id)
        return ContentWorkflowStepResult(
            department=task.department,
            task_id=task.task_id,
            success=result.success,
            summary=result.summary,
            output=dict(result.output),
            error=result.error,
        )

    def _failed(
        self,
        steps: list[ContentWorkflowStepResult],
        error: str,
    ) -> AffiliateFactoryWorkflowResult:
        return AffiliateFactoryWorkflowResult(
            success=False,
            steps=tuple(steps),
            summary="Affiliate workflow failed",
            error=error,
        )


def _optional_float(value: Any) -> float | None:
    if value is None or value == "":
        return None
    return float(value)


def _trust_for(marketplace: str) -> float:
    return {
        "amazon": 0.92,
        "mercado_livre": 0.86,
        "mercado livre": 0.86,
        "shopee": 0.78,
        "tiktok_shop": 0.72,
        "tiktok shop": 0.72,
        "hotmart": 0.78,
    }.get(marketplace.lower(), 0.65)
