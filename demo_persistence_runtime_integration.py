"""Demo: PersistenceRuntime integration with stateful runtimes.

Covers auto-save after mutations for WorkflowRuntime, SkillRuntime,
KnowledgeRuntime and CompanyTaskRuntime, plus cross-cutting operations.

60+ scenarios verifying:
- Persistence enabled: auto-save after each mutation
- Persistence disabled: identical behavior (no files created)
- Save, load, exists, delete round-trips
- clean_domain, storage_info, export/import
- Determinism
- Full pipeline (Workflow -> Company -> Skill -> Knowledge)
"""

from __future__ import annotations

import json
import time
from dataclasses import dataclass
from typing import Any
from pathlib import Path
from uuid import UUID, uuid4

from core.company.runtime import CompanyTaskRuntime
from core.departments.runtime import DepartmentRuntime
from core.employees import Employee
from core.events.bus import EventBus
from core.knowledge.runtime import KnowledgeRuntime, KnowledgeType
from core.orchestrator.runtime import OrchestratorRuntime
from core.persistence.runtime import PersistenceRuntime
from core.results.runtime import ResultRuntime, ResultRuntimeState
from core.runtime import CompanyRuntime
from core.skills.foundation import SkillRecord, SkillSnapshot
from core.skills.models import SkillLevel
from core.skills.runtime import SkillRuntime
from core.tasks import Task
from core.tasks.runtime import TaskRuntime
from core.workflow.foundation import (
    WorkflowDefinition,
    WorkflowExecution,
    WorkflowRuntime as FoundationWorkflowRuntime,
    WorkflowStep,
)
from core.workflows import Workflow
from core.workflows.runtime import WorkflowRuntime, WorkflowRuntimeState

STORAGE = Path("storage")
TEST_DOMAINS = {"workflow", "skill", "knowledge", "company_task"}

passed = 0
failed = 0


def _clean_test_domains() -> None:
    for d in TEST_DOMAINS:
        PersistenceRuntime.clean_domain(d)


def _count_files(domain: str) -> int:
    dp = STORAGE / domain
    if not dp.exists():
        return 0
    return len(list(dp.glob("*.json")))


def _file_exists(domain: str, sid: str | UUID) -> bool:
    return (STORAGE / domain / f"{sid}.json").exists()


def check(name: str, condition: bool, detail: str = "") -> None:
    global passed, failed
    if condition:
        passed += 1
        status = "PASS"
    else:
        failed += 1
        status = "FAIL"
    print(f"[{status}] {name:50s} | {detail}")


def summary() -> None:
    total = passed + failed
    print(f"\n{'=' * 70}")
    print(f"Total: {passed}/{total} passed, {failed} failed")
    print(f"{'=' * 70}")


# ==================================================================
# Shared setup — base runtimes
# ==================================================================

event_bus = EventBus()
company = CompanyRuntime(event_bus)
department_runtime = DepartmentRuntime(company, event_bus)
orchestrator = OrchestratorRuntime(company, department_runtime, event_bus)
task_runtime = TaskRuntime(company, orchestrator, event_bus)

company.initialize_company()
department = department_runtime.create_department("Engineering")
dept_id = department.department_id
emp = company.register_employee(Employee())
department_runtime.register_employee(dept_id, emp)

# ResultRuntime needs a WorkflowRuntime — create a base one
wr_base = WorkflowRuntime(company, orchestrator, task_runtime, event_bus, persistence_runtime=None)
result_runtime = ResultRuntime(wr_base, event_bus)
knowledge_rt = KnowledgeRuntime(result_runtime, event_bus)
skill_rt = SkillRuntime(knowledge_rt, event_bus)


def _create_approved_result(wf_name: str, task_name: str) -> Any:
    """Helper: create a workflow + task, complete, and return an approved result."""
    wf = Workflow(name=wf_name)
    wf.id = uuid4()
    wr_base.register_workflow(wf)
    t = Task(name=task_name)
    t.id = uuid4()
    task_runtime.register_task(t)
    wr_base.add_task(wf.id, t.id)
    wr_base.start(wf.id)
    wr_base.complete_task(wf.id, t.id)
    rs = result_runtime.create_from_workflow(wf.id, t.id)
    result_runtime.approve(rs.result_id)
    return rs


_clean_test_domains()


# ==================================================================
# 1: WorkflowRuntime — no persistence (backward compat)
# ==================================================================
print("\n" + "=" * 70)
print("Section 1: WorkflowRuntime — no persistence")
print("=" * 70)

wr_no = WorkflowRuntime(company, orchestrator, task_runtime, event_bus, persistence_runtime=None)
wf = Workflow(name="TestWF", description="Compat test")
wf.id = uuid4()

snap = wr_no.register_workflow(wf)
check("register_workflow returns snapshot", snap is not None, "")

ta = Task(name="Task A")
ta.id = uuid4()
task_runtime.register_task(ta)
snap = wr_no.add_task(wf.id, ta.id)
check("add_task adds task_id", ta.id in snap.task_ids, f"ids={snap.task_ids}")

tb = Task(name="Task B")
tb.id = uuid4()
task_runtime.register_task(tb)
wr_no.add_task(wf.id, tb.id)
wr_no.add_dependency(wf.id, tb.id, ta.id)
check("add_dependency creates edge", wr_no.validate_dependency(wf.id, tb.id, ta.id), "")

wr_no.remove_dependency(wf.id, tb.id, ta.id)
check("remove_dependency removes edge", not wr_no.validate_dependency(wf.id, tb.id, ta.id), "")

wr_no.start(wf.id)
check("start runs workflow", wr_no._workflows[wf.id].state in (WorkflowRuntimeState.RUNNING, WorkflowRuntimeState.WAITING), f"state={wr_no._workflows[wf.id].state}")

task_runtime.complete(ta.id)
snap = wr_no.complete_task(wf.id, ta.id)
check("complete_task updates progress", snap.progress > 0, f"progress={snap.progress}")

fd = FoundationWorkflowRuntime.create_definition(
    name="FW",
    steps=[WorkflowStep(step_id=uuid4(), name="S1"), WorkflowStep(step_id=uuid4(), name="S2")],
)
snap_pd = wr_no.promote_definition(fd)
check("promote_definition returns snapshot", snap_pd is not None, "")

fe = FoundationWorkflowRuntime.start_execution(fd)
snap_pe = wr_no.promote_execution(fd.workflow_id, fe)
check("promote_execution returns snapshot", snap_pe is not None, "")

check("No files written without persistence", _count_files("workflow") == 0, "clean")


# ==================================================================
# 2: WorkflowRuntime — with persistence
# ==================================================================
print("\n" + "=" * 70)
print("Section 2: WorkflowRuntime — with persistence")
print("=" * 70)

PersistenceRuntime.clean_domain("workflow")
wr_per = WorkflowRuntime(company, orchestrator, task_runtime, event_bus, persistence_runtime=PersistenceRuntime)

wf2 = Workflow(name="PerWF")
wf2.id = uuid4()
wr_per.register_workflow(wf2)
check("register_workflow saves", _file_exists("workflow", wf2.id), f"id={wf2.id}")

tc = Task(name="Task C")
tc.id = uuid4()
task_runtime.register_task(tc)
wr_per.add_task(wf2.id, tc.id)
check("add_task saves", _file_exists("workflow", wf2.id), "")

td = Task(name="Task D")
td.id = uuid4()
task_runtime.register_task(td)
wr_per.add_task(wf2.id, td.id)
wr_per.add_dependency(wf2.id, td.id, tc.id)
check("add_dependency saves", _file_exists("workflow", wf2.id), "")

wr_per.remove_dependency(wf2.id, td.id, tc.id)
check("remove_dependency saves", _file_exists("workflow", wf2.id), "")

wr_per.start(wf2.id)
check("start saves", _file_exists("workflow", wf2.id), "")

task_runtime.complete(tc.id)
wr_per.complete_task(wf2.id, tc.id)
check("complete_task saves", _file_exists("workflow", wf2.id), "")

fd2 = FoundationWorkflowRuntime.create_definition(
    name="PerFW",
    steps=[WorkflowStep(step_id=uuid4(), name="P1")],
)
wr_per.promote_definition(fd2)
check("promote_definition saves", _file_exists("workflow", fd2.workflow_id), f"id={fd2.workflow_id}")

fe2 = FoundationWorkflowRuntime.start_execution(fd2)
wr_per.promote_execution(fd2.workflow_id, fe2)
check("promote_execution saves", _file_exists("workflow", fd2.workflow_id), "")

# load round-trip
lr = PersistenceRuntime.load_snapshot("workflow", wf2.id)
check("load_snapshot restores", lr.success, f"type={type(lr.snapshot).__name__}")
if lr.success:
    check("  correct workflow_id", str(lr.snapshot.workflow_id) == str(wf2.id), "")
    check("  correct name", lr.snapshot.name == "PerWF", f"name={lr.snapshot.name}")

# exists
check("snapshot_exists True", PersistenceRuntime.snapshot_exists("workflow", wf2.id), "")
check("snapshot_exists False", not PersistenceRuntime.snapshot_exists("workflow", uuid4()), "")

# delete
PersistenceRuntime.delete_snapshot("workflow", wf2.id)
check("delete_snapshot removes file", not _file_exists("workflow", wf2.id), "")

# multiple snapshots
wf3 = Workflow(name="WF3"); wf3.id = uuid4()
wf4 = Workflow(name="WF4"); wf4.id = uuid4()
wr_per.register_workflow(wf3)
wr_per.register_workflow(wf4)
check("multiple snapshots on disk", _count_files("workflow") >= 2, f"count={_count_files('workflow')}")
PersistenceRuntime.delete_snapshot("workflow", wf3.id)
PersistenceRuntime.delete_snapshot("workflow", wf4.id)

# export/import
wf_e = Workflow(name="ExportWF")
wf_e.id = uuid4()
wr_per.register_workflow(wf_e)
tmp = STORAGE / "_tmp_exp" / f"{wf_e.id}.json"
tmp.parent.mkdir(parents=True, exist_ok=True)
er = PersistenceRuntime.export_json(wr_per._workflows[wf_e.id], tmp, domain="workflow", snapshot_id=wf_e.id)
check("export_json writes file", er.success and tmp.exists(), f"path={tmp}")
ir = PersistenceRuntime.import_json(tmp)
check("import_json reads file", ir.success, "")
tmp.unlink(missing_ok=True)
if tmp.parent.exists(): tmp.parent.rmdir()

PersistenceRuntime.delete_snapshot("workflow", wf_e.id)

# import missing file
im = PersistenceRuntime.import_json(STORAGE / "_nosuch" / "x.json")
check("import_json missing fails", not im.success, "expected failure")


# ==================================================================
# 3: SkillRuntime — no persistence
# ==================================================================
print("\n" + "=" * 70)
print("Section 3: SkillRuntime — no persistence")
print("=" * 70)

sr_no = SkillRuntime(knowledge_rt, event_bus, persistence_runtime=None)

rec1 = SkillRecord(skill_id=uuid4(), skill_name="S1", description="", recommendation_id=uuid4(), level=1, experience_points=10, created_at=time.time(), metadata={})
sp1 = sr_no.promote_record(rec1)
check("promote_record returns snapshot", sp1.name == "S1", f"name={sp1.name}")

sr_no.evolve(sp1.skill_id, level=SkillLevel.ADVANCED)
check("evolve updates level", sr_no._skills[sp1.skill_id].level == SkillLevel.ADVANCED, "")

ss = SkillSnapshot(skills=[SkillRecord(skill_id=uuid4(), skill_name="S2", description="", recommendation_id=uuid4(), level=1, experience_points=5, created_at=time.time(), metadata={})])
snaps = sr_no.promote_snapshot(ss)
check("promote_snapshot returns list", len(snaps) == 1, f"count={len(snaps)}")

snaps2 = sr_no.create_from_foundation(SkillSnapshot(skills=[SkillRecord(skill_id=uuid4(), skill_name="S3", description="", recommendation_id=uuid4(), level=2, experience_points=20, created_at=time.time(), metadata={})]))
check("create_from_foundation returns list", len(snaps2) == 1, f"count={len(snaps2)}")

check("No files without persistence", _count_files("skill") == 0, "clean")


# ==================================================================
# 4: SkillRuntime — with persistence
# ==================================================================
print("\n" + "=" * 70)
print("Section 4: SkillRuntime — with persistence")
print("=" * 70)

PersistenceRuntime.clean_domain("skill")
sr_per = SkillRuntime(knowledge_rt, event_bus, persistence_runtime=PersistenceRuntime)

rec_p1 = SkillRecord(skill_id=uuid4(), skill_name="PerS1", description="", recommendation_id=uuid4(), level=2, experience_points=100, created_at=time.time(), metadata={})
sr_per.promote_record(rec_p1)
check("promote_record saves", _file_exists("skill", rec_p1.skill_id), f"id={rec_p1.skill_id}")

lr_s = PersistenceRuntime.load_snapshot("skill", rec_p1.skill_id)
check("load_snapshot restores skill", lr_s.success, f"type={type(lr_s.snapshot).__name__}")
if lr_s.success:
    check("  correct name", lr_s.snapshot.name == "PerS1", f"name={lr_s.snapshot.name}")

ev_id = uuid4()
sr_per.promote_record(SkillRecord(skill_id=ev_id, skill_name="Evolve", description="", recommendation_id=uuid4(), level=1, experience_points=5, created_at=time.time(), metadata={}))
sr_per.evolve(ev_id, level=SkillLevel.INTERMEDIATE)
check("evolve saves", _file_exists("skill", ev_id), "")

sr_per.promote_snapshot(SkillSnapshot(skills=[SkillRecord(skill_id=uuid4(), skill_name="Batch", description="", recommendation_id=uuid4(), level=1, experience_points=3, created_at=time.time(), metadata={})]))
check("promote_snapshot saves", _count_files("skill") >= 3, f"count={_count_files('skill')}")

check("snapshot_exists True", PersistenceRuntime.snapshot_exists("skill", rec_p1.skill_id), "")
check("snapshot_exists False", not PersistenceRuntime.snapshot_exists("skill", uuid4()), "")

PersistenceRuntime.delete_snapshot("skill", rec_p1.skill_id)
check("delete_snapshot", not _file_exists("skill", rec_p1.skill_id), "")


# ==================================================================
# 5: KnowledgeRuntime — no persistence
# ==================================================================
print("\n" + "=" * 70)
print("Section 5: KnowledgeRuntime — no persistence")
print("=" * 70)

kr_no = KnowledgeRuntime(result_runtime, event_bus, persistence_runtime=None)
rs_k = _create_approved_result("KRNoWF", "KRNoTask")
k_snap = kr_no.create_from_result(rs_k.result_id)
check("create_from_result returns snapshot", k_snap.key.startswith("knowledge:"), f"key={k_snap.key}")

kr_no.validate(k_snap.knowledge_id)
k_pub = kr_no.publish(k_snap.knowledge_id)
check("publish transitions to published", k_pub.state.value == "published", f"state={k_pub.state}")

check("No files without persistence", _count_files("knowledge") == 0, "clean")


# ==================================================================
# 6: KnowledgeRuntime — with persistence
# ==================================================================
print("\n" + "=" * 70)
print("Section 6: KnowledgeRuntime — with persistence")
print("=" * 70)

PersistenceRuntime.clean_domain("knowledge")
kr_per = KnowledgeRuntime(result_runtime, event_bus, persistence_runtime=PersistenceRuntime)

rs_k2 = _create_approved_result("KRPerWF", "KRPerTask")
k_per = kr_per.create_from_result(rs_k2.result_id)
check("create_from_result saves", _file_exists("knowledge", k_per.knowledge_id), f"id={k_per.knowledge_id}")

kr_per.validate(k_per.knowledge_id)
kr_per.publish(k_per.knowledge_id)
check("publish saves", _file_exists("knowledge", k_per.knowledge_id), "")

lr_k = PersistenceRuntime.load_snapshot("knowledge", k_per.knowledge_id)
check("load_snapshot restores knowledge", lr_k.success, f"type={type(lr_k.snapshot).__name__}")
if lr_k.success:
    check("  correct key", lr_k.snapshot.key == k_per.key, f"key={lr_k.snapshot.key}")

check("snapshot_exists True", PersistenceRuntime.snapshot_exists("knowledge", k_per.knowledge_id), "")
check("snapshot_exists False", not PersistenceRuntime.snapshot_exists("knowledge", uuid4()), "")

PersistenceRuntime.delete_snapshot("knowledge", k_per.knowledge_id)
check("delete_snapshot", not _file_exists("knowledge", k_per.knowledge_id), "")


# ==================================================================
# 7: CompanyTaskRuntime — no persistence
# ==================================================================
print("\n" + "=" * 70)
print("Section 7: CompanyTaskRuntime — no persistence")
print("=" * 70)

ctr_no = CompanyTaskRuntime(company, orchestrator, skill_runtime=skill_rt, event_bus=event_bus, persistence_runtime=None)
tid = ctr_no.receive_task("Compat company task")
check("receive_task returns UUID", isinstance(tid, UUID), f"id={tid}")

ctr_no.route_task(tid, dept_id, emp.employee_id)
check("route_task updates state", ctr_no.task_state(tid) == "routed", f"state={ctr_no.task_state(tid)}")

ctr_no.complete_task(tid)
check("complete_task updates state", ctr_no.task_state(tid) == "completed", f"state={ctr_no.task_state(tid)}")

check("No files without persistence", _count_files("company_task") == 0, "clean")


# ==================================================================
# 8: CompanyTaskRuntime — with persistence
# ==================================================================
print("\n" + "=" * 70)
print("Section 8: CompanyTaskRuntime — with persistence")
print("=" * 70)

PersistenceRuntime.clean_domain("company_task")
ctr_per = CompanyTaskRuntime(company, orchestrator, skill_runtime=skill_rt, event_bus=event_bus, persistence_runtime=PersistenceRuntime)

tid_p = ctr_per.receive_task("Persist company task")
check("receive_task saves", _file_exists("company_task", tid_p), f"id={tid_p}")

ctr_per.route_task(tid_p, dept_id, emp.employee_id)
check("route_task saves", _file_exists("company_task", tid_p), "")

ctr_per.complete_task(tid_p)
check("complete_task saves", _file_exists("company_task", tid_p), "")

lr_c = PersistenceRuntime.load_snapshot("company_task", tid_p)
check("load_snapshot restores", lr_c.success, f"type={type(lr_c.snapshot).__name__}")
if lr_c.success:
    check("  correct title", lr_c.snapshot.title == "Persist company task", f"title={lr_c.snapshot.title}")
    check("  correct stage", lr_c.snapshot.stage == "completed", f"stage={lr_c.snapshot.stage}")

check("snapshot_exists True", PersistenceRuntime.snapshot_exists("company_task", tid_p), "")
check("snapshot_exists False", not PersistenceRuntime.snapshot_exists("company_task", uuid4()), "")

PersistenceRuntime.delete_snapshot("company_task", tid_p)
check("delete_snapshot", not _file_exists("company_task", tid_p), "")


# ==================================================================
# 9: Cross-cutting
# ==================================================================
print("\n" + "=" * 70)
print("Section 9: Cross-cutting operations")
print("=" * 70)

for d in TEST_DOMAINS:
    PersistenceRuntime.clean_domain(d)

wr_cc = WorkflowRuntime(company, orchestrator, task_runtime, event_bus, persistence_runtime=PersistenceRuntime)
wf_cc = Workflow(name="CCWF"); wf_cc.id = uuid4()
wr_cc.register_workflow(wf_cc)
check("4-domain: workflow saved", _file_exists("workflow", wf_cc.id), "")

sr_cc = SkillRuntime(knowledge_rt, event_bus, persistence_runtime=PersistenceRuntime)
rec_cc = SkillRecord(skill_id=uuid4(), skill_name="CCSkill", description="", recommendation_id=uuid4(), level=1, experience_points=25, created_at=time.time(), metadata={})
sr_cc.promote_record(rec_cc)
check("4-domain: skill saved", _file_exists("skill", rec_cc.skill_id), "")

kr_cc = KnowledgeRuntime(result_runtime, event_bus, persistence_runtime=PersistenceRuntime)
rs_cc = _create_approved_result("CCKnowWF", "CCKnowTask")
k_cc = kr_cc.create_from_result(rs_cc.result_id)
check("4-domain: knowledge saved", _file_exists("knowledge", k_cc.knowledge_id), "")

ctr_cc = CompanyTaskRuntime(company, orchestrator, skill_runtime=skill_rt, event_bus=event_bus, persistence_runtime=PersistenceRuntime)
tid_cc = ctr_cc.receive_task("CC company task")
check("4-domain: company_task saved", _file_exists("company_task", tid_cc), "")

# storage_info
info = PersistenceRuntime.storage_info()
check("storage_info success", info.success, "")
if info.success and info.snapshot:
    dd = {d for d, c in info.snapshot.items() if c > 0}
    check("  has workflow", "workflow" in dd, f"domains={dd}")
    check("  has skill", "skill" in dd, "")
    check("  has knowledge", "knowledge" in dd, "")
    check("  has company_task", "company_task" in dd, "")

# clean_domain all
for d in TEST_DOMAINS:
    PersistenceRuntime.clean_domain(d)
    check(f"clean_domain {d}", _count_files(d) == 0, "")

rc = PersistenceRuntime.clean_domain("nonexistent_domain")
check("clean_domain idempotent", rc.success, "")

# Determinism (hash-based for types without UUID)
@dataclass(frozen=True, slots=True)
class SimpleSnap:
    value: str

s1 = SimpleSnap(value="det")
s2 = SimpleSnap(value="det")
r1 = PersistenceRuntime.save_snapshot(s1, "_det")
r2 = PersistenceRuntime.save_snapshot(s2, "_det")
check("determinism: same hash ID", r1.snapshot.snapshot_id == r2.snapshot.snapshot_id, f"id={r1.snapshot.snapshot_id}")
PersistenceRuntime.clean_domain("_det")

# Determinism with UUID (different UUIDs → different IDs)
wf_d1 = Workflow(name="Det1"); wf_d1.id = uuid4()
wf_d2 = Workflow(name="Det2"); wf_d2.id = uuid4()
wr_cc.register_workflow(wf_d1)
wr_cc.register_workflow(wf_d2)
r_d1 = PersistenceRuntime.save_snapshot(wr_cc._workflows[wf_d1.id], "_det_wf", wf_d1.id)
r_d2 = PersistenceRuntime.save_snapshot(wr_cc._workflows[wf_d2.id], "_det_wf", wf_d2.id)
check("determinism: UUIDs differ", r_d1.snapshot.snapshot_id != r_d2.snapshot.snapshot_id, "different IDs")
PersistenceRuntime.clean_domain("_det_wf")

for d in TEST_DOMAINS:
    PersistenceRuntime.clean_domain(d)


# ==================================================================
# 10: Pipeline — Workflow → Company → Skill → Knowledge
# ==================================================================
print("\n" + "=" * 70)
print("Section 10: Pipeline — Workflow -> Company -> Skill -> Knowledge")
print("=" * 70)

for d in TEST_DOMAINS:
    PersistenceRuntime.clean_domain(d)

wr_p = WorkflowRuntime(company, orchestrator, task_runtime, event_bus, persistence_runtime=PersistenceRuntime)
kr_p = KnowledgeRuntime(result_runtime, event_bus, persistence_runtime=PersistenceRuntime)
sr_p = SkillRuntime(knowledge_rt, event_bus, persistence_runtime=PersistenceRuntime)
ctr_p = CompanyTaskRuntime(company, orchestrator, skill_runtime=sr_p, event_bus=event_bus, persistence_runtime=PersistenceRuntime)

# Workflow
wf_p = Workflow(name="PipeWF"); wf_p.id = uuid4()
wr_p.register_workflow(wf_p)
check("Pipe: workflow saved", _file_exists("workflow", wf_p.id), "")

# Company
tid_p = ctr_p.receive_task("Pipe company task")
check("Pipe: company saved", _file_exists("company_task", tid_p), "")
ctr_p.route_task(tid_p, dept_id, emp.employee_id)
check("Pipe: company routed saved", _file_exists("company_task", tid_p), "")
ctr_p.complete_task(tid_p)
check("Pipe: company completed saved", _file_exists("company_task", tid_p), "")

# Knowledge
rs_p = _create_approved_result("PipeKnowWF", "PipeKnowTask")
k_p = kr_p.create_from_result(rs_p.result_id)
check("Pipe: knowledge saved", _file_exists("knowledge", k_p.knowledge_id), "")
kr_p.validate(k_p.knowledge_id)
kr_p.publish(k_p.knowledge_id)
check("Pipe: knowledge published saved", _file_exists("knowledge", k_p.knowledge_id), "")

# Skill
rec_p = SkillRecord(skill_id=uuid4(), skill_name="PipeSkill", description="", recommendation_id=uuid4(), level=2, experience_points=150, created_at=time.time(), metadata={})
sr_p.promote_record(rec_p)
check("Pipe: skill saved", _file_exists("skill", rec_p.skill_id), "")

# storage_info shows all 4
info_p = PersistenceRuntime.storage_info()
if info_p.success and info_p.snapshot:
    dp = {d for d, c in info_p.snapshot.items() if c > 0}
    check("Pipe: all 4 domains present", {"workflow", "skill", "knowledge", "company_task"}.issubset(dp), f"domains={dp}")

for d in TEST_DOMAINS:
    PersistenceRuntime.clean_domain(d)


# ==================================================================
# SUMMARY
# ==================================================================
summary()
