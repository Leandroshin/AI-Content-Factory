"""Concrete content production workflow.

This module coordinates existing production departments. It is not a generic
workflow runtime and it does not replace CEO, DM, Orchestrator, or department
pipelines.
"""

from __future__ import annotations

from typing import Any
from uuid import uuid4

from core.company.specialist_employee import ReceivedTask, TaskDecision
from core.content_factory.models import (
    ContentBrief,
    ContentProductionPackage,
    ContentWorkflowEmployees,
    ContentWorkflowResult,
    ContentWorkflowStepResult,
)
from core.departments.audio.models import (
    AudioTrack,
    MasterProfile,
    MixProfile,
    VoiceSegment,
)
from core.departments.image.models import (
    CanvasSpec,
    ExportProfile,
    ImageVariant,
    LayerSpec,
    TextOverlay,
)
from core.departments.video.models import (
    RenderProfile,
    SubtitleSegment,
    TimelineSegment,
    VideoAsset,
)


class ContentProductionWorkflow:
    """Minimum concrete workflow for producing a short-form video asset."""

    def run_short_video(
        self,
        brief: ContentBrief,
        employees: ContentWorkflowEmployees,
    ) -> ContentWorkflowResult:
        """Run Brief -> Script -> Audio -> Image -> Video and return a package."""
        steps: list[ContentWorkflowStepResult] = []

        script_step = self._execute(employees.script_writer, self._script_task(brief))
        steps.append(script_step)
        if not script_step.success:
            return self._failed(steps, script_step.error or "Script production failed")

        audio_step = self._execute(employees.audio_engineer, self._audio_task(brief, script_step.output))
        steps.append(audio_step)
        if not audio_step.success:
            return self._failed(steps, audio_step.error or "Audio production failed")

        image_step = self._execute(employees.image_designer, self._image_task(brief, script_step.output))
        steps.append(image_step)
        if not image_step.success:
            return self._failed(steps, image_step.error or "Image production failed")

        video_step = self._execute(
            employees.video_editor,
            self._video_task(brief, script_step.output, audio_step.output, image_step.output),
        )
        steps.append(video_step)
        if not video_step.success:
            return self._failed(steps, video_step.error or "Video production failed")

        package = self._package(brief, script_step.output, audio_step.output, image_step.output, video_step.output)
        return ContentWorkflowResult(
            success=package.quality_passed,
            package=package,
            steps=tuple(steps),
            summary=(
                f"Content package produced: {package.final_format} "
                f"@ {package.final_resolution}"
            ),
            error="" if package.quality_passed else "Quality validation failed",
        )

    # ------------------------------------------------------------------
    # Task builders
    # ------------------------------------------------------------------

    def _script_task(self, brief: ContentBrief) -> ReceivedTask:
        hook = self._hook_for(brief)
        return ReceivedTask(
            task_id=uuid4(),
            title=f"Create script: {brief.topic}",
            description="Create a retention-first short script for the content workflow.",
            department="Script Production",
            required_skills=("text_generation", "document_generation"),
            context={
                "script_type": brief.video_type,
                "duration_seconds": brief.duration_seconds,
                "brief": {
                    "topic": brief.topic,
                    "objective": brief.objective,
                    "target_audience": brief.target_audience,
                    "tone": brief.tone,
                    "language": brief.language,
                    "platform": brief.platform,
                    "key_points": brief.key_points,
                },
                "sections": (
                    {
                        "name": "hook",
                        "purpose": "Stop scroll",
                        "target_duration_seconds": 5,
                        "content": hook,
                        "order": 1,
                    },
                    {
                        "name": "body",
                        "purpose": "Explain the operating model",
                        "target_duration_seconds": max(20, brief.duration_seconds - 15),
                        "content": self._body_for(brief),
                        "order": 2,
                    },
                    {
                        "name": "cta",
                        "purpose": "Ask for engagement",
                        "target_duration_seconds": 10,
                        "content": brief.call_to_action,
                        "order": 3,
                    },
                ),
                "hooks": (
                    {
                        "text": hook,
                        "style": "direct",
                        "retention_score": 0.9,
                    },
                ),
                "cta": {
                    "text": brief.call_to_action,
                    "action_type": "engagement",
                    "placement": "end",
                },
                "variants": (
                    {"name": "operator", "angle": "proof"},
                    {"name": "builder", "angle": "process"},
                ),
                "export_profile": {
                    "format": "markdown",
                    "language": brief.language,
                    "platform_template": brief.platform,
                    "include_timestamps": True,
                },
                "content_brief": dict(brief.metadata),
            },
        )

    def _audio_task(self, brief: ContentBrief, script_output: dict[str, Any]) -> ReceivedTask:
        script_text = str(script_output.get("script_text", ""))
        hook = str(script_output.get("hook", self._hook_for(brief)))
        cta = str(script_output.get("call_to_action", brief.call_to_action))
        voice_metadata = {
            key: brief.metadata[key]
            for key in ("voice_id", "model_id", "voice_settings")
            if key in brief.metadata
        }
        for source_key, target_key in (
            ("speech_output_dir", "output_dir"),
            ("audio_output_dir", "output_dir"),
            ("speech_output_format", "output_format"),
            ("audio_output_format", "output_format"),
            ("write_audio_file", "write_file"),
            ("speech_write_file", "write_file"),
        ):
            if source_key in brief.metadata:
                voice_metadata[target_key] = brief.metadata[source_key]
        output_format = str(voice_metadata.get("output_format", "mp3"))
        codec = "pcm" if output_format == "wav" else output_format

        return ReceivedTask(
            task_id=uuid4(),
            title=f"Create voiceover: {brief.topic}",
            description="Turn the approved script into deterministic voiceover assets.",
            department="Audio Production",
            required_skills=("audio_processing", "speech_generation"),
            context={
                "audio_type": "voiceover",
                "duration_seconds": brief.duration_seconds,
                "voice_segments": (
                    VoiceSegment(
                        speaker="narrator",
                        text=f"{hook} {script_text} {cta}",
                        start_time=0.0,
                        end_time=float(brief.duration_seconds),
                        style="direct",
                        metadata=voice_metadata,
                    ),
                ),
                "tracks": (
                    AudioTrack(
                        name="narration",
                        type="voice",
                        source=f"script://{script_output.get('task_id', '')}",
                        effects=("normalize", "compressor"),
                    ),
                ),
                "mix_profile": MixProfile(compressor="light"),
                "master_profile": MasterProfile(format=output_format, codec=codec, bitrate="192k"),
                "source_script_task_id": script_output.get("task_id", ""),
            },
        )

    def _image_task(self, brief: ContentBrief, script_output: dict[str, Any]) -> ReceivedTask:
        hook = str(script_output.get("hook", self._hook_for(brief)))
        context: dict[str, Any] = {
            "image_type": "thumbnail",
            "canvas": CanvasSpec(
                width=1080,
                height=1920,
                orientation="portrait",
                background_color=str(brief.metadata.get("image_background_color", "#FFFFFF")),
            ),
            "layers": (
                LayerSpec(
                    name="background",
                    type="shape",
                    width=1080,
                    height=1920,
                    opacity=1.0,
                ),
            ),
            "text_overlays": (
                TextOverlay(
                    text=hook,
                    font_size=64,
                    font_color="#FFFFFF",
                    width=980,
                    height=260,
                    x=50,
                    y=180,
                ),
            ),
            "variants": (
                ImageVariant(name="shorts_cover", width=1080, height=1920, format="png"),
            ),
            "export_profile": ExportProfile(format="png", quality=95),
            "source_script_task_id": script_output.get("task_id", ""),
        }
        for source_key, target_key in (
            ("image_output_dir", "output_dir"),
            ("write_image_file", "write_file"),
        ):
            if source_key in brief.metadata:
                context[target_key] = brief.metadata[source_key]

        return ReceivedTask(
            task_id=uuid4(),
            title=f"Create cover image: {brief.topic}",
            description="Create a vertical cover image tied to the script hook.",
            department="Image Production",
            required_skills=("image_generation", "image_editing"),
            context=context,
        )

    def _video_task(
        self,
        brief: ContentBrief,
        script_output: dict[str, Any],
        audio_output: dict[str, Any],
        image_output: dict[str, Any],
    ) -> ReceivedTask:
        audio_file_path = self._output_file_path(audio_output)
        image_file_path = self._output_file_path(image_output)
        voice_metadata = {"file_path": audio_file_path} if audio_file_path else {}
        cover_metadata = {"file_path": image_file_path} if image_file_path else {}
        voice_asset = VideoAsset(
            type="audio",
            source=audio_file_path or f"audio://{audio_output.get('task_id', '')}",
            duration_seconds=float(brief.duration_seconds),
            format=str(audio_output.get("export", {}).get("output_format", "mp3")),
            metadata=voice_metadata,
        )
        cover_asset = VideoAsset(
            type="image",
            source=image_file_path or f"image://{image_output.get('task_id', '')}",
            duration_seconds=float(brief.duration_seconds),
            format=str(image_output.get("export", {}).get("output_format", "png")),
            resolution=(1080, 1920),
            metadata=cover_metadata,
        )

        context: dict[str, Any] = {
            "video_type": brief.video_type,
            "duration_seconds": brief.duration_seconds,
            "assets": (voice_asset, cover_asset),
            "timeline": (
                TimelineSegment(
                    asset_id=cover_asset.asset_id,
                    start_time=0.0,
                    end_time=float(brief.duration_seconds),
                    layer=0,
                    effects=("zoom_in",),
                ),
                TimelineSegment(
                    asset_id=voice_asset.asset_id,
                    start_time=0.0,
                    end_time=float(brief.duration_seconds),
                    layer=1,
                    effects=("ducking",),
                ),
            ),
            "subtitles": (
                SubtitleSegment(
                    start_time=0.0,
                    end_time=min(5.0, float(brief.duration_seconds)),
                    text=str(script_output.get("hook", self._hook_for(brief))),
                    style="shorts_bold",
                ),
            ),
            "render_profile": RenderProfile(
                format="mp4",
                codec="h264",
                resolution=(1080, 1920),
                fps=30,
                bitrate="8M",
                quality="standard",
            ),
            "source_script_task_id": script_output.get("task_id", ""),
            "source_audio_task_id": audio_output.get("task_id", ""),
            "source_image_task_id": image_output.get("task_id", ""),
            "editing_standard": brief.metadata.get("editing_standard", ""),
            "render_engine_preference": brief.metadata.get("render_engine_preference", ""),
            "editorial_requirements": {
                "word_level_captions": True,
                "keyword_emphasis": True,
                "source_provenance": True,
                "contact_sheet_review": True,
                "overflow_check": True,
                "occlusion_check": True,
                "preview_review": True,
                "youtube_shorts_variant": bool(brief.metadata.get("youtube_shorts_variant", False)),
                "avatar_optional": bool(brief.metadata.get("avatar_optional", False)),
            } if brief.metadata.get("editing_standard") else {},
        }
        for source_key, target_key in (
            ("video_output_dir", "output_dir"),
            ("video_background_color", "background_color"),
            ("image_background_color", "background_color"),
        ):
            if source_key in brief.metadata:
                context[target_key] = brief.metadata[source_key]

        return ReceivedTask(
            task_id=uuid4(),
            title=f"Assemble short video: {brief.topic}",
            description="Assemble script, voiceover, cover, timeline, subtitles, and render profile.",
            department="Video Production",
            required_skills=("video_editing", "video_rendering"),
            context=context,
        )

    # ------------------------------------------------------------------
    # Execution and packaging
    # ------------------------------------------------------------------

    def _execute(self, employee: Any, task: ReceivedTask) -> ContentWorkflowStepResult:
        decision = employee.receive_task(task)
        if decision != TaskDecision.ACCEPTED:
            return ContentWorkflowStepResult(
                department=task.department,
                task_id=task.task_id,
                success=False,
                error=f"Task rejected by {task.department}",
            )

        result = employee.execute_task(task.task_id)
        return ContentWorkflowStepResult(
            department=task.department,
            task_id=task.task_id,
            success=result.success,
            summary=result.summary,
            output=dict(result.output),
            error=result.error,
        )

    def _package(
        self,
        brief: ContentBrief,
        script_output: dict[str, Any],
        audio_output: dict[str, Any],
        image_output: dict[str, Any],
        video_output: dict[str, Any],
    ) -> ContentProductionPackage:
        render = video_output.get("render", {})
        quality_passed = all(
            out.get("quality_passed", True)
            for out in (script_output, audio_output, image_output, video_output)
        )
        return ContentProductionPackage(
            script_task_id=self._uuid_or_none(script_output.get("task_id")),
            audio_task_id=self._uuid_or_none(audio_output.get("task_id")),
            image_task_id=self._uuid_or_none(image_output.get("task_id")),
            video_task_id=self._uuid_or_none(video_output.get("task_id")),
            final_format=str(render.get("output_format", "")),
            final_resolution=str(render.get("output_resolution", "")),
            duration_seconds=brief.duration_seconds,
            quality_passed=quality_passed,
            metadata={
                "topic": brief.topic,
                "platform": brief.platform,
                "video_type": brief.video_type,
                "language": brief.language,
                "final_file_path": str(render.get("file_path", "")),
                "render_inputs": render.get("inputs", {}),
            },
        )

    def _failed(
        self,
        steps: list[ContentWorkflowStepResult],
        error: str,
    ) -> ContentWorkflowResult:
        return ContentWorkflowResult(
            success=False,
            package=None,
            steps=tuple(steps),
            summary="Content workflow failed",
            error=error,
        )

    # ------------------------------------------------------------------
    # Text helpers
    # ------------------------------------------------------------------

    def _hook_for(self, brief: ContentBrief) -> str:
        if brief.metadata.get("hook"):
            return str(brief.metadata["hook"])
        return f"Most people use AI as chat. This turns it into production for {brief.topic}."

    def _body_for(self, brief: ContentBrief) -> str:
        if brief.key_points:
            return " ".join(brief.key_points)
        return (
            "A script department writes, audio creates narration, image designs "
            "the cover, video assembles the asset, and quality validates the result."
        )

    def _uuid_or_none(self, value: Any):
        if value is None:
            return None
        try:
            from uuid import UUID

            return value if isinstance(value, UUID) else UUID(str(value))
        except (TypeError, ValueError):
            return None

    def _output_file_path(self, output: dict[str, Any]) -> str:
        candidates = (
            output.get("asset_file_path"),
            output.get("export", {}).get("file_path", ""),
            output.get("speech_generation", {}).get("output", {}).get("file_path", ""),
        )
        for candidate in candidates:
            if candidate:
                return str(candidate)
        return ""
