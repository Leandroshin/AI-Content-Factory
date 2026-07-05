"""Foundation runtime for the AI Execution Engine.

Stateless execution runtime that orchestrates the pipeline:

  prepare_context → execute_llm → validate_output → build_result

No events emitted. No persistence. No external runtime coupling.
The LLM call is injected via a callable (dependency inversion).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable
from uuid import UUID, uuid4
import time

from core.conversation import ConversationRuntime, ConversationSession
from core.llm.models import LLMRequest, LLMResponse


# ------------------------------------------------------------------
# Immutable data types
# ------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class ExecutionContext:
    """Immutable context for a single AI execution.

    Contains the task snapshot, employee snapshot, the LLM request,
    and optional metadata. All fields are snapshot-based — never
    runtime objects.
    """

    execution_id: UUID
    task_snapshot: Any
    employee_snapshot: Any
    llm_request: LLMRequest
    metadata: dict[str, Any] = field(default_factory=dict)
    conversation_session: ConversationSession | None = None


@dataclass(frozen=True, slots=True)
class ExecutionTrace:
    """Immutable trace recording pipeline stages and timing.

    Attributes:
        stages: List of stage names in execution order.
        timestamps: Dict mapping stage name to Unix timestamp.
        provider_used: The LLM provider that serviced the request.
        model_used: The model identifier used.
    """

    stages: list[str] = field(default_factory=list)
    timestamps: dict[str, float] = field(default_factory=dict)
    provider_used: str = ""
    model_used: str = ""


@dataclass(frozen=True, slots=True)
class ExecutionResult:
    """Immutable outcome of an AI execution.

    Attributes:
        execution_id: Matches the ExecutionContext.execution_id.
        success: True if execution completed without errors.
        output: The LLM response content (empty on failure).
        error_message: Human-readable error description (empty on success).
        started_at: Unix timestamp of when execution began.
        finished_at: Unix timestamp of when execution finished.
        duration_seconds: Wall-clock duration in seconds.
        trace: ExecutionTrace with pipeline timing and provider info.
    """

    execution_id: UUID
    success: bool
    output: str
    error_message: str
    started_at: float
    finished_at: float
    duration_seconds: float
    trace: ExecutionTrace
    updated_conversation: ConversationSession | None = None


# ------------------------------------------------------------------
# ExecutionRuntime
# ------------------------------------------------------------------


class ExecutionRuntime:
    """Stateless orchestrator for AI task execution.

    Pipeline:
      1. prepare_context   — assemble ExecutionContext from snapshots
      2. execute_llm       — invoke the injected LLM callable
      3. validate_output   — check LLMResponse for content and errors
      4. build_result      — assemble ExecutionResult with trace
    """

    @staticmethod
    def prepare_context(
        task_snapshot: Any,
        employee_snapshot: Any,
        llm_request: LLMRequest,
        metadata: dict[str, Any] | None = None,
        conversation_session: ConversationSession | None = None,
    ) -> ExecutionContext:
        """Assemble an ExecutionContext from raw snapshots.

        Args:
            task_snapshot: Snapshot of the task to execute.
            employee_snapshot: Snapshot of the assigned employee.
            llm_request: Pre-built LLMRequest for the gateway.
            metadata: Optional extra metadata.
            conversation_session: Optional conversation session to attach.

        Returns:
            A new ExecutionContext with an auto-generated execution_id.
        """
        return ExecutionContext(
            execution_id=uuid4(),
            task_snapshot=task_snapshot,
            employee_snapshot=employee_snapshot,
            llm_request=llm_request,
            metadata=dict(metadata) if metadata else {},
            conversation_session=conversation_session,
        )

    @staticmethod
    def execute_llm(
        context: ExecutionContext,
        call_llm: Callable[[LLMRequest], LLMResponse],
    ) -> LLMResponse | None:
        """Execute the LLM call via the injected callable.

        Args:
            context: The execution context containing the LLM request.
            call_llm: A callable that takes LLMRequest and returns
                      LLMResponse. Typically wraps LLMGateway.execute().

        Returns:
            An LLMResponse on success, or None if the callable raised.
        """
        try:
            return call_llm(context.llm_request)
        except Exception:
            return None

    @staticmethod
    def validate_output(response: LLMResponse | None) -> tuple[bool, str]:
        """Validate the LLM response for content and errors.

        Args:
            response: The LLMResponse from execute_llm (or None on error).

        Returns:
            Tuple of (is_valid, error_message).
        """
        if response is None:
            return False, "LLM call failed with an exception."

        if response.finish_reason in ("error", "fail"):
            return False, f"LLM finished with reason '{response.finish_reason}'."

        if not response.content or not response.content.strip():
            return False, "LLM returned empty output."

        return True, ""

    @staticmethod
    def build_result(
        context: ExecutionContext,
        response: LLMResponse | None,
        started_at: float,
        is_valid: bool,
        error_message: str,
        updated_conversation: ConversationSession | None = None,
    ) -> ExecutionResult:
        """Assemble the final ExecutionResult with trace.

        Args:
            context: The original execution context.
            response: The LLM response (or None).
            started_at: Timestamp when the pipeline started.
            is_valid: Whether the output passed validation.
            error_message: Error description (empty on success).
            provider_used: Provider name from the response.
            model_used: Model name from the response.
            updated_conversation: The conversation session after auto-logging.

        Returns:
            A complete ExecutionResult.
        """
        finished_at = time.time()
        duration = round(finished_at - started_at, 4)

        provider = response.provider if response else ""
        model = response.model if response else ""

        trace = ExecutionTrace(
            stages=["prepare_context", "execute_llm", "validate_output", "build_result"],
            timestamps={
                "start": started_at,
                "llm_response": finished_at,
            },
            provider_used=provider,
            model_used=model,
        )

        output = response.content if response and is_valid else ""

        return ExecutionResult(
            execution_id=context.execution_id,
            success=is_valid,
            output=output,
            error_message=error_message,
            started_at=started_at,
            finished_at=finished_at,
            duration_seconds=duration,
            trace=trace,
            updated_conversation=updated_conversation,
        )

    @classmethod
    def execute(
        cls,
        task_snapshot: Any,
        employee_snapshot: Any,
        llm_request: LLMRequest,
        call_llm: Callable[[LLMRequest], LLMResponse],
        metadata: dict[str, Any] | None = None,
        conversation_session: ConversationSession | None = None,
    ) -> ExecutionResult:
        """Run the full execution pipeline end-to-end.

        Automatically logs the user prompt and assistant response
        into the conversation session when one is provided.

        Args:
            task_snapshot: Snapshot of the task.
            employee_snapshot: Snapshot of the assigned employee.
            llm_request: Pre-built LLMRequest.
            call_llm: Callable that sends the request to an LLM.
            metadata: Optional extra metadata.
            conversation_session: Optional session for auto-logging.

        Returns:
            An ExecutionResult with success/failure and full trace.
        """
        started_at = time.time()

        context = cls.prepare_context(
            task_snapshot, employee_snapshot, llm_request, metadata,
            conversation_session=conversation_session,
        )

        updated_session = context.conversation_session

        if updated_session is not None:
            updated_session = ConversationRuntime.append_message(
                updated_session, "user", context.llm_request.prompt,
            )
            context = ExecutionContext(
                execution_id=context.execution_id,
                task_snapshot=context.task_snapshot,
                employee_snapshot=context.employee_snapshot,
                llm_request=context.llm_request,
                metadata=dict(context.metadata),
                conversation_session=updated_session,
            )

        response = cls.execute_llm(context, call_llm)

        if updated_session is not None and response is not None:
            updated_session = ConversationRuntime.append_message(
                updated_session, "assistant", response.content,
            )

        is_valid, error_message = cls.validate_output(response)
        return cls.build_result(
            context, response, started_at, is_valid, error_message,
            updated_conversation=updated_session,
        )

    @classmethod
    def execute_with_gateway(
        cls,
        task_snapshot: Any,
        employee_snapshot: Any,
        llm_request: LLMRequest,
        gateway: Any,
        provider_name: str | None = None,
        metadata: dict[str, Any] | None = None,
        conversation_session: ConversationSession | None = None,
    ) -> ExecutionResult:
        """Convenience method: inject gateway.execute as the LLM callable.

        Accepts any object with an ``execute(request, provider_name=None)``
        method (e.g. LLMGateway). This keeps ``execute()`` fully generic
        while providing a convenient binding for real Gateway usage.

        Args:
            task_snapshot: Snapshot of the task.
            employee_snapshot: Snapshot of the assigned employee.
            llm_request: Pre-built LLMRequest.
            gateway: Object with execute(request, provider_name) method.
            provider_name: Optional provider name override.
            metadata: Optional extra metadata.
            conversation_session: Optional session for auto-logging.

        Returns:
            An ExecutionResult with success/failure and full trace.
        """
        def _call_llm(request: LLMRequest) -> LLMResponse:
            return gateway.execute(request, provider_name=provider_name)

        return cls.execute(
            task_snapshot, employee_snapshot, llm_request, _call_llm, metadata,
            conversation_session=conversation_session,
        )
