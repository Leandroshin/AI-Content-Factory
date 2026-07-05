"""Runtime for live skill lifecycle handling."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any, TYPE_CHECKING
from uuid import UUID

import time

from core.events.bus import EventBus
from core.events.domain_events import SkillLevelChanged
from core.persistence._helpers import save_if_enabled

from .foundation import SkillRecord, SkillSnapshot
from .models import Skill, SkillCapability, SkillCategory, SkillContext, SkillLevel, SkillMetadata, SkillProfile, SkillStatus

if TYPE_CHECKING:
    from core.employees import EmployeeRuntimeSnapshot
    from core.knowledge.runtime import KnowledgeRuntime
    from core.persistence.runtime import PersistenceRuntime


class SkillRuntimeState(StrEnum):
    """Runtime states for skills."""

    CREATED = "created"
    LEARNING = "learning"
    ACTIVE = "active"
    DEPRECATED = "deprecated"
    ARCHIVED = "archived"


@dataclass(frozen=True, slots=True)
class SkillStateChangedEvent:
    """Deterministic event emitted by the skill runtime."""

    skill_id: UUID
    previous_state: SkillRuntimeState
    new_state: SkillRuntimeState
    knowledge_id: UUID | None = None
    employee_id: UUID | None = None
    payload: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class SkillRuntimeSnapshot:
    """In-memory snapshot for skill lifecycle state."""

    skill_id: UUID
    name: str
    state: SkillRuntimeState = SkillRuntimeState.CREATED
    level: SkillLevel = SkillLevel.BASIC
    knowledge_id: UUID | None = None
    employee_ids: set[UUID] = field(default_factory=set)
    history: list[tuple[SkillRuntimeState, SkillRuntimeState]] = field(default_factory=list)
    skill: Skill | None = None


class SkillRuntime:
    """Deterministic in-memory runtime for skill lifecycle management."""

    _TRANSITIONS: dict[SkillRuntimeState, set[SkillRuntimeState]] = {
        SkillRuntimeState.CREATED: {SkillRuntimeState.LEARNING, SkillRuntimeState.DEPRECATED, SkillRuntimeState.ARCHIVED},
        SkillRuntimeState.LEARNING: {SkillRuntimeState.ACTIVE, SkillRuntimeState.DEPRECATED, SkillRuntimeState.ARCHIVED},
        SkillRuntimeState.ACTIVE: {SkillRuntimeState.DEPRECATED, SkillRuntimeState.ARCHIVED},
        SkillRuntimeState.DEPRECATED: {SkillRuntimeState.ARCHIVED},
        SkillRuntimeState.ARCHIVED: set(),
    }

    def __init__(self, knowledge_runtime: "KnowledgeRuntime", event_bus: EventBus | None = None, persistence_runtime: PersistenceRuntime | None = None) -> None:
        self.knowledge_runtime = knowledge_runtime
        self.event_bus = event_bus or knowledge_runtime.event_bus
        self._persistence = persistence_runtime
        self._skills: dict[UUID, SkillRuntimeSnapshot] = {}
        self._events: list[SkillStateChangedEvent] = []

    def create_from_knowledge(self, knowledge_id: UUID, *, category: SkillCategory = SkillCategory.SYSTEM, capability: SkillCapability | None = None) -> SkillRuntimeSnapshot:
        knowledge_snapshot = next((snapshot for snapshot in self.knowledge_runtime.snapshot() if snapshot.knowledge_id == knowledge_id), None)
        if knowledge_snapshot is None:
            raise KeyError(f"Knowledge {knowledge_id} is not registered in knowledge runtime.")
        if knowledge_snapshot.state not in self._knowledge_creatable_states():
            raise ValueError("Skill can only be created from accepted or published knowledge.")
        if knowledge_snapshot.entry is None:
            raise ValueError("Knowledge entry is missing.")
        skill = Skill(
            profile=SkillProfile(
                name=knowledge_snapshot.entry.metadata.title or knowledge_snapshot.entry.key,
                description=knowledge_snapshot.entry.metadata.description,
                tags=[knowledge_snapshot.knowledge_type.value, knowledge_snapshot.entry.category.value],
            ),
            category=category,
            level=SkillLevel.BASIC,
            status=SkillStatus.DRAFT,
            capabilities=[capability] if capability is not None else [],
            context=SkillContext(
                project_name=knowledge_snapshot.entry.context.project_name if knowledge_snapshot.entry.context else None,
                workspace_name=knowledge_snapshot.entry.context.project_name if knowledge_snapshot.entry.context else None,
                metadata=SkillMetadata(name="skill_from_knowledge", description="Derived from published knowledge", attributes={"knowledge_id": str(knowledge_id)}),
            ),
            metadata=SkillMetadata(name=knowledge_snapshot.entry.key, description="Skill derived from knowledge", attributes={"knowledge_id": str(knowledge_id)}),
        )
        snapshot = SkillRuntimeSnapshot(
            skill_id=skill.id,
            name=skill.profile.name or skill.id.hex,
            state=SkillRuntimeState.CREATED,
            level=skill.level,
            knowledge_id=knowledge_id,
            skill=skill,
        )
        self._skills[skill.id] = snapshot
        self._emit(skill.id, SkillRuntimeState.CREATED, SkillRuntimeState.LEARNING, knowledge_id=knowledge_id)
        snapshot.state = SkillRuntimeState.LEARNING
        skill.status = SkillStatus.DRAFT
        self._save(snapshot)
        return snapshot

    def evolve(self, skill_id: UUID, *, level: SkillLevel | None = None, state: SkillRuntimeState = SkillRuntimeState.ACTIVE) -> SkillRuntimeSnapshot:
        snapshot = self._require_skill(skill_id)
        previous_level = snapshot.level
        if level is not None:
            snapshot.level = level
            if snapshot.skill is not None:
                snapshot.skill.level = level
            if previous_level != level:
                self.event_bus.publish(SkillLevelChanged(
                    skill_id=skill_id, name=snapshot.name,
                    previous_level=previous_level.value,
                    new_level=level.value,
                    timestamp=time.time(),
                ))
        result = self.transition(skill_id, state)
        self._save(snapshot)
        return result

    def associate_employee(self, skill_id: UUID, employee_id: UUID) -> SkillRuntimeSnapshot:
        snapshot = self._require_skill(skill_id)
        snapshot.employee_ids.add(employee_id)
        self._emit(skill_id, snapshot.state, snapshot.state, knowledge_id=snapshot.knowledge_id, employee_id=employee_id)
        return snapshot

    def deprecate(self, skill_id: UUID) -> SkillRuntimeSnapshot:
        return self.transition(skill_id, SkillRuntimeState.DEPRECATED)

    def archive(self, skill_id: UUID) -> SkillRuntimeSnapshot:
        snapshot = self.transition(skill_id, SkillRuntimeState.ARCHIVED)
        if snapshot.skill is not None:
            snapshot.skill.status = SkillStatus.ARCHIVED
        return snapshot

    def transition(self, skill_id: UUID, new_state: SkillRuntimeState) -> SkillRuntimeSnapshot:
        snapshot = self._require_skill(skill_id)
        if new_state not in self._TRANSITIONS[snapshot.state]:
            raise ValueError(f"Invalid skill transition from {snapshot.state.value} to {new_state.value}.")
        previous_state = snapshot.state
        snapshot.state = new_state
        snapshot.history.append((previous_state, new_state))
        if snapshot.skill is not None:
            if new_state == SkillRuntimeState.ACTIVE:
                snapshot.skill.status = SkillStatus.ACTIVE
            elif new_state == SkillRuntimeState.DEPRECATED:
                snapshot.skill.status = SkillStatus.INACTIVE
            elif new_state == SkillRuntimeState.ARCHIVED:
                snapshot.skill.status = SkillStatus.ARCHIVED
        self._emit(skill_id, previous_state, new_state, knowledge_id=snapshot.knowledge_id)
        return snapshot

    def summary(self, skill_id: UUID) -> dict[str, Any]:
        snapshot = self._require_skill(skill_id)
        return {
            "skill_id": str(snapshot.skill_id),
            "state": snapshot.state.value,
            "level": snapshot.level.value,
            "knowledge_id": str(snapshot.knowledge_id) if snapshot.knowledge_id else None,
            "employees": [str(employee_id) for employee_id in sorted(snapshot.employee_ids, key=str)],
            "history": [(previous.value, current.value) for previous, current in snapshot.history],
        }

    def events(self) -> list[SkillStateChangedEvent]:
        return list(self._events)

    def snapshot(self) -> list[SkillRuntimeSnapshot]:
        return list(self._skills.values())

    def _save(self, snapshot: SkillRuntimeSnapshot) -> None:
        persistence = getattr(self, "_persistence", None)
        save_if_enabled(persistence, snapshot, "skill", snapshot.skill_id)

    # ------------------------------------------------------------------
    # Foundation integration: promote stateless records into stateful runtime
    # ------------------------------------------------------------------

    @staticmethod
    def _foundation_level_to_skill_level(level: int) -> SkillLevel:
        """Map foundation numeric level to runtime SkillLevel enum."""
        if level <= 1:
            return SkillLevel.BASIC
        if level == 2:
            return SkillLevel.INTERMEDIATE
        if level == 3:
            return SkillLevel.ADVANCED
        return SkillLevel.EXPERT

    def promote_record(self, foundation_record: SkillRecord) -> SkillRuntimeSnapshot:
        """Promote a Foundation SkillRecord into a stateful runtime snapshot.

        Creates a Skill model and SkillRuntimeSnapshot from the foundation record,
        registers it in the runtime, and transitions it to LEARNING state.

        Args:
            foundation_record: The SkillRecord from the foundation layer.

        Returns:
            The newly created SkillRuntimeSnapshot.
        """
        skill_level = self._foundation_level_to_skill_level(foundation_record.level)
        skill = Skill(
            profile=SkillProfile(
                name=foundation_record.skill_name,
                description=foundation_record.description,
                tags=["foundation"],
            ),
            category=SkillCategory.SYSTEM,
            level=skill_level,
            status=SkillStatus.DRAFT,
            context=SkillContext(
                metadata=SkillMetadata(
                    name=foundation_record.skill_name,
                    description=foundation_record.description,
                    attributes={
                        "recommendation_id": str(foundation_record.recommendation_id),
                        "skill_id": str(foundation_record.skill_id),
                        "experience_points": str(foundation_record.experience_points),
                        "created_at": str(foundation_record.created_at),
                        **{str(k): str(v) for k, v in foundation_record.metadata.items()},
                    },
                ),
            ),
            metadata=SkillMetadata(
                name=foundation_record.skill_name,
                description="Skill promoted from foundation",
                attributes={
                    "source": "foundation",
                    "recommendation_id": str(foundation_record.recommendation_id),
                },
            ),
        )
        snapshot = SkillRuntimeSnapshot(
            skill_id=foundation_record.skill_id,
            name=foundation_record.skill_name,
            state=SkillRuntimeState.CREATED,
            level=skill_level,
            skill=skill,
        )
        self._skills[snapshot.skill_id] = snapshot
        self._emit(
            snapshot.skill_id,
            SkillRuntimeState.CREATED,
            SkillRuntimeState.LEARNING,
        )
        snapshot.state = SkillRuntimeState.LEARNING
        skill.status = SkillStatus.DRAFT
        self._save(snapshot)
        return snapshot

    def promote_snapshot(self, foundation_snapshot: SkillSnapshot) -> list[SkillRuntimeSnapshot]:
        """Promote an entire Foundation SkillSnapshot into stateful runtime snapshots.

        Args:
            foundation_snapshot: The SkillSnapshot from the foundation layer.

        Returns:
            A list of SkillRuntimeSnapshot instances, one per SkillRecord.
        """
        return [self.promote_record(record) for record in foundation_snapshot.skills]

    def create_from_foundation(self, foundation_snapshot: SkillSnapshot) -> list[SkillRuntimeSnapshot]:
        """Create runtime snapshots from a Foundation SkillSnapshot.

        This is the canonical entry point for integrating foundation data
        into the stateful runtime. Delegates to promote_snapshot().

        Args:
            foundation_snapshot: The SkillSnapshot from the foundation layer.

        Returns:
            A list of SkillRuntimeSnapshot instances.
        """
        return self.promote_snapshot(foundation_snapshot)

    def _emit(
        self,
        skill_id: UUID,
        previous_state: SkillRuntimeState,
        new_state: SkillRuntimeState,
        *,
        knowledge_id: UUID | None = None,
        employee_id: UUID | None = None,
    ) -> None:
        event = SkillStateChangedEvent(
            skill_id=skill_id,
            previous_state=previous_state,
            new_state=new_state,
            knowledge_id=knowledge_id,
            employee_id=employee_id,
        )
        self._events.append(event)
        self.event_bus.publish(event)

    def _require_skill(self, skill_id: UUID) -> SkillRuntimeSnapshot:
        try:
            return self._skills[skill_id]
        except KeyError as error:
            raise KeyError(f"Skill {skill_id} is not registered in skill runtime.") from error

    def _knowledge_creatable_states(self) -> set[Any]:
        from core.knowledge.runtime import KnowledgeRuntimeState

        return {KnowledgeRuntimeState.ACCEPTED, KnowledgeRuntimeState.PUBLISHED}