"""Deterministic video production pipeline.

Cada stage avança a pipeline por uma state machine.
Sem AI, sem LLM — rule-based.
"""

from __future__ import annotations

from enum import StrEnum
from typing import Any

from core.departments.base.pipeline import ProductionPipeline, StageResult
from core.departments.video.models import (
    RenderProfile,
    SubtitleSegment,
    TimelineSegment,
    VideoAsset,
    VideoTask,
)


class PipelineStage(StrEnum):
    """Stages of the video production pipeline."""
    CREATED = "created"
    ANALYZING = "analyzing"
    VALIDATING = "validating"
    PLANNING = "planning"
    EXECUTING = "executing"
    RENDERING = "rendering"
    DELIVERING = "delivering"
    COMPLETED = "completed"
    FAILED = "failed"


class VideoProductionPipeline(ProductionPipeline):
    """Deterministic video production state machine.

    Usage::

        pipeline = VideoProductionPipeline(task)
        while pipeline.stage not in ("completed", "failed"):
            result = pipeline.advance()
    """

    def __init__(self, task: VideoTask) -> None:
        super().__init__()
        self._task = task
        self._stage: str = PipelineStage.CREATED.value
        self._current_segment_index: int = 0
        self._render_output: dict[str, Any] = {}

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    @property
    def stage(self) -> str:
        return self._stage

    @property
    def task(self) -> VideoTask:
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
            PipelineStage.PLANNING: self._stage_planning,
            PipelineStage.EXECUTING: self._stage_executing,
            PipelineStage.RENDERING: self._stage_rendering,
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
        self._current_segment_index = 0
        self._render_output = {}

    # ------------------------------------------------------------------
    # Stage handlers
    # ------------------------------------------------------------------

    def _stage_created(self) -> StageResult:
        return StageResult(
            stage=PipelineStage.CREATED.value,
            success=True,
            summary=f"Task '{self._task.title}' created",
            output={"task_id": str(self._task.task_id), "video_type": self._task.video_type},
            next_stage=PipelineStage.ANALYZING.value,
        )

    def _stage_analyzing(self) -> StageResult:
        vt = self._task.video_type
        valid_types = ("horizontal", "vertical", "shorts", "reels", "tiktok", "cortes")
        if vt not in valid_types:
            return StageResult(
                stage=PipelineStage.ANALYZING.value,
                success=False,
                error=f"Unsupported video type: '{vt}'. Must be one of {valid_types}",
            )

        analysis = {
            "video_type": vt,
            "duration_seconds": self._task.duration_seconds,
            "resolution": _resolution_for_type(vt),
            "aspect": _aspect_for_type(vt),
            "assets_count": len(self._task.assets),
            "segments_count": len(self._task.timeline),
            "subtitles_count": len(self._task.subtitles),
            "required_capabilities": list(self._task.requires_capabilities),
        }
        return StageResult(
            stage=PipelineStage.ANALYZING.value,
            success=True,
            summary=f"Analyzed: {vt}, {len(self._task.assets)} assets, {analysis['segments_count']} segments",
            output=analysis,
            next_stage=PipelineStage.VALIDATING.value,
        )

    def _stage_validating(self) -> StageResult:
        issues: list[str] = []
        for asset in self._task.assets:
            if not asset.source:
                issues.append(f"Asset {asset.asset_id} has no source")
        if not self._task.timeline and not self._task.render_profile:
            issues.append("No timeline or render profile specified")
        if not self._task.title:
            issues.append("Task has no title")

        return StageResult(
            stage=PipelineStage.VALIDATING.value,
            success=len(issues) == 0,
            summary=f"Validated: {len(issues)} issues" if issues else "All assets valid",
            output={"issues": issues, "assets_checked": len(self._task.assets)},
            next_stage=PipelineStage.PLANNING.value if len(issues) == 0 else None,
            error="; ".join(issues) if issues else "",
        )

    def _stage_planning(self) -> StageResult:
        profile = self._task.render_profile or RenderProfile()
        plan = {
            "timeline_segments": len(self._task.timeline),
            "total_duration": self._task.duration_seconds,
            "render_format": profile.format,
            "render_codec": profile.codec,
            "render_resolution": f"{profile.resolution[0]}x{profile.resolution[1]}",
            "render_fps": profile.fps,
            "render_quality": profile.quality,
            "needs_subtitles": len(self._task.subtitles) > 0,
        }
        return StageResult(
            stage=PipelineStage.PLANNING.value,
            success=True,
            summary=f"Planned: {plan['timeline_segments']} segments, {profile.format} @ {plan['render_resolution']}",
            output=plan,
            next_stage=PipelineStage.EXECUTING.value,
        )

    def _stage_executing(self) -> StageResult:
        segments = self._task.timeline
        processed = len(segments)
        effects_used: set[str] = set()
        for seg in segments:
            for e in seg.effects:
                effects_used.add(e)
            for t in seg.transitions:
                effects_used.add(t)

        return StageResult(
            stage=PipelineStage.EXECUTING.value,
            success=True,
            summary=f"Executed: {processed} segments processed, {len(effects_used)} effects applied",
            output={
                "segments_processed": processed,
                "effects_applied": list(effects_used),
                "current_segment": processed,
            },
            next_stage=PipelineStage.RENDERING.value,
        )

    def _stage_rendering(self) -> StageResult:
        profile = self._task.render_profile or RenderProfile()
        self._render_output = {
            "output_format": profile.format,
            "output_codec": profile.codec,
            "output_resolution": f"{profile.resolution[0]}x{profile.resolution[1]}",
            "output_fps": profile.fps,
            "output_bitrate": profile.bitrate,
            "output_quality": profile.quality,
            "duration_seconds": self._task.duration_seconds,
            "estimated_size_mb": _estimate_size(
                profile.resolution, profile.fps, self._task.duration_seconds,
            ),
        }
        return StageResult(
            stage=PipelineStage.RENDERING.value,
            success=True,
            summary=f"Rendered: {self._render_output['output_format']} @ "
                    f"{self._render_output['output_resolution']}, "
                    f"~{self._render_output['estimated_size_mb']}MB",
            output=dict(self._render_output),
            next_stage=PipelineStage.DELIVERING.value,
        )

    def _stage_delivering(self) -> StageResult:
        delivery = {
            "task_id": str(self._task.task_id),
            "title": self._task.title,
            "video_type": self._task.video_type,
            "duration_seconds": self._task.duration_seconds,
            "render": dict(self._render_output),
            "segments_count": len(self._task.timeline),
            "subtitles_count": len(self._task.subtitles),
            "assets_used": len(self._task.assets),
        }
        return StageResult(
            stage=PipelineStage.DELIVERING.value,
            success=True,
            summary=f"Delivered: '{self._task.title}' ({self._task.video_type}, "
                    f"{self._task.duration_seconds}s)",
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
# Module-level helpers (deterministic, no AI)
# ==================================================================


def _resolution_for_type(video_type: str) -> str:
    return {
        "horizontal": "1920x1080",
        "vertical": "1080x1920",
        "shorts": "1080x1920",
        "reels": "1080x1920",
        "tiktok": "1080x1920",
        "cortes": "1920x1080",
    }.get(video_type, "1920x1080")


def _aspect_for_type(video_type: str) -> str:
    return {
        "horizontal": "16:9",
        "vertical": "9:16",
        "shorts": "9:16",
        "reels": "9:16",
        "tiktok": "9:16",
        "cortes": "16:9",
    }.get(video_type, "16:9")


def _estimate_size(resolution: tuple[int, int], fps: int, duration_s: int) -> int:
    pixels = resolution[0] * resolution[1]
    bytes_per_frame = pixels * 3
    total_frames = fps * duration_s
    raw_size_mb = (bytes_per_frame * total_frames) / (1024 * 1024)
    compressed_mb = raw_size_mb / 50
    return max(1, round(compressed_mb))
