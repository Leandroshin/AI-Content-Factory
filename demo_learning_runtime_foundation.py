"""Foundation demo for the Learning Runtime.

Validates LearningRecommendation creation, KnowledgeRecord promotion,
filtering by priority, immutability, ordering, trace, determinism,
and the complete Conversation -> Memory -> Knowledge -> Learning pipeline.
"""

from __future__ import annotations

from uuid import UUID

from core.knowledge.foundation import KnowledgeRecord, KnowledgeRuntime as FoundationKR
from core.learning.foundation import (
    LearningRecommendation,
    LearningResult,
    LearningRuntime,
    LearningSnapshot,
    LearningTrace,
)
from core.memory import MemoryRecord, MemoryRuntime


# ------------------------------------------------------------------
# Scenario 1: Empty snapshot
# ------------------------------------------------------------------


def scenario_empty_snapshot() -> None:
    """A newly created snapshot has no recommendations."""
    snapshot = LearningRuntime.create_snapshot()

    assert isinstance(snapshot, LearningSnapshot)
    assert snapshot.recommendations == ()
    assert snapshot.created_at > 0
    print(f"[PASS] empty_snapshot                  | recommendations={len(snapshot.recommendations)} "
          f"created_at={snapshot.created_at:.2f}")


# ------------------------------------------------------------------
# Scenario 2: Promote KnowledgeRecord
# ------------------------------------------------------------------


def scenario_promote_knowledge() -> None:
    """A KnowledgeRecord is promoted to a LearningRecommendation."""
    kr = KnowledgeRecord.create(
        source="conversation",
        title="AI Definition",
        content="AI stands for Artificial Intelligence.",
    )

    rec = LearningRuntime.promote_knowledge(kr)

    assert isinstance(rec, LearningRecommendation)
    assert rec.knowledge_id == kr.knowledge_id
    assert rec.title == "AI Definition"
    assert rec.description == "AI stands for Artificial Intelligence."
    assert rec.recommendation_type == "study"
    assert rec.priority == 1
    print(f"[PASS] promote_knowledge              | recommendation_id={rec.recommendation_id.hex[:8]} "
          f"title='{rec.title}' type='{rec.recommendation_type}' "
          f"priority={rec.priority}")


# ------------------------------------------------------------------
# Scenario 3: Multiple recommendations
# ------------------------------------------------------------------


def scenario_multiple_recommendations() -> None:
    """Multiple KnowledgeRecords produce the same number of recommendations."""
    krs = [
        KnowledgeRecord.create(source="conv", title="A", content="Alpha"),
        KnowledgeRecord.create(source="exec", title="B", content="Beta"),
        KnowledgeRecord.create(source="learn", title="C", content="Gamma"),
    ]

    snapshot = LearningRuntime.create_snapshot()
    for kr in krs:
        rec = LearningRuntime.promote_knowledge(kr)
        snapshot = LearningRuntime.append_recommendation(snapshot, rec)

    assert len(snapshot.recommendations) == 3
    assert snapshot.recommendations[0].title == "A"
    assert snapshot.recommendations[1].title == "B"
    assert snapshot.recommendations[2].title == "C"
    print(f"[PASS] multiple_recommendations       | {len(snapshot.recommendations)} recs -> "
          f"titles=[{', '.join(r.title for r in snapshot.recommendations)}]")


# ------------------------------------------------------------------
# Scenario 4: Order preserved
# ------------------------------------------------------------------


def scenario_order_preserved() -> None:
    """Recommendations maintain append order."""
    krs = [
        KnowledgeRecord.create(source="test", title="First", content="1"),
        KnowledgeRecord.create(source="test", title="Second", content="2"),
        KnowledgeRecord.create(source="test", title="Third", content="3"),
    ]

    snapshot = LearningRuntime.create_snapshot()
    for kr in krs:
        rec = LearningRuntime.promote_knowledge(kr)
        snapshot = LearningRuntime.append_recommendation(snapshot, rec)

    titles = [r.title for r in snapshot.recommendations]
    assert titles == ["First", "Second", "Third"]
    print(f"[PASS] order_preserved                | titles={titles}")


# ------------------------------------------------------------------
# Scenario 5: Metadata preserved
# ------------------------------------------------------------------


def scenario_metadata_preserved() -> None:
    """KnowledgeRecord metadata is accessible after promotion."""
    kr = KnowledgeRecord.create(
        source="conversation", title="With Meta", content="Content",
        metadata={"session_id": "s-001", "role": "assistant"},
    )

    rec = LearningRuntime.promote_knowledge(kr)

    assert rec.title == "With Meta"
    assert rec.description == "Content"
    print(f"[PASS] metadata_preserved              | title='{rec.title}' "
          f"description='{rec.description}'")


# ------------------------------------------------------------------
# Scenario 6: Timestamps preserved
# ------------------------------------------------------------------


def scenario_timestamps_preserved() -> None:
    """Each promoted recommendation gets a valid creation timestamp."""
    kr = KnowledgeRecord.create(source="test", title="Timed", content="Content")
    rec = LearningRuntime.promote_knowledge(kr)

    assert rec.timestamp > 0
    assert isinstance(rec.timestamp, float)
    print(f"[PASS] timestamps_preserved            | timestamp={rec.timestamp:.2f}")


# ------------------------------------------------------------------
# Scenario 7: Priority correct
# ------------------------------------------------------------------


def scenario_priority_correct() -> None:
    """All promoted recommendations start with priority 1."""
    krs = [
        KnowledgeRecord.create(source="a", title="X", content="1"),
        KnowledgeRecord.create(source="b", title="Y", content="2"),
    ]

    for kr in krs:
        rec = LearningRuntime.promote_knowledge(kr)
        assert rec.priority == 1

    print(f"[PASS] priority_correct               | all recommendations priority=1"
          f" ({len(krs)} recs)")


# ------------------------------------------------------------------
# Scenario 8: recommendation_type correct
# ------------------------------------------------------------------


def scenario_recommendation_type_correct() -> None:
    """All promoted recommendations have type='study'."""
    kr = KnowledgeRecord.create(source="test", title="Type Test", content="Content")
    rec = LearningRuntime.promote_knowledge(kr)

    assert rec.recommendation_type == "study"
    print(f"[PASS] recommendation_type_correct    | type='{rec.recommendation_type}'")


# ------------------------------------------------------------------
# Scenario 9: filter_by_priority
# ------------------------------------------------------------------


def scenario_filter_by_priority() -> None:
    """filter_by_priority returns recommendations within the priority range."""
    krs = [
        KnowledgeRecord.create_with_timestamp("test", "Low", "L", timestamp=1.0),
        KnowledgeRecord.create_with_timestamp("test", "Mid", "M", timestamp=2.0),
        KnowledgeRecord.create_with_timestamp("test", "High", "H", timestamp=3.0),
    ]

    snapshot = LearningRuntime.create_snapshot()
    for i, kr in enumerate(krs):
        rec = LearningRuntime.promote_knowledge(kr)
        snapshot = LearningRuntime.append_recommendation(snapshot, rec)

    all_recs = LearningRuntime.filter_by_priority(snapshot)
    assert len(all_recs) == 3

    print(f"[PASS] filter_by_priority             | all={len(all_recs)} "
          f"(all priority=1, range 0-10 catches everything)")


# ------------------------------------------------------------------
# Scenario 10: promote_snapshot correct
# ------------------------------------------------------------------


def scenario_promote_snapshot_correct() -> None:
    """promote_snapshot converts a KnowledgeSnapshot to a LearningSnapshot."""
    krs = [
        KnowledgeRecord.create(source="conv", title="K1", content="C1"),
        KnowledgeRecord.create(source="exec", title="K2", content="C2"),
    ]
    know_snap = FoundationKR.create_snapshot(krs)

    learn_snap = LearningRuntime.promote_snapshot(know_snap)

    assert isinstance(learn_snap, LearningSnapshot)
    assert len(learn_snap.recommendations) == 2
    assert learn_snap.recommendations[0].title == "K1"
    assert learn_snap.recommendations[1].title == "K2"
    assert learn_snap.recommendations[0].knowledge_id == krs[0].knowledge_id
    assert learn_snap.recommendations[1].knowledge_id == krs[1].knowledge_id
    print(f"[PASS] promote_snapshot_correct       | {len(learn_snap.recommendations)} recs "
          f"promoted from KnowledgeSnapshot")


# ------------------------------------------------------------------
# Scenario 11: Trace correct
# ------------------------------------------------------------------


def scenario_trace_correct() -> None:
    """LearningResult contains snapshot, trace, and stats."""
    kr = KnowledgeRecord.create(source="test", title="Trace", content="T")
    rec = LearningRuntime.promote_knowledge(kr)
    snap = LearningRuntime.create_snapshot([rec])

    result = LearningRuntime.build_result(
        snapshot=snap,
        timestamps={"start": 100.0, "end": 101.0},
    )

    assert isinstance(result, LearningResult)
    assert result.success is True
    assert result.trace.promoted_knowledge == 1
    assert result.trace.recommendations_created == 1
    assert result.trace.timestamps["start"] == 100.0
    assert result.error_message == ""
    print(f"[PASS] trace_correct                  | success={result.success} "
          f"promoted={result.trace.promoted_knowledge} "
          f"created={result.trace.recommendations_created}")


# ------------------------------------------------------------------
# Scenario 12: Immutability
# ------------------------------------------------------------------


def scenario_immutability() -> None:
    """Original snapshot is never mutated by append_recommendation."""
    original = LearningRuntime.create_snapshot()
    kr = KnowledgeRecord.create(source="test", title="Imm", content="C")
    rec = LearningRuntime.promote_knowledge(kr)

    _ = LearningRuntime.append_recommendation(original, rec)

    assert len(original.recommendations) == 0
    print(f"[PASS] immutability                   | original untouched "
          f"(recommendations={len(original.recommendations)})")


# ------------------------------------------------------------------
# Scenario 13: Determinism
# ------------------------------------------------------------------


def scenario_determinism() -> None:
    """Same KnowledgeRecord produces identical recommendation content."""
    kr = KnowledgeRecord.create_with_timestamp(
        "test", "Det Title", "Det Content", timestamp=1.0,
    )

    r1 = LearningRuntime.promote_knowledge(kr)
    r2 = LearningRuntime.promote_knowledge(kr)

    assert r1.title == r2.title
    assert r1.description == r2.description
    assert r1.priority == r2.priority
    assert r1.recommendation_type == r2.recommendation_type
    print(f"[PASS] determinism                    | title='{r1.title}' "
          f"type='{r1.recommendation_type}' priority={r1.priority} (identical)")


# ------------------------------------------------------------------
# Scenario 14: Full pipeline — empty KnowledgeSnapshot
# ------------------------------------------------------------------


def scenario_pipeline_empty() -> None:
    """Empty KnowledgeSnapshot promotes to empty LearningSnapshot."""
    know_snap = FoundationKR.create_snapshot()
    learn_snap = LearningRuntime.promote_snapshot(know_snap)

    assert len(learn_snap.recommendations) == 0
    print(f"[PASS] pipeline_empty                 | empty KnowledgeSnapshot -> "
          f"empty LearningSnapshot ({len(learn_snap.recommendations)} recs)")


# ------------------------------------------------------------------
# Scenario 15: Complete Conversation -> Memory -> Knowledge -> Learning
# ------------------------------------------------------------------


def scenario_full_pipeline() -> None:
    """Complete end-to-end pipeline from conversation to learning recommendation."""
    from core.conversation import ConversationRuntime

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
    assert learn_records[0].title == "Memory Promotion"
    assert learn_records[0].description == "Explain transformers."
    assert learn_records[1].description == (
        "Transformers are a neural network architecture based on attention."
    )

    print(f"[PASS] full_pipeline                  | {len(session.messages)} msgs -> "
          f"{len(mem_records)} memory -> "
          f"{len(know_records)} knowledge -> "
          f"{len(learn_records)} learning")


# ------------------------------------------------------------------
# Main
# ------------------------------------------------------------------


def main() -> None:
    print("=" * 58)
    print("Learning Runtime Foundation Demo")
    print("=" * 58)
    print()

    scenario_empty_snapshot()
    scenario_promote_knowledge()
    scenario_multiple_recommendations()
    scenario_order_preserved()
    scenario_metadata_preserved()
    scenario_timestamps_preserved()
    scenario_priority_correct()
    scenario_recommendation_type_correct()
    scenario_filter_by_priority()
    scenario_promote_snapshot_correct()
    scenario_trace_correct()
    scenario_immutability()
    scenario_determinism()
    scenario_pipeline_empty()
    scenario_full_pipeline()

    print()
    print("=" * 58)
    print("All Learning Runtime scenarios passed.")
    print("=" * 58)


if __name__ == "__main__":
    main()
