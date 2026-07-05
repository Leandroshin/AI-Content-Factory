"""Demonstration: Product Research Department.

Flow:
  1. Receive 10 product candidates from manual/assisted research
  2. Score demand, margin, creative feasibility, competition, trust, and risk
  3. Shortlist the strongest candidates
  4. Deliver a handoff package for Affiliate Deals and approval
"""

from __future__ import annotations

from uuid import uuid4

from core.company.specialist_employee import EmployeeSkill, ReceivedTask, TaskDecision
from core.departments.product_research import (
    MarketplaceSignal,
    ProductCandidate,
    ProductResearchEmployee,
)
from core.events.bus import EventBus
from core.observability import ObservabilityProjector
from core.runtime import CompanyRuntime
from core.tools.capabilities import Capability


_ASSERTION_COUNTER: int = 0


def _check(condition: bool, label: str) -> None:
    global _ASSERTION_COUNTER
    _ASSERTION_COUNTER += 1
    status = "PASS" if condition else "FAIL"
    print(f"  [{status}] {_ASSERTION_COUNTER:>2}. {label}")
    if not condition:
        raise AssertionError(label)


def _signal(name: str, value: float, weight: float = 1.0, source: str = "") -> MarketplaceSignal:
    return MarketplaceSignal(name=name, value=value, weight=weight, source=source)


def _candidates() -> tuple[ProductCandidate, ...]:
    return (
        ProductCandidate(
            product_name="Mini projetor portátil 1080p",
            marketplace="mercado_livre",
            category="eletronicos",
            niche="casa_gamer",
            source_url="https://produto.example/mini-projetor",
            image_url="https://img.example/projetor.jpg",
            current_price=289.90,
            old_price=499.90,
            commission_percent=6.0,
            marketplace_trust=0.86,
            demand_signals=(
                _signal("youtube_mentions", 8, 1.2),
                _signal("deal_group_repeats", 7, 1.1),
                _signal("pain_intensity", 6, 1.0),
            ),
            creative_signals=(
                _signal("before_after_visual", 7, 1.1),
                _signal("demo_potential", 8, 1.0),
            ),
            competition_level="medium",
            saturation_level="medium",
            notes=("Easy visual demo: wall projection before/after.",),
        ),
        ProductCandidate(
            product_name="Controle PS5 DualSense Gray Camouflage",
            marketplace="amazon",
            category="gamer",
            niche="games",
            source_url="https://produto.example/dualsense",
            affiliate_url="https://amzn.example/dualsense-aff",
            image_url="https://img.example/dualsense.jpg",
            current_price=327.22,
            old_price=499.90,
            commission_percent=4.0,
            marketplace_trust=0.92,
            demand_signals=(
                _signal("deal_group_repeats", 9, 1.1),
                _signal("recognizable_brand", 8, 1.0),
            ),
            creative_signals=(
                _signal("product_photo_quality", 8, 1.0),
                _signal("short_hook_potential", 7, 1.0),
            ),
            competition_level="high",
            saturation_level="medium",
        ),
        ProductCandidate(
            product_name="Escova secadora compacta",
            marketplace="amazon",
            category="beleza",
            niche="beleza",
            source_url="https://produto.example/escova",
            image_url="https://img.example/escova.jpg",
            current_price=119.90,
            old_price=199.90,
            commission_percent=7.0,
            marketplace_trust=0.88,
            demand_signals=(
                _signal("tiktok_visual_trend", 8, 1.2),
                _signal("problem_frequency", 7, 1.0),
            ),
            creative_signals=(
                _signal("ugc_demo_potential", 9, 1.2),
                _signal("before_after_visual", 8, 1.0),
            ),
            competition_level="medium",
            saturation_level="low",
            notes=("Needs honest claims; no miracle language.",),
        ),
        ProductCandidate(
            product_name="Kit organizador transparente para geladeira",
            marketplace="mercado_livre",
            category="casa",
            niche="organizacao",
            source_url="https://produto.example/organizador",
            current_price=79.90,
            old_price=129.90,
            commission_percent=5.0,
            marketplace_trust=0.84,
            demand_signals=(
                _signal("evergreen_problem", 8, 1.0),
                _signal("home_content_fit", 7, 1.0),
            ),
            creative_signals=(
                _signal("before_after_visual", 8, 1.0),
            ),
            competition_level="medium",
            saturation_level="medium",
        ),
        ProductCandidate(
            product_name="Fone bluetooth sem marca com bateria 72h",
            marketplace="unknown_store",
            category="audio",
            niche="tech",
            source_url="https://produto.example/fone-duvidoso",
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
        ProductCandidate(
            product_name="Curso rápido de organização financeira pessoal",
            marketplace="hotmart",
            category="infoproduto",
            niche="financas_pessoais",
            source_url="https://produto.example/curso-financas",
            affiliate_url="https://hotmart.example/curso-financas-aff",
            image_url="https://img.example/curso-financas.jpg",
            current_price=97.0,
            old_price=297.0,
            commission_percent=40.0,
            marketplace_trust=0.78,
            demand_signals=(
                _signal("pain_intensity", 8, 1.0),
                _signal("evergreen_problem", 8, 1.0),
            ),
            creative_signals=(_signal("educational_angle", 7, 1.0),),
            competition_level="medium",
            saturation_level="medium",
            risk_flags=("regulated_finance_claims",),
            metadata={"manual_source_reviewed": True, "positioning": "educational"},
        ),
        ProductCandidate(
            product_name="Ring light de mesa com suporte de celular",
            marketplace="mercado_livre",
            category="criador",
            niche="criadores",
            source_url="https://produto.example/ring-light",
            image_url="https://img.example/ring-light.jpg",
            current_price=59.90,
            old_price=109.90,
            commission_percent=5.0,
            marketplace_trust=0.86,
            demand_signals=(
                _signal("creator_need", 8, 1.0),
                _signal("low_ticket_impulse", 8, 1.0),
            ),
            creative_signals=(
                _signal("demo_potential", 9, 1.0),
                _signal("visible_result", 8, 1.0),
            ),
            competition_level="medium",
            saturation_level="low",
        ),
        ProductCandidate(
            product_name="Mini impressora térmica bluetooth",
            marketplace="shopee",
            category="papelaria",
            niche="estudo",
            source_url="https://produto.example/mini-impressora",
            image_url="https://img.example/impressora.jpg",
            current_price=89.90,
            old_price=149.90,
            commission_percent=8.0,
            marketplace_trust=0.72,
            demand_signals=(
                _signal("tiktok_visual_trend", 9, 1.0),
                _signal("giftability", 7, 1.0),
            ),
            creative_signals=(
                _signal("satisfying_demo", 9, 1.2),
            ),
            competition_level="high",
            saturation_level="high",
            notes=("Good visual product, but saturated.",),
        ),
        ProductCandidate(
            product_name="Monitor gamer 24 polegadas 144Hz",
            marketplace="amazon",
            category="gamer",
            niche="pc_gamer",
            source_url="https://produto.example/monitor",
            image_url="https://img.example/monitor.jpg",
            current_price=530.10,
            old_price=749.00,
            commission_percent=3.0,
            marketplace_trust=0.92,
            demand_signals=(
                _signal("deal_group_repeats", 7, 1.0),
                _signal("high_search_intent", 8, 1.0),
            ),
            creative_signals=(_signal("product_photo_quality", 6, 1.0),),
            competition_level="high",
            saturation_level="medium",
        ),
        ProductCandidate(
            product_name="Garrafa térmica inteligente com display",
            marketplace="tiktok_shop",
            category="casa",
            niche="presentes",
            source_url="https://produto.example/garrafa-display",
            image_url="https://img.example/garrafa.jpg",
            current_price=49.90,
            old_price=99.90,
            commission_percent=9.0,
            marketplace_trust=0.72,
            demand_signals=(
                _signal("short_video_fit", 8, 1.0),
                _signal("giftability", 8, 1.0),
            ),
            creative_signals=(
                _signal("demo_potential", 8, 1.0),
                _signal("curiosity_hook", 8, 1.0),
            ),
            competition_level="medium",
            saturation_level="medium",
        ),
    )


def main() -> None:
    print("=" * 70)
    print("Product Research Department - Candidate Shortlist")
    print("=" * 70)

    event_bus = EventBus()
    observer = ObservabilityProjector(event_bus)
    company = CompanyRuntime(event_bus)
    company.initialize_company()

    employee = ProductResearchEmployee(
        company_runtime=company,
        employee_id=uuid4(),
        skills=(
            EmployeeSkill(name="web_search", proficiency=0.84),
            EmployeeSkill(name="market_signal_review", proficiency=0.86),
            EmployeeSkill(name="creative_feasibility", proficiency=0.82),
            EmployeeSkill(name="risk_triage", proficiency=0.8),
        ),
        event_bus=event_bus,
    )

    task = ReceivedTask(
        task_id=uuid4(),
        title="Rankear 10 candidatos de produtos vencedores",
        description="Organize and score candidate products before Affiliate Deals production.",
        department="Product Research",
        required_skills=("web_search", "risk_triage"),
        context={
            "objective": "Find products worth sending to AffiliateDealsEmployee.",
            "target_market": "BR",
            "niches": ("gamer", "casa", "beleza", "criadores", "infoprodutos"),
            "source_platforms": ("manual", "telegram_reference", "youtube_strategy", "marketplace"),
            "candidates": _candidates(),
            "shortlist_size": 4,
            "require_affiliate_url": False,
        },
    )

    print("\n" + "-" * 70)
    print("Step 1: Receive product research task")
    print("-" * 70)
    decision = employee.receive_task(task)
    _check(decision == TaskDecision.ACCEPTED, "Product research task accepted")
    _check(employee.pipeline_stage == "created", "Pipeline starts at created")
    _check(len(employee.product_research_capabilities) == 6, "Research capabilities loaded")

    print("\n" + "-" * 70)
    print("Step 2: Execute product research pipeline")
    print("-" * 70)
    result = employee.execute_task(task.task_id)
    output = result.output
    shortlisted = output["shortlisted"]
    findings = output["findings"]

    _check(result.success, "Product research pipeline succeeded")
    _check(output["total_candidates"] == 10, "Ten candidates analyzed")
    _check(len(shortlisted) == 4, "Four candidates shortlisted")
    _check(output["rejected_count"] >= 1, "At least one risky candidate rejected")
    _check(shortlisted[0]["score_total"] >= shortlisted[-1]["score_total"], "Shortlist sorted by score")
    _check(all(item["recommendation"] != "skip" for item in shortlisted), "Shortlist excludes skipped candidates")
    _check(any(item["marketplace"] == "tiktok_shop" for item in findings), "TikTok Shop source can be represented")
    _check(any(item["marketplace"] == "hotmart" for item in findings), "Digital product source can be represented")
    _check(any("affiliate_url_missing" in item["reasons"] for item in findings), "Missing affiliate URL can be flagged")
    _check(any("risk_flags_present" in item["reasons"] for item in findings), "Risk flags influence scoring")

    print("\n" + "-" * 70)
    print("Step 3: Handoff to Affiliate Deals")
    print("-" * 70)
    next_actions = output["next_actions"]
    _check(any("AffiliateDealsEmployee" in action for action in next_actions), "Handoff points to AffiliateDealsEmployee")
    _check(any("affiliate links" in action for action in next_actions), "Next actions mention affiliate links")
    _check(any("image quality" in action for action in next_actions), "Next actions mention image review")
    _check(employee.production_metrics.candidates_analyzed == 10, "Metrics count candidates")
    _check(employee.production_metrics.shortlisted_count == 4, "Metrics count shortlist")
    _check(employee.production_metrics.top_score == shortlisted[0]["score_total"], "Metrics keep top score")

    needs = employee.analyze_capability_needs()
    _check(Capability.WEB_SEARCH in needs, "WEB_SEARCH capability needed")
    _check(Capability.BROWSER_AUTOMATION in needs, "BROWSER_AUTOMATION capability needed")
    _check(Capability.IMAGE_EDITING in needs, "IMAGE_EDITING capability needed for creative/image review")

    print("\n" + "-" * 70)
    print("Step 4: Observability")
    print("-" * 70)
    snap = observer.snapshot
    _check(snap.product_research_production.pipeline_stage == "completed", "Product research production completed")
    _check(snap.product_research_department.successful_productions == 1, "Product research success projected")
    _check(snap.product_research_metrics.total_candidates_analyzed == 10, "Candidates projected")
    _check(snap.product_research_metrics.shortlisted_count == 4, "Shortlist projected")
    _check(snap.product_research_metrics.top_score == shortlisted[0]["score_total"], "Top score projected")
    _check(any("dept=product_research" in event for event in snap.events), "Product research events logged")

    print(f"\n{'=' * 70}")
    print(f"All {_ASSERTION_COUNTER} assertions passed.")
    print(f"{'=' * 70}")


if __name__ == "__main__":
    main()
