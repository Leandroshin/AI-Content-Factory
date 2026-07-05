"""Company runtime for AI Content Factory."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any
from uuid import UUID, uuid4

from core.employees import Employee, EmployeeRuntime, EmployeeRuntimeSnapshot
from core.events.bus import EventBus


class CompanyState(StrEnum):
    """Global company states."""

    STARTING = "starting"
    INITIALIZING = "initializing"
    READY = "ready"
    RUNNING = "running"
    PAUSED = "paused"
    STOPPING = "stopping"
    SHUTDOWN = "shutdown"
    ERROR = "error"


@dataclass(frozen=True, slots=True)
class TaskRecord:
    """In-memory task placeholder."""

    task_id: UUID
    title: str
    assigned_employee_id: UUID | None = None
    state: str = "created"
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class CompanyStateChangedEvent:
    """Deterministic company state transition event."""

    previous_state: CompanyState
    new_state: CompanyState
    reason: str | None = None


class RuntimeStateManager:
    """In-memory manager for company runtime state."""

    def __init__(self, event_bus: EventBus | None = None) -> None:
        self._state = CompanyState.STARTING
        self._events: list[CompanyStateChangedEvent] = []
        self._event_bus = event_bus

    def transition(self, new_state: CompanyState, reason: str | None = None) -> CompanyState:
        previous_state = self._state
        self._state = new_state
        event = CompanyStateChangedEvent(previous_state=previous_state, new_state=new_state, reason=reason)
        self._events.append(event)
        if self._event_bus is not None:
            self._event_bus.publish(event)
        return self._state

    @property
    def state(self) -> CompanyState:
        return self._state

    def events(self) -> list[CompanyStateChangedEvent]:
        return list(self._events)


class CompanyRuntime:
    """Minimal company runtime coordinating employees and tasks."""

    def __init__(self, event_bus: EventBus | None = None) -> None:
        self.runtime_id = uuid4()
        self.event_bus = event_bus or EventBus()
        self.state_manager = RuntimeStateManager(self.event_bus)
        self.employee_runtime = EmployeeRuntime(self.event_bus)
        self._employees: dict[UUID, EmployeeRuntimeSnapshot] = {}
        self._tasks: dict[UUID, TaskRecord] = {}

    def initialize_company(self) -> None:
        self.state_manager.transition(CompanyState.INITIALIZING, "company boot")
        self.employee_runtime.initialize_company()
        self.state_manager.transition(CompanyState.READY, "runtime ready")
        self.state_manager.transition(CompanyState.RUNNING, "company running")

    def register_employee(self, employee: Employee) -> EmployeeRuntimeSnapshot:
        snapshot = self.employee_runtime.create_employee(employee)
        self._employees[snapshot.employee_id] = snapshot
        return snapshot

    def register_task(self, title: str, *, metadata: dict[str, Any] | None = None) -> TaskRecord:
        record = TaskRecord(task_id=uuid4(), title=title, metadata=metadata or {})
        self._tasks[record.task_id] = record
        return record

    def assign_task(self, employee_id: UUID, task_id: UUID) -> EmployeeRuntimeSnapshot:
        employee_snapshot = self.employee_runtime.assign_task(employee_id, str(task_id))
        self._employees[employee_id] = employee_snapshot
        task = self._tasks[task_id]
        self._tasks[task_id] = TaskRecord(
            task_id=task.task_id,
            title=task.title,
            assigned_employee_id=employee_id,
            state="busy",
            metadata=task.metadata,
        )
        return employee_snapshot

    def complete_task(self, employee_id: UUID, task_id: UUID) -> EmployeeRuntimeSnapshot:
        employee_snapshot = self.employee_runtime.complete_task(employee_id)
        self._employees[employee_id] = employee_snapshot
        task = self._tasks[task_id]
        self._tasks[task_id] = TaskRecord(
            task_id=task.task_id,
            title=task.title,
            assigned_employee_id=employee_id,
            state="completed",
            metadata=task.metadata,
        )
        return employee_snapshot

    def employees(self) -> list[EmployeeRuntimeSnapshot]:
        return list(self._employees.values())

    def tasks(self) -> list[TaskRecord]:
        return list(self._tasks.values())

    def state(self) -> CompanyState:
        return self.state_manager.state

    def events(self) -> list[Any]:
        return [*self.state_manager.events(), *self.employee_runtime.events()]

    def observability_snapshots(self) -> list[dict[str, Any]]:
        return []