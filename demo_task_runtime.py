"""End-to-end demonstration for the task runtime lifecycle."""

from __future__ import annotations

from core.departments.runtime import DepartmentRuntime, DepartmentStateChangedEvent
from core.employees import Employee
from core.employees.runtime import EmployeeStateChangedEvent
from core.events.bus import EventBus
from core.observability import ObservabilityProjector
from core.orchestrator import OrchestratorRuntime
from core.runtime import CompanyRuntime, CompanyStateChangedEvent
from core.tasks import Task
from core.tasks.runtime import TaskRuntime, TaskRuntimeState


def main() -> None:
    event_bus = EventBus()
    observability = ObservabilityProjector()
    company = CompanyRuntime(event_bus)
    department_runtime = DepartmentRuntime(company, event_bus)
    orchestrator = OrchestratorRuntime(company, department_runtime, event_bus)
    task_runtime = TaskRuntime(company, orchestrator, event_bus)

    company.initialize_company()
    event_bus.subscribe(CompanyStateChangedEvent, observability.handle_company_event)
    event_bus.subscribe(EmployeeStateChangedEvent, observability.handle_employee_event)
    event_bus.subscribe(DepartmentStateChangedEvent, observability.handle_department_event)
    department = department_runtime.create_department("Operations")
    employee = company.register_employee(Employee())
    department_runtime.register_employee(department.department_id, employee)

    task = Task(name="Lifecycle Task")
    snapshot = task_runtime.register_task(task)
    task_runtime.assign_via_orchestrator(snapshot.task_id, department.department_id)
    task_runtime.pause(snapshot.task_id)
    task_runtime.transition(snapshot.task_id, TaskRuntimeState.RUNNING)
    task_runtime.block(snapshot.task_id)
    task_runtime.transition(snapshot.task_id, TaskRuntimeState.QUEUED)
    task_runtime.assign_via_orchestrator(snapshot.task_id, department.department_id)
    task_runtime.complete(snapshot.task_id)

    print("TASK STATE:", task_runtime.snapshot()[0].state.value)
    print("COMPANY STATE:", company.state().value)
    print("DEPARTMENT STATE:", department_runtime.department(department.department_id).state.value)
    print("EMPLOYEE STATE:", company.employees()[0].state.value)
    print("TASK EVENTS:")
    for event in task_runtime.events():
        print(f"- {event.previous_state.value} -> {event.new_state.value}")


if __name__ == "__main__":
    main()