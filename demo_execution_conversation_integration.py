"""Integration demo — ExecutionRuntime + ConversationRuntime.

Validates that every execution with a conversation session
auto-logs the user prompt and assistant response, preserving
immutability and determinism throughout the pipeline.
"""

from __future__ import annotations

from uuid import UUID

from core.conversation import ConversationRuntime, ConversationSession
from core.execution import ExecutionResult, ExecutionRuntime
from core.llm.models import LLMRequest, LLMResponse


# ------------------------------------------------------------------
# Fake callable for deterministic LLM responses
# ------------------------------------------------------------------


def fake_call_llm_fixed(request: LLMRequest) -> LLMResponse:
    """Return a deterministic 'Hello!' response."""
    return LLMResponse(
        request_id=request.request_id,
        provider="fake",
        model="fake-model",
        content="Hello!",
        finish_reason="stop",
    )


def fake_call_llm_custom(request: LLMRequest) -> LLMResponse:
    """Return a response based on the input prompt."""
    return LLMResponse(
        request_id=request.request_id,
        provider="fake",
        model="fake-model",
        content=f"Echo: {request.prompt}",
        finish_reason="stop",
    )


# ------------------------------------------------------------------
# Scenario 1: Execution without conversation session
# ------------------------------------------------------------------


def scenario_execution_without_session() -> None:
    """When no session is provided, updated_conversation is None."""
    request = LLMRequest.create(prompt="Hello")
    result = ExecutionRuntime.execute(
        task_snapshot="task-1",
        employee_snapshot="emp-1",
        llm_request=request,
        call_llm=fake_call_llm_fixed,
    )

    assert isinstance(result, ExecutionResult)
    assert result.success is True
    assert result.updated_conversation is None
    print(f"[PASS] execution_without_session       | success={result.success} "
          f"updated_conversation={result.updated_conversation}")


# ------------------------------------------------------------------
# Scenario 2: Execution with existing session
# ------------------------------------------------------------------


def scenario_execution_with_session() -> None:
    """When a session is provided, updated_conversation contains new messages."""
    session = ConversationRuntime.create_session("emp-001")
    request = LLMRequest.create(prompt="What is AI?")

    result = ExecutionRuntime.execute(
        task_snapshot="task-1",
        employee_snapshot="emp-1",
        llm_request=request,
        call_llm=fake_call_llm_fixed,
        conversation_session=session,
    )

    assert result.updated_conversation is not None
    assert len(result.updated_conversation.messages) == 2
    print(f"[PASS] execution_with_session          | messages={len(result.updated_conversation.messages)} "
          f"session_id={result.updated_conversation.session_id.hex[:8]}")


# ------------------------------------------------------------------
# Scenario 3: Historical messages preserved
# ------------------------------------------------------------------


def scenario_history_preserved() -> None:
    """Previous messages survive the execution round."""
    session = ConversationRuntime.create_session("emp-001")
    session = ConversationRuntime.append_message(session, "user", "Old message")

    request = LLMRequest.create(prompt="New message")
    result = ExecutionRuntime.execute(
        task_snapshot="task-1",
        employee_snapshot="emp-1",
        llm_request=request,
        call_llm=fake_call_llm_fixed,
        conversation_session=session,
    )

    assert result.updated_conversation is not None
    assert len(result.updated_conversation.messages) == 3
    assert result.updated_conversation.messages[0].content == "Old message"
    assert result.updated_conversation.messages[1].content == "New message"
    assert result.updated_conversation.messages[2].content == "Hello!"
    print(f"[PASS] history_preserved               | total={len(result.updated_conversation.messages)} "
          f"msgs=['{result.updated_conversation.messages[0].content}', "
          f"'{result.updated_conversation.messages[1].content}', "
          f"'{result.updated_conversation.messages[2].content}']")


# ------------------------------------------------------------------
# Scenario 4: Original session remains immutable
# ------------------------------------------------------------------


def scenario_original_session_immutable() -> None:
    """The original session passed in is never modified."""
    original = ConversationRuntime.create_session("emp-001")
    request = LLMRequest.create(prompt="Hello")

    _ = ExecutionRuntime.execute(
        task_snapshot="task-1",
        employee_snapshot="emp-1",
        llm_request=request,
        call_llm=fake_call_llm_fixed,
        conversation_session=original,
    )

    assert len(original.messages) == 0
    assert original.updated_at == original.created_at
    print(f"[PASS] original_session_immutable     | original untouched "
          f"(messages={len(original.messages)})")


# ------------------------------------------------------------------
# Scenario 5: New session instance returned
# ------------------------------------------------------------------


def scenario_new_session_instance() -> None:
    """The updated session is a different object from the original."""
    original = ConversationRuntime.create_session("emp-001")
    request = LLMRequest.create(prompt="Hello")

    result = ExecutionRuntime.execute(
        task_snapshot="task-1",
        employee_snapshot="emp-1",
        llm_request=request,
        call_llm=fake_call_llm_fixed,
        conversation_session=original,
    )

    assert result.updated_conversation is not None
    assert result.updated_conversation is not original
    assert result.updated_conversation.session_id == original.session_id
    print(f"[PASS] new_session_instance            | different object, same session_id "
          f"{original.session_id.hex[:8]}")


# ------------------------------------------------------------------
# Scenario 6: User message added
# ------------------------------------------------------------------


def scenario_user_message_added() -> None:
    """The user prompt is logged as the first new message."""
    session = ConversationRuntime.create_session("emp-001")
    request = LLMRequest.create(prompt="What is the capital of France?")

    result = ExecutionRuntime.execute(
        task_snapshot="task-1",
        employee_snapshot="emp-1",
        llm_request=request,
        call_llm=fake_call_llm_fixed,
        conversation_session=session,
    )

    assert result.updated_conversation is not None
    user_msg = result.updated_conversation.messages[0]
    assert user_msg.role == "user"
    assert user_msg.content == "What is the capital of France?"
    print(f"[PASS] user_message_added             | role='{user_msg.role}' "
          f"content='{user_msg.content}'")


# ------------------------------------------------------------------
# Scenario 7: Assistant response added
# ------------------------------------------------------------------


def scenario_assistant_response_added() -> None:
    """The assistant response is logged as the second new message."""
    session = ConversationRuntime.create_session("emp-001")
    request = LLMRequest.create(prompt="Hello")

    result = ExecutionRuntime.execute(
        task_snapshot="task-1",
        employee_snapshot="emp-1",
        llm_request=request,
        call_llm=fake_call_llm_fixed,
        conversation_session=session,
    )

    assert result.updated_conversation is not None
    assistant_msg = result.updated_conversation.messages[1]
    assert assistant_msg.role == "assistant"
    assert assistant_msg.content == "Hello!"
    print(f"[PASS] assistant_response_added       | role='{assistant_msg.role}' "
          f"content='{assistant_msg.content}'")


# ------------------------------------------------------------------
# Scenario 8: Correct message order
# ------------------------------------------------------------------


def scenario_correct_message_order() -> None:
    """User message always precedes assistant message."""
    session = ConversationRuntime.create_session("emp-001")
    request = LLMRequest.create(prompt="What is AI?")

    result = ExecutionRuntime.execute(
        task_snapshot="task-1",
        employee_snapshot="emp-1",
        llm_request=request,
        call_llm=fake_call_llm_fixed,
        conversation_session=session,
    )

    assert result.updated_conversation is not None
    assert result.updated_conversation.messages[0].role == "user"
    assert result.updated_conversation.messages[1].role == "assistant"
    assert result.updated_conversation.messages[0].timestamp <= result.updated_conversation.messages[1].timestamp
    print(f"[PASS] correct_message_order          | user before assistant "
          f"(t_user={result.updated_conversation.messages[0].timestamp}, "
          f"t_assistant={result.updated_conversation.messages[1].timestamp})")


# ------------------------------------------------------------------
# Scenario 9: Determinism (same inputs → same structure)
# ------------------------------------------------------------------


def scenario_determinism() -> None:
    """Identical inputs produce identical conversation structure."""
    request = LLMRequest.create(prompt="Count to three.", model="gpt-4o")

    def fake_call(request: LLMRequest) -> LLMResponse:
        return LLMResponse(
            request_id=request.request_id,
            provider="fake",
            model="fake-model",
            content="One, two, three.",
            finish_reason="stop",
        )

    session = ConversationRuntime.create_session("emp-001")

    r1 = ExecutionRuntime.execute(
        task_snapshot="task-x", employee_snapshot="emp-x",
        llm_request=request, call_llm=fake_call,
        conversation_session=session,
    )

    r2 = ExecutionRuntime.execute(
        task_snapshot="task-x", employee_snapshot="emp-x",
        llm_request=request, call_llm=fake_call,
        conversation_session=session,
    )

    assert r1.updated_conversation is not None
    assert r2.updated_conversation is not None
    assert r1.updated_conversation.messages[0].role == r2.updated_conversation.messages[0].role
    assert r1.updated_conversation.messages[0].content == r2.updated_conversation.messages[0].content
    assert r1.updated_conversation.messages[1].role == r2.updated_conversation.messages[1].role
    assert r1.updated_conversation.messages[1].content == r2.updated_conversation.messages[1].content
    print(f"[PASS] determinism                    | identical structure "
          f"(user='{r1.updated_conversation.messages[0].content}', "
          f"assistant='{r1.updated_conversation.messages[1].content}')")


# ------------------------------------------------------------------
# Scenario 10: Multiple independent executions
# ------------------------------------------------------------------


def scenario_multiple_executions() -> None:
    """The session can be passed through multiple executions,
    accumulating history each time."""
    session = ConversationRuntime.create_session("emp-001")
    request1 = LLMRequest.create(prompt="First prompt")
    request2 = LLMRequest.create(prompt="Second prompt")
    request3 = LLMRequest.create(prompt="Third prompt")

    def echo_call(request: LLMRequest) -> LLMResponse:
        return LLMResponse(
            request_id=request.request_id,
            provider="fake",
            model="fake-model",
            content=f"Response to: {request.prompt}",
            finish_reason="stop",
        )

    # First execution
    r1 = ExecutionRuntime.execute(
        task_snapshot="task-1", employee_snapshot="emp-1",
        llm_request=request1, call_llm=echo_call,
        conversation_session=session,
    )
    assert r1.updated_conversation is not None
    assert len(r1.updated_conversation.messages) == 2

    # Second execution — pass previous session
    r2 = ExecutionRuntime.execute(
        task_snapshot="task-2", employee_snapshot="emp-1",
        llm_request=request2, call_llm=echo_call,
        conversation_session=r1.updated_conversation,
    )
    assert r2.updated_conversation is not None
    assert len(r2.updated_conversation.messages) == 4

    # Third execution
    r3 = ExecutionRuntime.execute(
        task_snapshot="task-3", employee_snapshot="emp-1",
        llm_request=request3, call_llm=echo_call,
        conversation_session=r2.updated_conversation,
    )
    assert r3.updated_conversation is not None
    assert len(r3.updated_conversation.messages) == 6

    assert r3.updated_conversation.messages[0].content == "First prompt"
    assert r3.updated_conversation.messages[1].content == "Response to: First prompt"
    assert r3.updated_conversation.messages[2].content == "Second prompt"
    assert r3.updated_conversation.messages[3].content == "Response to: Second prompt"
    assert r3.updated_conversation.messages[4].content == "Third prompt"
    assert r3.updated_conversation.messages[5].content == "Response to: Third prompt"
    print(f"[PASS] multiple_executions            | 3 executions -> "
          f"{len(r3.updated_conversation.messages)} messages, "
          f"all in order")


# ------------------------------------------------------------------
# Scenario 11: End-to-end integration with prepare_context
# ------------------------------------------------------------------


def scenario_end_to_end() -> None:
    """Full pipeline: prepare_context → execute → result with conversation."""
    session = ConversationRuntime.create_session("emp-001")
    request = LLMRequest.create(prompt="End-to-end test", model="gpt-4o")

    ctx = ExecutionRuntime.prepare_context(
        task_snapshot="task-e2e",
        employee_snapshot="emp-e2e",
        llm_request=request,
        metadata={"env": "test"},
        conversation_session=session,
    )

    assert ctx.conversation_session is not None
    assert ctx.conversation_session.session_id == session.session_id

    response = fake_call_llm_fixed(request)
    is_valid, error = ExecutionRuntime.validate_output(response)
    assert is_valid is True

    result = ExecutionRuntime.build_result(
        ctx, response, started_at=1000.0,
        is_valid=is_valid, error_message=error,
        updated_conversation=session,
    )

    assert result.updated_conversation is not None
    assert result.updated_conversation.session_id == session.session_id
    assert result.trace.provider_used == "fake"
    print(f"[PASS] end_to_end                     | success={result.success} "
          f"trace.provider='{result.trace.provider_used}' "
          f"result.updated_conversation.session_id={result.updated_conversation.session_id.hex[:8]}")


# ------------------------------------------------------------------
# Scenario 12: Provider failure still logs user message
# ------------------------------------------------------------------


def scenario_failure_logs_user_message() -> None:
    """When the LLM call fails, the user message is still recorded."""
    session = ConversationRuntime.create_session("emp-001")

    def failing_call(request: LLMRequest) -> LLMResponse:
        msg = "Provider unavailable"
        raise RuntimeError(msg)

    request = LLMRequest.create(prompt="This will fail")
    result = ExecutionRuntime.execute(
        task_snapshot="task-fail",
        employee_snapshot="emp-fail",
        llm_request=request,
        call_llm=failing_call,
        conversation_session=session,
    )

    assert result.success is False
    assert result.updated_conversation is not None
    assert len(result.updated_conversation.messages) == 1
    assert result.updated_conversation.messages[0].role == "user"
    assert result.updated_conversation.messages[0].content == "This will fail"
    print(f"[PASS] failure_logs_user_message      | success={result.success} "
          f"messages={len(result.updated_conversation.messages)} "
          f"user_msg='{result.updated_conversation.messages[0].content}'")


# ------------------------------------------------------------------
# Main
# ------------------------------------------------------------------


def main() -> None:
    print("=" * 66)
    print("ExecutionRuntime + ConversationRuntime Integration Demo")
    print("=" * 66)
    print()

    scenario_execution_without_session()
    scenario_execution_with_session()
    scenario_history_preserved()
    scenario_original_session_immutable()
    scenario_new_session_instance()
    scenario_user_message_added()
    scenario_assistant_response_added()
    scenario_correct_message_order()
    scenario_determinism()
    scenario_multiple_executions()
    scenario_end_to_end()
    scenario_failure_logs_user_message()

    print()
    print("=" * 66)
    print("All Execution+Conversation integration scenarios passed.")
    print("=" * 66)


if __name__ == "__main__":
    main()
