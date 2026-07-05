"""End-to-end demonstration for the AI Company task flow."""

from __future__ import annotations

from core.departments.runtime import DepartmentRuntime, DepartmentStateChangedEvent
from core.employees import Employee
from core.employees.runtime import EmployeeStateChangedEvent
from core.events.bus import EventBus
from core.observability import ObservabilityProjector
from core.orchestrator import OrchestratorRuntime
from core.runtime import CompanyRuntime, CompanyStateChangedEvent


def main() -> None:
    event_bus = EventBus()
    observability = ObservabilityProjector()
    company = CompanyRuntime(event_bus)
    department_runtime = DepartmentRuntime(company, event_bus)
    orchestrator = OrchestratorRuntime(company, department_runtime, event_bus)

    company.initialize_company()
    event_bus.subscribe(CompanyStateChangedEvent, observability.handle_company_event)
    event_bus.subscribe(EmployeeStateChangedEvent, observability.handle_employee_event)
    event_bus.subscribe(DepartmentStateChangedEvent, observability.handle_department_event)
    department = department_runtime.create_department("Operations")
    employee_one = company.register_employee(Employee())
    employee_two = company.register_employee(Employee())
    department_runtime.register_employee(department.department_id, employee_one)
    department_runtime.register_employee(department.department_id, employee_two)

    received = orchestrator.receive_task("End-to-End Task")
    chosen = orchestrator.choose_employee(department.department_id)
    orchestrator.route_task(received.task.task_id, department.department_id, chosen.employee_id)
    orchestrator.complete_task(received.task.task_id)

    print("COMPANY STATE:", company.state().value)
    print("DEPARTMENT STATE:", department_runtime.department(department.department_id).state.value)
    print("EMPLOYEES:")
    for snapshot in company.employees():
        print(f"- {snapshot.employee_id} | {snapshot.state.value} | task={snapshot.task_id}")
    print("ORCHESTRATOR EVENTS:")
    for event in orchestrator.events():
        print(f"- {event.stage} | task={event.task_id}")
    print("BUS EVENTS:", len(event_bus.events()))
    print("OBSERVABILITY:", observability.snapshot)


if __name__ == "__main__":
    main()