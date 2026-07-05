"""Managed AI Content Factory workflow demo.

Proves:
Brief -> ExecutivePlan -> DM tasks -> assign/start -> departments execute ->
complete -> company progress/health -> final content package.
"""

from __future__ import annotations

from uuid import uuid4

from core.company.department_manager import (
    DepartmentManager,
    PlanReceived,
    TaskAssigned,
    TaskCompleted,
    TaskStatus,
    TasksDecomposed,
)
from core.company.quality import QualityRuntime
from core.company.runtime import CompanyTaskRuntime
from core.company.specialist_employee import EmployeeSkill
from core.content_factory import (
    ContentBrief,
    ContentWorkflowEmployees,
    ManagedContentProductionWorkflow,
)
from core.departments.audio.employee import AudioEngineerEmployee
from core.departments.image.employee import ImageDesignerEmployee
from core.departments.runtime import DepartmentRuntime
from core.departments.script.employee import ScriptWriterEmployee
from core.departments.video.employee import VideoEditorEmployee
from core.events.bus import EventBus
from core.observability import ObservabilityProjector
from core.orchestrator.runtime import OrchestratorRuntime
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
        name="Managed production output has no execution errors",
        description="Every managed department output must be successful.",
        category="output_quality",
        severity="critical",
        criteria={},
    )
    return quality


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


def main() -> None:
    print("=" * 70)
    print("AI Content Factory - Managed Workflow")
    print("=" * 70)

    event_bus = EventBus()
    observer = ObservabilityProjector(event_bus)
    company = CompanyRuntime(event_bus)
    company.initialize_company()
    quality = _make_quality_runtime(event_bus)
    tool_runtime, tool_registry = _make_production_tools(event_bus)

    department_runtime = DepartmentRuntime(company, event_bus)
    orchestrator = OrchestratorRuntime(company, department_runtime, event_bus)
    manager = DepartmentManager(company, event_bus)
    company_orchestrator = CompanyTaskRuntime(
        core_company=company,
        orchestrator=orchestrator,
        event_bus=event_bus,
        department_manager=manager,
        observability=observer,
    )

    employees = _make_employees(company, event_bus, quality, tool_runtime, tool_registry)
    brief = ContentBrief(
        topic="AI Content Factory",
        objective="Prove the content factory can be managed like a company.",
        target_audience="solo creators",
        platform="youtube_shorts",
        language="pt-BR",
        tone="clear",
        duration_seconds=45,
        video_type="shorts",
        key_points=(
            "A manager receives an executive plan.",
            "Departments execute real production steps.",
            "Progress reaches 100 percent after QA sign-off.",
        ),
        call_to_action="Comment factory if you want the management map.",
        metadata={
            "hook": "The factory now has management, not just production.",
            "voice_id": "voice_narrator_pt_br",
            "model_id": "mock_multilingual_v2",
        },
    )

    workflow = ManagedContentProductionWorkflow(
        manager,
        company_runtime=company,
        company_task_runtime=company_orchestrator,
    )
    result = workflow.run_short_video_managed(brief, employees)

    print("\n" + "-" * 70)
    print("Step 1: Managed workflow result")
    print("-" * 70)
    _check(result.success, "Managed workflow succeeded")
    _check(result.workflow_result is not None, "Underlying content workflow returned")
    _check(result.workflow_result.success, "Underlying content workflow succeeded")
    _check(result.plan_id is not None, "Executive plan id returned")
    _check(result.progress_pct == 100.0, "DepartmentManager progress reached 100%")
    _check(result.completed_tasks == result.total_tasks, "All managed tasks completed")
    _check(result.total_tasks == len(result.management_tasks), "Every DM task has a management record")
    _check(all(t.assigned for t in result.management_tasks), "All management tasks assigned")
    _check(all(t.started for t in result.management_tasks), "All management tasks started")
    _check(all(t.completed for t in result.management_tasks), "All management tasks completed")
    _check(all(t.success for t in result.management_tasks), "All management tasks succeeded")

    workflow_result = result.workflow_result
    package = workflow_result.package
    _check(package is not None, "Final content package created")
    _check(package.final_format == "mp4", "Final package format is mp4")
    _check(package.quality_passed, "Final package quality passed")
    _check(len(workflow_result.steps) == 4, "Four production department steps executed")

    print("\n" + "-" * 70)
    print("Step 2: DepartmentManager state")
    print("-" * 70)
    assert result.plan_id is not None
    tasks = manager.tasks_for_plan(result.plan_id)
    _check(len(tasks) == result.total_tasks, "DM exposes all plan tasks")
    _check(all(t.status == TaskStatus.COMPLETED for t in tasks), "All DM tasks are completed")
    _check({t.manager_department for t in result.management_tasks} == {
        "Content Production",
        "Audio Production",
        "Marketing",
        "Video Editing",
        "Quality Assurance",
    }, "All expected management departments participated")

    state = manager.plan_state(result.plan_id)
    _check(state is not None, "Plan state is available")
    _check(state["progress_pct"] == 100.0, "Plan state reports 100%")
    _check(state["completed_tasks"] == state["total_tasks"], "Plan state completed count matches total")

    print("\n" + "-" * 70)
    print("Step 3: Company orchestration visibility")
    print("-" * 70)
    _check(result.company_progress["progress_pct"] == 100.0, "Company progress reports 100%")
    _check(result.company_progress["active_plans"] == 1, "Company sees one active plan")
    _check(result.health_state["active_plans"] == 1, "Health sees one active plan")
    _check(result.health_state["blocked_tasks"] == 0, "Health sees no blocked tasks")
    _check(result.health_state["has_feedback"], "Health consumed DM feedback")
    _check(result.health_state["has_history"], "Health consumed historical learning")
    _check(result.health_state["has_predictions"], "Health consumed predictions")
    _check(len(company.employees()) == 4, "Four production employees registered in runtime")
    _check(len(company.tasks()) >= result.total_tasks, "Company runtime received managed tasks")

    print("\n" + "-" * 70)
    print("Step 4: Observability and events")
    print("-" * 70)
    snapshot = observer.snapshot
    _check(snapshot.script_department.successful_productions >= 1, "Script production observed")
    _check(snapshot.audio_department.successful_productions >= 1, "Audio production observed")
    _check(snapshot.image_department.successful_productions >= 1, "Image production observed")
    _check(snapshot.video_department.successful_productions >= 1, "Video production observed")

    events = event_bus.events()
    _check(len([e for e in events if isinstance(e, PlanReceived)]) == 1, "PlanReceived event published")
    _check(len([e for e in events if isinstance(e, TasksDecomposed)]) == 1, "TasksDecomposed event published")
    _check(len([e for e in events if isinstance(e, TaskAssigned)]) == result.total_tasks, "TaskAssigned events match task count")
    _check(len([e for e in events if isinstance(e, TaskCompleted)]) == result.total_tasks, "TaskCompleted events match task count")

    print("\n" + "-" * 70)
    print("Managed Package")
    print("-" * 70)
    print(f"plan_id: {result.plan_id}")
    print(f"package_id: {package.package_id}")
    print(f"tasks: {result.completed_tasks}/{result.total_tasks}")
    print(f"progress: {result.progress_pct}%")
    print(f"health_success_rate: {result.health_state['success_rate']}")

    print(f"\n{'=' * 70}")
    print(f"All {_ASSERTION_COUNTER} assertions passed.")
    print(f"{'=' * 70}")


if __name__ == "__main__":
    main()
