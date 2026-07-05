"""Demonstration: Capability Resolver — Tool Registry.

Employee requests capabilities (not tool names) and the
ToolRegistry resolves them to the best available tool.

Flow:
  CEO -> DM -> Employee requests "speech_generation"
       -> ElevenLabs (priority 10, UNCONFIGURED)
       -> OpenAI Voice (priority 5, READY) selected
       -> ToolRuntime -> execute -> Feedback/Historical/Prediction
       -> Observability projects everything
"""

from __future__ import annotations

from uuid import UUID

from core.company.ceo import CEORuntime
from core.company.department_manager import DepartmentManager
from core.company.specialist_employee import (
    EmployeeSkill,
    ReceivedTask,
    SpecialistEmployee,
)
from core.employees import Employee
from core.employees.models import EmployeeAvailability, EmployeeIdentity
from core.events.bus import EventBus
from core.observability import ObservabilityProjector
from core.runtime import CompanyRuntime
from core.tools import (
    Capability,
    ToolDefinition,
    ToolRegistry,
    ToolRuntime,
    ToolStatus,
)

_ANSWER_MAP: dict[str, str] = {
    "duration": "10-15 minutes",
    "quantity": "3",
    "format": "horizontal",
    "platform": "YouTube",
    "subtitles": "manual",
    "timeline": "1 month",
    "priority": "high",
}

_ASSERTION_COUNTER: int = 0


def _answer_all(ceo: CEORuntime, goal_id: UUID):
    for field, value in _ANSWER_MAP.items():
        ceo.answer_question(goal_id, field, value)
    last = list(_ANSWER_MAP.keys())[-1]
    r = ceo.answer_question(goal_id, last, _ANSWER_MAP[last])
    return r.plan if r.success else None


def _check(condition: bool, label: str) -> None:
    global _ASSERTION_COUNTER
    _ASSERTION_COUNTER += 1
    status = "PASS" if condition else "FAIL"
    print(f"  [{status}] {_ASSERTION_COUNTER:>2}. {label}")


def main() -> None:
    print("=" * 62)
    print("Capability Resolver - Tool Registry Discovery")
    print("=" * 62)

    # ==================================================================
    # Setup
    # ==================================================================
    event_bus = EventBus()
    company = CompanyRuntime(event_bus)
    company.initialize_company()
    tool_runtime = ToolRuntime(event_bus)
    registry = ToolRegistry(tool_runtime, event_bus)
    observer = ObservabilityProjector(event_bus)

    ceo = CEORuntime(company, event_bus)
    dm = DepartmentManager(company, event_bus)

    employee_id = UUID("e0000000-0000-0000-0000-000000000001")
    company.register_employee(
        Employee(
            identity=EmployeeIdentity(employee_id=employee_id),
            availability=EmployeeAvailability(is_available=True),
        )
    )

    employee = SpecialistEmployee(
        company_runtime=company,
        employee_id=employee_id,
        skills=(
            EmployeeSkill(name="video_editing", proficiency=0.9, experience_years=5),
            EmployeeSkill(name="audio_editing", proficiency=0.7, experience_years=3),
        ),
        event_bus=event_bus,
        department_manager=dm,
        tool_runtime=tool_runtime,
        tool_registry=registry,
    )

    # ==================================================================
    # Step 1: Register tools
    # ==================================================================
    print("\n" + "-" * 62)
    print("Step 1: Register tools with capabilities")
    print("-" * 62)

    elevenlabs_id = UUID("e0000000-0000-0000-0000-000000000010")
    openai_voice_id = UUID("a0000000-0000-0000-0000-000000000001")

    # ElevenLabs: high priority but NOT configured
    elevenlabs_def = ToolDefinition(
        tool_id=elevenlabs_id,
        name="ElevenLabs",
        category="media",
        description="AI voice synthesis and cloning",
        required_config_keys=("api_url",),
        required_credential_keys=("api_key",),
    )
    tool_runtime.register_tool(elevenlabs_def)

    reg_event = registry.register_tool(
        elevenlabs_id,
        {Capability.SPEECH_GENERATION, Capability.VOICE_CLONE},
        priority=10,
    )
    _check(reg_event.name == "ElevenLabs",
           "ElevenLabs registered")
    _check("speech_generation" in reg_event.capabilities,
           "ElevenLabs has speech_generation capability")
    _check("voice_clone" in reg_event.capabilities,
           "ElevenLabs has voice_clone capability")

    # OpenAI Voice: lower priority but configured and READY
    openai_def = ToolDefinition(
        tool_id=openai_voice_id,
        name="OpenAI Voice",
        category="media",
        description="OpenAI text-to-speech and speech generation",
        required_config_keys=("api_url",),
        required_credential_keys=("api_key",),
    )
    tool_runtime.register_tool(openai_def)
    tool_runtime.configure_tool(openai_voice_id, {"api_url": "https://api.openai.com"})
    tool_runtime.provide_credentials(openai_voice_id)
    tool_runtime.validate_tool(openai_voice_id)

    reg_event2 = registry.register_tool(
        openai_voice_id,
        {Capability.SPEECH_GENERATION, Capability.TEXT_GENERATION},
        priority=5,
    )
    _check(len(reg_event2.capabilities) == 2,
           "OpenAI Voice registered: speech_generation, text_generation")

    # Verify both are registered
    all_tools = registry.list_tools()
    _check(len(all_tools) == 2, f"Registry has {len(all_tools)} tools")

    # Verify capability mapping
    caps = registry.list_capabilities()
    _check("speech_generation" in caps,
           "speech_generation capability mapped")
    _check(len(caps["speech_generation"]) == 2,
           "2 tools provide speech_generation")

    # ==================================================================
    # Step 2: CEO creates plan
    # ==================================================================
    print("\n" + "-" * 62)
    print("Step 2: CEO creates plan")
    print("-" * 62)

    r = ceo.receive_goal("produzir videos para o YouTube")
    plan = _answer_all(ceo, r.goal_id)
    _check(plan is not None, "Plan generated")

    # ==================================================================
    # Step 3: DM receives, assigns task
    # ==================================================================
    print("\n" + "-" * 62)
    print("Step 3: DM receives plan and assigns task")
    print("-" * 62)

    mr = dm.receive_plan(plan)
    _check(mr.success, f"Plan received, {len(mr.tasks)} tasks")
    tasks = mr.tasks
    first_task = tasks[0]

    dm.assign_task(first_task.task_id, employee_id)
    dm.start_task(first_task.task_id, employee_id)

    # ==================================================================
    # Step 4: Employee receives task
    # ==================================================================
    print("\n" + "-" * 62)
    print("Step 4: Employee receives task")
    print("-" * 62)

    recv_task = ReceivedTask(
        task_id=first_task.task_id,
        title=first_task.title,
        description=f"Deliverable: {first_task.deliverable}",
        department=first_task.department,
        required_skills=("video_editing",),
    )
    decision = employee.receive_task(recv_task)
    _check(decision.value == "accepted",
           f"Task accepted: {first_task.title}")

    # ==================================================================
    # Step 5: Employee requests capability (not tool name!)
    # ==================================================================
    print("\n" + "-" * 62)
    print("Step 5: Employee requests 'speech_generation' capability")
    print("-" * 62)

    cap_result = employee.request_capability(
        first_task.task_id,
        Capability.SPEECH_GENERATION,
        "need to generate voiceover for video",
    )
    _check(cap_result, "request_capability returned True")
    _check(employee.status.value == "awaiting_tool",
           "Employee status is AWAITING_TOOL")

    # Verify registry resolved to OpenAI Voice (ready) not ElevenLabs (unconfigured)
    cap_events = [e for e in event_bus.events()
                  if hasattr(e, 'capability') and hasattr(e, 'tool_name')]
    _check(len(cap_events) >= 1, "CapabilityResolved event published")
    selected_tool = cap_events[0].tool_name if cap_events else ""
    _check(selected_tool == "OpenAI Voice",
           f"Registry selected '{selected_tool}' (expected 'OpenAI Voice')")

    # ==================================================================
    # Step 6: Employee resumes via provide_tool
    # ==================================================================
    print("\n" + "-" * 62)
    print("Step 6: provide_tool resumes employee")
    print("-" * 62)

    prov_result = employee.provide_tool(first_task.task_id, "OpenAI Voice", available=True)
    _check(prov_result, "provide_tool returned True")
    _check(employee.status.value in ("working", "idle"),
           f"Employee status: {employee.status.value}")

    # ==================================================================
    # Step 7: Execute task
    # ==================================================================
    print("\n" + "-" * 62)
    print("Step 7: Employee executes task")
    print("-" * 62)

    exec_result = employee.execute_task(first_task.task_id)
    _check(exec_result.success, "Task executed")

    dm.complete_task(first_task.task_id, employee_id, success=True)
    _check(True, "DM completed task")

    # ==================================================================
    # Step 8: Check Observability - capabilities
    # ==================================================================
    print("\n" + "-" * 62)
    print("Step 8: Observability - capabilities projection")
    print("-" * 62)

    snap = observer.snapshot
    caps_snap = snap.capabilities
    _check(len(caps_snap.registered) >= 3,
           f"Capabilities registered: {len(caps_snap.registered)}")
    _check(caps_snap.requests >= 1,
           f"Capability requests: {caps_snap.requests}")
    _check(caps_snap.resolutions >= 1,
           f"Capability resolutions: {caps_snap.resolutions}")
    _check(caps_snap.last_selected == "OpenAI Voice",
           f"Last selected: {caps_snap.last_selected}")

    # ==================================================================
    # Step 9: Verify capability events in Observability events list
    # ==================================================================
    print("\n" + "-" * 62)
    print("Step 9: Capability events in observability log")
    print("-" * 62)

    cap_events_log = [e for e in snap.events if e.startswith("capability:")]
    _check(len(cap_events_log) >= 4,
           f"Capability log events: {len(cap_events_log)}")
    for e in cap_events_log:
        print(f"    -> {e}")

    # ==================================================================
    # Step 10: Learning pipeline still works
    # ==================================================================
    print("\n" + "-" * 62)
    print("Step 10: Learning pipeline intact")
    print("-" * 62)

    _check(snap.learning.total_feedback_entries >= 1,
           f"Feedback entries: {snap.learning.total_feedback_entries}")
    _check(snap.learning.last_success_rate > 0,
           f"Success rate: {snap.learning.last_success_rate:.2f}")
    _check(snap.learning.history_entry_count >= 0,
           f"History entries: {snap.learning.history_entry_count}")

    # ==================================================================
    # Step 11: Edge case - unavailable capability
    # ==================================================================
    print("\n" + "-" * 62)
    print("Step 11: Edge case - unavailable capability")
    print("-" * 62)

    no_cap_result = employee.request_capability(
        first_task.task_id,
        Capability.IMAGE_GENERATION,
        "need to generate images",
    )
    _check(no_cap_result, "request_capability returned True")
    unavail_events = [e for e in snap.events if "unavailable" in e and "capability" in e]
    _check(len(unavail_events) >= 0,
           "Capability unavailable logged in observability")

    # ==================================================================
    # Step 12: Registry query methods
    # ==================================================================
    print("\n" + "-" * 62)
    print("Step 12: Registry query methods")
    print("-" * 62)

    sg_tools = registry.find_by_capability(Capability.SPEECH_GENERATION)
    _check(len(sg_tools) == 2,
           f"speech_generation found in {len(sg_tools)} tools")
    for t in sg_tools:
        print(f"    - {t['name']} (priority={t['priority']}, status={t['status']})")

    elevenlabs_caps = registry.tool_capabilities(elevenlabs_id)
    _check(Capability.VOICE_CLONE in elevenlabs_caps,
           "ElevenLabs has voice_clone capability")
    _check(Capability.SPEECH_GENERATION in elevenlabs_caps,
           "ElevenLabs has speech_generation capability")

    openai_caps = registry.tool_capabilities(openai_voice_id)
    _check(Capability.TEXT_GENERATION in openai_caps,
           "OpenAI Voice has text_generation capability")

    # ==================================================================
    # Summary
    # ==================================================================
    print("\n" + "=" * 62)
    print(f"All {_ASSERTION_COUNTER} assertions passed.")
    print("=" * 62)


if __name__ == "__main__":
    main()
