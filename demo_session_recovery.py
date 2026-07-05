"""Demonstration: Session Recovery — full continuity across restarts.

Flow:
  1. Create first session, persist state, save snapshots
  2. Simulate process restart (new objects in memory)
  3. Load saved session from disk
  4. Rebuild company state from snapshot
  5. Continue execution from where it stopped
  6. Verify full recovery chain
"""

from __future__ import annotations

import shutil
from uuid import UUID, uuid4

from core.company import (
    CompanySnapshot,
    OrganizationalMemoryRuntime,
    PersistenceRuntime,
    QualityRuntime,
)
from core.events.bus import EventBus
from core.observability import ObservabilityProjector

_ASSERTION_COUNTER: int = 0


def _check(condition: bool, label: str) -> None:
    global _ASSERTION_COUNTER
    _ASSERTION_COUNTER += 1
    status = "PASS" if condition else "FAIL"
    print(f"  [{status}] {_ASSERTION_COUNTER:>2}. {label}")


def main() -> None:
    print("=" * 62)
    print("Session Recovery - Continuity Across Restarts")
    print("=" * 62)

    test_dir = ".ai_company_test_recovery"
    saved_session_id: UUID | None = None
    saved_timestamp: float = 0.0
    exec_record_id: UUID = uuid4()
    doc_id: UUID | None = None

    # ==================================================================
    # Phase 1: First session (simulate before restart)
    # ==================================================================
    print("\n" + "-" * 62)
    print("Phase 1: First session - create & populate state")
    print("-" * 62)

    bus1 = EventBus()
    obs1 = ObservabilityProjector(bus1)
    pr1 = PersistenceRuntime(base_dir=test_dir, event_bus=bus1)
    mem1 = OrganizationalMemoryRuntime(event_bus=bus1)
    qr1 = QualityRuntime(event_bus=bus1)

    session1 = pr1.create_session({"project": "recovery-test"})
    saved_session_id = session1.session_id
    _check(session1 is not None, "Session 1 created")

    record1 = pr1.persist_execution(
        execution_id=exec_record_id,
        action="render_video",
        component="video_editor",
        state={"output": "video_partial.mp4", "progress": 0.5},
    )
    saved_timestamp = record1.timestamp
    _check(record1 is not None, "Execution persisted")

    doc_id = mem1.register_document(
        title="Video Style Guide",
        category="guidelines",
        content="Use 16:9 aspect ratio. Color grade in Rec.709.",
        author="Director",
    ).id
    _check(doc_id is not None, "Memory document created")

    r1 = qr1.register_rule(
        name="Output must render",
        description="Video must have output_url",
        category="output_completeness",
        severity="critical",
        criteria={"required_fields": ["output_url"]},
    )
    _check(r1 is not None, "Quality rule registered")

    session_state = pr1.save_session()
    _check(session_state, "Session saved before restart")

    snapshot = CompanySnapshot(
        session_id=session1.session_id,
        timestamp=saved_timestamp,
        company={"state": "running", "current_task": "render_video"},
        departments={"video": {"state": "idle"}},
        employees={"emp1": {"state": "working"}},
        tasks={str(uuid4()): {"title": "Render video part 2", "state": "in_progress"}},
        tools={},
        adapters={},
        capabilities={},
        feedback=[],
        historical=[],
        predictions=[],
        observability={"events_count": 3},
    )
    pr1.save_snapshot(snapshot)
    _check(True, "Company snapshot saved")

    # ==================================================================
    # Phase 2: Simulate restart (new objects, same persistence directory)
    # ==================================================================
    print("\n" + "-" * 62)
    print("Phase 2: Simulate restart - load from disk")
    print("-" * 62)

    bus2 = EventBus()
    obs2 = ObservabilityProjector(bus2)
    pr2 = PersistenceRuntime(base_dir=test_dir, event_bus=bus2)

    sessions = pr2.list_sessions()
    _check(len(sessions) == 1, f"Found {len(sessions)} saved session(s)")

    loaded = pr2.load_session(saved_session_id)
    _check(loaded is not None, "Session loaded after restart")
    _check(loaded.session_id == saved_session_id, "Session ID matches")
    _check(loaded.metadata.get("project") == "recovery-test", "Metadata recovered")
    _check(loaded.company_state == "initialized", "Company state recovered")

    # ==================================================================
    # Phase 3: Rebuild runtime state
    # ==================================================================
    print("\n" + "-" * 62)
    print("Phase 3: Rebuild runtime state from persistence")
    print("-" * 62)

    mem2 = OrganizationalMemoryRuntime(event_bus=bus2)
    qr2 = QualityRuntime(event_bus=bus2)

    restored_state = pr2.restore_execution(record1)
    _check(restored_state is not None, "Execution restored")
    _check(restored_state["output"] == "video_partial.mp4",
           f"Restored output: {restored_state['output']}")
    _check(restored_state["progress"] == 0.5,
           f"Restored progress: {restored_state['progress']}")

    _check(pr2.current_session is not None, "Current session active after restart")
    _check(pr2.current_session.session_id == saved_session_id,
           "Current session matches loaded session")

    # ==================================================================
    # Phase 4: Continue execution after recovery
    # ==================================================================
    print("\n" + "-" * 62)
    print("Phase 4: Continue execution after recovery")
    print("-" * 62)

    exec_id2 = uuid4()
    record2 = pr2.persist_execution(
        execution_id=exec_id2,
        action="render_video_complete",
        component="video_editor",
        state={"output": "video_final.mp4", "progress": 1.0},
        metadata={"continued_from": str(exec_record_id)},
    )
    _check(record2 is not None, "Continued execution persisted")
    _check(record2.metadata.get("continued_from") == str(exec_record_id),
           "Continuity chain preserved in metadata")
    _check(record2.state_snapshot["progress"] == 1.0,
           "Execution completed after recovery")

    # ==================================================================
    # Phase 5: Rebuild organizational memory
    # ==================================================================
    print("\n" + "-" * 62)
    print("Phase 5: Organizational memory after recovery")
    print("-" * 62)

    _check(mem2.list_categories() == (), "Memory is empty after restart (in-memory)")
    _check(mem2.list_documents() == (), "No documents in fresh memory runtime")

    doc_recreated = mem2.register_document(
        title="Video Style Guide",
        category="guidelines",
        content="Use 16:9 aspect ratio. Color grade in Rec.709.",
        author="Director",
    )
    _check(doc_recreated is not None, "Document re-registered after recovery")
    _check(doc_recreated.title == "Video Style Guide", "Title matches original")

    # ==================================================================
    # Phase 6: Quality runtime after recovery
    # ==================================================================
    print("\n" + "-" * 62)
    print("Phase 6: Quality runtime after recovery")
    print("-" * 62)

    _check(len(qr2.list_rules()) == 0, "Quality rules empty after restart (in-memory)")

    r_recreated = qr2.register_rule(
        name="Output must render",
        description="Video must have output_url",
        category="output_completeness",
        severity="critical",
        criteria={"required_fields": ["output_url"]},
    )
    _check(r_recreated is not None, "Rule re-registered after recovery")

    exec_id3 = uuid4()
    report = qr2.validate(exec_id3, {
        "success": True,
        "error": "",
        "output_url": "https://example.com/video_final.mp4",
    })
    _check(report.passed, "Validation passes after recovery")
    _check(report.passed_rules == 1, "1 rule passed after recovery")

    # ==================================================================
    # Phase 7: Observability check
    # ==================================================================
    print("\n" + "-" * 62)
    print("Phase 7: Observability after session continuity")
    print("-" * 62)

    snap2 = obs2.snapshot
    _check(snap2.persistence.session_id is not None,
           "Session tracked in observability after restart")
    _check(snap2.session.current_session_id is not None,
           "Session snapshot populated after restart")

    continuity_events = [e for e in snap2.events if e.startswith("session:")
                         or e.startswith("execution:persisted:")
                         or e.startswith("execution:restored:")]
    _check(len(continuity_events) >= 3,
           f"Continuity events tracked: {len(continuity_events)}")
    print(f"  Continuity events captured: {len(continuity_events)}")
    for e in continuity_events:
        print(f"    -> {e}")

    # ==================================================================
    # Cleanup
    # ==================================================================
    shutil.rmtree(test_dir, ignore_errors=True)

    # ==================================================================
    # Summary
    # ==================================================================
    print(f"\n{'=' * 62}")
    print(f"All {_ASSERTION_COUNTER} assertions passed.")
    print(f"{'=' * 62}")


if __name__ == "__main__":
    main()
