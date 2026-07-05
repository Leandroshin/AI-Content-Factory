"""Observability projection for employee runtime state."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any
from uuid import UUID

from .runtime import EmployeeRuntimeSnapshot, EmployeeRuntimeState, EmployeeStateChangedEvent


@dataclass(slots=True)
class EmployeeObservabilityRecord:
    """Read-only observability record for an employee."""

    employee_id: UUID
    name: str
    state: str
    task_id: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


class EmployeeObservabilityProjector:
    """Project employee runtime snapshots into observability records."""

    def project_snapshot(self, snapshot: EmployeeRuntimeSnapshot) -> EmployeeObservabilityRecord:
        return EmployeeObservabilityRecord(
            employee_id=snapshot.employee_id,
            name=snapshot.name,
            state=snapshot.state.value,
            task_id=snapshot.task_id,
        )

    def project_event(self, event: EmployeeStateChangedEvent) -> EmployeeObservabilityRecord:
        return EmployeeObservabilityRecord(
            employee_id=event.employee_id,
            name="Employee",
            state=event.new_state.value,
            task_id=event.task_id,
            metadata={"previous_state": event.previous_state.value, **event.payload},
        )
