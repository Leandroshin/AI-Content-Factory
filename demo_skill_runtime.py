"""End-to-end demonstration for the skill runtime lifecycle."""

from __future__ import annotations

from core.departments.runtime import DepartmentRuntime, DepartmentStateChangedEvent
from core.employees import Employee
from core.employees.runtime import EmployeeStateChangedEvent
from core.events.bus import EventBus
from core.knowledge.runtime import KnowledgeRuntime, KnowledgeStateChangedEvent
from core.observability import ObservabilityProjector
from core.orchestrator import OrchestratorRuntime
from core.results.runtime import ResultRuntime, ResultStateChangedEvent
from core.runtime import CompanyRuntime, CompanyStateChangedEvent
from core.skills import SkillCapability, SkillCategory
from core.skills.runtime import SkillRuntime, SkillRuntimeState, SkillStateChangedEvent
from core.tasks import Task
from core.tasks.runtime import TaskRuntime, TaskStateChangedEvent
from core.workflows import Workflow
from core.workflows.runtime import WorkflowRuntime, WorkflowStateChangedEvent


def main() -> None:
    event_bus = EventBus()
    observability = ObservabilityProjector()
    company = CompanyRuntime(event_bus)
    department_runtime = DepartmentRuntime(company, event_bus)
    orchestrator = OrchestratorRuntime(company, department_runtime, event_bus)
    task_runtime = TaskRuntime(company, orchestrator, event_bus)
    workflow_runtime = WorkflowRuntime(company, orchestrator, task_runtime, event_bus)
    result_runtime = ResultRuntime(workflow_runtime, event_bus)
    knowledge_runtime = KnowledgeRuntime(result_runtime, event_bus)
    skill_runtime = SkillRuntime(knowledge_runtime, event_bus)

    company.initialize_company()
    department = department_runtime.create_department("Operations")
    employee = company.register_employee(Employee())
    department_runtime.register_employee(department.department_id, employee)

    event_bus.subscribe(CompanyStateChangedEvent, observability.handle_company_event)
    event_bus.subscribe(DepartmentStateChangedEvent, observability.handle_department_event)
    event_bus.subscribe(EmployeeStateChangedEvent, observability.handle_employee_event)
    event_bus.subscribe(TaskStateChangedEvent, observability.handle_task_event)
    event_bus.subscribe(WorkflowStateChangedEvent, observability.handle_workflow_event)
    event_bus.subscribe(ResultStateChangedEvent, observability.handle_result_event)
    event_bus.subscribe(KnowledgeStateChangedEvent, observability.handle_knowledge_event)
    event_bus.subscribe(SkillStateChangedEvent, observability.handle_skill_event)

    workflow = Workflow(name="Skill Workflow")
    workflow_runtime.register_workflow(workflow)
    task = Task(name="Skill Task")
    task_runtime.register_task(task)
    workflow_runtime.add_task(workflow.id, task.id)
    task_runtime.assign_via_orchestrator(task.id, department.department_id)
    workflow_runtime.start(workflow.id)
    workflow_runtime.complete_task(workflow.id, task.id)

    result_snapshot = result_runtime.create_from_workflow(workflow.id, task.id)
    result_runtime.approve(result_snapshot.result_id)

    knowledge_snapshot = knowledge_runtime.create_from_result(result_snapshot.result_id)
    knowledge_runtime.validate(knowledge_snapshot.knowledge_id)
    knowledge_runtime.publish(knowledge_snapshot.knowledge_id)

    skill_snapshot = skill_runtime.create_from_knowledge(
        knowledge_snapshot.knowledge_id,
        category=SkillCategory.SYSTEM,
        capability=SkillCapability.ANALYZE,
    )
    skill_runtime.evolve(skill_snapshot.skill_id, level=skill_snapshot.level, state=SkillRuntimeState.ACTIVE)
    skill_runtime.associate_employee(skill_snapshot.skill_id, employee.employee_id)

    print("EVENTS:")
    for event in event_bus.events():
        print(f"- {type(event).__name__}")

    print("SNAPSHOTS:")
    print("Company:", observability.snapshot.company.state)
    print("Departments:", observability.snapshot.departments.states)
    print("Employees:", observability.snapshot.employees.states)
    print("Tasks:", observability.snapshot.tasks.states)
    print("Workflows:", observability.snapshot.workflows.states)
    print("Results:", observability.snapshot.results.states)
    print("Knowledge:", observability.snapshot.knowledge.states)
    print("Skills:", observability.snapshot.skills.states)

    print("FINAL STATE:")
    print("Company runtime:", company.state().value)
    print("Workflow:", workflow_runtime.snapshot()[0].state.value)
    print("Result:", result_runtime.snapshot()[0].state.value)
    print("Knowledge:", knowledge_runtime.snapshot()[0].state.value)
    print("Skill:", skill_runtime.snapshot()[0].state.value)


if __name__ == "__main__":
    main()