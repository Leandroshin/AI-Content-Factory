"""Pipeline demo — Memory Foundation -> Knowledge Foundation.

Validates automatic promotion of MemoryRecords to KnowledgeRecords
via MemoryRuntime.promote_records() and promote_snapshot().
Covers empty snapshots, single/multiple records, order preservation,
metadata, timestamps, confidence, source, determinism, immutability,
trace, full pipeline, and Conversation -> Memory -> Knowledge flow.
"""

from __future__ import annotations

from core.knowledge.foundation import KnowledgeRecord, KnowledgeRuntime as FoundationKR, KnowledgeSnapshot
from core.memory import MemoryRecord, MemoryRuntime, MemorySnapshot


# ------------------------------------------------------------------
# Scenario 1: Empty snapshot produces empty tuple
# ------------------------------------------------------------------


def scenario_empty_snapshot() -> None:
    """Promoting an empty snapshot returns an empty tuple."""
    snapshot = MemoryRuntime.create_snapshot()
    records = MemoryRuntime.promote_records(snapshot)

    assert records == ()
    assert isinstance(records, tuple)
    print(f"[PASS] empty_snapshot                  | records={len(records)}")


# ------------------------------------------------------------------
# Scenario 2: One record promoted
# ------------------------------------------------------------------


def scenario_one_record() -> None:
    """A single MemoryRecord promotes to a single KnowledgeRecord."""
    memory = MemoryRecord.create(source="conversation", category="msg", content="Hello")
    snapshot = MemoryRuntime.create_snapshot([memory])

    records = MemoryRuntime.promote_records(snapshot)

    assert len(records) == 1
    assert isinstance(records[0], KnowledgeRecord)
    assert records[0].content == "Hello"
    print(f"[PASS] one_record                     | knowledge_id={records[0].knowledge_id.hex[:8]} "
          f"content='{records[0].content}'")


# ------------------------------------------------------------------
# Scenario 3: Multiple records promoted
# ------------------------------------------------------------------


def scenario_multiple_records() -> None:
    """Multiple MemoryRecords promote to the same number of KnowledgeRecords."""
    mems = [
        MemoryRecord.create(source="conv", category="msg", content="First"),
        MemoryRecord.create(source="exec", category="result", content="Second"),
        MemoryRecord.create(source="learn", category="pattern", content="Third"),
    ]
    snapshot = MemoryRuntime.create_snapshot(mems)

    records = MemoryRuntime.promote_records(snapshot)

    assert len(records) == 3
    assert records[0].content == "First"
    assert records[1].content == "Second"
    assert records[2].content == "Third"
    print(f"[PASS] multiple_records               | {len(records)} records -> "
          f"contents=[{', '.join(r.content for r in records)}]")


# ------------------------------------------------------------------
# Scenario 4: Order preserved
# ------------------------------------------------------------------


def scenario_order_preserved() -> None:
    """Promoted records maintain the original memory order."""
    mems = [
        MemoryRecord.create_with_timestamp("test", "seq", "A", timestamp=3.0),
        MemoryRecord.create_with_timestamp("test", "seq", "B", timestamp=1.0),
        MemoryRecord.create_with_timestamp("test", "seq", "C", timestamp=2.0),
    ]
    snapshot = MemoryRuntime.create_snapshot(mems)

    records = MemoryRuntime.promote_records(snapshot)

    assert records[0].content == "A"
    assert records[1].content == "B"
    assert records[2].content == "C"
    print(f"[PASS] order_preserved                | memory order preserved -> "
          f"{[r.content for r in records]}")


# ------------------------------------------------------------------
# Scenario 5: Metadata preserved
# ------------------------------------------------------------------


def scenario_metadata_preserved() -> None:
    """MemoryRecord metadata is carried over to the KnowledgeRecord."""
    memory = MemoryRecord.create(
        source="conversation", category="msg", content="With metadata",
        metadata={"session_id": "s-001", "role": "user"},
    )
    snapshot = MemoryRuntime.create_snapshot([memory])

    records = MemoryRuntime.promote_records(snapshot)

    assert records[0].metadata["session_id"] == "s-001"
    assert records[0].metadata["role"] == "user"
    print(f"[PASS] metadata_preserved              | session_id='{records[0].metadata['session_id']}' "
          f"role='{records[0].metadata['role']}'")


# ------------------------------------------------------------------
# Scenario 6: Timestamp on each promoted record
# ------------------------------------------------------------------


def scenario_timestamp_preserved() -> None:
    """Each promoted KnowledgeRecord gets a valid timestamp (> 0)."""
    memory = MemoryRecord.create(source="test", category="info", content="Timed")
    snapshot = MemoryRuntime.create_snapshot([memory])

    records = MemoryRuntime.promote_records(snapshot)

    assert records[0].timestamp > 0
    assert isinstance(records[0].timestamp, float)
    print(f"[PASS] timestamp_preserved             | timestamp={records[0].timestamp:.2f}")


# ------------------------------------------------------------------
# Scenario 7: Confidence = 1.0
# ------------------------------------------------------------------


def scenario_confidence() -> None:
    """All promoted records start with confidence 1.0."""
    mems = [
        MemoryRecord.create(source="a", category="x", content="One"),
        MemoryRecord.create(source="b", category="y", content="Two"),
    ]
    snapshot = MemoryRuntime.create_snapshot(mems)

    records = MemoryRuntime.promote_records(snapshot)

    assert all(r.confidence == 1.0 for r in records)
    print(f"[PASS] confidence                     | all records confidence=1.0"
          f" ({len(records)} records)")


# ------------------------------------------------------------------
# Scenario 8: Source preserved
# ------------------------------------------------------------------


def scenario_source_preserved() -> None:
    """MemoryRecord.source is carried over as KnowledgeRecord.source."""
    memory = MemoryRecord.create(source="execution", category="result", content="Done")
    snapshot = MemoryRuntime.create_snapshot([memory])

    records = MemoryRuntime.promote_records(snapshot)

    assert records[0].source == "execution"
    print(f"[PASS] source_preserved                | source='{records[0].source}'")


# ------------------------------------------------------------------
# Scenario 9: Deterministic promotion
# ------------------------------------------------------------------


def scenario_promotion_deterministic() -> None:
    """Same MemoryRecord promotes to same KnowledgeRecord content."""
    mem = MemoryRecord.create_with_timestamp(
        "test", "cat", "Fixed content", timestamp=1.0,
    )
    snap = MemoryRuntime.create_snapshot([mem])

    r1 = MemoryRuntime.promote_records(snap)
    r2 = MemoryRuntime.promote_records(snap)

    assert r1[0].content == r2[0].content
    assert r1[0].source == r2[0].source
    assert r1[0].confidence == r2[0].confidence
    print(f"[PASS] promotion_deterministic        | content='{r1[0].content}' "
          f"source={r1[0].source} confidence={r1[0].confidence} (identical)")


# ------------------------------------------------------------------
# Scenario 10: promote_snapshot returns correct KnowledgeSnapshot
# ------------------------------------------------------------------


def scenario_promote_snapshot_correct() -> None:
    """promote_snapshot wraps promoted records in a KnowledgeSnapshot."""
    mems = [
        MemoryRecord.create(source="conv", category="msg", content="Q"),
        MemoryRecord.create(source="conv", category="msg", content="A"),
    ]
    mem_snap = MemoryRuntime.create_snapshot(mems)

    know_snap = MemoryRuntime.promote_snapshot(mem_snap)

    assert isinstance(know_snap, KnowledgeSnapshot)
    assert len(know_snap.records) == 2
    assert know_snap.records[0].content == "Q"
    assert know_snap.records[1].content == "A"
    assert know_snap.created_at > 0
    print(f"[PASS] promote_snapshot_correct       | {len(know_snap.records)} records "
          f"in KnowledgeSnapshot, created_at={know_snap.created_at:.2f}")


# ------------------------------------------------------------------
# Scenario 11: Immutability
# ------------------------------------------------------------------


def scenario_immutability() -> None:
    """Original memory snapshot is never mutated by promotion."""
    mem = MemoryRecord.create(source="test", category="x", content="Immutable")
    original = MemoryRuntime.create_snapshot([mem])

    _ = MemoryRuntime.promote_records(original)

    assert len(original.records) == 1
    assert original.records[0].content == "Immutable"
    print(f"[PASS] immutability                   | original untouched "
          f"(records={len(original.records)})")


# ------------------------------------------------------------------
# Scenario 12: Trace correctness via MemoryRuntime.build_result
# ------------------------------------------------------------------


def scenario_trace_correct() -> None:
    """MemoryResult trace works before and after promotion."""
    mem = MemoryRecord.create(source="test", category="x", content="Trace")
    snap = MemoryRuntime.create_snapshot([mem])

    result = MemoryRuntime.build_result(
        snapshot=snap,
        operations=["create_snapshot", "promote_records"],
        timestamps={"start": 1.0, "end": 2.0},
    )

    assert result.success is True
    assert result.trace.operations == ["create_snapshot", "promote_records"]
    assert result.trace.records_created == 1
    assert result.error_message == ""
    print(f"[PASS] trace_correct                  | ops={result.trace.operations} "
          f"records_created={result.trace.records_created}")


# ------------------------------------------------------------------
# Scenario 13: Full pipeline — empty KnowledgeSnapshot from empty MemorySnapshot
# ------------------------------------------------------------------


def scenario_pipeline_empty() -> None:
    """Empty MemorySnapshot promotes to empty KnowledgeSnapshot."""
    mem_snap = MemoryRuntime.create_snapshot()

    know_snap = MemoryRuntime.promote_snapshot(mem_snap)

    assert len(know_snap.records) == 0
    print(f"[PASS] pipeline_empty                 | empty MemorySnapshot -> "
          f"empty KnowledgeSnapshot ({len(know_snap.records)} records)")


# ------------------------------------------------------------------
# Scenario 14: Conversation -> Memory -> Knowledge pipeline
# ------------------------------------------------------------------


def scenario_conversation_memory_knowledge() -> None:
    """Simulate the complete Conversation -> Memory -> Knowledge flow."""
    from core.conversation import ConversationRuntime

    session = ConversationRuntime.create_session("emp-001")
    session = ConversationRuntime.append_message(session, "user", "What is AI?")
    session = ConversationRuntime.append_message(session, "assistant", "AI stands for Artificial Intelligence.")
    session = ConversationRuntime.append_message(session, "user", "What is ML?")
    session = ConversationRuntime.append_message(session, "assistant", "ML is Machine Learning.")

    # Conversation -> Memory
    memory_records = []
    for msg in session.messages:
        mem = ConversationRuntime.create_memory_record(session, msg)
        memory_records.append(mem)

    assert len(memory_records) == 4
    memory_snapshot = MemoryRuntime.create_snapshot(memory_records)

    # Memory -> Knowledge (promote_records)
    knowledge_records = MemoryRuntime.promote_records(memory_snapshot)

    assert len(knowledge_records) == 4
    assert knowledge_records[0].content == "What is AI?"
    assert knowledge_records[1].content == "AI stands for Artificial Intelligence."
    assert knowledge_records[2].content == "What is ML?"
    assert knowledge_records[3].content == "ML is Machine Learning."
    assert all(k.source == "conversation" for k in knowledge_records)
    assert all(k.confidence == 1.0 for k in knowledge_records)
    assert all(k.title == "Memory Promotion" for k in knowledge_records)

    # Memory -> Knowledge (promote_snapshot)
    knowledge_snapshot = MemoryRuntime.promote_snapshot(memory_snapshot)
    assert len(knowledge_snapshot.records) == 4

    # Filter the knowledge snapshot
    from_conv = FoundationKR.filter_by_source(knowledge_snapshot, "conversation")
    assert len(from_conv) == 4

    print(f"[PASS] conversation_memory_knowledge  | {len(session.messages)} msgs -> "
          f"{len(memory_records)} memory -> "
          f"{len(knowledge_records)} knowledge (source={from_conv[0].source})")


# ------------------------------------------------------------------
# Scenario 15: Total determinism
# ------------------------------------------------------------------


def scenario_total_determinism() -> None:
    """Same memory pipeline produces identical knowledge output."""
    mems = [
        MemoryRecord.create_with_timestamp("test", "cat", "Det A", timestamp=1.0),
        MemoryRecord.create_with_timestamp("test", "cat", "Det B", timestamp=2.0),
    ]
    snap = MemoryRuntime.create_snapshot(mems)

    r1 = MemoryRuntime.promote_records(snap)
    r2 = MemoryRuntime.promote_records(snap)

    assert len(r1) == len(r2)
    assert r1[0].content == r2[0].content
    assert r1[0].source == r2[0].source
    assert r1[0].confidence == r2[0].confidence
    assert r1[0].title == r2[0].title
    assert r1[1].content == r2[1].content

    ks1 = MemoryRuntime.promote_snapshot(snap)
    ks2 = MemoryRuntime.promote_snapshot(snap)
    assert len(ks1.records) == len(ks2.records)
    assert ks1.records[0].content == ks2.records[0].content
    print(f"[PASS] total_determinism              | promote_records and "
          f"promote_snapshot both deterministic "
          f"(records={len(r1)}, snapshot_records={len(ks1.records)})")


# ------------------------------------------------------------------
# Main
# ------------------------------------------------------------------


def main() -> None:
    print("=" * 62)
    print("Memory -> Knowledge Pipeline Demo")
    print("=" * 62)
    print()

    scenario_empty_snapshot()
    scenario_one_record()
    scenario_multiple_records()
    scenario_order_preserved()
    scenario_metadata_preserved()
    scenario_timestamp_preserved()
    scenario_confidence()
    scenario_source_preserved()
    scenario_promotion_deterministic()
    scenario_promote_snapshot_correct()
    scenario_immutability()
    scenario_trace_correct()
    scenario_pipeline_empty()
    scenario_conversation_memory_knowledge()
    scenario_total_determinism()

    print()
    print("=" * 62)
    print("All Memory -> Knowledge pipeline scenarios passed.")
    print("=" * 62)


if __name__ == "__main__":
    main()
