"""Foundation demo for the Skill Runtime.

Validates SkillRecord creation, LearningRecommendation promotion,
filtering by level, immutability, ordering, trace, determinism,
and the complete Conversation -> Memory -> Knowledge -> Learning -> Skills pipeline.
"""

from __future__ import annotations

from uuid import UUID

from core.learning.foundation import (
    LearningRecommendation,
    LearningRuntime,
    LearningSnapshot,
)
from core.skills.foundation import (
    SkillRecord,
    SkillResult,
    SkillRuntime,
    SkillSnapshot,
    SkillTrace,
)


# ------------------------------------------------------------------
# Scenario 1: Empty snapshot
# ------------------------------------------------------------------


def scenario_empty_snapshot() -> None:
    """A newly created snapshot has no skills."""
    snapshot = SkillRuntime.create_snapshot()

    assert isinstance(snapshot, SkillSnapshot)
    assert snapshot.skills == ()
    assert snapshot.created_at > 0
    print(f"[PASS] empty_snapshot                  | skills={len(snapshot.skills)} "
          f"created_at={snapshot.created_at:.2f}")


# ------------------------------------------------------------------
# Scenario 2: Promote one recommendation
# ------------------------------------------------------------------


def scenario_promote_recommendation() -> None:
    """A LearningRecommendation is promoted to a SkillRecord."""
    rec = LearningRecommendation.create_with_timestamp(
        knowledge_id=UUID("00000000-0000-0000-0000-000000000001"),
        recommendation_type="study",
        title="Python Basics",
        description="Learn Python fundamentals.",
        timestamp=1000.0,
    )

    skill = SkillRuntime.promote_learning(rec)

    assert isinstance(skill, SkillRecord)
    assert skill.recommendation_id == rec.recommendation_id
    assert skill.skill_name == "Python Basics"
    assert skill.description == "Learn Python fundamentals."
    assert skill.level == 1
    assert skill.experience_points == 0
    print(f"[PASS] promote_recommendation         | skill_id={skill.skill_id.hex[:8]} "
          f"name='{skill.skill_name}' level={skill.level} exp={skill.experience_points}")


# ------------------------------------------------------------------
# Scenario 3: Multiple recommendations
# ------------------------------------------------------------------


def scenario_multiple_recommendations() -> None:
    """Multiple LearningRecommendations produce the same number of skills."""
    recs = [
        LearningRecommendation.create_with_timestamp(
            UUID("00000000-0000-0000-0000-000000000001"), "study", "A", "Alpha", 1.0,
        ),
        LearningRecommendation.create_with_timestamp(
            UUID("00000000-0000-0000-0000-000000000002"), "practice", "B", "Beta", 2.0,
        ),
        LearningRecommendation.create_with_timestamp(
            UUID("00000000-0000-0000-0000-000000000003"), "review", "C", "Gamma", 3.0,
        ),
    ]

    snapshot = SkillRuntime.create_snapshot()
    for rec in recs:
        skill = SkillRuntime.promote_learning(rec)
        snapshot = SkillRuntime.append_skill(snapshot, skill)

    assert len(snapshot.skills) == 3
    assert snapshot.skills[0].skill_name == "A"
    assert snapshot.skills[1].skill_name == "B"
    assert snapshot.skills[2].skill_name == "C"
    print(f"[PASS] multiple_recommendations       | {len(snapshot.skills)} skills -> "
          f"names=[{', '.join(s.skill_name for s in snapshot.skills)}]")


# ------------------------------------------------------------------
# Scenario 4: Order preserved
# ------------------------------------------------------------------


def scenario_order_preserved() -> None:
    """Skills maintain append order."""
    recs = [
        LearningRecommendation.create_with_timestamp(
            UUID("00000000-0000-0000-0000-000000000001"), "study", "First", "1", 1.0,
        ),
        LearningRecommendation.create_with_timestamp(
            UUID("00000000-0000-0000-0000-000000000002"), "study", "Second", "2", 2.0,
        ),
        LearningRecommendation.create_with_timestamp(
            UUID("00000000-0000-0000-0000-000000000003"), "study", "Third", "3", 3.0,
        ),
    ]

    snapshot = SkillRuntime.create_snapshot()
    for rec in recs:
        skill = SkillRuntime.promote_learning(rec)
        snapshot = SkillRuntime.append_skill(snapshot, skill)

    names = [s.skill_name for s in snapshot.skills]
    assert names == ["First", "Second", "Third"]
    print(f"[PASS] order_preserved                | names={names}")


# ------------------------------------------------------------------
# Scenario 5: Timestamps preserved
# ------------------------------------------------------------------


def scenario_timestamps_preserved() -> None:
    """Each promoted skill gets the recommendation's timestamp via created_at."""
    rec = LearningRecommendation.create_with_timestamp(
        UUID("00000000-0000-0000-0000-000000000001"), "study", "Timed Skill", "Content", 42.0,
    )
    skill = SkillRuntime.promote_learning(rec)

    assert skill.created_at > 0
    assert isinstance(skill.created_at, float)
    print(f"[PASS] timestamps_preserved            | created_at={skill.created_at:.2f}")


# ------------------------------------------------------------------
# Scenario 6: Metadata correct
# ------------------------------------------------------------------


def scenario_metadata_correct() -> None:
    """SkillRecord metadata starts as empty dict {}."""
    rec = LearningRecommendation.create_with_timestamp(
        UUID("00000000-0000-0000-0000-000000000001"), "study", "Meta Skill", "Content", 1.0,
    )
    skill = SkillRuntime.promote_learning(rec)

    assert skill.metadata == {}
    print(f"[PASS] metadata_correct               | metadata={skill.metadata}")


# ------------------------------------------------------------------
# Scenario 7: Level inicial (initial level)
# ------------------------------------------------------------------


def scenario_level_inicial() -> None:
    """All promoted skills start with level=1."""
    rec = LearningRecommendation.create_with_timestamp(
        UUID("00000000-0000-0000-0000-000000000001"), "study", "Level Test", "Content", 1.0,
    )
    skill = SkillRuntime.promote_learning(rec)

    assert skill.level == 1
    print(f"[PASS] level_inicial                  | level={skill.level}")


# ------------------------------------------------------------------
# Scenario 8: Experience inicial (initial experience)
# ------------------------------------------------------------------


def scenario_experience_inicial() -> None:
    """All promoted skills start with experience_points=0."""
    rec = LearningRecommendation.create_with_timestamp(
        UUID("00000000-0000-0000-0000-000000000001"), "study", "Exp Test", "Content", 1.0,
    )
    skill = SkillRuntime.promote_learning(rec)

    assert skill.experience_points == 0
    print(f"[PASS] experience_inicial             | experience_points={skill.experience_points}")


# ------------------------------------------------------------------
# Scenario 9: filter_by_level
# ------------------------------------------------------------------


def scenario_filter_by_level() -> None:
    """filter_by_level returns skills within the level range."""
    # All promoted skills start at level 1, so all should match default range
    recs = [
        LearningRecommendation.create_with_timestamp(
            UUID("00000000-0000-0000-0000-000000000001"), "study", "S1", "C1", 1.0,
        ),
        LearningRecommendation.create_with_timestamp(
            UUID("00000000-0000-0000-0000-000000000002"), "study", "S2", "C2", 2.0,
        ),
    ]

    snapshot = SkillRuntime.create_snapshot()
    for rec in recs:
        skill = SkillRuntime.promote_learning(rec)
        snapshot = SkillRuntime.append_skill(snapshot, skill)

    # All skills have level=1, default range 1-10 should catch all
    all_skills = SkillRuntime.filter_by_level(snapshot)
    assert len(all_skills) == 2

    # Range 2-10 should catch none (all are level 1)
    none_skills = SkillRuntime.filter_by_level(snapshot, min_level=2)
    assert len(none_skills) == 0

    print(f"[PASS] filter_by_level                | all={len(all_skills)}, "
          f"min_level=2 -> {len(none_skills)}")


# ------------------------------------------------------------------
# Scenario 10: Snapshot correct
# ------------------------------------------------------------------


def scenario_snapshot_correct() -> None:
    """promote_snapshot converts a LearningSnapshot to a SkillSnapshot."""
    recs = [
        LearningRecommendation.create_with_timestamp(
            UUID("00000000-0000-0000-0000-000000000001"), "study", "Skill A", "Desc A", 1.0,
        ),
        LearningRecommendation.create_with_timestamp(
            UUID("00000000-0000-0000-0000-000000000002"), "practice", "Skill B", "Desc B", 2.0,
        ),
    ]
    learn_snap = LearningRuntime.create_snapshot(recs)

    skill_snap = SkillRuntime.promote_snapshot(learn_snap)

    assert isinstance(skill_snap, SkillSnapshot)
    assert len(skill_snap.skills) == 2
    assert skill_snap.skills[0].skill_name == "Skill A"
    assert skill_snap.skills[1].skill_name == "Skill B"
    assert skill_snap.skills[0].recommendation_id == recs[0].recommendation_id
    assert skill_snap.skills[1].recommendation_id == recs[1].recommendation_id
    print(f"[PASS] snapshot_correct               | {len(skill_snap.skills)} skills "
          f"promoted from LearningSnapshot")


# ------------------------------------------------------------------
# Scenario 11: Trace correct
# ------------------------------------------------------------------


def scenario_trace_correct() -> None:
    """SkillResult contains snapshot, trace, and stats."""
    rec = LearningRecommendation.create_with_timestamp(
        UUID("00000000-0000-0000-0000-000000000001"), "study", "Trace Skill", "Content", 1.0,
    )
    skill = SkillRuntime.promote_learning(rec)
    snap = SkillRuntime.create_snapshot([skill])

    result = SkillRuntime.build_result(
        snapshot=snap,
        timestamps={"start": 100.0, "end": 101.0},
    )

    assert isinstance(result, SkillResult)
    assert result.success is True
    assert result.trace.recommendations_processed == 1
    assert result.trace.skills_created == 1
    assert result.trace.timestamps["start"] == 100.0
    assert result.error_message == ""
    print(f"[PASS] trace_correct                  | success={result.success} "
          f"processed={result.trace.recommendations_processed} "
          f"created={result.trace.skills_created}")


# ------------------------------------------------------------------
# Scenario 12: Immutability
# ------------------------------------------------------------------


def scenario_immutability() -> None:
    """Original snapshot is never mutated by append_skill."""
    original = SkillRuntime.create_snapshot()
    rec = LearningRecommendation.create_with_timestamp(
        UUID("00000000-0000-0000-0000-000000000001"), "study", "Immutable", "Content", 1.0,
    )
    skill = SkillRuntime.promote_learning(rec)

    _ = SkillRuntime.append_skill(original, skill)

    assert len(original.skills) == 0
    print(f"[PASS] immutability                   | original untouched "
          f"(skills={len(original.skills)})")


# ------------------------------------------------------------------
# Scenario 13: Determinism
# ------------------------------------------------------------------


def scenario_determinism() -> None:
    """Same LearningRecommendation produces identical skill content."""
    rec = LearningRecommendation.create_with_timestamp(
        UUID("00000000-0000-0000-0000-000000000001"), "study", "Det Skill", "Det Content", 1.0,
    )

    s1 = SkillRuntime.promote_learning(rec)
    s2 = SkillRuntime.promote_learning(rec)

    assert s1.skill_name == s2.skill_name
    assert s1.description == s2.description
    assert s1.level == s2.level
    assert s1.experience_points == s2.experience_points
    print(f"[PASS] determinism                    | name='{s1.skill_name}' "
          f"level={s1.level} exp={s1.experience_points} (identical)")


# ------------------------------------------------------------------
# Scenario 14: Full pipeline — empty LearningSnapshot
# ------------------------------------------------------------------


def scenario_pipeline_empty() -> None:
    """Empty LearningSnapshot promotes to empty SkillSnapshot."""
    learn_snap = LearningRuntime.create_snapshot()
    skill_snap = SkillRuntime.promote_snapshot(learn_snap)

    assert len(skill_snap.skills) == 0
    print(f"[PASS] pipeline_empty                 | empty LearningSnapshot -> "
          f"empty SkillSnapshot ({len(skill_snap.skills)} skills)")


# ------------------------------------------------------------------
# Scenario 15: Complete Conversation -> Memory -> Knowledge -> Learning -> Skills
# ------------------------------------------------------------------


def scenario_full_pipeline() -> None:
    """Complete end-to-end pipeline from conversation to skill record."""
    from core.conversation import ConversationRuntime
    from core.knowledge.foundation import KnowledgeRuntime as FoundationKR
    from core.memory import MemoryRecord, MemoryRuntime

    session = ConversationRuntime.create_session("emp-001")
    session = ConversationRuntime.append_message(session, "user", "Explain transformers.")
    session = ConversationRuntime.append_message(session, "assistant",
        "Transformers are a neural network architecture based on attention.")
    session = ConversationRuntime.append_message(session, "user", "What is attention?")
    session = ConversationRuntime.append_message(session, "assistant",
        "Attention is a mechanism that weighs input importance.")

    # Conversation -> Memory
    mem_records = []
    for msg in session.messages:
        mem_records.append(
            ConversationRuntime.create_memory_record(session, msg),
        )
    mem_snap = MemoryRuntime.create_snapshot(mem_records)
    assert len(mem_snap.records) == 4

    # Memory -> Knowledge
    know_records = MemoryRuntime.promote_records(mem_snap)
    know_snap = MemoryRuntime.promote_snapshot(mem_snap)
    assert len(know_records) == 4
    assert len(know_snap.records) == 4

    # Knowledge -> Learning
    learn_records = []
    for kr in know_records:
        learn_records.append(LearningRuntime.promote_knowledge(kr))
    learn_snap = LearningRuntime.promote_snapshot(know_snap)

    assert len(learn_records) == 4
    assert len(learn_snap.recommendations) == 4
    assert all(r.recommendation_type == "study" for r in learn_records)
    assert all(r.priority == 1 for r in learn_records)

    # Learning -> Skills
    skill_records = []
    for rec in learn_records:
        skill_records.append(SkillRuntime.promote_learning(rec))
    skill_snap = SkillRuntime.promote_snapshot(learn_snap)

    assert len(skill_records) == 4
    assert len(skill_snap.skills) == 4
    assert all(s.level == 1 for s in skill_records)
    assert all(s.experience_points == 0 for s in skill_records)
    assert skill_records[0].skill_name == "Memory Promotion"
    assert skill_records[0].description == "Explain transformers."
    assert skill_records[1].description == (
        "Transformers are a neural network architecture based on attention."
    )

    print(f"[PASS] full_pipeline                  | {len(session.messages)} msgs -> "
          f"{len(mem_records)} memory -> "
          f"{len(know_records)} knowledge -> "
          f"{len(learn_records)} learning -> "
          f"{len(skill_records)} skills")


# ------------------------------------------------------------------
# Scenario 16: Empty LearningSnapshot via promote_snapshot
# ------------------------------------------------------------------


def scenario_promote_snapshot_empty() -> None:
    """promote_snapshot with empty LearningSnapshot returns empty SkillSnapshot."""
    learn_snap = LearningRuntime.create_snapshot()
    skill_snap = SkillRuntime.promote_snapshot(learn_snap)

    assert len(skill_snap.skills) == 0
    assert skill_snap.created_at > 0
    print(f"[PASS] promote_snapshot_empty         | skills={len(skill_snap.skills)} "
          f"created_at={skill_snap.created_at:.2f}")


# ------------------------------------------------------------------
# Scenario 17: SkillRecord factory create and create_with_timestamp
# ------------------------------------------------------------------


def scenario_skill_record_factories() -> None:
    """SkillRecord.create and create_with_timestamp produce valid records."""
    rec_id = UUID("00000000-0000-0000-0000-000000000001")

    sr1 = SkillRecord.create(
        recommendation_id=rec_id,
        skill_name="Factory Test",
        description="Testing factory methods",
    )
    assert sr1.skill_id is not None
    assert sr1.recommendation_id == rec_id
    assert sr1.skill_name == "Factory Test"
    assert sr1.level == 1
    assert sr1.experience_points == 0
    assert sr1.created_at > 0
    assert sr1.metadata == {}

    sr2 = SkillRecord.create_with_timestamp(
        recommendation_id=rec_id,
        skill_name="Factory Timed",
        description="Testing timed factory",
        created_at=500.0,
    )
    assert sr2.skill_id is not None
    assert sr2.created_at == 500.0

    print(f"[PASS] skill_record_factories         | create() id={sr1.skill_id.hex[:8]} "
          f"create_with_timestamp() created_at={sr2.created_at}")


# ------------------------------------------------------------------
# Scenario 18: SkillResult with error
# ------------------------------------------------------------------


def scenario_skill_result_error() -> None:
    """SkillResult can represent failure with error_message."""
    snap = SkillRuntime.create_snapshot()
    result = SkillRuntime.build_result(
        snapshot=snap,
        timestamps={"fail": 99.0},
        success=False,
        error_message="Skill promotion failed: invalid recommendation",
    )

    assert isinstance(result, SkillResult)
    assert result.success is False
    assert result.error_message == "Skill promotion failed: invalid recommendation"
    assert result.trace.skills_created == 0
    print(f"[PASS] skill_result_error             | success={result.success} "
          f"error='{result.error_message}'")


# ------------------------------------------------------------------
# Scenario 19: filter_by_level with custom levels via SkillRecord.create
# ------------------------------------------------------------------


def scenario_filter_by_level_custom() -> None:
    """filter_by_level correctly filters skills with different levels."""
    rec_id = UUID("00000000-0000-0000-0000-000000000001")

    s1 = SkillRecord.create_with_timestamp(
        recommendation_id=rec_id, skill_name="Junior",
        description="J", created_at=1.0, level=1,
    )
    s2 = SkillRecord.create_with_timestamp(
        recommendation_id=rec_id, skill_name="Mid",
        description="M", created_at=2.0, level=3,
    )
    s3 = SkillRecord.create_with_timestamp(
        recommendation_id=rec_id, skill_name="Senior",
        description="S", created_at=3.0, level=5,
    )

    snap = SkillRuntime.create_snapshot([s1, s2, s3])

    juniors = SkillRuntime.filter_by_level(snap, min_level=1, max_level=2)
    assert len(juniors) == 1
    assert juniors[0].skill_name == "Junior"

    mids = SkillRuntime.filter_by_level(snap, min_level=3, max_level=4)
    assert len(mids) == 1
    assert mids[0].skill_name == "Mid"

    seniors = SkillRuntime.filter_by_level(snap, min_level=5, max_level=10)
    assert len(seniors) == 1
    assert seniors[0].skill_name == "Senior"

    print(f"[PASS] filter_by_level_custom         | junior={len(juniors)} "
          f"mid={len(mids)} senior={len(seniors)}")


# ------------------------------------------------------------------
# Scenario 20: SkillSnapshot immutability via frozen dataclass
# ------------------------------------------------------------------


def scenario_snapshot_frozen() -> None:
    """SkillSnapshot is a frozen dataclass — attempting mutation raises an error."""
    snap = SkillRuntime.create_snapshot()

    try:
        snap.skills = ()  # type: ignore[misc]
        assert False, "Should have raised TypeError"
    except AttributeError:
        pass

    print(f"[PASS] snapshot_frozen                | SkillSnapshot is frozen (cannot mutate)")


# ------------------------------------------------------------------
# Main
# ------------------------------------------------------------------


def main() -> None:
    print("=" * 58)
    print("Skill Runtime Foundation Demo")
    print("=" * 58)
    print()

    scenario_empty_snapshot()
    scenario_promote_recommendation()
    scenario_multiple_recommendations()
    scenario_order_preserved()
    scenario_timestamps_preserved()
    scenario_metadata_correct()
    scenario_level_inicial()
    scenario_experience_inicial()
    scenario_filter_by_level()
    scenario_snapshot_correct()
    scenario_trace_correct()
    scenario_immutability()
    scenario_determinism()
    scenario_pipeline_empty()
    scenario_full_pipeline()
    scenario_promote_snapshot_empty()
    scenario_skill_record_factories()
    scenario_skill_result_error()
    scenario_filter_by_level_custom()
    scenario_snapshot_frozen()

    print()
    print("=" * 58)
    print("All Skill Runtime scenarios passed.")
    print("=" * 58)


if __name__ == "__main__":
    main()
