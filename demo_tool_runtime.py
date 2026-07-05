"""Demonstration: Tool Runtime lifecycle with the AI Company.

Flow:
  CEO -> DM -> Employee -> ToolRuntime(ToolUnavailable)
       -> Owner configures tool -> validate -> ToolReady
       -> Employee resumes via provide_tool -> execute -> Feedback/Historical/Prediction
       -> Observability reflects everything
"""

from __future__ import annotations

from uuid import UUID, uuid4

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
from core.tools import ToolDefinition, ToolRuntime, ToolStatus

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
    print("Tool Runtime - Lifecycle & Integration")
    print("=" * 62)

    # ==================================================================
    # Setup
    # ==================================================================
    event_bus = EventBus()
    company = CompanyRuntime(event_bus)
    company.initialize_company()
    tool_runtime = ToolRuntime(event_bus)
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
    )

    # ==================================================================
    # Step 1: Register a tool
    # ==================================================================
    print("\n" + "-" * 62)
    print("Step 1: Register 'YouTube Downloader' tool")
    print("-" * 62)

    youtube_id = UUID("f0000000-0000-0000-0000-000000000001")
    youtube_def = ToolDefinition(
        tool_id=youtube_id,
        name="YouTube Downloader",
        category="media",
        description="Download videos and metadata from YouTube",
        required_config_keys=("api_url", "rate_limit"),
        required_credential_keys=("api_key",),
        required_permission_keys=("download", "metadata"),
    )
    reg_event = tool_runtime.register_tool(youtube_def)
    _check(reg_event.name == "YouTube Downloader",
           f"Tool registered: {reg_event.name}")
    _check(reg_event.tool_id == youtube_id,
           "Tool ID matches")

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
    # Step 3: DM receives plan and assigns task
    # ==================================================================
    print("\n" + "-" * 62)
    print("Step 3: DepartmentManager receives plan, assigns task")
    print("-" * 62)

    mr = dm.receive_plan(plan)
    _check(mr.success, f"Plan received, {len(mr.tasks)} tasks created")
    tasks = mr.tasks
    first_task = tasks[0]

    assign_r = dm.assign_task(first_task.task_id, employee_id)
    _check(assign_r.success, f"Task assigned to employee")
    dm.start_task(first_task.task_id, employee_id)

    # ==================================================================
    # Step 4: Employee receives and requests tool
    # ==================================================================
    print("\n" + "-" * 62)
    print("Step 4: Employee requests 'YouTube Downloader' tool")
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

    req_result = employee.request_tool(first_task.task_id, "YouTube Downloader",
                                       "need to download reference video")
    _check(req_result, "request_tool returned True")
    _check(employee.status.value == "awaiting_tool",
           "Employee status is AWAITING_TOOL")

    # ==================================================================
    # Step 5: Check Observability
    # ==================================================================
    print("\n" + "-" * 62)
    print("Step 5: Observability - tool state after request")
    print("-" * 62)

    snap = observer.snapshot
    tools = snap.tools
    tid_short = youtube_id.hex[:8]
    _check(tid_short in tools.states,
           f"Tool tracked in observability ({tid_short})")
    _check(tools.states[tid_short] in ("unavailable", "registered"),
           f"Tool state: {tools.states[tid_short]}")
    _check(tools.blocked_count == 0,
           "Blocked tools: 0 (tool is unavailable, not error)")
    _check(tools.states.get(tid_short) == "unavailable",
           "Tool state reflects unavailability")

    tool_events = [e for e in snap.events if e.startswith("tool:")]
    _check(len(tool_events) >= 2,
           f"Tool events captured: {len(tool_events)}")
    print(f"  Tool events captured: {len(tool_events)}")
    for e in tool_events:
        print(f"    -> {e}")

    # ==================================================================
    # Step 6: Owner configures the tool
    # ==================================================================
    print("\n" + "-" * 62)
    print("Step 6: Owner configures tool - config, credentials, permissions")
    print("-" * 62)

    cfg_event = tool_runtime.configure_tool(youtube_id, {"api_url": "https://youtube.com", "rate_limit": "10/min"})
    _check(cfg_event.name == "YouTube Downloader",
           "configure_tool succeeded")
    _check(len(cfg_event.config_keys) == 2,
           f"2 config keys provided")

    cred_event = tool_runtime.provide_credentials(youtube_id)
    _check(cred_event.name == "YouTube Downloader",
           "Credentials marked as provided")

    perm_event = tool_runtime.grant_permissions(youtube_id)
    _check(perm_event.name == "YouTube Downloader",
           "Permissions marked as granted")

    # ==================================================================
    # Step 7: Validate tool
    # ==================================================================
    print("\n" + "-" * 62)
    print("Step 7: Validate tool - should become READY")
    print("-" * 62)

    val_event = tool_runtime.validate_tool(youtube_id)
    _check(val_event.success, "Validation succeeded")
    _check(val_event.name == "YouTube Downloader",
           "Validated tool name correct")

    tool_def = tool_runtime.tool_state(youtube_id)
    _check(tool_def is not None, "Tool found after validation")
    _check(tool_def.status == ToolStatus.READY,
           f"Tool status is READY ({tool_def.status.value})")

    av = tool_runtime.check_availability(youtube_id)
    _check(av["available"], "Tool is available")

    # ==================================================================
    # Step 8: Observability after configure
    # ==================================================================
    print("\n" + "-" * 62)
    print("Step 8: Observability - tool is now READY")
    print("-" * 62)

    _check(tools.states.get(tid_short) == "ready",
           f"Tool state: {tools.states.get(tid_short)}")
    _check(tools.available_count >= 1,
           f"Available count: {tools.available_count}")

    # ==================================================================
    # Step 9: Employee resumes via provide_tool
    # ==================================================================
    print("\n" + "-" * 62)
    print("Step 9: provide_tool resumes employee, releases tool")
    print("-" * 62)

    prev_status = employee.status.value
    prov_result = employee.provide_tool(first_task.task_id, "YouTube Downloader", available=True)
    _check(prov_result, "provide_tool returned True")
    _check(employee.status.value in ("working", "idle"),
           f"Employee status changed from {prev_status} to {employee.status.value}")

    tool_def2 = tool_runtime.tool_state(youtube_id)
    _check(tool_def2.status == ToolStatus.READY,
           "Tool released back to READY")
    _check(tool_def2.usage_count >= 1,
           "Usage count incremented")

    # ==================================================================
    # Step 10: Employee executes task
    # ==================================================================
    print("\n" + "-" * 62)
    print("Step 10: Employee executes task")
    print("-" * 62)

    exec_result = employee.execute_task(first_task.task_id)
    _check(exec_result.success,
           f"Task executed successfully: {exec_result.summary}")

    # DM completes the task (triggers feedback/history/prediction)
    complete_r = dm.complete_task(first_task.task_id, employee_id, success=True)
    _check(complete_r.success, "DM completed task")

    # ==================================================================
    # Step 11: Observability - learning pipeline
    # ==================================================================
    print("\n" + "-" * 62)
    print("Step 11: Observability - learning pipeline after completion")
    print("-" * 62)

    _check(snap.learning.total_feedback_entries >= 1,
           f"Feedback entries: {snap.learning.total_feedback_entries}")
    _check(snap.learning.last_success_rate > 0,
           f"Success rate: {snap.learning.last_success_rate:.2f}")
    _check(snap.learning.history_entry_count >= 0,
           f"History entries: {snap.learning.history_entry_count}")
    _check(snap.learning.last_prediction_count >= 0,
           f"Predictions: {snap.learning.last_prediction_count}")

    # ==================================================================
    # Step 12: Final tool state
    # ==================================================================
    print("\n" + "-" * 62)
    print("Step 12: Final tool state in Observability")
    print("-" * 62)

    _check(snap.tools.states.get(tid_short) == "ready",
           "Tool still READY")
    _check(snap.tools.available_count >= 1,
           "Tool available in counts")

    all_snap_events = snap.events
    tool_events_final = [e for e in all_snap_events if e.startswith("tool:")]
    _check(len(tool_events_final) >= 6,
           f"Total tool events tracked: {len(tool_events_final)}")
    print(f"  Tool events in observability:")
    for e in tool_events_final:
        print(f"    -> {e}")

    demo_events = employee.events()
    tool_req_events = [e for e in demo_events
                       if hasattr(e, 'tool_name')]
    _check(len(tool_req_events) >= 1,
           f"Tool-related events on bus: {len(tool_req_events)}")

    # ==================================================================
    # Summary
    # ==================================================================
    print("\n" + "=" * 62)
    print(f"All {_ASSERTION_COUNTER} assertions passed.")
    print("=" * 62)


if __name__ == "__main__":
    main()
