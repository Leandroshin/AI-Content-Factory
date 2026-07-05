"""Demonstration: Script Department - ScriptWriterEmployee + Pipeline + Quality.

Flow:
  1. Create ScriptTask models directly
  2. Create ScriptWriterEmployee with script skills
  3. Receive a compatible script task -> ACCEPTS
  4. Execute the script task -> pipeline runs all script stages
  5. Verify hook, CTA, variations, metrics, capabilities, and state
  6. Verify QualityRuntime and ObservabilityProjector integration
  7. Verify pipeline failure scenario
  8. Verify quality failure and correction generation
  9. Run a light regression over Video, Audio, and Image departments
"""

from __future__ import annotations

from uuid import uuid4

from core.company.quality import QualityRuntime
from core.company.specialist_employee import (
    EmployeeSkill,
    ReceivedTask,
    TaskDecision,
)
from core.departments.audio.employee import AudioEngineerEmployee
from core.departments.image.employee import ImageDesignerEmployee
from core.departments.script.employee import ScriptWriterEmployee
from core.departments.script.models import (
    CallToAction,
    HookVariant,
    RetentionBeat,
    ScriptBrief,
    ScriptExportProfile,
    ScriptSection,
    ScriptTask,
    ScriptVariant,
)
from core.departments.video.employee import VideoEditorEmployee
from core.events.bus import EventBus
from core.observability import ObservabilityProjector
from core.runtime import CompanyRuntime


_ASSERTION_COUNTER: int = 0


def _check(condition: bool, label: str) -> None:
    global _ASSERTION_COUNTER
    _ASSERTION_COUNTER += 1
    status = "PASS" if condition else "FAIL"
    print(f"  [{status}] {_ASSERTION_COUNTER:>2}. {label}")
    if not condition:
        raise AssertionError(label)


def main() -> None:
    print("=" * 62)
    print("Script Department - Writer Employee + Pipeline")
    print("=" * 62)

    # ==================================================================
    # Setup
    # ==================================================================
    event_bus = EventBus()
    observer = ObservabilityProjector(event_bus)
    company = CompanyRuntime(event_bus)
    company.initialize_company()
    qr = QualityRuntime(event_bus=event_bus)

    qr.register_rule(
        name="Script output has no execution errors",
        description="Execution must not contain an error field",
        category="output_quality",
        severity="critical",
        criteria={},
    )
    qr.register_rule(
        name="Script required fields present",
        description="Script quality context must expose expected fields",
        category="output_completeness",
        severity="critical",
        criteria={
            "required_fields": [
                "output_format",
                "script_type",
                "target_audience",
                "objective",
                "hook_present",
                "cta_present",
            ]
        },
    )
    qr.register_rule(
        name="Script production duration within limit",
        description="Production must finish under 30 wall minutes",
        category="process",
        severity="minor",
        criteria={"max_duration_minutes": 30},
    )

    # ==================================================================
    # Step 1: Create ScriptTask models directly
    # ==================================================================
    print("\n" + "-" * 62)
    print("Step 1: Create ScriptTask models")
    print("-" * 62)

    direct_task = ScriptTask(
        task_id=uuid4(),
        title="Direct model script",
        script_type="shorts",
        duration_seconds=45,
        brief=ScriptBrief(
            topic="AI content factory",
            objective="Explain the company pipeline",
            target_audience="founders",
            key_points=("CEO routes work", "Departments produce assets"),
        ),
        hooks=(HookVariant(text="Your content team can run like a factory."),),
        call_to_action=CallToAction(text="Save this for your next launch."),
        export_profile=ScriptExportProfile(format="markdown"),
    )

    _check(direct_task.script_type == "shorts", "ScriptTask created")
    _check(direct_task.brief.topic == "AI content factory", "ScriptBrief attached")
    _check(len(direct_task.requires_capabilities) >= 3, "Model capability hints available")
    _check(direct_task.export_profile.format == "markdown", "Export profile attached")

    # ==================================================================
    # Step 2: Create ScriptWriterEmployee
    # ==================================================================
    print("\n" + "-" * 62)
    print("Step 2: Create ScriptWriterEmployee")
    print("-" * 62)

    writer = ScriptWriterEmployee(
        company_runtime=company,
        employee_id=uuid4(),
        skills=(
            EmployeeSkill(name="text_generation", proficiency=0.95),
            EmployeeSkill(name="document_generation", proficiency=0.85),
            EmployeeSkill(name="storytelling", proficiency=0.90),
        ),
        event_bus=event_bus,
        quality_runtime=qr,
    )

    _check(writer is not None, "Writer created")
    _check(writer.status.value == "idle", "Initial status: idle")
    _check(len(writer.skills) == 3, f"{len(writer.skills)} skills registered")
    scaps = writer.script_capabilities
    _check(len(scaps) == 11, f"{len(scaps)} script capabilities loaded")
    _check(scaps["hooks"].proficiency == 0.9, "Hooks proficiency 0.9")
    _check(scaps["text_revision"].proficiency == 0.87, "Text revision proficiency 0.87")

    # ==================================================================
    # Step 3: Receive compatible script task
    # ==================================================================
    print("\n" + "-" * 62)
    print("Step 3: Receive compatible script task -> ACCEPTS")
    print("-" * 62)

    script_task = ReceivedTask(
        task_id=uuid4(),
        title="Write a retention-first Reel script",
        description="Create a short-form script with hook, narration, beats, CTA, and variants",
        department="Script Production",
        required_skills=("text_generation", "document_generation"),
        context={
            "script_type": "reels",
            "duration_seconds": 45,
            "brief": {
                "topic": "AI Company operating model",
                "objective": "Show how departments turn a request into content",
                "target_audience": "solo founders",
                "tone": "direct",
                "language": "pt-BR",
                "platform": "instagram",
                "key_points": (
                    "CEO delegates the goal",
                    "Department managers assign specialists",
                    "Production departments deliver assets",
                ),
            },
            "source_language": "en-US",
            "requires_research": True,
            "sections": (
                {
                    "name": "hook",
                    "purpose": "Stop scroll",
                    "target_duration_seconds": 4,
                    "content": "Most content teams do not need more ideas. They need an operating system.",
                    "order": 1,
                },
                {
                    "name": "story",
                    "purpose": "Explain the system",
                    "target_duration_seconds": 32,
                    "content": "The CEO reads the goal, the manager routes it, and each department produces one real asset.",
                    "order": 2,
                },
                {
                    "name": "cta",
                    "purpose": "Invite action",
                    "target_duration_seconds": 9,
                    "content": "Use the same structure for your next launch.",
                    "order": 3,
                },
            ),
            "hooks": (
                {
                    "text": "Your AI company should feel less like chat and more like operations.",
                    "style": "contrarian",
                    "retention_score": 0.92,
                },
            ),
            "cta": {
                "text": "Comment 'factory' if you want the workflow map.",
                "action_type": "comment",
                "placement": "end",
            },
            "retention_beats": (
                {
                    "timestamp_seconds": 12,
                    "technique": "pattern_interrupt",
                    "message": "But the trick is not the tool. It is the handoff.",
                },
                {
                    "timestamp_seconds": 28,
                    "technique": "open_loop",
                    "message": "The last department is where quality gets proven.",
                },
            ),
            "narration_blocks": (
                {
                    "speaker": "narrator",
                    "text": "Start with the system, then show the handoff.",
                    "start_time": 0.0,
                    "duration_seconds": 8.0,
                },
            ),
            "variants": (
                {"name": "founder_angle", "angle": "speed"},
                {"name": "operator_angle", "angle": "process"},
            ),
            "export_profile": {
                "format": "markdown",
                "language": "pt-BR",
                "platform_template": "instagram",
                "include_timestamps": True,
            },
        },
    )

    decision = writer.receive_task(script_task)
    _check(decision == TaskDecision.ACCEPTED, f"Decision: {decision}")
    _check(writer.status == "analyzing", f"Status after accept: {writer.status}")
    _check(writer.workload == 1, f"Workload: {writer.workload}")
    _check(writer.pipeline_stage == "created", "Pipeline at CREATED")

    # ==================================================================
    # Step 4: Execute script task
    # ==================================================================
    print("\n" + "-" * 62)
    print("Step 4: Execute script task -> pipeline")
    print("-" * 62)

    result = writer.execute_task(script_task.task_id)
    output = result.output

    _check(result.success, "Pipeline succeeded")
    _check(result.duration_minutes >= 0.0, f"Duration: {result.duration_minutes} min")
    _check(output["pipeline_progress"] > 80.0, f"Progress: {output['pipeline_progress']}%")
    _check(output["script_type"] == "reels", "Script type: reels")
    _check(output["export"]["output_format"] == "markdown", "Export format: markdown")
    _check(output["export"]["platform_template"] == "instagram", "Platform template: instagram")
    _check(output["hook"].startswith("Your AI company"), "Hook present")
    _check("Comment 'factory'" in output["call_to_action"], "CTA present")
    _check(output["variants_count"] == 2, "2 variants generated")
    _check(output["retention_beats_count"] == 2, "2 retention beats")
    _check(output["narration_blocks_count"] == 1, "1 narration block")
    _check(output["word_count"] > 20, f"Word count: {output['word_count']}")
    _check(result.summary.startswith("Delivered"), f"Summary: {result.summary}")
    _check(writer.status == "completed", f"Final status: {writer.status}")

    # ==================================================================
    # Step 5: Production metrics and state
    # ==================================================================
    print("\n" + "-" * 62)
    print("Step 5: Production metrics and state")
    print("-" * 62)

    pm = writer.production_metrics
    _check(pm.total_stages == 9, f"Total stages: {pm.total_stages}")
    _check(pm.completed_stages == pm.total_stages, "All stages completed")
    _check(pm.failed_stages == 0, "Zero failed stages")
    _check(pm.sections_written == 3, "3 sections written")
    _check(pm.hooks_generated == 1, "Hook counted")
    _check(pm.variants_generated == 2, "Variants counted")
    _check(pm.export_format == "markdown", "Metrics export format: markdown")
    _check(pm.word_count == output["word_count"], "Metrics word count matches output")
    _check(pm.quality_passed, "Quality check passed")

    state = writer.state()
    _check("script_capabilities" in state, "script_capabilities in state")
    _check("current_script_task" in state, "current_script_task in state")
    _check(state["pipeline_stage"] == "completed", "State stage: completed")
    _check(state["current_script_task"]["script_type"] == "reels", "State script type: reels")
    _check(state["production_metrics"]["variants_generated"] == 2, "State variants: 2")

    # ==================================================================
    # Step 6: Capability analysis
    # ==================================================================
    print("\n" + "-" * 62)
    print("Step 6: Capability analysis")
    print("-" * 62)

    needs = writer.analyze_capability_needs()
    values = [cap.value for cap in needs]
    _check("text_generation" in values, "TEXT_GENERATION needed")
    _check("document_generation" in values, "DOCUMENT_GENERATION needed")
    _check("web_search" in values, "WEB_SEARCH needed")
    _check("translation" in values, "TRANSLATION needed")
    _check("storage" in values, "STORAGE needed")
    _check("browser_automation" not in values, "No browser automation unless requested")

    # ==================================================================
    # Step 7: Quality and Observability
    # ==================================================================
    print("\n" + "-" * 62)
    print("Step 7: Quality and Observability")
    print("-" * 62)

    snap = observer.snapshot
    _check(snap.quality.rules_count == 3, f"Quality rules: {snap.quality.rules_count}")
    _check(snap.quality.last_validation_passed is True, "Last validation passed")
    _check(snap.script_production.task_id is not None, "ScriptProductionSnapshot task_id set")
    _check(snap.script_production.script_type == "reels", "ScriptProductionSnapshot type: reels")
    _check(snap.script_production.pipeline_stage == "completed", "Script pipeline: completed")
    _check(snap.script_production.quality_passed, "ScriptProductionSnapshot quality passed")
    _check(snap.script_department.total_productions >= 1, "Script total productions incremented")
    _check(snap.script_department.successful_productions >= 1, "Script successful productions incremented")
    _check(snap.script_department.active_productions == 0, "Script active productions: 0")

    prod_events = [e for e in snap.events if e.startswith("production:")]
    quality_events = [e for e in snap.events if e.startswith("quality:")]
    _check(any("dept=script" in e for e in prod_events), "Script production event logged")
    _check(len(quality_events) >= 2, f"Quality events: {len(quality_events)}")

    # ==================================================================
    # Step 8: Pipeline failure scenario
    # ==================================================================
    print("\n" + "-" * 62)
    print("Step 8: Pipeline failure scenario")
    print("-" * 62)

    fail_writer = ScriptWriterEmployee(
        company_runtime=company,
        employee_id=uuid4(),
        skills=(EmployeeSkill(name="text_generation", proficiency=0.9),),
        event_bus=event_bus,
        quality_runtime=qr,
    )
    fail_task = ReceivedTask(
        task_id=uuid4(),
        title="Invalid script type",
        description="Should fail at ANALYZING",
        department="Script Production",
        required_skills=("text_generation",),
        context={"script_type": "threadstorm", "duration_seconds": 45},
    )

    fail_writer.receive_task(fail_task)
    fail_result = fail_writer.execute_task(fail_task.task_id)
    _check(not fail_result.success, "Pipeline failure result")
    _check("Unsupported script type" in fail_result.error, "Unsupported script type error")
    _check(observer.snapshot.script_department.failed_productions >= 1, "Script failed productions incremented")
    fail_stage_logs = [
        e for e in observer.snapshot.events
        if "production:stage:" in e and str(fail_task.task_id)[:8] in e
    ]
    _check(any("stages_failed=1" in e for e in fail_stage_logs), "Failure stage count tracked")

    # ==================================================================
    # Step 9: Quality failure and correction scenario
    # ==================================================================
    print("\n" + "-" * 62)
    print("Step 9: Quality failure and correction scenario")
    print("-" * 62)

    strict_rule = qr.register_rule(
        name="Editorial review required",
        description="Requires editorial_review field in quality context",
        category="output_completeness",
        severity="critical",
        criteria={"required_fields": ["editorial_review"]},
    )
    _check(strict_rule is not None, "Strict quality rule registered")

    quality_writer = ScriptWriterEmployee(
        company_runtime=company,
        employee_id=uuid4(),
        skills=(EmployeeSkill(name="text_generation", proficiency=0.9),),
        event_bus=event_bus,
        quality_runtime=qr,
    )
    quality_task = ReceivedTask(
        task_id=uuid4(),
        title="Quality correction script",
        description="Pipeline succeeds but quality validation fails",
        department="Script Production",
        required_skills=("text_generation",),
        context={
            "script_type": "video",
            "duration_seconds": 60,
            "brief": {
                "topic": "quality loops",
                "objective": "Explain correction flow",
                "target_audience": "operators",
            },
            "export_profile": {"format": "markdown"},
        },
    )

    quality_writer.receive_task(quality_task)
    quality_result = quality_writer.execute_task(quality_task.task_id)
    qout = quality_result.output
    _check(quality_result.success, "Pipeline succeeded despite quality failure")
    _check(qout.get("quality_passed") is False, "Quality validation failed")
    _check(len(qout.get("quality_issues", [])) >= 1, "Quality corrections generated")
    _check(any("editorial_review" in c for c in qout["quality_issues"]), "Correction mentions editorial_review")
    _check(observer.snapshot.production.quality_passed is False, "Generic ProductionSnapshot quality false")
    _check(observer.snapshot.script_production.quality_passed is False, "ScriptProductionSnapshot quality false")

    # ==================================================================
    # Step 10: Light regression over previous production departments
    # ==================================================================
    print("\n" + "-" * 62)
    print("Step 10: Regression with previous departments")
    print("-" * 62)

    regression_bus = EventBus()
    regression_company = CompanyRuntime(regression_bus)
    regression_company.initialize_company()

    video_emp = VideoEditorEmployee(
        company_runtime=regression_company,
        employee_id=uuid4(),
        skills=(EmployeeSkill(name="video_editing", proficiency=0.9),),
        event_bus=regression_bus,
    )
    video_task = ReceivedTask(
        task_id=uuid4(),
        title="Regression video",
        description="Video department still executes",
        department="Video Production",
        required_skills=("video_editing",),
        context={"video_type": "horizontal", "duration_seconds": 30},
    )
    video_emp.receive_task(video_task)
    _check(video_emp.execute_task(video_task.task_id).success, "Video regression passed")

    audio_emp = AudioEngineerEmployee(
        company_runtime=regression_company,
        employee_id=uuid4(),
        skills=(EmployeeSkill(name="audio_processing", proficiency=0.9),),
        event_bus=regression_bus,
    )
    audio_task = ReceivedTask(
        task_id=uuid4(),
        title="Regression audio",
        description="Audio department still executes",
        department="Audio Production",
        required_skills=("audio_processing",),
        context={"audio_type": "voiceover", "duration_seconds": 30},
    )
    audio_emp.receive_task(audio_task)
    _check(audio_emp.execute_task(audio_task.task_id).success, "Audio regression passed")

    image_emp = ImageDesignerEmployee(
        company_runtime=regression_company,
        employee_id=uuid4(),
        skills=(EmployeeSkill(name="image_generation", proficiency=0.9),),
        event_bus=regression_bus,
    )
    image_task = ReceivedTask(
        task_id=uuid4(),
        title="Regression image",
        description="Image department still executes",
        department="Image Production",
        required_skills=("image_generation",),
        context={"image_type": "thumbnail", "canvas": {"width": 1280, "height": 720}},
    )
    image_emp.receive_task(image_task)
    _check(image_emp.execute_task(image_task.task_id).success, "Image regression passed")

    # ==================================================================
    # Summary
    # ==================================================================
    print(f"\n{'=' * 62}")
    print(f"All {_ASSERTION_COUNTER} assertions passed.")
    print(f"{'=' * 62}")


if __name__ == "__main__":
    main()
