"""End-to-end AI Content Factory workflow demo.

Flow proved here:
Brief -> Script -> Audio -> Image -> Video -> Quality -> Observability.
"""

from __future__ import annotations

from uuid import uuid4

from core.company.quality import QualityRuntime
from core.company.specialist_employee import EmployeeSkill
from core.content_factory import (
    ContentBrief,
    ContentProductionWorkflow,
    ContentWorkflowEmployees,
)
from core.departments.audio.employee import AudioEngineerEmployee
from core.departments.image.employee import ImageDesignerEmployee
from core.departments.script.employee import ScriptWriterEmployee
from core.departments.video.employee import VideoEditorEmployee
from core.events.bus import EventBus
from core.observability import ObservabilityProjector
from core.runtime import CompanyRuntime
from core.tools import (
    Capability,
    ElevenLabsAdapter,
    FFmpegRenderAdapter,
    ToolDefinition,
    ToolRegistry,
    ToolRuntime,
    ToolStatus,
)


_ASSERTION_COUNTER: int = 0


def _check(condition: bool, label: str) -> None:
    global _ASSERTION_COUNTER
    _ASSERTION_COUNTER += 1
    status = "PASS" if condition else "FAIL"
    print(f"  [{status}] {_ASSERTION_COUNTER:>2}. {label}")
    if not condition:
        raise AssertionError(label)


def _make_quality_runtime(event_bus: EventBus) -> QualityRuntime:
    quality = QualityRuntime(event_bus=event_bus)
    quality.register_rule(
        name="Production output has no execution errors",
        description="Every department output must be successful and error-free.",
        category="output_quality",
        severity="critical",
        criteria={},
    )
    return quality


def _make_employees(
    company: CompanyRuntime,
    event_bus: EventBus,
    quality: QualityRuntime,
    tool_runtime: ToolRuntime,
    tool_registry: ToolRegistry,
) -> ContentWorkflowEmployees:
    return ContentWorkflowEmployees(
        script_writer=ScriptWriterEmployee(
            company_runtime=company,
            employee_id=uuid4(),
            skills=(
                EmployeeSkill(name="text_generation", proficiency=0.95),
                EmployeeSkill(name="document_generation", proficiency=0.9),
            ),
            event_bus=event_bus,
            quality_runtime=quality,
        ),
        audio_engineer=AudioEngineerEmployee(
            company_runtime=company,
            employee_id=uuid4(),
            skills=(
                EmployeeSkill(name="audio_processing", proficiency=0.9),
                EmployeeSkill(name="speech_generation", proficiency=0.85),
            ),
            event_bus=event_bus,
            tool_runtime=tool_runtime,
            tool_registry=tool_registry,
            quality_runtime=quality,
        ),
        image_designer=ImageDesignerEmployee(
            company_runtime=company,
            employee_id=uuid4(),
            skills=(
                EmployeeSkill(name="image_generation", proficiency=0.9),
                EmployeeSkill(name="image_editing", proficiency=0.85),
            ),
            event_bus=event_bus,
            quality_runtime=quality,
        ),
        video_editor=VideoEditorEmployee(
            company_runtime=company,
            employee_id=uuid4(),
            skills=(EmployeeSkill(name="video_editing", proficiency=0.9),),
            event_bus=event_bus,
            tool_runtime=tool_runtime,
            tool_registry=tool_registry,
            quality_runtime=quality,
        ),
    )


def _make_production_tools(event_bus: EventBus) -> tuple[ToolRuntime, ToolRegistry]:
    runtime = ToolRuntime(event_bus=event_bus)
    registry = ToolRegistry(runtime, event_bus=event_bus)

    speech_tool_id = uuid4()
    runtime.register_tool(
        ToolDefinition(
            tool_id=speech_tool_id,
            name="ElevenLabs",
            category="audio",
            description="Text-to-speech provider for voiceover generation.",
            status=ToolStatus.READY,
            required_config_keys=("api_key",),
            required_credential_keys=("api_key",),
            current_config={"api_key": "mock_api_key"},
            has_credentials=True,
        )
    )

    adapter = ElevenLabsAdapter()
    adapter.configure({"api_key": "mock_api_key"})
    adapter.authenticate()
    adapter.mark_ready()
    runtime.register_adapter(speech_tool_id, adapter)
    registry.register_tool(speech_tool_id, {Capability.SPEECH_GENERATION}, priority=10)

    render_tool_id = uuid4()
    runtime.register_tool(
        ToolDefinition(
            tool_id=render_tool_id,
            name="FFmpeg Renderer",
            category="video",
            description="Local renderer for assembling final video files.",
            status=ToolStatus.READY,
        )
    )
    render_adapter = FFmpegRenderAdapter()
    render_adapter.configure({})
    render_adapter.mark_ready()
    runtime.register_adapter(render_tool_id, render_adapter)
    registry.register_tool(render_tool_id, {Capability.VIDEO_RENDERING}, priority=20)

    return runtime, registry


def main() -> None:
    print("=" * 62)
    print("AI Content Factory - Minimum End-to-End Workflow")
    print("=" * 62)

    event_bus = EventBus()
    observer = ObservabilityProjector(event_bus)
    company = CompanyRuntime(event_bus)
    company.initialize_company()
    quality = _make_quality_runtime(event_bus)
    tool_runtime, tool_registry = _make_production_tools(event_bus)

    employees = _make_employees(company, event_bus, quality, tool_runtime, tool_registry)
    brief = ContentBrief(
        topic="AI Content Factory",
        objective="Show that an AI company can produce content through departments.",
        target_audience="solo founders",
        platform="youtube_shorts",
        language="pt-BR",
        tone="clear",
        duration_seconds=45,
        video_type="shorts",
        key_points=(
            "The CEO receives the goal.",
            "Departments transform the brief into assets.",
            "Quality proves the output before publishing.",
        ),
        call_to_action="Comment factory if you want the workflow map.",
        metadata={
            "hook": "Most people use AI as a chat. I am turning it into a company.",
            "voice_id": "voice_narrator_pt_br",
            "model_id": "mock_multilingual_v2",
            "voice_settings": {"stability": 0.55, "similarity_boost": 0.8},
        },
    )

    workflow = ContentProductionWorkflow()
    result = workflow.run_short_video(brief, employees)

    print("\n" + "-" * 62)
    print("Step 1: Workflow result")
    print("-" * 62)
    _check(result.success, "Workflow succeeded")
    _check(result.package is not None, "Package created")
    _check(len(result.steps) == 4, "Four department steps executed")
    _check(all(step.success for step in result.steps), "All department steps succeeded")

    package = result.package
    assert package is not None
    _check(package.workflow == "brief_to_short_video", "Package workflow name set")
    _check(package.final_format == "mp4", "Package final format is mp4")
    _check(package.final_resolution == "1080x1920", "Package final resolution is vertical")
    _check(package.duration_seconds == 45, "Package duration preserved")
    _check(package.quality_passed, "Package quality passed")

    print("\n" + "-" * 62)
    print("Step 2: Department outputs")
    print("-" * 62)
    script_output = result.output_for("Script Production")
    audio_output = result.output_for("Audio Production")
    image_output = result.output_for("Image Production")
    video_output = result.output_for("Video Production")

    _check(script_output["script_type"] == "shorts", "Script type is shorts")
    _check(script_output["export"]["output_format"] == "markdown", "Script exported as markdown")
    _check("factory" in script_output["call_to_action"].lower(), "Script CTA preserved")
    _check(audio_output["audio_type"] == "voiceover", "Audio type is voiceover")
    _check(audio_output["voice_segments_count"] == 1, "Audio has one voice segment")
    _check(audio_output["export"]["output_format"] == "mp3", "Audio exported as mp3")
    _check(audio_output["speech_generation"]["available"], "Speech tool resolved")
    _check(audio_output["speech_generation"]["success"], "Speech adapter executed")
    _check(audio_output["speech_generation"]["tool_name"] == "ElevenLabs", "ElevenLabs selected by capability")
    _check(audio_output["speech_generation"]["output"]["audio_format"] == "mp3", "Speech output is mp3")
    _check(audio_output["speech_generation"]["output"]["voice_id"] == "voice_narrator_pt_br", "Speech voice id preserved")
    _check(audio_output["speech_generation"]["output"]["model_id"] == "mock_multilingual_v2", "Speech model id preserved")
    _check(image_output["image_type"] == "thumbnail", "Image type is thumbnail")
    _check(image_output["canvas"]["height"] == 1920, "Image canvas is vertical")
    _check(image_output["text_overlays_count"] == 1, "Image has one text overlay")
    _check(video_output["video_type"] == "shorts", "Video type is shorts")
    _check(video_output["render"]["output_format"] == "mp4", "Video rendered as mp4")
    _check(video_output["render"]["output_resolution"] == "1080x1920", "Video resolution is vertical")
    _check(video_output["render"]["render_execution"]["available"], "Render tool resolved")
    _check(video_output["render"]["render_execution"]["success"], "Render adapter executed")
    _check(video_output["render"]["render_execution"]["tool_name"] == "FFmpeg Renderer", "FFmpeg selected by capability")
    _check(video_output["render"]["renderer"] == "ffmpeg", "Render output records FFmpeg renderer")

    print("\n" + "-" * 62)
    print("Step 3: Metrics and observability")
    print("-" * 62)
    _check(employees.audio_engineer.production_metrics.voice_segments_generated == 1, "Audio metrics counted voice")
    _check(employees.image_designer.production_metrics.export_format == "png", "Image metrics export png")
    _check(employees.video_editor.production_metrics.assets_validated == 2, "Video metrics counted assets")
    _check(employees.video_editor.production_metrics.segments_processed == 2, "Video metrics counted timeline")
    _check(tool_runtime.find_by_name("ElevenLabs").usage_count == 1, "Speech tool usage counted")
    _check(tool_runtime.find_by_name("FFmpeg Renderer").usage_count == 1, "Render tool usage counted")

    snapshot = observer.snapshot
    _check(snapshot.script_department.successful_productions >= 1, "Script department observed")
    _check(snapshot.audio_department.successful_productions >= 1, "Audio department observed")
    _check(snapshot.image_department.successful_productions >= 1, "Image department observed")
    _check(snapshot.video_department.successful_productions >= 1, "Video department observed")
    _check(snapshot.quality.reports_count >= 4, "Quality validations observed")

    production_events = [e for e in snapshot.events if e.startswith("production:completed")]
    _check(len(production_events) >= 4, "Production completion events captured")

    print("\n" + "-" * 62)
    print("Workflow Package")
    print("-" * 62)
    print(f"package_id: {package.package_id}")
    print(f"workflow: {package.workflow}")
    print(f"script_task_id: {package.script_task_id}")
    print(f"audio_task_id: {package.audio_task_id}")
    print(f"image_task_id: {package.image_task_id}")
    print(f"video_task_id: {package.video_task_id}")
    print(f"final_format: {package.final_format}")
    print(f"final_resolution: {package.final_resolution}")
    print(f"quality_passed: {package.quality_passed}")

    print(f"\n{'=' * 62}")
    print(f"All {_ASSERTION_COUNTER} assertions passed.")
    print(f"{'=' * 62}")


if __name__ == "__main__":
    main()
