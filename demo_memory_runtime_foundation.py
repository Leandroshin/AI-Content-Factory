"""Foundation demo for the Memory Runtime — no external dependencies.

Validates snapshot creation, record appending, filtering by category
and source, immutability, ordering, metadata, timestamps, trace,
determinism, and simulated integration with Conversation.
"""

from __future__ import annotations

from uuid import UUID

from core.memory import (
    MemoryRecord,
    MemoryResult,
    MemoryRuntime,
    MemorySnapshot,
    MemoryTrace,
)


# ------------------------------------------------------------------
# Scenario 1: Empty snapshot
# ------------------------------------------------------------------


def scenario_empty_snapshot() -> None:
    """A newly created snapshot has no records."""
    snapshot = MemoryRuntime.create_snapshot()

    assert isinstance(snapshot, MemorySnapshot)
    assert snapshot.records == ()
    assert snapshot.created_at > 0
    print(f"[PASS] empty_snapshot                  | records={len(snapshot.records)} "
          f"created_at={snapshot.created_at:.2f}")


# ------------------------------------------------------------------
# Scenario 2: Add a record
# ------------------------------------------------------------------


def scenario_add_record() -> None:
    """Appending a record adds it to the snapshot."""
    snapshot = MemoryRuntime.create_snapshot()
    record = MemoryRecord.create(source="test", category="info", content="Hello")

    updated = MemoryRuntime.append_record(snapshot, record)

    assert len(updated.records) == 1
    assert updated.records[0].content == "Hello"
    assert updated.records[0].source == "test"
    assert updated.records[0].category == "info"
    assert isinstance(updated.records[0].memory_id, UUID)
    print(f"[PASS] add_record                     | count={len(updated.records)} "
          f"source='{updated.records[0].source}' category='{updated.records[0].category}'")


# ------------------------------------------------------------------
# Scenario 3: Multiple records
# ------------------------------------------------------------------


def scenario_multiple_records() -> None:
    """Multiple appends produce an ordered sequence of records."""
    snapshot = MemoryRuntime.create_snapshot()

    records = [
        MemoryRecord.create_with_timestamp("conv", "message", "First", timestamp=1.0),
        MemoryRecord.create_with_timestamp("exec", "result", "Second", timestamp=2.0),
        MemoryRecord.create_with_timestamp("decision", "choice", "Third", timestamp=3.0),
    ]
    for rec in records:
        snapshot = MemoryRuntime.append_record(snapshot, rec)

    assert len(snapshot.records) == 3
    assert snapshot.records[0].content == "First"
    assert snapshot.records[1].content == "Second"
    assert snapshot.records[2].content == "Third"
    print(f"[PASS] multiple_records               | count={len(snapshot.records)} "
          f"contents=[{', '.join(r.content for r in snapshot.records)}]")


# ------------------------------------------------------------------
# Scenario 4: Filter by category
# ------------------------------------------------------------------


def scenario_filter_by_category() -> None:
    """filter_by_category returns only records with the matching category."""
    snapshot = MemoryRuntime.create_snapshot()

    for cat, text in [("info", "A"), ("error", "B"), ("info", "C"), ("debug", "D"), ("info", "E")]:
        rec =         MemoryRecord.create_with_timestamp("sys", cat, text, timestamp=1.0)
        snapshot = MemoryRuntime.append_record(snapshot, rec)

    info_records = MemoryRuntime.filter_by_category(snapshot, "info")
    error_records = MemoryRuntime.filter_by_category(snapshot, "error")
    debug_records = MemoryRuntime.filter_by_category(snapshot, "debug")

    assert len(info_records) == 3
    assert len(error_records) == 1
    assert len(debug_records) == 1
    assert all(r.category == "info" for r in info_records)
    assert info_records[0].content == "A"
    assert info_records[1].content == "C"
    assert info_records[2].content == "E"
    print(f"[PASS] filter_by_category             | info={len(info_records)} "
          f"error={len(error_records)} debug={len(debug_records)}")


# ------------------------------------------------------------------
# Scenario 5: Filter by source
# ------------------------------------------------------------------


def scenario_filter_by_source() -> None:
    """filter_by_source returns only records with the matching source."""
    snapshot = MemoryRuntime.create_snapshot()

    recs = [
        MemoryRecord.create_with_timestamp("conversation", "msg", "Hi", timestamp=1.0),
        MemoryRecord.create_with_timestamp("execution", "result", "Done", timestamp=2.0),
        MemoryRecord.create_with_timestamp("conversation", "msg", "Bye", timestamp=3.0),
        MemoryRecord.create_with_timestamp("decision", "choice", "Alice", timestamp=4.0),
    ]
    for rec in recs:
        snapshot = MemoryRuntime.append_record(snapshot, rec)

    conv = MemoryRuntime.filter_by_source(snapshot, "conversation")
    exec_ = MemoryRuntime.filter_by_source(snapshot, "execution")
    dec_ = MemoryRuntime.filter_by_source(snapshot, "decision")

    assert len(conv) == 2
    assert len(exec_) == 1
    assert len(dec_) == 1
    assert all(r.source == "conversation" for r in conv)
    print(f"[PASS] filter_by_source               | conversation={len(conv)} "
          f"execution={len(exec_)} decision={len(dec_)}")


# ------------------------------------------------------------------
# Scenario 6: Immutability — original snapshot unchanged
# ------------------------------------------------------------------


def scenario_immutability() -> None:
    """The original snapshot is never mutated by append_record."""
    original = MemoryRuntime.create_snapshot()
    record = MemoryRecord.create(source="test", category="info", content="Hello")

    _ = MemoryRuntime.append_record(original, record)

    assert len(original.records) == 0
    print(f"[PASS] immutability                   | original untouched "
          f"(records={len(original.records)})")


# ------------------------------------------------------------------
# Scenario 7: Order preserved (by append sequence)
# ------------------------------------------------------------------


def scenario_order_preserved() -> None:
    """Records maintain the order they were appended."""
    snapshot = MemoryRuntime.create_snapshot()

    for i in range(5):
        rec = MemoryRecord.create_with_timestamp("test", "seq", f"Item-{i}", timestamp=float(i))
        snapshot = MemoryRuntime.append_record(snapshot, rec)

    contents = [r.content for r in snapshot.records]
    assert contents == ["Item-0", "Item-1", "Item-2", "Item-3", "Item-4"]
    assert [r.timestamp for r in snapshot.records] == [0.0, 1.0, 2.0, 3.0, 4.0]
    print(f"[PASS] order_preserved                | contents={contents}")


# ------------------------------------------------------------------
# Scenario 8: Metadata preserved
# ------------------------------------------------------------------


def scenario_metadata() -> None:
    """Record metadata is preserved correctly."""
    record = MemoryRecord.create(
        source="conv",
        category="msg",
        content="Hello",
        metadata={"session_id": "abc-123", "user": "Alice"},
    )

    assert record.metadata["session_id"] == "abc-123"
    assert record.metadata["user"] == "Alice"
    print(f"[PASS] metadata                       | session_id='{record.metadata['session_id']}' "
          f"user='{record.metadata['user']}'")


# ------------------------------------------------------------------
# Scenario 9: Timestamps are set on creation
# ------------------------------------------------------------------


def scenario_timestamps() -> None:
    """Records created via create() get an auto-generated timestamp."""
    record = MemoryRecord.create(source="test", category="info", content="Timed")

    assert record.timestamp > 0
    assert isinstance(record.timestamp, float)
    print(f"[PASS] timestamps                     | timestamp={record.timestamp:.2f} "
          f"(> 0)")


# ------------------------------------------------------------------
# Scenario 10: Trace populated in build_result
# ------------------------------------------------------------------


def scenario_trace() -> None:
    """MemoryResult contains snapshot, trace, and stats."""
    snapshot = MemoryRuntime.create_snapshot()

    record = MemoryRecord.create(source="test", category="info", content="Trace test")
    snapshot = MemoryRuntime.append_record(snapshot, record)

    result = MemoryRuntime.build_result(
        snapshot=snapshot,
        operations=["create_snapshot", "append_record"],
        timestamps={"start": 100.0, "end": 101.0},
    )

    assert isinstance(result, MemoryResult)
    assert result.success is True
    assert result.trace.operations == ["create_snapshot", "append_record"]
    assert result.trace.timestamps["start"] == 100.0
    assert result.trace.records_created == 1
    assert result.error_message == ""
    print(f"[PASS] trace                          | success={result.success} "
          f"ops={result.trace.operations} "
          f"records_created={result.trace.records_created}")


# ------------------------------------------------------------------
# Scenario 11: Determinism
# ------------------------------------------------------------------


def scenario_determinism() -> None:
    """Identical append sequences produce identical snapshot content."""
    recs = [
        MemoryRecord.create_with_timestamp("test", "cat", "Same", timestamp=1.0),
        MemoryRecord.create_with_timestamp("test", "cat", "Same2", timestamp=2.0),
    ]

    s1 = MemoryRuntime.create_snapshot()
    s1 = MemoryRuntime.append_record(s1, recs[0])
    s1 = MemoryRuntime.append_record(s1, recs[1])

    s2 = MemoryRuntime.create_snapshot()
    s2 = MemoryRuntime.append_record(s2, recs[0])
    s2 = MemoryRuntime.append_record(s2, recs[1])

    assert s1.records[0].content == s2.records[0].content
    assert s1.records[0].category == s2.records[0].category
    assert s1.records[0].source == s2.records[0].source
    assert s1.records[1].content == s2.records[1].content
    assert len(s1.records) == len(s2.records)
    print(f"[PASS] determinism                    | records={len(s1.records)} "
          f"(identical structure)")


# ------------------------------------------------------------------
# Scenario 12: Simulated integration with Conversation
# ------------------------------------------------------------------


def scenario_simulated_conversation_integration() -> None:
    """Simulate recording conversation messages as memory records."""
    snapshot = MemoryRuntime.create_snapshot()

    conversation_messages = [
        ("user", "What is AI?", "conversation"),
        ("assistant", "AI stands for Artificial Intelligence.", "conversation"),
        ("user", "What is ML?", "conversation"),
        ("assistant", "ML stands for Machine Learning.", "conversation"),
    ]

    for role, content, source in conversation_messages:
        rec = MemoryRecord.create(
            source=source,
            category="message",
            content=f"[{role}] {content}",
            metadata={"role": role},
        )
        snapshot = MemoryRuntime.append_record(snapshot, rec)

    assert len(snapshot.records) == 4
    assert all(r.category == "message" for r in snapshot.records)
    assert all(r.source == "conversation" for r in snapshot.records)

    user_records = tuple(r for r in snapshot.records if r.metadata.get("role") == "user")
    assistant_records = tuple(r for r in snapshot.records if r.metadata.get("role") == "assistant")

    assert len(user_records) == 2
    assert len(assistant_records) == 2
    assert user_records[0].content == "[user] What is AI?"

    # Filter by source to find all conversation records
    conv_records = MemoryRuntime.filter_by_source(snapshot, "conversation")
    assert len(conv_records) == 4

    print(f"[PASS] simulated_conversation         | total={len(snapshot.records)} "
          f"user_msgs={len(user_records)} "
          f"assistant_msgs={len(assistant_records)}")


# ------------------------------------------------------------------
# Scenario 13: Build result with error
# ------------------------------------------------------------------


def scenario_build_result_error() -> None:
    """MemoryResult can represent a failure with an error message."""
    snapshot = MemoryRuntime.create_snapshot()

    result = MemoryRuntime.build_result(
        snapshot=snapshot,
        operations=["validate"],
        timestamps={"start": 0.0},
        success=False,
        error_message="Validation failed: empty content.",
    )

    assert result.success is False
    assert result.error_message == "Validation failed: empty content."
    assert result.trace.records_created == 0
    print(f"[PASS] build_result_error             | success={result.success} "
          f"error='{result.error_message}'")


# ------------------------------------------------------------------
# Main
# ------------------------------------------------------------------


def main() -> None:
    print("=" * 56)
    print("Memory Runtime Foundation Demo")
    print("=" * 56)
    print()

    scenario_empty_snapshot()
    scenario_add_record()
    scenario_multiple_records()
    scenario_filter_by_category()
    scenario_filter_by_source()
    scenario_immutability()
    scenario_order_preserved()
    scenario_metadata()
    scenario_timestamps()
    scenario_trace()
    scenario_determinism()
    scenario_simulated_conversation_integration()
    scenario_build_result_error()

    print()
    print("=" * 56)
    print("All Memory Runtime scenarios passed.")
    print("=" * 56)


if __name__ == "__main__":
    main()
