"""End-to-end demonstration for the workflow runtime lifecycle."""

from __future__ import annotations

from core.departments.runtime import DepartmentRuntime, DepartmentStateChangedEvent
from core.employees import Employee
from core.employees.runtime import EmployeeStateChangedEvent
from core.events.bus import EventBus
from core.observability import ObservabilityProjector
from core.orchestrator import OrchestratorRuntime
from core.runtime import CompanyRuntime, CompanyStateChangedEvent
from core.tasks import Task
from core.tasks.runtime import TaskRuntime
from core.workflows import Workflow
from core.workflows.runtime import WorkflowRuntime


def main() -> None:
    event_bus = EventBus()
    observability = ObservabilityProjector()
    company = CompanyRuntime(event_bus)
    department_runtime = DepartmentRuntime(company, event_bus)
    orchestrator = OrchestratorRuntime(company, department_runtime, event_bus)
    task_runtime = TaskRuntime(company, orchestrator, event_bus)
    workflow_runtime = WorkflowRuntime(company, orchestrator, task_runtime, event_bus)

    company.initialize_company()
    event_bus.subscribe(CompanyStateChangedEvent, observability.handle_company_event)
    event_bus.subscribe(EmployeeStateChangedEvent, observability.handle_employee_event)
    event_bus.subscribe(DepartmentStateChangedEvent, observability.handle_department_event)
    department = department_runtime.create_department("Operations")
    employee = company.register_employee(Employee())
    department_runtime.register_employee(department.department_id, employee)

    workflow = Workflow(name="Editorial Workflow")
    workflow_snapshot = workflow_runtime.register_workflow(workflow)

    task_one = Task(name="Task One")
    task_two = Task(name="Task Two")
    task_runtime.register_task(task_one)
    task_runtime.register_task(task_two)
    workflow_runtime.add_task(workflow.id, task_one.id)
    workflow_runtime.add_task(workflow.id, task_two.id)

    workflow_runtime.start(workflow.id)
    workflow_runtime.complete_task(workflow.id, task_one.id)
    workflow_runtime.complete_task(workflow.id, task_two.id)

    print("WORKFLOW STATE:", workflow_runtime.snapshot()[0].state.value)
    print("WORKFLOW PROGRESS:", workflow_runtime.progress(workflow.id))
    print("TASK STATES:")
    for task_snapshot in task_runtime.snapshot():
        print(f"- {task_snapshot.name} | {task_snapshot.state.value}")
    print("WORKFLOW EVENTS:")
    for event in workflow_runtime.events():
        print(f"- {event.previous_state.value} -> {event.new_state.value} | progress={event.progress}")
    print("OBSERVABILITY:", observability.snapshot)


if __name__ == "__main__":
    main()