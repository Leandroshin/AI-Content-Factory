"""Demonstration: full affiliate factory workflow.

Flow:
  Strategy Intelligence -> Product Research -> Creative Review ->
  Affiliate Deals -> HITL Approval -> Telegram
"""

from __future__ import annotations

from uuid import uuid4

from core.approval import ApprovalRuntime, ApprovalStatus
from core.company.specialist_employee import EmployeeSkill
from core.content_factory import AffiliateCommerceWorkflow, AffiliateFactoryEmployees
from core.departments.affiliate_deals import AffiliateDealsEmployee
from core.departments.creative_review import CreativeReviewEmployee
from core.departments.product_research import (
    MarketplaceSignal,
    ProductCandidate,
    ProductResearchEmployee,
)
from core.departments.strategy_intelligence import StrategyIntelligenceEmployee, StrategySource
from core.events.bus import EventBus
from core.observability import ObservabilityProjector
from core.runtime import CompanyRuntime
from core.tools import TelegramAdapter


_ASSERTION_COUNTER: int = 0
_TOKEN = "test_telegram_token_affiliate_factory"
_OWNER_CHAT_ID = "-1001234567890"
_CHANNEL_CHAT_ID = "@achadosbaratosBrasil"


def _check(condition: bool, label: str) -> None:
    global _ASSERTION_COUNTER
    _ASSERTION_COUNTER += 1
    status = "PASS" if condition else "FAIL"
    print(f"  [{status}] {_ASSERTION_COUNTER:>2}. {label}")
    if not condition:
        raise AssertionError(label)


def _signal(name: str, value: float, weight: float = 1.0, source: str = "") -> MarketplaceSignal:
    return MarketplaceSignal(name=name, value=value, weight=weight, source=source)


def _sources() -> tuple[StrategySource, ...]:
    return (
        StrategySource(
            title="TikTok Shop POV and trend notes",
            creator="strategy_notes",
            source_url="https://youtube.example/tiktok-shop-pov",
            transcript_text=(
                "TikTok Shop POV video with IA. Choose products by grafico de crescimento, "
                "avoid queda, compare receita, ticket medio, comissao, and creator signals from Kalodata."
            ),
            tags=("tiktok_shop", "pov", "research"),
        ),
        StrategySource(
            title="Amazon Keepa validation notes",
            creator="strategy_notes",
            source_url="https://youtube.example/keepa",
            transcript_text=(
                "Keepa analysis uses ranking, BSR, Buy Box, variacao, reviews, avaliacao, "
                "preco historico, sellers, and historical context before selecting offers."
            ),
            tags=("amazon", "keepa"),
        ),
        StrategySource(
            title="Affiliate automation notes",
            creator="strategy_notes",
            source_url="https://youtube.example/divulga-ninja",
            transcript_text=(
                "Divulga Ninja, Insta Ninja and AliExpress API examples show post automatico "
                "for Telegram, WhatsApp manual flow and Instagram with affiliate disclosure."
            ),
            tags=("affiliate", "automation"),
        ),
    )


def _candidates() -> tuple[ProductCandidate, ...]:
    return (
        ProductCandidate(
            product_name="PlayStation DualSense Controle sem fio - Gray Camouflage",
            marketplace="amazon",
            category="gamer",
            niche="games",
            source_url="https://amazon.example/dualsense",
            affiliate_url="https://amzn.example/seu-link-afiliado",
            image_url="https://img.example/dualsense-clean.jpg",
            current_price=327.22,
            old_price=499.90,
            commission_percent=4.0,
            marketplace_trust=0.92,
            demand_signals=(
                _signal("deal_group_repeats", 9, 1.1),
                _signal("recognizable_brand", 8, 1.0),
                _signal("trend_growth_graph", 8, 1.0),
            ),
            creative_signals=(
                _signal("product_photo_quality", 10, 1.0),
                _signal("short_hook_potential", 8, 1.0),
            ),
            competition_level="medium",
            saturation_level="medium",
            metadata={
                "coupon_code": "TUDOPRIME",
                "tracking_id": "shin-20",
                "payment_terms": "no Pix",
                "shipping_notes": "Prime",
                "urgency_level": "flash",
                "stock_status": "available",
                "audience": "gamers e compradores de tecnologia",
                "visual_quality": 10,
                "product_visibility": 10,
                "resolution_score": 10,
                "text_clutter": 0,
                "watermark_risk": 0,
                "brand_safety": 10,
            },
        ),
        ProductCandidate(
            product_name="Monitor gamer 24 polegadas 144Hz",
            marketplace="amazon",
            category="gamer",
            niche="pc_gamer",
            source_url="https://amazon.example/monitor",
            affiliate_url="https://amzn.example/monitor-afiliado",
            image_url="https://img.example/monitor.jpg",
            current_price=530.10,
            old_price=749.00,
            commission_percent=3.0,
            marketplace_trust=0.92,
            demand_signals=(
                _signal("high_search_intent", 8, 1.0),
                _signal("deal_group_repeats", 7, 1.0),
            ),
            creative_signals=(_signal("product_photo_quality", 6, 1.0),),
            competition_level="high",
            saturation_level="medium",
            metadata={"coupon_code": "TUDOPRIME", "visual_quality": 7, "product_visibility": 7},
        ),
        ProductCandidate(
            product_name="Fone bluetooth sem marca com bateria 72h",
            marketplace="unknown_store",
            category="audio",
            niche="tech",
            source_url="https://loja.example/fone-duvidoso",
            image_url="https://img.example/fone-duvidoso.jpg",
            current_price=39.90,
            old_price=299.90,
            commission_percent=20.0,
            marketplace_trust=0.3,
            demand_signals=(_signal("too_good_to_be_true_discount", 9, 1.0),),
            creative_signals=(_signal("generic_product_photo", 3, 1.0),),
            competition_level="high",
            saturation_level="high",
            risk_flags=("untrusted_marketplace", "too_good_to_be_true"),
        ),
    )


def _employees(company: CompanyRuntime, event_bus: EventBus) -> AffiliateFactoryEmployees:
    return AffiliateFactoryEmployees(
        strategy_intelligence=StrategyIntelligenceEmployee(
            company_runtime=company,
            employee_id=uuid4(),
            skills=(
                EmployeeSkill(name="source_triage", proficiency=0.88),
                EmployeeSkill(name="metric_extraction", proficiency=0.86),
            ),
            event_bus=event_bus,
        ),
        product_research=ProductResearchEmployee(
            company_runtime=company,
            employee_id=uuid4(),
            skills=(
                EmployeeSkill(name="web_search", proficiency=0.84),
                EmployeeSkill(name="market_signal_review", proficiency=0.86),
                EmployeeSkill(name="risk_triage", proficiency=0.8),
            ),
            event_bus=event_bus,
        ),
        creative_review=CreativeReviewEmployee(
            company_runtime=company,
            employee_id=uuid4(),
            skills=(
                EmployeeSkill(name="image_readiness", proficiency=0.9),
                EmployeeSkill(name="thumbnail_formula_review", proficiency=0.86),
            ),
            event_bus=event_bus,
        ),
        affiliate_deals=AffiliateDealsEmployee(
            company_runtime=company,
            employee_id=uuid4(),
            skills=(
                EmployeeSkill(name="text_generation", proficiency=0.88),
                EmployeeSkill(name="affiliate_compliance", proficiency=0.88),
                EmployeeSkill(name="social_media", proficiency=0.82),
            ),
            event_bus=event_bus,
        ),
    )


def main() -> None:
    print("=" * 70)
    print("Affiliate Factory Workflow - Strategy to Telegram")
    print("=" * 70)

    event_bus = EventBus()
    observer = ObservabilityProjector(event_bus)
    company = CompanyRuntime(event_bus)
    company.initialize_company()
    approvals = ApprovalRuntime(event_bus=event_bus)

    telegram = TelegramAdapter()
    telegram.configure({"bot_token": _TOKEN})
    telegram.authenticate()
    telegram.mark_ready()

    workflow = AffiliateCommerceWorkflow(
        approvals,
        telegram,
        owner_chat_id=_OWNER_CHAT_ID,
        telegram_chat_id=_CHANNEL_CHAT_ID,
    )
    employees = _employees(company, event_bus)

    print("\n" + "-" * 70)
    print("Step 1: Run full workflow with demo approval")
    print("-" * 70)
    result = workflow.run_offer_pipeline(
        title="Oferta gamer validada por estrategia",
        employees=employees,
        strategy_sources=_sources(),
        product_candidates=_candidates(),
        shortlist_size=2,
        auto_approve=True,
        approved_by="Shin",
    )

    _check(result.success, "Workflow succeeds end-to-end")
    _check(result.package is not None, "Workflow returns publication package")
    assert result.package is not None
    _check(len(result.steps) == 4, "Four department steps executed")
    _check(result.steps[0].department == "Strategy Intelligence", "Step 1 is Strategy Intelligence")
    _check(result.steps[1].department == "Product Research", "Step 2 is Product Research")
    _check(result.steps[2].department == "Creative Review", "Step 3 is Creative Review")
    _check(result.steps[3].department == "Affiliate Deals", "Step 4 is Affiliate Deals")

    print("\n" + "-" * 70)
    print("Step 2: Strategy and product research outputs")
    print("-" * 70)
    strategy_output = result.output_for("Strategy Intelligence")
    research_output = result.output_for("Product Research")
    patterns = {pattern["pattern_id"] for pattern in strategy_output["patterns"]}
    shortlisted = research_output["shortlisted"]
    _check("tiktok_shop_pov_ai_video" in patterns, "Strategy captured TikTok Shop POV pattern")
    _check("amazon_keepa_product_analysis" in patterns, "Strategy captured Amazon/Keepa pattern")
    _check(len(shortlisted) == 2, "Product Research returns requested shortlist")
    _check(shortlisted[0]["product_name"] == result.package.selected_product_name, "Selected package product comes from shortlist")
    _check(shortlisted[0]["affiliate_url"], "Selected product has affiliate URL")

    print("\n" + "-" * 70)
    print("Step 3: Creative Review gates image work")
    print("-" * 70)
    creative_output = result.output_for("Creative Review")
    findings = creative_output["findings"]
    _check(creative_output["ready_count"] >= 1, "At least one asset is ready as-is")
    _check(result.package.creative_action == "use_as_is", "Workflow chooses use_as_is creative")
    _check(result.package.creative_score >= 72.0, "Chosen creative meets threshold")
    _check(any(f["recommended_action"] == "use_as_is" for f in findings), "Findings include ready asset")

    print("\n" + "-" * 70)
    print("Step 4: Affiliate Deals prepares approval-gated message")
    print("-" * 70)
    affiliate_output = result.output_for("Affiliate Deals")
    _check(affiliate_output["recommendation"] == "post_now", "Affiliate Deals recommends post_now")
    _check(affiliate_output["publishing_status"] == "pending_approval", "Affiliate publishing waits for approval")
    _check(affiliate_output["requires_human_approval"], "Human approval required")
    _check("TUDOPRIME" in affiliate_output["message_body"], "Message includes coupon")
    _check("Link de afiliado" in affiliate_output["message_body"], "Message includes affiliate disclosure")
    _check(result.package.deal_score >= 76.0, "Deal score is publishable")

    print("\n" + "-" * 70)
    print("Step 5: HITL approval blocks, approves, then Telegram publishes")
    print("-" * 70)
    assert result.approval_request is not None
    assert result.approval_notification is not None
    assert result.pending_publication is not None
    assert result.publication_result is not None
    _check(result.approval_notification.success, "Owner approval notification sent")
    _check(not result.pending_publication.success, "Publication is blocked while approval is pending")
    _check(result.pending_publication.output["approval_status"] == "pending", "Pending block is explicit")
    _check(approvals.require(result.approval_request.approval_id).status == ApprovalStatus.APPROVED, "Approval runtime records approval")
    _check(result.publication_result.success, "Telegram publication succeeds after approval")
    _check(result.publication_result.output["status"] == "sent_mock", "Telegram stays in mock-safe mode")
    _check(result.publication_result.output["chat_id"] == _CHANNEL_CHAT_ID, "Telegram destination channel is used")
    _check(result.package.telegram_status == "sent_mock", "Package records Telegram status")
    _check(result.package.telegram_message_id == 1001, "Package records mock message id")
    _check(result.package.approval_status == "approved", "Package records approved status")

    print("\n" + "-" * 70)
    print("Step 6: Observability sees the whole chain")
    print("-" * 70)
    snap = observer.snapshot
    _check(snap.strategy_intelligence_department.successful_productions == 1, "Strategy success projected")
    _check(snap.product_research_department.successful_productions == 1, "Product Research success projected")
    _check(snap.creative_review_department.successful_productions == 1, "Creative Review success projected")
    _check(snap.affiliate_deals_department.successful_productions == 1, "Affiliate Deals success projected")
    _check(snap.approvals.total_requests == 1, "Approval request projected")
    _check(snap.approvals.approved == 1, "Approval decision projected")
    _check(any("dept=strategy_intelligence" in event for event in snap.events), "Strategy event logged")
    _check(any("dept=product_research" in event for event in snap.events), "Product Research event logged")
    _check(any("dept=creative_review" in event for event in snap.events), "Creative Review event logged")
    _check(any("dept=affiliate_deals" in event for event in snap.events), "Affiliate event logged")

    print(f"\n{'=' * 70}")
    print(f"All {_ASSERTION_COUNTER} assertions passed.")
    print(f"{'=' * 70}")


if __name__ == "__main__":
    main()
