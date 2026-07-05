"""Foundation demo for the Knowledge Runtime — no external dependencies.

Validates KnowledgeRecord creation, snapshot management, MemoryRecord
promotion, filtering by source and confidence, immutability, ordering,
trace, determinism, and simulated Memory -> Knowledge integration.
"""

from __future__ import annotations

from uuid import UUID

from core.knowledge.foundation import (
    KnowledgeRecord,
    KnowledgeResult,
    KnowledgeRuntime,
    KnowledgeSnapshot,
    KnowledgeTrace,
)
from core.memory import MemoryRecord


# ------------------------------------------------------------------
# Scenario 1: Empty snapshot
# ------------------------------------------------------------------


def scenario_empty_snapshot() -> None:
    """A newly created snapshot has no records."""
    snapshot = KnowledgeRuntime.create_snapshot()

    assert isinstance(snapshot, KnowledgeSnapshot)
    assert snapshot.records == ()
    assert snapshot.created_at > 0
    print(f"[PASS] empty_snapshot                  | records={len(snapshot.records)} "
          f"created_at={snapshot.created_at:.2f}")


# ------------------------------------------------------------------
# Scenario 2: Promote MemoryRecord to KnowledgeRecord
# ------------------------------------------------------------------


def scenario_promote_memory_record() -> None:
    """A MemoryRecord is promoted to a KnowledgeRecord deterministically."""
    memory = MemoryRecord.create(
        source="conversation",
        category="conversation_message",
        content="AI is transforming industries.",
        metadata={"session_id": "abc-123", "role": "assistant"},
    )

    knowledge = KnowledgeRuntime.promote_memory_record(memory)

    assert isinstance(knowledge, KnowledgeRecord)
    assert knowledge.source == "conversation"
    assert knowledge.title == "Memory Promotion"
    assert knowledge.content == "AI is transforming industries."
    assert knowledge.confidence == 1.0
    assert knowledge.metadata["session_id"] == "abc-123"
    assert knowledge.metadata["role"] == "assistant"
    print(f"[PASS] promote_memory_record          | knowledge_id={knowledge.knowledge_id.hex[:8]} "
          f"source='{knowledge.source}' title='{knowledge.title}' "
          f"confidence={knowledge.confidence}")


# ------------------------------------------------------------------
# Scenario 3: Add KnowledgeRecord to snapshot
# ------------------------------------------------------------------


def scenario_add_knowledge_record() -> None:
    """Appending a KnowledgeRecord adds it to the snapshot."""
    snapshot = KnowledgeRuntime.create_snapshot()
    record = KnowledgeRecord.create(
        source="manual", title="Test Entry", content="Some knowledge.",
    )

    updated = KnowledgeRuntime.append_record(snapshot, record)

    assert len(updated.records) == 1
    assert updated.records[0].title == "Test Entry"
    assert updated.records[0].content == "Some knowledge."
    assert isinstance(updated.records[0].knowledge_id, UUID)
    print(f"[PASS] add_knowledge_record           | count={len(updated.records)} "
          f"title='{updated.records[0].title}'")


# ------------------------------------------------------------------
# Scenario 4: Multiple records
# ------------------------------------------------------------------


def scenario_multiple_records() -> None:
    """Multiple appends produce an ordered sequence."""
    snapshot = KnowledgeRuntime.create_snapshot()

    records = [
        KnowledgeRecord.create_with_timestamp("conv", "A", "First", timestamp=1.0),
        KnowledgeRecord.create_with_timestamp("exec", "B", "Second", timestamp=2.0),
        KnowledgeRecord.create_with_timestamp("learn", "C", "Third", timestamp=3.0),
    ]
    for rec in records:
        snapshot = KnowledgeRuntime.append_record(snapshot, rec)

    assert len(snapshot.records) == 3
    assert snapshot.records[0].content == "First"
    assert snapshot.records[1].content == "Second"
    assert snapshot.records[2].content == "Third"
    print(f"[PASS] multiple_records               | count={len(snapshot.records)} "
          f"titles=[{', '.join(r.title for r in snapshot.records)}]")


# ------------------------------------------------------------------
# Scenario 5: Filter by source
# ------------------------------------------------------------------


def scenario_filter_by_source() -> None:
    """filter_by_source returns only records with the matching source."""
    snapshot = KnowledgeRuntime.create_snapshot()

    sources = ["conv", "exec", "conv", "learn", "conv"]
    for i, src in enumerate(sources):
        rec = KnowledgeRecord.create_with_timestamp(src, f"R{i}", f"Content {i}", timestamp=float(i))
        snapshot = KnowledgeRuntime.append_record(snapshot, rec)

    conv = KnowledgeRuntime.filter_by_source(snapshot, "conv")
    exec_ = KnowledgeRuntime.filter_by_source(snapshot, "exec")
    learn = KnowledgeRuntime.filter_by_source(snapshot, "learn")

    assert len(conv) == 3
    assert len(exec_) == 1
    assert len(learn) == 1
    assert all(r.source == "conv" for r in conv)
    print(f"[PASS] filter_by_source               | conv={len(conv)} exec={len(exec_)} "
          f"learn={len(learn)}")


# ------------------------------------------------------------------
# Scenario 6: Filter by confidence
# ------------------------------------------------------------------


def scenario_filter_by_confidence() -> None:
    """filter_by_confidence returns records within the confidence range."""
    snapshot = KnowledgeRuntime.create_snapshot()

    confs = [0.5, 0.8, 1.0, 0.6, 0.95]
    for i, c in enumerate(confs):
        rec = KnowledgeRecord.create_with_timestamp(
            "test", f"R{i}", f"C{i}", timestamp=float(i), confidence=c,
        )
        snapshot = KnowledgeRuntime.append_record(snapshot, rec)

    high = KnowledgeRuntime.filter_by_confidence(snapshot, min_confidence=0.9)
    mid = KnowledgeRuntime.filter_by_confidence(snapshot, min_confidence=0.6, max_confidence=0.85)
    low = KnowledgeRuntime.filter_by_confidence(snapshot, max_confidence=0.55)

    assert len(high) == 2
    assert len(mid) == 2
    assert len(low) == 1
    assert all(r.confidence >= 0.9 for r in high)
    print(f"[PASS] filter_by_confidence            | high(>=0.9)={len(high)} "
          f"mid(0.6-0.85)={len(mid)} low(<=0.55)={len(low)}")


# ------------------------------------------------------------------
# Scenario 7: Metadata preserved
# ------------------------------------------------------------------


def scenario_metadata_preserved() -> None:
    """Record metadata is preserved during promotion and creation."""
    memory = MemoryRecord.create(
        source="execution",
        category="result",
        content="Task completed.",
        metadata={"task_id": "t-001", "employee": "Alice"},
    )

    knowledge = KnowledgeRuntime.promote_memory_record(memory)

    assert knowledge.metadata["task_id"] == "t-001"
    assert knowledge.metadata["employee"] == "Alice"

    direct = KnowledgeRecord.create(
        source="manual", title="Direct", content="Direct entry",
        metadata={"key": "value"},
    )
    assert direct.metadata["key"] == "value"
    print(f"[PASS] metadata_preserved              | task_id='{knowledge.metadata['task_id']}' "
          f"employee='{knowledge.metadata['employee']}'")


# ------------------------------------------------------------------
# Scenario 8: Timestamp preserved on promotion
# ------------------------------------------------------------------


def scenario_timestamp_preserved() -> None:
    """The KnowledgeRecord gets its own creation timestamp."""
    memory = MemoryRecord.create(source="test", category="info", content="Timed")
    knowledge = KnowledgeRuntime.promote_memory_record(memory)

    assert knowledge.timestamp > 0
    assert isinstance(knowledge.timestamp, float)
    print(f"[PASS] timestamp_preserved             | timestamp={knowledge.timestamp:.2f} "
          f"(> 0)")


# ------------------------------------------------------------------
# Scenario 9: Order preserved
# ------------------------------------------------------------------


def scenario_order_preserved() -> None:
    """Records maintain the order they were appended."""
    snapshot = KnowledgeRuntime.create_snapshot()

    for i in range(5):
        rec = KnowledgeRecord.create_with_timestamp(
            "test", f"Item-{i}", f"Content-{i}", timestamp=float(i),
        )
        snapshot = KnowledgeRuntime.append_record(snapshot, rec)

    titles = [r.title for r in snapshot.records]
    assert titles == ["Item-0", "Item-1", "Item-2", "Item-3", "Item-4"]
    print(f"[PASS] order_preserved                | titles={titles}")


# ------------------------------------------------------------------
# Scenario 10: Immutability
# ------------------------------------------------------------------


def scenario_immutability() -> None:
    """The original snapshot is never mutated by append_record."""
    original = KnowledgeRuntime.create_snapshot()
    record = KnowledgeRecord.create(source="test", title="T", content="C")

    _ = KnowledgeRuntime.append_record(original, record)

    assert len(original.records) == 0
    print(f"[PASS] immutability                   | original untouched "
          f"(records={len(original.records)})")


# ------------------------------------------------------------------
# Scenario 11: Trace populated in build_result
# ------------------------------------------------------------------


def scenario_trace() -> None:
    """KnowledgeResult contains snapshot, trace, and stats."""
    snapshot = KnowledgeRuntime.create_snapshot()
    record = KnowledgeRecord.create(source="test", title="Trace", content="Trace test")
    snapshot = KnowledgeRuntime.append_record(snapshot, record)

    result = KnowledgeRuntime.build_result(
        snapshot=snapshot,
        operations=["create_snapshot", "append_record"],
        timestamps={"start": 100.0, "end": 101.0},
    )

    assert isinstance(result, KnowledgeResult)
    assert result.success is True
    assert result.trace.operations == ["create_snapshot", "append_record"]
    assert result.trace.timestamps["start"] == 100.0
    assert result.trace.promoted_records == 1
    assert result.error_message == ""
    print(f"[PASS] trace                          | success={result.success} "
          f"ops={result.trace.operations} "
          f"promoted={result.trace.promoted_records}")


# ------------------------------------------------------------------
# Scenario 12: Determinism
# ------------------------------------------------------------------


def scenario_determinism() -> None:
    """Identical inputs produce identical record content."""
    rec = KnowledgeRecord.create_with_timestamp("test", "Same", "Same content", timestamp=1.0, confidence=0.8)
    rec2 = KnowledgeRecord.create_with_timestamp("test", "Same", "Same content", timestamp=1.0, confidence=0.8)

    assert rec.source == rec2.source
    assert rec.title == rec2.title
    assert rec.content == rec2.content
    assert rec.confidence == rec2.confidence
    print(f"[PASS] determinism                    | source={rec.source} "
          f"title='{rec.title}' confidence={rec.confidence} (identical)")


# ------------------------------------------------------------------
# Scenario 13: Simulated Memory -> Knowledge integration
# ------------------------------------------------------------------


def scenario_memory_to_knowledge() -> None:
    """Full pipeline: MemoryRecords promoted to KnowledgeRecords in a snapshot."""
    memory_records = [
        MemoryRecord.create(source="conversation", category="message", content="What is AI?"),
        MemoryRecord.create(source="conversation", category="message", content="AI is Artificial Intelligence."),
        MemoryRecord.create(source="execution", category="result", content="Task generated successfully."),
    ]

    knowledge_records = []
    for mem in memory_records:
        kr = KnowledgeRuntime.promote_memory_record(mem)
        knowledge_records.append(kr)

    snapshot = KnowledgeRuntime.create_snapshot(knowledge_records)

    assert len(snapshot.records) == 3

    conv = KnowledgeRuntime.filter_by_source(snapshot, "conversation")
    exec_ = KnowledgeRuntime.filter_by_source(snapshot, "execution")

    assert len(conv) == 2
    assert len(exec_) == 1
    assert all(r.title == "Memory Promotion" for r in snapshot.records)

    print(f"[PASS] memory_to_knowledge            | {len(memory_records)} memory records -> "
          f"{len(snapshot.records)} knowledge records "
          f"(conv={len(conv)}, exec={len(exec_)})")


# ------------------------------------------------------------------
# Main
# ------------------------------------------------------------------


def main() -> None:
    print("=" * 60)
    print("Knowledge Runtime Foundation Demo")
    print("=" * 60)
    print()

    scenario_empty_snapshot()
    scenario_promote_memory_record()
    scenario_add_knowledge_record()
    scenario_multiple_records()
    scenario_filter_by_source()
    scenario_filter_by_confidence()
    scenario_metadata_preserved()
    scenario_timestamp_preserved()
    scenario_order_preserved()
    scenario_immutability()
    scenario_trace()
    scenario_determinism()
    scenario_memory_to_knowledge()

    print()
    print("=" * 60)
    print("All Knowledge Runtime scenarios passed.")
    print("=" * 60)


if __name__ == "__main__":
    main()
