"""Managed content production workflow.

This module keeps the concrete content workflow domain-specific while adding a
DepartmentManager/CompanyTaskRuntime management envelope around it.
"""

from __future__ import annotations

import time
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any
from uuid import UUID, uuid4

from core.company.ceo import ExecutivePlan
from core.company.department_manager import (
    DecomposedTask,
    DepartmentManager,
    TaskStatus,
)
from core.company.specialist_employee import ReceivedTask
from core.content_factory.models import (
    ContentBrief,
    ContentManagedWorkflowResult,
    ContentManagementTaskResult,
    ContentWorkflowEmployees,
    ContentWorkflowResult,
    ContentWorkflowStepResult,
)
from core.content_factory.workflow import ContentProductionWorkflow
from core.employees import (
    Employee,
    EmployeeAvailability,
    EmployeeIdentity,
    EmployeeProfile,
)
from core.runtime import CompanyRuntime

if TYPE_CHECKING:
    from core.company.runtime import CompanyTaskRuntime


@dataclass(frozen=True, slots=True)
class _TaskAttempt:
    task: DecomposedTask
    employee_id: UUID
    assigned: bool
    started: bool
    error: str = ""


class ManagedContentProductionWorkflow(ContentProductionWorkflow):
    """Run the short-video factory with DM plan/progress visibility."""

    _DEPARTMENT_ALIASES: dict[str, tuple[str, ...]] = {
        "Script Production": ("Content Production",),
        "Audio Production": ("Audio Production",),
        "Image Production": ("Marketing",),
        "Video Production": ("Video Editing",),
        "Quality Assurance": ("Quality Assurance",),
    }

    def __init__(
        self,
        department_manager: DepartmentManager,
        *,
        company_runtime: CompanyRuntime | None = None,
        company_task_runtime: CompanyTaskRuntime | None = None,
        auto_register_employees: bool = True,
    ) -> None:
        self._department_manager = department_manager
        self._company_runtime = company_runtime or getattr(department_manager, "_company", None)
        self._company_task_runtime = company_task_runtime
        self._auto_register_employees = auto_register_employees
        self._active_plan_id: UUID | None = None
        self._management_records: list[ContentManagementTaskResult] = []

        if self._company_task_runtime is not None:
            self._company_task_runtime.register_department_manager(department_manager)

    def run_short_video_managed(
        self,
        brief: ContentBrief,
        employees: ContentWorkflowEmployees,
    ) -> ContentManagedWorkflowResult:
        """Create a DM plan, execute production, and report managed progress."""
        self._management_records = []
        self._ensure_runtime_employees(employees)

        plan = self._build_plan(brief)
        plan_result = self._department_manager.receive_plan(plan)
        if not plan_result.success:
            return ContentManagedWorkflowResult(
                success=False,
                plan_id=plan.plan_id,
                error=plan_result.error_message,
            )

        self._active_plan_id = plan.plan_id
        try:
            workflow_result = super().run_short_video(brief, employees)
            if workflow_result.success:
                self._complete_quality_signoff(employees.video_editor.employee_id)
        finally:
            self._active_plan_id = None

        progress_result = self._department_manager.report_progress(plan.plan_id)
        progress = progress_result.progress
        completed = progress.completed if progress is not None else 0
        total = progress.total if progress is not None else 0
        progress_pct = progress.progress_pct if progress is not None else 0.0
        company_progress = self._company_progress()
        health_state = self._health_state()

        return ContentManagedWorkflowResult(
            success=workflow_result.success and progress_pct == 100.0,
            workflow_result=workflow_result,
            plan_id=plan.plan_id,
            management_tasks=tuple(self._management_records),
            progress_pct=progress_pct,
            completed_tasks=completed,
            total_tasks=total,
            company_progress=company_progress,
            health_state=health_state,
            error="" if workflow_result.success and progress_pct == 100.0 else workflow_result.error,
        )

    def _execute(self, employee: Any, task: ReceivedTask) -> ContentWorkflowStepResult:
        attempts = self._activate_management_tasks(task.department, employee.employee_id)
        step = super()._execute(employee, task)
        self._finish_management_tasks(task.department, attempts, step.success, step.error)
        return step

    def _build_plan(self, brief: ContentBrief) -> ExecutivePlan:
        topic = brief.topic
        return ExecutivePlan(
            plan_id=uuid4(),
            objective=f"Produce managed short video package for {topic}",
            departments=(
                "Content Production",
                "Audio Production",
                "Marketing",
                "Video Editing",
                "Quality Assurance",
            ),
            risks=(
                "Missing API credentials for paid providers",
                "Rendered asset may require manual approval before publishing",
            ),
            deliverables=(
                "content script piece",
                "audio voiceover file",
                "market campaign creative asset",
                "video short render",
                "quality sign-off rendered asset",
            ),
            success_metrics=(
                "All department steps succeed",
                "Final package quality passes",
                "DepartmentManager progress reaches 100%",
            ),
            completion_criteria=(
                "Script, audio, image, video, and QA management tasks completed",
                "Final production package returned to the operator",
            ),
            estimated_duration_days=1,
            priority="high",
            created_at=time.time(),
            metadata={
                "source": "content_factory_managed_workflow",
                "platform": brief.platform,
                "video_type": brief.video_type,
                "duration_seconds": brief.duration_seconds,
            },
        )

    def _activate_management_tasks(
        self,
        workflow_department: str,
        employee_id: UUID,
    ) -> tuple[_TaskAttempt, ...]:
        if self._active_plan_id is None:
            return ()

        tasks = self._pending_tasks_for(workflow_department)
        attempts: list[_TaskAttempt] = []
        for task in tasks:
            assigned = False
            started = False
            error = ""
            try:
                assigned_result = self._department_manager.assign_task(task.task_id, employee_id)
                assigned = assigned_result.success
                if not assigned:
                    error = assigned_result.error_message
                if assigned:
                    started_result = self._department_manager.start_task(task.task_id, employee_id)
                    started = started_result.success
                    if not started:
                        error = started_result.error_message
            except (KeyError, ValueError) as exc:
                error = str(exc)

            attempts.append(_TaskAttempt(
                task=task,
                employee_id=employee_id,
                assigned=assigned,
                started=started,
                error=error,
            ))
        return tuple(attempts)

    def _finish_management_tasks(
        self,
        workflow_department: str,
        attempts: tuple[_TaskAttempt, ...],
        step_success: bool,
        step_error: str,
    ) -> None:
        for attempt in attempts:
            completed = False
            success = False
            error = attempt.error or step_error
            try:
                complete_result = self._department_manager.complete_task(
                    attempt.task.task_id,
                    attempt.employee_id,
                    success=step_success and attempt.assigned,
                )
                completed = complete_result.success
                success = completed and step_success and attempt.assigned
                if not completed:
                    error = complete_result.error_message
            except (KeyError, ValueError) as exc:
                error = str(exc)

            self._management_records.append(ContentManagementTaskResult(
                workflow_department=workflow_department,
                manager_department=attempt.task.department,
                manager_task_id=attempt.task.task_id,
                manager_task_title=attempt.task.title,
                deliverable=attempt.task.deliverable,
                employee_id=attempt.employee_id,
                assigned=attempt.assigned,
                started=attempt.started,
                completed=completed,
                success=success,
                error=error,
            ))

    def _complete_quality_signoff(self, employee_id: UUID) -> None:
        attempts = self._activate_management_tasks("Quality Assurance", employee_id)
        self._finish_management_tasks("Quality Assurance", attempts, True, "")

    def _pending_tasks_for(self, workflow_department: str) -> tuple[DecomposedTask, ...]:
        if self._active_plan_id is None:
            return ()
        aliases = self._DEPARTMENT_ALIASES.get(workflow_department, (workflow_department,))
        tasks = self._department_manager.tasks_for_plan(self._active_plan_id)
        return tuple(
            task for task in tasks
            if task.department in aliases and task.status == TaskStatus.PENDING
        )

    def _ensure_runtime_employees(self, employees: ContentWorkflowEmployees) -> None:
        if not self._auto_register_employees or self._company_runtime is None:
            return

        existing = {snapshot.employee_id for snapshot in self._company_runtime.employees()}
        employee_specs = (
            (employees.script_writer.employee_id, "Script Writer", "Content Production"),
            (employees.audio_engineer.employee_id, "Audio Engineer", "Audio Production"),
            (employees.image_designer.employee_id, "Image Designer", "Marketing"),
            (employees.video_editor.employee_id, "Video Editor", "Video Editing"),
        )

        for employee_id, name, department in employee_specs:
            if employee_id in existing:
                continue
            self._company_runtime.register_employee(
                Employee(
                    identity=EmployeeIdentity(employee_id=employee_id, display_name=name),
                    profile=EmployeeProfile(full_name=name, department_name=department),
                    availability=EmployeeAvailability(is_available=True),
                )
            )
            existing.add(employee_id)

    def _company_progress(self) -> dict[str, Any]:
        if self._company_task_runtime is None:
            return {}
        return dict(self._company_task_runtime.company_progress())

    def _health_state(self) -> dict[str, Any]:
        if self._company_task_runtime is None:
            return {}
        health = self._company_task_runtime.company_health()
        return {
            "company_state": health.company_state,
            "active_plans": health.active_plans,
            "total_employees": health.total_employees,
            "total_tasks": health.total_tasks,
            "completed_tasks": health.completed_tasks,
            "pending_tasks": health.pending_tasks,
            "blocked_tasks": health.blocked_tasks,
            "success_rate": health.success_rate,
            "has_feedback": health.has_feedback,
            "has_history": health.has_history,
            "has_predictions": health.has_predictions,
            "recommendations": tuple(health.recommendations),
        }
