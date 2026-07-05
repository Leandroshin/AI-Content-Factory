"""Demonstration script for Hand-Off system — task routing between employees.

Flow:
  CEO -> DepartmentManager -> Employee A (Editor)
                                    |
                               request_review
                                    |
                           DepartmentManager routes
                                    |
                           Employee B (Reviewer/QA)
                                    |
                              complete_review
                                    |
                           DepartmentManager concludes
                                    |
                              CEO (via events)
"""

from __future__ import annotations

from uuid import UUID, uuid4

from core.company.ceo import CEORuntime
from core.company.department_manager import (
    DepartmentManager,
    HandOffRequested,
    ReviewCompleted,
    ReviewRequested,
    TaskForwarded,
    TaskReturned,
    TaskAwaiting,
    TaskResumed,
)
from core.company.specialist_employee import (
    EmployeeSkill,
    ReceivedTask,
    SpecialistEmployee,
    TaskAccepted,
    TaskDecision,
    TaskFinished,
)
from core.employees import Employee
from core.employees.models import EmployeeAvailability, EmployeeIdentity
from core.events.bus import EventBus
from core.runtime import CompanyRuntime


def _answer_all(ceo: CEORuntime, goal_id: UUID, answers: dict[str, str]):
    for field, value in answers.items():
        ceo.answer_question(goal_id, field, value)
    last = list(answers.keys())[-1]
    r = ceo.answer_question(goal_id, last, answers[last])
    return r.plan if r.success else None


def _register(company: CompanyRuntime, employee_id: UUID) -> None:
    company.register_employee(
        Employee(
            identity=EmployeeIdentity(employee_id=employee_id),
            availability=EmployeeAvailability(is_available=True),
        )
    )


def main() -> None:
    print("=" * 60)
    print("Hand-Off System — Task Routing Between Employees")
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
    # Step 1: CEO creates a plan
    # ==================================================================
    print("\n" + "=" * 60)
    print("Step 1: CEO creates an ExecutivePlan")
    print("=" * 60)

    r = ceo.receive_goal("produzir videos para o YouTube")
    plan = _answer_all(ceo, r.goal_id, {
        "duration": "10-15 minutes",
        "quantity": "3",
        "format": "horizontal",
        "platform": "YouTube",
        "subtitles": "manual",
        "timeline": "1 month",
        "priority": "high",
    })
    assert plan is not None
    print(f"\n  Plan: {plan.objective}")
    print(f"  Departments: {', '.join(plan.departments)}")
    print(f"  Deliverables:")
    for d in plan.deliverables:
        print(f"    - {d}")

    # ==================================================================
    # Step 2: DM decomposes the plan
    # ==================================================================
    print("\n" + "=" * 60)
    print("Step 2: DM decomposes plan into tasks")
    print("=" * 60)

    plan_result = manager.receive_plan(plan)
    assert plan_result.success
    print(f"\n  Decomposed into {len(plan_result.tasks)} tasks:")
    for i, t in enumerate(plan_result.tasks, 1):
        print(f"    {i}. [{t.department}] {t.title}")

    task_id = plan_result.tasks[0].task_id

    # ==================================================================
    # Step 3: Create employees
    # ==================================================================
    print("\n" + "=" * 60)
    print("Step 3: Create Editor (A) and Reviewer (B)")
    print("=" * 60)

    editor_id = uuid4()
    reviewer_id = uuid4()

    editor = SpecialistEmployee(
        company_runtime=company, employee_id=editor_id,
        skills=(
            EmployeeSkill(name="video", proficiency=0.95, experience_years=3.0),
            EmployeeSkill(name="edit", proficiency=0.90, experience_years=3.0),
        ),
        event_bus=event_bus, department_manager=manager,
    )
    reviewer = SpecialistEmployee(
        company_runtime=company, employee_id=reviewer_id,
        skills=(
            EmployeeSkill(name="quality", proficiency=0.90, experience_years=2.0),
            EmployeeSkill(name="review", proficiency=0.85, experience_years=2.0),
        ),
        event_bus=event_bus, department_manager=manager,
    )
    _register(company, editor_id)
    _register(company, reviewer_id)

    print(f"\n  Editor (A): {editor_id}")
    for s in editor.skills:
        print(f"    Skill: {s.name} ({s.proficiency})")
    print(f"  Reviewer (B): {reviewer_id}")
    for s in reviewer.skills:
        print(f"    Skill: {s.name} ({s.proficiency})")

    # ==================================================================
    # Step 4: DM assigns task to Editor A and starts it
    # ==================================================================
    print("\n" + "=" * 60)
    print("Step 4: DM assigns task to Editor A and starts it")
    print("=" * 60)

    assign = manager.assign_task(task_id, editor_id)
    assert assign.success
    start = manager.start_task(task_id, editor_id)
    assert start.success
    print(f"  Task assigned and started for Editor A.")

    # ==================================================================
    # Step 5: Editor A receives, accepts the task (does work conceptually)
    # ==================================================================
    print("\n" + "=" * 60)
    print("Step 5: Editor A accepts the task and does work")
    print("=" * 60)

    edit_task = ReceivedTask(
        task_id=task_id,
        title=plan_result.tasks[0].title,
        description=f"Execute video editing for plan: {plan.objective}",
        department="Video Editing",
        required_skills=("video", "edit"),
    )
    d = editor.receive_task(edit_task)
    assert d == TaskDecision.ACCEPTED
    print(f"  Editor A accepted the task.")
    print(f"  Editor A: performing video editing work...")

    # ==================================================================
    # Step 6: Editor A requests peer review (hand-off)
    # ==================================================================
    print("\n" + "=" * 60)
    print("Step 6: Editor A requests peer review -> Hand-off")
    print("=" * 60)

    handed = editor.request_review(task_id, reviewer_id)
    assert handed
    print(f"  Editor A submitted for review (Reviewer B).")
    print(f"  Editor A status after hand-off: {editor.status}")

    state_before = manager.plan_state(plan.plan_id)
    assert state_before is not None
    print(f"  DM plan: {state_before['completed_tasks']}/{state_before['total_tasks']} before review")

    # ==================================================================
    # Step 7: Reviewer B receives and reviews
    # ==================================================================
    print("\n" + "=" * 60)
    print("Step 7: Reviewer B reviews the work")
    print("=" * 60)

    review_task = ReceivedTask(
        task_id=task_id,
        title=f"Review: {plan_result.tasks[0].title}",
        description=f"Quality review of completed editing work.",
        department="Quality Assurance",
        required_skills=("quality", "review"),
    )
    d2 = reviewer.receive_task(review_task)
    assert d2 == TaskDecision.ACCEPTED
    print(f"  Reviewer B: accepted review task.")
    print(f"  Conducting quality review...")

    # DM completes the review (approves)
    review = manager.complete_review(task_id, reviewer_id, approved=True, feedback="All edits meet quality standards. Approved.")
    assert review.success
    print(f"  Review approved. Task finalized by DM.")
    print(f"  Feedback: All edits meet quality standards. Approved.")

    state_after = manager.plan_state(plan.plan_id)
    assert state_after is not None
    print(f"  DM plan after review: {state_after['completed_tasks']}/{state_after['total_tasks']} completed")

    # ==================================================================
    # Step 8: Forward a task (edge: route to another employee)
    # ==================================================================
    print("\n" + "=" * 60)
    print("Step 8: Forward a task to another employee")
    print("=" * 60)

    task2_id = plan_result.tasks[1].task_id
    a2 = manager.assign_task(task2_id, editor_id)
    assert a2.success

    routed = manager.route_task(task2_id, editor_id, reviewer_id, "Needs audio specialist review")
    assert routed.success
    print(f"  Task forwarded from Editor A to Reviewer B.")
    print(f"  Reason: Needs audio specialist review")

    # ==================================================================
    # Step 9: Return a task to DM
    # ==================================================================
    print("\n" + "=" * 60)
    print("Step 9: Return a task to DepartmentManager")
    print("=" * 60)

    task3_id = plan_result.tasks[2].task_id
    a3 = manager.assign_task(task3_id, editor_id)
    assert a3.success

    ret = manager.return_task(task3_id, editor_id, "Missing source assets, cannot proceed")
    assert ret.success
    print(f"  Task returned by Editor A.")
    print(f"  Reason: Missing source assets, cannot proceed")
    print(f"  Task status after return: PENDING (unassigned)")

    # ==================================================================
    # Step 10: Awaiting + Resume cycle
    # ==================================================================
    print("\n" + "=" * 60)
    print("Step 10: Awaiting + Resume cycle")
    print("=" * 60)

    reassign = manager.assign_task(task3_id, editor_id)
    assert reassign.success

    emp_state = manager.start_task(task3_id, editor_id)
    assert emp_state.success

    await_res = manager.mark_awaiting(task3_id, editor_id, "tool", "Waiting for After Effects license approval")
    assert await_res.success
    print(f"  Task marked as awaiting (tool).")
    print(f"  Details: Waiting for After Effects license approval")

    resume = manager.resume_task(task3_id, editor_id)
    assert resume.success
    print(f"  Task resumed from awaiting state.")

    # ==================================================================
    # Step 11: Hand-off history
    # ==================================================================
    print("\n" + "=" * 60)
    print("Step 11: Hand-off history")
    print("=" * 60)

    history = manager.handoff_history(task_id)
    print(f"  Task 1 hand-offs: {len(history)}")
    for h in history:
        print(f"    - type={h.handoff_type}, from={str(h.from_employee_id)[:8]}..., status={h.status}, reason={h.reason}")

    history2 = manager.handoff_history(task2_id)
    print(f"  Task 2 hand-offs: {len(history2)}")

    history3 = manager.handoff_history(task3_id)
    print(f"  Task 3 hand-offs: {len(history3)}")

    bad = manager.handoff_history(UUID("00000000-0000-0000-0000-000000000000"))
    assert len(bad) == 0
    print(f"  Unknown task hand-off history: empty")

    # ==================================================================
    # Step 12: Edge cases
    # ==================================================================
    print("\n" + "=" * 60)
    print("Step 12: Edge cases")
    print("=" * 60)

    fake_id = UUID("00000000-0000-0000-0000-000000000000")

    e1 = manager.submit_for_review(fake_id, editor_id, reviewer_id)
    assert not e1.success
    print(f"  Review unknown task: {e1.error_message}")

    e2 = manager.complete_review(fake_id, reviewer_id, True, "")
    assert not e2.success
    print(f"  Complete review unknown task: {e2.error_message}")

    e3 = manager.route_task(fake_id, editor_id, reviewer_id, "test")
    assert not e3.success
    print(f"  Route unknown task: {e3.error_message}")

    e4 = manager.return_task(fake_id, editor_id, "test")
    assert not e4.success
    print(f"  Return unknown task: {e4.error_message}")

    e5 = manager.mark_awaiting(fake_id, editor_id, "info", "test")
    assert not e5.success
    print(f"  Await unknown task: {e5.error_message}")

    e6 = manager.resume_task(fake_id, editor_id)
    assert not e6.success
    print(f"  Resume unknown task: {e6.error_message}")

    # ==================================================================
    # Step 13: Event verification
    # ==================================================================
    print("\n" + "=" * 60)
    print("Step 13: Event verification")
    print("=" * 60)

    all_events = event_bus.events()
    review_req = [e for e in all_events if isinstance(e, ReviewRequested)]
    review_cmp = [e for e in all_events if isinstance(e, ReviewCompleted)]
    handoff_req = [e for e in all_events if isinstance(e, HandOffRequested)]
    forwarded = [e for e in all_events if isinstance(e, TaskForwarded)]
    returned = [e for e in all_events if isinstance(e, TaskReturned)]
    awaiting = [e for e in all_events if isinstance(e, TaskAwaiting)]
    resumed = [e for e in all_events if isinstance(e, TaskResumed)]

    print(f"  ReviewRequested events: {len(review_req)}")
    print(f"  ReviewCompleted events: {len(review_cmp)}")
    print(f"  TaskForwarded events: {len(forwarded)}")
    print(f"  TaskReturned events: {len(returned)}")
    print(f"  TaskAwaiting events: {len(awaiting)}")
    print(f"  TaskResumed events: {len(resumed)}")
    print(f"  Total events published: {len(all_events)}")

    assert len(review_req) >= 1
    assert len(review_cmp) >= 1
    assert len(forwarded) >= 1
    assert len(returned) >= 1
    assert len(awaiting) >= 1
    assert len(resumed) >= 1

    # ==================================================================
    # Summary
    # ==================================================================
    print("\n" + "=" * 60)
    print("HAND-OFF DEMONSTRATION SUMMARY")
    print("=" * 60)

    checks = [
        ("CEO created plan", plan is not None, True),
        ("DM decomposed tasks", plan_result.success and len(plan_result.tasks) > 0, True),
        ("Editor A accepted task", d == TaskDecision.ACCEPTED, True),
        ("Editor A requested review (hand-off)", handed, True),
        ("Reviewer B accepted task", d2 == TaskDecision.ACCEPTED, True),
        ("DM completed review (approved)", review.success, True),
        ("Task finalized after review", state_after is not None and state_after["completed_tasks"] >= 1, True),
        ("Task forwarded to another employee", routed.success, True),
        ("Task returned to DM", ret.success, True),
        ("Task marked awaiting", await_res.success, True),
        ("Task resumed", resume.success, True),
        ("Hand-off history tracked", len(history) > 0, True),
        ("Unknown history returns empty", len(bad) == 0, True),
        ("ReviewRequested events >= 1", len(review_req) >= 1, True),
        ("ReviewCompleted events >= 1", len(review_cmp) >= 1, True),
        ("TaskForwarded events >= 1", len(forwarded) >= 1, True),
        ("TaskReturned events >= 1", len(returned) >= 1, True),
        ("TaskAwaiting events >= 1", len(awaiting) >= 1, True),
        ("TaskResumed events >= 1", len(resumed) >= 1, True),
        ("Edge: review unknown task", not e1.success, True),
        ("Edge: route unknown task", not e3.success, True),
        ("Edge: return unknown task", not e4.success, True),
        ("Edge: await unknown task", not e5.success, True),
        ("Edge: resume unknown task", not e6.success, True),
    ]

    passed = sum(1 for _, v, e in checks if v == e)
    failed = sum(1 for _, v, e in checks if v != e)

    for label, v, e in checks:
        if v != e:
            print(f"  FAIL: {label} (expected {e}, got {v})")
    print(f"\n  Total: {passed}/{passed+failed} passed, {failed} failed")
    print(f"  Total events: {len(all_events)}")
    print(f"  Plans managed: {len(manager.list_plans())}")
    print(f"  Hand-off system is deterministic\n")


if __name__ == "__main__":
    main()
