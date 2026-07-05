"""ImageDesignerEmployee — ProductionEmployee especializado em imagem.

Herda ProductionEmployee (→ SpecialistEmployee) sem duplicar.
Todo comportamento genérico está em core/departments/base/.
Aqui: apenas lógica específica de imagem.
"""

from __future__ import annotations

import time
import zlib
from dataclasses import dataclass, field
from pathlib import Path
from struct import pack
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
from core.departments.image.models import (
    CanvasSpec,
    ExportProfile,
    ImageTask,
    ImageVariant,
)
from core.departments.image.pipeline import ImageProductionPipeline, PipelineStage
from core.events.bus import EventBus
from core.runtime import CompanyRuntime as CoreCompanyRuntime
from core.tools.capabilities import Capability
from core.tools.registry import ToolRegistry
from core.tools.runtime import ToolRuntime


@dataclass(frozen=True, slots=True)
class ImageCapability:
    """Domain-specific image capability metadata.
    Complementar a EmployeeSkill — não substitui.
    """
    name: str
    proficiency: float = 0.5
    enabled: bool = True


@dataclass(frozen=True, slots=True)
class ProductionMetrics:
    """Metrics accumulated across an image production run.
    Inclui campos genéricos + específicos de imagem.
    """
    total_stages: int = 0
    completed_stages: int = 0
    failed_stages: int = 0
    layers_composed: int = 0
    text_overlays_edited: int = 0
    variants_generated: int = 0
    export_format: str = ""
    estimate_size_kb: int = 0
    quality_passed: bool = False
    quality_corrections: tuple[str, ...] = field(default_factory=tuple)
    duration_minutes: float = 0.0


class ImageDesignerEmployee(ProductionEmployee):
    """Specialist employee for image production.

    Aceita apenas tarefas compatíveis com imagem.
    Utiliza pipeline de produção de imagem (8 stages).
    Integra QualityRuntime para validação pós-export.
    """

    _DEPARTMENT_KEYWORD = "image"

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
        self._image_capabilities: dict[str, ImageCapability] = {
            "thumbnail": ImageCapability(name="thumbnail", proficiency=0.95),
            "banner": ImageCapability(name="banner", proficiency=0.9),
            "cover": ImageCapability(name="cover", proficiency=0.85),
            "social_media": ImageCapability(name="social_media", proficiency=0.9),
            "visual_asset": ImageCapability(name="visual_asset", proficiency=0.8),
            "overlay": ImageCapability(name="overlay", proficiency=0.85),
            "composition": ImageCapability(name="composition", proficiency=0.8),
            "image_editing": ImageCapability(name="image_editing", proficiency=0.9),
            "creative_variation": ImageCapability(name="creative_variation", proficiency=0.75),
            "export_optimization": ImageCapability(name="export_optimization", proficiency=0.85),
        }
        self._current_image_task: ImageTask | None = None

    # ------------------------------------------------------------------
    # Properties
    # ------------------------------------------------------------------

    @property
    def image_capabilities(self) -> dict[str, ImageCapability]:
        return dict(self._image_capabilities)

    # ------------------------------------------------------------------
    # Task handling — image-specific
    # ------------------------------------------------------------------

    def receive_task(self, task: ReceivedTask) -> TaskDecision:
        if "image" not in task.department.lower():
            return super().receive_task(task)

        if self._workload >= self._max_workload:
            return super().receive_task(task)

        self._tasks[task.task_id] = task
        self._current_task_id = task.task_id
        self._workload += 1
        self._status = EmployeeStatus.ANALYZING

        ctx = task.context

        export_profile = ctx.get("export_profile")
        if export_profile is not None and not isinstance(export_profile, ExportProfile):
            export_profile = ExportProfile(
                format=export_profile.get("format", "png"),
                quality=export_profile.get("quality", 95),
                color_space=export_profile.get("color_space", "sRGB"),
                icc_profile=export_profile.get("icc_profile", ""),
                optimize_for_web=export_profile.get("optimize_for_web", True),
            )
        elif export_profile is None:
            export_profile = ExportProfile()

        canvas_data = ctx.get("canvas")
        if canvas_data is not None and not isinstance(canvas_data, CanvasSpec):
            canvas = CanvasSpec(
                width=canvas_data.get("width", 1920),
                height=canvas_data.get("height", 1080),
                dpi=canvas_data.get("dpi", 72),
                orientation=canvas_data.get("orientation", "landscape"),
                background_color=canvas_data.get("background_color", "#FFFFFF"),
                bleed_mm=canvas_data.get("bleed_mm", 0.0),
            )
        elif isinstance(canvas_data, CanvasSpec):
            canvas = canvas_data
        else:
            canvas = CanvasSpec()

        variants_raw = ctx.get("variants", ())
        variants: tuple[ImageVariant, ...] = tuple(
            v if isinstance(v, ImageVariant) else ImageVariant(
                name=v.get("name", "variant"),
                width=v.get("width", canvas.width),
                height=v.get("height", canvas.height),
                format=v.get("format", export_profile.format),
                quality=v.get("quality", export_profile.quality),
                crop=v.get("crop", "center"),
            )
            for v in variants_raw
        )

        layers = ctx.get("layers", ())
        text_overlays = ctx.get("text_overlays", ())
        assets = ctx.get("assets", ())

        self._current_image_task = ImageTask(
            task_id=task.task_id,
            title=task.title,
            image_type=ctx.get("image_type", "thumbnail"),
            canvas=canvas,
            layers=layers,
            text_overlays=text_overlays,
            assets=assets,
            variants=variants,
            export_profile=export_profile,
            metadata=dict(ctx),
        )
        self._pipeline = ImageProductionPipeline(self._current_image_task)

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
        if "image" not in task.department.lower():
            return f"Department '{task.department}' is not image"
        if self._workload >= self._max_workload:
            return "Workload limit reached (max 3)"
        return None

    # ------------------------------------------------------------------
    # Pipeline
    # ------------------------------------------------------------------

    def _build_pipeline(self, task: ReceivedTask) -> ProductionPipeline:
        return ImageProductionPipeline(self._current_image_task)

    def _estimate_duration(self, ctx: dict[str, Any]) -> int:
        image_type = ctx.get("image_type", "thumbnail")
        type_factor = {
            "thumbnail": 1.0, "banner": 2.0, "cover": 2.5,
            "social_media": 1.5, "visual_asset": 3.0,
            "overlay": 1.0, "composition": 3.5,
        }.get(image_type, 1.0)
        canvas = ctx.get("canvas", {})
        w = canvas.get("width", 1920) if isinstance(canvas, dict) else 1920
        h = canvas.get("height", 1080) if isinstance(canvas, dict) else 1080
        base = max(1, (w * h) // (1920 * 1080))
        return max(1, round(base * type_factor))

    def _get_production_type(self) -> str:
        if self._current_image_task:
            return self._current_image_task.image_type
        return ""

    # ------------------------------------------------------------------
    # Output building — image-specific
    # ------------------------------------------------------------------

    def _build_output_from_stages(
        self, final_output: dict[str, Any], summary_parts: list[str],
    ) -> None:
        for slog in self._pipeline.stages_log:
            if slog.stage == PipelineStage.DELIVERING.value:
                final_output.update(slog.output)
                summary_parts.append(slog.summary)
            if slog.stage == PipelineStage.EXPORTING.value:
                final_output["export"] = slog.output
            if slog.stage == PipelineStage.EDITING.value:
                final_output.update({k: v for k, v in slog.output.items()
                                     if k != "fonts_used"})
                if slog.output.get("fonts_used"):
                    final_output["fonts_used"] = slog.output["fonts_used"]
            if slog.stage == PipelineStage.COMPOSING.value:
                final_output.update({k: v for k, v in slog.output.items()})
            if slog.stage == PipelineStage.VARIATION_GENERATION.value:
                final_output.update({k: v for k, v in slog.output.items()
                                     if k != "variants"})

        asset_info = self._try_write_image_asset(final_output)
        if asset_info:
            final_output["asset_file_path"] = asset_info["file_path"]
            export_output = dict(final_output.get("export", {}))
            export_output.update(asset_info)
            final_output["export"] = export_output

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
            layers_composed=final_output.get("layers_composed", 0),
            text_overlays_edited=final_output.get("text_overlays_edited", 0),
            variants_generated=final_output.get("variants_count", 0),
            export_format=final_output.get("export", {}).get("output_format", ""),
            estimate_size_kb=final_output.get("export", {}).get("estimate_size_kb", 0),
            quality_passed=final_output.get("quality_passed", True),
            quality_corrections=tuple(final_output.get("quality_issues", [])),
            duration_minutes=round(duration, 2),
        )

    def _build_summary(self, success: bool, summary_parts: list[str]) -> str:
        if summary_parts:
            return " | ".join(summary_parts)
        return "Image production completed" if success else "Image production failed"

    # ------------------------------------------------------------------
    # Quality — adds image-specific fields
    # ------------------------------------------------------------------

    def _run_quality_check(self, output: dict[str, Any]) -> tuple[bool, list[str]]:
        if self._quality_runtime is None:
            return True, []

        exec_id = self._current_task_id or UUID(int=0)
        report = self._quality_runtime.validate(exec_id, {
            "success": output.get("error", "") == "",
            "error": output.get("error", ""),
            "output_format": output.get("export", {}).get("output_format", ""),
            "canvas_width": output.get("canvas", {}).get("width", 0),
            "canvas_height": output.get("canvas", {}).get("height", 0),
        })

        if report.passed:
            return True, []
        return False, self._quality_runtime.generate_correction(report)

    # ------------------------------------------------------------------
    # Capability analysis — image-specific
    # ------------------------------------------------------------------

    def analyze_capability_needs(self) -> tuple[Capability, ...]:
        needed: list[Capability] = [Capability.IMAGE_GENERATION]

        if self._current_image_task and self._current_image_task.layers:
            needed.append(Capability.IMAGE_EDITING)
        if self._current_image_task and self._current_image_task.variants:
            needed.append(Capability.STORAGE)

        return tuple(needed)

    # ------------------------------------------------------------------
    # Optional local asset export
    # ------------------------------------------------------------------

    def _try_write_image_asset(self, final_output: dict[str, Any]) -> dict[str, Any]:
        if self._current_image_task is None:
            return {}

        metadata = self._current_image_task.metadata
        output_dir_raw = metadata.get("output_dir") or metadata.get("image_output_dir")
        write_file = bool(metadata.get("write_file") or output_dir_raw)
        if not write_file:
            return {}

        export = final_output.get("export", {})
        output_format = str(export.get("output_format", "png")).lower().lstrip(".")
        if output_format != "png":
            output_format = "png"

        output_dir = Path(str(output_dir_raw or "output/image"))
        output_dir.mkdir(parents=True, exist_ok=True)
        output_path = output_dir / f"{self._current_image_task.task_id}.{output_format}"
        canvas = self._current_image_task.canvas
        _write_solid_png(
            output_path=output_path,
            width=canvas.width,
            height=canvas.height,
            color=_parse_hex_color(canvas.background_color),
        )
        return {
            "file_path": str(output_path.resolve()),
            "file_size_bytes": output_path.stat().st_size,
            "physical_asset": True,
            "output_format": "png",
        }

    # ------------------------------------------------------------------
    # State
    # ------------------------------------------------------------------

    def state(self) -> dict[str, Any]:
        base = super().state()
        base["image_capabilities"] = {
            k: {"name": v.name, "proficiency": v.proficiency, "enabled": v.enabled}
            for k, v in self._image_capabilities.items()
        }
        base["current_image_task"] = (
            {
                "title": self._current_image_task.title,
                "image_type": self._current_image_task.image_type,
                "canvas_width": self._current_image_task.canvas.width,
                "canvas_height": self._current_image_task.canvas.height,
            }
            if self._current_image_task else None
        )
        base["production_metrics"]["layers_composed"] = self._production_metrics.layers_composed
        base["production_metrics"]["text_overlays_edited"] = self._production_metrics.text_overlays_edited
        base["production_metrics"]["variants_generated"] = self._production_metrics.variants_generated
        base["production_metrics"]["export_format"] = self._production_metrics.export_format
        return base


def _parse_hex_color(value: str) -> tuple[int, int, int]:
    color = value.strip().lstrip("#")
    if len(color) == 3:
        color = "".join(ch * 2 for ch in color)
    if len(color) != 6:
        return (255, 255, 255)
    try:
        return (
            int(color[0:2], 16),
            int(color[2:4], 16),
            int(color[4:6], 16),
        )
    except ValueError:
        return (255, 255, 255)


def _write_solid_png(
    output_path: Path,
    width: int,
    height: int,
    color: tuple[int, int, int],
) -> None:
    width = max(1, int(width))
    height = max(1, int(height))
    pixel = bytes(color)
    raw_rows = bytearray()
    row = pixel * width
    for _ in range(height):
        raw_rows.append(0)
        raw_rows.extend(row)

    def chunk(chunk_type: bytes, data: bytes) -> bytes:
        return (
            pack(">I", len(data))
            + chunk_type
            + data
            + pack(">I", zlib.crc32(chunk_type + data) & 0xFFFFFFFF)
        )

    png = (
        b"\x89PNG\r\n\x1a\n"
        + chunk(b"IHDR", pack(">IIBBBBB", width, height, 8, 2, 0, 0, 0))
        + chunk(b"IDAT", zlib.compress(bytes(raw_rows), level=9))
        + chunk(b"IEND", b"")
    )
    output_path.write_bytes(png)
