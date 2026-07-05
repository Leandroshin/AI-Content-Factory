"""Deterministic audio production pipeline.

Cada stage avança a pipeline por uma state machine.
Sem AI, sem LLM — rule-based.
"""

from __future__ import annotations

from enum import StrEnum
from typing import Any

from core.departments.audio.models import AudioTask, MasterProfile, MixProfile
from core.departments.base.pipeline import ProductionPipeline, StageResult


class PipelineStage(StrEnum):
    """Stages of the audio production pipeline."""
    CREATED = "created"
    ANALYZING = "analyzing"
    VALIDATING = "validating"
    VOICE_GENERATION = "voice_generation"
    EDITING = "editing"
    MIXING = "mixing"
    MASTERING = "mastering"
    EXPORTING = "exporting"
    DELIVERING = "delivering"
    COMPLETED = "completed"
    FAILED = "failed"


class AudioProductionPipeline(ProductionPipeline):
    """Deterministic audio production pipeline.

    Usage::

        pipeline = AudioProductionPipeline(task)
        while pipeline.stage not in ("completed", "failed"):
            result = pipeline.advance()
    """

    def __init__(self, task: AudioTask) -> None:
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
    def task(self) -> AudioTask:
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
            PipelineStage.VOICE_GENERATION: self._stage_voice_generation,
            PipelineStage.EDITING: self._stage_editing,
            PipelineStage.MIXING: self._stage_mixing,
            PipelineStage.MASTERING: self._stage_mastering,
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
            output={"task_id": str(self._task.task_id), "audio_type": self._task.audio_type},
            next_stage=PipelineStage.ANALYZING.value,
        )

    def _stage_analyzing(self) -> StageResult:
        at = self._task.audio_type
        valid_types = ("voiceover", "podcast", "music", "sound_design", "mix_master")
        if at not in valid_types:
            return StageResult(
                stage=PipelineStage.ANALYZING.value,
                success=False,
                error=f"Unsupported audio type: '{at}'. Must be one of {valid_types}",
            )

        analysis = {
            "audio_type": at,
            "duration_seconds": self._task.duration_seconds,
            "tracks_count": len(self._task.tracks),
            "voice_segments_count": len(self._task.voice_segments),
            "music_segments_count": len(self._task.music_segments),
            "sound_effects_count": len(self._task.sound_effects),
            "sample_rate": (self._task.mix_profile or MixProfile()).sample_rate,
            "has_master": self._task.master_profile is not None,
            "required_capabilities": list(self._task.requires_capabilities),
        }
        return StageResult(
            stage=PipelineStage.ANALYZING.value,
            success=True,
            summary=f"Analyzed: {at}, {analysis['tracks_count']} tracks, "
                    f"{analysis['voice_segments_count']} voice segments",
            output=analysis,
            next_stage=PipelineStage.VALIDATING.value,
        )

    def _stage_validating(self) -> StageResult:
        issues: list[str] = []
        for v in self._task.voice_segments:
            if not v.text and v.end_time > v.start_time:
                issues.append(f"Voice segment {v.segment_id} has no text")
        if not self._task.tracks and not self._task.mix_profile:
            issues.append("No audio tracks or mix profile specified")
        if not self._task.title:
            issues.append("Task has no title")

        return StageResult(
            stage=PipelineStage.VALIDATING.value,
            success=len(issues) == 0,
            summary=f"Validated: {len(issues)} issues" if issues else "All assets valid",
            output={"issues": issues, "voice_segments_checked": len(self._task.voice_segments)},
            next_stage=PipelineStage.VOICE_GENERATION.value if len(issues) == 0 else None,
            error="; ".join(issues) if issues else "",
        )

    def _stage_voice_generation(self) -> StageResult:
        segments = self._task.voice_segments
        total_text = sum(len(v.text) for v in segments if v.text)
        speakers = set(v.speaker for v in segments if v.speaker)

        return StageResult(
            stage=PipelineStage.VOICE_GENERATION.value,
            success=True,
            summary=f"Voice generated: {len(segments)} segments, {total_text} chars, "
                    f"{len(speakers)} speaker(s)",
            output={
                "voice_segments_generated": len(segments),
                "total_characters": total_text,
                "unique_speakers": list(speakers),
            },
            next_stage=PipelineStage.EDITING.value,
        )

    def _stage_editing(self) -> StageResult:
        tracks = self._task.tracks
        total_tracks = len(tracks)
        effects_used: set[str] = set()
        for t in tracks:
            for e in t.effects:
                effects_used.add(e)

        return StageResult(
            stage=PipelineStage.EDITING.value,
            success=True,
            summary=f"Edited: {total_tracks} tracks, {len(effects_used)} effects applied",
            output={
                "tracks_edited": total_tracks,
                "effects_applied": list(effects_used),
            },
            next_stage=PipelineStage.MIXING.value,
        )

    def _stage_mixing(self) -> StageResult:
        mix = self._task.mix_profile or MixProfile()
        mix_info = {
            "sample_rate": mix.sample_rate,
            "bit_depth": mix.bit_depth,
            "channels": mix.channels,
            "normalize": mix.volume_normalize,
            "compressor": mix.compressor,
        }
        return StageResult(
            stage=PipelineStage.MIXING.value,
            success=True,
            summary=f"Mixed: {mix.channels} channels @ {mix.sample_rate}Hz, "
                    f"{mix.bit_depth}bit, normalize={mix.volume_normalize}",
            output=mix_info,
            next_stage=PipelineStage.MASTERING.value,
        )

    def _stage_mastering(self) -> StageResult:
        master = self._task.master_profile or MasterProfile()
        master_info = {
            "format": master.format,
            "codec": master.codec,
            "bitrate": master.bitrate,
            "loudness_target": master.loudness_target,
            "sample_rate": master.sample_rate,
        }
        return StageResult(
            stage=PipelineStage.MASTERING.value,
            success=True,
            summary=f"Mastered: {master.format} / {master.codec} @ {master.bitrate}, "
                    f"loudness={master.loudness_target}LUFS",
            output=master_info,
            next_stage=PipelineStage.EXPORTING.value,
        )

    def _stage_exporting(self) -> StageResult:
        master = self._task.master_profile or MasterProfile()
        self._export_output = {
            "output_format": master.format,
            "output_codec": master.codec,
            "output_bitrate": master.bitrate,
            "output_sample_rate": master.sample_rate,
            "duration_seconds": self._task.duration_seconds,
            "estimated_size_mb": _estimate_audio_size(
                master.sample_rate, master.bitrate, self._task.duration_seconds,
            ),
        }
        return StageResult(
            stage=PipelineStage.EXPORTING.value,
            success=True,
            summary=f"Exported: {self._export_output['output_format']} @ "
                    f"{self._export_output['output_bitrate']}, "
                    f"~{self._export_output['estimated_size_mb']}MB",
            output=dict(self._export_output),
            next_stage=PipelineStage.DELIVERING.value,
        )

    def _stage_delivering(self) -> StageResult:
        delivery = {
            "task_id": str(self._task.task_id),
            "title": self._task.title,
            "audio_type": self._task.audio_type,
            "duration_seconds": self._task.duration_seconds,
            "export": dict(self._export_output),
            "tracks_count": len(self._task.tracks),
            "voice_segments_count": len(self._task.voice_segments),
            "music_segments_count": len(self._task.music_segments),
            "sound_effects_count": len(self._task.sound_effects),
        }
        return StageResult(
            stage=PipelineStage.DELIVERING.value,
            success=True,
            summary=f"Delivered: '{self._task.title}' ({self._task.audio_type}, "
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
# Module-level helpers
# ==================================================================


def _estimate_audio_size(sample_rate: int, bitrate_str: str, duration_s: int) -> int:
    """Estimate file size based on bitrate and duration."""
    bitrate_map = {"1411k": 1411000, "320k": 320000, "256k": 256000,
                   "192k": 192000, "128k": 128000, "96k": 96000}
    bitrate = bitrate_map.get(bitrate_str, 1411000)
    bytes_total = (bitrate // 8) * duration_s
    return max(1, round(bytes_total / (1024 * 1024)))
