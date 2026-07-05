"""Deterministic image production pipeline.

Cada stage avança a pipeline por uma state machine.
Sem AI, sem LLM — rule-based.
"""

from __future__ import annotations

from enum import StrEnum
from typing import Any

from core.departments.base.pipeline import ProductionPipeline, StageResult
from core.departments.image.models import CanvasSpec, ExportProfile, ImageTask


class PipelineStage(StrEnum):
    """Stages of the image production pipeline."""
    CREATED = "created"
    ANALYZING = "analyzing"
    VALIDATING = "validating"
    COMPOSING = "composing"
    EDITING = "editing"
    VARIATION_GENERATION = "variation_generation"
    EXPORTING = "exporting"
    DELIVERING = "delivering"
    COMPLETED = "completed"
    FAILED = "failed"


class ImageProductionPipeline(ProductionPipeline):
    """Deterministic image production pipeline.

    Usage::

        pipeline = ImageProductionPipeline(task)
        while pipeline.stage not in ("completed", "failed"):
            result = pipeline.advance()
    """

    def __init__(self, task: ImageTask) -> None:
        super().__init__()
        self._task = task
        self._stage: str = PipelineStage.CREATED.value
        self._export_output: dict[str, Any] = {}

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    @property
    def stage(self) -> str:
        return self._stage

    @property
    def task(self) -> ImageTask:
        return self._task

    @property
    def progress(self) -> float:
        stages = list(PipelineStage)
        try:
            idx = stages.index(PipelineStage(self._stage))
            return round((idx / (len(stages) - 1)) * 100, 1)
        except (ValueError, KeyError):
            return 0.0

    def advance(self) -> StageResult:
        handlers = {
            PipelineStage.CREATED: self._stage_created,
            PipelineStage.ANALYZING: self._stage_analyzing,
            PipelineStage.VALIDATING: self._stage_validating,
            PipelineStage.COMPOSING: self._stage_composing,
            PipelineStage.EDITING: self._stage_editing,
            PipelineStage.VARIATION_GENERATION: self._stage_variation_generation,
            PipelineStage.EXPORTING: self._stage_exporting,
            PipelineStage.DELIVERING: self._stage_delivering,
        }

        try:
            current = PipelineStage(self._stage)
        except (ValueError, KeyError):
            self._stages_log.append(StageResult(
                stage=self._stage, success=False, error=f"Unknown stage: {self._stage}",
            ))
            self._stage = PipelineStage.FAILED.value
            return self._stages_log[-1]

        handler = handlers.get(current)
        if handler is None:
            self._stages_log.append(StageResult(
                stage=self._stage, success=False, error=f"No handler for: {self._stage}",
            ))
            self._stage = PipelineStage.FAILED.value
            return self._stages_log[-1]

        result = handler()
        self._stages_log.append(result)
        if result.next_stage:
            self._stage = result.next_stage
        elif result.success:
            self._stage = self._next_stage(current).value
        else:
            self._stage = PipelineStage.FAILED.value

        return result

    def reset(self) -> None:
        super().reset()
        self._stage = PipelineStage.CREATED.value
        self._export_output = {}

    # ------------------------------------------------------------------
    # Stage handlers
    # ------------------------------------------------------------------

    def _stage_created(self) -> StageResult:
        return StageResult(
            stage=PipelineStage.CREATED.value,
            success=True,
            summary=f"Task '{self._task.title}' created",
            output={"task_id": str(self._task.task_id), "image_type": self._task.image_type},
            next_stage=PipelineStage.ANALYZING.value,
        )

    def _stage_analyzing(self) -> StageResult:
        it = self._task.image_type
        valid_types = ("thumbnail", "banner", "cover", "social_media",
                       "visual_asset", "overlay", "composition")
        if it not in valid_types:
            return StageResult(
                stage=PipelineStage.ANALYZING.value,
                success=False,
                error=f"Unsupported image type: '{it}'. Must be one of {valid_types}",
            )

        canvas = self._task.canvas or CanvasSpec()
        analysis = {
            "image_type": it,
            "canvas_width": canvas.width,
            "canvas_height": canvas.height,
            "canvas_orientation": canvas.orientation,
            "layers_count": len(self._task.layers),
            "text_overlays_count": len(self._task.text_overlays),
            "assets_count": len(self._task.assets),
            "variants_count": len(self._task.variants),
            "has_design_brief": self._task.design_brief is not None,
            "required_capabilities": list(self._task.requires_capabilities),
        }
        return StageResult(
            stage=PipelineStage.ANALYZING.value,
            success=True,
            summary=f"Analyzed: {it}, {canvas.width}x{canvas.height}, "
                    f"{analysis['layers_count']} layers, "
                    f"{analysis['text_overlays_count']} text overlays",
            output=analysis,
            next_stage=PipelineStage.VALIDATING.value,
        )

    def _stage_validating(self) -> StageResult:
        issues: list[str] = []
        if self._task.canvas.width <= 0 or self._task.canvas.height <= 0:
            issues.append("Canvas dimensions invalid (width or height <= 0)")
        for t in self._task.text_overlays:
            if not t.text and t.opacity > 0:
                issues.append(f"Text overlay {t.overlay_id} has no text but is visible")
        for lyr in self._task.layers:
            if lyr.type == "image" and not lyr.source:
                issues.append(f"Layer '{lyr.name}' is type 'image' but has no source")
        if not self._task.title:
            issues.append("Task has no title")

        return StageResult(
            stage=PipelineStage.VALIDATING.value,
            success=len(issues) == 0,
            summary=f"Validated: {len(issues)} issues" if issues else "All assets valid",
            output={"issues": issues, "layers_checked": len(self._task.layers)},
            next_stage=PipelineStage.COMPOSING.value if len(issues) == 0 else None,
            error="; ".join(issues) if issues else "",
        )

    def _stage_composing(self) -> StageResult:
        layers = self._task.layers
        visible_layers = [l for l in layers if l.visible]
        total_layers = len(layers)
        total_images = sum(1 for l in layers if l.type == "image")
        total_shapes = sum(1 for l in layers if l.type == "shape")

        return StageResult(
            stage=PipelineStage.COMPOSING.value,
            success=True,
            summary=f"Composed: {total_layers} layers "
                    f"({total_images} images, {total_shapes} shapes, "
                    f"{len(visible_layers)} visible)",
            output={
                "layers_composed": total_layers,
                "visible_layers": len(visible_layers),
                "image_layers": total_images,
                "shape_layers": total_shapes,
            },
            next_stage=PipelineStage.EDITING.value,
        )

    def _stage_editing(self) -> StageResult:
        overlays = self._task.text_overlays
        total_overlays = len(overlays)
        total_chars = sum(len(t.text) for t in overlays if t.text)
        used_fonts = set(t.font_family for t in overlays if t.font_family)

        return StageResult(
            stage=PipelineStage.EDITING.value,
            success=True,
            summary=f"Edited: {total_overlays} text overlays, "
                    f"{total_chars} chars, {len(used_fonts)} font(s)",
            output={
                "text_overlays_edited": total_overlays,
                "total_characters": total_chars,
                "fonts_used": list(used_fonts),
            },
            next_stage=PipelineStage.VARIATION_GENERATION.value,
        )

    def _stage_variation_generation(self) -> StageResult:
        variants = self._task.variants
        total_variants = len(variants)
        variant_summary = [f"{v.name} ({v.width}x{v.height})" for v in variants]

        return StageResult(
            stage=PipelineStage.VARIATION_GENERATION.value,
            success=True,
            summary=f"Variations: {total_variants} variant(s): "
                    f"{', '.join(variant_summary) if variant_summary else 'none'}",
            output={
                "variants_generated": total_variants,
                "variants": [{"name": v.name, "width": v.width,
                              "height": v.height, "format": v.format}
                             for v in variants],
            },
            next_stage=PipelineStage.EXPORTING.value,
        )

    def _stage_exporting(self) -> StageResult:
        export = self._task.export_profile or ExportProfile()
        self._export_output = {
            "output_format": export.format,
            "output_quality": export.quality,
            "output_color_space": export.color_space,
            "optimize_for_web": export.optimize_for_web,
            "canvas_width": self._task.canvas.width,
            "canvas_height": self._task.canvas.height,
            "estimate_size_kb": _estimate_image_size(
                export.format, self._task.canvas.width,
                self._task.canvas.height, export.quality,
            ),
            "variants_count": len(self._task.variants),
            "variants": [{"name": v.name, "width": v.width,
                          "height": v.height, "format": v.format}
                         for v in self._task.variants],
        }
        return StageResult(
            stage=PipelineStage.EXPORTING.value,
            success=True,
            summary=f"Exported: {self._export_output['output_format']} @ "
                    f"{self._export_output['output_quality']}%, "
                    f"~{self._export_output['estimate_size_kb']}KB, "
                    f"{self._export_output['variants_count']} variant(s)",
            output=dict(self._export_output),
            next_stage=PipelineStage.DELIVERING.value,
        )

    def _stage_delivering(self) -> StageResult:
        delivery = {
            "task_id": str(self._task.task_id),
            "title": self._task.title,
            "image_type": self._task.image_type,
            "canvas": {
                "width": self._task.canvas.width,
                "height": self._task.canvas.height,
                "orientation": self._task.canvas.orientation,
            },
            "export": dict(self._export_output),
            "layers_count": len(self._task.layers),
            "text_overlays_count": len(self._task.text_overlays),
            "assets_count": len(self._task.assets),
            "variants_count": len(self._task.variants),
        }
        return StageResult(
            stage=PipelineStage.DELIVERING.value,
            success=True,
            summary=f"Delivered: '{self._task.title}' ({self._task.image_type}, "
                    f"{self._task.canvas.width}x{self._task.canvas.height})",
            output=delivery,
            next_stage=PipelineStage.COMPLETED.value,
        )

    @staticmethod
    def _next_stage(current: PipelineStage) -> PipelineStage:
        stages = list(PipelineStage)
        idx = stages.index(current)
        if idx + 1 < len(stages):
            return stages[idx + 1]
        return PipelineStage.COMPLETED


# ==================================================================
# Module-level helpers
# ==================================================================


def _estimate_image_size(fmt: str, width: int, height: int, quality: int) -> int:
    """Estimate file size in KB based on format, dimensions, and quality."""
    base = width * height * 3  # RGB bytes
    if fmt in ("jpg", "jpeg"):
        compression = quality / 100.0
        return max(1, round(base * 0.3 * compression / 1024))
    elif fmt == "png":
        return max(1, round(base * 0.5 / 1024))
    elif fmt == "webp":
        compression = quality / 100.0
        return max(1, round(base * 0.25 * compression / 1024))
    else:
        return max(1, round(base / 1024))
