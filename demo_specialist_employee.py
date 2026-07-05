"""Demonstration script for SpecialistEmployee — first intelligent worker.

Flow:
  1. Create a video editor employee with relevant skills
  2. Employee receives a compatible video editing task -> ACCEPTS
  3. Employee receives an incompatible research task -> REJECTS
  4. Employee requests additional information before proceeding
  5. Employee requests a tool (unavailable -> blocker)
  6. Employee executes a task and produces a result
  7. DepartmentManager integration: CEO -> DM -> Employee -> completion
  8. Event verification
"""

from __future__ import annotations

from uuid import UUID, uuid4

from core.company.ceo import CEORuntime
from core.company.department_manager import (
    DepartmentManager,
    TaskCompleted as DMTaskCompleted,
)
from core.company.specialist_employee import (
    EmployeeSkill,
    InformationRequested,
    ReceivedTask,
    SpecialistEmployee,
    TaskAccepted,
    TaskBlocked,
    TaskDecision,
    TaskFinished,
    TaskRejected,
    TaskStarted,
    ToolRequested,
)
from core.employees import Employee
from core.employees.models import EmployeeAvailability, EmployeeIdentity
from core.events.bus import EventBus
from core.runtime import CompanyRuntime


def _answer_all(ceo: CEORuntime, goal_id: UUID, answers: dict[str, str]):
    for field, value in answers.items():
        ceo.answer_question(goal_id, field, value)
    last_field = list(answers.keys())[-1]
    r = ceo.answer_question(goal_id, last_field, answers[last_field])
    return r.plan if r.success else None


def main() -> None:
    print("=" * 60)
    print("SpecialistEmployee — First Intelligent Worker")
    print("=" * 60)

    # ------------------------------------------------------------------
    # Setup
    # ------------------------------------------------------------------
    event_bus = EventBus()
    company = CompanyRuntime(event_bus)
    company.initialize_company()

    # ==================================================================
    # Step 1: Create a SpecialistEmployee with skills
    # ==================================================================
    print("\n" + "=" * 60)
    print("Step 1: Create a specialist video editor employee")
    print("=" * 60)

    editor_id = uuid4()
    editor = SpecialistEmployee(
        company_runtime=company,
        employee_id=editor_id,
        skills=(
            EmployeeSkill(name="video", proficiency=0.95, experience_years=3.0),
            EmployeeSkill(name="edit", proficiency=0.90, experience_years=3.0),
            EmployeeSkill(name="audio", proficiency=0.70, experience_years=1.5),
            EmployeeSkill(name="content", proficiency=0.60, experience_years=1.0),
        ),
        event_bus=event_bus,
    )

    print(f"\n  Employee ID: {editor.employee_id}")
    print(f"  Skills:")
    for s in editor.skills:
        print(f"    - {s.name}: proficiency {s.proficiency}, {s.experience_years}y exp")
    print(f"  Status: {editor.status}")
    print(f"  Confidence: {editor.confidence}")

    company.register_employee(
        Employee(
            identity=EmployeeIdentity(employee_id=editor_id),
            availability=EmployeeAvailability(is_available=True),
        )
    )

    # ==================================================================
    # Step 2: Compatible task -> ACCEPTS
    # ==================================================================
    print("\n" + "=" * 60)
    print("Step 2: Compatible task -> ACCEPTS")
    print("=" * 60)

    edit_task = ReceivedTask(
        task_id=uuid4(),
        title="Edit 20 short vertical clips",
        description="Trim, color grade, add subtitles, and export 20 short clips for TikTok and Instagram Reels.",
        department="Video Editing",
        required_skills=("video", "edit"),
    )

    decision = editor.receive_task(edit_task)
    assert decision == TaskDecision.ACCEPTED
    print(f"\n  Task: {edit_task.title}")
    print(f"  Decision: {decision}")
    print(f"  Employee status: {editor.status}")
    print(f"  Workload: {editor.workload}")
    print(f"  Confidence: {editor.confidence}")

    # ==================================================================
    # Step 3: Incompatible task -> REJECTS
    # ==================================================================
    print("\n" + "=" * 60)
    print("Step 3: Incompatible task -> REJECTS")
    print("=" * 60)

    research_task = ReceivedTask(
        task_id=uuid4(),
        title="Analyze market trends for Q3",
        description="Research competitor strategies, analyze market data, and produce a report with recommendations.",
        department="Research",
        required_skills=("research", "data", "analysis"),
    )

    decision2 = editor.receive_task(research_task)
    assert decision2 == TaskDecision.REJECTED
    print(f"\n  Task: {research_task.title}")
    print(f"  Decision: {decision2}")
    print(f"  Tasks rejected: {editor.total_tasks_rejected}")

    # Re-accept the edit task for execution
    editor.receive_task(edit_task)

    # ==================================================================
    # Step 4: Request information
    # ==================================================================
    print("\n" + "=" * 60)
    print("Step 4: Request additional information")
    print("=" * 60)

    info_result = editor.request_information(
        edit_task.task_id,
        field="target_platforms",
        question="Which platforms should the clips be optimized for? TikTok, Reels, or both?",
    )
    assert info_result
    print(f"\n  Info requested: target_platforms")
    print(f"  Question: Which platforms should the clips be optimized for?")
    print(f"  Employee status: {editor.status}")

    # Provide the information
    editor.provide_information(edit_task.task_id, "target_platforms", "TikTok and Instagram Reels")
    print(f"  Information provided. Employee status: {editor.status}")

    # ==================================================================
    # Step 5: Request a tool (unavailable -> blocker)
    # ==================================================================
    print("\n" + "=" * 60)
    print("Step 5: Request an unavailable tool -> blocked")
    print("=" * 60)

    tool_result = editor.request_tool(
        edit_task.task_id,
        tool_name="After Effects",
        reason="Need advanced motion graphics for clip transitions.",
    )
    assert tool_result
    print(f"\n  Tool requested: After Effects")
    print(f"  Reason: Need advanced motion graphics for clip transitions.")
    print(f"  Employee status: {editor.status}")

    # Tool is unavailable -> blocker
    editor.provide_tool(edit_task.task_id, "After Effects", available=False)
    was_blocked = editor.status.value == "blocked"
    print(f"  Tool denied. Employee status: {editor.status}")

    # Provide tool (now it's available) -> resumes working
    editor.provide_tool(edit_task.task_id, "After Effects", available=True)
    print(f"  Tool provided. Employee status: {editor.status}")

    # ==================================================================
    # Step 6: Execute task and produce result
    # ==================================================================
    print("\n" + "=" * 60)
    print("Step 6: Execute task and produce result")
    print("=" * 60)

    result = editor.execute_task(edit_task.task_id)
    assert result.success
    print(f"\n  Execution result:")
    print(f"    Success: {result.success}")
    print(f"    Summary: {result.summary}")
    print(f"    Duration: {result.duration_minutes} min")
    print(f"    Skills applied: {result.output.get('skills_applied', [])}")
    print(f"    Artifacts:")
    for art in result.output.get("artifacts", []):
        print(f"      - {art}")
    print(f"\n  Employee status after: {editor.status}")
    print(f"  Tasks completed: {editor.total_tasks_completed}")
    print(f"  Performance score: {editor.performance_score}")

    # ==================================================================
    # Step 7: Full integration — CEO -> DM -> Employee -> completion
    # ==================================================================
    print("\n" + "=" * 60)
    print("Step 7: Full integration (CEO -> DM -> Employee)")
    print("=" * 60)

    ceo = CEORuntime(company, event_bus)
    manager = DepartmentManager(company, event_bus)

    r = ceo.receive_goal("produzir videos para o YouTube")
    plan = _answer_all(ceo, r.goal_id, {
        "duration": "10-15 minutes",
        "quantity": "5",
        "format": "horizontal",
        "platform": "YouTube",
        "subtitles": "manual",
        "timeline": "1 month",
        "priority": "high",
    })
    assert plan is not None
    print(f"\n  CEO created plan: {plan.objective}")

    plan_result = manager.receive_plan(plan)
    assert plan_result.success
    print(f"  DM decomposed into {len(plan_result.tasks)} tasks")

    # Create a second employee for DM integration
    editor2_id = uuid4()
    editor2 = SpecialistEmployee(
        company_runtime=company,
        employee_id=editor2_id,
        skills=(
            EmployeeSkill(name="video", proficiency=0.90, experience_years=2.0),
            EmployeeSkill(name="edit", proficiency=0.85, experience_years=2.0),
        ),
        event_bus=event_bus,
        department_manager=manager,
    )
    company.register_employee(
        Employee(
            identity=EmployeeIdentity(employee_id=editor2_id),
            availability=EmployeeAvailability(is_available=True),
        )
    )

    dm_task = plan_result.tasks[0]
    dm_assign = manager.assign_task(dm_task.task_id, editor2.employee_id)
    assert dm_assign.success
    print(f"  DM assigned task: {dm_task.title}")

    se_task = ReceivedTask(
        task_id=dm_task.task_id,
        title=dm_task.title,
        description=f"Execute video editing for plan: {plan.objective}",
        department="Video Editing",
        required_skills=("video", "edit"),
    )

    d = editor2.receive_task(se_task)
    assert d == TaskDecision.ACCEPTED
    print(f"  Employee accepted: {d}")

    se_result = editor2.execute_task(dm_task.task_id)
    assert se_result.success
    print(f"  Employee executed: success={se_result.success}")
    print(f"  Summary: {se_result.summary}")

    # Verify DM knows the task is completed
    state = manager.plan_state(plan.plan_id)
    assert state is not None
    print(f"  DM plan progress: {state['completed_tasks']}/{state['total_tasks']} completed")

    # ==================================================================
    # Step 8: Edge cases
    # ==================================================================
    print("\n" + "=" * 60)
    print("Step 8: Edge cases")
    print("=" * 60)

    fake_id = UUID("00000000-0000-0000-0000-000000000000")

    r1 = editor.execute_task(fake_id)
    assert not r1.success
    print(f"  Execute unknown task: {r1.error}")

    r2 = editor.request_information(fake_id, "x", "y")
    assert not r2
    print(f"  Request info for unknown task: False")

    r3 = editor.request_tool(fake_id, "tool", "reason")
    assert not r3
    print(f"  Request tool for unknown task: False")

    r4 = editor.report_blocker(fake_id, "test")
    assert not r4
    print(f"  Report blocker for unknown task: False")

    # ==================================================================
    # Step 9: Event verification
    # ==================================================================
    print("\n" + "=" * 60)
    print("Step 9: Event verification")
    print("=" * 60)

    all_events = event_bus.events()
    accepted = [e for e in all_events if isinstance(e, TaskAccepted)]
    rejected = [e for e in all_events if isinstance(e, TaskRejected)]
    started = [e for e in all_events if isinstance(e, TaskStarted)]
    finished = [e for e in all_events if isinstance(e, TaskFinished)]
    info_reqs = [e for e in all_events if isinstance(e, InformationRequested)]
    tool_reqs = [e for e in all_events if isinstance(e, ToolRequested)]
    blocked = [e for e in all_events if isinstance(e, TaskBlocked)]
    dm_completed = [e for e in all_events if isinstance(e, DMTaskCompleted)]

    print(f"  TaskAccepted events: {len(accepted)}")
    print(f"  TaskRejected events: {len(rejected)}")
    print(f"  TaskStarted events: {len(started)}")
    print(f"  TaskFinished events: {len(finished)}")
    print(f"  InformationRequested events: {len(info_reqs)}")
    print(f"  ToolRequested events: {len(tool_reqs)}")
    print(f"  TaskBlocked events: {len(blocked)}")
    print(f"  DM TaskCompleted events: {len(dm_completed)}")
    print(f"  Total events: {len(all_events)}")

    assert len(accepted) >= 2
    assert len(rejected) >= 1
    assert len(finished) >= 2
    assert len(info_reqs) >= 1
    assert len(tool_reqs) >= 1
    assert len(blocked) >= 1
    assert len(dm_completed) >= 1

    for ev in accepted:
        print(f"    - Accepted: {ev.title[:40]} (difficulty={ev.difficulty}, est={ev.estimated_time_minutes}min)")

    for ev in rejected:
        print(f"    - Rejected: {ev.title[:40]} (missing: {', '.join(ev.missing_skills)})")

    # ==================================================================
    # Summary
    # ==================================================================
    print("\n" + "=" * 60)
    print("SPECIALIST EMPLOYEE DEMONSTRATION SUMMARY")
    print("=" * 60)

    checks = [
        ("Employee created with skills", len(editor.skills) > 0, True),
        ("Compatible task accepted", decision == TaskDecision.ACCEPTED, True),
        ("Incompatible task rejected", decision2 == TaskDecision.REJECTED, True),
        ("Info request published", info_result, True),
        ("Tool request published", tool_result, True),
        ("Blocker on unavailable tool", was_blocked, True),

        ("Task executed successfully", result.success, True),
        ("Result has summary", len(result.summary) > 0, True),
        ("Result has output artifacts", len(result.output.get("artifacts", [])) > 0, True),
        ("Employee confidence increased", editor.confidence > 0.8, True),
        ("Tasks completed tracked", editor.total_tasks_completed >= 1, True),

        ("DM integration: plan created", plan is not None, True),
        ("DM integration: task assigned", dm_assign.success, True),
        ("DM integration: employee accepted", d == TaskDecision.ACCEPTED, True),
        ("DM integration: employee executed", se_result.success, True),

        ("TaskAccepted events", len(accepted) >= 2, True),
        ("TaskRejected events", len(rejected) >= 1, True),
        ("TaskFinished events", len(finished) >= 2, True),
        ("InformationRequested events", len(info_reqs) >= 1, True),
        ("ToolRequested events", len(tool_reqs) >= 1, True),
        ("TaskBlocked events", len(blocked) >= 1, True),
        ("DM TaskCompleted events", len(dm_completed) >= 1, True),

        ("Edge: unknown task execute returns error", not r1.success, True),
        ("Edge: unknown task info request returns False", not r2, True),
        ("Edge: unknown task tool request returns False", not r3, True),
        ("Edge: unknown task blocker returns False", not r4, True),
    ]

    passed = sum(1 for _, v, e in checks if v == e)
    failed = sum(1 for _, v, e in checks if v != e)

    for label, result_val, expected in checks:
        if result_val != expected:
            print(f"  FAIL: {label} (expected {expected}, got {result_val})")

    print(f"\n  Total: {passed}/{passed + failed} passed, {failed} failed")
    print(f"  Total events: {len(all_events)}")
    print(f"  Employee is generic: based on skills, not profession\n")


if __name__ == "__main__":
    main()
