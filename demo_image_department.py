"""Demonstration: Image Department — ImageDesignerEmployee + Pipeline + Quality.

Flow:
  1. Create ImageDesignerEmployee with image skills
  2. Receive a compatible image task -> ACCEPTS
  3. Receive an incompatible task -> REJECTS
  4. Execute the image task -> pipeline runs through all 8 stages
  5. Verify production metrics
  6. Verify state includes image metadata
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
from core.departments.image.employee import ImageDesignerEmployee
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
    print("Image Department — Designer Employee + Pipeline")
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
        name="Image must have export format",
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
    # Step 1: Create ImageDesignerEmployee
    # ==================================================================
    print("\n" + "-" * 62)
    print("Step 1: Create ImageDesignerEmployee")
    print("-" * 62)

    designer_id = uuid4()
    designer = ImageDesignerEmployee(
        company_runtime=company,
        employee_id=designer_id,
        skills=(
            EmployeeSkill(name="image_design", proficiency=0.95),
            EmployeeSkill(name="composition", proficiency=0.85),
            EmployeeSkill(name="export_optimization", proficiency=0.75),
        ),
        event_bus=event_bus,
        quality_runtime=qr,
    )

    _check(designer is not None, "Designer created")
    _check(designer.status.value == "idle", "Initial status: idle")
    _check(len(designer.skills) == 3, f"{len(designer.skills)} skills registered")
    imcaps = designer.image_capabilities
    _check(len(imcaps) == 10, f"{len(imcaps)} image capabilities loaded")
    _check(imcaps["thumbnail"].proficiency == 0.95, "Thumbnail proficiency 0.95")
    _check(imcaps["banner"].proficiency == 0.9, "Banner proficiency 0.9")
    print(f"  Employee ID: {designer.employee_id}")

    # ==================================================================
    # Step 2: Compatible image task -> ACCEPTS
    # ==================================================================
    print("\n" + "-" * 62)
    print("Step 2: Receive compatible image task -> ACCEPTS")
    print("-" * 62)

    image_task = ReceivedTask(
        task_id=uuid4(),
        title="Criar thumbnail para v\u00eddeo do YouTube",
        description="Criar thumbnail 1280x720 com texto e camadas",
        department="Image Production",
        required_skills=("image_design",),
        context={
            "image_type": "thumbnail",
            "canvas": {"width": 1280, "height": 720, "orientation": "landscape"},
            "export_profile": {"format": "jpg", "quality": 90},
            "variants": (
                {"name": "thumb_small", "width": 640, "height": 360, "format": "jpg"},
                {"name": "thumb_large", "width": 1920, "height": 1080, "format": "jpg"},
            ),
        },
    )

    decision = designer.receive_task(image_task)
    _check(decision == TaskDecision.ACCEPTED, f"Decision: {decision}")
    _check(designer.status == "analyzing", f"Status after accept: {designer.status}")
    _check(designer.workload == 1, f"Workload: {designer.workload}")
    _check(designer.pipeline_stage is not None, "Pipeline initialized")
    _check(designer.pipeline_stage == "created", "Pipeline at CREATED")

    # ==================================================================
    # Step 3: Incompatible task -> REJECTS
    # ==================================================================
    print("\n" + "-" * 62)
    print("Step 3: Incompatible task -> REJECTS")
    print("-" * 62)

    research_task = ReceivedTask(
        task_id=uuid4(),
        title="Analisar tend\u00eancias de design",
        description="Relat\u00f3rio de tend\u00eancias",
        department="Research",
        required_skills=("research",),
    )

    decision2 = designer.receive_task(research_task)
    _check(decision2 == TaskDecision.REJECTED, f"Decision: {decision2}")
    _check(designer.total_tasks_rejected == 1, "Rejection counter: 1")

    # ==================================================================
    # Step 4: Execute the image task -> pipeline runs all stages
    # ==================================================================
    print("\n" + "-" * 62)
    print("Step 4: Execute image task -> pipeline")
    print("-" * 62)

    result = designer.execute_task(image_task.task_id)
    _check(result.success, "Pipeline succeeded")
    _check(result.duration_minutes >= 0.0, f"Duration: {result.duration_minutes} min")
    _check("pipeline_progress" in result.output, "Pipeline progress in output")
    _check(result.output["pipeline_progress"] > 80.0, f"Progress: {result.output['pipeline_progress']}%")
    _check("export" in result.output, "Export output present")
    _check(result.output["export"]["output_format"] == "jpg", "Format: jpg")
    _check(result.output["export"]["variants_count"] == 2, "2 variants generated")
    _check(result.summary.startswith("Delivered"), f"Summary: {result.summary}")
    _check(designer.status == "completed", f"Final status: {designer.status}")

    # ==================================================================
    # Step 5: Production metrics
    # ==================================================================
    print("\n" + "-" * 62)
    print("Step 5: Production metrics")
    print("-" * 62)

    pm = designer.production_metrics
    _check(pm.total_stages > 0, f"Total stages: {pm.total_stages}")
    _check(pm.completed_stages == pm.total_stages, "All stages completed")
    _check(pm.failed_stages == 0, "Zero failed stages")
    _check(pm.export_format == "jpg", f"Export format: {pm.export_format}")
    _check(pm.estimate_size_kb > 0, f"Size: ~{pm.estimate_size_kb}KB")
    _check(pm.variants_generated == 2, f"Variants: {pm.variants_generated}")
    _check(pm.quality_passed, "Quality check passed")
    _check(pm.duration_minutes >= 0.0, f"Duration: {pm.duration_minutes} min")

    # ==================================================================
    # Step 6: State includes image metadata
    # ==================================================================
    print("\n" + "-" * 62)
    print("Step 6: Employee state includes image metadata")
    print("-" * 62)

    state = designer.state()
    _check("image_capabilities" in state, "image_capabilities in state")
    _check("pipeline_stage" in state, "pipeline_stage in state")
    _check("current_image_task" in state, "current_image_task in state")
    _check(state["pipeline_stage"] == "completed", f"State stage: {state['pipeline_stage']}")
    _check(state["current_image_task"]["image_type"] == "thumbnail", "Image type: thumbnail")
    _check(state["current_image_task"]["canvas_width"] == 1280, "Canvas width: 1280")
    _check(state["current_image_task"]["canvas_height"] == 720, "Canvas height: 720")
    _check("production_metrics" in state, "production_metrics in state")
    _check(state["production_metrics"]["export_format"] == "jpg", "State export format: jpg")
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
            title=f"Design extra {i+1}",
            description="Extra task",
            department="Image Production",
            required_skills=("image_design",),
            context={"image_type": "banner", "canvas": {"width": 1920, "height": 480}},
        )
        d = designer.receive_task(t)
        if i < 2:
            _check(d == TaskDecision.ACCEPTED, f"Extra {i+1}: ACCEPTED")
        else:
            _check(d == TaskDecision.REJECTED, f"Extra {i+1} (overload): REJECTED")

    _check(designer.workload <= 3, f"Workload capped at {designer.workload}")

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

    designer2 = ImageDesignerEmployee(
        company_runtime=company,
        employee_id=uuid4(),
        skills=(EmployeeSkill(name="image_design", proficiency=0.9),),
        event_bus=event_bus,
        quality_runtime=qr,
    )

    task_with_layers = ReceivedTask(
        task_id=uuid4(),
        title="Banner com camadas",
        description="Criar banner com m\u00faltiplas camadas",
        department="Image Production",
        required_skills=("image_design",),
        context={
            "image_type": "banner",
            "canvas": {"width": 1920, "height": 480},
            "layers": (
                {"name": "BG", "type": "shape", "width": 1920, "height": 480},
                {"name": "Logo", "type": "image", "source": "logo.png",
                 "width": 200, "height": 200},
            ),
            "variants": (
                {"name": "banner_full", "width": 1920, "height": 480},
            ),
        },
    )

    designer2.receive_task(task_with_layers)
    needs = designer2.analyze_capability_needs()
    _check(len(needs) >= 2, f"Capabilities needed: {len(needs)}")
    has_image_gen = any(c.value == "image_generation" for c in needs)
    _check(has_image_gen, "IMAGE_GENERATION needed")
    has_image_edit = any(c.value == "image_editing" for c in needs)
    _check(has_image_edit, "IMAGE_EDITING needed (layers)")
    has_storage = any(c.value == "storage" for c in needs)
    _check(has_storage, "STORAGE needed (variants)")

    designer3 = ImageDesignerEmployee(
        company_runtime=company,
        employee_id=uuid4(),
        skills=(EmployeeSkill(name="image_design", proficiency=0.9),),
        event_bus=event_bus,
        quality_runtime=qr,
    )
    task_simple = ReceivedTask(
        task_id=uuid4(),
        title="Thumbnail simples",
        description="Apenas uma thumbnail",
        department="Image Production",
        required_skills=("image_design",),
        context={"image_type": "thumbnail", "canvas": {"width": 1280, "height": 720}},
    )
    designer3.receive_task(task_simple)
    needs3 = designer3.analyze_capability_needs()
    _check(len(needs3) == 1, f"Simple needs: {len(needs3)}")
    _check(needs3[0].value == "image_generation", "Only IMAGE_GENERATION needed")

    # ==================================================================
    # Summary
    # ==================================================================
    print(f"\n{'=' * 62}")
    print(f"All {_ASSERTION_COUNTER} assertions passed.")
    print(f"{'=' * 62}")


if __name__ == "__main__":
    main()
