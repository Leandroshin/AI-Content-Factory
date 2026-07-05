"""Demonstration script for DepartmentManager — first manager of AI Company.

Flow:
  1. CEO receives a business objective -> clarifying questions -> answers -> ExecutivePlan
  2. DepartmentManager receives the plan -> decomposes deliverables into tasks
  3. Employees are registered and tasks are assigned
  4. Tasks progress through states: assigned -> in_progress -> completed
  5. DepartmentManager reports progress
  6. All events are verified
"""

from __future__ import annotations

from uuid import UUID

from core.company.ceo import CEORuntime, ExecutivePlan
from core.company.department_manager import (
    DepartmentManager,
    PlanReceived,
    ProgressReported,
    TaskAssigned,
    TaskCompleted,
    TasksDecomposed,
)
from core.employees import Employee
from core.events.bus import EventBus
from core.runtime import CompanyRuntime


def _answer_all(ceo: CEORuntime, goal_id: UUID, answers: dict[str, str]) -> ExecutivePlan | None:
    for field, value in answers.items():
        ceo.answer_question(goal_id, field, value)
    last_field = list(answers.keys())[-1]
    r = ceo.answer_question(goal_id, last_field, answers[last_field])
    return r.plan if r.success else None


def main() -> None:
    print("=" * 60)
    print("DepartmentManager — First Manager of AI Company")
    print("=" * 60)

    # ------------------------------------------------------------------
    # Setup
    # ------------------------------------------------------------------
    event_bus = EventBus()
    company = CompanyRuntime(event_bus)
    company.initialize_company()
    ceo = CEORuntime(company, event_bus)
    manager = DepartmentManager(company, event_bus)

    # ==================================================================
    # Step 1: CEO creates an ExecutivePlan
    # ==================================================================
    print("\n" + "=" * 60)
    print("Step 1: CEO receives a business objective")
    print("=" * 60)

    result = ceo.receive_goal("criar cortes de um podcast")
    assert result.success
    assert len(result.questions) > 0

    plan = _answer_all(ceo, result.goal_id, {
        "duration": "30-60 seconds",
        "quantity": "20",
        "format": "vertical",
        "platform": "TikTok, Instagram Reels",
        "subtitles": "auto-generated",
        "frequency": "daily",
        "guests": "0",
        "content_type": "short clips",
        "language": "Portuguese",
        "tone": "entertaining",
        "word_count": "N/A",
        "timeline": "2 weeks",
        "priority": "high",
    })
    assert plan is not None
    assert len(plan.deliverables) >= 2
    assert "Video Editing" in plan.departments

    print(f"\n  ExecutivePlan generated:")
    print(f"    Objective: {plan.objective}")
    print(f"    Departments: {', '.join(plan.departments)}")
    print(f"    Priority: {plan.priority}")
    print(f"    Deliverables ({len(plan.deliverables)}):")
    for d in plan.deliverables:
        print(f"      - {d}")

    # ==================================================================
    # Step 2: DepartmentManager receives the plan
    # ==================================================================
    print("\n" + "=" * 60)
    print("Step 2: DepartmentManager receives the ExecutivePlan")
    print("=" * 60)

    plan_result = manager.receive_plan(plan)
    assert plan_result.success
    assert len(plan_result.tasks) > 0

    total_tasks = len(plan_result.tasks)
    print(f"\n  Plan received. Decomposed into {total_tasks} tasks.")

    # Group tasks by department
    dept_groups: dict[str, list[str]] = {}
    for task in plan_result.tasks:
        dept_groups.setdefault(task.department, []).append(task.title)

    for dept, tasks in dept_groups.items():
        print(f"\n  [{dept}] — {len(tasks)} tasks:")
        for t in tasks:
            print(f"    - {t}")

    # ==================================================================
    # Step 3: Register employees and assign tasks
    # ==================================================================
    print("\n" + "=" * 60)
    print("Step 3: Register employees and assign tasks")
    print("=" * 60)

    emp1 = company.register_employee(Employee())
    emp2 = company.register_employee(Employee())
    company.register_employee(Employee())
    print(f"\n  Registered 3 employees.")
    print(f"    Employee 1: {emp1.employee_id}")
    print(f"    Employee 2: {emp2.employee_id}")

    # Assign first two tasks
    task_ids = [t.task_id for t in plan_result.tasks]
    a1 = manager.assign_task(task_ids[0], emp1.employee_id)
    assert a1.success
    print(f"\n  Assigned task 1 to Employee 1: {plan_result.tasks[0].title}")

    a2 = manager.assign_task(task_ids[1], emp2.employee_id)
    assert a2.success
    print(f"  Assigned task 2 to Employee 2: {plan_result.tasks[1].title}")

    # Try assigning same task again (should fail)
    a3 = manager.assign_task(task_ids[0], emp2.employee_id)
    assert not a3.success
    print(f"  Re-assign attempt correctly rejected: {a3.error_message}")

    # ==================================================================
    # Step 4: Execute tasks through states
    # ==================================================================
    print("\n" + "=" * 60)
    print("Step 4: Execute tasks (assigned -> in_progress -> completed)")
    print("=" * 60)

    s1 = manager.start_task(task_ids[0], emp1.employee_id)
    assert s1.success
    print(f"  Task 1 started (-> in_progress).")

    c1 = manager.complete_task(task_ids[0], emp1.employee_id, success=True)
    assert c1.success
    print(f"  Task 1 completed successfully.")

    c2 = manager.complete_task(task_ids[1], emp2.employee_id, success=True)
    assert c2.success
    print(f"  Task 2 completed successfully.")

    # ==================================================================
    # Step 5: Report progress
    # ==================================================================
    print("\n" + "=" * 60)
    print("Step 5: Progress report")
    print("=" * 60)

    progress_result = manager.report_progress(plan.plan_id)
    assert progress_result.success
    report = progress_result.progress
    assert report is not None

    print(f"\n  Overall: {report.completed}/{report.total} tasks completed")
    print(f"  Progress: {report.progress_pct}%")
    print(f"\n  Per deliverable:")
    for name, done, total in report.deliverables_progress:
        pct = round(done / total * 100, 1) if total > 0 else 0.0
        print(f"    - {name}: {done}/{total} ({pct}%)")

    # ==================================================================
    # Step 6: Plan state inspection
    # ==================================================================
    print("\n" + "=" * 60)
    print("Step 6: Plan state inspection")
    print("=" * 60)

    state = manager.plan_state(plan.plan_id)
    assert state is not None
    print(f"\n  Objective: {state['objective']}")
    print(f"  Departments: {', '.join(state['departments'])}")
    print(f"  Tasks: {state['completed_tasks']}/{state['total_tasks']} completed ({state['progress_pct']}%)")
    print(f"  Tasks by department: {state['tasks_by_department']}")

    all_plans = manager.list_plans()
    print(f"\n  Active plans: {len(all_plans)}")
    for p in all_plans:
        print(f"    - {p['objective'][:40]:40s} ({p['task_count']} tasks)")

    # ==================================================================
    # Step 7: Event verification
    # ==================================================================
    print("\n" + "=" * 60)
    print("Step 7: Event verification")
    print("=" * 60)

    all_events = event_bus.events()
    plan_events = [e for e in all_events if isinstance(e, PlanReceived)]
    decompose_events = [e for e in all_events if isinstance(e, TasksDecomposed)]
    assign_events = [e for e in all_events if isinstance(e, TaskAssigned)]
    complete_events = [e for e in all_events if isinstance(e, TaskCompleted)]
    progress_events = [e for e in all_events if isinstance(e, ProgressReported)]

    print(f"  PlanReceived events: {len(plan_events)}")
    print(f"  TasksDecomposed events: {len(decompose_events)}")
    print(f"  TaskAssigned events: {len(assign_events)}")
    print(f"  TaskCompleted events: {len(complete_events)}")
    print(f"  ProgressReported events: {len(progress_events)}")
    print(f"  Total CEO + DM events: {len(all_events)}")

    assert len(plan_events) >= 1
    assert len(decompose_events) >= 1
    assert len(assign_events) >= 2
    assert len(complete_events) >= 2
    assert len(progress_events) >= 1

    # ==================================================================
    # Scenario 8: Edge cases
    # ==================================================================
    print("\n" + "=" * 60)
    print("Step 8: Edge cases")
    print("=" * 60)

    from uuid import UUID
    fake_id = UUID("00000000-0000-0000-0000-000000000000")

    r1 = manager.assign_task(fake_id, emp1.employee_id)
    assert not r1.success
    print(f"  Assign unknown task: {r1.error_message}")

    r2 = manager.complete_task(fake_id, emp1.employee_id)
    assert not r2.success
    print(f"  Complete unknown task: {r2.error_message}")

    r3 = manager.report_progress(fake_id)
    assert not r3.success
    print(f"  Report unknown plan: {r3.error_message}")

    assert manager.plan_state(fake_id) is None
    print(f"  State for unknown plan: None")

    # ==================================================================
    # Summary
    # ==================================================================
    print("\n" + "=" * 60)
    print("DEPARTMENT MANAGER DEMONSTRATION SUMMARY")
    print("=" * 60)

    checks = [
        ("CEO plan created", plan is not None, True),
        ("DM received plan", plan_result.success, True),
        ("Tasks decomposed", len(plan_result.tasks) > 0, True),
        ("Task assigned to emp1", a1.success, True),
        ("Task assigned to emp2", a2.success, True),
        ("Re-assign rejected", not a3.success, True),
        ("Task started (in_progress)", s1.success, True),
        ("Task 1 completed", c1.success, True),
        ("Task 2 completed", c2.success, True),
        ("Progress report generated", progress_result.success, True),
        ("Progress has correct data", report is not None and report.progress_pct > 0, True),
        ("Plan state accessible", state is not None and state["total_tasks"] > 0, True),
        ("PlanReceived event", len(plan_events) >= 1, True),
        ("TasksDecomposed event", len(decompose_events) >= 1, True),
        ("TaskAssigned events (2)", len(assign_events) >= 2, True),
        ("TaskCompleted events (2)", len(complete_events) >= 2, True),
        ("ProgressReported event", len(progress_events) >= 1, True),
        ("Unknown task assign returns error", not r1.success, True),
        ("Unknown task complete returns error", not r2.success, True),
        ("Unknown plan report returns error", not r3.success, True),
    ]

    passed = sum(1 for _, v, e in checks if v == e)
    failed = sum(1 for _, v, e in checks if v != e)

    for label, result_val, expected in checks:
        if result_val != expected:
            print(f"  FAIL: {label} (expected {expected}, got {result_val})")

    print(f"\n  Total: {passed}/{passed + failed} passed, {failed} failed")
    print(f"  Total events published: {len(all_events)}")
    print(f"  Company tasks registered: {len(company.tasks())}")
    print(f"  DM is generic: knows no specific domain\n")


if __name__ == "__main__":
    main()
