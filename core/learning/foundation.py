"""Foundation runtime for the Learning Runtime.

Stateless, deterministic learning recommendation manager.
No IO, no async, no threads, no database, no AI, no inference,
no semantic analysis — pure data manipulation only.
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Any
from uuid import UUID, uuid4

from core.knowledge.foundation import KnowledgeRecord, KnowledgeSnapshot


# ------------------------------------------------------------------
# LearningRecommendation
# ------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class LearningRecommendation:
    """A single immutable learning recommendation.

    Attributes:
        recommendation_id: Unique identifier for this recommendation.
        knowledge_id: The knowledge record that originated this recommendation.
        recommendation_type: Type of recommendation (e.g. "study", "review", "practice").
        title: Human-readable title.
        description: Detailed description of the recommendation.
        priority: Priority level (higher = more important).
        timestamp: Unix timestamp of when the recommendation was created.
    """

    recommendation_id: UUID
    knowledge_id: UUID
    recommendation_type: str
    title: str
    description: str
    priority: int
    timestamp: float

    @staticmethod
    def create(
        knowledge_id: UUID,
        recommendation_type: str,
        title: str,
        description: str,
        priority: int = 1,
    ) -> LearningRecommendation:
        """Factory that auto-generates recommendation_id and timestamp."""
        return LearningRecommendation(
            recommendation_id=uuid4(),
            knowledge_id=knowledge_id,
            recommendation_type=recommendation_type,
            title=title,
            description=description,
            priority=priority,
            timestamp=time.time(),
        )

    @staticmethod
    def create_with_timestamp(
        knowledge_id: UUID,
        recommendation_type: str,
        title: str,
        description: str,
        timestamp: float,
        priority: int = 1,
    ) -> LearningRecommendation:
        """Factory with an explicit timestamp (for determinism in tests)."""
        return LearningRecommendation(
            recommendation_id=uuid4(),
            knowledge_id=knowledge_id,
            recommendation_type=recommendation_type,
            title=title,
            description=description,
            priority=priority,
            timestamp=timestamp,
        )


# ------------------------------------------------------------------
# LearningSnapshot
# ------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class LearningSnapshot:
    """An immutable point-in-time view of learning recommendations.

    Attributes:
        recommendations: Ordered tuple of LearningRecommendation instances.
        created_at: Unix timestamp of snapshot creation.
    """

    recommendations: tuple[LearningRecommendation, ...] = ()
    created_at: float = 0.0


# ------------------------------------------------------------------
# LearningTrace
# ------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class LearningTrace:
    """Execution trace for learning operations.

    Attributes:
        promoted_knowledge: Number of knowledge records promoted.
        recommendations_created: Number of recommendations created.
        timestamps: Dict mapping operation name to Unix timestamp.
    """

    promoted_knowledge: int = 0
    recommendations_created: int = 0
    timestamps: dict[str, float] = field(default_factory=dict)


# ------------------------------------------------------------------
# LearningResult
# ------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class LearningResult:
    """Outcome of a learning runtime operation.

    Attributes:
        success: True if the operation completed without errors.
        snapshot: The snapshot after the operation (new instance).
        trace: Execution trace with operations and timing.
        error_message: Human-readable error description (empty on success).
    """

    success: bool
    snapshot: LearningSnapshot
    trace: LearningTrace
    error_message: str = ""


# ------------------------------------------------------------------
# LearningRuntime
# ------------------------------------------------------------------


class LearningRuntime:
    """Stateless runtime for learning recommendation management.

    All methods are deterministic pure functions — they take inputs
    and return outputs without mutating any internal state.
    """

    @staticmethod
    def create_snapshot(
        recommendations: tuple[LearningRecommendation, ...] | list[LearningRecommendation] | None = None,
    ) -> LearningSnapshot:
        """Create a new snapshot with the given recommendations.

        Args:
            recommendations: Optional initial recommendations.

        Returns:
            A new LearningSnapshot.
        """
        if recommendations is None:
            recommendations = ()
        return LearningSnapshot(
            recommendations=tuple(recommendations),
            created_at=time.time(),
        )

    @staticmethod
    def append_recommendation(
        snapshot: LearningSnapshot,
        recommendation: LearningRecommendation,
    ) -> LearningSnapshot:
        """Return a new snapshot with the recommendation appended.

        The original snapshot is not modified (immutable).

        Args:
            snapshot: The current snapshot.
            recommendation: The LearningRecommendation to append.

        Returns:
            A new LearningSnapshot with the recommendation added.
        """
        return LearningSnapshot(
            recommendations=snapshot.recommendations + (recommendation,),
            created_at=time.time(),
        )

    @staticmethod
    def promote_knowledge(
        knowledge_record: KnowledgeRecord,
    ) -> LearningRecommendation:
        """Promote a KnowledgeRecord to a LearningRecommendation.

        This is the bridge between Knowledge Runtime and Learning Runtime:
        a validated knowledge record becomes a study recommendation.

        Args:
            knowledge_record: The KnowledgeRecord to promote.

        Returns:
            A LearningRecommendation with type='study' and priority=1.
        """
        return LearningRecommendation.create(
            knowledge_id=knowledge_record.knowledge_id,
            recommendation_type="study",
            title=knowledge_record.title,
            description=knowledge_record.content,
            priority=1,
        )

    @staticmethod
    def promote_snapshot(
        knowledge_snapshot: KnowledgeSnapshot,
    ) -> LearningSnapshot:
        """Promote an entire KnowledgeSnapshot to a LearningSnapshot.

        Args:
            knowledge_snapshot: The knowledge snapshot to promote.

        Returns:
            A new LearningSnapshot with all records promoted.
        """
        recommendations: list[LearningRecommendation] = []
        for kr in knowledge_snapshot.records:
            recommendations.append(
                LearningRuntime.promote_knowledge(kr),
            )
        return LearningRuntime.create_snapshot(recommendations)

    @staticmethod
    def filter_by_priority(
        snapshot: LearningSnapshot,
        min_priority: int = 0,
        max_priority: int = 10,
    ) -> tuple[LearningRecommendation, ...]:
        """Filter recommendations in the snapshot by priority range.

        Args:
            snapshot: The snapshot to filter.
            min_priority: Minimum priority (inclusive).
            max_priority: Maximum priority (inclusive).

        Returns:
            A tuple of matching LearningRecommendation instances.
        """
        return tuple(
            r for r in snapshot.recommendations
            if min_priority <= r.priority <= max_priority
        )

    @staticmethod
    def build_result(
        snapshot: LearningSnapshot,
        timestamps: dict[str, float],
        success: bool = True,
        error_message: str = "",
    ) -> LearningResult:
        """Assemble a LearningResult from operation data.

        Args:
            snapshot: The snapshot after the operation.
            timestamps: Dict of operation timestamps.
            success: Whether the operation succeeded.
            error_message: Error description (empty on success).

        Returns:
            A new LearningResult.
        """
        trace = LearningTrace(
            promoted_knowledge=len(snapshot.recommendations),
            recommendations_created=len(snapshot.recommendations),
            timestamps=dict(timestamps),
        )
        return LearningResult(
            success=success,
            snapshot=snapshot,
            trace=trace,
            error_message=error_message,
        )
