"""StrategyIntelligenceEmployee specialized in learning from content sources."""

from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Any
from uuid import UUID

from core.company.department_manager import DepartmentManager
from core.company.quality import QualityRuntime
from core.company.specialist_employee import (
    EmployeeSkill,
    EmployeeStatus,
    ReceivedTask,
    TaskAccepted,
    TaskDecision,
)
from core.departments.base.employee import ProductionEmployee
from core.departments.base.pipeline import ProductionPipeline
from core.departments.strategy_intelligence.models import (
    StrategyIntelligenceMetrics,
    StrategyIntelligenceTask,
    StrategySource,
)
from core.departments.strategy_intelligence.pipeline import PipelineStage, StrategyIntelligencePipeline
from core.events.bus import EventBus
from core.runtime import CompanyRuntime as CoreCompanyRuntime
from core.tools.capabilities import Capability
from core.tools.registry import ToolRegistry
from core.tools.runtime import ToolRuntime


@dataclass(frozen=True, slots=True)
class StrategyIntelligenceCapability:
    """Domain-specific strategy intelligence capability metadata."""

    name: str
    proficiency: float = 0.5
    enabled: bool = True


class StrategyIntelligenceEmployee(ProductionEmployee):
    """Specialist employee that extracts reusable strategies from videos and notes."""

    _DEPARTMENT_KEYWORD = "strategy_intelligence"

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
            quality_runtime=quality_runtime,
        )
        self._strategy_capabilities: dict[str, StrategyIntelligenceCapability] = {
            "source_triage": StrategyIntelligenceCapability("source_triage", 0.88),
            "tool_detection": StrategyIntelligenceCapability("tool_detection", 0.84),
            "metric_extraction": StrategyIntelligenceCapability("metric_extraction", 0.86),
            "strategy_patterning": StrategyIntelligenceCapability("strategy_patterning", 0.9),
            "copyright_safe_learning": StrategyIntelligenceCapability("copyright_safe_learning", 0.92),
            "department_handoff": StrategyIntelligenceCapability("department_handoff", 0.85),
        }
        self._current_strategy_task: StrategyIntelligenceTask | None = None

    @property
    def strategy_capabilities(self) -> dict[str, StrategyIntelligenceCapability]:
        return dict(self._strategy_capabilities)

    def receive_task(self, task: ReceivedTask) -> TaskDecision:
        if not _is_strategy_department(task.department):
            return super().receive_task(task)
        if self._workload >= self._max_workload:
            return super().receive_task(task)

        self._tasks[task.task_id] = task
        self._current_task_id = task.task_id
        self._workload += 1
        self._status = EmployeeStatus.ANALYZING

        self._current_strategy_task = _coerce_task(task)
        self._pipeline = StrategyIntelligencePipeline(self._current_strategy_task)

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
        if not _is_strategy_department(task.department):
            return f"Department '{task.department}' is not strategy_intelligence"
        if self._workload >= self._max_workload:
            return "Workload limit reached (max 3)"
        return None

    def _build_pipeline(self, task: ReceivedTask) -> ProductionPipeline:
        return StrategyIntelligencePipeline(self._current_strategy_task or _coerce_task(task))

    def _estimate_duration(self, ctx: dict[str, Any]) -> int:
        sources = _as_iterable(ctx.get("sources", ()))
        return max(5, 4 + len(sources) * 2)

    def _get_production_type(self) -> str:
        return "strategy_intelligence"

    def _build_output_from_stages(
        self,
        final_output: dict[str, Any],
        summary_parts: list[str],
    ) -> None:
        for slog in self._pipeline.stages_log:
            if slog.stage == PipelineStage.DELIVERING.value:
                final_output.update(slog.output)
                summary_parts.append(slog.summary)
            elif slog.stage in (
                PipelineStage.VALIDATING_SOURCES.value,
                PipelineStage.DETECTING_TOOLS.value,
                PipelineStage.DETECTING_METRICS.value,
                PipelineStage.EXTRACTING_PATTERNS.value,
                PipelineStage.BUILDING_GUARDRAILS.value,
                PipelineStage.HANDOFF_PLANNING.value,
            ):
                final_output.update(slog.output)

    def _build_metrics(
        self,
        stages_completed: int,
        stages_failed: int,
        final_output: dict[str, Any],
        duration: float,
    ) -> StrategyIntelligenceMetrics:
        patterns = final_output.get("patterns", [])
        top_pattern = patterns[0].get("pattern_id", "") if patterns and isinstance(patterns[0], dict) else ""
        return StrategyIntelligenceMetrics(
            total_stages=stages_completed + stages_failed,
            completed_stages=stages_completed,
            failed_stages=stages_failed,
            sources_analyzed=final_output.get("sources_analyzed", 0),
            tools_detected=len(final_output.get("tools_detected", [])),
            metrics_detected=len(final_output.get("metrics_detected", [])),
            patterns_extracted=len(patterns),
            warnings_count=len(final_output.get("warnings", [])),
            top_pattern=top_pattern,
            quality_passed=final_output.get("quality_passed", True),
            quality_corrections=tuple(final_output.get("quality_issues", [])),
            duration_minutes=round(duration, 2),
        )

    def _build_summary(self, success: bool, summary_parts: list[str]) -> str:
        if summary_parts:
            return " | ".join(summary_parts)
        return "Strategy intelligence completed" if success else "Strategy intelligence failed"

    def analyze_capability_needs(self) -> tuple[Capability, ...]:
        return (
            Capability.TRANSCRIPTION,
            Capability.TEXT_GENERATION,
            Capability.WEB_SEARCH,
            Capability.DOCUMENT_GENERATION,
            Capability.STORAGE,
        )

    def state(self) -> dict[str, Any]:
        base = super().state()
        base["strategy_capabilities"] = {
            k: {"name": v.name, "proficiency": v.proficiency, "enabled": v.enabled}
            for k, v in self._strategy_capabilities.items()
        }
        task = self._current_strategy_task
        base["current_strategy_task"] = (
            {
                "title": task.title,
                "sources": len(task.sources),
                "focus_areas": list(task.focus_areas),
                "max_patterns": task.max_patterns,
            }
            if task is not None else None
        )
        metrics = base["production_metrics"]
        metrics["sources_analyzed"] = getattr(self._production_metrics, "sources_analyzed", 0)
        metrics["patterns_extracted"] = getattr(self._production_metrics, "patterns_extracted", 0)
        metrics["top_pattern"] = getattr(self._production_metrics, "top_pattern", "")
        return base


def _is_strategy_department(department: str) -> bool:
    lowered = department.lower()
    markers = ("strategy_intelligence", "strategy intelligence", "estrategia", "strategy", "learning")
    return any(marker in lowered for marker in markers)


def _coerce_task(task: ReceivedTask) -> StrategyIntelligenceTask:
    ctx = task.context
    return StrategyIntelligenceTask(
        task_id=task.task_id,
        title=task.title,
        objective=ctx.get("objective", "Extract reusable content and commerce strategy."),
        sources=_coerce_sources(ctx.get("sources", ())),
        focus_areas=tuple(ctx.get("focus_areas", ())),
        max_patterns=int(ctx.get("max_patterns", 8) or 8),
        metadata=dict(ctx.get("metadata", {})),
    )


def _coerce_sources(raw: Any) -> tuple[StrategySource, ...]:
    return tuple(
        item if isinstance(item, StrategySource) else _coerce_source(item)
        for item in _as_iterable(raw)
        if isinstance(item, (StrategySource, dict))
    )


def _coerce_source(data: dict[str, Any]) -> StrategySource:
    return StrategySource(
        title=data.get("title", ""),
        creator=data.get("creator", ""),
        source_url=data.get("source_url", data.get("url", "")),
        source_type=data.get("source_type", "transcript"),
        transcript_text=data.get("transcript_text", data.get("text", "")),
        tags=tuple(data.get("tags", ())),
        metadata=dict(data.get("metadata", {})),
    )


def _as_iterable(raw: Any) -> tuple[Any, ...]:
    if raw is None:
        return ()
    if isinstance(raw, tuple):
        return raw
    if isinstance(raw, list):
        return tuple(raw)
    return (raw,)
