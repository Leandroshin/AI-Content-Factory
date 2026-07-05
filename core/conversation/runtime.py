"""Foundation runtime for the Conversation Runtime.

Stateless, deterministic conversation session manager.
No IO, no async, no threads, no database, no EventBus, no Memory,
no Knowledge, no LLM integration — pure data manipulation only.
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Any
from uuid import UUID, uuid4

from core.memory.runtime import MemoryRecord


# ------------------------------------------------------------------
# ConversationMessage
# ------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class ConversationMessage:
    """A single message in a conversation session.

    Attributes:
        message_id: Unique identifier for the message.
        role: Who sent the message (e.g. "user", "assistant", "system").
        content: The message body text.
        timestamp: Unix timestamp of when the message was created.
        metadata: Optional extra data associated with the message.
    """

    message_id: UUID
    role: str
    content: str
    timestamp: float
    metadata: dict[str, Any] = field(default_factory=dict)

    @staticmethod
    def create(
        role: str,
        content: str,
        metadata: dict[str, Any] | None = None,
    ) -> ConversationMessage:
        """Factory that auto-generates message_id and timestamp."""
        return ConversationMessage(
            message_id=uuid4(),
            role=role,
            content=content,
            timestamp=time.time(),
            metadata=dict(metadata) if metadata else {},
        )


# ------------------------------------------------------------------
# ConversationSession
# ------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class ConversationSession:
    """An immutable conversation session.

    Every mutation returns a new instance. Messages are stored in
    a tuple to guarantee immutability and ordering.

    Attributes:
        session_id: Unique identifier for the session.
        participant_id: Identifier of the participant (employee, system).
        created_at: Unix timestamp of session creation.
        updated_at: Unix timestamp of last update.
        messages: Ordered tuple of ConversationMessage.
        metadata: Optional extra data for the session.
    """

    session_id: UUID
    participant_id: str
    created_at: float
    updated_at: float
    messages: tuple[ConversationMessage, ...] = ()
    metadata: dict[str, Any] = field(default_factory=dict)

    @staticmethod
    def create(
        participant_id: str,
        metadata: dict[str, Any] | None = None,
    ) -> ConversationSession:
        """Factory that auto-generates session_id and timestamps."""
        now = time.time()
        return ConversationSession(
            session_id=uuid4(),
            participant_id=participant_id,
            created_at=now,
            updated_at=now,
            messages=(),
            metadata=dict(metadata) if metadata else {},
        )

    def add_message(self, message: ConversationMessage) -> ConversationSession:
        """Return a new session with the given message appended.

        The original session is not modified (immutable).
        """
        return ConversationSession(
            session_id=self.session_id,
            participant_id=self.participant_id,
            created_at=self.created_at,
            updated_at=time.time(),
            messages=self.messages + (message,),
            metadata=dict(self.metadata),
        )

    def update_metadata(self, new_metadata: dict[str, Any]) -> ConversationSession:
        """Return a new session with merged metadata.

        The original session is not modified (immutable).
        """
        merged = dict(self.metadata)
        merged.update(new_metadata)
        return ConversationSession(
            session_id=self.session_id,
            participant_id=self.participant_id,
            created_at=self.created_at,
            updated_at=time.time(),
            messages=self.messages,
            metadata=merged,
        )


# ------------------------------------------------------------------
# ConversationContext
# ------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class ConversationContext:
    """Immutable context wrapping a session and current execution state.

    Attributes:
        session: The active conversation session.
        current_task: Snapshot of the current task (Any for decoupling).
        current_employee: Snapshot of the current employee (Any).
        current_company: Snapshot of the company (Any).
        metadata: Optional extra context data.
    """

    session: ConversationSession
    current_task: Any = None
    current_employee: Any = None
    current_company: Any = None
    metadata: dict[str, Any] = field(default_factory=dict)


# ------------------------------------------------------------------
# ConversationTrace
# ------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class ConversationTrace:
    """Execution trace for conversation operations.

    Attributes:
        stages: List of stage names executed.
        timestamps: Dict mapping stage name to Unix timestamp.
        message_count: Number of messages in the session.
        token_estimate: Estimated token count for the session content.
    """

    stages: list[str] = field(default_factory=list)
    timestamps: dict[str, float] = field(default_factory=dict)
    message_count: int = 0
    token_estimate: int = 0


# ------------------------------------------------------------------
# ConversationResult
# ------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class ConversationResult:
    """Outcome of a conversation runtime operation.

    Attributes:
        success: True if the operation completed without errors.
        updated_session: The session after the operation (new instance).
        trace: Execution trace with timing and stats.
        error_message: Human-readable error description (empty on success).
    """

    success: bool
    updated_session: ConversationSession
    trace: ConversationTrace
    error_message: str = ""


# ------------------------------------------------------------------
# ConversationRuntime
# ------------------------------------------------------------------


class ConversationRuntime:
    """Stateless runtime for conversation session management.

    All methods are deterministic pure functions — they take inputs
    and return outputs without mutating any internal state.
    """

    @staticmethod
    def create_session(
        participant_id: str,
        metadata: dict[str, Any] | None = None,
    ) -> ConversationSession:
        """Create a new empty conversation session.

        Args:
            participant_id: Identifier of the participant.
            metadata: Optional session metadata.

        Returns:
            A new ConversationSession with no messages.
        """
        return ConversationSession.create(
            participant_id=participant_id,
            metadata=metadata,
        )

    @staticmethod
    def append_message(
        session: ConversationSession,
        role: str,
        content: str,
        metadata: dict[str, Any] | None = None,
    ) -> ConversationSession:
        """Return a new session with a message appended.

        Args:
            session: The current session (not modified).
            role: Message role ("user", "assistant", "system").
            content: Message body text.
            metadata: Optional message metadata.

        Returns:
            A new ConversationSession with the message added.
        """
        message = ConversationMessage.create(
            role=role,
            content=content,
            metadata=metadata,
        )
        return session.add_message(message)

    @staticmethod
    def build_context(
        session: ConversationSession,
        current_task: Any = None,
        current_employee: Any = None,
        current_company: Any = None,
        metadata: dict[str, Any] | None = None,
    ) -> ConversationContext:
        """Wrap a session into a ConversationContext with execution state.

        Args:
            session: The active session.
            current_task: Optional task snapshot.
            current_employee: Optional employee snapshot.
            current_company: Optional company snapshot.
            metadata: Optional context metadata.

        Returns:
            A new ConversationContext.
        """
        return ConversationContext(
            session=session,
            current_task=current_task,
            current_employee=current_employee,
            current_company=current_company,
            metadata=dict(metadata) if metadata else {},
        )

    @staticmethod
    def estimate_tokens(text: str) -> int:
        """Rough token estimate based on character count.

        Uses a conservative ratio of ~4 characters per token.
        This is a deterministic approximation — no Tokenizer dependency.

        Args:
            text: The text to estimate.

        Returns:
            Estimated token count (always >= 0).
        """
        return max(1, len(text) // 4)

    @staticmethod
    def estimate_session_tokens(session: ConversationSession) -> int:
        """Estimate total tokens for all messages in a session.

        Args:
            session: The session to estimate.

        Returns:
            Estimated total token count.
        """
        total = 0
        for msg in session.messages:
            total += ConversationRuntime.estimate_tokens(msg.content)
        return total

    @staticmethod
    def create_memory_record(
        session: ConversationSession,
        message: ConversationMessage,
    ) -> MemoryRecord:
        """Create a MemoryRecord from a conversation message.

        This is the bridge between Conversation Runtime and Memory Runtime:
        every message in a conversation can be recorded as an immutable
        memory record for future querying and analysis.

        Args:
            session: The session the message belongs to.
            message: The message to record.

        Returns:
            A new MemoryRecord with source='conversation' and
            category='conversation_message'.
        """
        return MemoryRecord.create_with_timestamp(
            source="conversation",
            category="conversation_message",
            content=message.content,
            timestamp=message.timestamp,
            metadata={
                "session_id": str(session.session_id),
                "message_id": str(message.message_id),
                "role": message.role,
                "participant_id": session.participant_id,
            },
        )

    @staticmethod
    def build_result(
        session: ConversationSession,
        stages: list[str],
        timestamps: dict[str, float],
        success: bool = True,
        error_message: str = "",
    ) -> ConversationResult:
        """Assemble a ConversationResult from operation data.

        Args:
            session: The (possibly updated) session.
            stages: List of stage names executed.
            timestamps: Dict of stage timestamps.
            success: Whether the operation succeeded.
            error_message: Error description (empty on success).

        Returns:
            A new ConversationResult.
        """
        trace = ConversationTrace(
            stages=list(stages),
            timestamps=dict(timestamps),
            message_count=len(session.messages),
            token_estimate=ConversationRuntime.estimate_session_tokens(session),
        )
        return ConversationResult(
            success=success,
            updated_session=session,
            trace=trace,
            error_message=error_message,
        )
