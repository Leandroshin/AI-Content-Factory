"""Runtime for live knowledge lifecycle handling."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any, TYPE_CHECKING
from uuid import UUID

import time

from core.events.bus import EventBus
from core.events.domain_events import KnowledgePromoted
from core.persistence._helpers import save_if_enabled
from core.results import Result, ResultStatus

if TYPE_CHECKING:
    from core.persistence.runtime import PersistenceRuntime
    from core.results.runtime import ResultRuntime

from .models import KnowledgeCategory, KnowledgeContext, KnowledgeEntry, KnowledgeMetadata, KnowledgeSource, KnowledgeStatus


class KnowledgeRuntimeState(StrEnum):
    """Runtime states for knowledge entries."""

    CREATED = "created"
    VALIDATING = "validating"
    ACCEPTED = "accepted"
    PUBLISHED = "published"
    DEPRECATED = "deprecated"
    ARCHIVED = "archived"


class KnowledgeType(StrEnum):
    """Knowledge classifications."""

    OPERATIONAL = "operational"
    STRATEGIC = "strategic"
    TECHNICAL = "technical"
    LEARNED = "learned"


@dataclass(frozen=True, slots=True)
class KnowledgeStateChangedEvent:
    """Deterministic event emitted by the knowledge runtime."""

    knowledge_id: UUID
    previous_state: KnowledgeRuntimeState
    new_state: KnowledgeRuntimeState
    result_id: UUID | None = None
    payload: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class KnowledgeRuntimeSnapshot:
    """In-memory snapshot for knowledge lifecycle state."""

    knowledge_id: UUID
    key: str
    state: KnowledgeRuntimeState = KnowledgeRuntimeState.CREATED
    knowledge_type: KnowledgeType = KnowledgeType.OPERATIONAL
    result_id: UUID | None = None
    version_history: list[str] = field(default_factory=list)
    entry: KnowledgeEntry | None = None


class KnowledgeRuntime:
    """Deterministic in-memory runtime for knowledge lifecycle management."""

    _TRANSITIONS: dict[KnowledgeRuntimeState, set[KnowledgeRuntimeState]] = {
        KnowledgeRuntimeState.CREATED: {KnowledgeRuntimeState.VALIDATING, KnowledgeRuntimeState.ARCHIVED},
        KnowledgeRuntimeState.VALIDATING: {KnowledgeRuntimeState.ACCEPTED, KnowledgeRuntimeState.ARCHIVED},
        KnowledgeRuntimeState.ACCEPTED: {KnowledgeRuntimeState.PUBLISHED, KnowledgeRuntimeState.DEPRECATED, KnowledgeRuntimeState.ARCHIVED},
        KnowledgeRuntimeState.PUBLISHED: {KnowledgeRuntimeState.DEPRECATED, KnowledgeRuntimeState.ARCHIVED},
        KnowledgeRuntimeState.DEPRECATED: {KnowledgeRuntimeState.ARCHIVED},
        KnowledgeRuntimeState.ARCHIVED: set(),
    }

    def __init__(self, result_runtime: "ResultRuntime", event_bus: EventBus | None = None, persistence_runtime: PersistenceRuntime | None = None) -> None:
        self.result_runtime = result_runtime
        self.event_bus = event_bus or result_runtime.event_bus
        self._persistence = persistence_runtime
        self._knowledge: dict[UUID, KnowledgeRuntimeSnapshot] = {}
        self._events: list[KnowledgeStateChangedEvent] = []

    def create_from_result(self, result_id: UUID, *, knowledge_type: KnowledgeType = KnowledgeType.OPERATIONAL) -> KnowledgeRuntimeSnapshot:
        result_snapshot = next((snapshot for snapshot in self.result_runtime.snapshot() if snapshot.result_id == result_id), None)
        if result_snapshot is None:
            raise KeyError(f"Result {result_id} is not registered in result runtime.")
        if result_snapshot.state not in self._result_creatable_states():
            raise ValueError("Knowledge can only be created from approved or published results.")
        if result_snapshot.result is None:
            raise ValueError("Result payload is missing.")
        entry = KnowledgeEntry(
            key=f"knowledge:{result_snapshot.result.id}",
            category=self._category_from_type(knowledge_type),
            status=KnowledgeStatus.DRAFT,
            source=KnowledgeSource(name=result_snapshot.name, origin="result", metadata={"result_id": str(result_id)}),
            context=KnowledgeContext(
                project_name=result_snapshot.result.context.project_name if result_snapshot.result.context else None,
                engine_name=None,
                metadata=KnowledgeMetadata(title=result_snapshot.result.name, description="Derived from approved result"),
            ),
            metadata=KnowledgeMetadata(title=result_snapshot.result.name, description="Organizational knowledge asset"),
            content={
                "result_id": str(result_id),
                "summary": result_snapshot.result.summary.model_dump(),
            },
        )
        snapshot = KnowledgeRuntimeSnapshot(
            knowledge_id=entry.id,
            key=entry.key,
            state=KnowledgeRuntimeState.CREATED,
            knowledge_type=knowledge_type,
            result_id=result_id,
            version_history=[f"v1:{KnowledgeRuntimeState.CREATED.value}"],
            entry=entry,
        )
        self._knowledge[entry.id] = snapshot
        self._emit(entry.id, KnowledgeRuntimeState.CREATED, KnowledgeRuntimeState.VALIDATING, result_id=result_id)
        snapshot.state = KnowledgeRuntimeState.VALIDATING
        self._save(snapshot)
        return snapshot

    def validate(self, knowledge_id: UUID) -> KnowledgeRuntimeSnapshot:
        return self.transition(knowledge_id, KnowledgeRuntimeState.ACCEPTED)

    def publish(self, knowledge_id: UUID) -> KnowledgeRuntimeSnapshot:
        snapshot = self.transition(knowledge_id, KnowledgeRuntimeState.PUBLISHED)
        if snapshot.entry is not None:
            snapshot.entry.status = KnowledgeStatus.ACTIVE
        self.event_bus.publish(KnowledgePromoted(
            knowledge_id=knowledge_id,
            source="knowledge_runtime",
            records_count=1,
            timestamp=time.time(),
        ))
        self._save(snapshot)
        return snapshot

    def deprecate(self, knowledge_id: UUID) -> KnowledgeRuntimeSnapshot:
        snapshot = self.transition(knowledge_id, KnowledgeRuntimeState.DEPRECATED)
        if snapshot.entry is not None:
            snapshot.entry.status = KnowledgeStatus.DEPRECATED
        return snapshot

    def archive(self, knowledge_id: UUID) -> KnowledgeRuntimeSnapshot:
        snapshot = self.transition(knowledge_id, KnowledgeRuntimeState.ARCHIVED)
        if snapshot.entry is not None:
            snapshot.entry.status = KnowledgeStatus.ARCHIVED
        return snapshot

    def transition(self, knowledge_id: UUID, new_state: KnowledgeRuntimeState) -> KnowledgeRuntimeSnapshot:
        snapshot = self._require_knowledge(knowledge_id)
        if new_state not in self._TRANSITIONS[snapshot.state]:
            raise ValueError(f"Invalid knowledge transition from {snapshot.state.value} to {new_state.value}.")
        previous_state = snapshot.state
        snapshot.state = new_state
        snapshot.version_history.append(f"v{len(snapshot.version_history) + 1}:{new_state.value}")
        if snapshot.entry is not None:
            if new_state == KnowledgeRuntimeState.ACCEPTED:
                snapshot.entry.status = KnowledgeStatus.DRAFT
            elif new_state == KnowledgeRuntimeState.PUBLISHED:
                snapshot.entry.status = KnowledgeStatus.ACTIVE
            elif new_state == KnowledgeRuntimeState.DEPRECATED:
                snapshot.entry.status = KnowledgeStatus.DEPRECATED
            elif new_state == KnowledgeRuntimeState.ARCHIVED:
                snapshot.entry.status = KnowledgeStatus.ARCHIVED
        self._emit(knowledge_id, previous_state, new_state, result_id=snapshot.result_id)
        return snapshot

    def summary(self, knowledge_id: UUID) -> dict[str, Any]:
        snapshot = self._require_knowledge(knowledge_id)
        return {
            "knowledge_id": str(snapshot.knowledge_id),
            "state": snapshot.state.value,
            "type": snapshot.knowledge_type.value,
            "result_id": str(snapshot.result_id) if snapshot.result_id else None,
            "versions": list(snapshot.version_history),
        }

    def events(self) -> list[KnowledgeStateChangedEvent]:
        return list(self._events)

    def snapshot(self) -> list[KnowledgeRuntimeSnapshot]:
        return list(self._knowledge.values())

    def _save(self, snapshot: KnowledgeRuntimeSnapshot) -> None:
        persistence = getattr(self, "_persistence", None)
        save_if_enabled(persistence, snapshot, "knowledge", snapshot.knowledge_id)

    def _emit(self, knowledge_id: UUID, previous_state: KnowledgeRuntimeState, new_state: KnowledgeRuntimeState, *, result_id: UUID | None = None) -> None:
        event = KnowledgeStateChangedEvent(
            knowledge_id=knowledge_id,
            previous_state=previous_state,
            new_state=new_state,
            result_id=result_id,
        )
        self._events.append(event)
        self.event_bus.publish(event)

    def _require_knowledge(self, knowledge_id: UUID) -> KnowledgeRuntimeSnapshot:
        try:
            return self._knowledge[knowledge_id]
        except KeyError as error:
            raise KeyError(f"Knowledge {knowledge_id} is not registered in knowledge runtime.") from error

    def _result_creatable_states(self) -> set[Any]:
        from core.results.runtime import ResultRuntimeState

        return {ResultRuntimeState.APPROVED, ResultRuntimeState.PUBLISHED}

    def _category_from_type(self, knowledge_type: KnowledgeType) -> KnowledgeCategory:
        return {
            KnowledgeType.OPERATIONAL: KnowledgeCategory.SYSTEM,
            KnowledgeType.STRATEGIC: KnowledgeCategory.SYSTEM,
            KnowledgeType.TECHNICAL: KnowledgeCategory.ENGINE,
            KnowledgeType.LEARNED: KnowledgeCategory.EVENT,
        }[knowledge_type]