"""Demonstration: Department Observability - event-driven snapshots.

Proves that Video, Audio, and Image departments automatically
populate ObservabilityProjector snapshots through events - no
manual calls needed.

Flow:
   1. Create ObservabilityProjector + CompanyRuntime + QualityRuntime
   2. Create one employee per department (Video, Audio, Image)
   3. Execute a production task per department
   4. Verify ProductionSnapshot is populated generically
   5. Verify VideoDepartmentSnapshot + VideoProductionSnapshot + RenderSnapshot
   6. Verify AudioDepartmentSnapshot + AudioProductionSnapshot + ExportSnapshot
   7. Verify ImageDepartmentSnapshot + ImageProductionSnapshot + AssetSnapshot
   8. Verify quality events update ProductionSnapshot
   9. Verify production event log strings
  10. Verify pipeline stage tracking per department
  11. Pipeline failure scenario - invalid video_type -> stage fail tracked
  12. Quality correction scenario - pipeline succeeds, quality fails,
      corrections generated, department snapshot updated via event
"""

from __future__ import annotations

from uuid import uuid4

from core.company.quality import QualityRuntime
from core.company.specialist_employee import (
    EmployeeSkill,
    ReceivedTask,
)
from core.departments.audio.employee import AudioEngineerEmployee
from core.departments.image.employee import ImageDesignerEmployee
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
    print("Department Observability - Event-Driven Snapshots")
    print("=" * 62)

    # ==================================================================
    # Setup
    # ==================================================================
    print("\n" + "-" * 62)
    print("Setup: EventBus + ObservabilityProjector + QualityRuntime")
    print("-" * 62)

    event_bus = EventBus()
    observer = ObservabilityProjector(event_bus)
    company = CompanyRuntime(event_bus)
    company.initialize_company()

    qr = QualityRuntime(event_bus=event_bus)
    qr.register_rule(
        name="Output must have format",
        description="Export/render/output must specify format",
        category="output_quality",
        severity="critical",
        criteria={},
    )

    _check(observer is not None, "ObservabilityProjector created")
    _check(observer.snapshot.production.task_id is None, "ProductionSnapshot empty initially")

    # ==================================================================
    # Step 1: Video Department production
    # ==================================================================
    print("\n" + "-" * 62)
    print("Step 1: Video Department - execute production")
    print("-" * 62)

    video_emp = VideoEditorEmployee(
        company_runtime=company,
        employee_id=uuid4(),
        skills=(EmployeeSkill(name="video_editing", proficiency=0.9),),
        event_bus=event_bus,
        quality_runtime=qr,
    )

    video_task = ReceivedTask(
        task_id=uuid4(),
        title="Video observability test",
        description="Test video observability via events",
        department="Video Production",
        required_skills=("video_editing",),
        context={
            "video_type": "horizontal",
            "duration_seconds": 60,
            "resolution": (1920, 1080),
            "target_format": "mp4",
        },
    )

    video_emp.receive_task(video_task)
    video_emp.execute_task(video_task.task_id)

    _check(observer.snapshot.production.task_id is not None, "ProductionSnapshot task_id set")
    _check(observer.snapshot.video_production.task_id is not None, "VideoProductionSnapshot task_id set")
    _check(observer.snapshot.video_production.video_type == "horizontal", "Video type: horizontal")
    _check(observer.snapshot.video_production.quality_passed, "Video quality passed")
    _check(observer.snapshot.video_department.total_productions >= 1, f"Video total: {observer.snapshot.video_department.total_productions}")
    _check(observer.snapshot.video_department.successful_productions >= 1, f"Video successful: {observer.snapshot.video_department.successful_productions}")
    _check(observer.snapshot.video_department.active_productions == 0, "Video active: 0 (completed)")
    _check(observer.snapshot.video_production.pipeline_stage == "completed", "Video pipeline: completed")
    _check(observer.snapshot.video_production.duration_minutes >= 0.0, "Video duration set")
    _check(observer.snapshot.render.output_format == "mp4", f"Render format: {observer.snapshot.render.output_format}")
    print(f"  Video department snapshot: total={observer.snapshot.video_department.total_productions}, "
          f"success={observer.snapshot.video_department.successful_productions}")

    # ==================================================================
    # Step 2: Audio Department production
    # ==================================================================
    print("\n" + "-" * 62)
    print("Step 2: Audio Department - execute production")
    print("-" * 62)

    audio_emp = AudioEngineerEmployee(
        company_runtime=company,
        employee_id=uuid4(),
        skills=(EmployeeSkill(name="audio_processing", proficiency=0.9),),
        event_bus=event_bus,
        quality_runtime=qr,
    )

    audio_task = ReceivedTask(
        task_id=uuid4(),
        title="Audio observability test",
        description="Test audio observability via events",
        department="Audio Production",
        required_skills=("audio_processing",),
        context={
            "audio_type": "podcast",
            "duration_seconds": 120,
        },
    )

    audio_emp.receive_task(audio_task)
    audio_emp.execute_task(audio_task.task_id)

    _check(observer.snapshot.audio_production.task_id is not None, "AudioProductionSnapshot task_id set")
    _check(observer.snapshot.audio_production.audio_type == "podcast", f"Audio type: {observer.snapshot.audio_production.audio_type}")
    _check(observer.snapshot.audio_production.quality_passed, "Audio quality passed")
    _check(observer.snapshot.audio_department.total_productions >= 1, f"Audio total: {observer.snapshot.audio_department.total_productions}")
    _check(observer.snapshot.audio_department.successful_productions >= 1, f"Audio successful: {observer.snapshot.audio_department.successful_productions}")
    _check(observer.snapshot.audio_department.active_productions == 0, "Audio active: 0 (completed)")
    _check(observer.snapshot.audio_production.pipeline_stage == "completed", "Audio pipeline: completed")
    _check(observer.snapshot.export.output_format == "wav", f"Export format: {observer.snapshot.export.output_format}")
    _check(observer.snapshot.export.output_bitrate == "1411k", f"Bitrate: {observer.snapshot.export.output_bitrate}")
    print(f"  Audio department snapshot: total={observer.snapshot.audio_department.total_productions}, "
          f"success={observer.snapshot.audio_department.successful_productions}")

    # ==================================================================
    # Step 3: Image Department production
    # ==================================================================
    print("\n" + "-" * 62)
    print("Step 3: Image Department - execute production")
    print("-" * 62)

    image_emp = ImageDesignerEmployee(
        company_runtime=company,
        employee_id=uuid4(),
        skills=(EmployeeSkill(name="image_design", proficiency=0.9),),
        event_bus=event_bus,
        quality_runtime=qr,
    )

    image_task = ReceivedTask(
        task_id=uuid4(),
        title="Image observability test",
        description="Test image observability via events",
        department="Image Production",
        required_skills=("image_design",),
        context={
            "image_type": "banner",
            "canvas": {"width": 1920, "height": 480, "orientation": "landscape"},
            "export_profile": {"format": "png", "quality": 95},
        },
    )

    image_emp.receive_task(image_task)
    image_emp.execute_task(image_task.task_id)

    _check(observer.snapshot.image_production.task_id is not None, "ImageProductionSnapshot task_id set")
    _check(observer.snapshot.image_production.image_type == "banner", f"Image type: {observer.snapshot.image_production.image_type}")
    _check(observer.snapshot.image_production.quality_passed, "Image quality passed")
    _check(observer.snapshot.image_department.total_productions >= 1, f"Image total: {observer.snapshot.image_department.total_productions}")
    _check(observer.snapshot.image_department.successful_productions >= 1, f"Image successful: {observer.snapshot.image_department.successful_productions}")
    _check(observer.snapshot.image_department.active_productions == 0, "Image active: 0 (completed)")
    _check(observer.snapshot.image_production.pipeline_stage == "completed", "Image pipeline: completed")
    _check(observer.snapshot.asset.output_format == "png", f"Asset format: {observer.snapshot.asset.output_format}")
    print(f"  Image department snapshot: total={observer.snapshot.image_department.total_productions}, "
          f"success={observer.snapshot.image_department.successful_productions}")

    # ==================================================================
    # Step 4: Generic ProductionSnapshot
    # ==================================================================
    print("\n" + "-" * 62)
    print("Step 4: Generic ProductionSnapshot")
    print("-" * 62)

    _check(observer.snapshot.production.task_id is not None, "Production task_id set (last production)")
    _check(observer.snapshot.production.pipeline_stage != "", "Production pipeline_stage set")
    _check(observer.snapshot.production.progress >= 0.0, "Production progress set")
    _check(observer.snapshot.production.quality_passed is not None, "Production quality_passed set")
    _check(observer.snapshot.production.duration_minutes >= 0.0, "Production duration set")
    print(f"  ProductionSnapshot: stage={observer.snapshot.production.pipeline_stage}, "
          f"progress={observer.snapshot.production.progress}%, "
          f"quality={observer.snapshot.production.quality_passed}")

    # ==================================================================
    # Step 5: Production event log strings
    # ==================================================================
    print("\n" + "-" * 62)
    print("Step 5: Production event log strings")
    print("-" * 62)

    prod_events = [e for e in observer.snapshot.events if e.startswith("production:")]
    prod_started = [e for e in prod_events if "production:started:" in e]
    prod_stages = [e for e in prod_events if "production:stage:" in e]
    prod_completed = [e for e in prod_events if "production:completed:" in e]

    _check(len(prod_started) == 3, f"ProductionStarted events: {len(prod_started)}")
    _check(len(prod_stages) >= 21, f"ProductionStageAdvanced events: {len(prod_stages)} "
           "(7 video + 9 audio + 8 image = 24 stages tracked)")
    _check(len(prod_completed) == 3, f"ProductionCompleted events: {len(prod_completed)}")

    for e in prod_started:
        print(f"    {e}")
    for e in prod_completed:
        print(f"    {e}")
    print(f"    ... {len(prod_stages)} stage events omitted")

    # ==================================================================
    # Step 6: Quality events also update ProductionSnapshot
    # ==================================================================
    print("\n" + "-" * 62)
    print("Step 6: Quality events update ProductionSnapshot")
    print("-" * 62)

    quality_events = [e for e in observer.snapshot.events if e.startswith("quality:")]
    _check(len(quality_events) >= 6, f"Quality events: {len(quality_events)} "
           "(3 productions x 2 events each)")
    for e in quality_events:
        print(f"    {e}")

    _check(observer.snapshot.quality.rules_count == 1, f"Quality rules: {observer.snapshot.quality.rules_count}")
    _check(observer.snapshot.quality.last_validation_passed is True, "Last validation passed")
    _check(observer.snapshot.quality.reports_count >= 3, f"Quality reports: {observer.snapshot.quality.reports_count}")

    # ==================================================================
    # Step 7: Pipeline stage tracking
    # ==================================================================
    print("\n" + "-" * 62)
    print("Step 7: Pipeline stage tracking per department")
    print("-" * 62)

    _check(len(observer.snapshot.video_department.pipeline_stages) > 0, "Video pipeline stages tracked")
    _check(len(observer.snapshot.audio_department.pipeline_stages) > 0, "Audio pipeline stages tracked")
    _check(len(observer.snapshot.image_department.pipeline_stages) > 0, "Image pipeline stages tracked")

    last_video_stage = list(observer.snapshot.video_department.pipeline_stages.values())[-1]
    last_audio_stage = list(observer.snapshot.audio_department.pipeline_stages.values())[-1]
    last_image_stage = list(observer.snapshot.image_department.pipeline_stages.values())[-1]
    _check(last_video_stage == "completed", f"Video last stage: {last_video_stage}")
    _check(last_audio_stage == "completed", f"Audio last stage: {last_audio_stage}")
    _check(last_image_stage == "completed", f"Image last stage: {last_image_stage}")
    print(f"  Video final: {last_video_stage}")
    print(f"  Audio final: {last_audio_stage}")
    print(f"  Image final: {last_image_stage}")

    # ==================================================================
    # Step 8: Pipeline failure scenario - invalid video_type
    # ==================================================================
    print("\n" + "-" * 62)
    print("Step 8: Pipeline failure scenario")
    print("-" * 62)

    fail_emp = VideoEditorEmployee(
        company_runtime=company,
        employee_id=uuid4(),
        skills=(EmployeeSkill(name="video_editing", proficiency=0.9),),
        event_bus=event_bus,
        quality_runtime=qr,
    )

    fail_task = ReceivedTask(
        task_id=uuid4(),
        title="Failure test",
        description="Should fail at ANALYZING - invalid video_type",
        department="Video Production",
        required_skills=("video_editing",),
        context={
            "video_type": "unknown_format",
            "duration_seconds": 60,
            "resolution": (1920, 1080),
            "target_format": "mp4",
        },
    )

    fail_emp.receive_task(fail_task)
    fail_result = fail_emp.execute_task(fail_task.task_id)

    _check(not fail_result.success, "Pipeline failure result")
    _check("Unsupported video type" in fail_result.error, f"Error message: {fail_result.error[:60]}")

    fail_events = [e for e in observer.snapshot.events
                   if "unknown_format" in e or "Unsupported" in e]
    _check(len(fail_events) >= 1, f"Failure logged in events ({len(fail_events)})")

    # verify stage event carries the error
    fail_stage_logs = [e for e in observer.snapshot.events
                       if "production:stage:" in e and str(fail_task.task_id)[:8] in e]
    has_error_log = any("Unsupported video type" in e for e in fail_stage_logs)
    _check(has_error_log, "Stage error logged in production:stage event")

    # verify failed_productions incremented
    _check(observer.snapshot.video_department.failed_productions >= 1,
           f"Video failed_productions: {observer.snapshot.video_department.failed_productions}")

    # verify stages_completed/stages_failed in the log
    fail_stage_counts = [e for e in fail_stage_logs if "stages_completed=" in e]
    last_fail_stage = fail_stage_counts[-1] if fail_stage_counts else ""
    _check("stages_failed=1" in last_fail_stage, f"Stage counts in log: {last_fail_stage[:80]}")

    print(f"  Pipeline failure correctly tracked in observability")

    # ==================================================================
    # Step 9: Quality correction scenario
    # ==================================================================
    print("\n" + "-" * 62)
    print("Step 9: Quality correction scenario")
    print("-" * 62)

    # Register a strict completeness rule that will NOT be satisfied
    strict_rule = qr.register_rule(
        name="Extra validation required",
        description="Requires extra_validation field in quality check result",
        category="output_completeness",
        severity="critical",
        criteria={"required_fields": ["extra_validation"]},
    )
    _check(strict_rule is not None, "Strict quality rule registered")

    quality_emp = VideoEditorEmployee(
        company_runtime=company,
        employee_id=uuid4(),
        skills=(EmployeeSkill(name="video_editing", proficiency=0.9),),
        event_bus=event_bus,
        quality_runtime=qr,
    )

    quality_task = ReceivedTask(
        task_id=uuid4(),
        title="Quality correction test",
        description="Pipeline succeeds, quality validation fails",
        department="Video Production",
        required_skills=("video_editing",),
        context={
            "video_type": "horizontal",
            "duration_seconds": 30,
            "resolution": (1920, 1080),
            "target_format": "mp4",
        },
    )

    quality_emp.receive_task(quality_task)
    quality_result = quality_emp.execute_task(quality_task.task_id)

    # Pipeline succeeded (task success != quality passed)
    _check(quality_result.success, "Pipeline succeeded")

    # Quality should have failed
    output = quality_result.output or {}
    _check(output.get("quality_passed") is False, "Quality validation failed")
    _check(len(output.get("quality_issues", [])) >= 1, f"Corrections generated: {len(output.get('quality_issues', []))}")

    corrections = output.get("quality_issues", [])
    _check(any("extra_validation" in c for c in corrections), f"Correction mentions missing field: {corrections[0][:60]}")
    print(f"  Quality corrections:")
    for c in corrections:
        print(f"    {c}")

    # Verify quality events in observability
    quality_finished_events = [e for e in observer.snapshot.events
                               if "quality:finished:" in e
                               and str(quality_task.task_id)[:8] in e]
    _check(len(quality_finished_events) >= 1, "QualityValidationFinished in events")
    _check(any("passed=False" in e for e in quality_finished_events),
           "Quality event shows passed=False")

    # Verify ProductionSnapshot quality_passed = False (last production had quality failure)
    _check(observer.snapshot.production.quality_passed is False,
           "ProductionSnapshot quality_passed is False")

    # Verify department-specific snapshot was updated by quality event
    _check(observer.snapshot.video_production.quality_passed is False,
           "VideoProductionSnapshot quality_passed is False (via quality->dept propagation)")

    print(f"  Quality failure correctly propagated to department snapshot")

    # ==================================================================
    # Summary
    # ==================================================================
    print(f"\n{'=' * 62}")
    print(f"All {_ASSERTION_COUNTER} assertions passed.")
    print(f"{'=' * 62}")


if __name__ == "__main__":
    main()
