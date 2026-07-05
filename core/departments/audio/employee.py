"""AudioEngineerEmployee — ProductionEmployee especializado em áudio.

Herda ProductionEmployee (→ SpecialistEmployee) sem duplicar.
Todo comportamento genérico está em core/departments/base/.
Aqui: apenas lógica específica de áudio.
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
    ReceivedTask,
    TaskAccepted,
    TaskDecision,
)
from core.departments.audio.models import AudioTask, MasterProfile, MixProfile
from core.departments.audio.pipeline import AudioProductionPipeline, PipelineStage
from core.departments.base.employee import ProductionEmployee
from core.departments.base.pipeline import ProductionPipeline
from core.events.bus import EventBus
from core.runtime import CompanyRuntime as CoreCompanyRuntime
from core.tools.adapters.models import ToolRequest
from core.tools.capabilities import Capability
from core.tools.registry import ToolRegistry
from core.tools.runtime import ToolRuntime


@dataclass(frozen=True, slots=True)
class AudioCapability:
    """Domain-specific audio capability metadata.
    Complementar a EmployeeSkill — não substitui.
    """
    name: str
    proficiency: float = 0.5
    enabled: bool = True


@dataclass(frozen=True, slots=True)
class ProductionMetrics:
    """Metrics accumulated across an audio production run.
    Inclui campos genéricos + específicos de áudio.
    """
    total_stages: int = 0
    completed_stages: int = 0
    failed_stages: int = 0
    voice_segments_generated: int = 0
    tracks_processed: int = 0
    effects_applied: tuple[str, ...] = field(default_factory=tuple)
    export_format: str = ""
    export_bitrate: str = ""
    estimated_size_mb: int = 0
    quality_passed: bool = False
    quality_corrections: tuple[str, ...] = field(default_factory=tuple)
    duration_minutes: float = 0.0


class AudioEngineerEmployee(ProductionEmployee):
    """Specialist employee for audio production.

    Aceita apenas tarefas compatíveis com áudio.
    Utiliza pipeline de produção de áudio (9 stages).
    Integra QualityRuntime para validação pós-export.
    """

    _DEPARTMENT_KEYWORD = "audio"

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
        self._audio_capabilities: dict[str, AudioCapability] = {
            "voiceover": AudioCapability(name="voiceover", proficiency=0.9),
            "podcast": AudioCapability(name="podcast", proficiency=0.85),
            "music_production": AudioCapability(name="music_production", proficiency=0.7),
            "sound_design": AudioCapability(name="sound_design", proficiency=0.75),
            "mix_master": AudioCapability(name="mix_master", proficiency=0.8),
            "tts_synthesis": AudioCapability(name="tts_synthesis", proficiency=0.9),
            "voice_cloning": AudioCapability(name="voice_cloning", proficiency=0.6),
            "noise_reduction": AudioCapability(name="noise_reduction", proficiency=0.8),
            "audio_restoration": AudioCapability(name="audio_restoration", proficiency=0.5),
            "format_conversion": AudioCapability(name="format_conversion", proficiency=0.85),
        }
        self._current_audio_task: AudioTask | None = None

    # ------------------------------------------------------------------
    # Properties
    # ------------------------------------------------------------------

    @property
    def audio_capabilities(self) -> dict[str, AudioCapability]:
        return dict(self._audio_capabilities)

    # ------------------------------------------------------------------
    # Task handling — audio-specific
    # ------------------------------------------------------------------

    def receive_task(self, task: ReceivedTask) -> TaskDecision:
        if "audio" not in task.department.lower():
            return super().receive_task(task)

        if self._workload >= self._max_workload:
            return super().receive_task(task)

        self._tasks[task.task_id] = task
        self._current_task_id = task.task_id
        self._workload += 1
        self._status = EmployeeStatus.ANALYZING

        ctx = task.context

        master_profile = ctx.get("master_profile")
        if master_profile is not None and not isinstance(master_profile, MasterProfile):
            master_profile = MasterProfile(
                format=master_profile.get("format", "wav"),
                codec=master_profile.get("codec", "pcm"),
                bitrate=master_profile.get("bitrate", "1411k"),
                loudness_target=master_profile.get("loudness_target", -14.0),
                sample_rate=master_profile.get("sample_rate", 48000),
            )
        elif master_profile is None:
            master_profile = MasterProfile()

        mix_profile = ctx.get("mix_profile")
        if mix_profile is not None and not isinstance(mix_profile, MixProfile):
            mix_profile = MixProfile(
                sample_rate=mix_profile.get("sample_rate", 48000),
                bit_depth=mix_profile.get("bit_depth", 24),
                channels=mix_profile.get("channels", 2),
                volume_normalize=mix_profile.get("volume_normalize", True),
                noise_gate=mix_profile.get("noise_gate", False),
                compressor=mix_profile.get("compressor", "none"),
            )
        elif mix_profile is None:
            mix_profile = MixProfile()

        tracks = ctx.get("tracks", ())
        voice_segments = ctx.get("voice_segments", ())
        music_segments = ctx.get("music_segments", ())
        sound_effects = ctx.get("sound_effects", ())

        self._current_audio_task = AudioTask(
            task_id=task.task_id,
            title=task.title,
            audio_type=ctx.get("audio_type", "voiceover"),
            duration_seconds=ctx.get("duration_seconds", 60),
            tracks=tracks,
            voice_segments=voice_segments,
            music_segments=music_segments,
            sound_effects=sound_effects,
            mix_profile=mix_profile,
            master_profile=master_profile,
            metadata=dict(ctx),
        )
        self._pipeline = AudioProductionPipeline(self._current_audio_task)

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
        if "audio" not in task.department.lower():
            return f"Department '{task.department}' is not audio"
        if self._workload >= self._max_workload:
            return "Workload limit reached (max 3)"
        return None

    # ------------------------------------------------------------------
    # Pipeline
    # ------------------------------------------------------------------

    def _build_pipeline(self, task: ReceivedTask) -> ProductionPipeline:
        return AudioProductionPipeline(self._current_audio_task)

    def _estimate_duration(self, ctx: dict[str, Any]) -> int:
        dur = ctx.get("duration_seconds", 60)
        base = max(1, dur // 60)
        audio_type = ctx.get("audio_type", "voiceover")
        type_factor = {
            "voiceover": 1.0, "podcast": 1.5, "music": 2.0,
            "sound_design": 2.5, "mix_master": 3.0,
        }.get(audio_type, 1.0)
        return max(1, round(base * type_factor))

    def _get_production_type(self) -> str:
        if self._current_audio_task:
            return self._current_audio_task.audio_type
        return ""

    # ------------------------------------------------------------------
    # Output building — audio-specific
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
                                     if k != "effects_applied"})
                if slog.output.get("effects_applied"):
                    final_output["effects_applied"] = slog.output["effects_applied"]

        speech_generation = self._try_generate_speech()
        if speech_generation:
            final_output["speech_generation"] = speech_generation
            speech_output = speech_generation.get("output", {})
            if speech_generation.get("success") and speech_output.get("file_path"):
                final_output["asset_file_path"] = speech_output["file_path"]
                export_output = dict(final_output.get("export", {}))
                export_output["file_path"] = speech_output["file_path"]
                export_output["file_size_bytes"] = speech_output.get("file_size_bytes", 0)
                export_output["physical_asset"] = True
                if speech_output.get("audio_format"):
                    export_output["output_format"] = speech_output["audio_format"]
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
            voice_segments_generated=(
                len(self._current_audio_task.voice_segments)
                if self._current_audio_task else 0
            ),
            tracks_processed=final_output.get("tracks_edited", 0),
            effects_applied=tuple(final_output.get("effects_applied", [])),
            export_format=final_output.get("export", {}).get("output_format", ""),
            export_bitrate=final_output.get("export", {}).get("output_bitrate", ""),
            estimated_size_mb=final_output.get("export", {}).get("estimated_size_mb", 0),
            quality_passed=final_output.get("quality_passed", True),
            quality_corrections=tuple(final_output.get("quality_issues", [])),
            duration_minutes=round(duration, 2),
        )

    def _build_summary(self, success: bool, summary_parts: list[str]) -> str:
        if summary_parts:
            return " | ".join(summary_parts)
        return "Audio production completed" if success else "Audio production failed"

    # ------------------------------------------------------------------
    # Optional tools — capability -> adapter
    # ------------------------------------------------------------------

    def _try_generate_speech(self) -> dict[str, Any]:
        """Use a registered speech-generation tool when one is available.

        This is intentionally optional. Without ToolRegistry/ToolRuntime the
        deterministic audio pipeline remains unchanged.
        """
        if self._tool_registry is None or self._tool_runtime is None:
            return {}
        if self._current_audio_task is None:
            return {}

        segments = tuple(
            v for v in self._current_audio_task.voice_segments if v.text
        )
        if not segments:
            return {}

        task_id = self._current_task_id or UUID(int=0)
        selected = self._tool_registry.resolve(
            Capability.SPEECH_GENERATION,
            self._employee_id,
            task_id=task_id,
        )
        tool_id = getattr(selected, "tool_id", None)
        if tool_id is None:
            return {
                "available": False,
                "capability": Capability.SPEECH_GENERATION.value,
                "reason": getattr(selected, "reason", "No speech generation tool available"),
            }

        text = " ".join(v.text for v in segments)
        first_segment = segments[0]
        voice = first_segment.speaker or "default"
        request_params: dict[str, Any] = {
            "action": "synthesize",
            "text": text,
            "voice": voice,
            "duration_seconds": self._current_audio_task.duration_seconds,
        }
        for key in (
            "voice_id",
            "model_id",
            "voice_settings",
            "output_dir",
            "output_format",
            "write_file",
        ):
            if key in first_segment.metadata:
                request_params[key] = first_segment.metadata[key]

        request = ToolRequest(
            tool_id=tool_id,
            capability=Capability.SPEECH_GENERATION.value,
            params=request_params,
            metadata={
                "audio_task_id": str(self._current_audio_task.task_id),
                "audio_type": self._current_audio_task.audio_type,
            },
        )
        try:
            result = self._tool_runtime.execute_tool(tool_id, request)
        except Exception as exc:  # pragma: no cover - defensive around real APIs
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

        output = dict(result.output)
        speech_generation = {
            "available": True,
            "tool_id": str(tool_id),
            "tool_name": getattr(selected, "tool_name", ""),
            "success": result.success,
            "summary": result.summary,
            "output": output,
            "error": result.error,
        }
        return speech_generation

    # ------------------------------------------------------------------
    # Quality — adds audio-specific fields
    # ------------------------------------------------------------------

    def _run_quality_check(self, output: dict[str, Any]) -> tuple[bool, list[str]]:
        if self._quality_runtime is None:
            return True, []

        exec_id = self._current_task_id or UUID(int=0)
        report = self._quality_runtime.validate(exec_id, {
            "success": output.get("error", "") == "",
            "error": output.get("error", ""),
            "output_format": output.get("export", {}).get("output_format", ""),
            "output_bitrate": output.get("export", {}).get("output_bitrate", ""),
            "duration_seconds": output.get("duration_seconds", 0),
        })

        if report.passed:
            return True, []
        return False, self._quality_runtime.generate_correction(report)

    # ------------------------------------------------------------------
    # Capability analysis — audio-specific
    # ------------------------------------------------------------------

    def analyze_capability_needs(self) -> tuple[Capability, ...]:
        needed: list[Capability] = [Capability.AUDIO_PROCESSING]

        if self._current_audio_task and any(
            v.text for v in self._current_audio_task.voice_segments if v.text
        ):
            needed.append(Capability.SPEECH_GENERATION)
        if self._current_audio_task and any(
            v.speaker != "default" for v in self._current_audio_task.voice_segments
        ):
            needed.append(Capability.VOICE_CLONE)
        if self._current_audio_task and self._current_audio_task.master_profile is not None:
            needed.append(Capability.AUDIO_EDITING)

        return tuple(needed)

    # ------------------------------------------------------------------
    # State
    # ------------------------------------------------------------------

    def state(self) -> dict[str, Any]:
        base = super().state()
        base["audio_capabilities"] = {
            k: {"name": v.name, "proficiency": v.proficiency, "enabled": v.enabled}
            for k, v in self._audio_capabilities.items()
        }
        base["current_audio_task"] = (
            {
                "title": self._current_audio_task.title,
                "audio_type": self._current_audio_task.audio_type,
                "duration_seconds": self._current_audio_task.duration_seconds,
            }
            if self._current_audio_task else None
        )
        base["production_metrics"]["voice_segments_generated"] = self._production_metrics.voice_segments_generated
        base["production_metrics"]["tracks_processed"] = self._production_metrics.tracks_processed
        base["production_metrics"]["export_format"] = self._production_metrics.export_format
        base["production_metrics"]["export_bitrate"] = self._production_metrics.export_bitrate
        return base
