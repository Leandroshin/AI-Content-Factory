"""Demonstration: Video Department — VideoEditorEmployee + Pipeline + Quality.

Flow:
  1. Create VideoEditorEmployee with video editing skills
  2. Receive a compatible video task -> ACCEPTS
  3. Receive an incompatible task -> REJECTS
  4. Execute the video task -> pipeline runs through all 8 stages
  5. Verify production metrics
  6. Verify state includes video metadata
  7. Test Quality integration (good output vs bad output)
  8. Test capability analysis
  9. Test workload limit (max 3)
  10. Verify observability events
"""

from __future__ import annotations

from uuid import UUID, uuid4

from core.company.quality import QualityRuntime
from core.company.specialist_employee import (
    EmployeeSkill,
    ReceivedTask,
    TaskDecision,
    TaskFinished,
    TaskRejected,
    TaskStarted,
)
from core.departments.video.models import (
    AudioAsset,
    VideoAsset,
    VideoTask,
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


def main() -> None:
    print("=" * 62)
    print("Video Department — Editor Employee + Pipeline")
    print("=" * 62)

    # ==================================================================
    # Setup
    # ==================================================================
    event_bus = EventBus()
    observer = ObservabilityProjector(event_bus)
    company = CompanyRuntime(event_bus)
    company.initialize_company()
    qr = QualityRuntime(event_bus=event_bus)

    # Register quality rules for video
    qr.register_rule(
        name="Video must have output format",
        description="Render output must specify format",
        category="output_quality",
        severity="critical",
        criteria={},
    )
    qr.register_rule(
        name="Duration within limit",
        description="Production must finish under 30 wall minutes",
        category="process",
        severity="minor",
        criteria={"max_duration_minutes": 30},
    )

    # ==================================================================
    # Step 1: Create VideoEditorEmployee
    # ==================================================================
    print("\n" + "-" * 62)
    print("Step 1: Create VideoEditorEmployee")
    print("-" * 62)

    editor_id = uuid4()
    editor = VideoEditorEmployee(
        company_runtime=company,
        employee_id=editor_id,
        skills=(
            EmployeeSkill(name="video_editing", proficiency=0.95),
            EmployeeSkill(name="translation", proficiency=0.70),
            EmployeeSkill(name="delivery_management", proficiency=0.80),
        ),
        event_bus=event_bus,
        quality_runtime=qr,
    )

    _check(editor is not None, "Editor created")
    _check(editor.status.value == "idle", "Initial status: idle")
    _check(len(editor.skills) == 3, f"{len(editor.skills)} skills registered")
    vcaps = editor.video_capabilities
    _check(len(vcaps) == 11, f"{len(vcaps)} video capabilities loaded")
    _check(vcaps["horizontal"].proficiency == 0.9, "Horizontal proficiency 0.9")
    _check(vcaps["cortes"].proficiency == 0.9, "Cortes proficiency 0.9")
    print(f"  Employee ID: {editor.employee_id}")

    # ==================================================================
    # Step 2: Compatible video task -> ACCEPTS
    # ==================================================================
    print("\n" + "-" * 62)
    print("Step 2: Receive compatible video task -> ACCEPTS")
    print("-" * 62)

    video_task = ReceivedTask(
        task_id=uuid4(),
        title="Criar video vertical para Instagram Reels",
        description="Produzir um video vertical de 30s com legendas e 2 assets",
        department="Video Editing",
        required_skills=("video_editing",),
        context={
            "video_type": "vertical",
            "duration_seconds": 30,
            "target_platform": "Instagram Reels",
        },
    )

    decision = editor.receive_task(video_task)
    _check(decision == TaskDecision.ACCEPTED, f"Decision: {decision}")
    _check(editor.status == "analyzing", f"Status after accept: {editor.status}")
    _check(editor.workload == 1, f"Workload: {editor.workload}")
    _check(editor.pipeline_stage is not None, "Pipeline initialized")
    _check(editor.pipeline_stage == "created", "Pipeline at CREATED")

    # ==================================================================
    # Step 3: Incompatible task -> REJECTS
    # ==================================================================
    print("\n" + "-" * 62)
    print("Step 3: Incompatible task -> REJECTS")
    print("-" * 62)

    research_task = ReceivedTask(
        task_id=uuid4(),
        title="Analisar tendências de mercado",
        description="Relatório de tendências do setor",
        department="Research",
        required_skills=("research", "data_analysis"),
    )

    decision2 = editor.receive_task(research_task)
    _check(decision2 == TaskDecision.REJECTED, f"Decision: {decision2}")
    _check(editor.total_tasks_rejected == 1, "Rejection counter: 1")

    # ==================================================================
    # Step 4: Execute the video task -> pipeline runs all stages
    # ==================================================================
    print("\n" + "-" * 62)
    print("Step 4: Execute video task -> pipeline")
    print("-" * 62)

    result = editor.execute_task(video_task.task_id)
    _check(result.success, "Pipeline succeeded")
    _check(result.duration_minutes >= 0.0, f"Duration: {result.duration_minutes} min")
    _check("pipeline_progress" in result.output, "Pipeline progress in output")
    _check(result.output["pipeline_progress"] > 80.0, f"Progress: {result.output['pipeline_progress']}%")
    _check("render" in result.output, "Render output present")
    _check(result.output["render"]["output_format"] == "mp4", "Format: mp4")
    _check(result.output["render"]["output_resolution"] == "1920x1080", "Resolution: 1920x1080")
    _check(result.summary.startswith("Delivered"), f"Summary: {result.summary}")
    _check(editor.status == "completed", f"Final status: {editor.status}")

    # ==================================================================
    # Step 5: Production metrics
    # ==================================================================
    print("\n" + "-" * 62)
    print("Step 5: Production metrics")
    print("-" * 62)

    pm = editor.production_metrics
    _check(pm.total_stages > 0, f"Total stages: {pm.total_stages}")
    _check(pm.completed_stages == pm.total_stages, "All stages completed")
    _check(pm.failed_stages == 0, "Zero failed stages")
    _check(pm.render_format == "mp4", f"Render format: {pm.render_format}")
    _check(pm.render_resolution == "1920x1080", f"Resolution: {pm.render_resolution}")
    _check(pm.estimated_size_mb > 0, f"Size: ~{pm.estimated_size_mb}MB")
    _check(pm.quality_passed, "Quality check passed")
    _check(pm.duration_minutes >= 0.0, f"Duration: {pm.duration_minutes} min")

    # ==================================================================
    # Step 6: State includes video metadata
    # ==================================================================
    print("\n" + "-" * 62)
    print("Step 6: Employee state includes video metadata")
    print("-" * 62)

    state = editor.state()
    _check("video_capabilities" in state, "video_capabilities in state")
    _check("pipeline_stage" in state, "pipeline_stage in state")
    _check("current_video_task" in state, "current_video_task in state")
    _check(state["pipeline_stage"] == "completed", f"State stage: {state['pipeline_stage']}")
    _check(state["current_video_task"]["video_type"] == "vertical", "Video type: vertical")
    _check(state["current_video_task"]["duration_seconds"] == 30, "Duration: 30s")
    _check("production_metrics" in state, "production_metrics in state")
    _check(state["production_metrics"]["render_format"] == "mp4", "State render format: mp4")
    _check(state["production_metrics"]["quality_passed"], "State quality: passed")

    # ==================================================================
    # Step 7: Reject second task (workload already at 1, but re-accept)
    # ==================================================================
    print("\n" + "-" * 62)
    print("Step 7: Workload rejection (max 3)")
    print("-" * 62)

    # Accept 3 more tasks to fill workload
    for i in range(3):
        t = ReceivedTask(
            task_id=uuid4(),
            title=f"Video extra {i+1}",
            description="Extra task",
            department="Video Editing",
            required_skills=("video_editing",),
            context={"video_type": "horizontal", "duration_seconds": 60},
        )
        d = editor.receive_task(t)
        if i < 2:
            _check(d == TaskDecision.ACCEPTED, f"Extra {i+1}: ACCEPTED")
        else:
            _check(d == TaskDecision.REJECTED, f"Extra {i+1} (overload): REJECTED")

    _check(editor.workload <= 3, f"Workload capped at {editor.workload}")

    # ==================================================================
    # Step 8: Quality integration
    # ==================================================================
    print("\n" + "-" * 62)
    print("Step 8: Quality integration")
    print("-" * 62)

    snap = observer.snapshot
    _check(snap.quality.rules_count == 2, f"Quality rules: {snap.quality.rules_count}")
    _check(snap.quality.last_validation_passed is True, "Last validation passed")

    quality_events = [e for e in snap.events if e.startswith("quality:")]
    _check(len(quality_events) >= 2, f"Quality events: {len(quality_events)}")
    for e in quality_events:
        print(f"    -> {e}")

    # ==================================================================
    # Step 9: Task events verified
    # ==================================================================
    print("\n" + "-" * 62)
    print("Step 9: Event verification")
    print("-" * 62)

    all_events = event_bus.events()
    accepted_events = [e for e in all_events
                       if type(e).__name__ == "TaskAccepted"]
    rejected_events = [e for e in all_events
                       if type(e).__name__ == "TaskRejected"]
    started_events = [e for e in all_events
                      if type(e).__name__ == "TaskStarted"]
    finished_events = [e for e in all_events
                       if type(e).__name__ == "TaskFinished"]

    _check(len(accepted_events) >= 3, f"TaskAccepted: {len(accepted_events)}")
    _check(len(rejected_events) >= 2, f"TaskRejected: {len(rejected_events)}")
    _check(len(started_events) >= 1, f"TaskStarted: {len(started_events)}")
    _check(len(finished_events) >= 1, f"TaskFinished: {len(finished_events)}")

    # ==================================================================
    # Step 10: Capability analysis
    # ==================================================================
    print("\n" + "-" * 62)
    print("Step 10: Capability analysis")
    print("-" * 62)

    # Editor has a task with subtitles -> create fresh for analysis
    editor2 = VideoEditorEmployee(
        company_runtime=company,
        employee_id=uuid4(),
        skills=(EmployeeSkill(name="video_editing", proficiency=0.9),),
        event_bus=event_bus,
        quality_runtime=qr,
    )

    task_with_subtitles = ReceivedTask(
        task_id=uuid4(),
        title="Video com legendas",
        description="Produzir video com legendas",
        department="Video Editing",
        required_skills=("video_editing",),
        context={
            "video_type": "horizontal",
            "duration_seconds": 60,
            "has_subtitles": True,
        },
    )

    editor2.receive_task(task_with_subtitles)
    # Manually add subtitle to internal VideoTask for analysis
    from core.departments.video.models import SubtitleSegment
    editor2._current_video_task = VideoTask(
        task_id=task_with_subtitles.task_id,
        title=task_with_subtitles.title,
        video_type="horizontal",
        duration_seconds=60,
        subtitles=(SubtitleSegment(text="Hello"),),
        metadata=dict(task_with_subtitles.context),
    )

    needs = editor2.analyze_capability_needs()
    _check(len(needs) >= 3, f"Capabilities needed: {len(needs)}")
    _check("video_editing" in [c.value for c in needs], "VIDEO_EDITING needed")
    _check("video_rendering" in [c.value for c in needs], "VIDEO_RENDERING needed")
    has_translation = any(c.value == "translation" for c in needs)
    _check(has_translation, "TRANSLATION needed (subtitles)")

    # Without subtitles
    editor3 = VideoEditorEmployee(
        company_runtime=company,
        employee_id=uuid4(),
        skills=(EmployeeSkill(name="video_editing", proficiency=0.9),),
        event_bus=event_bus,
        quality_runtime=qr,
    )
    task_simple = ReceivedTask(
        task_id=uuid4(),
        title="Video simples",
        description="Video sem legendas",
        department="Video Editing",
        required_skills=("video_editing",),
        context={"video_type": "shorts", "duration_seconds": 15},
    )
    editor3.receive_task(task_simple)
    needs3 = editor3.analyze_capability_needs()
    _check(len(needs3) == 2, f"Simple needs: {len(needs3)}")
    _check([c.value for c in needs3] == ["video_editing", "video_rendering"],
           "VIDEO_EDITING + VIDEO_RENDERING needed")

    # ==================================================================
    # Summary
    # ==================================================================
    print(f"\n{'=' * 62}")
    print(f"All {_ASSERTION_COUNTER} assertions passed.")
    print(f"{'=' * 62}")


if __name__ == "__main__":
    main()
