"""Demo: first concrete short-video factory pass.

This proves a practical 60-second path:
Topic brief -> Script Department -> Audio Department -> Image Department ->
Video Department -> FFmpeg render adapter.

The demo keeps paid providers in MOCK mode and uses FFmpeg REAL mode only
when ffmpeg/ffprobe are installed locally. That makes the demo repeatable
without spending API credits while still producing a physical MP4 when the
machine is ready.
"""

from __future__ import annotations

import shutil
from pathlib import Path
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
    ExecutionMode,
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
        name="Short video output has no execution errors",
        description="Each department output must be successful and error-free.",
        category="output_quality",
        severity="critical",
        criteria={},
    )
    return quality


def _make_tools(event_bus: EventBus, output_dir: Path) -> tuple[ToolRuntime, ToolRegistry, bool]:
    runtime = ToolRuntime(event_bus=event_bus)
    registry = ToolRegistry(runtime, event_bus=event_bus)

    speech_tool_id = uuid4()
    runtime.register_tool(
        ToolDefinition(
            tool_id=speech_tool_id,
            name="ElevenLabs",
            category="audio",
            description="Text-to-speech provider for narration.",
            status=ToolStatus.READY,
            required_config_keys=("api_key",),
            required_credential_keys=("api_key",),
            current_config={"api_key": "mock_api_key"},
            has_credentials=True,
        )
    )
    speech_adapter = ElevenLabsAdapter()
    speech_adapter.configure({"api_key": "mock_api_key"})
    speech_adapter.authenticate()
    speech_adapter.mark_ready()
    runtime.register_adapter(speech_tool_id, speech_adapter)
    registry.register_tool(speech_tool_id, {Capability.SPEECH_GENERATION}, priority=10)

    render_tool_id = uuid4()
    runtime.register_tool(
        ToolDefinition(
            tool_id=render_tool_id,
            name="FFmpeg Renderer",
            category="video",
            description="Local FFmpeg renderer for the first short-video pass.",
            status=ToolStatus.READY,
        )
    )
    render_adapter = FFmpegRenderAdapter()
    render_adapter.configure({"output_dir": str(output_dir)})
    has_local_ffmpeg = shutil.which("ffmpeg") is not None and shutil.which("ffprobe") is not None
    if has_local_ffmpeg:
        render_adapter.set_execution_mode(ExecutionMode.REAL)
    render_adapter.mark_ready()
    runtime.register_adapter(render_tool_id, render_adapter)
    registry.register_tool(render_tool_id, {Capability.VIDEO_RENDERING}, priority=20)

    return runtime, registry, has_local_ffmpeg


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
                EmployeeSkill(name="storytelling", proficiency=0.88),
            ),
            event_bus=event_bus,
            quality_runtime=quality,
        ),
        audio_engineer=AudioEngineerEmployee(
            company_runtime=company,
            employee_id=uuid4(),
            skills=(
                EmployeeSkill(name="audio_processing", proficiency=0.9),
                EmployeeSkill(name="speech_generation", proficiency=0.88),
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
                EmployeeSkill(name="image_editing", proficiency=0.86),
            ),
            event_bus=event_bus,
            quality_runtime=quality,
        ),
        video_editor=VideoEditorEmployee(
            company_runtime=company,
            employee_id=uuid4(),
            skills=(
                EmployeeSkill(name="video_editing", proficiency=0.9),
                EmployeeSkill(name="video_rendering", proficiency=0.82),
            ),
            event_bus=event_bus,
            tool_runtime=tool_runtime,
            tool_registry=tool_registry,
            quality_runtime=quality,
        ),
    )


def main() -> None:
    print("=" * 62)
    print("AI Content Factory - First 60s Short Video Pass")
    print("=" * 62)

    output_dir = Path("output/short_video_factory")
    output_dir.mkdir(parents=True, exist_ok=True)

    event_bus = EventBus()
    observer = ObservabilityProjector(event_bus)
    company = CompanyRuntime(event_bus)
    company.initialize_company()
    quality = _make_quality_runtime(event_bus)
    tool_runtime, tool_registry, has_local_ffmpeg = _make_tools(event_bus, output_dir)
    employees = _make_employees(company, event_bus, quality, tool_runtime, tool_registry)

    brief = ContentBrief(
        topic="curiosidades sobre o oceano profundo",
        objective="Criar um video curto de curiosidade com narrador e gancho forte.",
        target_audience="pessoas que gostam de curiosidades rapidas",
        platform="youtube_shorts",
        language="pt-BR",
        tone="curioso e direto",
        duration_seconds=60,
        video_type="shorts",
        key_points=(
            "A maior parte do oceano profundo ainda nao foi vista de perto.",
            "A pressao no fundo do mar muda completamente a forma como a vida sobrevive.",
            "Alguns animais produzem luz propria para se comunicar e cacar.",
            "O misterio final e que sabemos mais sobre algumas regioes do espaco do que sobre o fundo do oceano.",
        ),
        call_to_action="Comenta qual curiosidade voce quer ver no proximo minuto.",
        metadata={
            "hook": "O lugar mais estranho da Terra nao esta no espaco. Esta debaixo do mar.",
            "voice_id": "pt_br_narrator_curious",
            "model_id": "mock_multilingual_v2",
            "voice_settings": {"stability": 0.52, "similarity_boost": 0.82},
            "speech_output_dir": str(output_dir / "audio"),
            "speech_output_format": "wav",
            "write_audio_file": True,
            "image_output_dir": str(output_dir / "image"),
            "write_image_file": True,
            "image_background_color": "#0F172A",
            "video_background_color": "#0F172A",
        },
    )

    result = ContentProductionWorkflow().run_short_video(brief, employees)

    print("\n" + "-" * 62)
    print("Step 1: Workflow package")
    print("-" * 62)
    _check(result.success, "Workflow succeeded")
    _check(result.package is not None, "Package created")
    _check(len(result.steps) == 4, "Four departments executed")
    _check(all(step.success for step in result.steps), "All department steps succeeded")

    package = result.package
    assert package is not None
    _check(package.final_format == "mp4", "Final format is mp4")
    _check(package.final_resolution == "1080x1920", "Final resolution is vertical")
    _check(package.duration_seconds == 60, "Duration is 60 seconds")
    _check(package.quality_passed, "Package quality passed")

    print("\n" + "-" * 62)
    print("Step 2: Creative chain")
    print("-" * 62)
    script_output = result.output_for("Script Production")
    audio_output = result.output_for("Audio Production")
    image_output = result.output_for("Image Production")
    video_output = result.output_for("Video Production")
    render = video_output["render"]
    render_execution = render["render_execution"]

    _check(script_output["script_type"] == "shorts", "Script is short-form")
    _check(script_output["word_count"] > 35, "Script has enough narration text")
    _check("oceano" in script_output["script_text"].lower(), "Script keeps the topic")
    _check(script_output["variants_count"] == 2, "Script produced two variants")
    _check(audio_output["speech_generation"]["success"], "Narration adapter executed")
    _check(audio_output["speech_generation"]["output"]["voice_id"] == "pt_br_narrator_curious",
           "Voice id preserved")
    audio_asset_path = Path(str(audio_output["asset_file_path"]))
    _check(audio_output["export"]["physical_asset"], "Narration exported as a physical asset")
    _check(audio_asset_path.exists(), "Narration WAV exists")
    _check(audio_asset_path.stat().st_size > 0, "Narration WAV has bytes")
    _check(audio_output["export"]["output_format"] == "wav", "Narration export format is wav")
    _check(image_output["canvas"]["width"] == 1080, "Image canvas width is vertical format")
    _check(image_output["canvas"]["height"] == 1920, "Image canvas height is vertical format")
    image_asset_path = Path(str(image_output["asset_file_path"]))
    _check(image_output["export"]["physical_asset"], "Cover image exported as a physical asset")
    _check(image_asset_path.exists(), "Cover PNG exists")
    _check(image_asset_path.stat().st_size > 0, "Cover PNG has bytes")
    _check(video_output["assets_used"] == 2, "Video received image and audio assets")
    _check(video_output["segments_processed"] == 2, "Video timeline has two segments")
    _check(render_execution["available"], "Video rendering capability resolved")
    _check(render_execution["success"], "Render adapter succeeded")
    _check(render["renderer"] == "ffmpeg", "Renderer is FFmpeg")

    print("\n" + "-" * 62)
    print("Step 3: Render artifact")
    print("-" * 62)
    _check(render["output_format"] == "mp4", "Render output format is mp4")
    _check(render["output_resolution"] == "1080x1920", "Render output resolution is 1080x1920")

    if has_local_ffmpeg:
        output_path = Path(str(render["file_path"]))
        _check(render["mode"] == "real", "FFmpeg ran in REAL mode")
        _check(output_path.exists(), "Physical MP4 exists")
        _check(output_path.stat().st_size > 0, "Physical MP4 has bytes")
        _check(output_path.parent.resolve() == output_dir.resolve(), "MP4 written to short_video_factory output")
        render_inputs = render["inputs"]
        _check(render_inputs["used_audio_file"], "FFmpeg consumed the narration WAV")
        _check(render_inputs["used_image_file"], "FFmpeg consumed the cover PNG")
        print(f"\nvideo_file: {output_path.resolve()}")
    else:
        _check(render["mode"] == "mock", "FFmpeg mock mode used without local binaries")
        _check(str(render["file_path"]).startswith("mock://video/"), "Mock render path recorded")

    print("\n" + "-" * 62)
    print("Step 4: Observability and tool usage")
    print("-" * 62)
    snapshot = observer.snapshot
    _check(snapshot.script_department.successful_productions >= 1, "Script department observed")
    _check(snapshot.audio_department.successful_productions >= 1, "Audio department observed")
    _check(snapshot.image_department.successful_productions >= 1, "Image department observed")
    _check(snapshot.video_department.successful_productions >= 1, "Video department observed")
    _check(snapshot.quality.reports_count >= 4, "Quality reports observed")
    _check(tool_runtime.find_by_name("ElevenLabs").usage_count == 1, "ElevenLabs usage counted")
    _check(tool_runtime.find_by_name("FFmpeg Renderer").usage_count == 1, "FFmpeg usage counted")

    print(f"\n{'=' * 62}")
    print(f"All {_ASSERTION_COUNTER} assertions passed.")
    print(f"{'=' * 62}")


if __name__ == "__main__":
    main()
