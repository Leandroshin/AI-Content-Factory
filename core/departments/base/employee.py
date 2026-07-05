"""ProductionEmployee — base class for all production department employees.

Herda SpecialistEmployee e adiciona:
- pipeline de produção genérico
- integração com QualityRuntime
- coleta de métricas
- fluxo de execução reutilizável
- serialização de estado genérico

Departamentos concretos (Video, Audio, Image, etc.):
1. Herdam ProductionEmployee
2. Definem seu próprio pipeline (extends ProductionPipeline)
3. Implementam receive_task() específico
4. Sobrescrevem hooks de output/build se necessário
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Any
from uuid import UUID

from core.company.department_manager import DepartmentManager
from core.company.quality import QualityRuntime
from core.company.specialist_employee import (
    EmployeeSkill,
    EmployeeStatus,
    ExecutionResult,
    ReceivedTask,
    SpecialistEmployee,
    TaskAccepted,
    TaskDecision,
    TaskFinished,
    TaskRejected,
    TaskStarted,
)
from core.departments.base.models import ProductionMetrics
from core.departments.base.pipeline import ProductionPipeline, StageResult
from core.events.bus import EventBus
from core.events.domain_events import (
    ProductionCompleted,
    ProductionStageAdvanced,
    ProductionStarted,
)
from core.runtime import CompanyRuntime as CoreCompanyRuntime
from core.tools.capabilities import Capability
from core.tools.registry import ToolRegistry
from core.tools.runtime import ToolRuntime


_DEPARTMENT_KEYWORD: str = ""  # override in subclass


class ProductionEmployee(SpecialistEmployee):
    """Base class for all AI Company production employees.

    Usage::

        class VideoEditorEmployee(ProductionEmployee):
            _DEPARTMENT_KEYWORD = "video"

            def _build_pipeline(self, task: ReceivedTask) -> ProductionPipeline:
                return VideoProductionPipeline(...)

            def _estimate_duration(self, ctx: dict[str, Any]) -> int:
                ...

            def _reject_reason(self, task: ReceivedTask) -> str | None:
                ...  # return str to reject, None to accept
    """

    _DEPARTMENT_KEYWORD: str = ""

    def __init__(
        self,
        company_runtime: CoreCompanyRuntime,
        employee_id: UUID,
        skills: tuple[EmployeeSkill, ...] = (),
        *,
        event_bus: EventBus | None = None,
        department_manager: DepartmentManager | None = None,
        tool_runtime: ToolRuntime | None = None,
        tool_registry: ToolRegistry | None = None,
        quality_runtime: QualityRuntime | None = None,
    ) -> None:
        super().__init__(
            company_runtime=company_runtime,
            employee_id=employee_id,
            skills=skills,
            event_bus=event_bus,
            department_manager=department_manager,
            tool_runtime=tool_runtime,
            tool_registry=tool_registry,
        )
        self._quality_runtime = quality_runtime
        self._pipeline: ProductionPipeline | None = None
        self._production_metrics: ProductionMetrics = ProductionMetrics()
        self._max_workload: int = 3

    # ------------------------------------------------------------------
    # Properties
    # ------------------------------------------------------------------

    @property
    def pipeline_stage(self) -> str | None:
        if self._pipeline is not None:
            return self._pipeline.stage
        return None

    @property
    def production_metrics(self) -> ProductionMetrics:
        return self._production_metrics

    # ------------------------------------------------------------------
    # Task handling — departments override for domain logic
    # ------------------------------------------------------------------

    def receive_task(self, task: ReceivedTask) -> TaskDecision:
        reject = self._check_reject(task)
        if reject is not None:
            self._total_tasks_rejected += 1
            self._publish(TaskRejected(
                employee_id=self._employee_id,
                task_id=task.task_id,
                title=task.title,
                reason=reject,
                missing_skills=(),
                timestamp=time.time(),
            ))
            return TaskDecision.REJECTED

        self._tasks[task.task_id] = task
        self._current_task_id = task.task_id
        self._workload += 1
        self._status = EmployeeStatus.ANALYZING

        self._pipeline = self._build_pipeline(task)

        self._publish(TaskAccepted(
            employee_id=self._employee_id,
            task_id=task.task_id,
            title=task.title,
            difficulty=0.5,
            estimated_time_minutes=self._estimate_duration(task.context),
            timestamp=time.time(),
        ))
        return TaskDecision.ACCEPTED

    def _check_reject(self, task: ReceivedTask) -> str | None:
        """Return rejection reason string, or None to accept."""
        keyword = self._DEPARTMENT_KEYWORD
        if keyword and keyword not in task.department.lower():
            return f"Department '{task.department}' is not {keyword}"
        if self._workload >= self._max_workload:
            return "Workload limit reached (max {self._max_workload})"
        return None

    # ------------------------------------------------------------------
    # Execute — generic flow with overrideable hooks
    # ------------------------------------------------------------------

    def execute_task(self, task_id: UUID) -> ExecutionResult:
        task = self._tasks.get(task_id)
        if task is None:
            return ExecutionResult(success=False, summary="", error="Task not found")

        if self._pipeline is None:
            return ExecutionResult(success=False, summary="", error="No pipeline initialized")

        start_time = time.time()
        self._status = EmployeeStatus.WORKING
        now = time.time()
        self._publish(TaskStarted(
            employee_id=self._employee_id,
            task_id=task_id,
            title=task.title,
            timestamp=now,
        ))

        dept = self._DEPARTMENT_KEYWORD
        prod_type = self._get_production_type()

        initial_stage = self._pipeline.stage
        self._publish(ProductionStarted(
            employee_id=self._employee_id,
            task_id=task_id,
            department=dept,
            production_type=prod_type,
            stage=initial_stage,
            timestamp=now,
        ))

        # Advance pipeline through all stages
        stages_completed = 0
        stages_failed = 0
        while self._pipeline.stage not in ("completed", "failed"):
            t = time.time()
            result = self._pipeline.advance()
            if result.success:
                stages_completed += 1
            else:
                stages_failed += 1
            self._publish(ProductionStageAdvanced(
                employee_id=self._employee_id,
                task_id=task_id,
                department=dept,
                stage=result.stage,
                progress=self._pipeline.progress,
                success=result.success,
                error=result.error,
                timestamp=t,
                stages_completed=stages_completed,
                stages_failed=stages_failed,
            ))

        final_output: dict[str, Any] = {"pipeline_progress": self._pipeline.progress}
        success = self._pipeline.stage == "completed"
        summary_parts: list[str] = []

        if success:
            self._build_output_from_stages(final_output, summary_parts)

            quality_passed, corrections = self._run_quality_check(final_output)
            if not quality_passed:
                summary_parts.append(f"Quality: {len(corrections)} issues")
                final_output["quality_issues"] = corrections
                final_output["quality_passed"] = False
        else:
            for slog in self._pipeline.stages_log:
                if not slog.success:
                    summary_parts.append(f"Failed at {slog.stage}: {slog.error}")
                    final_output["error"] = slog.error

        duration = (time.time() - start_time) / 60.0

        self._production_metrics = self._build_metrics(
            stages_completed, stages_failed, final_output, duration,
        )

        summary = self._build_summary(success, summary_parts)
        result = ExecutionResult(
            success=success,
            summary=summary,
            output=final_output,
            duration_minutes=round(duration, 2),
            error=final_output.get("error", ""),
        )

        final_now = time.time()
        self._publish(ProductionCompleted(
            employee_id=self._employee_id,
            task_id=task_id,
            department=dept,
            success=success,
            summary=summary,
            output=final_output,
            duration_minutes=round(duration, 2),
            timestamp=final_now,
        ))

        self._status = EmployeeStatus.COMPLETED if success else EmployeeStatus.IDLE
        self._publish(TaskFinished(
            employee_id=self._employee_id,
            task_id=task_id,
            success=success,
            summary=summary,
            output=final_output,
            duration_minutes=round(duration, 2),
            timestamp=final_now,
        ))

        if success and self._department_manager is not None:
            self._department_manager.complete_task(task_id, self._employee_id, success=True)

        self._total_tasks_completed += 1
        return result

    # ------------------------------------------------------------------
    # Overrideable hooks
    # ------------------------------------------------------------------

    def _build_pipeline(self, task: ReceivedTask) -> ProductionPipeline:
        """Create a pipeline for the given task."""
        raise NotImplementedError

    def _estimate_duration(self, ctx: dict[str, Any]) -> int:
        return 10

    def _get_production_type(self) -> str:
        """Return the department-specific production type (e.g. 'thumbnail', 'voiceover').
        Override in each department to return the type from the current task model.
        """
        return ""

    def _build_output_from_stages(
        self, final_output: dict[str, Any], summary_parts: list[str],
    ) -> None:
        """Populate final_output and summary_parts from pipeline stages_log.

        Override in department to extract domain-specific output.
        """
        for slog in self._pipeline.stages_log:
            if slog.success:
                final_output.update(slog.output)
                summary_parts.append(slog.summary)

    def _build_metrics(
        self,
        stages_completed: int,
        stages_failed: int,
        final_output: dict[str, Any],
        duration: float,
    ) -> ProductionMetrics:
        return ProductionMetrics(
            total_stages=stages_completed + stages_failed,
            completed_stages=stages_completed,
            failed_stages=stages_failed,
            quality_passed=final_output.get("quality_passed", True),
            quality_corrections=tuple(final_output.get("quality_issues", [])),
            duration_minutes=round(duration, 2),
        )

    def _build_summary(self, success: bool, summary_parts: list[str]) -> str:
        if summary_parts:
            return " | ".join(summary_parts)
        return "Production completed" if success else "Production failed"

    # ------------------------------------------------------------------
    # Quality
    # ------------------------------------------------------------------

    def _run_quality_check(self, output: dict[str, Any]) -> tuple[bool, list[str]]:
        if self._quality_runtime is None:
            return True, []

        exec_id = self._current_task_id or UUID(int=0)
        report = self._quality_runtime.validate(exec_id, {
            "success": output.get("error", "") == "",
            "error": output.get("error", ""),
        })

        if report.passed:
            return True, []
        return False, self._quality_runtime.generate_correction(report)

    # ------------------------------------------------------------------
    # Capability analysis — override in department
    # ------------------------------------------------------------------

    def analyze_capability_needs(self) -> tuple[Capability, ...]:
        return ()

    # ------------------------------------------------------------------
    # State
    # ------------------------------------------------------------------

    def state(self) -> dict[str, Any]:
        base = super().state()
        base["pipeline_stage"] = self.pipeline_stage
        base["production_metrics"] = {
            "total_stages": self._production_metrics.total_stages,
            "completed_stages": self._production_metrics.completed_stages,
            "failed_stages": self._production_metrics.failed_stages,
            "quality_passed": self._production_metrics.quality_passed,
            "duration_minutes": self._production_metrics.duration_minutes,
        }
        return base
