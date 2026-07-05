"""Demonstration: Creative Review Department.

Flow:
  1. Receive product images, offer screenshots, and thumbnail references
  2. Decide whether each asset is publishable, needs cleanup, needs rebuild, or needs owner review
  3. Deliver a handoff package for Affiliate Deals, Image, Video, and HITL approval
"""

from __future__ import annotations

from uuid import uuid4

from core.company.specialist_employee import EmployeeSkill, ReceivedTask, TaskDecision
from core.departments.creative_review import CreativeAsset, CreativeReviewEmployee
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


def _assets() -> tuple[CreativeAsset, ...]:
    return (
        CreativeAsset(
            title="Clean marketplace product photo",
            asset_type="product_image",
            product_name="Controle PS5 DualSense Gray Camouflage",
            platform="amazon",
            image_url="https://img.example/dualsense-clean.jpg",
            use_case="affiliate_post",
            visual_quality=10,
            product_visibility=10,
            resolution_score=10,
            text_clutter=0,
            watermark_risk=0,
            brand_safety=10,
            notes=("Good product focus; no rebuild needed.",),
        ),
        CreativeAsset(
            title="Offer card with useful product visual but some noise",
            asset_type="offer_card",
            product_name="Monitor Gamer AOC AGON",
            platform="telegram",
            image_url="https://img.example/monitor-offer.jpg",
            use_case="affiliate_post",
            visual_quality=8.5,
            product_visibility=8.5,
            resolution_score=8,
            text_clutter=3.5,
            watermark_risk=0,
            brand_safety=8.5,
            notes=("Can be posted after small cleanup.",),
        ),
        CreativeAsset(
            title="TikTok Shop money thumbnail reference",
            asset_type="thumbnail_reference",
            product_name="TikTok Shop strategy video",
            platform="youtube",
            file_path="C:/Users/Shin/AppData/Local/Temp/codex-clipboard-888738a9-0d2c-4f06-bdcd-6df598ed4c66.png",
            source_url="local://thumbnail-reference",
            use_case="youtube_thumbnail",
            visual_quality=9,
            product_visibility=6,
            resolution_score=8,
            text_clutter=6,
            watermark_risk=4,
            brand_safety=7,
            face_emotion=9,
            proof_element=9,
            risk_flags=("third_party_thumbnail_reference", "earnings_claim"),
            notes=("Use the formula, not the original face or proof card.",),
        ),
        CreativeAsset(
            title="Blurry supplier product photo",
            asset_type="product_image",
            product_name="Mini impressora termica",
            platform="shopee",
            image_url="https://img.example/blurry-printer.jpg",
            use_case="short_video",
            visual_quality=3,
            product_visibility=3,
            resolution_score=2,
            text_clutter=1,
            watermark_risk=0,
            brand_safety=8,
            notes=("Product is hard to see.",),
        ),
    )


def main() -> None:
    print("=" * 70)
    print("Creative Review Department - Asset Readiness")
    print("=" * 70)

    event_bus = EventBus()
    observer = ObservabilityProjector(event_bus)
    company = CompanyRuntime(event_bus)
    company.initialize_company()

    employee = CreativeReviewEmployee(
        company_runtime=company,
        employee_id=uuid4(),
        skills=(
            EmployeeSkill(name="image_readiness", proficiency=0.9),
            EmployeeSkill(name="thumbnail_formula_review", proficiency=0.86),
            EmployeeSkill(name="earnings_claim_review", proficiency=0.88),
        ),
        event_bus=event_bus,
    )

    task = ReceivedTask(
        task_id=uuid4(),
        title="Revisar criativos antes de publicar ofertas",
        description="Decide what can be posted now and what needs improvement.",
        department="Creative Review",
        required_skills=("image_readiness", "thumbnail_formula_review"),
        context={
            "objective": "Avoid wasting time rebuilding assets that are already good enough.",
            "target_platforms": ("telegram", "youtube", "tiktok_shop"),
            "ready_threshold": 72,
            "assets": _assets(),
        },
    )

    print("\n" + "-" * 70)
    print("Step 1: Receive creative review task")
    print("-" * 70)
    decision = employee.receive_task(task)
    _check(decision == TaskDecision.ACCEPTED, "Creative review task accepted")
    _check(employee.pipeline_stage == "created", "Pipeline starts at created")
    _check(len(employee.creative_review_capabilities) == 5, "Creative capabilities loaded")

    print("\n" + "-" * 70)
    print("Step 2: Execute creative review")
    print("-" * 70)
    result = employee.execute_task(task.task_id)
    output = result.output
    findings = output["findings"]
    actions = {finding["title"]: finding["recommended_action"] for finding in findings}

    _check(result.success, "Creative review pipeline succeeded")
    _check(output["total_assets"] == 4, "Four assets reviewed")
    _check(output["ready_count"] == 1, "One asset can be used as-is")
    _check(output["improve_count"] == 1, "One asset needs light cleanup")
    _check(output["rebuild_count"] >= 1, "At least one asset needs rebuild or alternative image")
    _check(output["human_review_count"] == 1, "Thumbnail reference is held for human review")
    _check(actions["Clean marketplace product photo"] == "use_as_is", "Clean product image avoids unnecessary rebuild")
    _check(actions["Offer card with useful product visual but some noise"] == "minor_cleanup", "Noisy but useful card gets cleanup")
    _check(actions["TikTok Shop money thumbnail reference"] == "human_review", "Third-party thumbnail is reference-only")
    _check(actions["Blurry supplier product photo"] == "find_alternative_image", "Blurry image requests alternative")

    print("\n" + "-" * 70)
    print("Step 3: Handoff and capabilities")
    print("-" * 70)
    next_actions = output["next_actions"]
    _check(any("AffiliateDealsEmployee" in action for action in next_actions), "Ready assets hand off to AffiliateDealsEmployee")
    _check(any("ImageDesignerEmployee" in action for action in next_actions), "Cleanup hands off to ImageDesignerEmployee")
    _check(any("owner approval" in action for action in next_actions), "Risky assets require owner approval")
    _check(employee.production_metrics.assets_reviewed == 4, "Metrics count assets")
    _check(employee.production_metrics.ready_count == 1, "Metrics count ready assets")
    _check(employee.production_metrics.rebuild_count >= 1, "Metrics count rebuild/alternative assets")

    needs = employee.analyze_capability_needs()
    _check(Capability.IMAGE_EDITING in needs, "IMAGE_EDITING capability needed")
    _check(Capability.IMAGE_GENERATION in needs, "IMAGE_GENERATION capability needed")
    _check(Capability.WEB_SEARCH in needs, "WEB_SEARCH capability needed")

    print("\n" + "-" * 70)
    print("Step 4: Observability")
    print("-" * 70)
    snap = observer.snapshot
    _check(snap.creative_review_production.pipeline_stage == "completed", "Creative review production completed")
    _check(snap.creative_review_department.successful_productions == 1, "Creative review success projected")
    _check(snap.creative_review_metrics.assets_reviewed == 4, "Assets projected")
    _check(snap.creative_review_metrics.ready_count == 1, "Ready count projected")
    _check(any("dept=creative_review" in event for event in snap.events), "Creative review events logged")

    print(f"\n{'=' * 70}")
    print(f"All {_ASSERTION_COUNTER} assertions passed.")
    print(f"{'=' * 70}")


if __name__ == "__main__":
    main()
