"""Proof of evidence-first TikTok growth planning with owner approval."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

from core.content_factory import (
    AudienceGrowthPlanner,
    GrowthCandidate,
    GrowthDecisionStatus,
    TrendEvidence,
)


def main() -> None:
    now = datetime(2026, 7, 11, 12, 0, tzinfo=UTC)
    official = TrendEvidence(
        title="Grand Theft Auto VI",
        source_url="https://www.rockstargames.com/VI/",
        source_type="official_product_page",
        observed_at=now - timedelta(hours=3),
        confidence=1.0,
    )
    unsafe = TrendEvidence(
        title="Unverified income video",
        source_url="https://example.invalid/video",
        source_type="social_video",
        observed_at=now - timedelta(hours=1),
        confidence=0.2,
    )
    candidates = (
        GrowthCandidate(
            candidate_id="gta6-countdown-01",
            topic="Tres fatos oficiais de GTA VI antes do lancamento",
            hook="GTA VI ja tem data, mas estes tres detalhes passaram despercebidos.",
            angle="official facts without rumor",
            pillar="gaming",
            key_points=("Official release date", "Leonida setting", "Only verified material"),
            evidence=(official,),
            visual_plan=("official page capture", "release date typography", "map-style motion"),
            series_potential=True,
        ),
        GrowthCandidate(
            candidate_id="income-promise-01",
            topic="Ganhe dinheiro garantido em um dia",
            hook="Dinheiro garantido hoje.",
            angle="income promise",
            pillar="technology_ai",
            key_points=("Unverified promise",),
            evidence=(unsafe,),
            visual_plan=("money screenshot",),
            risks=("income_guarantee", "unverified_claim"),
        ),
        GrowthCandidate(
            candidate_id="off-topic-01",
            topic="Unrelated topic",
            hook="Unrelated.",
            angle="unrelated",
            pillar="celebrity_gossip",
            key_points=("Not aligned",),
            evidence=(official,),
        ),
    )

    planner = AudienceGrowthPlanner(max_candidates=10, cadence_per_week=5)
    review_plan = planner.build_plan(candidates, now=now)
    assert len(review_plan.decisions) == 3
    assert len(review_plan.approved_briefs) == 0
    assert review_plan.manual_publish is True
    assert review_plan.cadence_per_week == 5
    gta_review = next(item for item in review_plan.decisions if item.candidate.candidate_id == "gta6-countdown-01")
    assert gta_review.status is GrowthDecisionStatus.REVIEW
    assert gta_review.score.total == 100.0
    assert gta_review.score.evidence == 30.0
    assert gta_review.score.freshness == 20.0
    assert gta_review.score.visual == 15.0
    assert gta_review.score.series == 15.0
    assert gta_review.score.alignment == 20.0
    assert gta_review.score.penalty == 0.0

    blocked = [item for item in review_plan.decisions if item.status is GrowthDecisionStatus.BLOCKED]
    assert len(blocked) == 2
    assert any("blocked:income_guarantee" in item.reasons for item in blocked)
    assert any("blocked:off_strategy_pillar" in item.reasons for item in blocked)

    approved_plan = planner.build_plan(candidates, approved_ids=("gta6-countdown-01",), now=now)
    assert len(approved_plan.approved_briefs) == 1
    brief = approved_plan.approved_briefs[0]
    assert brief.platform == "tiktok"
    assert brief.language == "pt-BR"
    assert brief.duration_seconds == 45
    assert brief.metadata["manual_publish"] is True
    assert brief.metadata["requires_final_policy_review"] is True
    assert brief.metadata["candidate_id"] == "gta6-countdown-01"
    assert brief.metadata["source_urls"] == ("https://www.rockstargames.com/VI/",)
    assert brief.metadata["growth_score"] == 100.0
    assert "Official release date" in brief.key_points
    print("All 24 assertions passed.")


if __name__ == "__main__":
    main()
