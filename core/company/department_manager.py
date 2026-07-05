"""Department Manager - first manager of AI Company.

The DepartmentManager receives an ExecutivePlan from the CEO,
decomposes deliverables into concrete tasks, assigns work,
tracks progress, and reports status back to the CEO.
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any
from uuid import UUID, uuid4

from core.company.ceo import ExecutivePlan
from core.events.bus import EventBus
from core.feedback.foundation import (
    FeedbackEntry,
    FeedbackSnapshot,
    FoundationFeedbackRuntime,
)
from core.history.foundation import FoundationHistoricalRuntime, HistoricalSnapshot
from core.prediction.foundation import FoundationPredictionRuntime, PredictionSnapshot
from core.runtime import CompanyRuntime

# ------------------------------------------------------------------
# Enums
# ------------------------------------------------------------------

class TaskStatus(StrEnum):
    PENDING = "pending"
    ASSIGNED = "assigned"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"


# ------------------------------------------------------------------
# Events - published on the shared EventBus
# ------------------------------------------------------------------

@dataclass(frozen=True, slots=True)
class PlanReceived:
    manager_id: UUID
    plan_id: UUID
    objective: str
    departments: tuple[str, ...]
    timestamp: float = 0.0
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class TasksDecomposed:
    manager_id: UUID
    plan_id: UUID
    task_ids: tuple[UUID, ...]
    task_titles: tuple[str, ...]
    task_departments: tuple[str, ...]
    timestamp: float = 0.0
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class TaskAssigned:
    manager_id: UUID
    plan_id: UUID
    task_id: UUID
    employee_id: UUID
    title: str
    department: str
    timestamp: float = 0.0
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class TaskCompleted:
    manager_id: UUID
    plan_id: UUID
    task_id: UUID
    employee_id: UUID
    success: bool
    timestamp: float = 0.0
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class ProgressReported:
    manager_id: UUID
    plan_id: UUID
    completed: int
    total: int
    progress_pct: float
    deliverables_progress: tuple[tuple[str, int, int], ...]
    timestamp: float = 0.0
    metadata: dict[str, Any] = field(default_factory=dict)


# ------------------------------------------------------------------
# Hand-Off events - task routing between employees
# ------------------------------------------------------------------

@dataclass(frozen=True, slots=True)
class HandOffRequested:
    manager_id: UUID
    handoff_id: UUID
    task_id: UUID
    from_employee_id: UUID
    handoff_type: str           # "review", "forward", "completion", "awaiting_info", "awaiting_tool", "awaiting_credentials", "awaiting_api"
    reason: str
    timestamp: float = 0.0
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class TaskForwarded:
    manager_id: UUID
    task_id: UUID
    from_employee_id: UUID
    to_employee_id: UUID
    reason: str
    timestamp: float = 0.0
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class ReviewRequested:
    manager_id: UUID
    task_id: UUID
    from_employee_id: UUID
    reviewer_id: UUID
    timestamp: float = 0.0
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class ReviewCompleted:
    manager_id: UUID
    task_id: UUID
    reviewer_id: UUID
    approved: bool
    feedback: str
    timestamp: float = 0.0
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class TaskReturned:
    manager_id: UUID
    task_id: UUID
    from_employee_id: UUID
    reason: str
    timestamp: float = 0.0
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class TaskAwaiting:
    manager_id: UUID
    task_id: UUID
    employee_id: UUID
    await_type: str
    details: str
    timestamp: float = 0.0
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class TaskResumed:
    manager_id: UUID
    task_id: UUID
    employee_id: UUID
    timestamp: float = 0.0
    metadata: dict[str, Any] = field(default_factory=dict)


# ------------------------------------------------------------------
# Learning events - published when tasks complete
# ------------------------------------------------------------------

@dataclass(frozen=True, slots=True)
class FeedbackRecorded:
    manager_id: UUID
    task_id: UUID
    employee_id: UUID
    success: bool
    total_entries: int
    success_rate: float
    timestamp: float = 0.0
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class HistoryUpdated:
    manager_id: UUID
    domain: str
    entry_count: int
    improving_count: int
    declining_count: int
    stable_count: int
    timestamp: float = 0.0
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class PredictionGenerated:
    manager_id: UUID
    domain: str
    total_predictions: int
    avg_confidence: float
    upward_count: int
    downward_count: int
    timestamp: float = 0.0
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class EmployeePerformanceUpdated:
    manager_id: UUID
    employee_id: UUID
    tasks_completed: int
    tasks_succeeded: int
    tasks_failed: int
    success_rate: float
    timestamp: float = 0.0
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class DepartmentPerformanceUpdated:
    manager_id: UUID
    department: str
    tasks_completed: int
    tasks_succeeded: int
    tasks_failed: int
    success_rate: float
    timestamp: float = 0.0
    metadata: dict[str, Any] = field(default_factory=dict)


# ------------------------------------------------------------------
# Hand-Off data models
# ------------------------------------------------------------------

@dataclass(frozen=True, slots=True)
class HandOffRecord:
    handoff_id: UUID
    task_id: UUID
    from_employee_id: UUID
    handoff_type: str
    reason: str
    status: str                             # "requested", "completed"
    created_at: float = 0.0
    metadata: dict[str, Any] = field(default_factory=dict)


# ------------------------------------------------------------------
# Data models
# ------------------------------------------------------------------

@dataclass(frozen=True, slots=True)
class DecomposedTask:
    task_id: UUID
    title: str
    department: str
    deliverable: str
    status: TaskStatus = TaskStatus.PENDING
    assigned_employee_id: UUID | None = None

    def with_status(self, status: TaskStatus) -> DecomposedTask:
        return DecomposedTask(
            task_id=self.task_id,
            title=self.title,
            department=self.department,
            deliverable=self.deliverable,
            status=status,
            assigned_employee_id=self.assigned_employee_id,
        )

    def with_assignment(self, employee_id: UUID) -> DecomposedTask:
        return DecomposedTask(
            task_id=self.task_id,
            title=self.title,
            department=self.department,
            deliverable=self.deliverable,
            status=self.status,
            assigned_employee_id=employee_id,
        )


@dataclass(frozen=True, slots=True)
class ManagedPlan:
    plan_id: UUID
    objective: str
    departments: tuple[str, ...]
    tasks: tuple[DecomposedTask, ...]
    created_at: float = 0.0


@dataclass(frozen=True, slots=True)
class ManagerResult:
    success: bool
    plan_id: UUID | None = None
    tasks: tuple[DecomposedTask, ...] = field(default_factory=tuple)
    progress: ProgressReported | None = None
    error_message: str = ""


# ------------------------------------------------------------------
# Helpers
# ------------------------------------------------------------------

_DELIVERABLE_DECOMPOSITION: dict[str, list[str]] = {
    "video": [
        "Prepare source assets",
        "Execute primary edit",
        "Review and revise",
        "Export and deliver",
    ],
    "edit": [
        "Prepare source assets",
        "Execute primary edit",
        "Review and revise",
        "Export and deliver",
    ],
    "audio": [
        "Capture or source audio",
        "Process and mix",
        "Master and finalize",
    ],
    "podcast": [
        "Capture or source audio",
        "Process and mix",
        "Master and finalize",
    ],
    "content": [
        "Research and outline",
        "Write first draft",
        "Review and polish",
        "Publish",
    ],
    "article": [
        "Research and outline",
        "Write first draft",
        "Review and polish",
        "Publish",
    ],
    "market": [
        "Define strategy",
        "Create creative assets",
        "Launch and monitor",
        "Report performance",
    ],
    "campaign": [
        "Define strategy",
        "Create creative assets",
        "Launch and monitor",
        "Report performance",
    ],
    "sale": [
        "Prepare materials",
        "Execute outreach",
        "Follow up and close",
    ],
    "product": [
        "Prepare materials",
        "Execute outreach",
        "Follow up and close",
    ],
    "research": [
        "Collect data",
        "Analyze findings",
        "Write and deliver report",
    ],
    "report": [
        "Collect data",
        "Analyze findings",
        "Write and deliver report",
    ],
    "quality": [
        "Define criteria",
        "Execute review",
        "Document results",
    ],
    "coordination": [
        "Create schedule",
        "Coordinate execution",
        "Deliver status",
    ],
}


def _decompose_deliverable(deliverable: str) -> list[str]:
    dl = deliverable.lower()
    for keyword, subtasks in _DELIVERABLE_DECOMPOSITION.items():
        if keyword in dl:
            return [f"{s} for {deliverable}" for s in subtasks]
    return [
        f"Plan and prepare for {deliverable}",
        f"Execute {deliverable}",
        f"Review and deliver {deliverable}",
    ]


def _associate_department(deliverable: str, plan_departments: tuple[str, ...]) -> str:
    dl = deliverable.lower()
    dept_map: dict[str, list[str]] = {
        "Video Editing": ["video", "edit", "film", "short", "reel", "clip"],
        "Audio Production": ["audio", "sound", "music", "podcast", "voice"],
        "Content Production": ["content", "article", "blog", "post", "text", "copy", "script"],
        "Marketing": ["market", "campaign", "brand", "promot"],
        "Sales": ["sale", "funnel", "convert", "product", "affiliate"],
        "Research": ["research", "report", "analysis", "data"],
        "Quality Assurance": ["quality", "qa", "review", "sign-off", "check"],
        "Management": ["coordination", "report", "manage", "plan", "schedule"],
    }
    for dept, kws in dept_map.items():
        if any(kw in dl for kw in kws):
            return dept
    return plan_departments[0] if plan_departments else "Management"


def _build_task_title(subtask: str, deliverable: str, index: int) -> str:
    base = subtask.replace(f"for {deliverable}", "").replace(f" for {deliverable}", "").strip()
    return f"{base} ({deliverable})"


# ------------------------------------------------------------------
# DepartmentManager
# ------------------------------------------------------------------

class DepartmentManager:
    """First manager of the AI Company.

    Receives ExecutivePlans from the CEO, decomposes deliverables
    into tasks, assigns work to employees, tracks execution, and
    reports progress.
    """

    def __init__(
        self,
        company_runtime: CompanyRuntime,
        event_bus: EventBus | None = None,
    ) -> None:
        self._manager_id = uuid4()
        self._company = company_runtime
        self._event_bus = event_bus or company_runtime.event_bus
        self._plans: dict[UUID, ManagedPlan] = {}
        self._tasks: dict[UUID, DecomposedTask] = {}
        self._handoffs: dict[UUID, list[HandOffRecord]] = {}  # task_id -> records
        self._feedback_entries: list[FeedbackEntry] = []
        self._last_feedback_snapshot: FeedbackSnapshot | None = None
        self._historical_snapshots: dict[str, HistoricalSnapshot] = {}
        self._prediction_snapshots: dict[str, PredictionSnapshot] = {}
        self._employee_stats: dict[UUID, dict[str, int]] = {}
        self._department_stats: dict[str, dict[str, int]] = {}

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def receive_plan(self, plan: ExecutivePlan) -> ManagerResult:
        """Receive an ExecutivePlan and decompose deliverables into tasks."""
        plan_id = plan.plan_id

        all_tasks: list[DecomposedTask] = []
        for deliverable in plan.deliverables:
            sub_tasks = _decompose_deliverable(deliverable)
            dept = _associate_department(deliverable, plan.departments)
            for subtask in sub_tasks:
                task = DecomposedTask(
                    task_id=uuid4(),
                    title=subtask,
                    department=dept,
                    deliverable=deliverable,
                )
                all_tasks.append(task)
                self._tasks[task.task_id] = task

        tasks_tuple = tuple(all_tasks)
        managed = ManagedPlan(
            plan_id=plan_id,
            objective=plan.objective,
            departments=plan.departments,
            tasks=tasks_tuple,
            created_at=time.time(),
        )
        self._plans[plan_id] = managed

        self._publish(PlanReceived(
            manager_id=self._manager_id,
            plan_id=plan_id,
            objective=plan.objective,
            departments=plan.departments,
            timestamp=time.time(),
        ))
        self._publish(TasksDecomposed(
            manager_id=self._manager_id,
            plan_id=plan_id,
            task_ids=tuple(t.task_id for t in all_tasks),
            task_titles=tuple(t.title for t in all_tasks),
            task_departments=tuple(t.department for t in all_tasks),
            timestamp=time.time(),
        ))

        return ManagerResult(success=True, plan_id=plan_id, tasks=tasks_tuple)

    def assign_task(self, task_id: UUID, employee_id: UUID) -> ManagerResult:
        """Assign a decomposed task to an employee."""
        task = self._tasks.get(task_id)
        if task is None:
            return ManagerResult(
                success=False,
                error_message=f"Task {task_id} not found.",
            )
        if task.status != TaskStatus.PENDING:
            return ManagerResult(
                success=False,
                error_message=f"Task {task_id} is {task.status}, cannot assign.",
            )

        plan_id = self._find_plan_for_task(task_id)

        updated = task.with_assignment(employee_id).with_status(TaskStatus.ASSIGNED)
        self._tasks[task_id] = updated
        if plan_id:
            self._update_plan_task(plan_id, updated)

        company_task = self._company.register_task(
            title=task.title,
            metadata={
                "department": task.department,
                "plan_id": str(plan_id or ""),
                "deliverable": task.deliverable,
            },
        )
        self._company.assign_task(employee_id, company_task.task_id)

        self._publish(TaskAssigned(
            manager_id=self._manager_id,
            plan_id=plan_id or uuid4(),
            task_id=task_id,
            employee_id=employee_id,
            title=task.title,
            department=task.department,
            timestamp=time.time(),
        ))

        return ManagerResult(success=True, plan_id=plan_id)

    def complete_task(self, task_id: UUID, employee_id: UUID, *, success: bool = True) -> ManagerResult:
        """Mark a decomposed task as completed."""
        task = self._tasks.get(task_id)
        if task is None:
            return ManagerResult(
                success=False,
                error_message=f"Task {task_id} not found.",
            )

        plan_id = self._find_plan_for_task(task_id)
        new_status = TaskStatus.COMPLETED if success else TaskStatus.FAILED
        updated = task.with_status(new_status)
        self._tasks[task_id] = updated
        if plan_id:
            self._update_plan_task(plan_id, updated)

        company_tasks = self._company.tasks()
        for ct in company_tasks:
            if ct.metadata.get("department") == task.department:
                self._company.complete_task(employee_id, ct.task_id)

        self._publish(TaskCompleted(
            manager_id=self._manager_id,
            plan_id=plan_id or uuid4(),
            task_id=task_id,
            employee_id=employee_id,
            success=success,
            timestamp=time.time(),
        ))

        self._record_learning(task_id, employee_id, success)

        return ManagerResult(success=True, plan_id=plan_id)

    def start_task(self, task_id: UUID, employee_id: UUID) -> ManagerResult:
        """Transition a task from ASSIGNED to IN_PROGRESS."""
        task = self._tasks.get(task_id)
        if task is None:
            return ManagerResult(
                success=False,
                error_message=f"Task {task_id} not found.",
            )
        if task.status != TaskStatus.ASSIGNED:
            return ManagerResult(
                success=False,
                error_message=f"Task {task_id} is {task.status}, expected ASSIGNED.",
            )
        plan_id = self._find_plan_for_task(task_id)
        updated = task.with_status(TaskStatus.IN_PROGRESS)
        self._tasks[task_id] = updated
        if plan_id:
            self._update_plan_task(plan_id, updated)
        return ManagerResult(success=True, plan_id=plan_id)

    def report_progress(self, plan_id: UUID) -> ManagerResult:
        """Generate a progress report for a plan."""
        managed = self._plans.get(plan_id)
        if managed is None:
            return ManagerResult(
                success=False,
                error_message=f"Plan {plan_id} not found.",
            )

        current_tasks = tuple(
            self._tasks.get(t.task_id, t) for t in managed.tasks
        )
        total = len(current_tasks)
        completed = sum(1 for t in current_tasks if t.status == TaskStatus.COMPLETED)
        progress_pct = 0.0
        if total > 0:
            progress_pct = round(completed / total * 100, 1)

        d_progress: list[tuple[str, int, int]] = []
        seen: set[str] = set()
        for deliverable in (t.deliverable for t in current_tasks):
            if deliverable not in seen:
                seen.add(deliverable)
                d_tasks = [t for t in current_tasks if t.deliverable == deliverable]
                d_completed = sum(1 for t in d_tasks if t.status == TaskStatus.COMPLETED)
                d_progress.append((deliverable, d_completed, len(d_tasks)))

        report = ProgressReported(
            manager_id=self._manager_id,
            plan_id=plan_id,
            completed=completed,
            total=total,
            progress_pct=progress_pct,
            deliverables_progress=tuple(d_progress),
            timestamp=time.time(),
        )

        self._publish(report)

        return ManagerResult(success=True, plan_id=plan_id, progress=report)

    def plan_state(self, plan_id: UUID) -> dict[str, Any] | None:
        """Get the current state of a managed plan."""
        managed = self._plans.get(plan_id)
        if managed is None:
            return None
        current = tuple(self._tasks.get(t.task_id, t) for t in managed.tasks)
        total = len(current)
        completed = sum(1 for t in current if t.status == TaskStatus.COMPLETED)
        progress_pct = 0.0
        if total > 0:
            progress_pct = round(completed / total * 100, 1)
        dept_counts: dict[str, int] = {}
        for t in current:
            dept_counts[t.department] = dept_counts.get(t.department, 0) + 1
        return {
            "plan_id": plan_id,
            "objective": managed.objective,
            "departments": managed.departments,
            "total_tasks": total,
            "completed_tasks": completed,
            "progress_pct": progress_pct,
            "tasks_by_department": dept_counts,
        }

    def list_plans(self) -> list[dict[str, Any]]:
        """List all plans being managed."""
        return [
            {
                "plan_id": pid,
                "objective": p.objective,
                "departments": p.departments,
                "task_count": len(p.tasks),
            }
            for pid, p in self._plans.items()
        ]

    def tasks_for_plan(self, plan_id: UUID) -> tuple[DecomposedTask, ...]:
        """Return all tasks for a plan with current status."""
        managed = self._plans.get(plan_id)
        if managed is None:
            return ()
        return tuple(self._tasks.get(t.task_id, t) for t in managed.tasks)

    # ------------------------------------------------------------------
    # Hand-Off API
    # ------------------------------------------------------------------

    def submit_for_review(self, task_id: UUID, from_employee_id: UUID, reviewer_id: UUID) -> ManagerResult:
        """Submit a task for peer review. DM routes to the reviewer."""
        task = self._tasks.get(task_id)
        if task is None:
            return ManagerResult(success=False, error_message=f"Task {task_id} not found.")
        if task.status != TaskStatus.IN_PROGRESS:
            return ManagerResult(success=False, error_message=f"Task {task_id} is {task.status}, expected IN_PROGRESS.")

        plan_id = self._find_plan_for_task(task_id)
        handoff_id = uuid4()

        record = HandOffRecord(
            handoff_id=handoff_id,
            task_id=task_id,
            from_employee_id=from_employee_id,
            handoff_type="review",
            reason="Submitted for review",
            status="requested",
            created_at=time.time(),
        )
        self._handoffs.setdefault(task_id, []).append(record)

        updated = task.with_status(TaskStatus.ASSIGNED).with_assignment(reviewer_id)
        self._tasks[task_id] = updated
        if plan_id:
            self._update_plan_task(plan_id, updated)

        company_task = self._company.register_task(
            title=f"Review: {task.title}",
            metadata={"department": task.department, "plan_id": str(plan_id or ""), "review": "true"},
        )
        self._company.assign_task(reviewer_id, company_task.task_id)

        self._publish(ReviewRequested(
            manager_id=self._manager_id,
            task_id=task_id,
            from_employee_id=from_employee_id,
            reviewer_id=reviewer_id,
            timestamp=time.time(),
        ))

        return ManagerResult(success=True, plan_id=plan_id)

    def complete_review(self, task_id: UUID, reviewer_id: UUID, approved: bool, feedback: str) -> ManagerResult:
        """Complete a review. If approved, task is done; if rejected, routes back."""
        task = self._tasks.get(task_id)
        if task is None:
            return ManagerResult(success=False, error_message=f"Task {task_id} not found.")

        plan_id = self._find_plan_for_task(task_id)

        handoff_id = uuid4()
        record = HandOffRecord(
            handoff_id=handoff_id,
            task_id=task_id,
            from_employee_id=reviewer_id,
            handoff_type="review",
            reason=f"Review {'approved' if approved else 'rejected'}: {feedback}",
            status="completed",
            created_at=time.time(),
        )
        self._handoffs.setdefault(task_id, []).append(record)

        self._publish(ReviewCompleted(
            manager_id=self._manager_id,
            task_id=task_id,
            reviewer_id=reviewer_id,
            approved=approved,
            feedback=feedback,
            timestamp=time.time(),
        ))

        if approved:
            return self.complete_task(task_id, reviewer_id, success=True)

        original_employee = next(
            (r.from_employee_id for r in self._handoffs.get(task_id, [])
             if r.handoff_type == "review" and r.status == "requested"),
            None,
        )
        if original_employee is None:
            return ManagerResult(success=False, error_message="Cannot determine original employee to route back.")

        updated = task.with_status(TaskStatus.ASSIGNED).with_assignment(original_employee)
        self._tasks[task_id] = updated
        if plan_id:
            self._update_plan_task(plan_id, updated)

        return ManagerResult(success=True, plan_id=plan_id)

    def route_task(self, task_id: UUID, from_employee_id: UUID, to_employee_id: UUID, reason: str) -> ManagerResult:
        """Forward a task from one employee to another."""
        task = self._tasks.get(task_id)
        if task is None:
            return ManagerResult(success=False, error_message=f"Task {task_id} not found.")

        plan_id = self._find_plan_for_task(task_id)
        handoff_id = uuid4()

        record = HandOffRecord(
            handoff_id=handoff_id,
            task_id=task_id,
            from_employee_id=from_employee_id,
            handoff_type="forward",
            reason=reason,
            status="completed",
            created_at=time.time(),
        )
        self._handoffs.setdefault(task_id, []).append(record)

        updated = task.with_status(TaskStatus.ASSIGNED).with_assignment(to_employee_id)
        self._tasks[task_id] = updated
        if plan_id:
            self._update_plan_task(plan_id, updated)

        company_task = self._company.register_task(
            title=task.title,
            metadata={"department": task.department, "plan_id": str(plan_id or ""), "routed": "true"},
        )
        self._company.assign_task(to_employee_id, company_task.task_id)

        self._publish(TaskForwarded(
            manager_id=self._manager_id,
            task_id=task_id,
            from_employee_id=from_employee_id,
            to_employee_id=to_employee_id,
            reason=reason,
            timestamp=time.time(),
        ))

        return ManagerResult(success=True, plan_id=plan_id)

    def return_task(self, task_id: UUID, from_employee_id: UUID, reason: str) -> ManagerResult:
        """Return a task to the DepartmentManager (e.g., cannot proceed)."""
        task = self._tasks.get(task_id)
        if task is None:
            return ManagerResult(success=False, error_message=f"Task {task_id} not found.")

        plan_id = self._find_plan_for_task(task_id)
        handoff_id = uuid4()

        record = HandOffRecord(
            handoff_id=handoff_id,
            task_id=task_id,
            from_employee_id=from_employee_id,
            handoff_type="completion",
            reason=reason,
            status="completed",
            created_at=time.time(),
        )
        self._handoffs.setdefault(task_id, []).append(record)

        updated = task.with_status(TaskStatus.PENDING).with_assignment(None)
        self._tasks[task_id] = updated
        if plan_id:
            self._update_plan_task(plan_id, updated)

        self._publish(TaskReturned(
            manager_id=self._manager_id,
            task_id=task_id,
            from_employee_id=from_employee_id,
            reason=reason,
            timestamp=time.time(),
        ))

        return ManagerResult(success=True, plan_id=plan_id)

    def mark_awaiting(self, task_id: UUID, employee_id: UUID, await_type: str, details: str) -> ManagerResult:
        """Mark a task as waiting for an external dependency."""
        task = self._tasks.get(task_id)
        if task is None:
            return ManagerResult(success=False, error_message=f"Task {task_id} not found.")

        plan_id = self._find_plan_for_task(task_id)
        handoff_id = uuid4()

        record = HandOffRecord(
            handoff_id=handoff_id,
            task_id=task_id,
            from_employee_id=employee_id,
            handoff_type=f"awaiting_{await_type}",
            reason=details,
            status="requested",
            created_at=time.time(),
        )
        self._handoffs.setdefault(task_id, []).append(record)

        self._publish(TaskAwaiting(
            manager_id=self._manager_id,
            task_id=task_id,
            employee_id=employee_id,
            await_type=await_type,
            details=details,
            timestamp=time.time(),
        ))

        return ManagerResult(success=True, plan_id=plan_id)

    def resume_task(self, task_id: UUID, employee_id: UUID) -> ManagerResult:
        """Resume a task from a waiting state."""
        task = self._tasks.get(task_id)
        if task is None:
            return ManagerResult(success=False, error_message=f"Task {task_id} not found.")

        plan_id = self._find_plan_for_task(task_id)

        updated = task.with_status(TaskStatus.IN_PROGRESS)
        self._tasks[task_id] = updated
        if plan_id:
            self._update_plan_task(plan_id, updated)

        self._publish(TaskResumed(
            manager_id=self._manager_id,
            task_id=task_id,
            employee_id=employee_id,
            timestamp=time.time(),
        ))

        return ManagerResult(success=True, plan_id=plan_id)

    def handoff_history(self, task_id: UUID) -> tuple[HandOffRecord, ...]:
        """Return the hand-off history for a task."""
        return tuple(self._handoffs.get(task_id, []))

    def manager_id(self) -> UUID:
        return self._manager_id

    def events(self) -> list[Any]:
        if self._event_bus is None:
            return []
        return self._event_bus.events()

    # ------------------------------------------------------------------
    # Learning pipeline - feedback -> history -> prediction
    # ------------------------------------------------------------------

    _CONFIDENCE_BEFORE: float = 0.7
    _CONFIDENCE_AFTER_SUCCESS: float = 0.85
    _CONFIDENCE_AFTER_FAILURE: float = 0.25
    _PREDICTION_HORIZON: float = 3600.0

    def _record_learning(self, task_id: UUID, employee_id: UUID, success: bool) -> None:
        task = self._tasks.get(task_id)
        if task is None:
            return

        confidence_before = self._CONFIDENCE_BEFORE
        confidence_after = self._CONFIDENCE_AFTER_SUCCESS if success else self._CONFIDENCE_AFTER_FAILURE
        delta = confidence_after - confidence_before

        entry = FeedbackEntry(
            recommendation_id=task_id,
            action_id=task_id,
            expected_outcome="success",
            actual_outcome="success" if success else "failure",
            success=success,
            confidence_before=confidence_before,
            confidence_after=confidence_after,
            delta=delta,
            execution_duration=0.0,
            execution_cost=0.0,
            metadata={
                "department": task.department,
                "deliverable": task.deliverable,
                "employee_id": str(employee_id),
                "task_title": task.title,
                "source": "department_manager",
            },
        )

        self._feedback_entries.append(entry)

        new_snapshot = FoundationFeedbackRuntime.build_snapshot(
            self._feedback_entries,
            {"manager_id": str(self._manager_id), "domain": "feedback"},
        )
        old_snapshot = self._last_feedback_snapshot

        historical_snapshot: HistoricalSnapshot | None = None
        prediction_snapshot: PredictionSnapshot | None = None

        if old_snapshot is not None:
            hist_entries = FoundationHistoricalRuntime.compare_feedback(old_snapshot, new_snapshot)
            if hist_entries:
                historical_snapshot = FoundationHistoricalRuntime.build_snapshot(
                    hist_entries,
                    {"domain": "feedback", "manager_id": str(self._manager_id)},
                )
                self._historical_snapshots["feedback"] = historical_snapshot

                predictions = FoundationPredictionRuntime.predict_feedback(
                    new_snapshot, historical_snapshot, horizon=self._PREDICTION_HORIZON,
                )
                if predictions:
                    prediction_snapshot = FoundationPredictionRuntime.build_snapshot(
                        predictions,
                        {"domain": "feedback", "manager_id": str(self._manager_id)},
                    )
                    self._prediction_snapshots["feedback"] = prediction_snapshot

        self._last_feedback_snapshot = new_snapshot

        self._publish(FeedbackRecorded(
            manager_id=self._manager_id,
            task_id=task_id,
            employee_id=employee_id,
            success=success,
            total_entries=len(self._feedback_entries),
            success_rate=new_snapshot.success_rate,
            timestamp=time.time(),
        ))

        if historical_snapshot is not None:
            self._publish(HistoryUpdated(
                manager_id=self._manager_id,
                domain="feedback",
                entry_count=historical_snapshot.total_entries,
                improving_count=historical_snapshot.improving_count,
                declining_count=historical_snapshot.declining_count,
                stable_count=historical_snapshot.stable_count,
                timestamp=time.time(),
            ))

        if prediction_snapshot is not None:
            self._publish(PredictionGenerated(
                manager_id=self._manager_id,
                domain="feedback",
                total_predictions=prediction_snapshot.total_predictions,
                avg_confidence=prediction_snapshot.avg_confidence,
                upward_count=prediction_snapshot.upward_count,
                downward_count=prediction_snapshot.downward_count,
                timestamp=time.time(),
            ))

        emp_stats = self._employee_stats.setdefault(employee_id, {"completed": 0, "succeeded": 0, "failed": 0})
        emp_stats["completed"] += 1
        if success:
            emp_stats["succeeded"] += 1
        else:
            emp_stats["failed"] += 1
        emp_sr = emp_stats["succeeded"] / emp_stats["completed"] if emp_stats["completed"] > 0 else 0.0

        self._publish(EmployeePerformanceUpdated(
            manager_id=self._manager_id,
            employee_id=employee_id,
            tasks_completed=emp_stats["completed"],
            tasks_succeeded=emp_stats["succeeded"],
            tasks_failed=emp_stats["failed"],
            success_rate=round(emp_sr, 2),
            timestamp=time.time(),
        ))

        dept_name = task.department
        dept_stats = self._department_stats.setdefault(dept_name, {"completed": 0, "succeeded": 0, "failed": 0})
        dept_stats["completed"] += 1
        if success:
            dept_stats["succeeded"] += 1
        else:
            dept_stats["failed"] += 1
        dept_sr = dept_stats["succeeded"] / dept_stats["completed"] if dept_stats["completed"] > 0 else 0.0

        self._publish(DepartmentPerformanceUpdated(
            manager_id=self._manager_id,
            department=dept_name,
            tasks_completed=dept_stats["completed"],
            tasks_succeeded=dept_stats["succeeded"],
            tasks_failed=dept_stats["failed"],
            success_rate=round(dept_sr, 2),
            timestamp=time.time(),
        ))

    def learning_state(self) -> dict[str, Any]:
        """Query full learning state - feedback snapshot, history, predictions."""
        fb = self._last_feedback_snapshot
        return {
            "total_feedback_entries": len(self._feedback_entries),
            "feedback_snapshot": fb,
            "historical_snapshots": {k: v for k, v in self._historical_snapshots.items()},
            "prediction_snapshots": {k: v for k, v in self._prediction_snapshots.items()},
        }

    def employee_performance(self, employee_id: UUID) -> dict[str, int] | None:
        """Query cumulative stats for an employee."""
        return self._employee_stats.get(employee_id)

    def department_performance(self, department: str) -> dict[str, int] | None:
        """Query cumulative stats for a department."""
        return self._department_stats.get(department)

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _publish(self, event: Any) -> None:
        if self._event_bus is not None:
            self._event_bus.publish(event)

    def _find_plan_for_task(self, task_id: UUID) -> UUID | None:
        for pid, managed in self._plans.items():
            for t in managed.tasks:
                if t.task_id == task_id:
                    return pid
        return None

    def _update_plan_task(self, plan_id: UUID, updated: DecomposedTask) -> None:
        managed = self._plans[plan_id]
        new_tasks = tuple(
            updated if t.task_id == updated.task_id else self._tasks.get(t.task_id, t)
            for t in managed.tasks
        )
        self._plans[plan_id] = ManagedPlan(
            plan_id=managed.plan_id,
            objective=managed.objective,
            departments=managed.departments,
            tasks=new_tasks,
            created_at=managed.created_at,
        )
