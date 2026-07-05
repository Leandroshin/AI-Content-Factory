"""Demonstration: Audio Department — AudioEngineerEmployee + Pipeline + Quality.

Flow:
  1. Create AudioEngineerEmployee with audio skills
  2. Receive a compatible audio task -> ACCEPTS
  3. Receive an incompatible task -> REJECTS
  4. Execute the audio task -> pipeline runs through all 9 stages
  5. Verify production metrics
  6. Verify state includes audio metadata
  7. Test Quality integration
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
)
from core.departments.audio.employee import AudioEngineerEmployee
from core.departments.audio.models import (
    AudioTask,
    VoiceSegment,
)
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
    print("Audio Department — Engineer Employee + Pipeline")
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
        name="Audio must have export format",
        description="Export output must specify format",
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
    # Step 1: Create AudioEngineerEmployee
    # ==================================================================
    print("\n" + "-" * 62)
    print("Step 1: Create AudioEngineerEmployee")
    print("-" * 62)

    engineer_id = uuid4()
    engineer = AudioEngineerEmployee(
        company_runtime=company,
        employee_id=engineer_id,
        skills=(
            EmployeeSkill(name="audio_processing", proficiency=0.95),
            EmployeeSkill(name="speech_generation", proficiency=0.80),
            EmployeeSkill(name="delivery_management", proficiency=0.70),
        ),
        event_bus=event_bus,
        quality_runtime=qr,
    )

    _check(engineer is not None, "Engineer created")
    _check(engineer.status.value == "idle", "Initial status: idle")
    _check(len(engineer.skills) == 3, f"{len(engineer.skills)} skills registered")
    acaps = engineer.audio_capabilities
    _check(len(acaps) == 10, f"{len(acaps)} audio capabilities loaded")
    _check(acaps["voiceover"].proficiency == 0.9, "Voiceover proficiency 0.9")
    _check(acaps["tts_synthesis"].proficiency == 0.9, "TTS proficiency 0.9")
    print(f"  Employee ID: {engineer.employee_id}")

    # ==================================================================
    # Step 2: Compatible audio task -> ACCEPTS
    # ==================================================================
    print("\n" + "-" * 62)
    print("Step 2: Receive compatible audio task -> ACCEPTS")
    print("-" * 62)

    audio_task = ReceivedTask(
        task_id=uuid4(),
        title="Produzir narração para vídeo institucional",
        description="Produzir locução de 60s com fundo musical e exportação em WAV",
        department="Audio Production",
        required_skills=("audio_processing",),
        context={
            "audio_type": "voiceover",
            "duration_seconds": 60,
            "target_format": "wav",
        },
    )

    decision = engineer.receive_task(audio_task)
    _check(decision == TaskDecision.ACCEPTED, f"Decision: {decision}")
    _check(engineer.status == "analyzing", f"Status after accept: {engineer.status}")
    _check(engineer.workload == 1, f"Workload: {engineer.workload}")
    _check(engineer.pipeline_stage is not None, "Pipeline initialized")
    _check(engineer.pipeline_stage == "created", "Pipeline at CREATED")

    # ==================================================================
    # Step 3: Incompatible task -> REJECTS
    # ==================================================================
    print("\n" + "-" * 62)
    print("Step 3: Incompatible task -> REJECTS")
    print("-" * 62)

    research_task = ReceivedTask(
        task_id=uuid4(),
        title="Analisar tendências de áudio",
        description="Relatório de tendências",
        department="Research",
        required_skills=("research",),
    )

    decision2 = engineer.receive_task(research_task)
    _check(decision2 == TaskDecision.REJECTED, f"Decision: {decision2}")
    _check(engineer.total_tasks_rejected == 1, "Rejection counter: 1")

    # ==================================================================
    # Step 4: Execute the audio task -> pipeline runs all stages
    # ==================================================================
    print("\n" + "-" * 62)
    print("Step 4: Execute audio task -> pipeline")
    print("-" * 62)

    result = engineer.execute_task(audio_task.task_id)
    _check(result.success, "Pipeline succeeded")
    _check(result.duration_minutes >= 0.0, f"Duration: {result.duration_minutes} min")
    _check("pipeline_progress" in result.output, "Pipeline progress in output")
    _check(result.output["pipeline_progress"] > 80.0, f"Progress: {result.output['pipeline_progress']}%")
    _check("export" in result.output, "Export output present")
    _check(result.output["export"]["output_format"] == "wav", "Format: wav")
    _check(result.output["export"]["output_bitrate"] == "1411k", "Bitrate: 1411k")
    _check(result.summary.startswith("Delivered"), f"Summary: {result.summary}")
    _check(engineer.status == "completed", f"Final status: {engineer.status}")

    # ==================================================================
    # Step 5: Production metrics
    # ==================================================================
    print("\n" + "-" * 62)
    print("Step 5: Production metrics")
    print("-" * 62)

    pm = engineer.production_metrics
    _check(pm.total_stages > 0, f"Total stages: {pm.total_stages}")
    _check(pm.completed_stages == pm.total_stages, "All stages completed")
    _check(pm.failed_stages == 0, "Zero failed stages")
    _check(pm.export_format == "wav", f"Export format: {pm.export_format}")
    _check(pm.export_bitrate == "1411k", f"Bitrate: {pm.export_bitrate}")
    _check(pm.estimated_size_mb > 0, f"Size: ~{pm.estimated_size_mb}MB")
    _check(pm.quality_passed, "Quality check passed")
    _check(pm.duration_minutes >= 0.0, f"Duration: {pm.duration_minutes} min")

    # ==================================================================
    # Step 6: State includes audio metadata
    # ==================================================================
    print("\n" + "-" * 62)
    print("Step 6: Employee state includes audio metadata")
    print("-" * 62)

    state = engineer.state()
    _check("audio_capabilities" in state, "audio_capabilities in state")
    _check("pipeline_stage" in state, "pipeline_stage in state")
    _check("current_audio_task" in state, "current_audio_task in state")
    _check(state["pipeline_stage"] == "completed", f"State stage: {state['pipeline_stage']}")
    _check(state["current_audio_task"]["audio_type"] == "voiceover", "Audio type: voiceover")
    _check(state["current_audio_task"]["duration_seconds"] == 60, "Duration: 60s")
    _check("production_metrics" in state, "production_metrics in state")
    _check(state["production_metrics"]["export_format"] == "wav", "State export format: wav")
    _check(state["production_metrics"]["quality_passed"], "State quality: passed")

    # ==================================================================
    # Step 7: Workload rejection (max 3)
    # ==================================================================
    print("\n" + "-" * 62)
    print("Step 7: Workload rejection (max 3)")
    print("-" * 62)

    for i in range(3):
        t = ReceivedTask(
            task_id=uuid4(),
            title=f"Audio extra {i+1}",
            description="Extra task",
            department="Audio Production",
            required_skills=("audio_processing",),
            context={"audio_type": "podcast", "duration_seconds": 120},
        )
        d = engineer.receive_task(t)
        if i < 2:
            _check(d == TaskDecision.ACCEPTED, f"Extra {i+1}: ACCEPTED")
        else:
            _check(d == TaskDecision.REJECTED, f"Extra {i+1} (overload): REJECTED")

    _check(engineer.workload <= 3, f"Workload capped at {engineer.workload}")

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

    engineer2 = AudioEngineerEmployee(
        company_runtime=company,
        employee_id=uuid4(),
        skills=(EmployeeSkill(name="audio_processing", proficiency=0.9),),
        event_bus=event_bus,
        quality_runtime=qr,
    )

    task_with_voice = ReceivedTask(
        task_id=uuid4(),
        title="Narração com vozes",
        description="Produzir narração com múltiplos speakers",
        department="Audio Production",
        required_skills=("audio_processing",),
        context={
            "audio_type": "voiceover",
            "duration_seconds": 30,
        },
    )

    engineer2.receive_task(task_with_voice)
    engineer2._current_audio_task = AudioTask(
        task_id=task_with_voice.task_id,
        title=task_with_voice.title,
        audio_type="voiceover",
        duration_seconds=30,
        voice_segments=(
            VoiceSegment(speaker="narrator", text="Hello world"),
            VoiceSegment(speaker="guest", text="Welcome"),
        ),
        metadata=dict(task_with_voice.context),
    )

    needs = engineer2.analyze_capability_needs()
    _check(len(needs) >= 2, f"Capabilities needed: {len(needs)}")
    has_audio_processing = any(c.value == "audio_processing" for c in needs)
    _check(has_audio_processing, "AUDIO_PROCESSING needed")
    has_speech = any(c.value == "speech_generation" for c in needs)
    _check(has_speech, "SPEECH_GENERATION needed (voice segments)")

    engineer3 = AudioEngineerEmployee(
        company_runtime=company,
        employee_id=uuid4(),
        skills=(EmployeeSkill(name="audio_processing", proficiency=0.9),),
        event_bus=event_bus,
        quality_runtime=qr,
    )
    task_simple = ReceivedTask(
        task_id=uuid4(),
        title="Mix simples",
        description="Apenas mixagem",
        department="Audio Production",
        required_skills=("audio_processing",),
        context={"audio_type": "mix_master", "duration_seconds": 60},
    )
    engineer3.receive_task(task_simple)
    needs3 = engineer3.analyze_capability_needs()
    _check(len(needs3) == 2, f"Simple needs: {len(needs3)} (AUDIO_PROCESSING + AUDIO_EDITING)")
    _check(needs3[0].value == "audio_processing", "Has AUDIO_PROCESSING")
    _check(needs3[1].value == "audio_editing", "Has AUDIO_EDITING (master profile defaults)")

    # ==================================================================
    # Summary
    # ==================================================================
    print(f"\n{'=' * 62}")
    print(f"All {_ASSERTION_COUNTER} assertions passed.")
    print(f"{'=' * 62}")


if __name__ == "__main__":
    main()
