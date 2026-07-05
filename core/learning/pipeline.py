"""Stateless learning pipeline -- automated Conversation -> Skills coordination.

Orchestrates the full deterministic pipeline without modifying any existing runtime.
No AI, no inference, no database, no observability.

Event integration is optional -- no EventBus, no events.
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Any

from core.conversation import ConversationRuntime, ConversationSession
from core.events.bus import EventBus
from core.events.domain_events import (
    ConversationCreated,
    KnowledgePromoted,
    MemoryRecordCreated,
    MessageAdded,
    RecommendationCreated,
)
from core.knowledge.foundation import KnowledgeRuntime as FoundationKnowledgeRuntime, KnowledgeSnapshot
from core.learning.foundation import LearningRuntime as FoundationLearningRuntime, LearningSnapshot
from core.memory import MemoryRuntime, MemorySnapshot
from core.skills.foundation import SkillRuntime as FoundationSkillRuntime, SkillSnapshot


# ------------------------------------------------------------------
# PipelineTrace
# ------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class PipelineTrace:
    """Execution trace for the full learning pipeline.

    Attributes:
        stages: Ordered list of stage names executed.
        memory_records_count: Number of memory records created.
        knowledge_records_count: Number of knowledge records promoted.
        recommendations_count: Number of learning recommendations generated.
        skills_created_count: Number of foundation skills created.
        skills_promoted_count: Number of runtime skills promoted.
        timestamps: Dict mapping stage name to Unix timestamp.
        duration_ms: Total pipeline execution time in milliseconds.
    """

    stages: tuple[str, ...] = ()
    memory_records_count: int = 0
    knowledge_records_count: int = 0
    recommendations_count: int = 0
    skills_created_count: int = 0
    skills_promoted_count: int = 0
    timestamps: dict[str, float] = field(default_factory=dict)
    duration_ms: float = 0.0


# ------------------------------------------------------------------
# PipelineResult
# ------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class PipelineResult:
    """Outcome of a full LearningPipeline execution.

    Attributes:
        success: True if all stages completed without errors.
        trace: PipelineTrace with execution details.
        knowledge_snapshot: KnowledgeSnapshot after memory promotion.
        learning_snapshot: LearningSnapshot after knowledge promotion.
        skill_snapshot: SkillSnapshot after learning promotion.
        runtime_skill_snapshots: List of SkillRuntimeSnapshot from stateful runtime.
        error_message: Human-readable error description (empty on success).
    """

    success: bool
    trace: PipelineTrace
    knowledge_snapshot: KnowledgeSnapshot | None = None
    learning_snapshot: LearningSnapshot | None = None
    skill_snapshot: SkillSnapshot | None = None
    runtime_skill_snapshots: list[Any] | None = None
    error_message: str = ""


# ------------------------------------------------------------------
# LearningPipeline
# ------------------------------------------------------------------


class LearningPipeline:
    """Stateless coordinator for the automated Conversation -> Skills pipeline.

    All methods are @staticmethod pure functions. The pipeline never mutates
    any runtime state and never uses AI.

    Dependencies are unidirectional: the pipeline imports runtimes,
    but no runtime imports the pipeline.
    """

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    @staticmethod
    def run(
        session: ConversationSession,
        skill_runtime: Any | None = None,
        event_bus: EventBus | None = None,
    ) -> PipelineResult:
        """Execute the full Conversation -> Skills pipeline.

        Args:
            session: A ConversationSession containing messages to process.
            skill_runtime: Optional stateful SkillRuntime instance for
                          promoting foundation skills into runtime snapshots.
            event_bus: Optional EventBus for publishing pipeline events.

        Returns:
            A PipelineResult with all intermediate and final snapshots.
        """
        timestamps: dict[str, float] = {}
        stages: list[str] = []
        start = time.perf_counter()

        def _pub(e: Any) -> None:
            if event_bus is not None:
                event_bus.publish(e)

        try:
            ts = time.time()

            # Stage 1: Conversation -> Memory
            stages.append("conversation_to_memory")
            timestamps["conversation_to_memory"] = ts
            mem_records = [
                ConversationRuntime.create_memory_record(session, msg)
                for msg in session.messages
            ]
            mem_snap = MemoryRuntime.create_snapshot(mem_records)
            mem_count = len(mem_snap.records)

            for msg in session.messages:
                _pub(MessageAdded(
                    session_id=session.session_id,
                    message_id=msg.message_id,
                    role=msg.role,
                    timestamp=msg.timestamp,
                ))

            for rec in mem_snap.records:
                _pub(MemoryRecordCreated(
                    memory_id=rec.memory_id,
                    source=rec.source,
                    category=rec.category,
                    timestamp=rec.timestamp,
                ))

            # Stage 2: Memory -> Knowledge
            stages.append("memory_to_knowledge")
            ts = time.time()
            timestamps["memory_to_knowledge"] = ts
            know_snap: KnowledgeSnapshot = MemoryRuntime.promote_snapshot(mem_snap)
            know_count = len(know_snap.records)

            for kr in know_snap.records:
                _pub(KnowledgePromoted(
                    knowledge_id=kr.knowledge_id,
                    source="memory",
                    records_count=1,
                    timestamp=ts,
                ))

            # Stage 3: Knowledge -> Learning
            stages.append("knowledge_to_learning")
            ts = time.time()
            timestamps["knowledge_to_learning"] = ts
            learn_snap: LearningSnapshot = FoundationLearningRuntime.promote_snapshot(know_snap)
            learn_count = len(learn_snap.recommendations)

            for rec in learn_snap.recommendations:
                _pub(RecommendationCreated(
                    recommendation_id=rec.recommendation_id,
                    knowledge_id=rec.knowledge_id,
                    title=rec.title,
                    timestamp=rec.timestamp,
                ))

            # Stage 4: Learning -> Skill Foundation
            stages.append("learning_to_skill_foundation")
            ts = time.time()
            timestamps["learning_to_skill_foundation"] = ts
            skill_snap: SkillSnapshot = FoundationSkillRuntime.promote_snapshot(learn_snap)
            skill_count = len(skill_snap.skills)

            # Stage 5: Skill Foundation -> Skill Runtime (optional)
            runtime_skills: list[Any] = []
            if skill_runtime is not None:
                stages.append("skill_foundation_to_runtime")
                ts = time.time()
                timestamps["skill_foundation_to_runtime"] = ts
                runtime_skills = skill_runtime.promote_snapshot(skill_snap)

            duration = (time.perf_counter() - start) * 1000.0

            trace = PipelineTrace(
                stages=tuple(stages),
                memory_records_count=mem_count,
                knowledge_records_count=know_count,
                recommendations_count=learn_count,
                skills_created_count=skill_count,
                skills_promoted_count=len(runtime_skills),
                timestamps=dict(timestamps),
                duration_ms=duration,
            )

            return PipelineResult(
                success=True,
                trace=trace,
                knowledge_snapshot=know_snap,
                learning_snapshot=learn_snap,
                skill_snapshot=skill_snap,
                runtime_skill_snapshots=runtime_skills if runtime_skills else None,
                error_message="",
            )

        except Exception as exc:
            duration = (time.perf_counter() - start) * 1000.0
            trace = PipelineTrace(
                stages=tuple(stages),
                timestamps=dict(timestamps),
                duration_ms=duration,
            )
            return PipelineResult(
                success=False,
                trace=trace,
                error_message=f"Pipeline failed at stage '{stages[-1] if stages else 'start'}': {exc}",
            )

    @staticmethod
    def run_from_messages(
        participant_id: str,
        messages: list[tuple[str, str]],
        skill_runtime: Any | None = None,
        event_bus: EventBus | None = None,
    ) -> PipelineResult:
        """Create a session from raw messages and run the pipeline.

        Args:
            participant_id: The participant identifier for the session.
            messages: List of (role, content) tuples.
            skill_runtime: Optional stateful SkillRuntime instance.
            event_bus: Optional EventBus for publishing pipeline events.

        Returns:
            A PipelineResult with all intermediate and final snapshots.
        """
        session = ConversationRuntime.create_session(participant_id)
        if event_bus is not None:
            event_bus.publish(ConversationCreated(
                session_id=session.session_id,
                participant_id=participant_id,
                timestamp=session.created_at,
            ))
        for role, content in messages:
            session = ConversationRuntime.append_message(session, role, content)
        return LearningPipeline.run(session, skill_runtime=skill_runtime, event_bus=event_bus)

    @staticmethod
    def run_from_session_id(
        participant_id: str,
        skill_runtime: Any | None = None,
        event_bus: EventBus | None = None,
    ) -> PipelineResult:
        """Run the pipeline with an empty session (no messages).

        Useful for validating the pipeline handles empty input gracefully.

        Args:
            participant_id: The participant identifier for the session.
            skill_runtime: Optional stateful SkillRuntime instance.
            event_bus: Optional EventBus for publishing pipeline events.

        Returns:
            A PipelineResult with empty but valid snapshots.
        """
        session = ConversationRuntime.create_session(participant_id)
        if event_bus is not None:
            event_bus.publish(ConversationCreated(
                session_id=session.session_id,
                participant_id=participant_id,
                timestamp=session.created_at,
            ))
        return LearningPipeline.run(session, skill_runtime=skill_runtime, event_bus=event_bus)
