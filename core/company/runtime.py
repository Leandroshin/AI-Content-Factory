"""Company Orchestrator - coordinates the full task lifecycle and
provides global visibility across the AI Company.

Flow: receive_task -> route_task -> Orchestrator.execute_task ->
      (WorkflowRuntime when applicable) -> ExecutionRuntime ->
      LearningPipeline -> complete_task

The orchestrator also consumes Feedback, Historical, Prediction,
and Observability to provide company-wide health, progress, and
recommendation queries.
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any
from uuid import UUID

from core.conversation import ConversationSession
from core.events.bus import EventBus
from core.events.domain_events import (
    CompanyTaskCompleted,
    CompanyTaskReceived,
    CompanyTaskRouted,
)
from core.llm.models import LLMRequest
from core.orchestrator.runtime import (
    OrchestratorExecutionResult,
    OrchestratorRuntime,
)
from core.persistence._helpers import CompanyTaskEntrySnapshot, save_if_enabled
from core.runtime import CompanyRuntime as CoreCompanyRuntime
from core.skills.runtime import SkillRuntime

if TYPE_CHECKING:
    from core.company.department_manager import DepartmentManager
    from core.observability import ObservabilityProjector
    from core.persistence.runtime import PersistenceRuntime


@dataclass(frozen=True, slots=True)
class CompanyExecutionResult:
    """Outcome of a full company-level task cycle.

    Attributes:
        task_id: The task that was executed.
        workflow_result: WorkflowRuntime snapshot, if a workflow was involved.
        orchestrator_result: The full OrchestratorExecutionResult.
        decision_result: The DecisionResult from candidate selection.
        execution_result: The ExecutionResult from AI execution.
        learning_pipeline_result: The PipelineResult from auto-learning.
        success: True if the entire cycle succeeded.
        duration: Wall-clock time in seconds.
    """

    task_id: UUID
    workflow_result: Any = None
    orchestrator_result: OrchestratorExecutionResult | None = None
    decision_result: Any = None
    execution_result: Any = None
    learning_pipeline_result: Any = None
    success: bool = False
    duration: float = 0.0


@dataclass(frozen=True, slots=True)
class CompanyHealthReport:
    """Snapshot of company health at a point in time.

    Aggregates data from DepartmentManager, CompanyRuntime,
    Observability, Feedback, Historical, and Prediction.
    """

    company_state: str
    active_plans: int
    total_employees: int
    busy_employees: int
    idle_employees: int
    total_tasks: int
    completed_tasks: int
    pending_tasks: int
    blocked_tasks: int
    success_rate: float
    has_feedback: bool
    has_history: bool
    has_predictions: bool
    predicted_success_rate: float | None = None
    recommendations: tuple[str, ...] = field(default_factory=tuple)
    timestamp: float = 0.0


@dataclass(slots=True)
class _TaskEntry:
    """Internal tracking record for a task in the company runtime."""

    task_id: UUID
    title: str
    stage: str = "received"
    orchestrator_snapshot: Any = None
    metadata: dict[str, Any] = field(default_factory=dict)


class CompanyTaskRuntime:
    """High-level company runtime that coordinates the full task lifecycle.

    Wraps OrchestratorRuntime, CoreCompanyRuntime, and optionally
    WorkflowRuntime to provide a single entry point for the complete
    company task flow: receive -> route -> execute -> learn -> complete.

    Args:
        core_company: The low-level CompanyRuntime (core.runtime).
        orchestrator: The OrchestratorRuntime instance.
        skill_runtime: Optional SkillRuntime for automatic skill promotion.
    """

    def __init__(
        self,
        core_company: CoreCompanyRuntime,
        orchestrator: OrchestratorRuntime,
        skill_runtime: SkillRuntime | None = None,
        event_bus: EventBus | None = None,
        persistence_runtime: PersistenceRuntime | None = None,
        department_manager: DepartmentManager | None = None,
        observability: ObservabilityProjector | None = None,
    ) -> None:
        self._core = core_company
        self._orchestrator = orchestrator
        self._skill_runtime = skill_runtime
        self._event_bus = event_bus
        self._persistence = persistence_runtime
        self._tasks: dict[UUID, _TaskEntry] = {}
        self._dm: DepartmentManager | None = department_manager
        self._observer: ObservabilityProjector | None = observability

    # ------------------------------------------------------------------
    # Task lifecycle
    # ------------------------------------------------------------------

    def receive_task(self, title: str, *, metadata: dict[str, Any] | None = None) -> UUID:
        """Register a new task in the company.

        Delegates to OrchestratorRuntime.receive_task() and stores
        internal tracking state.

        Args:
            title: Human-readable task title.
            metadata: Optional metadata for the task.

        Returns:
            The UUID of the newly created task.
        """
        snapshot = self._orchestrator.receive_task(title)
        task_id = snapshot.task.task_id
        self._tasks[task_id] = _TaskEntry(
            task_id=task_id,
            title=title,
            stage="received",
            orchestrator_snapshot=snapshot,
            metadata=dict(metadata) if metadata else {},
        )
        self._publish(CompanyTaskReceived(
            task_id=task_id, title=title,
            timestamp=time.time(),
        ))
        self._save_task(task_id)
        return task_id

    def route_task(self, task_id: UUID, department_id: UUID, employee_id: UUID) -> None:
        """Route a received task to a department and employee.

        Delegates to OrchestratorRuntime.route_task().

        Args:
            task_id: The task to route.
            department_id: Target department.
            employee_id: Target employee.

        Raises:
            KeyError: If the task is unknown to the orchestrator.
        """
        self._orchestrator.route_task(task_id, department_id, employee_id)
        entry = self._tasks.get(task_id)
        if entry is not None:
            entry.stage = "routed"
        self._save_task(task_id)
        self._publish(CompanyTaskRouted(
            task_id=task_id, department_id=department_id,
            employee_id=employee_id, timestamp=time.time(),
        ))

    def execute_company_task(
        self,
        task_id: UUID,
        *,
        candidate_snapshots: list[Any],
        department_snapshot: Any = None,
        skill_snapshots: list[Any] | None = None,
        policy_constraints: list[Any] | None = None,
        policy_rules: list[Any] | None = None,
        llm_request: LLMRequest | None = None,
        gateway: Any = None,
        gateway_provider: str | None = None,
        metadata: dict[str, Any] | None = None,
        conversation_session: ConversationSession | None = None,
        workflow_runtime: Any = None,
        workflow_id: UUID | None = None,
    ) -> CompanyExecutionResult:
        """Execute the full company task cycle.

        Flow:
            1. OrchestratorRuntime.execute_task() -> decide -> execute -> learn
            2. WorkflowRuntime (if applicable) -> advance workflow
            3. OrchestratorRuntime.complete_task() -> finalise

        Args:
            task_id: The task to execute.
            candidate_snapshots: Eligible employee snapshots.
            department_snapshot: Department context.
            skill_snapshots: Legacy skill snapshots.
            policy_constraints: Hard policy constraints.
            policy_rules: Declarative policy rules.
            llm_request: LLM request for execution.
            gateway: LLM gateway for execution.
            gateway_provider: Optional provider name.
            metadata: Optional metadata for decision/execution.
            conversation_session: Optional session to continue.
            workflow_runtime: Optional stateful WorkflowRuntime instance.
            workflow_id: Optional workflow this task belongs to.

        Returns:
            A CompanyExecutionResult with all intermediate results.
        """
        start = time.perf_counter()

        entry = self._tasks.get(task_id)
        task_snapshot = entry.orchestrator_snapshot if entry else None

        if task_snapshot is None:
            snapshots = getattr(self._orchestrator, "_tasks", {})
            task_snapshot = snapshots.get(task_id)

        if task_snapshot is None:
            return CompanyExecutionResult(
                task_id=task_id,
                success=False,
                duration=time.perf_counter() - start,
            )

        merged_metadata = dict(metadata) if metadata else {}
        merged_metadata["_company_task_title"] = entry.title if entry else ""

        # --- Orchestrate: decide -> execute -> learn ---
        orchestrator_result = OrchestratorRuntime.execute_task(
            task_snapshot=task_snapshot,
            candidate_snapshots=list(candidate_snapshots),
            department_snapshot=department_snapshot,
            skill_snapshots=list(skill_snapshots) if skill_snapshots else None,
            skill_runtime=self._skill_runtime,
            policy_constraints=list(policy_constraints) if policy_constraints else None,
            policy_rules=list(policy_rules) if policy_rules else None,
            llm_request=llm_request,
            gateway=gateway,
            gateway_provider=gateway_provider,
            metadata=merged_metadata,
            conversation_session=conversation_session,
        )

        success = orchestrator_result.success

        # --- Workflow integration (when applicable) ---
        workflow_result = None
        if success and workflow_runtime is not None and workflow_id is not None:
            try:
                workflow_result = workflow_runtime.complete_task(workflow_id, task_id)
            except (KeyError, ValueError):
                pass

        # --- Complete the task in the orchestrator ---
        if success:
            try:
                self._orchestrator.complete_task(task_id)
            except (KeyError, ValueError):
                pass

        if entry is not None:
            entry.stage = "completed" if success else "failed"
        self._save_task(task_id)

        self._publish(CompanyTaskCompleted(
            task_id=task_id, success=success,
            duration=time.perf_counter() - start,
            timestamp=time.time(),
        ))

        return CompanyExecutionResult(
            task_id=task_id,
            workflow_result=workflow_result,
            orchestrator_result=orchestrator_result,
            decision_result=orchestrator_result.decision_result,
            execution_result=orchestrator_result.execution_result,
            learning_pipeline_result=orchestrator_result.learning_pipeline_result,
            success=success,
            duration=time.perf_counter() - start,
        )

    def complete_task(self, task_id: UUID) -> None:
        """Mark a task as completed in the orchestrator.

        Args:
            task_id: The task to complete.

        Raises:
            KeyError: If the task is not assigned to an employee.
        """
        self._orchestrator.complete_task(task_id)
        entry = self._tasks.get(task_id)
        if entry is not None:
            entry.stage = "completed"
        self._save_task(task_id)
        self._publish(CompanyTaskCompleted(
            task_id=task_id, success=True,
            timestamp=time.time(),
        ))

    # ------------------------------------------------------------------
    # Queries
    # ------------------------------------------------------------------

    def task_state(self, task_id: UUID) -> str | None:
        """Get the current stage of a tracked task."""
        entry = self._tasks.get(task_id)
        return entry.stage if entry else None

    def _save_task(self, task_id: UUID) -> None:
        entry = self._tasks.get(task_id)
        if entry is not None:
            snap = CompanyTaskEntrySnapshot(
                task_id=entry.task_id,
                title=entry.title,
                stage=entry.stage,
                metadata=entry.metadata,
            )
            persistence = getattr(self, "_persistence", None)
            save_if_enabled(persistence, snap, "company_task", task_id)

    def _publish(self, event: Any) -> None:
        if self._event_bus is not None:
            self._event_bus.publish(event)

    def task_titles(self) -> list[str]:
        """List all tracked task titles."""
        return [e.title for e in self._tasks.values()]

    def task_count(self) -> int:
        """Number of tracked tasks."""
        return len(self._tasks)

    # ------------------------------------------------------------------
    # Company coordination - DepartmentManager + Observability binding
    # ------------------------------------------------------------------

    def register_department_manager(self, dm: DepartmentManager) -> None:
        """Bind a DepartmentManager for plan/task visibility."""
        self._dm = dm

    def register_observability(self, observer: ObservabilityProjector) -> None:
        """Bind an ObservabilityProjector for state projection."""
        self._observer = observer

    # ------------------------------------------------------------------
    # Company coordination - live queries
    # ------------------------------------------------------------------

    def active_plans(self) -> list[dict[str, Any]]:
        """Return all active plans with current progress."""
        if self._dm is None:
            return []
        plans = self._dm.list_plans()
        result: list[dict[str, Any]] = []
        for p in plans:
            state = self._dm.plan_state(p["plan_id"])
            if state:
                result.append(state)
            else:
                result.append(p)
        return result

    def active_departments(self) -> list[dict[str, Any]]:
        """Return departments with task counts and success rates."""
        if self._dm is None:
            return []
        seen: dict[str, dict[str, Any]] = {}
        for p in self._dm.list_plans():
            state = self._dm.plan_state(p["plan_id"])
            if state:
                for dept_name, count in state.get("tasks_by_department", {}).items():
                    if dept_name not in seen:
                        perf = self._dm.department_performance(dept_name) or {}
                        seen[dept_name] = {
                            "name": dept_name,
                            "tasks": count,
                            "completed": perf.get("completed", 0),
                            "succeeded": perf.get("succeeded", 0),
                            "failed": perf.get("failed", 0),
                            "success_rate": (
                                perf["succeeded"] / perf["completed"]
                                if perf.get("completed", 0) > 0 else 0.0
                            ),
                        }
                    else:
                        seen[dept_name]["tasks"] += count
        return list(seen.values())

    def active_employees(self) -> list[dict[str, Any]]:
        """Return employees with current state and performance."""
        result: list[dict[str, Any]] = []
        for snap in self._core.employees():
            emp_id = snap.employee_id
            perf = self._dm.employee_performance(emp_id) if self._dm else None
            result.append({
                "employee_id": emp_id,
                "name": getattr(snap, "name", str(emp_id.hex[:8])),
                "state": snap.state if hasattr(snap, "state") else "unknown",
                "tasks_completed": perf.get("completed", 0) if perf else 0,
                "tasks_succeeded": perf.get("succeeded", 0) if perf else 0,
                "tasks_failed": perf.get("failed", 0) if perf else 0,
                "success_rate": (
                    perf["succeeded"] / perf["completed"]
                    if perf and perf.get("completed", 0) > 0 else 0.0
                ),
            })
        return result

    def blocked_tasks(self) -> list[dict[str, Any]]:
        """Return tasks that are blocked or pending without progress."""
        if self._dm is None:
            return []
        blocked: list[dict[str, Any]] = []
        for p in self._dm.list_plans():
            tasks = self._dm.tasks_for_plan(p["plan_id"])
            for t in tasks:
                if t.status.value in ("pending", "failed"):
                    blocked.append({
                        "task_id": t.task_id,
                        "title": t.title,
                        "department": t.department,
                        "status": t.status.value,
                        "deliverable": t.deliverable,
                        "plan_id": p["plan_id"],
                    })
        return blocked

    def company_progress(self) -> dict[str, Any]:
        """Aggregate global progress across all plans."""
        if self._dm is None:
            return {"total_tasks": 0, "completed_tasks": 0, "progress_pct": 0.0}
        plans = self.active_plans()
        total = sum(p.get("total_tasks", 0) for p in plans)
        completed = sum(p.get("completed_tasks", 0) for p in plans)
        progress = round(completed / total * 100, 1) if total > 0 else 0.0
        return {
            "total_tasks": total,
            "completed_tasks": completed,
            "pending_tasks": total - completed,
            "progress_pct": progress,
            "active_plans": len(plans),
        }

    def company_health(self) -> CompanyHealthReport:
        """Full diagnostic of company health.

        Aggregates DepartmentManager, CompanyRuntime, Observability,
        Feedback, Historical, and Prediction into a single report.
        """
        progress = self.company_progress()
        emps = self.active_employees()
        total_emp = len(emps)
        busy_emp = sum(1 for e in emps if e["state"] == "busy")
        idle_emp = total_emp - busy_emp

        plans = self.active_plans()
        active_plan_count = len(plans)

        total_tasks = progress["total_tasks"]
        completed_tasks = progress["completed_tasks"]
        pending_tasks = progress["pending_tasks"]
        blocked = self.blocked_tasks()
        blocked_count = len(blocked)

        # Learning data from DM
        learning = self._dm.learning_state() if self._dm else {}
        fb = learning.get("feedback_snapshot")
        success_rate = fb.success_rate if fb else 0.0
        has_feedback = fb is not None
        has_history = bool(learning.get("historical_snapshots", {}))
        has_predictions = bool(learning.get("prediction_snapshots", {}))

        # Prediction data
        pred_snapshot = None
        if has_predictions:
            preds = learning["prediction_snapshots"]
            pred_snapshot = preds.get("feedback")

        predicted_success_rate = None
        if pred_snapshot and pred_snapshot.total_predictions > 0:
            predicted_entries = [
                e for e in pred_snapshot.entries
                if "success" in e.metric_name.lower() or "rate" in e.metric_name.lower()
            ]
            if predicted_entries:
                predicted_success_rate = round(
                    sum(e.predicted_value for e in predicted_entries) / len(predicted_entries),
                    2,
                )

        recommendations = self.next_recommended_actions()

        return CompanyHealthReport(
            company_state=self._core.state().value,
            active_plans=active_plan_count,
            total_employees=total_emp,
            busy_employees=busy_emp,
            idle_employees=idle_emp,
            total_tasks=total_tasks,
            completed_tasks=completed_tasks,
            pending_tasks=pending_tasks,
            blocked_tasks=blocked_count,
            success_rate=round(success_rate, 2),
            has_feedback=has_feedback,
            has_history=has_history,
            has_predictions=has_predictions,
            predicted_success_rate=predicted_success_rate,
            recommendations=tuple(recommendations),
            timestamp=time.time(),
        )

    def next_recommended_actions(self) -> list[str]:
        """Generate recommendations based on current company state.

        Uses predictions, health data, and operational state to suggest
        actions. Predictions do NOT alter decisions - they only inform.
        """
        actions: list[str] = []

        if self._dm is None:
            return actions

        emps = self.active_employees()
        progress = self.company_progress()
        blocked = self.blocked_tasks()
        learning = self._dm.learning_state()

        # Blocked tasks
        if blocked:
            dept_blocked: dict[str, int] = {}
            for b in blocked:
                dept_blocked[b["department"]] = dept_blocked.get(b["department"], 0) + 1
            worst_dept = max(dept_blocked, key=dept_blocked.get)
            actions.append(
                f"{len(blocked)} task(s) blocked/pending - "
                f"review '{worst_dept}' workload"
            )

        # Overloaded departments
        dept_info = self.active_departments()
        overloaded = [d for d in dept_info if d["tasks"] > 0 and d["success_rate"] < 0.5]
        if overloaded:
            names = ", ".join(d["name"] for d in overloaded[:3])
            actions.append(f"Department(s) {names} below 50% success rate - consider process review")

        # Busy employees
        busy_pct = sum(1 for e in emps if e["state"] == "busy")
        busy_ratio = (busy_pct / len(emps) * 100) if emps else 0
        if busy_ratio > 80 and emps:
            actions.append(f"{busy_ratio:.0f}% employees busy - consider hiring or redistribution")

        # Predictions
        preds = learning.get("prediction_snapshots", {})
        pred_snap = preds.get("feedback") if preds else None
        if pred_snap and pred_snap.downward_count > pred_snap.upward_count:
            actions.append(
                f"Prediction trend is downward ({pred_snap.downward_count} down "
                f"vs {pred_snap.upward_count} up) - investigate declining metrics"
            )

        # Progress
        if progress["progress_pct"] > 0 and progress["progress_pct"] < 30:
            actions.append("Company progress below 30% - consider increasing capacity")

        if not actions:
            if progress["progress_pct"] >= 100:
                actions.append("All plans completed - company is idle, awaiting new goals")
            else:
                actions.append("Company operating within normal parameters - monitor regularly")

        return actions
