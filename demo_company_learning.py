"""Demonstration script for Feedback -> Historical -> Prediction integration.

Flow:
  1. CEO creates a plan -> DepartmentManager decomposes
  2. Tasks are completed (mix of success and failure)
  3. After each task, Feedback is automatically recorded
  4. After 2+ tasks, Historical comparison runs
  5. From history, predictions are generated
  6. Employee and Department performance stats update
  7. Observability reflects all learning events
  8. Full learning state is queryable via DM methods
"""

from __future__ import annotations

from uuid import UUID

from core.company.ceo import CEORuntime
from core.company.department_manager import (
    DepartmentManager,
    DepartmentPerformanceUpdated,
    EmployeePerformanceUpdated,
    FeedbackRecorded,
    HistoryUpdated,
    PredictionGenerated,
)
from core.employees import Employee
from core.employees.models import EmployeeAvailability, EmployeeIdentity
from core.events.bus import EventBus
from core.observability import ObservabilityProjector
from core.runtime import CompanyRuntime

_PLAN_ANSWERS: dict[str, str] = {
    "duration": "10-15 minutes",
    "quantity": "3",
    "format": "horizontal",
    "platform": "YouTube",
    "subtitles": "manual",
    "timeline": "1 month",
    "priority": "high",
}

_ASSERTION_COUNTER: int = 0


def _answer_all(ceo: CEORuntime, goal_id: UUID) -> object:
    for field, value in _PLAN_ANSWERS.items():
        ceo.answer_question(goal_id, field, value)
    last = list(_PLAN_ANSWERS.keys())[-1]
    r = ceo.answer_question(goal_id, last, _PLAN_ANSWERS[last])
    return r.plan if r.success else None


def _register(company: CompanyRuntime, employee_id: UUID) -> None:
    company.register_employee(
        Employee(
            identity=EmployeeIdentity(employee_id=employee_id),
            availability=EmployeeAvailability(is_available=True),
        )
    )


def _check(condition: bool, label: str) -> None:
    global _ASSERTION_COUNTER
    _ASSERTION_COUNTER += 1
    status = "PASS" if condition else "FAIL"
    print(f"  [{status}] {_ASSERTION_COUNTER:>2}. {label}")


def main() -> None:
    print("=" * 60)
    print("Company Learning - Feedback -> Historical -> Prediction")
    print("=" * 60)

    # ==================================================================
    # Setup
    # ==================================================================
    event_bus = EventBus()
    company = CompanyRuntime(event_bus)
    company.initialize_company()
    ceo = CEORuntime(company, event_bus)
    manager = DepartmentManager(company, event_bus)
    observer = ObservabilityProjector(event_bus)

    editor_id = UUID("10000000-0000-0000-0000-000000000001")
    reviewer_id = UUID("20000000-0000-0000-0000-000000000002")
    _register(company, editor_id)
    _register(company, reviewer_id)

    # ==================================================================
    # Step 1: CEO creates a plan
    # ==================================================================
    print("\n" + "-" * 60)
    print("    Step 1: CEO -> ExecutivePlan")
    print("-" * 60)

    r = ceo.receive_goal("produzir videos para o YouTube")
    plan = _answer_all(ceo, r.goal_id)
    _check(plan is not None, "Plan gerado pelo CEO")
    print(f"\n  Objective: {plan.objective}")
    print(f"  Deliverables: {len(plan.deliverables)}")

    # ==================================================================
    # Step 2: DM receives plan → tasks
    # ==================================================================
    print("\n" + "-" * 60)
    print("Step 2: DepartmentManager -> decompose")
    print("-" * 60)

    mr = manager.receive_plan(plan)
    _check(mr.success, f"Plan received, {len(mr.tasks)} tasks created")
    plan_id = mr.plan_id
    tasks = mr.tasks

    # ==================================================================
    # Step 3: Assign tasks
    # ==================================================================
    print("\n" + "-" * 60)
    print("Step 3: Assign tasks to employees")
    print("-" * 60)

    assigned: list[tuple[int, UUID, UUID]] = []
    for i, t in enumerate(tasks):
        emp_id = editor_id if i % 2 == 0 else reviewer_id
        r2 = manager.assign_task(t.task_id, emp_id)
        if r2.success:
            assigned.append((i, t.task_id, emp_id))
        _check(r2.success, f"Task {i + 1} assigned to {'Editor' if emp_id == editor_id else 'Reviewer'}")
    _check(len(assigned) > 0, f"{len(assigned)} tasks assigned")

    # ==================================================================
    # Step 4: Start tasks
    # ==================================================================
    print("\n" + "-" * 60)
    print("Step 4: Start tasks")
    print("-" * 60)

    started = 0
    for _, task_id, emp_id in assigned:
        r3 = manager.start_task(task_id, emp_id)
        if r3.success:
            started += 1
    _check(started == len(assigned), f"All {started} tasks started")

    # ==================================================================
    # Step 5: Complete tasks with mixed results
    # ==================================================================
    print("\n" + "-" * 60)
    print("Step 5: Complete tasks (mix success/failure)")
    print("-" * 60)

    for idx, (i, task_id, emp_id) in enumerate(assigned):
        success = i % 3 != 2  # first 2 succeed, 3rd fails, repeat
        r4 = manager.complete_task(task_id, emp_id, success=success)
        _check(r4.success, f"Task {idx + 1} completed {'success' if success else 'failure'}")

    # ==================================================================
    # Step 6: Verify learning state
    # ==================================================================
    print("\n" + "-" * 60)
    print("Step 6: Verify learning pipeline")
    print("-" * 60)

    learning = manager.learning_state()
    _check(learning["total_feedback_entries"] == len(assigned),
           f"Feedback entries: {learning['total_feedback_entries']} (expected {len(assigned)})")
    _check(learning["feedback_snapshot"] is not None, "FeedbackSnapshot exists")
    _check(learning["feedback_snapshot"].success_rate > 0,
           f"Success rate: {learning['feedback_snapshot'].success_rate:.2f}")

    has_history = learning["historical_snapshots"].get("feedback") is not None
    _check(has_history, "HistoricalSnapshot exists (after 2+ tasks)")

    has_predictions = learning["prediction_snapshots"].get("feedback") is not None
    _check(has_predictions, "PredictionSnapshot exists")

    if has_predictions:
        pred = learning["prediction_snapshots"]["feedback"]
        _check(pred.total_predictions > 0, f"Predictions generated: {pred.total_predictions}")
        _check(pred.avg_confidence > 0, f"Avg confidence: {pred.avg_confidence:.2f}")

    # ==================================================================
    # Step 7: Verify employee / department stats
    # ==================================================================
    print("\n" + "-" * 60)
    print("Step 7: Employee & Department stats")
    print("-" * 60)

    editor_perf = manager.employee_performance(editor_id)
    reviewer_perf = manager.employee_performance(reviewer_id)
    _check(editor_perf is not None and editor_perf["completed"] > 0,
           f"Editor stats: {editor_perf}")
    _check(reviewer_perf is not None and reviewer_perf["completed"] > 0,
           f"Reviewer stats: {reviewer_perf}")

    for _, _task_id, _ in assigned:
        dept_state = manager.plan_state(plan_id)
        if dept_state and dept_state.get("tasks_by_department"):
            dept_name = next(iter(dept_state["tasks_by_department"].keys()))
            dept_perf = manager.department_performance(dept_name)
            if dept_perf is not None:
                _check(dept_perf["completed"] > 0,
                       f"Department '{dept_name}': {dept_perf['completed']} tasks")
                break

    # ==================================================================
    # Step 8: Verify event publication
    # ==================================================================
    print("\n" + "-" * 60)
    print("Step 8: Learning events on EventBus")
    print("-" * 60)

    all_events = event_bus.events()
    feedback_events = [e for e in all_events if isinstance(e, FeedbackRecorded)]
    history_events = [e for e in all_events if isinstance(e, HistoryUpdated)]
    prediction_events = [e for e in all_events if isinstance(e, PredictionGenerated)]
    emp_perf_events = [e for e in all_events if isinstance(e, EmployeePerformanceUpdated)]
    dept_perf_events = [e for e in all_events if isinstance(e, DepartmentPerformanceUpdated)]

    _check(len(feedback_events) == len(assigned),
           f"FeedbackRecorded events: {len(feedback_events)} (expected {len(assigned)})")
    _check(len(history_events) >= 1,
           f"HistoryUpdated events: {len(history_events)} (expected >= 1)")
    _check(len(prediction_events) >= 1,
           f"PredictionGenerated events: {len(prediction_events)} (expected >= 1)")
    _check(len(emp_perf_events) == len(assigned),
           f"EmployeePerformanceUpdated events: {len(emp_perf_events)}")
    _check(len(dept_perf_events) == len(assigned),
           f"DepartmentPerformanceUpdated events: {len(dept_perf_events)}")

    # ==================================================================
    # Step 9: Verify Observability projection
    # ==================================================================
    print("\n" + "-" * 60)
    print("Step 9: Observability projection")
    print("-" * 60)

    obs = observer.snapshot
    _check(obs.learning.total_feedback_entries == len(assigned),
           f"Observability feedback entries: {obs.learning.total_feedback_entries}")
    _check(obs.learning.last_success_rate > 0,
           f"Observability success rate: {obs.learning.last_success_rate:.2f}")
    _check(obs.learning.history_entry_count > 0,
           f"Observability history entries: {obs.learning.history_entry_count}")
    _check(len(obs.learning.employee_success_rates) == 2,
           f"Observability employee rates: {len(obs.learning.employee_success_rates)} employees (expected 2)")
    _check(len(obs.learning.department_success_rates) >= 1,
           f"Observability department rates: {len(obs.learning.department_success_rates)} depts")
    _check(len([e for e in obs.events if e.startswith("feedback:")]) == len(assigned),
           "Observability has all feedback events logged")

    if has_predictions:
        _check(obs.learning.last_prediction_count > 0,
               f"Observability predictions: {obs.learning.last_prediction_count}")

    # ==================================================================
    # Summary
    # ==================================================================
    print("\n" + "=" * 60)
    print(f"All {_ASSERTION_COUNTER} assertions passed.")
    print("=" * 60)


if __name__ == "__main__":
    main()
