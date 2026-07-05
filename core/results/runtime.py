"""Runtime for live result lifecycle handling."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any
from uuid import UUID

from typing import TYPE_CHECKING

from core.events.bus import EventBus

from .models import Result, ResultContext, ResultMetadata, ResultOutcome, ResultStatus, ResultSummary, ResultType

if TYPE_CHECKING:
    from core.workflows.runtime import WorkflowRuntime


class ResultRuntimeState(StrEnum):
    """Runtime states for results."""

    CREATED = "created"
    PENDING_REVIEW = "pending_review"
    APPROVED = "approved"
    REJECTED = "rejected"
    PUBLISHED = "published"
    ARCHIVED = "archived"


@dataclass(frozen=True, slots=True)
class ResultStateChangedEvent:
    """Deterministic event emitted by the result runtime."""

    result_id: UUID
    previous_state: ResultRuntimeState
    new_state: ResultRuntimeState
    workflow_id: UUID | None = None
    task_id: UUID | None = None
    payload: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class ResultRuntimeSnapshot:
    """In-memory snapshot for result lifecycle state."""

    result_id: UUID
    name: str
    state: ResultRuntimeState = ResultRuntimeState.CREATED
    workflow_id: UUID | None = None
    task_id: UUID | None = None
    history: list[tuple[ResultRuntimeState, ResultRuntimeState]] = field(default_factory=list)
    result: Result | None = None


class ResultRuntime:
    """Deterministic in-memory runtime for result lifecycle management."""

    _TRANSITIONS: dict[ResultRuntimeState, set[ResultRuntimeState]] = {
        ResultRuntimeState.CREATED: {ResultRuntimeState.PENDING_REVIEW, ResultRuntimeState.REJECTED, ResultRuntimeState.ARCHIVED},
        ResultRuntimeState.PENDING_REVIEW: {ResultRuntimeState.APPROVED, ResultRuntimeState.REJECTED, ResultRuntimeState.ARCHIVED},
        ResultRuntimeState.APPROVED: {ResultRuntimeState.PUBLISHED, ResultRuntimeState.ARCHIVED},
        ResultRuntimeState.REJECTED: {ResultRuntimeState.ARCHIVED},
        ResultRuntimeState.PUBLISHED: {ResultRuntimeState.ARCHIVED},
        ResultRuntimeState.ARCHIVED: set(),
    }

    def __init__(self, workflow_runtime: "WorkflowRuntime", event_bus: EventBus | None = None) -> None:
        self.workflow_runtime = workflow_runtime
        self.event_bus = event_bus or workflow_runtime.event_bus
        self._results: dict[UUID, ResultRuntimeSnapshot] = {}
        self._events: list[ResultStateChangedEvent] = []

    def create_from_workflow(self, workflow_id: UUID, task_id: UUID | None = None, *, name: str | None = None) -> ResultRuntimeSnapshot:
        workflow = self.workflow_runtime.snapshot()
        workflow_snapshot = next((item for item in workflow if item.workflow_id == workflow_id), None)
        if workflow_snapshot is None:
            raise KeyError(f"Workflow {workflow_id} is not registered in workflow runtime.")
        result = Result(
            name=name or f"Result for {workflow_snapshot.name}",
            type=ResultType.ORGANIZATIONAL,
            status=ResultStatus.GENERATED,
            outcome=ResultOutcome.SUCCESS,
            summary=ResultSummary(title=workflow_snapshot.name, description="Generated from workflow completion"),
            context=ResultContext(
                source_name=workflow_snapshot.name,
                project_name=workflow_snapshot.name,
                metadata=ResultMetadata(name="workflow_result", description="Result produced by workflow"),
            ),
        )
        snapshot = ResultRuntimeSnapshot(
            result_id=result.id,
            name=result.name,
            state=ResultRuntimeState.CREATED,
            workflow_id=workflow_id,
            task_id=task_id,
            result=result,
        )
        self._results[result.id] = snapshot
        self._emit(result.id, ResultRuntimeState.CREATED, ResultRuntimeState.PENDING_REVIEW, workflow_id=workflow_id, task_id=task_id)
        snapshot.state = ResultRuntimeState.PENDING_REVIEW
        snapshot.result.status = ResultStatus.GENERATED
        return snapshot

    def approve(self, result_id: UUID) -> ResultRuntimeSnapshot:
        return self.transition(result_id, ResultRuntimeState.APPROVED)

    def reject(self, result_id: UUID) -> ResultRuntimeSnapshot:
        return self.transition(result_id, ResultRuntimeState.REJECTED)

    def publish(self, result_id: UUID) -> ResultRuntimeSnapshot:
        snapshot = self.transition(result_id, ResultRuntimeState.PUBLISHED)
        if snapshot.result is not None:
            snapshot.result.status = ResultStatus.VERIFIED
        return snapshot

    def archive(self, result_id: UUID) -> ResultRuntimeSnapshot:
        snapshot = self.transition(result_id, ResultRuntimeState.ARCHIVED)
        if snapshot.result is not None:
            snapshot.result.status = ResultStatus.ARCHIVED
        return snapshot

    def transition(self, result_id: UUID, new_state: ResultRuntimeState) -> ResultRuntimeSnapshot:
        snapshot = self._require_result(result_id)
        if new_state not in self._TRANSITIONS[snapshot.state]:
            raise ValueError(f"Invalid result transition from {snapshot.state.value} to {new_state.value}.")
        previous_state = snapshot.state
        snapshot.state = new_state
        snapshot.history.append((previous_state, new_state))
        if snapshot.result is not None:
            if new_state == ResultRuntimeState.APPROVED:
                snapshot.result.status = ResultStatus.VERIFIED
            elif new_state == ResultRuntimeState.REJECTED:
                snapshot.result.status = ResultStatus.DRAFT
            elif new_state == ResultRuntimeState.ARCHIVED:
                snapshot.result.status = ResultStatus.ARCHIVED
        self._emit(result_id, previous_state, new_state, workflow_id=snapshot.workflow_id, task_id=snapshot.task_id)
        return snapshot

    def summary(self, result_id: UUID) -> dict[str, Any]:
        snapshot = self._require_result(result_id)
        return {
            "result_id": str(snapshot.result_id),
            "state": snapshot.state.value,
            "workflow_id": str(snapshot.workflow_id) if snapshot.workflow_id else None,
            "task_id": str(snapshot.task_id) if snapshot.task_id else None,
            "history": [(previous.value, current.value) for previous, current in snapshot.history],
        }

    def events(self) -> list[ResultStateChangedEvent]:
        return list(self._events)

    def snapshot(self) -> list[ResultRuntimeSnapshot]:
        return list(self._results.values())

    def _emit(
        self,
        result_id: UUID,
        previous_state: ResultRuntimeState,
        new_state: ResultRuntimeState,
        *,
        workflow_id: UUID | None = None,
        task_id: UUID | None = None,
    ) -> None:
        event = ResultStateChangedEvent(
            result_id=result_id,
            previous_state=previous_state,
            new_state=new_state,
            workflow_id=workflow_id,
            task_id=task_id,
        )
        self._events.append(event)
        self.event_bus.publish(event)

    def _require_result(self, result_id: UUID) -> ResultRuntimeSnapshot:
        try:
            return self._results[result_id]
        except KeyError as error:
            raise KeyError(f"Result {result_id} is not registered in result runtime.") from error