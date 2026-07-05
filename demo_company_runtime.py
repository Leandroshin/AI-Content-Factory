"""Demonstration script for the first integrated Company Runtime flow."""

from __future__ import annotations

from core.employees import Employee
from core.runtime import CompanyRuntime


def main() -> None:
    runtime = CompanyRuntime()
    runtime.initialize_company()
    employee = Employee()
    employee_snapshot = runtime.register_employee(employee)
    task = runtime.register_task("Demo Task")
    runtime.assign_task(employee_snapshot.employee_id, task.task_id)
    runtime.complete_task(employee_snapshot.employee_id, task.task_id)

    print("FINAL COMPANY STATE:", runtime.state().value)
    print("EMPLOYEES:")
    for snapshot in runtime.employees():
        print(f"- {snapshot.employee_id} | {snapshot.name} | {snapshot.state.value} | task={snapshot.task_id}")
    print("TASKS:")
    for task_record in runtime.tasks():
        print(f"- {task_record.task_id} | {task_record.title} | {task_record.state}")
    print("EVENTS:")
    for event in runtime.events():
        if hasattr(event, "reason"):
            print(f"- company {event.previous_state.value} -> {event.new_state.value}")
        else:
            print(f"- employee {event.previous_state.value} -> {event.new_state.value} for {event.employee_id}")
    print("OBSERVABILITY SNAPSHOTS:", len(runtime.observability_snapshots()))


if __name__ == "__main__":
    main()