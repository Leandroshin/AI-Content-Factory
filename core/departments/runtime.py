"""Runtime for departments in AI Content Factory."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any
from uuid import UUID, uuid4

from core.employees import EmployeeRuntimeState, EmployeeStateChangedEvent, EmployeeRuntimeSnapshot
from core.events.bus import EventBus
from core.runtime import CompanyRuntime


class DepartmentRuntimeState(StrEnum):
    """Runtime states for departments."""

    INITIALIZING = "initializing"
    IDLE = "idle"
    WORKING = "working"


@dataclass(frozen=True, slots=True)
class DepartmentStateChangedEvent:
    """Deterministic event emitted by the department runtime."""

    department_id: UUID
    previous_state: DepartmentRuntimeState
    new_state: DepartmentRuntimeState
    payload: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class DepartmentEmployeeLink:
    """In-memory link between department and employee."""

    employee_id: UUID
    state: EmployeeRuntimeState
    task_id: str | None = None


@dataclass(slots=True)
class DepartmentRuntimeSnapshot:
    """In-memory snapshot for department runtime state."""

    department_id: UUID
    name: str
    state: DepartmentRuntimeState = DepartmentRuntimeState.INITIALIZING
    employees: dict[UUID, DepartmentEmployeeLink] = field(default_factory=dict)


class DepartmentRuntime:
    """Deterministic in-memory runtime for departments."""

    def __init__(self, company_runtime: CompanyRuntime, event_bus: EventBus | None = None) -> None:
        self.company_runtime = company_runtime
        self.event_bus = event_bus or company_runtime.event_bus
        self._departments: dict[UUID, DepartmentRuntimeSnapshot] = {}
        self._events: list[DepartmentStateChangedEvent] = []

    def create_department(self, name: str) -> DepartmentRuntimeSnapshot:
        snapshot = DepartmentRuntimeSnapshot(department_id=uuid4(), name=name)
        self._departments[snapshot.department_id] = snapshot
        self._emit(snapshot.department_id, DepartmentRuntimeState.INITIALIZING, DepartmentRuntimeState.IDLE)
        snapshot.state = DepartmentRuntimeState.IDLE
        return snapshot

    def register_employee(self, department_id: UUID, employee_snapshot: EmployeeRuntimeSnapshot) -> None:
        department = self._require_department(department_id)
        department.employees[employee_snapshot.employee_id] = DepartmentEmployeeLink(
            employee_id=employee_snapshot.employee_id,
            state=employee_snapshot.state,
            task_id=employee_snapshot.task_id,
        )
        self._sync_state(department)

    def sync_employee_state(self, department_id: UUID, employee_event: EmployeeStateChangedEvent) -> None:
        department = self._require_department(department_id)
        link = department.employees.get(employee_event.employee_id)
        if link is None:
            return
        link.state = employee_event.new_state
        link.task_id = employee_event.task_id
        self._sync_state(department)

    def department(self, department_id: UUID) -> DepartmentRuntimeSnapshot:
        return self._require_department(department_id)

    def events(self) -> list[DepartmentStateChangedEvent]:
        return list(self._events)

    def _sync_state(self, department: DepartmentRuntimeSnapshot) -> None:
        previous_state = department.state
        active_states = {EmployeeRuntimeState.BUSY}
        department.state = (
            DepartmentRuntimeState.WORKING
            if any(link.state in active_states for link in department.employees.values())
            else DepartmentRuntimeState.IDLE
        )
        if department.state != previous_state:
            self._emit(department.department_id, previous_state, department.state)

    def _emit(self, department_id: UUID, previous_state: DepartmentRuntimeState, new_state: DepartmentRuntimeState) -> None:
        event = DepartmentStateChangedEvent(department_id=department_id, previous_state=previous_state, new_state=new_state)
        self._events.append(event)
        self.event_bus.publish(event)

    def _require_department(self, department_id: UUID) -> DepartmentRuntimeSnapshot:
        try:
            return self._departments[department_id]
        except KeyError as error:
            raise KeyError(f"Department {department_id} is not registered in runtime.") from error