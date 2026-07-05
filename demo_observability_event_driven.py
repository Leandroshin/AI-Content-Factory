"""Event-driven Observability demonstration."""

from __future__ import annotations

from core.departments.runtime import DepartmentRuntime
from core.employees import Employee
from core.events.bus import EventBus, EventEnvelope
from core.knowledge.runtime import KnowledgeRuntime, KnowledgeType
from core.observability import ObservabilityProjector
from core.orchestrator import OrchestratorRuntime
from core.results.runtime import ResultRuntime
from core.runtime import CompanyRuntime
from core.skills import SkillCapability, SkillCategory
from core.skills.runtime import SkillRuntime, SkillRuntimeState
from core.tasks import Task
from core.tasks.runtime import TaskRuntime
from core.workflows import Workflow
from core.workflows.runtime import WorkflowRuntime


def main() -> None:
    event_bus = EventBus()
    observability = ObservabilityProjector(event_bus)

    company = CompanyRuntime(event_bus)
    department_runtime = DepartmentRuntime(company, event_bus)
    orchestrator = OrchestratorRuntime(company, department_runtime, event_bus)
    task_runtime = TaskRuntime(company, orchestrator, event_bus)
    workflow_runtime = WorkflowRuntime(company, orchestrator, task_runtime, event_bus)
    result_runtime = ResultRuntime(workflow_runtime, event_bus)
    knowledge_runtime = KnowledgeRuntime(result_runtime, event_bus)
    skill_runtime = SkillRuntime(knowledge_runtime, event_bus)

    print("Initializing EventBus and Event-Driven Projector...")
    company.initialize_company()
    department = department_runtime.create_department("Engineering")
    employee = company.register_employee(Employee())
    department_runtime.register_employee(department.department_id, employee)

    workflow = Workflow(name="Release Workflow")
    workflow_runtime.register_workflow(workflow)
    task = Task(name="Code Verification")
    task_runtime.register_task(task)
    workflow_runtime.add_task(workflow.id, task.id)
    task_runtime.assign_via_orchestrator(task.id, department.department_id)
    workflow_runtime.start(workflow.id)
    workflow_runtime.complete_task(workflow.id, task.id)

    result_snapshot = result_runtime.create_from_workflow(workflow.id, task.id)
    result_runtime.approve(result_snapshot.result_id)

    knowledge_snapshot = knowledge_runtime.create_from_result(result_snapshot.result_id, knowledge_type=KnowledgeType.TECHNICAL)
    knowledge_runtime.validate(knowledge_snapshot.knowledge_id)
    knowledge_runtime.publish(knowledge_snapshot.knowledge_id)

    skill_snapshot = skill_runtime.create_from_knowledge(
        knowledge_snapshot.knowledge_id,
        category=SkillCategory.SYSTEM,
        capability=SkillCapability.ANALYZE,
    )
    skill_runtime.evolve(skill_snapshot.skill_id, level=skill_snapshot.level, state=SkillRuntimeState.ACTIVE)
    skill_runtime.associate_employee(skill_snapshot.skill_id, employee.employee_id)

    print("\n--- Events Published ---")
    for event in event_bus.events():
        print(f"- {EventEnvelope.get_event_type(event)} | entity={EventEnvelope.get_entity_id(event)}")

    print("\n--- Snapshots Updated ---")
    print("Company:", observability.snapshot.company.state)
    print("Departments:", observability.snapshot.departments.states)
    print("Employees:", observability.snapshot.employees.states)
    print("Tasks:", observability.snapshot.tasks.states)
    print("Workflows:", observability.snapshot.workflows.states)
    print("Results:", observability.snapshot.results.states)
    print("Knowledge:", observability.snapshot.knowledge.states)
    print("Skills:", observability.snapshot.skills.states)

    print("\n--- Final Platform Projection ---")
    print("Company runtime:", company.state().value)
    print("Workflow runtime:", workflow_runtime.snapshot()[0].state.value)
    print("Result runtime:", result_runtime.snapshot()[0].state.value)
    print("Knowledge runtime:", knowledge_runtime.snapshot()[0].state.value)
    print("Skill runtime:", skill_runtime.snapshot()[0].state.value)
    print("Task record:", observability.snapshot.task_records[str(task.id)].state)

    assert observability.snapshot.company.state == company.state().value
    assert observability.snapshot.departments.states[str(department.department_id)] == department_runtime.department(department.department_id).state.value
    assert observability.snapshot.employees.states[str(employee.employee_id)] == company.employee_runtime.snapshot()[0].state.value
    assert observability.snapshot.tasks.states[str(task.id)] == task_runtime.snapshot()[0].state.value
    assert observability.snapshot.workflows.states[str(workflow.id)] == workflow_runtime.snapshot()[0].state.value
    assert observability.snapshot.results.states[str(result_snapshot.result_id)] == result_runtime.snapshot()[0].state.value
    assert observability.snapshot.knowledge.states[str(knowledge_snapshot.knowledge_id)] == knowledge_runtime.snapshot()[0].state.value
    assert observability.snapshot.skills.states[str(skill_snapshot.skill_id)] == skill_runtime.snapshot()[0].state.value

    print("\n[SUCCESS] Event-driven observability verification complete.")


if __name__ == "__main__":
    main()