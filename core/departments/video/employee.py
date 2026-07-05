"""VideoEditorEmployee — ProductionEmployee especializado em vídeo.

Herda ProductionEmployee (→ SpecialistEmployee) sem duplicar.
Todo comportamento genérico está em core/departments/base/.
Aqui: apenas lógica específica de vídeo.
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from pathlib import Path
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
from core.departments.base.models import ProductionMetrics as BaseProductionMetrics
from core.departments.base.pipeline import ProductionPipeline
from core.departments.video.models import RenderProfile, VideoTask
from core.departments.video.pipeline import PipelineStage, VideoProductionPipeline
from core.events.bus import EventBus
from core.runtime import CompanyRuntime as CoreCompanyRuntime
from core.tools.adapters.models import ToolRequest
from core.tools.capabilities import Capability
from core.tools.registry import ToolRegistry
from core.tools.runtime import ToolRuntime


@dataclass(frozen=True, slots=True)
class VideoCapability:
    """Domain-specific video capability metadata.
    Complementar a EmployeeSkill — não substitui.
    """
    name: str
    proficiency: float = 0.5
    enabled: bool = True


@dataclass(frozen=True, slots=True)
class ProductionMetrics:
    """Metrics accumulated across a video production run.
    Inclui campos genéricos + específicos de vídeo.
    """
    total_stages: int = 0
    completed_stages: int = 0
    failed_stages: int = 0
    assets_validated: int = 0
    segments_processed: int = 0
    effects_applied: tuple[str, ...] = field(default_factory=tuple)
    render_format: str = ""
    render_resolution: str = ""
    estimated_size_mb: int = 0
    quality_passed: bool = False
    quality_corrections: tuple[str, ...] = field(default_factory=tuple)
    duration_minutes: float = 0.0


class VideoEditorEmployee(ProductionEmployee):
    """Specialist employee for video production.

    Aceita apenas tarefas compatíveis com vídeo.
    Utiliza pipeline de produção de vídeo (8 stages).
    Integra QualityRuntime para validação pós-render.
    """

    _DEPARTMENT_KEYWORD = "video"

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
        self._video_capabilities: dict[str, VideoCapability] = {
            "horizontal": VideoCapability(name="horizontal", proficiency=0.9),
            "vertical": VideoCapability(name="vertical", proficiency=0.8),
            "shorts": VideoCapability(name="shorts", proficiency=0.85),
            "reels": VideoCapability(name="reels", proficiency=0.8),
            "tiktok": VideoCapability(name="tiktok", proficiency=0.75),
            "cortes": VideoCapability(name="cortes", proficiency=0.9),
            "legendas": VideoCapability(name="legendas", proficiency=0.7),
            "color_grading": VideoCapability(name="color_grading", proficiency=0.6),
            "motion_graphics": VideoCapability(name="motion_graphics", proficiency=0.5),
            "thumbnail_awareness": VideoCapability(name="thumbnail_awareness", proficiency=0.8),
            "codecs": VideoCapability(name="codecs", proficiency=0.7),
        }
        self._current_video_task: VideoTask | None = None

    # ------------------------------------------------------------------
    # Properties
    # ------------------------------------------------------------------

    @property
    def video_capabilities(self) -> dict[str, VideoCapability]:
        return dict(self._video_capabilities)

    # ------------------------------------------------------------------
    # Task handling — video-specific
    # ------------------------------------------------------------------

    def receive_task(self, task: ReceivedTask) -> TaskDecision:
        # Department check via base
        if "video" not in task.department.lower():
            return super().receive_task(task)

        if self._workload >= self._max_workload:
            return super().receive_task(task)

        self._tasks[task.task_id] = task
        self._current_task_id = task.task_id
        self._workload += 1
        self._status = EmployeeStatus.ANALYZING

        ctx = task.context

        render_profile = ctx.get("render_profile")
        if render_profile is not None and not isinstance(render_profile, RenderProfile):
            render_profile = RenderProfile(
                format=render_profile.get("format", "mp4"),
                codec=render_profile.get("codec", "h264"),
                resolution=tuple(render_profile.get("resolution", (1920, 1080))),
                fps=render_profile.get("fps", 30),
                bitrate=render_profile.get("bitrate", "8M"),
                quality=render_profile.get("quality", "standard"),
            )
        elif render_profile is None:
            render_profile = RenderProfile()

        timeline = ctx.get("timeline", ())
        assets = ctx.get("assets", ())
        subtitles = ctx.get("subtitles", ())

        self._current_video_task = VideoTask(
            task_id=task.task_id,
            title=task.title,
            video_type=ctx.get("video_type", "horizontal"),
            duration_seconds=ctx.get("duration_seconds", 60),
            assets=assets,
            subtitles=subtitles,
            timeline=timeline,
            render_profile=render_profile,
            metadata=dict(ctx),
        )
        self._pipeline = VideoProductionPipeline(self._current_video_task)

        self._publish(TaskAccepted(
            employee_id=self._employee_id,
            task_id=task.task_id,
            title=task.title,
            difficulty=0.5,
            estimated_time_minutes=self._estimate_duration(ctx),
            timestamp=time.time(),
        ))
        return TaskDecision.ACCEPTED

    def _check_reject(self, task: ReceivedTask) -> str | None:
        if "video" not in task.department.lower():
            return f"Department '{task.department}' is not video"
        if self._workload >= self._max_workload:
            return "Workload limit reached (max 3)"
        return None

    # ------------------------------------------------------------------
    # Pipeline
    # ------------------------------------------------------------------

    def _build_pipeline(self, task: ReceivedTask) -> ProductionPipeline:
        return VideoProductionPipeline(self._current_video_task)

    def _estimate_duration(self, ctx: dict[str, Any]) -> int:
        dur = ctx.get("duration_seconds", 30)
        base = max(1, dur // 30)
        video_type = ctx.get("video_type", "horizontal")
        type_factor = {
            "horizontal": 1.0, "vertical": 1.2, "square": 1.0,
            "cinematic": 2.0, "tutorial": 2.5,
        }.get(video_type, 1.0)
        return max(1, round(base * type_factor))

    def _get_production_type(self) -> str:
        if self._current_video_task:
            return self._current_video_task.video_type
        return ""

    # ------------------------------------------------------------------
    # Output building — video-specific
    # ------------------------------------------------------------------

    def _build_output_from_stages(
        self, final_output: dict[str, Any], summary_parts: list[str],
    ) -> None:
        for slog in self._pipeline.stages_log:
            if slog.stage == PipelineStage.DELIVERING.value:
                final_output.update(slog.output)
                summary_parts.append(slog.summary)
            if slog.stage == PipelineStage.RENDERING.value:
                final_output["render"] = slog.output
            if slog.stage == PipelineStage.EXECUTING.value:
                final_output.update({k: v for k, v in slog.output.items()
                                     if k != "effects_applied"})
                if slog.output.get("effects_applied"):
                    final_output["effects_applied"] = slog.output["effects_applied"]

        render_execution = self._try_render_video(final_output.get("render", {}))
        if render_execution:
            render_output = dict(final_output.get("render", {}))
            render_output["render_execution"] = render_execution
            if render_execution.get("success"):
                adapter_output = render_execution.get("output", {})
                if isinstance(adapter_output, dict):
                    for key in (
                        "file_path",
                        "renderer",
                        "mode",
                        "file_size_bytes",
                        "inputs",
                        "probe",
                    ):
                        if key in adapter_output:
                            render_output[key] = adapter_output[key]
            final_output["render"] = render_output

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
            assets_validated=len(self._current_video_task.assets) if self._current_video_task else 0,
            segments_processed=final_output.get("segments_processed", 0),
            effects_applied=tuple(final_output.get("effects_applied", [])),
            render_format=final_output.get("render", {}).get("output_format", ""),
            render_resolution=final_output.get("render", {}).get("output_resolution", ""),
            estimated_size_mb=final_output.get("render", {}).get("estimated_size_mb", 0),
            quality_passed=final_output.get("quality_passed", True),
            quality_corrections=tuple(final_output.get("quality_issues", [])),
            duration_minutes=round(duration, 2),
        )

    def _build_summary(self, success: bool, summary_parts: list[str]) -> str:
        if summary_parts:
            return " | ".join(summary_parts)
        return "Video production completed" if success else "Video production failed"

    # ------------------------------------------------------------------
    # Optional tools — capability -> adapter
    # ------------------------------------------------------------------

    def _try_render_video(self, render_output: dict[str, Any]) -> dict[str, Any]:
        """Use a registered video-rendering tool when one is available."""
        if self._tool_registry is None or self._tool_runtime is None:
            return {}
        if self._current_video_task is None:
            return {}

        task_id = self._current_task_id or UUID(int=0)
        selected = self._tool_registry.resolve(
            Capability.VIDEO_RENDERING,
            self._employee_id,
            task_id=task_id,
        )
        tool_id = getattr(selected, "tool_id", None)
        if tool_id is None:
            return {
                "available": False,
                "capability": Capability.VIDEO_RENDERING.value,
                "reason": getattr(selected, "reason", "No video rendering tool available"),
            }

        request_params: dict[str, Any] = {
            "action": "render_short_video",
            "task_id": str(self._current_video_task.task_id),
            "duration_seconds": self._current_video_task.duration_seconds,
            "output_format": render_output.get("output_format", "mp4"),
            "output_resolution": render_output.get("output_resolution", "1080x1920"),
            "estimated_size_mb": render_output.get("estimated_size_mb", 0),
        }
        request_params.update(self._resolve_render_input_files())
        for source_key, target_key in (
            ("output_dir", "output_dir"),
            ("video_output_dir", "output_dir"),
            ("background_color", "background_color"),
            ("video_background_color", "background_color"),
        ):
            if source_key in self._current_video_task.metadata:
                request_params[target_key] = self._current_video_task.metadata[source_key]

        request = ToolRequest(
            tool_id=tool_id,
            capability=Capability.VIDEO_RENDERING.value,
            params=request_params,
            metadata={
                "video_task_id": str(self._current_video_task.task_id),
                "video_type": self._current_video_task.video_type,
            },
        )
        try:
            result = self._tool_runtime.execute_tool(tool_id, request)
        except Exception as exc:  # pragma: no cover - defensive around local tools
            return {
                "available": True,
                "tool_id": str(tool_id),
                "tool_name": getattr(selected, "tool_name", ""),
                "success": False,
                "summary": "",
                "output": {},
                "error": str(exc),
            }
        finally:
            self._tool_runtime.release_tool(tool_id, self._employee_id)

        return {
            "available": True,
            "tool_id": str(tool_id),
            "tool_name": getattr(selected, "tool_name", ""),
            "success": result.success,
            "summary": result.summary,
            "output": dict(result.output),
            "error": result.error,
        }

    def _resolve_render_input_files(self) -> dict[str, str]:
        if self._current_video_task is None:
            return {}

        resolved: dict[str, str] = {}
        for asset in self._current_video_task.assets:
            file_path = self._physical_asset_path(asset)
            if not file_path:
                continue
            if asset.type == "audio" and "audio_file_path" not in resolved:
                resolved["audio_file_path"] = file_path
            if asset.type == "image" and "image_file_path" not in resolved:
                resolved["image_file_path"] = file_path
        return resolved

    def _physical_asset_path(self, asset: Any) -> str:
        metadata = getattr(asset, "metadata", {}) or {}
        candidates = (
            metadata.get("file_path"),
            metadata.get("asset_file_path"),
            getattr(asset, "source", ""),
        )
        for raw in candidates:
            if not raw:
                continue
            value = str(raw)
            if "://" in value:
                continue
            path = Path(value).expanduser()
            if path.is_file():
                return str(path.resolve())
        return ""

    # ------------------------------------------------------------------
    # Quality — adds video-specific fields
    # ------------------------------------------------------------------

    def _run_quality_check(self, output: dict[str, Any]) -> tuple[bool, list[str]]:
        if self._quality_runtime is None:
            return True, []

        exec_id = self._current_task_id or UUID(int=0)
        report = self._quality_runtime.validate(exec_id, {
            "success": output.get("error", "") == "",
            "error": output.get("error", ""),
            "output_format": output.get("render", {}).get("output_format", ""),
            "output_resolution": output.get("render", {}).get("output_resolution", ""),
            "duration_seconds": output.get("duration_seconds", 0),
        })

        if report.passed:
            return True, []
        return False, self._quality_runtime.generate_correction(report)

    # ------------------------------------------------------------------
    # Capability analysis — video-specific
    # ------------------------------------------------------------------

    def analyze_capability_needs(self) -> tuple[Capability, ...]:
        needed: list[Capability] = [Capability.VIDEO_EDITING, Capability.VIDEO_RENDERING]

        if self._current_video_task and self._current_video_task.subtitles:
            needed.append(Capability.TRANSLATION)
        if self._current_video_task and any(
            a.type == "browser" for a in self._current_video_task.assets
        ):
            needed.append(Capability.BROWSER_AUTOMATION)
        if self._current_video_task and any(
            a.type == "image" for a in self._current_video_task.assets
        ):
            needed.append(Capability.IMAGE_GENERATION)

        return tuple(needed)

    # ------------------------------------------------------------------
    # State
    # ------------------------------------------------------------------

    def state(self) -> dict[str, Any]:
        base = super().state()
        base["video_capabilities"] = {
            k: {"name": v.name, "proficiency": v.proficiency, "enabled": v.enabled}
            for k, v in self._video_capabilities.items()
        }
        base["current_video_task"] = (
            {
                "title": self._current_video_task.title,
                "video_type": self._current_video_task.video_type,
                "duration_seconds": self._current_video_task.duration_seconds,
            }
            if self._current_video_task else None
        )
        base["production_metrics"]["assets_validated"] = self._production_metrics.assets_validated
        base["production_metrics"]["segments_processed"] = self._production_metrics.segments_processed
        base["production_metrics"]["render_format"] = self._production_metrics.render_format
        base["production_metrics"]["render_resolution"] = self._production_metrics.render_resolution
        return base
