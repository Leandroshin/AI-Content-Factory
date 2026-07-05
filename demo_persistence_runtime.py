"""Demo: PersistenceRuntime — generic dataclass persistence via JSON + pathlib.

Covers save, load, delete, list, overwrite, export, import,
determinism, edge cases, and all 8 foundation domain types.

Run: python demo_persistence_runtime.py
"""

from __future__ import annotations

import shutil
import time
from pathlib import Path
from uuid import UUID, uuid4

from core.collaboration.foundation import (
    CollaborationParticipant,
    CollaborationRequest,
    CollaborationResponse,
    CollaborationSession as CollabSession,
)
from core.conversation.runtime import ConversationMessage, ConversationSession
from core.knowledge.foundation import KnowledgeRecord, KnowledgeSnapshot
from core.learning.foundation import LearningRecommendation, LearningSnapshot
from core.memory.runtime import MemoryRecord, MemorySnapshot
from core.persistence.runtime import (
    PersistenceResult,
    PersistenceRuntime,
    PersistenceSnapshot,
    PersistenceTrace,
    STORAGE_ROOT,
)
from core.skills.foundation import SkillRecord, SkillSnapshot
from core.workflow.foundation import (
    WorkflowDefinition,
    WorkflowExecution,
    WorkflowStep,
)

_total = 0
_passed = 0


def _check(condition: bool, msg: str) -> None:
    global _total, _passed
    _total += 1
    if condition:
        _passed += 1
        print(f"  [PASS] {msg}")
    else:
        print(f"  [FAIL] {msg}")


def _clean() -> None:
    if STORAGE_ROOT.exists():
        shutil.rmtree(STORAGE_ROOT)


# ------------------------------------------------------------------
# Factory helpers
# ------------------------------------------------------------------

def _make_memory(id: UUID | None = None) -> tuple[MemoryRecord, MemorySnapshot]:
    rid = id or uuid4()
    rec = MemoryRecord(memory_id=rid, source="test", category="general", content="Hello World")
    return rec, MemorySnapshot(records=(rec,), created_at=time.time())


def _make_conversation() -> tuple[ConversationSession, ConversationMessage]:
    sid = uuid4()
    msg = ConversationMessage(message_id=uuid4(), role="user", content="hi", timestamp=time.time())
    sess = ConversationSession(session_id=sid, participant_id="p1", messages=(msg,), created_at=time.time(), updated_at=time.time())
    return sess, msg


def _make_knowledge() -> tuple[KnowledgeRecord, KnowledgeSnapshot]:
    kid = uuid4()
    rec = KnowledgeRecord(knowledge_id=kid, source="test", title="Title", content="Content", confidence=0.95, timestamp=time.time())
    return rec, KnowledgeSnapshot(records=(rec,), created_at=time.time())


def _make_learning() -> tuple[LearningRecommendation, LearningSnapshot]:
    lid = uuid4()
    rec = LearningRecommendation(recommendation_id=lid, knowledge_id=uuid4(), recommendation_type="improvement", title="Learn", description="Desc", priority=5, timestamp=time.time())
    return rec, LearningSnapshot(recommendations=(rec,), created_at=time.time())


def _make_skill() -> tuple[SkillRecord, SkillSnapshot]:
    sid = uuid4()
    rec = SkillRecord(skill_id=sid, recommendation_id=uuid4(), skill_name="Python", description="Coding", level=3, experience_points=100, created_at=time.time())
    return rec, SkillSnapshot(skills=(rec,), created_at=time.time())


def _make_workflow() -> tuple[WorkflowDefinition, WorkflowStep]:
    wid = uuid4()
    step = WorkflowStep(step_id=uuid4(), name="Step1", description="First step", order=1)
    wdef = WorkflowDefinition(workflow_id=wid, name="Pipeline", steps=(step,), created_at=time.time())
    return wdef, step


def _make_execution() -> WorkflowExecution:
    return WorkflowExecution(execution_id=uuid4(), workflow_id=uuid4(), completed_step_ids=frozenset(), started_at=time.time())


def _make_collaboration() -> CollabSession:
    p = CollaborationParticipant(participant_id=uuid4(), name="Alice")
    req = CollaborationRequest(request_id=uuid4(), title="Review", description="Review PR", created_at=time.time())
    resp = CollaborationResponse(response_id=uuid4(), request_id=req.request_id, participant_id=p.participant_id, content="LGTM", decision="approved", created_at=time.time())
    return CollabSession(session_id=uuid4(), request=req, participants=(p,), responses=(resp,), status="completed", created_at=time.time())


# ==================================================================
# 1-5: PersistenceSnapshot creation and metadata
# ==================================================================

def scenario1_wrapper_created_on_save() -> None:
    _clean()
    _, snap = _make_memory()
    r = PersistenceRuntime.save_snapshot(snap, "memory")
    _check(r.success and isinstance(r.snapshot, PersistenceSnapshot),
           "save returns PersistenceSnapshot wrapper")


def scenario2_wrapper_has_metadata() -> None:
    _clean()
    _, snap = _make_memory()
    r = PersistenceRuntime.save_snapshot(snap, "memory")
    w = r.snapshot
    _check(isinstance(w.snapshot_id, str) and w.domain == "memory" and w.type_name.startswith("core.memory."),
           f"wrapper metadata: id={w.snapshot_id} domain={w.domain} type={w.type_name}")


def scenario3_wrapper_stores_data_payload() -> None:
    _clean()
    _, snap = _make_memory()
    r = PersistenceRuntime.save_snapshot(snap, "memory")
    _check(isinstance(r.snapshot.data, dict) and "records" in r.snapshot.data,
           "wrapper.data contains serialised dataclass fields")


def scenario4_persistence_result_has_path() -> None:
    _clean()
    _, snap = _make_memory()
    r = PersistenceRuntime.save_snapshot(snap, "memory")
    _check(r.path.endswith(".json"), f"result.path ends with .json ({r.path})")


def scenario5_persistence_result_has_duration() -> None:
    _clean()
    _, snap = _make_memory()
    r = PersistenceRuntime.save_snapshot(snap, "memory")
    _check(r.duration > 0, "result.duration > 0")


# ==================================================================
# 6-12: Save and overwrite
# ==================================================================

def scenario6_save_creates_file() -> None:
    _clean()
    _, snap = _make_memory()
    r = PersistenceRuntime.save_snapshot(snap, "memory")
    _check(Path(r.path).exists(), "save creates JSON file on disk")


def scenario7_save_creates_domain_dir() -> None:
    _clean()
    _, snap = _make_memory()
    PersistenceRuntime.save_snapshot(snap, "memory")
    _check((STORAGE_ROOT / "memory").is_dir(), "save creates storage/memory directory")


def scenario8_save_returns_valid_json() -> None:
    _clean()
    _, snap = _make_memory()
    import json
    r = PersistenceRuntime.save_snapshot(snap, "memory")
    with open(r.path, "r") as f:
        data = json.load(f)
    _check("snapshot_id" in data and "data" in data and "type_name" in data,
           "JSON file contains wrapper keys")


def scenario9_overwrite_same_id() -> None:
    _clean()
    rid = uuid4()
    rec, snap = _make_memory(rid)
    r1 = PersistenceRuntime.save_snapshot(snap, "memory")
    snap2 = MemorySnapshot(records=(rec,), created_at=999.0)
    r2 = PersistenceRuntime.save_snapshot(snap2, "memory")
    _check(r2.success and Path(r2.path).exists(),
           "overwrite succeeds")


def scenario10_overwrite_updates_content() -> None:
    _clean()
    rid = uuid4()
    _, snap1 = _make_memory(rid)
    PersistenceRuntime.save_snapshot(snap1, "memory")
    rec2 = MemoryRecord(memory_id=rid, source="updated", category="sys", content="Overwritten")
    snap2 = MemorySnapshot(records=(rec2,), created_at=999.0)
    PersistenceRuntime.save_snapshot(snap2, "memory")
    r = PersistenceRuntime.load_snapshot("memory", str(rid))
    _check(r.success and r.snapshot.records[0].content == "Overwritten",
           "overwrite updates content")


def scenario11_save_nonexistent_domain() -> None:
    _clean()
    _, snap = _make_memory()
    r = PersistenceRuntime.save_snapshot(snap, "nonexistent")
    _check(r.success, "save auto-creates domain directory")


def scenario12_save_empty_records() -> None:
    _clean()
    snap = MemorySnapshot(records=(), created_at=1.0)
    r = PersistenceRuntime.save_snapshot(snap, "memory")
    _check(r.success, "save with empty records tuple succeeds")


# ==================================================================
# 13-20: Load
# ==================================================================

def scenario13_load_returns_snapshot() -> None:
    _clean()
    rid = uuid4()
    _, snap = _make_memory(rid)
    PersistenceRuntime.save_snapshot(snap, "memory")
    r = PersistenceRuntime.load_snapshot("memory", str(rid))
    _check(r.success and r.snapshot is not None, "load returns snapshot on success")


def scenario14_load_preserves_type() -> None:
    _clean()
    rid = uuid4()
    _, snap = _make_memory(rid)
    PersistenceRuntime.save_snapshot(snap, "memory")
    r = PersistenceRuntime.load_snapshot("memory", str(rid))
    _check(isinstance(r.snapshot, MemorySnapshot), f"load returns correct type ({type(r.snapshot).__name__})")


def scenario15_load_preserves_content() -> None:
    _clean()
    rid = uuid4()
    rec, snap = _make_memory(rid)
    PersistenceRuntime.save_snapshot(snap, "memory")
    r = PersistenceRuntime.load_snapshot("memory", str(rid))
    _check(r.snapshot.records[0].content == "Hello World" and r.snapshot.records[0].source == "test",
           "load preserves field values")


def scenario16_load_preserves_uuid() -> None:
    _clean()
    rid = uuid4()
    _, snap = _make_memory(rid)
    PersistenceRuntime.save_snapshot(snap, "memory")
    r = PersistenceRuntime.load_snapshot("memory", str(rid))
    _check(r.snapshot.records[0].memory_id == rid and isinstance(r.snapshot.records[0].memory_id, UUID),
           "load preserves UUID values")


def scenario17_load_nonexistent() -> None:
    _clean()
    r = PersistenceRuntime.load_snapshot("memory", str(uuid4()))
    _check(not r.success and "not found" in r.error_message,
           "load nonexistent returns error")


def scenario18_load_nonexistent_domain() -> None:
    _clean()
    r = PersistenceRuntime.load_snapshot("void", str(uuid4()))
    _check(not r.success, "load nonexistent domain returns error")


def scenario19_load_nonexistent_file() -> None:
    _clean()
    (STORAGE_ROOT / "memory").mkdir(parents=True, exist_ok=True)
    r = PersistenceRuntime.load_snapshot("memory", str(uuid4()))
    _check(not r.success, "load missing file returns error")


def scenario20_load_returns_path() -> None:
    _clean()
    rid = uuid4()
    _, snap = _make_memory(rid)
    PersistenceRuntime.save_snapshot(snap, "memory")
    r = PersistenceRuntime.load_snapshot("memory", str(rid))
    _check(r.path.endswith(".json"), "load result has .json path")


# ==================================================================
# 21-25: snapshot_exists
# ==================================================================

def scenario21_exists_true() -> None:
    _clean()
    rid = uuid4()
    _, snap = _make_memory(rid)
    PersistenceRuntime.save_snapshot(snap, "memory")
    _check(PersistenceRuntime.snapshot_exists("memory", str(rid)), "exists True after save")


def scenario22_exists_false() -> None:
    _clean()
    _check(not PersistenceRuntime.snapshot_exists("memory", str(uuid4())), "exists False for missing")


def scenario23_exists_false_domain() -> None:
    _clean()
    _check(not PersistenceRuntime.snapshot_exists("void", str(uuid4())), "exists False for missing domain")


def scenario24_exists_after_delete() -> None:
    _clean()
    rid = uuid4()
    _, snap = _make_memory(rid)
    PersistenceRuntime.save_snapshot(snap, "memory")
    PersistenceRuntime.delete_snapshot("memory", str(rid))
    _check(not PersistenceRuntime.snapshot_exists("memory", str(rid)), "exists False after delete")


def scenario25_exists_with_uuid_param() -> None:
    _clean()
    rid = uuid4()
    _, snap = _make_memory(rid)
    PersistenceRuntime.save_snapshot(snap, "memory")
    _check(PersistenceRuntime.snapshot_exists("memory", rid), "exists accepts UUID parameter")


# ==================================================================
# 26-30: Delete
# ==================================================================

def scenario26_delete_removes_file() -> None:
    _clean()
    rid = uuid4()
    _, snap = _make_memory(rid)
    PersistenceRuntime.save_snapshot(snap, "memory")
    p = STORAGE_ROOT / "memory" / f"{rid}.json"
    PersistenceRuntime.delete_snapshot("memory", str(rid))
    _check(not p.exists(), "delete removes JSON file")


def scenario27_delete_returns_success() -> None:
    _clean()
    rid = uuid4()
    _, snap = _make_memory(rid)
    PersistenceRuntime.save_snapshot(snap, "memory")
    r = PersistenceRuntime.delete_snapshot("memory", str(rid))
    _check(r.success, "delete returns success")


def scenario28_delete_nonexistent_is_idempotent() -> None:
    _clean()
    r = PersistenceRuntime.delete_snapshot("memory", str(uuid4()))
    _check(r.success, "delete nonexistent is idempotent")


def scenario29_delete_returns_path() -> None:
    _clean()
    rid = uuid4()
    _, snap = _make_memory(rid)
    PersistenceRuntime.save_snapshot(snap, "memory")
    r = PersistenceRuntime.delete_snapshot("memory", str(rid))
    _check(r.path.endswith(".json"), "delete result has path")


def scenario30_delete_twice_no_error() -> None:
    _clean()
    rid = uuid4()
    _, snap = _make_memory(rid)
    PersistenceRuntime.save_snapshot(snap, "memory")
    PersistenceRuntime.delete_snapshot("memory", str(rid))
    r = PersistenceRuntime.delete_snapshot("memory", str(rid))
    _check(r.success, "double delete returns success")


# ==================================================================
# 31-35: List snapshots
# ==================================================================

def scenario31_list_empty_domain() -> None:
    _clean()
    r = PersistenceRuntime.list_snapshots("memory")
    _check(r.success and r.snapshot == [], "list empty domain returns empty list")


def scenario32_list_after_save() -> None:
    _clean()
    rid = uuid4()
    _, snap = _make_memory(rid)
    PersistenceRuntime.save_snapshot(snap, "memory")
    r = PersistenceRuntime.list_snapshots("memory")
    _check(r.success and len(r.snapshot) == 1, "list after save returns 1 entry")


def scenario33_list_metadata() -> None:
    _clean()
    rid = uuid4()
    _, snap = _make_memory(rid)
    PersistenceRuntime.save_snapshot(snap, "memory")
    r = PersistenceRuntime.list_snapshots("memory")
    entry = r.snapshot[0]
    _check(entry["snapshot_id"] == str(rid) and entry["domain"] == "memory" and "type_name" in entry,
           f"list entry metadata: {list(entry.keys())}")


def scenario34_list_multiple() -> None:
    _clean()
    for _ in range(3):
        _, snap = _make_memory()
        PersistenceRuntime.save_snapshot(snap, "memory")
    r = PersistenceRuntime.list_snapshots("memory")
    _check(len(r.snapshot) == 3, "list returns 3 entries after 3 saves")


def scenario35_list_after_delete() -> None:
    _clean()
    ids = []
    for _ in range(3):
        rid = uuid4()
        _, snap = _make_memory(rid)
        PersistenceRuntime.save_snapshot(snap, "memory")
        ids.append(rid)
    PersistenceRuntime.delete_snapshot("memory", str(ids[0]))
    r = PersistenceRuntime.list_snapshots("memory")
    _check(len(r.snapshot) == 2, "list after delete returns 2 entries")


# ==================================================================
# 36-40: Export / Import
# ==================================================================

def scenario36_export_custom_path() -> None:
    _clean()
    _, snap = _make_memory()
    p = Path("tmp_export.json")
    r = PersistenceRuntime.export_json(snap, str(p))
    _check(r.success and p.exists(), "export writes to custom path")
    p.unlink()


def scenario37_import_round_trip() -> None:
    _clean()
    _, snap = _make_memory()
    p = Path("tmp_import.json")
    PersistenceRuntime.export_json(snap, str(p))
    r = PersistenceRuntime.import_json(str(p))
    _check(r.success and isinstance(r.snapshot, MemorySnapshot) and r.snapshot.records[0].content == "Hello World",
           "import reconstructs original")
    p.unlink()


def scenario38_import_nonexistent() -> None:
    r = PersistenceRuntime.import_json("missing.json")
    _check(not r.success and "not found" in r.error_message, "import missing file returns error")


def scenario39_export_with_explicit_id() -> None:
    _clean()
    _, snap = _make_memory()
    p = Path("tmp_eid.json")
    r = PersistenceRuntime.export_json(snap, str(p), snapshot_id=uuid4())
    _check(r.success and r.snapshot.snapshot_id is not None, "export with explicit id")
    p.unlink()


def scenario40_import_preserves_nested() -> None:
    _clean()
    collab = _make_collaboration()
    p = Path("tmp_collab.json")
    PersistenceRuntime.export_json(collab, str(p))
    r = PersistenceRuntime.import_json(str(p))
    _check(r.success and isinstance(r.snapshot, CollabSession) and r.snapshot.request.title == "Review",
           "import preserves nested dataclasses")
    p.unlink()


# ==================================================================
# 41-46: Determinism
# ==================================================================

def scenario41_save_deterministic_json() -> None:
    _clean()
    import hashlib, json
    fixed_id = UUID("00000000-0000-0000-0000-000000000001")
    rec = MemoryRecord(memory_id=fixed_id, source="det", category="c", content="det")
    snap = MemorySnapshot(records=(rec,), created_at=1.0)
    PersistenceRuntime.save_snapshot(snap, "memory")

    def _payload_hash() -> str:
        p = STORAGE_ROOT / "memory" / f"{fixed_id}.json"
        data = json.loads(p.read_bytes())
        del data["saved_at"]  # timestamp changes between runs
        return hashlib.sha256(json.dumps(data, sort_keys=True).encode()).hexdigest()

    h1 = _payload_hash()
    PersistenceRuntime.delete_snapshot("memory", str(fixed_id))
    PersistenceRuntime.save_snapshot(snap, "memory")
    h2 = _payload_hash()
    _check(h1 == h2, "save deterministic: same input -> identical JSON (except saved_at)")


def scenario42_load_deterministic() -> None:
    _clean()
    rid = uuid4()
    _, snap = _make_memory(rid)
    PersistenceRuntime.save_snapshot(snap, "memory")
    r1 = PersistenceRuntime.load_snapshot("memory", str(rid))
    r2 = PersistenceRuntime.load_snapshot("memory", str(rid))
    _check(r1.snapshot == r2.snapshot, "load deterministic: same file returns equal objects")


def scenario43_list_deterministic() -> None:
    _clean()
    for _ in range(3):
        _, snap = _make_memory()
        PersistenceRuntime.save_snapshot(snap, "memory")
    r1 = PersistenceRuntime.list_snapshots("memory")
    r2 = PersistenceRuntime.list_snapshots("memory")
    ids1 = [e["snapshot_id"] for e in r1.snapshot]
    ids2 = [e["snapshot_id"] for e in r2.snapshot]
    _check(ids1 == ids2, "list deterministic: same order across calls")


def scenario44_uuid_determinism() -> None:
    _clean()
    rid = uuid4()
    _, snap = _make_memory(rid)
    PersistenceRuntime.save_snapshot(snap, "memory")
    r = PersistenceRuntime.load_snapshot("memory", str(rid))
    uid = r.snapshot.records[0].memory_id
    _check(uid == rid and isinstance(uid, UUID), f"UUID determinism: {uid} == {rid}")


def scenario45_timestamp_preserved() -> None:
    _clean()
    rid = uuid4()
    rec = MemoryRecord(memory_id=rid, source="ts", category="c", content="x")
    snap = MemorySnapshot(records=(rec,), created_at=42.5)
    PersistenceRuntime.save_snapshot(snap, "memory")
    r = PersistenceRuntime.load_snapshot("memory", str(rid))
    _check(r.snapshot.created_at == 42.5, "timestamp preserved: 42.5")


def scenario46_integer_preserved() -> None:
    _clean()
    rec = SkillRecord(skill_id=uuid4(), recommendation_id=uuid4(), skill_name="S", description="D", level=42, experience_points=999, created_at=1.0)
    snap = SkillSnapshot(skills=(rec,), created_at=1.0)
    PersistenceRuntime.save_snapshot(snap, "skills")
    r = PersistenceRuntime.load_snapshot("skills", str(rec.skill_id))
    _check(r.snapshot.skills[0].level == 42 and r.snapshot.skills[0].experience_points == 999,
           f"integer fields preserved: level={r.snapshot.skills[0].level} xp={r.snapshot.skills[0].experience_points}")


# ==================================================================
# 47-52: All 8 domain types
# ==================================================================

def scenario47_conversation_persistence() -> None:
    _clean()
    sess, _ = _make_conversation()
    r = PersistenceRuntime.save_snapshot(sess, "conversation")
    r2 = PersistenceRuntime.load_snapshot("conversation", str(sess.session_id))
    _check(r.success and r2.success and isinstance(r2.snapshot, ConversationSession) and r2.snapshot.messages[0].role == "user",
           "ConversationSession round-trip")


def scenario48_memory_persistence() -> None:
    _clean()
    rid = uuid4()
    rec = MemoryRecord(memory_id=rid, source="demo", category="test", content="persist")
    snap = MemorySnapshot(records=(rec,), created_at=1.0)
    r = PersistenceRuntime.save_snapshot(snap, "memory")
    r2 = PersistenceRuntime.load_snapshot("memory", str(rid))
    _check(r.success and r2.success and r2.snapshot.records[0].content == "persist",
           "MemorySnapshot round-trip")


def scenario49_knowledge_persistence() -> None:
    _clean()
    kid = uuid4()
    rec = KnowledgeRecord(knowledge_id=kid, source="demo", title="KT", content="KC", confidence=0.8, timestamp=1.0)
    snap = KnowledgeSnapshot(records=(rec,), created_at=1.0)
    r = PersistenceRuntime.save_snapshot(snap, "knowledge")
    r2 = PersistenceRuntime.load_snapshot("knowledge", str(kid))
    _check(r.success and r2.success and r2.snapshot.records[0].title == "KT",
           "KnowledgeSnapshot round-trip")


def scenario50_learning_persistence() -> None:
    _clean()
    lid = uuid4()
    rec = LearningRecommendation(recommendation_id=lid, knowledge_id=uuid4(), recommendation_type="opt", title="LT", description="LD", priority=3, timestamp=1.0)
    snap = LearningSnapshot(recommendations=(rec,), created_at=1.0)
    r = PersistenceRuntime.save_snapshot(snap, "learning")
    r2 = PersistenceRuntime.load_snapshot("learning", str(lid))
    _check(r.success and r2.success and r2.snapshot.recommendations[0].title == "LT",
           "LearningSnapshot round-trip")


def scenario51_skill_persistence() -> None:
    _clean()
    sid = uuid4()
    rec = SkillRecord(skill_id=sid, recommendation_id=uuid4(), skill_name="Python", description="Coding", level=3, experience_points=100, created_at=1.0)
    snap = SkillSnapshot(skills=(rec,), created_at=1.0)
    r = PersistenceRuntime.save_snapshot(snap, "skills")
    r2 = PersistenceRuntime.load_snapshot("skills", str(sid))
    _check(r.success and r2.success and r2.snapshot.skills[0].skill_name == "Python",
           "SkillSnapshot round-trip")


def scenario52_workflow_persistence() -> None:
    _clean()
    wdef, _ = _make_workflow()
    r = PersistenceRuntime.save_snapshot(wdef, "workflow")
    r2 = PersistenceRuntime.load_snapshot("workflow", str(wdef.workflow_id))
    _check(r.success and r2.success and isinstance(r2.snapshot, WorkflowDefinition) and r2.snapshot.name == "Pipeline",
           "WorkflowDefinition round-trip")


def scenario53_execution_with_frozenset() -> None:
    _clean()
    we = _make_execution()
    r = PersistenceRuntime.save_snapshot(we, "workflow")
    r2 = PersistenceRuntime.load_snapshot("workflow", str(we.execution_id))
    loaded = r2.snapshot
    _check(r.success and r2.success and isinstance(loaded.completed_step_ids, frozenset) and len(loaded.completed_step_ids) == 0,
           "WorkflowExecution frozenset round-trip")


def scenario54_collaboration_persistence() -> None:
    _clean()
    collab = _make_collaboration()
    r = PersistenceRuntime.save_snapshot(collab, "collaboration")
    r2 = PersistenceRuntime.load_snapshot("collaboration", str(collab.session_id))
    _check(r.success and r2.success and isinstance(r2.snapshot, CollabSession) and r2.snapshot.request.title == "Review",
           "CollaborationSession round-trip")


# ==================================================================
# 55-60: Edge cases
# ==================================================================

def scenario55_clean_domain() -> None:
    _clean()
    for _ in range(3):
        _, snap = _make_memory()
        PersistenceRuntime.save_snapshot(snap, "memory")
    r = PersistenceRuntime.clean_domain("memory")
    _check(r.success and r.snapshot.get("deleted") == 3, f"clean domain: deleted {r.snapshot.get('deleted')}")
    _check(len(list((STORAGE_ROOT / "memory").iterdir())) == 0, "clean domain: directory empty")


def scenario56_storage_info() -> None:
    _clean()
    _, msnap = _make_memory()
    PersistenceRuntime.save_snapshot(msnap, "memory")
    krec, _ = _make_knowledge()
    PersistenceRuntime.save_snapshot(krec, "knowledge")
    r = PersistenceRuntime.storage_info()
    _check(r.success and "memory" in r.snapshot and "knowledge" in r.snapshot,
           f"storage info: {r.snapshot}")


def scenario57_save_mutable_dataclass_fails() -> None:
    _clean()
    from dataclasses import dataclass

    @dataclass
    class Mutable:
        x: int = 1

    r = PersistenceRuntime.save_snapshot(Mutable(), "test")
    _check(r.success, "save mutable dataclass (still works via fields introspection)")


def scenario58_load_corrupted_json() -> None:
    _clean()
    (STORAGE_ROOT / "memory").mkdir(parents=True, exist_ok=True)
    bad_path = STORAGE_ROOT / "memory" / "bad.json"
    bad_path.write_text("{invalid json", encoding="utf-8")
    r = PersistenceRuntime.load_snapshot("memory", "bad")
    _check(not r.success, "load corrupted JSON returns error")


def scenario59_non_json_file_skipped_in_list() -> None:
    _clean()
    (STORAGE_ROOT / "memory").mkdir(parents=True, exist_ok=True)
    (STORAGE_ROOT / "memory" / "readme.txt").write_text("hello", encoding="utf-8")
    rid = uuid4()
    _, snap = _make_memory(rid)
    PersistenceRuntime.save_snapshot(snap, "memory")
    r = PersistenceRuntime.list_snapshots("memory")
    _check(len(r.snapshot) == 1, "list skips non-JSON files")


def scenario60_id_fallback_for_domainless_type() -> None:
    _clean()
    from dataclasses import dataclass

    @dataclass(frozen=True, slots=True)
    class PlainData:
        value: str = "test"

    obj = PlainData()
    r = PersistenceRuntime.save_snapshot(obj, "generic")
    _check(r.success and r.snapshot.snapshot_id is not None,
           "save domainless type with fallback hash ID")


# ==================================================================
# Main
# ==================================================================

def main() -> None:
    global _total, _passed

    print("=" * 70)
    print("Persistence Runtime Demo -- 60 Scenarios")
    print("=" * 70)

    # 1-5: Wrapper
    print("\n--- 1-5: PersistenceSnapshot wrapper ---")
    scenario1_wrapper_created_on_save()
    scenario2_wrapper_has_metadata()
    scenario3_wrapper_stores_data_payload()
    scenario4_persistence_result_has_path()
    scenario5_persistence_result_has_duration()

    # 6-12: Save / Overwrite
    print("\n--- 6-12: Save & overwrite ---")
    scenario6_save_creates_file()
    scenario7_save_creates_domain_dir()
    scenario8_save_returns_valid_json()
    scenario9_overwrite_same_id()
    scenario10_overwrite_updates_content()
    scenario11_save_nonexistent_domain()
    scenario12_save_empty_records()

    # 13-20: Load
    print("\n--- 13-20: Load ---")
    scenario13_load_returns_snapshot()
    scenario14_load_preserves_type()
    scenario15_load_preserves_content()
    scenario16_load_preserves_uuid()
    scenario17_load_nonexistent()
    scenario18_load_nonexistent_domain()
    scenario19_load_nonexistent_file()
    scenario20_load_returns_path()

    # 21-25: Exists
    print("\n--- 21-25: Snapshot exists ---")
    scenario21_exists_true()
    scenario22_exists_false()
    scenario23_exists_false_domain()
    scenario24_exists_after_delete()
    scenario25_exists_with_uuid_param()

    # 26-30: Delete
    print("\n--- 26-30: Delete ---")
    scenario26_delete_removes_file()
    scenario27_delete_returns_success()
    scenario28_delete_nonexistent_is_idempotent()
    scenario29_delete_returns_path()
    scenario30_delete_twice_no_error()

    # 31-35: List
    print("\n--- 31-35: List snapshots ---")
    scenario31_list_empty_domain()
    scenario32_list_after_save()
    scenario33_list_metadata()
    scenario34_list_multiple()
    scenario35_list_after_delete()

    # 36-40: Export / Import
    print("\n--- 36-40: Export & import ---")
    scenario36_export_custom_path()
    scenario37_import_round_trip()
    scenario38_import_nonexistent()
    scenario39_export_with_explicit_id()
    scenario40_import_preserves_nested()

    # 41-46: Determinism
    print("\n--- 41-46: Determinism ---")
    scenario41_save_deterministic_json()
    scenario42_load_deterministic()
    scenario43_list_deterministic()
    scenario44_uuid_determinism()
    scenario45_timestamp_preserved()
    scenario46_integer_preserved()

    # 47-54: All 8 domain types
    print("\n--- 47-54: All 8 domain types ---")
    scenario47_conversation_persistence()
    scenario48_memory_persistence()
    scenario49_knowledge_persistence()
    scenario50_learning_persistence()
    scenario51_skill_persistence()
    scenario52_workflow_persistence()
    scenario53_execution_with_frozenset()
    scenario54_collaboration_persistence()

    # 55-60: Edge cases
    print("\n--- 55-60: Edge cases ---")
    scenario55_clean_domain()
    scenario56_storage_info()
    scenario57_save_mutable_dataclass_fails()
    scenario58_load_corrupted_json()
    scenario59_non_json_file_skipped_in_list()
    scenario60_id_fallback_for_domainless_type()

    # Cleanup
    _clean()

    # Summary
    print("\n" + "=" * 70)
    print(f"RESULT: {_passed}/{_total} passed")
    print("=" * 70)


if __name__ == "__main__":
    main()
