"""End-to-end demonstration for the result runtime lifecycle."""

from __future__ import annotations

from core.departments.runtime import DepartmentRuntime, DepartmentStateChangedEvent
from core.employees import Employee
from core.employees.runtime import EmployeeStateChangedEvent
from core.events.bus import EventBus
from core.observability import ObservabilityProjector
from core.orchestrator import OrchestratorRuntime
from core.results import ResultRuntime, ResultRuntimeState
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
    result_runtime = ResultRuntime(workflow_runtime, event_bus)

    company.initialize_company()
    event_bus.subscribe(CompanyStateChangedEvent, observability.handle_company_event)
    event_bus.subscribe(EmployeeStateChangedEvent, observability.handle_employee_event)
    event_bus.subscribe(DepartmentStateChangedEvent, observability.handle_department_event)
    department = department_runtime.create_department("Operations")
    employee = company.register_employee(Employee())
    department_runtime.register_employee(department.department_id, employee)

    workflow = Workflow(name="Publishing Workflow")
    workflow_runtime.register_workflow(workflow)

    task = Task(name="Result Task")
    task_snapshot = task_runtime.register_task(task)
    workflow_runtime.add_task(workflow.id, task.id)
    task_runtime.assign_via_orchestrator(task.id, department.department_id)
    workflow_runtime.start(workflow.id)
    result_snapshot = result_runtime.create_from_workflow(workflow.id, task.id)
    result_runtime.approve(result_snapshot.result_id)
    result_runtime.publish(result_snapshot.result_id)
    result_runtime.archive(result_snapshot.result_id)

    print("RESULT STATE:", result_runtime.snapshot()[0].state.value)
    print("RESULT SUMMARY:", result_runtime.summary(result_snapshot.result_id))
    print("RESULT EVENTS:")
    for event in result_runtime.events():
        print(f"- {event.previous_state.value} -> {event.new_state.value}")
    print("OBSERVABILITY:", observability.snapshot)


if __name__ == "__main__":
    main()