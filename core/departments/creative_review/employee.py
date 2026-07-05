"""CreativeReviewEmployee specialized in image and thumbnail readiness."""

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
from core.departments.creative_review.models import (
    CreativeAsset,
    CreativeReviewBrief,
    CreativeReviewMetrics,
)
from core.departments.creative_review.pipeline import CreativeReviewPipeline, PipelineStage
from core.events.bus import EventBus
from core.runtime import CompanyRuntime as CoreCompanyRuntime
from core.tools.capabilities import Capability
from core.tools.registry import ToolRegistry
from core.tools.runtime import ToolRuntime


@dataclass(frozen=True, slots=True)
class CreativeReviewCapability:
    """Domain-specific creative review capability metadata."""

    name: str
    proficiency: float = 0.5
    enabled: bool = True


class CreativeReviewEmployee(ProductionEmployee):
    """Specialist employee that decides whether a creative asset is publishable."""

    _DEPARTMENT_KEYWORD = "creative_review"

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
        self._creative_review_capabilities: dict[str, CreativeReviewCapability] = {
            "image_readiness": CreativeReviewCapability("image_readiness", 0.9),
            "thumbnail_formula_review": CreativeReviewCapability("thumbnail_formula_review", 0.86),
            "watermark_risk_triage": CreativeReviewCapability("watermark_risk_triage", 0.84),
            "earnings_claim_review": CreativeReviewCapability("earnings_claim_review", 0.88),
            "handoff_to_image_team": CreativeReviewCapability("handoff_to_image_team", 0.82),
        }
        self._current_creative_review_brief: CreativeReviewBrief | None = None

    @property
    def creative_review_capabilities(self) -> dict[str, CreativeReviewCapability]:
        return dict(self._creative_review_capabilities)

    def receive_task(self, task: ReceivedTask) -> TaskDecision:
        if not _is_creative_review_department(task.department):
            return super().receive_task(task)
        if self._workload >= self._max_workload:
            return super().receive_task(task)

        self._tasks[task.task_id] = task
        self._current_task_id = task.task_id
        self._workload += 1
        self._status = EmployeeStatus.ANALYZING

        self._current_creative_review_brief = _coerce_brief(task)
        self._pipeline = CreativeReviewPipeline(self._current_creative_review_brief)

        self._publish(TaskAccepted(
            employee_id=self._employee_id,
            task_id=task.task_id,
            title=task.title,
            difficulty=0.42,
            estimated_time_minutes=self._estimate_duration(task.context),
            timestamp=time.time(),
        ))
        return TaskDecision.ACCEPTED

    def _check_reject(self, task: ReceivedTask) -> str | None:
        if not _is_creative_review_department(task.department):
            return f"Department '{task.department}' is not creative_review"
        if self._workload >= self._max_workload:
            return "Workload limit reached (max 3)"
        return None

    def _build_pipeline(self, task: ReceivedTask) -> ProductionPipeline:
        return CreativeReviewPipeline(self._current_creative_review_brief or _coerce_brief(task))

    def _estimate_duration(self, ctx: dict[str, Any]) -> int:
        assets = _as_iterable(ctx.get("assets", ()))
        return max(4, 3 + len(assets))

    def _get_production_type(self) -> str:
        return "creative_review"

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
                PipelineStage.COLLECTING_ASSETS.value,
                PipelineStage.SCORING_ASSETS.value,
                PipelineStage.DECIDING_ACTIONS.value,
                PipelineStage.HANDOFF_PLANNING.value,
            ):
                final_output.update(slog.output)

    def _build_metrics(
        self,
        stages_completed: int,
        stages_failed: int,
        final_output: dict[str, Any],
        duration: float,
    ) -> CreativeReviewMetrics:
        findings = final_output.get("findings", [])
        actions: dict[str, int] = {}
        for finding in findings:
            action = finding.get("recommended_action", "") if isinstance(finding, dict) else ""
            actions[action] = actions.get(action, 0) + 1
        top_action = max(actions.items(), key=lambda item: item[1])[0] if actions else ""
        return CreativeReviewMetrics(
            total_stages=stages_completed + stages_failed,
            completed_stages=stages_completed,
            failed_stages=stages_failed,
            assets_reviewed=final_output.get("total_assets", final_output.get("assets_reviewed", 0)),
            ready_count=final_output.get("ready_count", 0),
            improve_count=final_output.get("improve_count", 0),
            rebuild_count=final_output.get("rebuild_count", 0),
            human_review_count=final_output.get("human_review_count", 0),
            average_score=final_output.get("average_score", 0.0),
            top_action=top_action,
            quality_passed=final_output.get("quality_passed", True),
            quality_corrections=tuple(final_output.get("quality_issues", [])),
            duration_minutes=round(duration, 2),
        )

    def _build_summary(self, success: bool, summary_parts: list[str]) -> str:
        if summary_parts:
            return " | ".join(summary_parts)
        return "Creative review completed" if success else "Creative review failed"

    def analyze_capability_needs(self) -> tuple[Capability, ...]:
        return (
            Capability.IMAGE_EDITING,
            Capability.IMAGE_GENERATION,
            Capability.WEB_SEARCH,
            Capability.BROWSER_AUTOMATION,
            Capability.STORAGE,
        )

    def state(self) -> dict[str, Any]:
        base = super().state()
        base["creative_review_capabilities"] = {
            k: {"name": v.name, "proficiency": v.proficiency, "enabled": v.enabled}
            for k, v in self._creative_review_capabilities.items()
        }
        brief = self._current_creative_review_brief
        base["current_creative_review_brief"] = (
            {
                "title": brief.title,
                "assets": len(brief.assets),
                "target_platforms": list(brief.target_platforms),
                "ready_threshold": brief.ready_threshold,
            }
            if brief is not None else None
        )
        metrics = base["production_metrics"]
        metrics["assets_reviewed"] = getattr(self._production_metrics, "assets_reviewed", 0)
        metrics["ready_count"] = getattr(self._production_metrics, "ready_count", 0)
        metrics["rebuild_count"] = getattr(self._production_metrics, "rebuild_count", 0)
        metrics["top_action"] = getattr(self._production_metrics, "top_action", "")
        return base


def _is_creative_review_department(department: str) -> bool:
    lowered = department.lower()
    markers = ("creative_review", "creative review", "criativo", "creative", "thumbnail", "thumb", "image_review")
    return any(marker in lowered for marker in markers)


def _coerce_brief(task: ReceivedTask) -> CreativeReviewBrief:
    ctx = task.context
    return CreativeReviewBrief(
        task_id=task.task_id,
        title=task.title,
        objective=ctx.get("objective", "Decide whether creative assets are ready or need improvement."),
        assets=_coerce_assets(ctx.get("assets", ())),
        target_platforms=tuple(ctx.get("target_platforms", ())),
        ready_threshold=float(ctx.get("ready_threshold", 76.0) or 76.0),
        metadata=dict(ctx.get("metadata", {})),
    )


def _coerce_assets(raw: Any) -> tuple[CreativeAsset, ...]:
    return tuple(
        item if isinstance(item, CreativeAsset) else _coerce_asset(item)
        for item in _as_iterable(raw)
        if isinstance(item, (CreativeAsset, dict))
    )


def _coerce_asset(data: dict[str, Any]) -> CreativeAsset:
    return CreativeAsset(
        title=data.get("title", ""),
        asset_type=data.get("asset_type", "product_image"),
        product_name=data.get("product_name", ""),
        platform=data.get("platform", ""),
        image_url=data.get("image_url", ""),
        file_path=data.get("file_path", ""),
        source_url=data.get("source_url", ""),
        use_case=data.get("use_case", "affiliate_post"),
        visual_quality=float(data.get("visual_quality", 6.0) or 0.0),
        product_visibility=float(data.get("product_visibility", 6.0) or 0.0),
        resolution_score=float(data.get("resolution_score", 6.0) or 0.0),
        text_clutter=float(data.get("text_clutter", 3.0) or 0.0),
        watermark_risk=float(data.get("watermark_risk", 0.0) or 0.0),
        brand_safety=float(data.get("brand_safety", 8.0) or 0.0),
        face_emotion=float(data.get("face_emotion", 0.0) or 0.0),
        proof_element=float(data.get("proof_element", 0.0) or 0.0),
        risk_flags=tuple(data.get("risk_flags", ())),
        notes=tuple(data.get("notes", ())),
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
