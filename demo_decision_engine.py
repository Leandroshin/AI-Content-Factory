"""Demonstration script for the deterministic Decision Engine foundation."""

from __future__ import annotations

from core.departments.runtime import DepartmentRuntime
from core.employees import Employee
from core.events.bus import EventBus
from core.knowledge.runtime import KnowledgeRuntime
from core.observability import ObservabilityProjector
from core.orchestrator import OrchestratorRuntime
from core.results.runtime import ResultRuntime
from core.runtime import CompanyRuntime
from core.skills import SkillCapability, SkillCategory
from core.skills.runtime import SkillRuntime
from core.tasks import Task
from core.tasks.runtime import TaskRuntime
from core.workflows import Workflow
from core.workflows.runtime import WorkflowRuntime
from core.decision.runtime import DecisionEngine, DecisionContextBuilder


def main() -> None:
    print("Initializing Runtimes and EventBus...")
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

    company.initialize_company()
    department = department_runtime.create_department("Engineering")

    # 1. Register two employees
    print("\nRegistering Employees (Alice and Bob)...")
    alice_employee = Employee()
    alice_employee.profile.full_name = "Alice"
    alice = company.register_employee(alice_employee)
    department_runtime.register_employee(department.department_id, alice)

    bob_employee = Employee()
    bob_employee.profile.full_name = "Bob"
    bob = company.register_employee(bob_employee)
    department_runtime.register_employee(department.department_id, bob)

    # Both are idle (Booting transitions to Idle automatically on registration)
    assert str(alice.state).lower() == "idle"
    assert str(bob.state).lower() == "idle"

    # 2. Establish a skill that Alice possesses
    print("\nLearning a skill and associating it with Alice...")
    workflow = Workflow(name="Design Review")
    workflow_runtime.register_workflow(workflow)
    task_setup = Task(name="Create Skill Asset")
    task_runtime.register_task(task_setup)
    workflow_runtime.add_task(workflow.id, task_setup.id)

    # Alice executes the setup task to learn the skill
    task_runtime.assign_via_orchestrator(task_setup.id, department.department_id)
    workflow_runtime.start(workflow.id)
    workflow_runtime.complete_task(workflow.id, task_setup.id)

    result_snap = result_runtime.create_from_workflow(workflow.id, task_setup.id)
    result_runtime.approve(result_snap.result_id)

    knowledge_snap = knowledge_runtime.create_from_result(result_snap.result_id)
    knowledge_runtime.validate(knowledge_snap.knowledge_id)
    knowledge_runtime.publish(knowledge_snap.knowledge_id)

    skill_snap = skill_runtime.create_from_knowledge(
        knowledge_snap.knowledge_id,
        category=SkillCategory.SYSTEM,
        capability=SkillCapability.ANALYZE,
    )

    # Associate skill with Alice
    skill_runtime.associate_employee(skill_snap.skill_id, alice.employee_id)

    # 3. Register the target evaluation Task
    print("\nRegistering Evaluation Task...")
    target_task = Task(name="Architecture Validation")
    # Add tags to indicate skill requirements
    target_task.metadata.tags = ["design review"]
    task_runtime.register_task(target_task)

    # Get snapshots from Runtimes (Strictly snapshots)
    task_snapshot = task_runtime.snapshot()[-1]
    employee_snapshots = company.employees()
    skill_snapshots = skill_runtime.snapshot()
    department_snapshot = department_runtime.department(department.department_id)

    # 4. Construct DecisionContext using ContextBuilder
    print("\nAssembling DecisionContext using DecisionContextBuilder...")
    context_builder = DecisionContextBuilder()

    # Alice and Bob are the candidates. We pass custom policies requiring "design review" skill
    policies = {
        "required_skills": ["design review"]
    }

    context = context_builder.build_assignment_context(
        task_snapshot=task_snapshot,
        candidate_snapshots=employee_snapshots,
        department_snapshot=department_snapshot,
        skill_snapshots=skill_snapshots,
        active_policies=policies,
    )

    # 5. Invoke DecisionEngine
    print("\nInvoking DecisionEngine to select best candidate...")
    engine = DecisionEngine()
    result = engine.choose_best_candidate(context)

    # 6. Print outcome and structured trace
    print("\n--- Evaluation Decision Result ---")
    print(f"Decision ID: {result.decision_id}")
    print(f"Approved: {result.approved}")
    print(f"Decision Code: {result.decision_code}")
    print(f"Chosen Candidate: {result.chosen_candidate_id}")
    print(f"Explanation: {result.explanation}")

    print("\n--- Structured Decision Trace ---")
    print(f"Stages Evaluated: {result.trace.stages_evaluated}")
    print(f"Candidates Selected (IDLE + Dept): {result.trace.candidates_selected}")
    print(f"Candidates Scored: {result.trace.candidates_scored}")
    print(f"Constraints Checked: {result.trace.constraints_checked}")
    print(f"Rejections: {result.trace.rejection_reasons}")
    print(f"Execution Time: {result.trace.execution_time_ms:.4f} ms")

    # Alice should be the chosen one because she has the matched skill
    assert result.approved is True
    assert result.chosen_candidate_id == alice.employee_id
    assert result.trace.candidates_scored[str(alice.employee_id)] == 1.0
    assert result.trace.candidates_scored[str(bob.employee_id)] == 0.0

    print("\n[SUCCESS] Verification complete. Alice was deterministically chosen based on skill match!")


if __name__ == "__main__":
    main()
