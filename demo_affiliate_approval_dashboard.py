"""Demonstration: affiliate approval dashboard UI.

Generates a local HTML preview for daily offer review:
pending offers, approved offers, publication state, message preview,
and printable A4 operator guide.
"""

from __future__ import annotations

from pathlib import Path
from uuid import uuid4

from core.approval import ApprovalRuntime
from core.company.specialist_employee import EmployeeSkill
from core.content_factory import (
    AffiliateApprovalDashboardRenderer,
    AffiliateCommerceWorkflow,
    AffiliateFactoryEmployees,
)
from core.departments.affiliate_deals import AffiliateDealsEmployee
from core.departments.creative_review import CreativeReviewEmployee
from core.departments.product_research import MarketplaceSignal, ProductCandidate, ProductResearchEmployee
from core.departments.strategy_intelligence import StrategyIntelligenceEmployee, StrategySource
from core.events.bus import EventBus
from core.runtime import CompanyRuntime
from core.tools import TelegramAdapter


_ASSERTION_COUNTER: int = 0
_TOKEN = "test_telegram_token_dashboard"
_OWNER_CHAT_ID = "-1001234567890"
_CHANNEL_CHAT_ID = "@achadosbaratosBrasil"


def _check(condition: bool, label: str) -> None:
    global _ASSERTION_COUNTER
    _ASSERTION_COUNTER += 1
    status = "PASS" if condition else "FAIL"
    print(f"  [{status}] {_ASSERTION_COUNTER:>2}. {label}")
    if not condition:
        raise AssertionError(label)


def _signal(name: str, value: float, weight: float = 1.0) -> MarketplaceSignal:
    return MarketplaceSignal(name=name, value=value, weight=weight)


def _sources() -> tuple[StrategySource, ...]:
    return (
        StrategySource(
            title="Affiliate offer research notes",
            creator="strategy_notes",
            source_url="https://youtube.example/strategy",
            transcript_text=(
                "TikTok Shop POV video with IA, grafico de crescimento, receita, ticket medio, "
                "comissao, Keepa, Buy Box, reviews, Divulga Ninja and Telegram approval."
            ),
            tags=("affiliate", "research", "creative"),
        ),
    )


def _candidates(prefix: str = "") -> tuple[ProductCandidate, ...]:
    name = f"{prefix}PlayStation DualSense Controle sem fio - Gray Camouflage".strip()
    return (
        ProductCandidate(
            product_name=name,
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
            product_name=f"{prefix}Monitor gamer 24 polegadas 144Hz".strip(),
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
            demand_signals=(_signal("high_search_intent", 8, 1.0),),
            creative_signals=(_signal("product_photo_quality", 7, 1.0),),
            competition_level="high",
            saturation_level="medium",
            metadata={"coupon_code": "TUDOPRIME", "visual_quality": 7, "product_visibility": 7},
        ),
    )


def _employees(company: CompanyRuntime, event_bus: EventBus) -> AffiliateFactoryEmployees:
    return AffiliateFactoryEmployees(
        strategy_intelligence=StrategyIntelligenceEmployee(
            company_runtime=company,
            employee_id=uuid4(),
            skills=(EmployeeSkill(name="source_triage", proficiency=0.88),),
            event_bus=event_bus,
        ),
        product_research=ProductResearchEmployee(
            company_runtime=company,
            employee_id=uuid4(),
            skills=(EmployeeSkill(name="market_signal_review", proficiency=0.86),),
            event_bus=event_bus,
        ),
        creative_review=CreativeReviewEmployee(
            company_runtime=company,
            employee_id=uuid4(),
            skills=(EmployeeSkill(name="image_readiness", proficiency=0.9),),
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
    print("Affiliate Approval Dashboard - Local Preview")
    print("=" * 70)

    event_bus = EventBus()
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

    print("\n" + "-" * 70)
    print("Step 1: Build pending and published queue items")
    print("-" * 70)
    pending = workflow.run_offer_pipeline(
        title="Fila pendente",
        employees=_employees(company, event_bus),
        strategy_sources=_sources(),
        product_candidates=_candidates(),
        shortlist_size=1,
        auto_approve=False,
    )
    published = workflow.run_offer_pipeline(
        title="Fila publicada",
        employees=_employees(company, event_bus),
        strategy_sources=_sources(),
        product_candidates=_candidates(prefix="Publicado - "),
        shortlist_size=1,
        auto_approve=True,
        approved_by="Shin",
    )

    _check(pending.success, "Pending workflow result succeeds")
    _check(published.success, "Published workflow result succeeds")
    assert pending.package is not None
    assert published.package is not None
    _check(pending.package.approval_status == "pending", "First package is pending approval")
    _check(published.package.approval_status == "approved", "Second package is approved")
    _check(published.package.telegram_status == "sent_mock", "Second package is published in mock-safe mode")

    print("\n" + "-" * 70)
    print("Step 2: Build dashboard state")
    print("-" * 70)
    state = AffiliateApprovalDashboardRenderer.dashboard_state((pending, published))
    offers = state["offers"]
    summary = state["summary"]
    _check(summary["total"] == 2, "Dashboard state has two offers")
    _check(summary["pending"] == 1, "Dashboard state counts one pending offer")
    _check(summary["approved"] == 1, "Dashboard state counts one approved offer")
    _check(summary["published"] == 1, "Dashboard state counts one published offer")
    _check(offers[0]["message_body"], "Offer state includes Telegram message")
    _check(offers[0]["steps"][0]["department"] == "Strategy Intelligence", "Offer state includes workflow steps")
    _check(offers[0]["creative_action"] == "use_as_is", "Offer state includes creative review action")

    print("\n" + "-" * 70)
    print("Step 3: Render local HTML dashboard")
    print("-" * 70)
    html = AffiliateApprovalDashboardRenderer.render_html(state)
    output_dir = Path("output/affiliate_approval_dashboard")
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / "index.html"
    output_path.write_text(html, encoding="utf-8")

    _check("<title>AI Content Factory - Fila de Ofertas</title>" in html, "HTML has expected title")
    _check("Fila de Ofertas" in html, "HTML renders queue heading")
    _check("Aprovar" in html, "HTML includes approve button")
    _check("Rejeitar" in html, "HTML includes reject button")
    _check("Publicar" in html, "HTML includes publish button")
    _check("Guia rapido de uso" in html, "HTML includes visual A4 guide")
    _check("window.__affiliateDashboard" in html, "HTML embeds dashboard state")
    _check("data-offer-row" in html, "HTML has selectable offer rows")
    _check("data-offer-card" in html, "HTML has offer cards")
    _check("function approveOffer" in html, "HTML includes local approve interaction")
    _check("function publishOffer" in html, "HTML includes local publish interaction")
    _check("Product Research" in html, "HTML includes workflow step labels")
    _check("Creative Review" in html, "HTML includes creative review step labels")
    _check("Affiliate Deals" in html, "HTML includes affiliate deals step labels")
    _check(_TOKEN not in html, "HTML does not expose Telegram token")
    _check(output_path.exists(), "HTML preview file was written")
    _check(output_path.stat().st_size > 10000, "HTML preview has substantial UI content")

    print(f"\nPreview written to: {output_path.resolve()}")
    print(f"\n{'=' * 70}")
    print(f"All {_ASSERTION_COUNTER} assertions passed.")
    print(f"{'=' * 70}")


if __name__ == "__main__":
    main()
