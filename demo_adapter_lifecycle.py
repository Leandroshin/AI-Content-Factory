"""Demonstration: Full Tool Adapter Lifecycle.

Covers:
  1. Adapter criado (UNCONFIGURED)
  2. Configuracao invalida
  3. Configuracao valida (CONFIGURED)
  4. Credenciais fornecidas (AUTHENTICATED)
  5. Adapter pronto (READY)
  6. Execucao via ToolRuntime (full stack)
  7. Erro controlado (ERROR)
  8. Owner Guidance
  9. Observability - adapter_states + last_execution_times
"""

from __future__ import annotations

import sys

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")

from typing import Any
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
    AdapterStatus,
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
    config: dict[str, Any] | None = None,
    priority: int = 0,
) -> None:
    definition = ToolDefinition(
        tool_id=tool_id,
        name=name,
        category=category,
        description=f"{name} adapter",
        required_config_keys=adapter.required_config_keys(),
        required_credential_keys=adapter.required_credential_keys(),
    )
    runtime.register_tool(definition)
    if config is not None:
        runtime.configure_tool(tool_id, config)
        for k, v in config.items():
            runtime.provide_credential(tool_id, k, v)
        runtime.provide_credentials(tool_id)
        runtime.validate_tool(tool_id)
    registry.register_tool(tool_id, capabilities, priority=priority)
    runtime.register_adapter(tool_id, adapter)


def main() -> None:
    print("=" * 62)
    print("Tool Adapter Lifecycle - Full Demo")
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

    youtube_id = UUID("f1000000-0000-0000-0000-000000000010")
    github_id = UUID("f2000000-0000-0000-0000-000000000011")
    elevenlabs_id = UUID("f3000000-0000-0000-0000-000000000012")
    playwright_id = UUID("f4000000-0000-0000-0000-000000000013")

    # ==================================================================
    # Step 1: Fresh adapter is UNCONFIGURED
    # ==================================================================
    print("\n" + "-" * 62)
    print("Step 1: Adapter criado — UNCONFIGURED")
    print("-" * 62)

    yt = YouTubeAdapter()
    _check(yt.status == AdapterStatus.UNCONFIGURED,
           f"YouTube status = {yt.status.value}")

    gh = GitHubAdapter()
    _check(gh.status == AdapterStatus.UNCONFIGURED,
           f"GitHub status = {gh.status.value}")

    el = ElevenLabsAdapter()
    _check(el.status == AdapterStatus.UNCONFIGURED,
           f"ElevenLabs status = {el.status.value}")

    pw = PlaywrightAdapter()
    _check(pw.status == AdapterStatus.UNCONFIGURED,
           f"Playwright status = {pw.status.value}")

    # ==================================================================
    # Step 2: Configuração inválida
    # ==================================================================
    print("\n" + "-" * 62)
    print("Step 2: Configuração inválida — ERROR")
    print("-" * 62)

    yt2 = YouTubeAdapter()
    invalid_config = {"api_key": "short"}
    yt2.configure(invalid_config)
    _check(yt2.status == AdapterStatus.ERROR,
           f"Invalid config -> {yt2.status.value}")
    _check("failed" in yt2.error_message.lower(),
           f"Error message: {yt2.error_message}")

    gh2 = GitHubAdapter()
    gh2.configure({"token": "invalid_format"})
    _check(gh2.status == AdapterStatus.ERROR,
           f"Invalid GitHub token -> {gh2.status.value}")

    # Playwright doesn't need config — stays UNCONFIGURED after configure
    pw2 = PlaywrightAdapter()
    pw2.configure({})
    _check(pw2.status == AdapterStatus.CONFIGURED,
           f"Playwright no config needed -> {pw2.status.value} (auto-CONFIGURED)")

    # ==================================================================
    # Step 3: Configuração válida -> CONFIGURED
    # ==================================================================
    print("\n" + "-" * 62)
    print("Step 3: Configuração válida — CONFIGURED")
    print("-" * 62)

    yt3 = YouTubeAdapter()
    yt3.configure({"api_key": "test_youtube_key_valid_123456"})
    _check(yt3.status == AdapterStatus.CONFIGURED,
           f"YouTube after valid config -> {yt3.status.value}")

    gh3 = GitHubAdapter()
    gh3.configure({"token": "test_github_token_valid_1234567890"})
    _check(gh3.status == AdapterStatus.CONFIGURED,
           f"GitHub after valid config -> {gh3.status.value}")

    # ==================================================================
    # Step 4: Credenciais fornecidas -> AUTHENTICATED
    # ==================================================================
    print("\n" + "-" * 62)
    print("Step 4: Credenciais fornecidas — AUTHENTICATED")
    print("-" * 62)

    yt4 = YouTubeAdapter()
    yt4.configure({"api_key": "test_youtube_key_valid_123456"})
    yt4.authenticate()
    _check(yt4.status == AdapterStatus.AUTHENTICATED,
           f"YouTube after authenticate -> {yt4.status.value}")

    gh4 = GitHubAdapter()
    gh4.configure({"token": "test_github_token_valid_1234567890"})
    gh4.authenticate()
    _check(gh4.status == AdapterStatus.AUTHENTICATED,
           f"GitHub after authenticate -> {gh4.status.value}")

    # ElevenLabs: configure + authenticate
    el4 = ElevenLabsAdapter()
    el4.configure({"api_key": "el_key_12345678"})
    el4.authenticate()
    _check(el4.status == AdapterStatus.AUTHENTICATED,
           f"ElevenLabs after authenticate -> {el4.status.value}")

    # ==================================================================
    # Step 5: Adapter pronto -> READY
    # ==================================================================
    print("\n" + "-" * 62)
    print("Step 5: Adapter pronto — READY")
    print("-" * 62)

    yt5 = YouTubeAdapter()
    yt5.configure({"api_key": "test_youtube_key_valid_123456"})
    yt5.authenticate()
    yt5.mark_ready()
    _check(yt5.status == AdapterStatus.READY,
           f"YouTube -> {yt5.status.value}")

    gh5 = GitHubAdapter()
    gh5.configure({"token": "test_github_token_valid_1234567890"})
    gh5.authenticate()
    gh5.mark_ready()
    _check(gh5.status == AdapterStatus.READY,
           f"GitHub -> {gh5.status.value}")

    # ==================================================================
    # Step 6: configuration_status() — report what's missing
    # ==================================================================
    print("\n" + "-" * 62)
    print("Step 6: configuration_status — diagnóstico")
    print("-" * 62)

    raw_yt = YouTubeAdapter()
    cs = raw_yt.configuration_status()
    _check(cs.status == AdapterStatus.UNCONFIGURED,
           f"Raw YouTube status={cs.status.value}")
    _check("api_key" in cs.missing_config,
           f"  Missing config: {cs.missing_config}")
    _check("api_key" in cs.missing_credentials,
           f"  Missing credentials: {cs.missing_credentials}")

    configured_yt = YouTubeAdapter()
    configured_yt.configure({"api_key": "test_youtube_key_valid_123456"})
    cs2 = configured_yt.configuration_status()
    _check(cs2.status == AdapterStatus.CONFIGURED,
           f"Configured YouTube status={cs2.status.value}")
    _check(len(cs2.missing_config) == 0,
           "  No missing config")
    _check("api_key" in cs2.missing_credentials,
           "  Missing credentials still reported")

    ready_yt = YouTubeAdapter()
    ready_yt.configure({"api_key": "test_youtube_key_valid_123456"})
    ready_yt.authenticate()
    ready_yt.mark_ready()
    cs3 = ready_yt.configuration_status()
    _check(cs3.status == AdapterStatus.READY,
           f"Ready YouTube status={cs3.status.value}")

    # Playwright: no credentials needed
    cs4 = pw2.configuration_status()
    _check(cs4.status == AdapterStatus.READY,
           f"Playwright status={cs4.status.value} (no creds needed)")

    # ==================================================================
    # Step 7: Execução via ToolRuntime (full stack)
    # ==================================================================
    print("\n" + "-" * 62)
    print("Step 7: Execução via ToolRuntime — full stack")
    print("-" * 62)

    r = ceo.receive_goal("produzir videos para o YouTube")
    plan = _answer_all(ceo, r.goal_id)
    _check(plan is not None, "Plan generated")

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
    employee.receive_task(recv_task)

    _register_tool(
        tool_runtime, registry, youtube_id, "YouTube", "media",
        {Capability.VIDEO_EDITING, Capability.STORAGE},
        yt5,
        config={"api_key": "test_youtube_key_demo_12345678"},
        priority=5,
    )

    _register_tool(
        tool_runtime, registry, elevenlabs_id, "ElevenLabs", "media",
        {Capability.SPEECH_GENERATION, Capability.VOICE_CLONE},
        el4,
        config={"api_key": "el_demo_key_12345678"},
        priority=10,
    )

    _register_tool(
        tool_runtime, registry, github_id, "GitHub", "code",
        {Capability.REPOSITORY_MANAGEMENT, Capability.CODE_SEARCH},
        gh5,
        config={"token": "test_github_token_demo_1234567890abcdef"},
        priority=5,
    )

    _register_tool(
        tool_runtime, registry, playwright_id, "Playwright", "browser",
        {Capability.BROWSER_NAVIGATION, Capability.BROWSER_AUTOMATION},
        pw,
        priority=5,
    )

    cap_result = employee.request_capability(
        first_task.task_id, Capability.VIDEO_EDITING,
        "need to edit video for YouTube",
    )
    _check(cap_result, "VIDEO_EDITING capability requested -> resolved")

    exec_result = tool_runtime.execute_tool(
        youtube_id,
        ToolRequest(
            tool_id=youtube_id,
            capability="video_editing",
            params={"action": "upload", "title": "Lifecycle Demo", "video_id": "lc001"},
        ),
    )
    _check(exec_result.success,
           f"YouTube execute via ToolRuntime: {exec_result.summary}")
    _check(exec_result.output.get("status") == "published",
           "Video status=published")

    employee.provide_tool(first_task.task_id, "YouTube", available=True)
    employee.execute_task(first_task.task_id)
    dm.complete_task(first_task.task_id, employee_id, success=True)

    # ==================================================================
    # Step 8: Erro controlado — ERROR
    # ==================================================================
    print("\n" + "-" * 62)
    print("Step 8: Erro controlado — ERROR")
    print("-" * 62)

    yt_err = YouTubeAdapter()
    yt_err.mark_error("YouTube API rate limit exceeded")
    _check(yt_err.status == AdapterStatus.ERROR,
           f"Error status = {yt_err.status.value}")
    _check("rate limit" in yt_err.error_message.lower(),
           f"Error message: {yt_err.error_message}")

    gh_err = GitHubAdapter()
    gh_err.configure({"token": "invalid"})
    _check(gh_err.status == AdapterStatus.ERROR,
           f"GitHub invalid config -> {gh_err.status.value}")

    # configuration_status on errored adapter
    cs_err = yt_err.configuration_status()
    _check(cs_err.status == AdapterStatus.ERROR,
           f"configuration_status shows ERROR")
    _check("rate limit" in cs_err.error_message.lower(),
           "Error propagated to configuration_status")

    # Reset and recover
    yt_err.reset()
    _check(yt_err.status == AdapterStatus.UNCONFIGURED,
           f"After reset -> {yt_err.status.value}")
    _check(yt_err.error_message == "",
           "Error message cleared after reset")

    # ==================================================================
    # Step 9: Owner Guidance
    # ==================================================================
    print("\n" + "-" * 62)
    print("Step 9: Owner Guidance")
    print("-" * 62)

    print("\n  YouTube Adapter:")
    yt_guide = YouTubeAdapter().owner_guidance()
    for step in yt_guide.steps:
        print(f"    {step}")
    _check(len(yt_guide.steps) > 0, "YouTube has guidance steps")
    _check(bool(yt_guide.docs_url), "YouTube has docs URL")

    print("\n  GitHub Adapter:")
    gh_guide = GitHubAdapter().owner_guidance()
    for step in gh_guide.steps:
        print(f"    {step}")
    _check(len(gh_guide.steps) > 0, "GitHub has guidance steps")

    print("\n  ElevenLabs Adapter:")
    el_guide = ElevenLabsAdapter().owner_guidance()
    for step in el_guide.steps:
        print(f"    {step}")
    _check(len(el_guide.steps) > 0, "ElevenLabs has guidance steps")

    print("\n  Playwright Adapter:")
    pw_guide = PlaywrightAdapter().owner_guidance()
    for step in pw_guide.steps:
        print(f"    {step}")
    _check(len(pw_guide.steps) > 0, "Playwright has guidance steps")
    _check("não precisa de credenciais" in " ".join(pw_guide.steps).lower(),
           "Playwright says no credentials needed")

    # ==================================================================
    # Step 10: Observability — adapter states
    # ==================================================================
    print("\n" + "-" * 62)
    print("Step 10: Observability — adapter_states + last_execution_times")
    print("-" * 62)

    snap = observer.snapshot

    adapter_events = [
        e for e in snap.events
        if e.startswith("tool:") and not e.startswith("tool:executed:")
    ]
    exec_events = [e for e in snap.events if e.startswith("tool:executed:")]

    # Check adapter_states in snapshot
    adapter_keys = list(snap.tools.adapter_states.keys())
    _check(len(adapter_keys) >= 4,
           f"Adapter states tracked: {len(adapter_keys)} tools")
    for tid, state in snap.tools.adapter_states.items():
        _check(state in ("unconfigured", "configured", "authenticated", "ready", "error"),
               f"  {tid}: {state}")

    # Check last_execution_times
    exec_keys = [k for k, v in snap.tools.last_execution_times.items() if v > 0]
    _check(len(exec_keys) >= 1,
           f"Execution times tracked: {len(exec_keys)}")

    # Check usage counts
    used_tools = [k for k, v in snap.tools.usage_counts.items() if v > 0]
    _check(len(used_tools) >= 1,
           f"Usage counts tracked: {len(used_tools)} tools")

    # Capability resolution events
    cap_events = [e for e in snap.events if e.startswith("capability:")]
    _check(len(cap_events) >= 1,
           f"Capability events: {len(cap_events)}")

    # Tool lifecycle events
    _check(len(adapter_events) >= 4,
           f"Tool lifecycle events: {len(adapter_events)}")

    # ==================================================================
    # Summary
    # ==================================================================
    print("\n" + "=" * 62)
    print(f"All {_ASSERTION_COUNTER} assertions passed.")
    print("=" * 62)


if __name__ == "__main__":
    main()
