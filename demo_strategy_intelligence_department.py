"""Demonstration: Strategy Intelligence Department.

Flow:
  1. Receive short, derived notes from transcripts/videos
  2. Detect tools, metrics, reusable strategy patterns, and guardrails
  3. Deliver a handoff package for Product Research, Creative Review, and Affiliate Deals
"""

from __future__ import annotations

from uuid import uuid4

from core.company.specialist_employee import EmployeeSkill, ReceivedTask, TaskDecision
from core.departments.strategy_intelligence import (
    StrategyIntelligenceEmployee,
    StrategySource,
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


def _sources() -> tuple[StrategySource, ...]:
    return (
        StrategySource(
            title="TikTok Shop POV AI strategy notes",
            creator="youtube_notes",
            source_url="https://youtube.example/tiktok-shop-pov",
            transcript_text=(
                "TikTok Shop POV video strategy with IA. Select products by grafico de crescimento, "
                "avoid queda in grafico, compare receita, ticket medio, comissao, and product images. "
                "Kalodata style research can show product, creator, and video signals."
            ),
            tags=("tiktok_shop", "pov", "product_research"),
        ),
        StrategySource(
            title="Amazon Keepa product validation notes",
            creator="amazon_course_notes",
            source_url="https://youtube.example/keepa",
            transcript_text=(
                "Keepa analysis checks ranking, BSR, Buy Box, variacao, reviews, avaliacao, "
                "preco historico, sellers, and whether Amazon shares the Buy Box."
            ),
            tags=("amazon", "keepa", "metrics"),
        ),
        StrategySource(
            title="Affiliate post automation notes",
            creator="affiliate_automation_notes",
            source_url="https://youtube.example/automation",
            transcript_text=(
                "Divulga Ninja and Insta Ninja examples mention AliExpress API, affiliate links, "
                "post automatico for Telegram, WhatsApp, and Instagram with product cards."
            ),
            tags=("affiliate", "automation"),
        ),
        StrategySource(
            title="Original infoproduct to checkout notes",
            creator="digital_product_notes",
            source_url="https://youtube.example/cakto",
            transcript_text=(
                "Claude can help plan an original produto, ebook, curso, entregaveis, cover, "
                "Gamma document, Canva assets, CapCut video, and Cakto checkout. TokFy appears as "
                "TikTok Shop AI tooling."
            ),
            tags=("digital_product", "checkout"),
        ),
        StrategySource(
            title="Thumbnail formula notes",
            creator="visual_reference_notes",
            source_url="local://thumbnail-reference",
            transcript_text=(
                "TikTok Shop thumbnail and thumb style: expressive face, SACAR button, proof card, "
                "platform logo, giant text, glow, and short promise. This is a style formula."
            ),
            tags=("thumbnail", "creative"),
        ),
        StrategySource(
            title="TikTok Shop eight-second Omni Flash notes",
            creator="youtube_notes",
            source_url="https://www.youtube.com/watch/HQ1F5jzAiss",
            transcript_text=(
                "TikTok Shop strategy with Google Flow and Gemini Omni Flash. Generate two 8 segundos "
                "image-to-video variants, add a CapCut textual hook, and measure conversao. The tutorial "
                "uses a rosto de mulher from Pinterest and shows faturamento and saque por semana."
            ),
            tags=("tiktok_shop", "omni_flash", "short_video", "claims"),
        ),
        StrategySource(
            title="OmniRoute gateway and visual demonstration notes",
            creator="youtube_notes",
            source_url="https://www.youtube.com/watch/example-omniroute",
            transcript_text=(
                "OmniRoute is an OpenAI compatible gateway. The navegador mostra and exibe the dashboard, "
                "provider page, API endpoint, and each tela while the video explains the related step. "
                "Free provider quotas and terms still require independent verification."
            ),
            tags=("provider_gateway", "video_editorial"),
        ),
        StrategySource(
            title="Affiliate network portfolio notes",
            creator="youtube_notes",
            source_url="https://www.youtube.com/watch/IdLbwCypSx4",
            transcript_text=(
                "Compare Amazon and Mercado Livre with ClickBank, Digistore24, BuyGoods, MaxWeb, "
                "Media Scalers and Braip. Evaluate tempo de cookie, comissao, CPA, saque, payout limits, "
                "refunds, paid traffic permissions and net conversion instead of copying a tier list."
            ),
            tags=("affiliate_networks", "offer_economics"),
        ),
    )


def main() -> None:
    print("=" * 70)
    print("Strategy Intelligence Department - Source Learning")
    print("=" * 70)

    event_bus = EventBus()
    observer = ObservabilityProjector(event_bus)
    company = CompanyRuntime(event_bus)
    company.initialize_company()

    employee = StrategyIntelligenceEmployee(
        company_runtime=company,
        employee_id=uuid4(),
        skills=(
            EmployeeSkill(name="source_triage", proficiency=0.88),
            EmployeeSkill(name="metric_extraction", proficiency=0.86),
            EmployeeSkill(name="copyright_safe_learning", proficiency=0.92),
        ),
        event_bus=event_bus,
    )

    task = ReceivedTask(
        task_id=uuid4(),
        title="Aprender estrategias de videos de afiliados e TikTok Shop",
        description="Extract safe reusable strategy from transcript-derived notes.",
        department="Strategy Intelligence",
        required_skills=("source_triage", "metric_extraction"),
        context={
            "objective": "Turn YouTube strategy notes into reusable operating knowledge.",
            "focus_areas": ("affiliate", "product_research", "creative", "digital_product"),
            "sources": _sources(),
            "max_patterns": 12,
        },
    )

    print("\n" + "-" * 70)
    print("Step 1: Receive strategy task")
    print("-" * 70)
    decision = employee.receive_task(task)
    _check(decision == TaskDecision.ACCEPTED, "Strategy intelligence task accepted")
    _check(employee.pipeline_stage == "created", "Pipeline starts at created")
    _check(len(employee.strategy_capabilities) == 6, "Strategy capabilities loaded")

    print("\n" + "-" * 70)
    print("Step 2: Execute strategy extraction")
    print("-" * 70)
    result = employee.execute_task(task.task_id)
    output = result.output
    tools = {tool["name"] for tool in output["tools_detected"]}
    metrics = {metric["name"] for metric in output["metrics_detected"]}
    patterns = {pattern["pattern_id"] for pattern in output["patterns"]}

    _check(result.success, "Strategy intelligence pipeline succeeded")
    _check(output["sources_analyzed"] == 8, "Eight sources analyzed")
    _check({"Keepa", "Divulga Ninja", "Cakto", "Kalodata", "Google Flow", "Gemini Omni Flash", "OmniRoute", "Digistore24"} <= tools, "Key tools detected")
    _check({"trend_growth_graph", "buy_box_share", "average_ticket", "short_completion_hypothesis", "conversion_signal", "cookie_window", "payout_friction", "fixed_cpa"} <= metrics, "Decision metrics detected")
    _check("tiktok_shop_pov_ai_video" in patterns, "TikTok Shop POV pattern extracted")
    _check("amazon_keepa_product_analysis" in patterns, "Amazon Keepa pattern extracted")
    _check("affiliate_post_automation" in patterns, "Affiliate automation pattern extracted")
    _check("ai_infoproduct_to_checkout" in patterns, "Original infoproduct pattern extracted")
    _check("thumbnail_money_proof_pattern" in patterns, "Thumbnail formula pattern extracted")
    _check("tiktok_shop_8s_commerce_test" in patterns, "Eight-second commerce experiment extracted")
    _check("audited_llm_gateway" in patterns, "Audited LLM gateway pattern extracted")
    _check("affiliate_network_portfolio" in patterns, "Affiliate network portfolio pattern extracted")
    _check("narration_evidence_visual_sync" in patterns, "Narration-to-evidence visual pattern extracted")

    print("\n" + "-" * 70)
    print("Step 3: Guardrails and handoff")
    print("-" * 70)
    warnings = output["warnings"]
    next_actions = output["next_actions"]
    _check(any("original" in warning.lower() for warning in warnings), "Original-content guardrail present")
    _check(any("guarantees" in warning.lower() for warning in warnings), "No guaranteed earnings guardrail present")
    _check(any("pinterest" in warning.lower() for warning in warnings), "Likeness-rights guardrail present")
    _check(any("selected marketing evidence" in warning.lower() for warning in warnings), "Revenue-proof warning present")
    _check(any("CreativeReviewEmployee" in action for action in next_actions), "Handoff points to CreativeReviewEmployee")
    _check(any("ProductResearchEmployee" in action for action in next_actions), "Handoff points to ProductResearchEmployee")
    _check(employee.production_metrics.sources_analyzed == 8, "Metrics count sources")
    _check(employee.production_metrics.patterns_extracted >= 5, "Metrics count patterns")

    needs = employee.analyze_capability_needs()
    _check(Capability.TRANSCRIPTION in needs, "TRANSCRIPTION capability needed")
    _check(Capability.TEXT_GENERATION in needs, "TEXT_GENERATION capability needed")
    _check(Capability.STORAGE in needs, "STORAGE capability needed")

    print("\n" + "-" * 70)
    print("Step 4: Observability")
    print("-" * 70)
    snap = observer.snapshot
    _check(snap.strategy_intelligence_production.pipeline_stage == "completed", "Strategy production completed")
    _check(snap.strategy_intelligence_department.successful_productions == 1, "Strategy success projected")
    _check(snap.strategy_intelligence_metrics.sources_analyzed == 8, "Sources projected")
    _check(snap.strategy_intelligence_metrics.patterns_extracted >= 5, "Patterns projected")
    _check(any("dept=strategy_intelligence" in event for event in snap.events), "Strategy events logged")

    print(f"\n{'=' * 70}")
    print(f"All {_ASSERTION_COUNTER} assertions passed.")
    print(f"{'=' * 70}")


if __name__ == "__main__":
    main()
