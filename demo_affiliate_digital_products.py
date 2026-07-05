"""Demonstration: digital infoproduct extension for Affiliate Deals.

Flow:
  1. Prepare a manually curated Hotmart/Kiwify digital offer
  2. Reuse AffiliateDealsEmployee and the existing pipeline
  3. Validate conservative regulated-vertical compliance
  4. Prove unsafe claims/manual-review gaps block publication
"""

from __future__ import annotations

from uuid import uuid4

from core.company.specialist_employee import EmployeeSkill, ReceivedTask, TaskDecision
from core.departments.affiliate_deals import (
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


def _employee(event_bus: EventBus, company: CompanyRuntime) -> AffiliateDealsEmployee:
    return AffiliateDealsEmployee(
        company_runtime=company,
        employee_id=uuid4(),
        skills=(
            EmployeeSkill(name="affiliate_compliance", proficiency=0.9),
            EmployeeSkill(name="affiliate_copywriting", proficiency=0.86),
            EmployeeSkill(name="deal_scoring", proficiency=0.84),
            EmployeeSkill(name="social_media", proficiency=0.78),
        ),
        event_bus=event_bus,
    )


def _safe_offer() -> ProductOffer:
    hotmart = MarketplaceSource(
        name="hotmart",
        display_name="Hotmart",
        trust_score=0.78,
        supports_affiliate_links=True,
        metadata={
            "manual_source_reviewed": True,
            "review_notes": "Manual curation by owner before automation.",
        },
    )
    return ProductOffer(
        marketplace=hotmart,
        product_name="Programa educacional de controle e bem-estar masculino",
        category="saude_bem_estar_digital",
        audience="homens adultos buscando conteudo educativo",
        product_url="https://hotmart.example/produto-educacional",
        image_url="https://img.example/curso.jpg",
        price=PriceSnapshot(
            old_price=297.0,
            current_price=97.0,
            payment_terms="acesso digital",
        ),
        coupon=CouponInfo(code="BEMESTAR20"),
        affiliate=AffiliateLink(
            original_url="https://hotmart.example/produto-educacional",
            affiliate_url="https://go.hotmart.example/seu-link-afiliado",
            tracking_id="shin-hotmart",
        ),
        urgency_level="high",
        stock_status="digital",
        source_label="manual_hotmart_curation",
        metadata={
            "product_format": "digital_course",
            "regulated_vertical": "sexual_wellness",
            "positioning": "educational",
            "manual_source_reviewed": True,
            "platform_policy_reviewed": True,
            "contains_explicit_or_erotic_content": False,
            "age_gate": "18+",
        },
    )


def _unsafe_offer() -> ProductOffer:
    kiwify = MarketplaceSource(
        name="kiwify",
        display_name="Kiwify",
        trust_score=0.74,
        supports_affiliate_links=True,
    )
    return ProductOffer(
        marketplace=kiwify,
        product_name="Cura definitiva: voce tem esse problema?",
        category="sexual_wellness_digital",
        audience="homens adultos",
        product_url="https://kiwify.example/produto-arriscado",
        price=PriceSnapshot(old_price=297.0, current_price=47.0),
        affiliate=AffiliateLink(affiliate_url="https://kiwify.example/afiliado"),
        urgency_level="flash",
        stock_status="digital",
        source_label="unreviewed_external_idea",
        metadata={
            "product_format": "digital_course",
            "regulated_vertical": "sexual_wellness",
            "positioning": "performance",
            "contains_explicit_or_erotic_content": False,
        },
    )


def main() -> None:
    print("=" * 70)
    print("Affiliate Digital Products - Conservative Infoproduct Extension")
    print("=" * 70)

    event_bus = EventBus()
    observer = ObservabilityProjector(event_bus)
    company = CompanyRuntime(event_bus)
    company.initialize_company()

    campaign = DealCampaign(
        name="Infoprodutos Bem-Estar",
        campaign_type="affiliate_digital_product",
        niche="saude_bem_estar",
        target_audience="adultos 18+ buscando conteudo educacional",
        preferred_marketplaces=("hotmart", "kiwify"),
        preferred_channels=("telegram", "website", "whatsapp_manual"),
    )
    growth_plan = AudienceGrowthPlan(
        primary_funnel="manual_review_to_telegram",
        warmup_goal_followers=1000,
        daily_deal_posts=2,
    )

    print("\n" + "-" * 70)
    print("Step 1: Safe manually reviewed digital offer")
    print("-" * 70)
    safe_task = ReceivedTask(
        task_id=uuid4(),
        title="Avaliar infoproduto Hotmart revisado",
        description="Score, compliance and approval plan for a manually reviewed digital offer.",
        department="Affiliate Deals",
        context={
            "campaign": campaign,
            "offers": (_safe_offer(),),
            "preferred_channel": "telegram",
            "audience_growth_plan": growth_plan,
            "require_human_approval": True,
            "auto_publish_allowed": False,
        },
    )

    safe_employee = _employee(event_bus, company)
    decision = safe_employee.receive_task(safe_task)
    _check(decision == TaskDecision.ACCEPTED, "Safe digital task is accepted")
    safe_result = safe_employee.execute_task(safe_task.task_id)
    safe_output = safe_result.output

    _check(safe_result.success, "Safe digital product pipeline succeeds")
    _check(safe_output["campaign_type"] == "affiliate_digital_product", "Digital campaign type delivered")
    _check(safe_output["product_offer"]["marketplace"]["name"] == "hotmart", "Hotmart marketplace preserved")
    _check(safe_output["score_total"] >= 70.0, f"Digital offer score is viable: {safe_output['score_total']}")
    _check(safe_output["recommendation"] in ("post_now", "needs_review"), "Safe offer remains publishable")
    _check(safe_output["compliance_passed"], "Safe offer compliance passed")
    _check(safe_output["compliance"]["metadata"]["digital_product"], "Compliance detects digital product")
    _check(safe_output["compliance"]["metadata"]["regulated_vertical"], "Compliance detects regulated vertical")
    _check(safe_output["compliance"]["metadata"]["manual_source_reviewed"], "Manual source review is recorded")
    _check(safe_output["compliance"]["metadata"]["educational_positioning"], "Educational positioning is recorded")
    _check(safe_output["publishing_status"] == "pending_approval", "Digital product still waits for human approval")
    _check("BEMESTAR20" in safe_output["message_body"], "Digital offer coupon appears in message")
    _check("Link de afiliado" in safe_output["message_body"], "Affiliate disclosure appears in message")

    print("\n" + "-" * 70)
    print("Step 2: Unsafe/unreviewed digital offer is blocked")
    print("-" * 70)
    unsafe_task = ReceivedTask(
        task_id=uuid4(),
        title="Bloquear infoproduto Kiwify sem revisao",
        description="Unsafe claims and missing manual review should block publication.",
        department="Affiliate Deals",
        context={
            "campaign": campaign,
            "offers": (_unsafe_offer(),),
            "preferred_channel": "telegram",
            "audience_growth_plan": growth_plan,
            "require_human_approval": True,
            "auto_publish_allowed": False,
        },
    )

    unsafe_employee = _employee(event_bus, company)
    unsafe_employee.receive_task(unsafe_task)
    unsafe_result = unsafe_employee.execute_task(unsafe_task.task_id)
    unsafe_output = unsafe_result.output
    issues = tuple(unsafe_output["compliance"]["issues"])

    _check(unsafe_result.success, "Unsafe digital pipeline completes for review")
    _check(not unsafe_output["compliance_passed"], "Unsafe offer compliance fails")
    _check(unsafe_output["publishing_status"] == "blocked", "Unsafe offer publishing is blocked")
    _check(any("manually reviewed" in issue for issue in issues), "Missing manual review is blocked")
    _check(any("educational" in issue for issue in issues), "Non-educational positioning is blocked")
    _check(any("Medical cure" in issue for issue in issues), "Cure claim is blocked")
    _check(any("Personal attribute" in issue for issue in issues), "Second-person diagnosis is blocked")

    print("\n" + "-" * 70)
    print("Step 3: Metrics and observability")
    print("-" * 70)
    _check(safe_employee.production_metrics.posts_prepared == 1, "Safe digital post is prepared")
    _check(safe_employee.production_metrics.pending_approvals == 1, "Safe digital post awaits approval")
    _check(unsafe_employee.production_metrics.offers_rejected == 1, "Unsafe digital offer counted as rejected")

    snap = observer.snapshot
    _check(snap.affiliate_deals_department.successful_productions >= 2, "Two affiliate productions completed")
    _check(snap.deal_metrics.posts_prepared >= 1, "Prepared digital post projected")
    _check(snap.deal_metrics.offers_rejected >= 1, "Rejected digital offer projected")
    _check(snap.deal_metrics.last_publishing_channel == "telegram", "Publishing channel projected")

    print(f"\n{'=' * 70}")
    print(f"All {_ASSERTION_COUNTER} assertions passed.")
    print(f"{'=' * 70}")


if __name__ == "__main__":
    main()
