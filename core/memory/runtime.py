"""Foundation runtime for the Memory Runtime.

Stateless, deterministic memory record manager.
No IO, no async, no threads, no database, no vector search,
no embeddings, no persistence — pure data manipulation only.
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any
from uuid import UUID, uuid4

if TYPE_CHECKING:
    from core.knowledge.foundation import KnowledgeRecord, KnowledgeSnapshot


# ------------------------------------------------------------------
# MemoryRecord
# ------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class MemoryRecord:
    """A single immutable memory record.

    Attributes:
        memory_id: Unique identifier for this record.
        source: Origin component (e.g. "conversation", "execution").
        category: Classification category (e.g. "info", "decision", "error").
        content: Record body content as plain text.
        metadata: Optional extra data associated with the record.
        timestamp: Unix timestamp of when the record was created.
    """

    memory_id: UUID
    source: str
    category: str
    content: str
    metadata: dict[str, Any] = field(default_factory=dict)
    timestamp: float = 0.0

    @staticmethod
    def create(
        source: str,
        category: str,
        content: str,
        metadata: dict[str, Any] | None = None,
    ) -> MemoryRecord:
        """Factory that auto-generates memory_id and timestamp."""
        return MemoryRecord(
            memory_id=uuid4(),
            source=source,
            category=category,
            content=content,
            metadata=dict(metadata) if metadata else {},
            timestamp=time.time(),
        )

    @staticmethod
    def create_with_timestamp(
        source: str,
        category: str,
        content: str,
        timestamp: float,
        metadata: dict[str, Any] | None = None,
    ) -> MemoryRecord:
        """Factory with an explicit timestamp (for determinism in tests)."""
        return MemoryRecord(
            memory_id=uuid4(),
            source=source,
            category=category,
            content=content,
            metadata=dict(metadata) if metadata else {},
            timestamp=timestamp,
        )


# ------------------------------------------------------------------
# MemorySnapshot
# ------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class MemorySnapshot:
    """An immutable point-in-time view of memory records.

    Attributes:
        records: Ordered tuple of MemoryRecord instances.
        created_at: Unix timestamp of snapshot creation.
    """

    records: tuple[MemoryRecord, ...] = ()
    created_at: float = 0.0


# ------------------------------------------------------------------
# MemoryTrace
# ------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class MemoryTrace:
    """Execution trace for memory operations.

    Attributes:
        operations: List of operation names executed.
        timestamps: Dict mapping operation name to Unix timestamp.
        records_created: Number of records created during the operation.
    """

    operations: list[str] = field(default_factory=list)
    timestamps: dict[str, float] = field(default_factory=dict)
    records_created: int = 0


# ------------------------------------------------------------------
# MemoryResult
# ------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class MemoryResult:
    """Outcome of a memory runtime operation.

    Attributes:
        success: True if the operation completed without errors.
        snapshot: The snapshot after the operation (new instance).
        trace: Execution trace with operations and timing.
        error_message: Human-readable error description (empty on success).
    """

    success: bool
    snapshot: MemorySnapshot
    trace: MemoryTrace
    error_message: str = ""


# ------------------------------------------------------------------
# MemoryRuntime
# ------------------------------------------------------------------


class MemoryRuntime:
    """Stateless runtime for memory record management.

    All methods are deterministic pure functions — they take inputs
    and return outputs without mutating any internal state.
    """

    @staticmethod
    def create_snapshot(
        records: tuple[MemoryRecord, ...] | list[MemoryRecord] | None = None,
    ) -> MemorySnapshot:
        """Create a new snapshot with the given records.

        Args:
            records: Optional initial records. An empty tuple is used
                     when None is provided.

        Returns:
            A new MemorySnapshot.
        """
        if records is None:
            records = ()
        return MemorySnapshot(
            records=tuple(records),
            created_at=time.time(),
        )

    @staticmethod
    def append_record(
        snapshot: MemorySnapshot,
        record: MemoryRecord,
    ) -> MemorySnapshot:
        """Return a new snapshot with the record appended.

        The original snapshot is not modified (immutable).

        Args:
            snapshot: The current snapshot.
            record: The MemoryRecord to append.

        Returns:
            A new MemorySnapshot with the record added.
        """
        return MemorySnapshot(
            records=snapshot.records + (record,),
            created_at=time.time(),
        )

    @staticmethod
    def filter_by_category(
        snapshot: MemorySnapshot,
        category: str,
    ) -> tuple[MemoryRecord, ...]:
        """Filter records in the snapshot by category.

        Args:
            snapshot: The snapshot to filter.
            category: Category string to match (case-sensitive).

        Returns:
            A tuple of matching MemoryRecord instances.
        """
        return tuple(r for r in snapshot.records if r.category == category)

    @staticmethod
    def filter_by_source(
        snapshot: MemorySnapshot,
        source: str,
    ) -> tuple[MemoryRecord, ...]:
        """Filter records in the snapshot by source.

        Args:
            snapshot: The snapshot to filter.
            source: Source string to match (case-sensitive).

        Returns:
            A tuple of matching MemoryRecord instances.
        """
        return tuple(r for r in snapshot.records if r.source == source)

    @staticmethod
    def promote_records(
        snapshot: MemorySnapshot,
    ) -> tuple["KnowledgeRecord", ...]:
        """Promote all MemoryRecords in a snapshot to KnowledgeRecords.

        Uses FoundationKnowledgeRuntime.promote_memory_record() to
        perform a deterministic 1:1 conversion of each record.

        Args:
            snapshot: The memory snapshot containing records to promote.

        Returns:
            An immutable tuple of KnowledgeRecord instances in the
            same order as the original MemoryRecords.
        """
        from core.knowledge.foundation import KnowledgeRuntime as FoundationKR

        return tuple(
            FoundationKR.promote_memory_record(r)
            for r in snapshot.records
        )

    @staticmethod
    def promote_snapshot(
        snapshot: MemorySnapshot,
    ) -> "KnowledgeSnapshot":
        """Promote an entire MemorySnapshot to a KnowledgeSnapshot.

        This is a convenience method that calls promote_records() and
        wraps the result in a new KnowledgeSnapshot.

        Args:
            snapshot: The memory snapshot to promote.

        Returns:
            A new KnowledgeSnapshot containing the promoted records.
        """
        from core.knowledge.foundation import KnowledgeRuntime as FoundationKR

        records = MemoryRuntime.promote_records(snapshot)
        return FoundationKR.create_snapshot(records=list(records))

    @staticmethod
    def build_result(
        snapshot: MemorySnapshot,
        operations: list[str],
        timestamps: dict[str, float],
        success: bool = True,
        error_message: str = "",
    ) -> MemoryResult:
        """Assemble a MemoryResult from operation data.

        Args:
            snapshot: The snapshot after the operation.
            operations: List of operation names executed.
            timestamps: Dict of operation timestamps.
            success: Whether the operation succeeded.
            error_message: Error description (empty on success).

        Returns:
            A new MemoryResult.
        """
        trace = MemoryTrace(
            operations=list(operations),
            timestamps=dict(timestamps),
            records_created=len(snapshot.records),
        )
        return MemoryResult(
            success=success,
            snapshot=snapshot,
            trace=trace,
            error_message=error_message,
        )
