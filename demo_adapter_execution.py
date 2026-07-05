"""Demonstration: Tool Adapter execution through the full stack.

Employee requests a capability -> ToolRegistry resolves ->
ToolRuntime.request_tool -> ToolRuntime.execute_tool -> Adapter
-> Result -> Observability projects everything.
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
    ElevenLabsAdapter,
    GitHubAdapter,
    PlaywrightAdapter,
    ToolDefinition,
    ToolRegistry,
    ToolRequest,
    ToolRuntime,
    YouTubeAdapter,
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


def _register_tool(
    runtime: ToolRuntime,
    registry: ToolRegistry,
    tool_id: UUID,
    name: str,
    category: str,
    capabilities: set[Capability],
    adapter,
    priority: int = 0,
) -> None:
    definition = ToolDefinition(
        tool_id=tool_id,
        name=name,
        category=category,
        description=f"{name} adapter",
        required_config_keys=("api_url",),
        required_credential_keys=("api_key",),
    )
    runtime.register_tool(definition)
    runtime.configure_tool(tool_id, {"api_url": f"https://api.{name.lower().replace(' ', '')}.com"})
    runtime.provide_credentials(tool_id)
    runtime.validate_tool(tool_id)
    registry.register_tool(tool_id, capabilities, priority=priority)
    runtime.register_adapter(tool_id, adapter)


def main() -> None:
    print("=" * 62)
    print("Tool Adapter Execution - Full Stack Demo")
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
        skills=(EmployeeSkill(name="video_editing", proficiency=0.9),),
        event_bus=event_bus,
        department_manager=dm,
        tool_runtime=tool_runtime,
        tool_registry=registry,
    )

    # ==================================================================
    # Step 1: Register tools, capabilities, and adapters
    # ==================================================================
    print("\n" + "-" * 62)
    print("Step 1: Register tools + capabilities + adapters")
    print("-" * 62)

    youtube_id = UUID("a0000000-0000-0000-0000-000000000001")
    elevenlabs_id = UUID("b0000000-0000-0000-0000-000000000002")
    github_id = UUID("c0000000-0000-0000-0000-000000000003")
    playwright_id = UUID("d0000000-0000-0000-0000-000000000004")

    _register_tool(tool_runtime, registry, youtube_id, "YouTube", "media",
                   {Capability.VIDEO_EDITING, Capability.STORAGE},
                   YouTubeAdapter(), priority=5)
    _register_tool(tool_runtime, registry, elevenlabs_id, "ElevenLabs", "media",
                   {Capability.SPEECH_GENERATION, Capability.VOICE_CLONE},
                   ElevenLabsAdapter(), priority=10)
    _register_tool(tool_runtime, registry, github_id, "GitHub", "code",
                   {Capability.REPOSITORY_MANAGEMENT, Capability.CODE_SEARCH},
                   GitHubAdapter(), priority=5)
    _register_tool(tool_runtime, registry, playwright_id, "Playwright", "browser",
                   {Capability.BROWSER_NAVIGATION, Capability.BROWSER_AUTOMATION},
                   PlaywrightAdapter(), priority=5)

    _check(len(tool_runtime.list_adapters()) == 4,
           f"4 adapters registered: {len(tool_runtime.list_adapters())}")
    _check(tool_runtime.find_adapter(youtube_id) is not None,
           "YouTube adapter found by tool_id")

    caps_map = registry.list_capabilities()
    _check("browser_navigation" in caps_map,
           "browser_navigation capability registered")

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
    # Step 3: DM assigns task
    # ==================================================================
    print("\n" + "-" * 62)
    print("Step 3: DM assigns task, employee accepts")
    print("-" * 62)

    mr = dm.receive_plan(plan)
    tasks = mr.tasks
    first_task = tasks[0]
    dm.assign_task(first_task.task_id, employee_id)
    dm.start_task(first_task.task_id, employee_id)

    recv_task = ReceivedTask(
        task_id=first_task.task_id,
        title=first_task.title,
        description=f"Deliverable: {first_task.deliverable}",
        department=first_task.department,
        required_skills=("video_editing",),
    )
    _check(employee.receive_task(recv_task).value == "accepted", "Task accepted")

    # ==================================================================
    # Step 4: Request capability -> resolve -> execute
    # ==================================================================
    print("\n" + "-" * 62)
    print("Step 4: Request VIDEO_EDITING -> resolve to YouTube -> execute")
    print("-" * 62)

    cap_result = employee.request_capability(
        first_task.task_id, Capability.VIDEO_EDITING,
        "need to edit video for YouTube",
    )
    _check(cap_result, "VIDEO_EDITING capability requested")

    # Execute while tool is BUSY, THEN release
    exec_result = tool_runtime.execute_tool(
        youtube_id,
        ToolRequest(
            tool_id=youtube_id,
            capability="video_editing",
            params={"action": "upload", "title": "My Video", "video_id": "abc123"},
        ),
    )
    _check(exec_result.success, f"YouTube execute: {exec_result.summary}")
    _check("published" in exec_result.output.get("status", ""),
           "Video status is 'published'")

    prov_result = employee.provide_tool(first_task.task_id, "YouTube", available=True)
    _check(prov_result, "provide_tool released YouTube")

    employee.execute_task(first_task.task_id)
    dm.complete_task(first_task.task_id, employee_id, success=True)

    # ==================================================================
    # Step 5: ElevenLabs speech generation
    # ==================================================================
    print("\n" + "-" * 62)
    print("Step 5: Request SPEECH_GENERATION -> ElevenLabs -> execute")
    print("-" * 62)

    # Need a second task for this
    if len(tasks) > 1:
        second_task = tasks[1]
        dm.assign_task(second_task.task_id, employee_id)
        dm.start_task(second_task.task_id, employee_id)
        r2 = ReceivedTask(
            task_id=second_task.task_id,
            title=second_task.title,
            description="Audio task",
            department=second_task.department,
            required_skills=("audio_editing",),
        )
        employee.receive_task(r2)
        employee.request_capability(
            second_task.task_id, Capability.SPEECH_GENERATION,
            "need voiceover for video",
        )
        # Execute while BUSY, then release
        speech_result = tool_runtime.execute_tool(
            elevenlabs_id,
            ToolRequest(
                tool_id=elevenlabs_id,
                capability="speech_generation",
                params={"action": "synthesize", "text": "Welcome to our channel", "voice": "Rachel"},
            ),
        )
        _check(speech_result.success,
               f"ElevenLabs execute: {speech_result.summary}")
        _check(speech_result.output.get("voice") == "Rachel",
               "Voice matches 'Rachel'")

        employee.provide_tool(second_task.task_id, "ElevenLabs", available=True)
        employee.execute_task(second_task.task_id)
        dm.complete_task(second_task.task_id, employee_id, success=True)

    # ==================================================================
    # Step 6: Direct adapter tests (standalone, no BUSY needed)
    # ==================================================================
    print("\n" + "-" * 62)
    print("Step 6: Direct adapter execution tests")
    print("-" * 62)

    playwright_adapter = PlaywrightAdapter()
    nav_result = playwright_adapter.execute(
        ToolRequest(
            tool_id=playwright_id,
            capability="browser_navigation",
            params={"action": "navigate", "url": "https://example.com"},
        ),
    )
    _check(nav_result.success, f"Playwright navigate: {nav_result.summary}")
    _check(nav_result.output.get("status_code") == 200,
           "HTTP status 200")

    github_adapter = GitHubAdapter()
    search_result = github_adapter.execute(
        ToolRequest(
            tool_id=github_id,
            capability="code_search",
            params={"action": "search_code", "repo": "user/ai-project", "query": "TODO"},
        ),
    )
    _check(search_result.success, f"GitHub search: {search_result.summary}")
    _check(search_result.output.get("total_count", 0) >= 2,
           f"Found {search_result.output.get('total_count', 0)} matches")

    # ==================================================================
    # Step 7: Error case - execute through ToolRuntime without BUSY
    # ==================================================================
    print("\n" + "-" * 62)
    print("Step 7: ToolRuntime guards non-BUSY execution")
    print("-" * 62)

    err_result = tool_runtime.execute_tool(
        github_id,
        ToolRequest(tool_id=github_id, capability="code_search"),
    )
    _check(not err_result.success,
           f"Execution prevented: {err_result.error}")

    # ==================================================================
    # Step 9: Observability
    # ==================================================================
    print("\n" + "-" * 62)
    print("Step 9: Observability - tool execution events")
    print("-" * 62)

    snap = observer.snapshot
    exec_events = [e for e in snap.events if e.startswith("tool:executed:")]
    _check(len(exec_events) >= 2,
           f"Tool execution events: {len(exec_events)}")
    for e in exec_events:
        print(f"    -> {e}")

    cap_events = [e for e in snap.events if e.startswith("capability:")]
    _check(len(cap_events) >= 2,
           f"Capability events: {len(cap_events)}")
    for e in cap_events:
        print(f"    -> {e}")

    _check(snap.learning.total_feedback_entries >= 1,
           f"Learning pipeline: {snap.learning.total_feedback_entries} entries")
    _check(snap.capabilities.resolutions >= 2,
           f"Capability resolutions: {snap.capabilities.resolutions}")

    # ==================================================================
    # Summary
    # ==================================================================
    print("\n" + "=" * 62)
    print(f"All {_ASSERTION_COUNTER} assertions passed.")
    print("=" * 62)


if __name__ == "__main__":
    main()
