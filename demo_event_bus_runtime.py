"""Demonstration of the internal event bus across runtime layers."""

from __future__ import annotations

from core.departments.runtime import DepartmentRuntime
from core.employees import Employee
from core.employees.runtime import EmployeeStateChangedEvent
from core.events.bus import EventBus
from core.observability import ObservabilityProjector
from core.runtime import CompanyRuntime, CompanyStateChangedEvent


def main() -> None:
    event_bus = EventBus()
    observability = ObservabilityProjector()
    event_bus.subscribe(object, lambda event: None)
    event_bus.subscribe(type(observability.snapshot), lambda event: None)

    company = CompanyRuntime(event_bus)

    company.initialize_company()
    event_bus.subscribe(CompanyStateChangedEvent, lambda event: None)
    event_bus.subscribe(EmployeeStateChangedEvent, lambda event: None)
    event_bus.subscribe(type(observability.snapshot), lambda event: None)
    event_bus.subscribe(CompanyStateChangedEvent, observability.handle_company_event)
    event_bus.subscribe(EmployeeStateChangedEvent, observability.handle_employee_event)
    employee = Employee()
    employee_snapshot = company.register_employee(employee)
    department_runtime = DepartmentRuntime(company, event_bus)
    department = department_runtime.create_department("Operations")
    department_runtime.register_employee(department.department_id, employee_snapshot)
    task = company.register_task("Bus Task")
    company.assign_task(employee_snapshot.employee_id, task.task_id)
    department_runtime.sync_employee_state(department.department_id, company.employee_runtime.events()[-1])
    company.complete_task(employee_snapshot.employee_id, task.task_id)
    department_runtime.sync_employee_state(department.department_id, company.employee_runtime.events()[-1])

    print("COMPANY STATE:", company.state().value)
    print("DEPARTMENT STATE:", department_runtime.department(department.department_id).state.value)
    print("EMPLOYEE STATE:", company.employees()[0].state.value)
    print("EVENT BUS EVENTS:", len(event_bus.events()))
    print("OBSERVABILITY:", observability.snapshot)


if __name__ == "__main__":
    main()