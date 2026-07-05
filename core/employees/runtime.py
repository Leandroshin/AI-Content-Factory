"""Runtime for live employee lifecycle handling."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any
from uuid import UUID

from core.events.bus import EventBus

from .models import Employee, EmployeeRole, EmployeeStatus


class EmployeeRuntimeState(StrEnum):
    """Runtime states for employees."""

    BOOTING = "booting"
    IDLE = "idle"
    BUSY = "busy"
    OFFLINE = "offline"


@dataclass(frozen=True, slots=True)
class EmployeeStateChangedEvent:
    """Deterministic event emitted by the employee runtime."""

    employee_id: UUID
    previous_state: EmployeeRuntimeState
    new_state: EmployeeRuntimeState
    task_id: str | None = None
    payload: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class EmployeeRuntimeSnapshot:
    """In-memory snapshot for employee runtime state."""

    employee_id: UUID
    name: str
    role: EmployeeRole
    state: EmployeeRuntimeState = EmployeeRuntimeState.BOOTING
    task_id: str | None = None


class EmployeeRuntime:
    """Deterministic in-memory runtime for employees."""

    def __init__(self, event_bus: EventBus | None = None) -> None:
        self._employees: dict[UUID, EmployeeRuntimeSnapshot] = {}
        self._events: list[EmployeeStateChangedEvent] = []
        self._event_bus = event_bus

    def initialize_company(self) -> None:
        """Mark the runtime as ready to manage employees."""

        return None

    def create_employee(self, employee: Employee) -> EmployeeRuntimeSnapshot:
        snapshot = EmployeeRuntimeSnapshot(
            employee_id=employee.identity.employee_id,
            name=employee.profile.full_name or employee.identity.display_name or employee.identity.username or "Employee",
            role=employee.role,
        )
        self._employees[snapshot.employee_id] = snapshot
        self._emit(snapshot.employee_id, EmployeeRuntimeState.BOOTING, EmployeeRuntimeState.IDLE)
        snapshot.state = EmployeeRuntimeState.IDLE
        return self._employees[snapshot.employee_id]

    def assign_task(self, employee_id: UUID, task_id: str) -> EmployeeRuntimeSnapshot:
        snapshot = self._require_employee(employee_id)
        self._emit(snapshot.employee_id, snapshot.state, EmployeeRuntimeState.BUSY, task_id=task_id)
        snapshot.state = EmployeeRuntimeState.BUSY
        snapshot.task_id = task_id
        return snapshot

    def complete_task(self, employee_id: UUID) -> EmployeeRuntimeSnapshot:
        snapshot = self._require_employee(employee_id)
        self._emit(snapshot.employee_id, snapshot.state, EmployeeRuntimeState.IDLE)
        snapshot.state = EmployeeRuntimeState.IDLE
        snapshot.task_id = None
        return snapshot

    def set_offline(self, employee_id: UUID) -> EmployeeRuntimeSnapshot:
        snapshot = self._require_employee(employee_id)
        self._emit(snapshot.employee_id, snapshot.state, EmployeeRuntimeState.OFFLINE)
        snapshot.state = EmployeeRuntimeState.OFFLINE
        snapshot.task_id = None
        return snapshot

    def events(self) -> list[EmployeeStateChangedEvent]:
        return list(self._events)

    def snapshot(self) -> list[EmployeeRuntimeSnapshot]:
        return list(self._employees.values())

    def _emit(
        self,
        employee_id: UUID,
        previous_state: EmployeeRuntimeState,
        new_state: EmployeeRuntimeState,
        task_id: str | None = None,
    ) -> None:
        event = EmployeeStateChangedEvent(employee_id=employee_id, previous_state=previous_state, new_state=new_state, task_id=task_id)
        self._events.append(event)
        if self._event_bus is not None:
            self._event_bus.publish(event)

    def _require_employee(self, employee_id: UUID) -> EmployeeRuntimeSnapshot:
        try:
            return self._employees[employee_id]
        except KeyError as error:
            raise KeyError(f"Employee {employee_id} is not registered in runtime.") from error
