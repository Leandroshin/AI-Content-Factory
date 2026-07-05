"""Foundation runtime for the Skill Runtime.

Stateless, deterministic skill record manager.
No IO, no async, no threads, no database, no AI, no inference,
no semantic analysis — pure data manipulation only.
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Any, TYPE_CHECKING
from uuid import UUID, uuid4

if TYPE_CHECKING:
    from core.learning.foundation import LearningRecommendation, LearningSnapshot


# ------------------------------------------------------------------
# SkillRecord
# ------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class SkillRecord:
    """A single immutable skill record.

    Attributes:
        skill_id: Unique identifier for this skill record.
        recommendation_id: The learning recommendation that originated this skill.
        skill_name: Human-readable skill name.
        description: Detailed description of the skill.
        level: Proficiency level (1 = initial).
        experience_points: Accumulated experience points (0 = initial).
        created_at: Unix timestamp of when the record was created.
        metadata: Optional extra data associated with the record.
    """

    skill_id: UUID
    recommendation_id: UUID
    skill_name: str
    description: str
    level: int = 1
    experience_points: int = 0
    created_at: float = 0.0
    metadata: dict[str, Any] = field(default_factory=dict)

    @staticmethod
    def create(
        recommendation_id: UUID,
        skill_name: str,
        description: str,
        level: int = 1,
        experience_points: int = 0,
        metadata: dict[str, Any] | None = None,
    ) -> SkillRecord:
        """Factory that auto-generates skill_id and created_at."""
        return SkillRecord(
            skill_id=uuid4(),
            recommendation_id=recommendation_id,
            skill_name=skill_name,
            description=description,
            level=level,
            experience_points=experience_points,
            created_at=time.time(),
            metadata=dict(metadata) if metadata else {},
        )

    @staticmethod
    def create_with_timestamp(
        recommendation_id: UUID,
        skill_name: str,
        description: str,
        created_at: float,
        level: int = 1,
        experience_points: int = 0,
        metadata: dict[str, Any] | None = None,
    ) -> SkillRecord:
        """Factory with an explicit timestamp (for determinism in tests)."""
        return SkillRecord(
            skill_id=uuid4(),
            recommendation_id=recommendation_id,
            skill_name=skill_name,
            description=description,
            level=level,
            experience_points=experience_points,
            created_at=created_at,
            metadata=dict(metadata) if metadata else {},
        )


# ------------------------------------------------------------------
# SkillSnapshot
# ------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class SkillSnapshot:
    """An immutable point-in-time view of skill records.

    Attributes:
        skills: Ordered tuple of SkillRecord instances.
        created_at: Unix timestamp of snapshot creation.
    """

    skills: tuple[SkillRecord, ...] = ()
    created_at: float = 0.0


# ------------------------------------------------------------------
# SkillTrace
# ------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class SkillTrace:
    """Execution trace for skill operations.

    Attributes:
        recommendations_processed: Number of recommendations processed.
        skills_created: Number of skills created.
        timestamps: Dict mapping operation name to Unix timestamp.
    """

    recommendations_processed: int = 0
    skills_created: int = 0
    timestamps: dict[str, float] = field(default_factory=dict)


# ------------------------------------------------------------------
# SkillResult
# ------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class SkillResult:
    """Outcome of a skill runtime operation.

    Attributes:
        success: True if the operation completed without errors.
        snapshot: The snapshot after the operation (new instance).
        trace: Execution trace with operations and timing.
        error_message: Human-readable error description (empty on success).
    """

    success: bool
    snapshot: SkillSnapshot
    trace: SkillTrace
    error_message: str = ""


# ------------------------------------------------------------------
# SkillRuntime
# ------------------------------------------------------------------


class SkillRuntime:
    """Stateless runtime for skill record management.

    All methods are deterministic pure functions — they take inputs
    and return outputs without mutating any internal state.
    """

    @staticmethod
    def create_snapshot(
        skills: tuple[SkillRecord, ...] | list[SkillRecord] | None = None,
    ) -> SkillSnapshot:
        """Create a new snapshot with the given skills.

        Args:
            skills: Optional initial skills. An empty tuple is used
                    when None is provided.

        Returns:
            A new SkillSnapshot.
        """
        if skills is None:
            skills = ()
        return SkillSnapshot(
            skills=tuple(skills),
            created_at=time.time(),
        )

    @staticmethod
    def append_skill(
        snapshot: SkillSnapshot,
        skill: SkillRecord,
    ) -> SkillSnapshot:
        """Return a new snapshot with the skill appended.

        The original snapshot is not modified (immutable).

        Args:
            snapshot: The current snapshot.
            skill: The SkillRecord to append.

        Returns:
            A new SkillSnapshot with the skill added.
        """
        return SkillSnapshot(
            skills=snapshot.skills + (skill,),
            created_at=time.time(),
        )

    @staticmethod
    def promote_learning(
        recommendation: LearningRecommendation,
    ) -> SkillRecord:
        """Promote a LearningRecommendation to a SkillRecord deterministically.

        This is the bridge between Learning Runtime and Skill Runtime:
        a learning recommendation becomes a skill record with
        level=1, experience_points=0, and metadata={}.

        No AI, no inference, no automatic evolution — pure deterministic
        transformation only.

        Args:
            recommendation: The LearningRecommendation to promote.

        Returns:
            A new SkillRecord.
        """
        return SkillRecord.create(
            recommendation_id=recommendation.recommendation_id,
            skill_name=recommendation.title,
            description=recommendation.description,
            level=1,
            experience_points=0,
            metadata={},
        )

    @staticmethod
    def promote_snapshot(
        learning_snapshot: LearningSnapshot,
    ) -> SkillSnapshot:
        """Promote an entire LearningSnapshot to a SkillSnapshot.

        Args:
            learning_snapshot: The learning snapshot to promote.

        Returns:
            A new SkillSnapshot with all recommendations promoted.
        """
        skills: list[SkillRecord] = []
        for rec in learning_snapshot.recommendations:
            skills.append(SkillRuntime.promote_learning(rec))
        return SkillRuntime.create_snapshot(skills)

    @staticmethod
    def filter_by_level(
        snapshot: SkillSnapshot,
        min_level: int = 1,
        max_level: int = 10,
    ) -> tuple[SkillRecord, ...]:
        """Filter skills in the snapshot by level range.

        Args:
            snapshot: The snapshot to filter.
            min_level: Minimum level (inclusive).
            max_level: Maximum level (inclusive).

        Returns:
            A tuple of matching SkillRecord instances.
        """
        return tuple(
            s for s in snapshot.skills
            if min_level <= s.level <= max_level
        )

    @staticmethod
    def build_result(
        snapshot: SkillSnapshot,
        timestamps: dict[str, float],
        success: bool = True,
        error_message: str = "",
    ) -> SkillResult:
        """Assemble a SkillResult from operation data.

        Args:
            snapshot: The snapshot after the operation.
            timestamps: Dict of operation timestamps.
            success: Whether the operation succeeded.
            error_message: Error description (empty on success).

        Returns:
            A new SkillResult.
        """
        trace = SkillTrace(
            recommendations_processed=len(snapshot.skills),
            skills_created=len(snapshot.skills),
            timestamps=dict(timestamps),
        )
        return SkillResult(
            success=success,
            snapshot=snapshot,
            trace=trace,
            error_message=error_message,
        )
