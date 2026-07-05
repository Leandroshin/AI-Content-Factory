"""Demonstration: Affiliate Deals Department.

Flow:
  1. Create affiliate deal models directly
  2. Create AffiliateDealsEmployee
  3. Execute a strong deal for Telegram with human approval
  4. Verify scoring, copy, creative, compliance, publishing plan, and growth plan
  5. Verify observability snapshots
  6. Execute a weak deal rejected by scoring
  7. Execute a compliance-blocked deal with missing affiliate URL
"""

from __future__ import annotations

from uuid import uuid4

from core.company.quality import QualityRuntime
from core.company.specialist_employee import (
    EmployeeSkill,
    ReceivedTask,
    TaskDecision,
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
from core.events.bus import EventBus
from core.observability import ObservabilityProjector
from core.runtime import CompanyRuntime


_ASSERTION_COUNTER: int = 0


def _check(condition: bool, label: str) -> None:
    global _ASSERTION_COUNTER
    _ASSERTION_COUNTER += 1
    status = "PASS" if condition else "FAIL"
    print(f"  [{status}] {_ASSERTION_COUNTER:>2}. {label}")
    if not condition:
        raise AssertionError(label)


def main() -> None:
    print("=" * 70)
    print("Affiliate Deals Department - Offer Curation + Growth Planning")
    print("=" * 70)

    # ==================================================================
    # Setup
    # ==================================================================
    event_bus = EventBus()
    observer = ObservabilityProjector(event_bus)
    company = CompanyRuntime(event_bus)
    company.initialize_company()
    qr = QualityRuntime(event_bus=event_bus)

    qr.register_rule(
        name="Affiliate output has no execution errors",
        description="Execution must not contain an error field",
        category="output_quality",
        severity="critical",
        criteria={},
    )
    qr.register_rule(
        name="Affiliate output required fields present",
        description="Affiliate deal output exposes required review fields",
        category="output_completeness",
        severity="critical",
        criteria={
            "required_fields": [
                "offer_message",
                "disclosure_text",
                "compliance_passed",
                "publishing_plan",
                "publishing_status",
                "score_total",
                "recommendation",
                "channel",
                "requires_human_approval",
            ]
        },
    )

    # ==================================================================
    # Step 1: Create models directly
    # ==================================================================
    print("\n" + "-" * 70)
    print("Step 1: Create affiliate deal models")
    print("-" * 70)

    amazon = MarketplaceSource(
        name="amazon",
        display_name="Amazon",
        trust_score=0.92,
        supports_affiliate_links=True,
    )
    direct_offer = ProductOffer(
        marketplace=amazon,
        product_name="PlayStation DualSense Controle sem fio - Gray Camouflage",
        category="gamer",
        audience="gamers e compradores de tecnologia",
        product_url="https://amazon.example/dualsense",
        image_url="https://img.example/dualsense.jpg",
        price=PriceSnapshot(
            old_price=499.90,
            current_price=327.22,
            payment_terms="no Pix",
            shipping_notes="Prime",
        ),
        coupon=CouponInfo(code="TUDOPRIME"),
        affiliate=AffiliateLink(
            original_url="https://amazon.example/dualsense",
            affiliate_url="https://amzn.example/seu-link-afiliado",
            tracking_id="shin-20",
        ),
        urgency_level="flash",
        stock_status="available",
        source_label="whatsapp_reference",
    )
    growth_plan = AudienceGrowthPlan(
        primary_funnel="facebook_warmup_to_telegram",
        warmup_goal_followers=5000,
        warmup_days=30,
        daily_organic_posts=1,
        daily_deal_posts=15,
        paid_budget_brl=300.0,
    )
    campaign = DealCampaign(
        name="Achados Tech Prime",
        niche="tech_gamer",
        target_audience="publico brasileiro buscando ofertas reais",
        preferred_marketplaces=("amazon", "mercado_livre"),
        preferred_channels=("telegram", "facebook_page", "whatsapp_manual"),
    )

    _check(direct_offer.discount_percent > 30.0, f"Discount computed: {direct_offer.discount_percent}%")
    _check(direct_offer.has_coupon, "Coupon is present")
    _check(direct_offer.affiliate.has_affiliate_target, "Affiliate URL present")
    _check(growth_plan.warmup_goal_followers == 5000, "Warmup goal keeps 5k followers strategy")
    _check("telegram" in campaign.preferred_channels, "Telegram is a preferred channel")

    # ==================================================================
    # Step 2: Create employee
    # ==================================================================
    print("\n" + "-" * 70)
    print("Step 2: Create AffiliateDealsEmployee")
    print("-" * 70)

    employee = AffiliateDealsEmployee(
        company_runtime=company,
        employee_id=uuid4(),
        skills=(
            EmployeeSkill(name="web_search", proficiency=0.85),
            EmployeeSkill(name="browser_automation", proficiency=0.78),
            EmployeeSkill(name="text_generation", proficiency=0.88),
            EmployeeSkill(name="image_editing", proficiency=0.76),
            EmployeeSkill(name="social_media", proficiency=0.82),
        ),
        event_bus=event_bus,
        quality_runtime=qr,
    )

    _check(employee.status.value == "idle", "Initial status: idle")
    _check(len(employee.affiliate_capabilities) == 11, "11 affiliate capabilities loaded")
    _check(employee.affiliate_capabilities["deal_scoring"].proficiency == 0.88, "Deal scoring capability ready")

    # ==================================================================
    # Step 3: Execute strong deal
    # ==================================================================
    print("\n" + "-" * 70)
    print("Step 3: Execute strong deal -> Telegram plan")
    print("-" * 70)

    good_task = ReceivedTask(
        task_id=uuid4(),
        title="Preparar oferta DualSense para canal Telegram",
        description="Score, copy, creative, compliance and publishing plan for an affiliate offer.",
        department="Affiliate Deals",
        required_skills=("web_search", "text_generation", "social_media"),
        context={
            "campaign": campaign,
            "offers": (direct_offer,),
            "preferred_channel": "telegram",
            "audience_growth_plan": growth_plan,
            "require_human_approval": True,
            "auto_publish_allowed": False,
            "disclosure_text": DEFAULT_DISCLOSURE,
        },
    )

    decision = employee.receive_task(good_task)
    _check(decision == TaskDecision.ACCEPTED, f"Decision: {decision}")
    _check(employee.pipeline_stage == "created", "Pipeline starts at created")

    result = employee.execute_task(good_task.task_id)
    output = result.output

    _check(result.success, "Strong deal pipeline succeeded")
    _check(output["pipeline_progress"] > 85.0, f"Pipeline progress: {output['pipeline_progress']}%")
    _check(output["campaign_type"] == "affiliate_deals", "Campaign type delivered")
    _check(output["offers_analyzed"] == 1, "One offer analyzed")
    _check(output["score_total"] >= 90.0, f"Strong deal score: {output['score_total']}")
    _check(output["recommendation"] == "post_now", "Strong deal recommendation: post_now")
    _check(output["compliance_passed"], "Compliance passed")
    _check(output["publishing_status"] == "pending_approval", "Publishing waits for human approval")
    _check(output["requires_human_approval"], "Human approval required")
    _check(output["auto_publish_allowed"] is False, "Auto publish is disabled")
    _check("Link de afiliado" in output["message_body"], "Disclosure included in message")
    _check("TUDOPRIME" in output["message_body"], "Coupon included in message")
    _check("327,22" in output["message_body"], "Current price included in message")
    _check("499,90" in output["message_body"], "Old price included in message")
    _check(output["creative"]["layout"] == "marketplace_price_drop_card", "Creative layout prepared")
    _check(output["creative"]["requires_image_enhancement"], "Creative can request image enhancement")
    _check(output["publishing_plan"]["channel"]["name"] == "telegram", "Publishing channel: telegram")
    _check(output["publishing_plan"]["approval_required"], "Publishing plan requires approval")
    _check(output["primary_funnel"] == "facebook_warmup_to_telegram", "Audience funnel delivered")
    _check(output["audience_growth_plan"]["warmup_goal_followers"] == 5000, "Audience warmup goal preserved")
    _check("roi" in output["audience_growth_plan"]["metrics_to_track"], "ROI metric tracked")

    # ==================================================================
    # Step 4: Metrics, state, capabilities
    # ==================================================================
    print("\n" + "-" * 70)
    print("Step 4: Metrics, state, capabilities")
    print("-" * 70)

    metrics = employee.production_metrics
    _check(metrics.total_stages == 12, f"Total stages: {metrics.total_stages}")
    _check(metrics.completed_stages == 12, "All affiliate stages completed")
    _check(metrics.failed_stages == 0, "No failed stages")
    _check(metrics.offers_analyzed == 1, "Metrics offers analyzed")
    _check(metrics.offers_approved == 1, "Metrics approved offer")
    _check(metrics.pending_approvals == 1, "Metrics pending approval")
    _check(metrics.posts_prepared == 1, "Metrics post prepared")
    _check(metrics.last_recommendation == "post_now", "Metrics recommendation")
    _check(metrics.publishing_channel == "telegram", "Metrics publishing channel")
    _check(metrics.audience_funnel == "facebook_warmup_to_telegram", "Metrics audience funnel")
    _check(metrics.quality_passed, "Quality passed")

    needs = employee.analyze_capability_needs()
    values = [cap.value for cap in needs]
    _check("web_search" in values, "WEB_SEARCH needed")
    _check("browser_automation" in values, "BROWSER_AUTOMATION needed")
    _check("text_generation" in values, "TEXT_GENERATION needed")
    _check("image_editing" in values, "IMAGE_EDITING needed")
    _check("social_media" in values, "SOCIAL_MEDIA needed")
    _check("storage" in values, "STORAGE needed")

    state = employee.state()
    _check(state["current_affiliate_task"]["niche"] == "tech_gamer", "State keeps niche")
    _check(state["production_metrics"]["last_score"] >= 90.0, "State keeps last score")
    _check(state["production_metrics"]["posts_prepared"] == 1, "State keeps posts prepared")

    # ==================================================================
    # Step 5: Observability
    # ==================================================================
    print("\n" + "-" * 70)
    print("Step 5: Observability snapshots")
    print("-" * 70)

    snap = observer.snapshot
    _check(snap.quality.rules_count == 2, "Quality rules projected")
    _check(snap.quality.last_validation_passed is True, "Quality last validation passed")
    _check(snap.affiliate_deals_production.task_id is not None, "Affiliate production task tracked")
    _check(snap.affiliate_deals_production.campaign_type == "affiliate_deals", "Affiliate campaign type tracked")
    _check(snap.affiliate_deals_production.pipeline_stage == "completed", "Affiliate production completed")
    _check(snap.affiliate_deals_department.total_productions >= 1, "Affiliate productions incremented")
    _check(snap.affiliate_deals_department.successful_productions >= 1, "Affiliate successes incremented")
    _check(snap.affiliate_deals_department.active_productions == 0, "No active affiliate production")
    _check(snap.deal_metrics.total_offers_analyzed >= 1, "Deal metrics offers analyzed")
    _check(snap.deal_metrics.offers_approved >= 1, "Deal metrics approved")
    _check(snap.deal_metrics.posts_prepared >= 1, "Deal metrics posts prepared")
    _check(snap.deal_metrics.offers_awaiting_approval >= 1, "Deal metrics approval queue")
    _check(snap.deal_metrics.marketplace_most_used == "amazon", "Deal metrics marketplace")
    _check(snap.deal_metrics.last_publishing_channel == "telegram", "Deal metrics channel")
    _check(snap.deal_metrics.primary_funnel == "facebook_warmup_to_telegram", "Deal metrics funnel")
    _check(any("dept=affiliate_deals" in e for e in snap.events), "Affiliate production event logged")

    # ==================================================================
    # Step 6: Weak deal rejected by score
    # ==================================================================
    print("\n" + "-" * 70)
    print("Step 6: Weak deal -> rejected by scoring")
    print("-" * 70)

    weak_employee = AffiliateDealsEmployee(
        company_runtime=company,
        employee_id=uuid4(),
        skills=(EmployeeSkill(name="web_search", proficiency=0.8),),
        event_bus=event_bus,
        quality_runtime=qr,
    )
    weak_offer = ProductOffer(
        marketplace=amazon,
        product_name="Mousepad basico sem desconto relevante",
        category="tech",
        product_url="https://amazon.example/mousepad",
        price=PriceSnapshot(old_price=300.00, current_price=295.00),
        affiliate=AffiliateLink(affiliate_url="https://amzn.example/mousepad-afiliado"),
        urgency_level="low",
    )
    weak_task = ReceivedTask(
        task_id=uuid4(),
        title="Avaliar oferta fraca",
        description="Should complete with SKIP recommendation and rejected publishing.",
        department="Affiliate Deals",
        context={
            "campaign": campaign,
            "offers": (weak_offer,),
            "preferred_channel": "telegram",
            "audience_growth_plan": growth_plan,
        },
    )
    weak_employee.receive_task(weak_task)
    weak_result = weak_employee.execute_task(weak_task.task_id)
    weak_output = weak_result.output

    _check(weak_result.success, "Weak deal pipeline still completes")
    _check(weak_output["recommendation"] == "skip", "Weak deal recommendation: skip")
    _check(weak_output["publishing_status"] == "rejected", "Weak deal publishing rejected")
    _check(weak_employee.production_metrics.offers_rejected == 1, "Weak deal counted as rejected")
    _check(observer.snapshot.deal_metrics.offers_rejected >= 1, "Rejected deal projected")

    # ==================================================================
    # Step 7: Compliance-blocked deal
    # ==================================================================
    print("\n" + "-" * 70)
    print("Step 7: Missing affiliate URL -> compliance blocked")
    print("-" * 70)

    blocked_employee = AffiliateDealsEmployee(
        company_runtime=company,
        employee_id=uuid4(),
        skills=(EmployeeSkill(name="affiliate_compliance", proficiency=0.9),),
        event_bus=event_bus,
        quality_runtime=qr,
    )
    blocked_offer = ProductOffer(
        marketplace=amazon,
        product_name="Headset Gamer Sem Fio HyperX Cloud Jet Bluetooth 5.3",
        category="audio gamer",
        product_url="https://amazon.example/hyperx",
        price=PriceSnapshot(old_price=419.00, current_price=296.10, payment_terms="em 6x"),
        coupon=CouponInfo(code="TUDOPRIME"),
        affiliate=AffiliateLink(original_url="https://amazon.example/hyperx"),
        urgency_level="high",
    )
    blocked_task = ReceivedTask(
        task_id=uuid4(),
        title="Validar oferta sem link afiliado",
        description="Should block publishing because affiliate URL is missing.",
        department="Affiliate Deals",
        context={
            "campaign": campaign,
            "offers": (blocked_offer,),
            "preferred_channel": "whatsapp_manual",
            "audience_growth_plan": growth_plan,
            "auto_publish_allowed": False,
        },
    )
    blocked_employee.receive_task(blocked_task)
    blocked_result = blocked_employee.execute_task(blocked_task.task_id)
    blocked_output = blocked_result.output

    _check(blocked_result.success, "Blocked compliance pipeline still completes")
    _check(blocked_output["compliance_passed"] is False, "Compliance failed")
    _check("Affiliate URL is missing." in blocked_output["compliance"]["issues"], "Missing affiliate URL issue")
    _check(blocked_output["publishing_status"] == "blocked", "Publishing blocked")
    _check(blocked_output["publishing_plan"]["channel"]["name"] == "whatsapp_manual", "WhatsApp remains manual")
    _check("WhatsApp stays manual" in blocked_output["publishing_plan"]["channel"]["notes"], "WhatsApp automation warning")
    _check(blocked_employee.production_metrics.offers_rejected == 1, "Compliance-blocked offer counted as rejected")

    # ==================================================================
    # Summary
    # ==================================================================
    print(f"\n{'=' * 70}")
    print(f"All {_ASSERTION_COUNTER} assertions passed.")
    print(f"{'=' * 70}")


if __name__ == "__main__":
    main()
