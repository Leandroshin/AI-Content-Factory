"""Foundation demo for the Conversation Runtime — no external dependencies.

Validates session creation, message appending, immutability,
chronological order, metadata, context, token estimation, trace,
and deterministic behaviour.
"""

from __future__ import annotations

from uuid import UUID

from core.conversation import (
    ConversationContext,
    ConversationMessage,
    ConversationResult,
    ConversationRuntime,
    ConversationSession,
    ConversationTrace,
)


# ------------------------------------------------------------------
# Scenario 1: Create a session
# ------------------------------------------------------------------


def scenario_create_session() -> None:
    """A new session has no messages and correct participant."""
    session = ConversationRuntime.create_session(participant_id="emp-001")

    assert isinstance(session, ConversationSession)
    assert isinstance(session.session_id, UUID)
    assert session.participant_id == "emp-001"
    assert session.messages == ()
    assert session.created_at > 0
    assert session.updated_at == session.created_at
    print(f"[PASS] create_session                  | id={session.session_id.hex[:8]} "
          f"participant={session.participant_id}")


# ------------------------------------------------------------------
# Scenario 2: Add a message to a session
# ------------------------------------------------------------------


def scenario_add_message() -> None:
    """Appending a message increments the message count."""
    session = ConversationRuntime.create_session("emp-001")
    updated = ConversationRuntime.append_message(session, "user", "Hello!")

    assert len(updated.messages) == 1
    assert updated.messages[0].role == "user"
    assert updated.messages[0].content == "Hello!"
    assert isinstance(updated.messages[0].message_id, UUID)
    print(f"[PASS] add_message                     | count={len(updated.messages)} "
          f"role={updated.messages[0].role} content='{updated.messages[0].content}'")


# ------------------------------------------------------------------
# Scenario 3: Multiple messages
# ------------------------------------------------------------------


def scenario_multiple_messages() -> None:
    """Multiple appends produce an ordered sequence of messages."""
    session = ConversationRuntime.create_session("emp-001")
    messages_data = [
        ("system", "You are a helpful assistant."),
        ("user", "What is AI?"),
        ("assistant", "AI stands for Artificial Intelligence."),
        ("user", "Thanks!"),
    ]
    for role, content in messages_data:
        session = ConversationRuntime.append_message(session, role, content)

    assert len(session.messages) == 4
    assert session.messages[0].role == "system"
    assert session.messages[1].role == "user"
    assert session.messages[2].role == "assistant"
    assert session.messages[3].role == "user"
    assert session.messages[3].content == "Thanks!"
    print(f"[PASS] multiple_messages              | count={len(session.messages)} "
          f"roles={[m.role for m in session.messages]}")


# ------------------------------------------------------------------
# Scenario 4: Immutability — original session unchanged after append
# ------------------------------------------------------------------


def scenario_immutability() -> None:
    """The original session is never mutated by append_message."""
    original = ConversationRuntime.create_session("emp-001")
    _ = ConversationRuntime.append_message(original, "user", "Hello")

    assert len(original.messages) == 0
    assert original.updated_at == original.created_at
    print(f"[PASS] immutability                   | original untouched "
          f"(messages={len(original.messages)})")


# ------------------------------------------------------------------
# Scenario 5: Immutability — original message unchanged
# ------------------------------------------------------------------


def scenario_message_immutability() -> None:
    """ConversationMessage instances are frozen and cannot be modified."""
    msg = ConversationMessage.create(role="user", content="Fixed")
    assert isinstance(msg, ConversationMessage)

    try:
        msg.content = "changed"
        assert False, "Should not allow mutation"
    except AttributeError:
        pass
    print(f"[PASS] message_immutability            | frozen dataclass prevents mutation")


# ------------------------------------------------------------------
# Scenario 6: Chronological order preserved
# ------------------------------------------------------------------


def scenario_chronological_order() -> None:
    """Messages are ordered by append sequence (timestamps should be non-decreasing)."""
    session = ConversationRuntime.create_session("emp-001")
    session = ConversationRuntime.append_message(session, "user", "First")
    session = ConversationRuntime.append_message(session, "assistant", "Second")
    session = ConversationRuntime.append_message(session, "user", "Third")

    timestamps = [m.timestamp for m in session.messages]
    assert timestamps[0] <= timestamps[1] <= timestamps[2]
    assert session.messages[0].content == "First"
    assert session.messages[1].content == "Second"
    assert session.messages[2].content == "Third"
    print(f"[PASS] chronological_order            | timestamps non-decreasing, "
          f"order preserved")


# ------------------------------------------------------------------
# Scenario 7: Metadata propagation
# ------------------------------------------------------------------


def scenario_metadata() -> None:
    """Session and message metadata is preserved and merged correctly."""
    session = ConversationRuntime.create_session(
        "emp-001",
        metadata={"env": "test", "language": "en"},
    )
    assert session.metadata["env"] == "test"

    session = session.update_metadata({"language": "pt", "version": "2.0"})
    assert session.metadata["env"] == "test"
    assert session.metadata["language"] == "pt"
    assert session.metadata["version"] == "2.0"

    msg = ConversationMessage.create("user", "Hi", metadata={"source": "web"})
    assert msg.metadata["source"] == "web"
    print(f"[PASS] metadata                       | session metadata={session.metadata} "
          f"message metadata={dict(msg.metadata)}")


# ------------------------------------------------------------------
# Scenario 8: Build context
# ------------------------------------------------------------------


def scenario_build_context() -> None:
    """ConversationContext wraps session with execution state."""
    session = ConversationRuntime.create_session("emp-001")
    session = ConversationRuntime.append_message(session, "user", "Hello")

    ctx = ConversationRuntime.build_context(
        session=session,
        current_task="Write article",
        current_employee="Alice",
        metadata={"department": "Content"},
    )

    assert isinstance(ctx, ConversationContext)
    assert ctx.session.session_id == session.session_id
    assert ctx.current_task == "Write article"
    assert ctx.current_employee == "Alice"
    assert ctx.metadata["department"] == "Content"
    assert ctx.current_company is None
    print(f"[PASS] build_context                  | task='{ctx.current_task}' "
          f"employee='{ctx.current_employee}'")


# ------------------------------------------------------------------
# Scenario 9: Token estimation
# ------------------------------------------------------------------


def scenario_token_estimation() -> None:
    """Token estimation returns a non-zero value proportional to text length."""
    text = "This is a sample text for token estimation."
    tokens = ConversationRuntime.estimate_tokens(text)

    assert tokens >= 1
    assert isinstance(tokens, int)
    # ~4 chars per token
    assert tokens <= len(text)

    # Longer text = more tokens
    longer = text + " And this additional text should increase the count."
    assert ConversationRuntime.estimate_tokens(longer) > tokens
    print(f"[PASS] token_estimation               | text_len={len(text)} "
          f"estimated_tokens={tokens}")


# ------------------------------------------------------------------
# Scenario 10: Session token estimation
# ------------------------------------------------------------------


def scenario_session_token_estimation() -> None:
    """Session token estimate sums estimates of all messages."""
    session = ConversationRuntime.create_session("emp-001")
    session = ConversationRuntime.append_message(session, "user", "Hello world")  # 11 chars → ~2 tokens
    session = ConversationRuntime.append_message(session, "assistant", "Hi there!")  # 9 chars → ~2 tokens

    total = ConversationRuntime.estimate_session_tokens(session)
    assert total >= 2
    print(f"[PASS] session_token_estimation        | messages={len(session.messages)} "
          f"total_estimated_tokens={total}")


# ------------------------------------------------------------------
# Scenario 11: Build result with trace
# ------------------------------------------------------------------


def scenario_build_result() -> None:
    """ConversationResult contains session, trace, and stats."""
    session = ConversationRuntime.create_session("emp-001")
    session = ConversationRuntime.append_message(session, "user", "Test content here.")
    session = ConversationRuntime.append_message(session, "assistant", "Response here.")

    result = ConversationRuntime.build_result(
        session=session,
        stages=["append_message", "build_result"],
        timestamps={"start": 1000.0, "end": 1001.0},
    )

    assert isinstance(result, ConversationResult)
    assert result.success is True
    assert result.updated_session.session_id == session.session_id
    assert result.trace.message_count == 2
    assert result.trace.token_estimate >= 1
    assert result.trace.stages == ["append_message", "build_result"]
    assert result.trace.timestamps["start"] == 1000.0
    assert result.error_message == ""
    print(f"[PASS] build_result                   | success={result.success} "
          f"messages={result.trace.message_count} "
          f"tokens={result.trace.token_estimate} "
          f"stages={result.trace.stages}")


# ------------------------------------------------------------------
# Scenario 12: Build result with error
# ------------------------------------------------------------------


def scenario_build_result_error() -> None:
    """ConversationResult can represent a failure with an error message."""
    session = ConversationRuntime.create_session("emp-001")

    result = ConversationRuntime.build_result(
        session=session,
        stages=["validate"],
        timestamps={"start": 0.0},
        success=False,
        error_message="Validation failed: empty content.",
    )

    assert result.success is False
    assert result.error_message == "Validation failed: empty content."
    assert result.updated_session.session_id == session.session_id
    print(f"[PASS] build_result_error             | success={result.success} "
          f"error='{result.error_message}'")


# ------------------------------------------------------------------
# Scenario 13: Determinism — same inputs produce same session structure
# ------------------------------------------------------------------


def scenario_determinism() -> None:
    """Identical append sequences produce identical session structures."""
    s1 = ConversationRuntime.create_session("emp-001")
    s1 = ConversationRuntime.append_message(s1, "user", "Hi")
    s1 = ConversationRuntime.append_message(s1, "assistant", "Hello")

    s2 = ConversationRuntime.create_session("emp-001")
    s2 = ConversationRuntime.append_message(s2, "user", "Hi")
    s2 = ConversationRuntime.append_message(s2, "assistant", "Hello")

    assert s1.messages[0].role == s2.messages[0].role
    assert s1.messages[0].content == s2.messages[0].content
    assert s1.messages[1].role == s2.messages[1].role
    assert s1.messages[1].content == s2.messages[1].content
    assert len(s1.messages) == len(s2.messages)
    print(f"[PASS] determinism                    | messages={len(s1.messages)} "
          f"(identical structure)")


# ------------------------------------------------------------------
# Main
# ------------------------------------------------------------------


def main() -> None:
    print("=" * 62)
    print("Conversation Runtime Foundation Demo")
    print("=" * 62)
    print()

    scenario_create_session()
    scenario_add_message()
    scenario_multiple_messages()
    scenario_immutability()
    scenario_message_immutability()
    scenario_chronological_order()
    scenario_metadata()
    scenario_build_context()
    scenario_token_estimation()
    scenario_session_token_estimation()
    scenario_build_result()
    scenario_build_result_error()
    scenario_determinism()

    print()
    print("=" * 62)
    print("All Conversation Runtime scenarios passed.")
    print("=" * 62)


if __name__ == "__main__":
    main()
