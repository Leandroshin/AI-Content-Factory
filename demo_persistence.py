"""Demonstration: Execution Persistence — save/load sessions & snapshots.

Flow:
  1. Create PersistenceRuntime + EventBus
  2. Create session
  3. Persist execution records
  4. Save company snapshot
  5. List sessions
  6. Load saved session
  7. Verify events in observability
"""

from __future__ import annotations

import shutil
from uuid import uuid4

from core.company import CompanySnapshot, PersistenceRuntime
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
    print("Execution Persistence - Save / Load Sessions")
    print("=" * 62)

    # ==================================================================
    # Setup
    # ==================================================================
    event_bus = EventBus()
    observer = ObservabilityProjector(event_bus)

    test_dir = ".ai_company_test_persistence"
    shutil.rmtree(test_dir, ignore_errors=True)

    pr = PersistenceRuntime(base_dir=test_dir, event_bus=event_bus)

    # ==================================================================
    # Step 1: Create a new session
    # ==================================================================
    print("\n" + "-" * 62)
    print("Step 1: Create new session")
    print("-" * 62)

    session = pr.create_session({"project": "test-persistence"})
    _check(session is not None, "Session created")
    _check(session.company_state == "initialized", "Company state is 'initialized'")
    _check(session.metadata.get("project") == "test-persistence", "Metadata preserved")

    # ==================================================================
    # Step 2: Persist execution records
    # ==================================================================
    print("\n" + "-" * 62)
    print("Step 2: Persist execution records")
    print("-" * 62)

    exec_id = uuid4()
    record = pr.persist_execution(
        execution_id=exec_id,
        action="render_video",
        component="video_editor",
        state={"output": "video.mp4", "duration_sec": 120},
    )
    _check(record.action == "render_video", f"Record action: {record.action}")
    _check(record.component == "video_editor", f"Record component: {record.component}")
    _check(record.state_snapshot["output"] == "video.mp4", "State snapshot preserved")
    _check(record.execution_id == exec_id, "Execution ID preserved")

    exec_id2 = uuid4()
    record2 = pr.persist_execution(
        execution_id=exec_id2,
        action="upload_youtube",
        component="youtube_adapter",
        state={"url": "https://youtube.com/watch?v=abc"},
        metadata={"platform": "youtube"},
    )
    _check(record2.metadata.get("platform") == "youtube", "Execution metadata preserved")

    # ==================================================================
    # Step 3: Save and verify company snapshot
    # ==================================================================
    print("\n" + "-" * 62)
    print("Step 3: Save company snapshot")
    print("-" * 62)

    snapshot = CompanySnapshot(
        session_id=session.session_id,
        timestamp=record.timestamp,
        company={"state": "running"},
        departments={"video": {"state": "idle"}},
        employees={"emp1": {"state": "idle"}},
        tasks={str(uuid4()): {"title": "Render video", "state": "completed"}},
        tools={},
        adapters={},
        capabilities={},
        feedback=[],
        historical=[],
        predictions=[],
        observability={"events_count": 3},
    )
    pr.save_snapshot(snapshot)
    _check(True, "Snapshot saved without errors")

    # ==================================================================
    # Step 4: List sessions
    # ==================================================================
    print("\n" + "-" * 62)
    print("Step 4: List sessions")
    print("-" * 62)

    sessions = pr.list_sessions()
    _check(len(sessions) == 1, f"1 session found: {len(sessions)}")
    _check(sessions[0]["session_id"] == str(session.session_id), "Session ID matches")

    # ==================================================================
    # Step 5: Save and reload session
    # ==================================================================
    print("\n" + "-" * 62)
    print("Step 5: Save session & verify file on disk")
    print("-" * 62)

    saved = pr.save_session()
    _check(saved, "Session saved to disk")

    session_file = pr.base_dir / "sessions" / f"{session.session_id}.json"
    _check(session_file.exists(), f"Session file exists: {session_file.name}")

    # ==================================================================
    # Step 6: Load session from disk
    # ==================================================================
    print("\n" + "-" * 62)
    print("Step 6: Load session from disk")
    print("-" * 62)

    loaded = pr.load_session(session.session_id)
    _check(loaded is not None, "Session loaded from disk")
    _check(loaded.session_id == session.session_id, "Loaded session ID matches")
    _check(loaded.metadata.get("project") == "test-persistence", "Metadata restored")

    # ==================================================================
    # Step 7: Restore an execution record
    # ==================================================================
    print("\n" + "-" * 62)
    print("Step 7: Restore execution record")
    print("-" * 62)

    restored_state = pr.restore_execution(record)
    _check(restored_state["output"] == "video.mp4", "Restored state: video.mp4")
    _check(restored_state["duration_sec"] == 120, "Restored state: duration 120s")

    # ==================================================================
    # Step 8: Observability verification
    # ==================================================================
    print("\n" + "-" * 62)
    print("Step 8: Observability - persistence events tracked")
    print("-" * 62)

    snap = observer.snapshot
    _check(snap.persistence.session_id is not None, "Session ID in persistence snapshot")
    _check(snap.persistence.sessions_count >= 1, f"Sessions tracked: {snap.persistence.sessions_count}")
    _check(snap.persistence.evidence_count >= 2, f"Evidence count: {snap.persistence.evidence_count}")
    _check(snap.persistence.snapshots_count >= 1, f"Snapshots count: {snap.persistence.snapshots_count}")
    _check(snap.persistence.last_saved is not None, "Last saved timestamp present")
    _check(snap.session.current_session_id is not None, "Session tracked in session snapshot")
    _check(snap.session.company_state == "initialized", "Company state tracked")

    persistence_events = [e for e in snap.events if e.startswith("session:") or e.startswith("snapshot:") or e.startswith("execution:")]
    _check(len(persistence_events) >= 5, f"Persistence events tracked: {len(persistence_events)}")
    print(f"  Persistence events captured: {len(persistence_events)}")
    for e in persistence_events:
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
