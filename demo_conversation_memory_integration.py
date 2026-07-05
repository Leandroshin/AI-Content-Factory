"""Integration demo — ConversationRuntime + MemoryRuntime.

Validates that every ConversationMessage can be transformed into
a deterministic MemoryRecord via ConversationRuntime.create_memory_record().
"""

from __future__ import annotations

from uuid import UUID

from core.conversation import (
    ConversationMessage,
    ConversationRuntime,
    ConversationSession,
)
from core.memory import MemoryRecord, MemoryRuntime, MemorySnapshot


# ------------------------------------------------------------------
# Scenario 1: First message creates a memory record
# ------------------------------------------------------------------


def scenario_first_message() -> None:
    """The first message in a session produces a valid MemoryRecord."""
    session = ConversationRuntime.create_session("emp-001")
    session = ConversationRuntime.append_message(session, "user", "Hello world")

    record = ConversationRuntime.create_memory_record(
        session, session.messages[0],
    )

    assert isinstance(record, MemoryRecord)
    assert record.source == "conversation"
    assert record.category == "conversation_message"
    assert record.content == "Hello world"
    print(f"[PASS] first_message                   | memory_id={record.memory_id.hex[:8]} "
          f"content='{record.content}'")


# ------------------------------------------------------------------
# Scenario 2: Multiple messages produce multiple records
# ------------------------------------------------------------------


def scenario_multiple_messages() -> None:
    """Each message in a session maps to its own MemoryRecord."""
    session = ConversationRuntime.create_session("emp-001")
    session = ConversationRuntime.append_message(session, "user", "First")
    session = ConversationRuntime.append_message(session, "assistant", "Second")
    session = ConversationRuntime.append_message(session, "user", "Third")

    records = [
        ConversationRuntime.create_memory_record(session, msg)
        for msg in session.messages
    ]

    assert len(records) == 3
    assert records[0].content == "First"
    assert records[1].content == "Second"
    assert records[2].content == "Third"
    print(f"[PASS] multiple_messages              | {len(records)} records -> "
          f"contents=[{', '.join(r.content for r in records)}]")


# ------------------------------------------------------------------
# Scenario 3: Role user
# ------------------------------------------------------------------


def scenario_role_user() -> None:
    """User messages are correctly identified in the MemoryRecord."""
    session = ConversationRuntime.create_session("emp-001")
    session = ConversationRuntime.append_message(session, "user", "A user query")

    record = ConversationRuntime.create_memory_record(
        session, session.messages[0],
    )

    assert record.metadata["role"] == "user"
    print(f"[PASS] role_user                      | role='{record.metadata['role']}' "
          f"content='{record.content}'")


# ------------------------------------------------------------------
# Scenario 4: Role assistant
# ------------------------------------------------------------------


def scenario_role_assistant() -> None:
    """Assistant messages are correctly identified in the MemoryRecord."""
    session = ConversationRuntime.create_session("emp-001")
    session = ConversationRuntime.append_message(session, "assistant", "An AI response")

    record = ConversationRuntime.create_memory_record(
        session, session.messages[0],
    )

    assert record.metadata["role"] == "assistant"
    print(f"[PASS] role_assistant                 | role='{record.metadata['role']}' "
          f"content='{record.content}'")


# ------------------------------------------------------------------
# Scenario 5: Metadata correct
# ------------------------------------------------------------------


def scenario_metadata_correct() -> None:
    """MemoryRecord metadata contains session_id, message_id, role, participant_id."""
    session = ConversationRuntime.create_session(
        "emp-042", metadata={"env": "test"},
    )
    session = ConversationRuntime.append_message(
        session, "user", "Metadata check",
        metadata={"source": "web"},
    )

    record = ConversationRuntime.create_memory_record(
        session, session.messages[0],
    )

    assert record.metadata["session_id"] == str(session.session_id)
    assert record.metadata["message_id"] == str(session.messages[0].message_id)
    assert record.metadata["role"] == "user"
    assert record.metadata["participant_id"] == "emp-042"
    assert record.metadata["session_id"] == str(session.session_id)
    print(f"[PASS] metadata_correct               | session_id={record.metadata['session_id'][:8]} "
          f"message_id={record.metadata['message_id'][:8]} "
          f"role={record.metadata['role']} "
          f"participant={record.metadata['participant_id']}")


# ------------------------------------------------------------------
# Scenario 6: Timestamp preserved
# ------------------------------------------------------------------


def scenario_timestamp_preserved() -> None:
    """The MemoryRecord timestamp matches the original message timestamp."""
    session = ConversationRuntime.create_session("emp-001")
    session = ConversationRuntime.append_message(session, "user", "Timed message")

    record = ConversationRuntime.create_memory_record(
        session, session.messages[0],
    )

    assert record.timestamp == session.messages[0].timestamp
    assert record.timestamp > 0
    print(f"[PASS] timestamp_preserved            | message_timestamp={session.messages[0].timestamp} "
          f"record_timestamp={record.timestamp} (match)")


# ------------------------------------------------------------------
# Scenario 7: Session ID correct
# ------------------------------------------------------------------


def scenario_session_id_correct() -> None:
    """The MemoryRecord metadata references the correct session_id."""
    session = ConversationRuntime.create_session("emp-001")
    session = ConversationRuntime.append_message(session, "user", "Session check")

    record = ConversationRuntime.create_memory_record(
        session, session.messages[0],
    )

    assert record.metadata["session_id"] == str(session.session_id)
    print(f"[PASS] session_id_correct             | session_id={record.metadata['session_id'][:8]} "
          f"(matches session)")


# ------------------------------------------------------------------
# Scenario 8: Participant ID correct
# ------------------------------------------------------------------


def scenario_participant_id_correct() -> None:
    """The MemoryRecord metadata carries the correct participant_id."""
    session = ConversationRuntime.create_session("emp-007")
    session = ConversationRuntime.append_message(session, "assistant", "Participant check")

    record = ConversationRuntime.create_memory_record(
        session, session.messages[0],
    )

    assert record.metadata["participant_id"] == "emp-007"
    print(f"[PASS] participant_id_correct         | participant_id='{record.metadata['participant_id']}'")


# ------------------------------------------------------------------
# Scenario 9: Order preserved (records follow message order)
# ------------------------------------------------------------------


def scenario_order_preserved() -> None:
    """Records maintain the same order as messages in the session."""
    session = ConversationRuntime.create_session("emp-001")
    messages_data = [
        ("user", "Q1"),
        ("assistant", "A1"),
        ("user", "Q2"),
        ("assistant", "A2"),
    ]
    for role, content in messages_data:
        session = ConversationRuntime.append_message(session, role, content)

    records = [
        ConversationRuntime.create_memory_record(session, msg)
        for msg in session.messages
    ]

    assert len(records) == 4
    assert records[0].content == "Q1"
    assert records[1].content == "A1"
    assert records[2].content == "Q2"
    assert records[3].content == "A2"
    assert records[0].metadata["role"] == "user"
    assert records[1].metadata["role"] == "assistant"
    assert records[2].metadata["role"] == "user"
    assert records[3].metadata["role"] == "assistant"
    print(f"[PASS] order_preserved                | {len(records)} records "
          f"in correct sequence")


# ------------------------------------------------------------------
# Scenario 10: Immutability — session unchanged by record creation
# ------------------------------------------------------------------


def scenario_immutability() -> None:
    """create_memory_record does not modify the session or message."""
    session = ConversationRuntime.create_session("emp-001")
    original_session_id = session.session_id
    session = ConversationRuntime.append_message(session, "user", "Immutability test")
    original_msg_count = len(session.messages)

    _ = ConversationRuntime.create_memory_record(session, session.messages[0])

    assert len(session.messages) == original_msg_count
    assert session.session_id == original_session_id
    print(f"[PASS] immutability                   | session untouched "
          f"(messages={len(session.messages)}, session_id unchanged)")


# ------------------------------------------------------------------
# Scenario 11: Determinism — same inputs produce same record content
# ------------------------------------------------------------------


def scenario_determinism() -> None:
    """Identical message inputs produce identical MemoryRecord content."""
    session = ConversationRuntime.create_session("emp-001")
    session1 = ConversationRuntime.append_message(session, "user", "Deterministic")
    session2 = ConversationRuntime.append_message(session, "user", "Deterministic")

    r1 = ConversationRuntime.create_memory_record(session1, session1.messages[0])
    r2 = ConversationRuntime.create_memory_record(session2, session2.messages[0])

    assert r1.content == r2.content
    assert r1.source == r2.source
    assert r1.category == r2.category
    assert r1.metadata["role"] == r2.metadata["role"]
    assert r1.metadata["participant_id"] == r2.metadata["participant_id"]
    print(f"[PASS] determinism                    | content='{r1.content}' "
          f"source={r1.source} category={r1.category} role={r1.metadata['role']} (identical)")


# ------------------------------------------------------------------
# Scenario 12: End-to-end integration
# ------------------------------------------------------------------


def scenario_end_to_end() -> None:
    """Full pipeline: session -> messages -> records -> snapshot -> filter."""
    session = ConversationRuntime.create_session("emp-001")
    session = ConversationRuntime.append_message(session, "user", "E2E question")
    session = ConversationRuntime.append_message(session, "assistant", "E2E answer")
    session = ConversationRuntime.append_message(session, "user", "E2E follow-up")

    records = [
        ConversationRuntime.create_memory_record(session, msg)
        for msg in session.messages
    ]

    snapshot = MemoryRuntime.create_snapshot(records)

    assert len(snapshot.records) == 3
    assert snapshot.records[0].content == "E2E question"
    assert snapshot.records[1].content == "E2E answer"
    assert snapshot.records[2].content == "E2E follow-up"

    conv_records = MemoryRuntime.filter_by_source(snapshot, "conversation")
    assert len(conv_records) == 3

    user_records = MemoryRuntime.filter_by_category(snapshot, "conversation_message")
    assert len(user_records) == 3

    print(f"[PASS] end_to_end                     | session -> "
          f"{len(records)} records -> snapshot -> "
          f"filter(source={len(conv_records)}, category={len(user_records)})")


# ------------------------------------------------------------------
# Scenario 13: Record can be appended to a MemorySnapshot
# ------------------------------------------------------------------


def scenario_append_to_snapshot() -> None:
    """MemoryRecords from conversation can be stored in a MemorySnapshot."""
    session = ConversationRuntime.create_session("emp-001")
    session = ConversationRuntime.append_message(session, "user", "Snapshot test")
    session = ConversationRuntime.append_message(session, "assistant", "Snapshot response")

    snapshot = MemoryRuntime.create_snapshot()

    for msg in session.messages:
        record = ConversationRuntime.create_memory_record(session, msg)
        snapshot = MemoryRuntime.append_record(snapshot, record)

    assert len(snapshot.records) == 2
    assert snapshot.records[0].content == "Snapshot test"
    assert snapshot.records[1].content == "Snapshot response"
    print(f"[PASS] append_to_snapshot             | {len(snapshot.records)} records "
          f"appended to snapshot")


# ------------------------------------------------------------------
# Main
# ------------------------------------------------------------------


def main() -> None:
    print("=" * 62)
    print("Conversation + Memory Integration Demo")
    print("=" * 62)
    print()

    scenario_first_message()
    scenario_multiple_messages()
    scenario_role_user()
    scenario_role_assistant()
    scenario_metadata_correct()
    scenario_timestamp_preserved()
    scenario_session_id_correct()
    scenario_participant_id_correct()
    scenario_order_preserved()
    scenario_immutability()
    scenario_determinism()
    scenario_end_to_end()
    scenario_append_to_snapshot()

    print()
    print("=" * 62)
    print("All Conversation + Memory integration scenarios passed.")
    print("=" * 62)


if __name__ == "__main__":
    main()
