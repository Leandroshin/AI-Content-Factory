"""Proof of daily gaming monitoring, no-news behavior and owner gating."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from tempfile import TemporaryDirectory

from core.content_factory import (
    GamingNewsDesk,
    GamingNewsItem,
    GamingNewsSource,
    GrowthDecisionStatus,
    JsonGamingNewsStateStore,
)


def main() -> None:
    now = datetime(2026, 7, 11, 9, 0, tzinfo=UTC)
    rockstar = GamingNewsSource(
        name="Rockstar Newswire",
        url="https://www.rockstargames.com/newswire",
        source_type="official_publisher",
        authority=1.0,
        primary=True,
    )
    rumor_channel = GamingNewsSource(
        name="Rumor Channel",
        url="https://example.invalid/channel",
        source_type="youtube_discovery",
        authority=0.4,
    )
    confirmed = GamingNewsItem(
        title="Grand Theft Auto VI pre-orders begin",
        url="https://www.rockstargames.com/newswire/article/example",
        published_at=now - timedelta(hours=2),
        source=rockstar,
        game="GTA VI",
        tags=("gta6", "release"),
        key_points=("Official announcement", "Pre-order timing", "Verified platforms"),
        visual_plan=("official page excerpt", "kinetic title", "platform icons"),
        external_id="rockstar-gta6-preorder",
        metadata={"hook": "A Rockstar acabou de atualizar a campanha de GTA VI."},
    )
    rumor = GamingNewsItem(
        title="Secret GTA VI map leaked",
        url="https://example.invalid/leak",
        published_at=now - timedelta(hours=1),
        source=rumor_channel,
        game="GTA VI",
        tags=("leak",),
        key_points=("Unverified map",),
        rumor=True,
    )

    desk = GamingNewsDesk()
    first = desk.run((confirmed, rumor), now=now)
    assert first.no_news is False
    assert len(first.new_items) == 1
    assert len(first.rejected_items) == 1
    assert first.new_items[0].title == confirmed.title
    assert len(first.growth_plan.decisions) == 1
    assert first.growth_plan.decisions[0].status is GrowthDecisionStatus.REVIEW
    assert len(first.growth_plan.approved_briefs) == 0
    assert first.state.last_run_at == now
    assert len(first.state.seen_fingerprints) == 2

    candidate_id = first.growth_plan.decisions[0].candidate.candidate_id
    approved = desk.run(
        (confirmed,),
        state=None,
        approved_ids=(candidate_id,),
        now=now,
    )
    assert len(approved.growth_plan.approved_briefs) == 1
    brief = approved.growth_plan.approved_briefs[0]
    assert brief.platform == "tiktok"
    assert brief.metadata["youtube_shorts_variant"] is True
    assert brief.metadata["subtitles_required"] is True
    assert brief.metadata["avatar_optional"] is True
    assert brief.metadata["source_primary"] is True

    duplicate_run = desk.run((confirmed,), state=first.state, now=now + timedelta(days=1))
    assert duplicate_run.no_news is True
    assert len(duplicate_run.new_items) == 0
    assert len(duplicate_run.rejected_items) == 1
    assert len(duplicate_run.growth_plan.decisions) == 0

    with TemporaryDirectory() as temp_dir:
        store = JsonGamingNewsStateStore(f"{temp_dir}/gaming-state.json")
        store.save(first.state)
        restored = store.load()
        assert restored == first.state
        assert len(restored.seen_fingerprints) == 2

    print("All 22 assertions passed.")


if __name__ == "__main__":
    main()
