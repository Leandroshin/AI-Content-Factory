"""Department runtime demonstration."""

from __future__ import annotations

from core.departments.runtime import DepartmentRuntime
from core.employees import Employee
from core.runtime import CompanyRuntime


def main() -> None:
    company = CompanyRuntime()
    company.initialize_company()

    department_runtime = DepartmentRuntime(company)
    department = department_runtime.create_department("Operations")

    employee_one = company.register_employee(Employee())
    employee_two = company.register_employee(Employee())
    department_runtime.register_employee(department.department_id, employee_one)
    department_runtime.register_employee(department.department_id, employee_two)

    task = company.register_task("Department Task")
    company.assign_task(employee_one.employee_id, task.task_id)
    department_runtime.sync_employee_state(department.department_id, company.employee_runtime.events()[-1])
    company.complete_task(employee_one.employee_id, task.task_id)
    department_runtime.sync_employee_state(department.department_id, company.employee_runtime.events()[-1])

    print("COMPANY STATE:", company.state().value)
    print("DEPARTMENT STATE:", department_runtime.department(department.department_id).state.value)
    print("EMPLOYEES:")
    for snapshot in company.employees():
        print(f"- {snapshot.employee_id} | {snapshot.state.value}")
    print("DEPARTMENT EVENTS:")
    for event in department_runtime.events():
        print(f"- {event.previous_state.value} -> {event.new_state.value}")
    print("COMPANY EVENTS:")
    for event in company.events():
        if hasattr(event, "reason"):
            print(f"- company {event.previous_state.value} -> {event.new_state.value}")
        else:
            print(f"- employee {event.previous_state.value} -> {event.new_state.value} for {event.employee_id}")


if __name__ == "__main__":
    main()