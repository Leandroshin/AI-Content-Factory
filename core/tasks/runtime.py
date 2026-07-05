"""Runtime for live task lifecycle handling."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any, TYPE_CHECKING
from uuid import UUID

from core.events.bus import EventBus
from core.runtime import CompanyRuntime

from .models import Task, TaskId

if TYPE_CHECKING:
    from core.orchestrator.runtime import OrchestratorRuntime


class TaskRuntimeState(StrEnum):
    """Runtime states for tasks."""

    CREATED = "created"
    QUEUED = "queued"
    ASSIGNED = "assigned"
    RUNNING = "running"
    PAUSED = "paused"
    BLOCKED = "blocked"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass(frozen=True, slots=True)
class TaskStateChangedEvent:
    """Deterministic event emitted by the task runtime."""

    task_id: UUID
    previous_state: TaskRuntimeState
    new_state: TaskRuntimeState
    employee_id: UUID | None = None
    department_id: UUID | None = None
    payload: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class TaskRuntimeSnapshot:
    """In-memory snapshot for task lifecycle state."""

    task_id: UUID
    name: str
    state: TaskRuntimeState = TaskRuntimeState.CREATED
    employee_id: UUID | None = None
    department_id: UUID | None = None
    result: Any | None = None


class TaskRuntime:
    """Deterministic in-memory runtime for task lifecycle management."""

    _TRANSITIONS: dict[TaskRuntimeState, set[TaskRuntimeState]] = {
        TaskRuntimeState.CREATED: {TaskRuntimeState.QUEUED, TaskRuntimeState.CANCELLED},
        TaskRuntimeState.QUEUED: {TaskRuntimeState.ASSIGNED, TaskRuntimeState.CANCELLED},
        TaskRuntimeState.ASSIGNED: {TaskRuntimeState.RUNNING, TaskRuntimeState.PAUSED, TaskRuntimeState.BLOCKED, TaskRuntimeState.CANCELLED},
        TaskRuntimeState.RUNNING: {TaskRuntimeState.PAUSED, TaskRuntimeState.BLOCKED, TaskRuntimeState.COMPLETED, TaskRuntimeState.FAILED, TaskRuntimeState.CANCELLED},
        TaskRuntimeState.PAUSED: {TaskRuntimeState.RUNNING, TaskRuntimeState.BLOCKED, TaskRuntimeState.CANCELLED},
        TaskRuntimeState.BLOCKED: {TaskRuntimeState.QUEUED, TaskRuntimeState.ASSIGNED, TaskRuntimeState.RUNNING, TaskRuntimeState.CANCELLED},
        TaskRuntimeState.COMPLETED: set(),
        TaskRuntimeState.FAILED: set(),
        TaskRuntimeState.CANCELLED: set(),
    }

    def __init__(self, company_runtime: CompanyRuntime, orchestrator_runtime: OrchestratorRuntime, event_bus: EventBus | None = None) -> None:
        self.company_runtime = company_runtime
        self.orchestrator_runtime = orchestrator_runtime
        self.event_bus = event_bus or company_runtime.event_bus
        self._tasks: dict[TaskId, TaskRuntimeSnapshot] = {}
        self._events: list[TaskStateChangedEvent] = []

    def register_task(self, task: Task) -> TaskRuntimeSnapshot:
        snapshot = TaskRuntimeSnapshot(task_id=task.id, name=task.name)
        self._tasks[task.id] = snapshot
        self._emit(snapshot.task_id, TaskRuntimeState.CREATED, TaskRuntimeState.QUEUED, payload={"title": task.name})
        snapshot.state = TaskRuntimeState.QUEUED
        self.company_runtime.register_task(task.name, metadata={"task_id": str(task.id)})
        return snapshot

    def transition(
        self,
        task_id: TaskId,
        new_state: TaskRuntimeState,
        *,
        employee_id: UUID | None = None,
        department_id: UUID | None = None,
    ) -> TaskRuntimeSnapshot:
        snapshot = self._require_task(task_id)
        if new_state not in self._TRANSITIONS[snapshot.state]:
            raise ValueError(f"Invalid task transition from {snapshot.state.value} to {new_state.value}.")
        previous_state = snapshot.state
        snapshot.state = new_state
        snapshot.employee_id = employee_id or snapshot.employee_id
        snapshot.department_id = department_id or snapshot.department_id
        self._emit(task_id, previous_state, new_state, employee_id=snapshot.employee_id, department_id=snapshot.department_id)
        return snapshot

    def assign_via_orchestrator(self, task_id: TaskId, department_id: UUID) -> TaskRuntimeSnapshot:
        snapshot = self._require_task(task_id)
        chosen = self.orchestrator_runtime.choose_employee(department_id)
        self.transition(task_id, TaskRuntimeState.ASSIGNED, employee_id=chosen.employee_id, department_id=department_id)
        self.transition(task_id, TaskRuntimeState.RUNNING)
        company_task_id = self._company_task_id(task_id)
        self.company_runtime.assign_task(chosen.employee_id, company_task_id)
        return snapshot

    def complete(self, task_id: TaskId) -> TaskRuntimeSnapshot:
        snapshot = self._require_task(task_id)
        if snapshot.employee_id is None:
            raise KeyError("Task is not assigned to an employee.")
        company_task_id = self._company_task_id(task_id)
        self.company_runtime.complete_task(snapshot.employee_id, company_task_id)
        self.transition(task_id, TaskRuntimeState.COMPLETED)
        return snapshot

    def pause(self, task_id: TaskId) -> TaskRuntimeSnapshot:
        return self.transition(task_id, TaskRuntimeState.PAUSED)

    def block(self, task_id: TaskId) -> TaskRuntimeSnapshot:
        return self.transition(task_id, TaskRuntimeState.BLOCKED)

    def fail(self, task_id: TaskId) -> TaskRuntimeSnapshot:
        return self.transition(task_id, TaskRuntimeState.FAILED)

    def cancel(self, task_id: TaskId) -> TaskRuntimeSnapshot:
        return self.transition(task_id, TaskRuntimeState.CANCELLED)

    def events(self) -> list[TaskStateChangedEvent]:
        return list(self._events)

    def snapshot(self) -> list[TaskRuntimeSnapshot]:
        return list(self._tasks.values())

    def _emit(
        self,
        task_id: UUID,
        previous_state: TaskRuntimeState,
        new_state: TaskRuntimeState,
        *,
        employee_id: UUID | None = None,
        department_id: UUID | None = None,
        payload: dict[str, Any] | None = None,
    ) -> None:
        event = TaskStateChangedEvent(
            task_id=task_id,
            previous_state=previous_state,
            new_state=new_state,
            employee_id=employee_id,
            department_id=department_id,
            payload=payload or {},
        )
        self._events.append(event)
        self.event_bus.publish(event)

    def _require_task(self, task_id: TaskId) -> TaskRuntimeSnapshot:
        try:
            return self._tasks[task_id]
        except KeyError as error:
            raise KeyError(f"Task {task_id} is not registered in task runtime.") from error

    def _company_task_id(self, task_id: TaskId) -> UUID:
        for company_task_id, task in self.company_runtime._tasks.items():
            if task.metadata.get("task_id") == str(task_id):
                return company_task_id
        raise KeyError(f"Task {task_id} is not registered in company runtime.")