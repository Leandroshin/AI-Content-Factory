"""Foundation runtime for the Knowledge Runtime.

Stateless, deterministic knowledge record manager.
No IO, no async, no threads, no database, no embeddings,
no semantic search, no AI — pure data manipulation only.
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Any
from uuid import UUID, uuid4

from core.memory.runtime import MemoryRecord


# ------------------------------------------------------------------
# KnowledgeRecord
# ------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class KnowledgeRecord:
    """A single immutable knowledge record.

    Attributes:
        knowledge_id: Unique identifier for this record.
        source: Origin component (e.g. "conversation", "execution").
        title: Human-readable title.
        content: Record body content as plain text.
        metadata: Optional extra data associated with the record.
        confidence: Confidence score between 0.0 and 1.0.
        timestamp: Unix timestamp of when the record was created.
    """

    knowledge_id: UUID
    source: str
    title: str
    content: str
    metadata: dict[str, Any] = field(default_factory=dict)
    confidence: float = 1.0
    timestamp: float = 0.0

    @staticmethod
    def create(
        source: str,
        title: str,
        content: str,
        metadata: dict[str, Any] | None = None,
        confidence: float = 1.0,
    ) -> KnowledgeRecord:
        """Factory that auto-generates knowledge_id and timestamp."""
        return KnowledgeRecord(
            knowledge_id=uuid4(),
            source=source,
            title=title,
            content=content,
            metadata=dict(metadata) if metadata else {},
            confidence=confidence,
            timestamp=time.time(),
        )

    @staticmethod
    def create_with_timestamp(
        source: str,
        title: str,
        content: str,
        timestamp: float,
        metadata: dict[str, Any] | None = None,
        confidence: float = 1.0,
    ) -> KnowledgeRecord:
        """Factory with an explicit timestamp (for determinism in tests)."""
        return KnowledgeRecord(
            knowledge_id=uuid4(),
            source=source,
            title=title,
            content=content,
            metadata=dict(metadata) if metadata else {},
            confidence=confidence,
            timestamp=timestamp,
        )


# ------------------------------------------------------------------
# KnowledgeSnapshot
# ------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class KnowledgeSnapshot:
    """An immutable point-in-time view of knowledge records.

    Attributes:
        records: Ordered tuple of KnowledgeRecord instances.
        created_at: Unix timestamp of snapshot creation.
    """

    records: tuple[KnowledgeRecord, ...] = ()
    created_at: float = 0.0


# ------------------------------------------------------------------
# KnowledgeTrace
# ------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class KnowledgeTrace:
    """Execution trace for knowledge operations.

    Attributes:
        operations: List of operation names executed.
        timestamps: Dict mapping operation name to Unix timestamp.
        promoted_records: Number of records promoted during the operation.
    """

    operations: list[str] = field(default_factory=list)
    timestamps: dict[str, float] = field(default_factory=dict)
    promoted_records: int = 0


# ------------------------------------------------------------------
# KnowledgeResult
# ------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class KnowledgeResult:
    """Outcome of a knowledge runtime operation.

    Attributes:
        success: True if the operation completed without errors.
        snapshot: The snapshot after the operation (new instance).
        trace: Execution trace with operations and timing.
        error_message: Human-readable error description (empty on success).
    """

    success: bool
    snapshot: KnowledgeSnapshot
    trace: KnowledgeTrace
    error_message: str = ""


# ------------------------------------------------------------------
# KnowledgeRuntime
# ------------------------------------------------------------------


class KnowledgeRuntime:
    """Stateless runtime for knowledge record management.

    All methods are deterministic pure functions — they take inputs
    and return outputs without mutating any internal state.
    """

    @staticmethod
    def create_snapshot(
        records: tuple[KnowledgeRecord, ...] | list[KnowledgeRecord] | None = None,
    ) -> KnowledgeSnapshot:
        """Create a new snapshot with the given records.

        Args:
            records: Optional initial records. An empty tuple is used
                     when None is provided.

        Returns:
            A new KnowledgeSnapshot.
        """
        if records is None:
            records = ()
        return KnowledgeSnapshot(
            records=tuple(records),
            created_at=time.time(),
        )

    @staticmethod
    def append_record(
        snapshot: KnowledgeSnapshot,
        record: KnowledgeRecord,
    ) -> KnowledgeSnapshot:
        """Return a new snapshot with the record appended.

        The original snapshot is not modified (immutable).

        Args:
            snapshot: The current snapshot.
            record: The KnowledgeRecord to append.

        Returns:
            A new KnowledgeSnapshot with the record added.
        """
        return KnowledgeSnapshot(
            records=snapshot.records + (record,),
            created_at=time.time(),
        )

    @staticmethod
    def promote_memory_record(
        memory_record: MemoryRecord,
        title: str | None = None,
    ) -> KnowledgeRecord:
        """Promote a MemoryRecord to a KnowledgeRecord deterministically.

        This is the bridge between Memory Runtime and Knowledge Runtime:
        a raw memory event is promoted to a validated knowledge record
        with a confidence score.

        Args:
            memory_record: The MemoryRecord to promote.
            title: Optional title override. Defaults to 'Memory Promotion'.

        Returns:
            A new KnowledgeRecord with source, content and timestamp
            carried over from the MemoryRecord.
        """
        return KnowledgeRecord.create(
            source=memory_record.source,
            title=title or "Memory Promotion",
            content=memory_record.content,
            metadata=dict(memory_record.metadata),
            confidence=1.0,
        )

    @staticmethod
    def filter_by_source(
        snapshot: KnowledgeSnapshot,
        source: str,
    ) -> tuple[KnowledgeRecord, ...]:
        """Filter records in the snapshot by source.

        Args:
            snapshot: The snapshot to filter.
            source: Source string to match (case-sensitive).

        Returns:
            A tuple of matching KnowledgeRecord instances.
        """
        return tuple(r for r in snapshot.records if r.source == source)

    @staticmethod
    def filter_by_confidence(
        snapshot: KnowledgeSnapshot,
        min_confidence: float = 0.0,
        max_confidence: float = 1.0,
    ) -> tuple[KnowledgeRecord, ...]:
        """Filter records in the snapshot by confidence range.

        Args:
            snapshot: The snapshot to filter.
            min_confidence: Minimum confidence (inclusive).
            max_confidence: Maximum confidence (inclusive).

        Returns:
            A tuple of matching KnowledgeRecord instances.
        """
        return tuple(
            r for r in snapshot.records
            if min_confidence <= r.confidence <= max_confidence
        )

    @staticmethod
    def build_result(
        snapshot: KnowledgeSnapshot,
        operations: list[str],
        timestamps: dict[str, float],
        success: bool = True,
        error_message: str = "",
    ) -> KnowledgeResult:
        """Assemble a KnowledgeResult from operation data.

        Args:
            snapshot: The snapshot after the operation.
            operations: List of operation names executed.
            timestamps: Dict of operation timestamps.
            success: Whether the operation succeeded.
            error_message: Error description (empty on success).

        Returns:
            A new KnowledgeResult.
        """
        trace = KnowledgeTrace(
            operations=list(operations),
            timestamps=dict(timestamps),
            promoted_records=len(snapshot.records),
        )
        return KnowledgeResult(
            success=success,
            snapshot=snapshot,
            trace=trace,
            error_message=error_message,
        )
