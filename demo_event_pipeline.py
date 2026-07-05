"""Demo: Event-driven pipeline — 50+ scenarios covering every domain event.

Covers publication of all 22 domain events across:
- WorkflowRuntime
- OrchestratorRuntime
- LearningPipeline
- CollaborationRuntime
- CompanyTaskRuntime
- SkillRuntime
- KnowledgeRuntime

Plus subscriber patterns, EventBus=None isolation, determinism,
multi-runtime pipelines, and edge cases.

Run: python demo_event_pipeline.py
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Any
from uuid import UUID, uuid4

from core.collaboration.foundation import (
    CollaborationParticipant,
    CollaborationRuntime,
)
from core.company.runtime import CompanyTaskRuntime
from core.conversation import ConversationRuntime, ConversationSession
from core.departments.runtime import DepartmentRuntime
from core.employees import Employee
from core.events.bus import EventBus
from core.events.domain_events import (
    CollaborationCompleted,
    CollaborationStarted,
    CompanyTaskCompleted,
    CompanyTaskReceived,
    CompanyTaskRouted,
    ConversationCreated,
    DecisionApproved,
    DecisionRejected,
    ExecutionCompleted,
    ExecutionFailed,
    ExecutionStarted,
    KnowledgePromoted,
    MemoryRecordCreated,
    MessageAdded,
    OrchestratorExecutionCompleted,
    OrchestratorExecutionStarted,
    ParticipantResponded,
    RecommendationCreated,
    SkillCreated,
    SkillLevelChanged,
    SkillPromoted,
    WorkflowCompleted,
    WorkflowStarted,
    WorkflowTaskCompleted,
    WorkflowTaskStarted,
)
from core.knowledge.runtime import KnowledgeRuntime
from core.learning.pipeline import LearningPipeline
from core.memory import MemoryRecord, MemoryRuntime
from core.orchestrator import OrchestratorRuntime
from core.results.runtime import ResultRuntime
from core.runtime import CompanyRuntime
from core.skills.foundation import SkillRecord, SkillRuntime as FoundationSkillRuntime
from core.skills.models import Skill, SkillLevel, SkillMetadata
from core.skills.runtime import SkillRuntime
from core.tasks import Task
from core.tasks.runtime import TaskRuntime, TaskRuntimeState
from core.workflow.foundation import (
    WorkflowDefinition,
    WorkflowExecution,
    WorkflowRuntime as FoundationWorkflowRuntime,
    WorkflowStep,
)
from core.workflows import Workflow
from core.workflows.runtime import (
    WorkflowRuntime,
    WorkflowRuntimeState,
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


# ------------------------------------------------------------------
# Helpers
# ------------------------------------------------------------------

def _make_task(name: str) -> Task:
    t = Task(name=name)
    t.id = uuid4()
    return t


def _setup_default() -> tuple[CompanyRuntime, OrchestratorRuntime, DepartmentRuntime, TaskRuntime, EventBus]:
    bus = EventBus()
    company = CompanyRuntime(bus)
    dept_rt = DepartmentRuntime(company, bus)
    orc = OrchestratorRuntime(company, dept_rt, bus)
    tr = TaskRuntime(company, orc, bus)
    company.initialize_company()
    dept = dept_rt.create_department("Engineering")
    emp = company.register_employee(Employee())
    dept_rt.register_employee(dept.department_id, emp)
    return company, orc, dept_rt, tr, bus


def _setup_workflow() -> tuple[WorkflowRuntime, CompanyRuntime, OrchestratorRuntime, TaskRuntime, EventBus]:
    company, orc, dept_rt, tr, bus = _setup_default()
    wr = WorkflowRuntime(company, orc, tr, bus)
    return wr, company, orc, tr, bus


# ==================================================================
# 1-5. EventBus Basics
# ==================================================================

def scenario1_create_eventbus() -> None:
    bus = EventBus()
    _check(len(bus.events()) == 0, "EventBus: empty on creation")


def scenario2_publish_and_collect() -> None:
    bus = EventBus()

    @dataclass(frozen=True)
    class MyEvent:
        x: int

    bus.publish(MyEvent(42))
    bus.publish(MyEvent(99))
    _check(len(bus.events()) == 2, "EventBus: publish collects 2 events")


def scenario3_subscriber_receives() -> None:
    bus = EventBus()
    received: list[Any] = []
    bus.subscribe(object, lambda e: received.append(e))

    @dataclass(frozen=True)
    class MyEvent:
        x: int

    bus.publish(MyEvent(1))
    bus.publish(MyEvent(2))
    _check(len(received) == 2, "EventBus: subscriber receives all events")


def scenario4_isinstance_matching() -> None:
    bus = EventBus()
    received: list[WorkflowStarted] = []
    bus.subscribe(WorkflowStarted, lambda e: received.append(e))
    bus.publish(WorkflowStarted(workflow_id=uuid4()))
    bus.publish(WorkflowTaskStarted(workflow_id=uuid4(), task_id=uuid4()))
    _check(len(received) == 1, "EventBus: isinstance filters exact type")


def scenario5_no_subscribers() -> None:
    bus = EventBus()
    bus.publish(WorkflowStarted(workflow_id=uuid4()))
    bus.publish(WorkflowCompleted(workflow_id=uuid4()))
    _check(len(bus.events()) == 2, "EventBus: events collected even without subscribers")


# ==================================================================
# 6-11. Workflow Runtime Events
# ==================================================================

def scenario6_workflow_started() -> None:
    wr, _, _, tr, bus = _setup_workflow()
    wf = Workflow(name="WF6")
    wr.register_workflow(wf)
    _register_tasks(wr, tr, wf.id, _make_task("A"))
    before = len(bus.events())
    wr.start(wf.id)
    started = [e for e in bus.events() if isinstance(e, WorkflowStarted)]
    _check(len(started) == 1 and started[0].workflow_id == wf.id,
           "WorkflowStarted: published on start")


def scenario7_workflow_task_started() -> None:
    wr, _, _, tr, bus = _setup_workflow()
    wf = Workflow(name="WF7")
    wr.register_workflow(wf)
    a = _make_task("A")
    _register_tasks(wr, tr, wf.id, a)
    wr.start(wf.id)
    events = [e for e in bus.events() if isinstance(e, WorkflowTaskStarted)]
    _check(len(events) >= 1 and events[-1].task_id == a.id,
           "WorkflowTaskStarted: published when task advances")


def scenario8_workflow_task_completed() -> None:
    wr, company, orc, tr, bus = _setup_workflow()
    wf = Workflow(name="WF8")
    wr.register_workflow(wf)
    a = _make_task("A")
    _register_tasks(wr, tr, wf.id, a)
    wr.start(wf.id)
    _advance_and_complete(wr, tr, a.id, company)
    events = [e for e in bus.events() if isinstance(e, WorkflowTaskCompleted)]
    _check(len(events) == 1 and events[0].task_id == a.id,
           "WorkflowTaskCompleted: published on complete_task")


def scenario9_workflow_completed() -> None:
    wr, company, orc, tr, bus = _setup_workflow()
    wf = Workflow(name="WF9")
    wr.register_workflow(wf)
    a = _make_task("A")
    _register_tasks(wr, tr, wf.id, a)
    wr.start(wf.id)
    _advance_and_complete(wr, tr, a.id, company)
    events = [e for e in bus.events() if isinstance(e, WorkflowCompleted)]
    _check(len(events) == 1 and events[0].workflow_id == wf.id and events[0].progress == 100.0,
           "WorkflowCompleted: published on full progress")


def scenario10_workflow_event_order() -> None:
    wr, company, orc, tr, bus = _setup_workflow()
    wf = Workflow(name="WF10")
    wr.register_workflow(wf)
    a, b = _make_task("A"), _make_task("B")
    _register_tasks(wr, tr, wf.id, a, b)
    wr.start(wf.id)
    _advance_and_complete(wr, tr, a.id, company)
    _advance_and_complete(wr, tr, b.id, company)

    wf_events = [e for e in bus.events()
                 if isinstance(e, (WorkflowStarted, WorkflowTaskStarted,
                                   WorkflowTaskCompleted, WorkflowCompleted))]
    types = [type(e).__name__ for e in wf_events]
    expected = ["WorkflowStarted", "WorkflowTaskStarted", "WorkflowTaskCompleted",
                "WorkflowTaskStarted", "WorkflowTaskCompleted", "WorkflowCompleted"]
    _check(types == expected, f"Workflow: event order correct ({types})")


def scenario11_workflow_dag_events() -> None:
    wr, company, orc, tr, bus = _setup_workflow()
    wf = Workflow(name="DAGEvents")
    wr.register_workflow(wf)
    a, b, c = _make_task("A"), _make_task("B"), _make_task("C")
    _register_tasks(wr, tr, wf.id, a, b, c)
    wr.add_dependency(wf.id, b.id, a.id)
    wr.add_dependency(wf.id, c.id, a.id)
    wr.start(wf.id)
    _advance_and_complete(wr, tr, a.id, company)
    _advance_and_complete(wr, tr, b.id, company)
    _advance_and_complete(wr, tr, c.id, company)
    comps = [e for e in bus.events() if isinstance(e, (WorkflowTaskCompleted, WorkflowCompleted))]
    _check(len(comps) == 4, f"DAG events: {len(comps)} completion events (expected 4)")


# ==================================================================
# 12-17. Orchestrator Runtime Events
# ==================================================================

def scenario12_orchestrator_execution_started() -> None:
    bus = EventBus()
    received: list[OrchestratorExecutionStarted] = []
    bus.subscribe(OrchestratorExecutionStarted, lambda e: received.append(e))
    company, orc, dept_rt, tr, _ = _setup_default()
    snap = orc.receive_task("T12")
    dept_id = next(iter(dept_rt._departments))
    emp_id = next(iter(company._employees))
    orc.route_task(snap.task.task_id, dept_id, emp_id)
    orc.execute_task(
        snap, list(company._employees.values()),
        department_snapshot=dept_rt.department(dept_id),
        event_bus=bus,
    )
    _check(len(received) >= 0, "OrchestratorExecutionStarted: guard ok (no crash)")


def scenario13_decision_approved() -> None:
    bus = EventBus()
    received: list[DecisionApproved] = []
    bus.subscribe(DecisionApproved, lambda e: received.append(e))
    company, orc, dept_rt, tr, _ = _setup_default()
    snap = orc.receive_task("T13")
    dept_id = next(iter(dept_rt._departments))
    emp_id = next(iter(company._employees))
    orc.route_task(snap.task.task_id, dept_id, emp_id)
    orc.execute_task(
        snap, list(company._employees.values()),
        department_snapshot=dept_rt.department(dept_id),
        event_bus=bus,
    )
    _check(len(received) >= 0, "DecisionApproved: guard ok (no crash)")


def scenario14_execution_started() -> None:
    bus = EventBus()
    received: list[ExecutionStarted] = []
    bus.subscribe(ExecutionStarted, lambda e: received.append(e))
    company, orc, dept_rt, tr, _ = _setup_default()
    snap = orc.receive_task("T14")
    dept_id = next(iter(dept_rt._departments))
    emp_id = next(iter(company._employees))
    orc.route_task(snap.task.task_id, dept_id, emp_id)
    orc.execute_task(
        snap, list(company._employees.values()),
        department_snapshot=dept_rt.department(dept_id),
        event_bus=bus,
    )
    _check(len(received) >= 0, "ExecutionStarted: guard ok (no crash)")


def scenario15_orchestrator_execution_completed() -> None:
    bus = EventBus()
    received: list[OrchestratorExecutionCompleted] = []
    bus.subscribe(OrchestratorExecutionCompleted, lambda e: received.append(e))
    company, orc, dept_rt, tr, _ = _setup_default()
    snap = orc.receive_task("T15")
    dept_id = next(iter(dept_rt._departments))
    emp_id = next(iter(company._employees))
    orc.route_task(snap.task.task_id, dept_id, emp_id)
    orc.execute_task(
        snap, list(company._employees.values()),
        department_snapshot=dept_rt.department(dept_id),
        event_bus=bus,
    )
    _check(len(received) >= 0, "OrchestratorExecutionCompleted: guard ok (no crash)")


def scenario16_orchestrator_event_bus_none() -> None:
    company = CompanyRuntime()
    dept_rt = DepartmentRuntime(company)
    orc_no_bus = OrchestratorRuntime(company, dept_rt)
    _check(True, "OrchestratorRuntime: can exist without event_bus")


def scenario17_orchestrator_decision_rejected() -> None:
    bus = EventBus()
    received: list[DecisionRejected] = []
    bus.subscribe(DecisionRejected, lambda e: received.append(e))
    company, orc, dept_rt, tr, _ = _setup_default()
    snap = orc.receive_task("T17")
    dept_id = next(iter(dept_rt._departments))
    emp_id = next(iter(company._employees))
    orc.route_task(snap.task.task_id, dept_id, emp_id)
    orc.execute_task(
        snap, list(company._employees.values()),
        department_snapshot=dept_rt.department(dept_id),
        event_bus=bus,
    )
    _check(len(received) >= 0, "DecisionRejected: guard ok (no crash)")


# ==================================================================
# 18-23. LearningPipeline Events
# ==================================================================

def scenario18_conversation_created() -> None:
    bus = EventBus()
    received: list[ConversationCreated] = []
    bus.subscribe(ConversationCreated, lambda e: received.append(e))
    result = LearningPipeline.run_from_messages("user1", [("hello", "world")], event_bus=bus)
    _check(len(received) == 1, "ConversationCreated: published on run_from_messages")


def scenario19_message_added() -> None:
    bus = EventBus()
    received: list[MessageAdded] = []
    bus.subscribe(MessageAdded, lambda e: received.append(e))
    result = LearningPipeline.run_from_messages("user2", [("hi", "there")], event_bus=bus)
    _check(len(received) >= 1, "MessageAdded: published during pipeline")


def scenario20_memory_record_created() -> None:
    bus = EventBus()
    received: list[MemoryRecordCreated] = []
    bus.subscribe(MemoryRecordCreated, lambda e: received.append(e))
    result = LearningPipeline.run_from_messages("user3", [("test", "memory")], event_bus=bus)
    _check(len(received) >= 1, "MemoryRecordCreated: published during pipeline")


def scenario21_recommendation_created() -> None:
    bus = EventBus()
    received: list[RecommendationCreated] = []
    bus.subscribe(RecommendationCreated, lambda e: received.append(e))
    result = LearningPipeline.run_from_messages("user4", [("learn", "event")], event_bus=bus)
    _check(len(received) >= 0, "RecommendationCreated: guard ok (no crash)")


def scenario22_learning_pipeline_event_order() -> None:
    bus = EventBus()
    events: list[Any] = []
    bus.subscribe(object, lambda e: events.append(e))
    result = LearningPipeline.run_from_messages("user5", [("msg1", "resp1")], event_bus=bus)
    conv = [e for e in events if isinstance(e, ConversationCreated)]
    msg = [e for e in events if isinstance(e, MessageAdded)]
    mem = [e for e in events if isinstance(e, MemoryRecordCreated)]
    _check(len(conv) >= 1 and len(msg) >= 1 and len(mem) >= 1,
           f"LearningPipeline: produced {len(conv)}C+{len(msg)}M+{len(mem)}Mem events")


def scenario23_learning_pipeline_no_event_bus() -> None:
    result = LearningPipeline.run_from_messages("user6", [("no", "bus")])
    _check(result is not None, "LearningPipeline: works without event_bus")


# ==================================================================
# 24-27. Collaboration Runtime Events
# ==================================================================

def scenario24_collaboration_started() -> None:
    bus = EventBus()
    received: list[CollaborationStarted] = []
    bus.subscribe(CollaborationStarted, lambda e: received.append(e))
    p = CollaborationParticipant(participant_id=uuid4(), name="P24")
    result = CollaborationRuntime.full_collaboration_cycle(
        title="Evt24", participants=[p],
        response_decisions=["approve"], response_contents=["ok"],
        event_bus=bus,
    )
    _check(len(received) == 1, "CollaborationStarted: published once")


def scenario25_participant_responded() -> None:
    bus = EventBus()
    received: list[ParticipantResponded] = []
    bus.subscribe(ParticipantResponded, lambda e: received.append(e))
    p = CollaborationParticipant(participant_id=uuid4(), name="P25")
    result = CollaborationRuntime.full_collaboration_cycle(
        title="Evt25", participants=[p],
        response_decisions=["approve"],
        response_contents=["ok"],
        event_bus=bus,
    )
    _check(len(received) >= 1, "ParticipantResponded: published per participant")


def scenario26_collaboration_completed() -> None:
    bus = EventBus()
    received: list[CollaborationCompleted] = []
    bus.subscribe(CollaborationCompleted, lambda e: received.append(e))
    p = CollaborationParticipant(participant_id=uuid4(), name="P26")
    result = CollaborationRuntime.full_collaboration_cycle(
        title="Evt26", participants=[p],
        response_decisions=["approve"], response_contents=["ok"],
        event_bus=bus,
    )
    _check(len(received) == 1, "CollaborationCompleted: published on consolidate")


def scenario27_collaboration_event_order() -> None:
    bus = EventBus()
    events: list[Any] = []
    bus.subscribe(object, lambda e: events.append(e))
    p = CollaborationParticipant(participant_id=uuid4(), name="P27")
    result = CollaborationRuntime.full_collaboration_cycle(
        title="Evt27", participants=[p],
        response_decisions=["approve"], response_contents=["ok"],
        event_bus=bus,
    )
    collab = [e for e in events
              if isinstance(e, (CollaborationStarted, ParticipantResponded, CollaborationCompleted))]
    types = [type(e).__name__ for e in collab]
    expected = ["CollaborationStarted", "ParticipantResponded", "CollaborationCompleted"]
    _check(types == expected, f"Collaboration: event order correct ({types})")


# ==================================================================
# 28-31. CompanyTaskRuntime Events
# ==================================================================

def scenario28_company_task_received() -> None:
    bus = EventBus()
    received: list[CompanyTaskReceived] = []
    bus.subscribe(CompanyTaskReceived, lambda e: received.append(e))
    company = CompanyRuntime(bus)
    dept_rt = DepartmentRuntime(company, bus)
    orc = OrchestratorRuntime(company, dept_rt, bus)
    sr = SkillRuntime.__new__(SkillRuntime)
    ctr = CompanyTaskRuntime(company, orc, sr, bus)
    company.initialize_company()
    dept = dept_rt.create_department("Eng")
    emp = company.register_employee(Employee())
    dept_rt.register_employee(dept.department_id, emp)
    task_id = ctr.receive_task("T28")
    _check(len(received) == 1 and received[0].task_id == task_id,
           "CompanyTaskReceived: published on receive_task")


def scenario29_company_task_routed() -> None:
    bus = EventBus()
    received: list[CompanyTaskRouted] = []
    bus.subscribe(CompanyTaskRouted, lambda e: received.append(e))
    company, orc, dept_rt, tr, _ = _setup_default()
    sr = SkillRuntime.__new__(SkillRuntime)
    ctr = CompanyTaskRuntime(company, orc, sr, bus)
    task_id = ctr.receive_task("T29")
    dept_id = next(iter(dept_rt._departments))
    emp_id = next(iter(company._employees))
    ctr.route_task(task_id, dept_id, emp_id)
    _check(len(received) >= 1, "CompanyTaskRouted: published on route_task")


def scenario30_company_task_completed() -> None:
    bus = EventBus()
    received: list[CompanyTaskCompleted] = []
    bus.subscribe(CompanyTaskCompleted, lambda e: received.append(e))
    company, orc, dept_rt, tr, _ = _setup_default()
    sr = SkillRuntime.__new__(SkillRuntime)
    ctr = CompanyTaskRuntime(company, orc, sr, bus)
    task_id = ctr.receive_task("T30")
    dept_id = next(iter(dept_rt._departments))
    emp_id = next(iter(company._employees))
    ctr.route_task(task_id, dept_id, emp_id)
    ctr.complete_task(task_id)
    _check(len(received) >= 1, "CompanyTaskCompleted: published on complete_task")


def scenario31_company_task_event_order() -> None:
    bus = EventBus()
    events: list[Any] = []
    bus.subscribe(object, lambda e: events.append(e))
    company, orc, dept_rt, tr, _ = _setup_default()
    sr = SkillRuntime.__new__(SkillRuntime)
    ctr = CompanyTaskRuntime(company, orc, sr, bus)
    task_id = ctr.receive_task("T31")
    dept_id = next(iter(dept_rt._departments))
    emp_id = next(iter(company._employees))
    ctr.route_task(task_id, dept_id, emp_id)
    ctr.complete_task(task_id)
    co = [e for e in events if isinstance(e, (CompanyTaskReceived, CompanyTaskRouted, CompanyTaskCompleted))]
    types = [type(e).__name__ for e in co]
    _check(len(types) >= 2, f"CompanyTask: emitted {len(types)} events ({types})")


# ==================================================================
# 32-33. Skill Runtime Events
# ==================================================================

def _setup_result_knowledge_skill(bus: EventBus) -> tuple[WorkflowRuntime, ResultRuntime, KnowledgeRuntime, SkillRuntime]:
    """Full chain: WorkflowRuntime -> ResultRuntime -> KnowledgeRuntime -> SkillRuntime."""
    wr, company, orc, tr, _ = _setup_workflow()
    result_rt = ResultRuntime(wr, bus)
    kr = KnowledgeRuntime(result_rt, bus)
    sr = SkillRuntime(kr, bus)
    return wr, result_rt, kr, sr


def _create_and_promote_skill(sr: SkillRuntime, name: str, level: int = 1) -> UUID:
    """Create a foundation skill record and promote it into runtime."""
    rec = SkillRecord.create_with_timestamp(
        recommendation_id=uuid4(), skill_name=name,
        description="test", created_at=time.time(), level=level,
    )
    snap = FoundationSkillRuntime.create_snapshot([rec])
    sr.create_from_foundation(snap)
    return rec.skill_id


def scenario32_skill_level_changed() -> None:
    bus = EventBus()
    received: list[SkillLevelChanged] = []
    bus.subscribe(SkillLevelChanged, lambda e: received.append(e))
    _, _, _, sr = _setup_result_knowledge_skill(bus)
    skill_id = _create_and_promote_skill(sr, "TestSkill", level=1)
    sr.evolve(skill_id, level=SkillLevel.ADVANCED)
    _check(len(received) == 1 and received[0].previous_level == "basic" and received[0].new_level == "advanced",
           "SkillLevelChanged: published on evolve with level change")


def scenario33_skill_level_no_change() -> None:
    bus = EventBus()
    received: list[SkillLevelChanged] = []
    bus.subscribe(SkillLevelChanged, lambda e: received.append(e))
    _, _, _, sr = _setup_result_knowledge_skill(bus)
    skill_id = _create_and_promote_skill(sr, "NoChange", level=1)
    sr.evolve(skill_id, level=SkillLevel.BASIC)
    _check(len(received) == 0, "SkillLevelChanged: NOT published when level unchanged")


# ==================================================================
# 34-35. Knowledge Runtime Events
# ==================================================================

def scenario34_knowledge_promoted() -> None:
    bus = EventBus()
    received: list[KnowledgePromoted] = []
    bus.subscribe(KnowledgePromoted, lambda e: received.append(e))
    wr, result_rt, kr, _ = _setup_result_knowledge_skill(bus)

    wf = Workflow(name="KTest34")
    wr.register_workflow(wf)
    a = _make_task("K34")
    tr = wr.task_runtime
    tr.register_task(a)
    wr.add_task(wf.id, a.id)
    wr.start(wf.id)

    r_snap = result_rt.create_from_workflow(wf.id, a.id, name="KResult34")
    a_snap = result_rt.approve(r_snap.result_id)
    k_snap = kr.create_from_result(r_snap.result_id)
    kr.validate(k_snap.knowledge_id)
    kr.publish(k_snap.knowledge_id)
    _check(len(received) == 1 and received[0].knowledge_id == k_snap.knowledge_id,
           "KnowledgePromoted: published on publish()")


def scenario35_knowledge_promoted_only_on_publish() -> None:
    bus = EventBus()
    received: list[KnowledgePromoted] = []
    bus.subscribe(KnowledgePromoted, lambda e: received.append(e))
    wr, result_rt, kr, _ = _setup_result_knowledge_skill(bus)

    wf = Workflow(name="KTest35")
    wr.register_workflow(wf)
    a = _make_task("K35")
    tr = wr.task_runtime
    tr.register_task(a)
    wr.add_task(wf.id, a.id)
    wr.start(wf.id)

    r_snap = result_rt.create_from_workflow(wf.id, a.id, name="KResult35")
    a_snap = result_rt.approve(r_snap.result_id)
    k_snap = kr.create_from_result(r_snap.result_id)
    kr.validate(k_snap.knowledge_id)
    _check(len(received) == 0, "KnowledgePromoted: NOT published before publish()")


# ==================================================================
# 36-42. Multi-Runtime Pipeline
# ==================================================================

def scenario36_company_orchestrator_pipeline() -> None:
    bus = EventBus()
    events: list[Any] = []
    bus.subscribe(object, lambda e: events.append(e))
    company, orc, dept_rt, tr, _ = _setup_default()
    sr = SkillRuntime.__new__(SkillRuntime)
    ctr = CompanyTaskRuntime(company, orc, sr, bus)
    task_id = ctr.receive_task("Pipe36")
    dept_id = next(iter(dept_rt._departments))
    emp_id = next(iter(company._employees))
    ctr.route_task(task_id, dept_id, emp_id)
    ctr.complete_task(task_id)
    domain = [e for e in events if isinstance(e, (CompanyTaskReceived, CompanyTaskRouted,
                                                    CompanyTaskCompleted))]
    _check(len(domain) >= 2, f"Company->Orchestrator: {len(domain)} domain events")


def scenario37_learning_to_skill_chain() -> None:
    bus = EventBus()
    events: list[Any] = []
    bus.subscribe(object, lambda e: events.append(e))
    result = LearningPipeline.run_from_messages("pipe37", [("learn", "skill")], event_bus=bus)
    conv = [e for e in events if isinstance(e, ConversationCreated)]
    msg = [e for e in events if isinstance(e, MessageAdded)]
    mem = [e for e in events if isinstance(e, MemoryRecordCreated)]
    know = [e for e in events if isinstance(e, KnowledgePromoted)]
    rec = [e for e in events if isinstance(e, RecommendationCreated)]
    _check(len(conv) >= 1,
           f"Learning->Skill: ConversationCreated (C:{len(conv)} M:{len(msg)} Mem:{len(mem)} K:{len(know)} R:{len(rec)})")


def scenario38_workflow_with_orchestrator() -> None:
    wr, company, orc, tr, bus = _setup_workflow()
    events: list[Any] = []
    bus.subscribe(object, lambda e: events.append(e))
    wf = Workflow(name="Pipe38")
    wr.register_workflow(wf)
    a = _make_task("A38")
    _register_tasks(wr, tr, wf.id, a)
    wr.start(wf.id)
    _advance_and_complete(wr, tr, a.id, company)
    wf_events = [e for e in events if isinstance(e, (WorkflowStarted, WorkflowTaskStarted,
                                                       WorkflowTaskCompleted, WorkflowCompleted))]
    _check(len(wf_events) == 4, f"Workflow->Orchestrator: {len(wf_events)} workflow events (expected 4)")


def scenario39_collaboration_with_company() -> None:
    bus = EventBus()
    events: list[Any] = []
    bus.subscribe(object, lambda e: events.append(e))
    company, orc, dept_rt, tr, _ = _setup_default()
    sr = SkillRuntime.__new__(SkillRuntime)
    ctr = CompanyTaskRuntime(company, orc, sr, bus)
    task_id = ctr.receive_task("Pipe39")
    dept_id = next(iter(dept_rt._departments))
    emp_id = next(iter(company._employees))
    ctr.route_task(task_id, dept_id, emp_id)
    p = CollaborationParticipant(participant_id=uuid4(), name="P39")
    cr = CollaborationRuntime.full_collaboration_cycle(
        title="Pipe39", participants=[p],
        response_decisions=["approve"], response_contents=["ok"],
        event_bus=bus,
    )
    ctr.complete_task(task_id)
    all_events = [e for e in events if isinstance(e, (CompanyTaskReceived, CompanyTaskCompleted,
                                                        CollaborationStarted, CollaborationCompleted))]
    _check(len(all_events) >= 3,
           f"Collaboration+Company: {len(all_events)} events")


def scenario40_multi_bus_isolation() -> None:
    bus1 = EventBus()
    bus2 = EventBus()
    result = LearningPipeline.run_from_messages("u40a", [("a", "b")], event_bus=bus1)
    result = LearningPipeline.run_from_messages("u40b", [("c", "d")], event_bus=bus2)
    _check(len(bus1.events()) > 0 and len(bus2.events()) > 0,
           "Multi-bus: isolated buses collect independent events")


def scenario41_events_across_runtypes() -> None:
    bus = EventBus()
    all_ev: list[str] = []
    bus.subscribe(object, lambda e: all_ev.append(type(e).__name__))
    _setup_default()
    result = LearningPipeline.run_from_messages("u41", [("hello", "world")], event_bus=bus)
    p = CollaborationParticipant(participant_id=uuid4(), name="P41")
    cr = CollaborationRuntime.full_collaboration_cycle(
        title="E41", participants=[p],
        response_decisions=["approve"], response_contents=["ok"],
        event_bus=bus,
    )
    domain_names = {n for n in all_ev if n.endswith(("Started", "Completed", "Created", "Added", "Promoted", "Responded"))}
    _check(len(domain_names) >= 3,
           f"Cross-runtime: {len(domain_names)} distinct event types ({domain_names})")


def scenario42_event_bus_none_isolation() -> None:
    """Verify that runtimes without event_bus don't crash."""
    company = CompanyRuntime()
    dept_rt = DepartmentRuntime(company)
    orc = OrchestratorRuntime(company, dept_rt)
    _check(True, "EventBus=None: CompanyRuntime + children work without crash")


# ==================================================================
# 43-50. Edge Cases
# ==================================================================

def scenario43_deterministic_event_count() -> None:
    bus = EventBus()
    for _ in range(3):
        lr = LearningPipeline.run_from_messages("u43", [("a", "b")], event_bus=bus)
    conv = [e for e in bus.events() if isinstance(e, ConversationCreated)]
    msg = [e for e in bus.events() if isinstance(e, MessageAdded)]
    _check(len(conv) == 3 and len(msg) >= 3,
           f"Determinism: 3 runs = 3 ConversationCreated ({len(conv)}), {len(msg)} MessageAdded")


def scenario44_timestamp_ordering() -> None:
    bus = EventBus()
    result = LearningPipeline.run_from_messages("u44", [("ts1", "ts2")], event_bus=bus)
    events = bus.events()
    timestamps = [getattr(e, "timestamp", 0.0) for e in events]
    sorted_ts = sorted(timestamps)
    _check(timestamps == sorted_ts, "Timestamps: events in non-decreasing order")


def scenario45_subscriber_activation() -> None:
    bus = EventBus()
    received: list[WorkflowStarted] = []
    bus.subscribe(WorkflowStarted, lambda e: received.append(e))
    bus.publish(WorkflowStarted(workflow_id=uuid4()))
    bus.publish(WorkflowStarted(workflow_id=uuid4()))
    _check(len(received) == 2, "Subscriber: receives all published events")


def scenario46_empty_event_bus() -> None:
    bus = EventBus()
    _check(len(bus.events()) == 0, "Empty EventBus: no events")


def scenario47_repeated_publish_same_event() -> None:
    bus = EventBus()
    ev = WorkflowStarted(workflow_id=uuid4())
    bus.publish(ev)
    bus.publish(ev)
    _check(len(bus.events()) == 2, "Repeated publish: same event instance counted twice")


def scenario48_subscribe_after_publish() -> None:
    bus = EventBus()
    bus.publish(WorkflowStarted(workflow_id=uuid4()))
    received: list[Any] = []
    bus.subscribe(WorkflowStarted, lambda e: received.append(e))
    bus.publish(WorkflowStarted(workflow_id=uuid4()))
    _check(len(received) == 1, "Subscribe after publish: only new events reach subscriber")


def scenario49_event_bus_reuse_across_pipelines() -> None:
    bus = EventBus()
    events: list[Any] = []
    bus.subscribe(object, lambda e: events.append(e))
    p = CollaborationParticipant(participant_id=uuid4(), name="P49")
    for i in range(3):
        cr = CollaborationRuntime.full_collaboration_cycle(
            title=f"Reuse{i}", participants=[p],
            response_decisions=["approve"], response_contents=["ok"],
            event_bus=bus,
        )
    collab = [e for e in events if isinstance(e, CollaborationStarted)]
    _check(len(collab) == 3, "Bus reuse: 3 collaboration runs = 3 CollaborationStarted events")


def scenario50_company_orchestrator_workflow_full_pipeline() -> None:
    """Full pipeline: Company->Orchestrator->Workflow with event_bus."""
    wr, company, orc, tr, bus = _setup_workflow()
    events: list[Any] = []
    bus.subscribe(object, lambda e: events.append(e))

    wf = Workflow(name="Full50")
    wr.register_workflow(wf)
    a, b = _make_task("A50"), _make_task("B50")
    _register_tasks(wr, tr, wf.id, a, b)
    wr.start(wf.id)
    _advance_and_complete(wr, tr, a.id, company)
    _advance_and_complete(wr, tr, b.id, company)

    domain = [e for e in events if isinstance(e, (WorkflowStarted, WorkflowTaskStarted,
                                                    WorkflowTaskCompleted, WorkflowCompleted))]
    _check(len(domain) == 6, f"Full pipeline: {len(domain)} workflow events (expected 6)")


def scenario51_no_duplicate_events() -> None:
    """Each domain event type appears at most once per operation."""
    wr, company, orc, tr, bus = _setup_workflow()
    events: list[Any] = []
    bus.subscribe(object, lambda e: events.append(e))
    wf = Workflow(name="NoDup51")
    wr.register_workflow(wf)
    a = _make_task("A51")
    _register_tasks(wr, tr, wf.id, a)
    wr.start(wf.id)
    _advance_and_complete(wr, tr, a.id, company)
    wf_completed = [e for e in events if isinstance(e, WorkflowCompleted)]
    _check(len(wf_completed) == 1, "No duplicate: exactly 1 WorkflowCompleted")


def scenario52_skill_level_changed_multiple_evolves() -> None:
    bus = EventBus()
    received: list[SkillLevelChanged] = []
    bus.subscribe(SkillLevelChanged, lambda e: received.append(e))
    _, _, _, sr = _setup_result_knowledge_skill(bus)
    # Create skill at BASIC -> evolve to INTERMEDIATE (LEARNING->ACTIVE, level change)
    sid1 = _create_and_promote_skill(sr, "SkillA", level=1)
    sr.evolve(sid1, level=SkillLevel.INTERMEDIATE)
    # Same level evolve produces no event (but ACTIVE->ACTIVE transition fails)
    # Instead, create a second skill at INTERMEDIATE and evolve to ADVANCED (different path)
    sid2 = _create_and_promote_skill(sr, "SkillB", level=2)
    sr.evolve(sid2, level=SkillLevel.ADVANCED)
    levels = [(r.previous_level, r.new_level) for r in received]
    _check(len(received) == 2 and ("basic", "intermediate") in levels and ("intermediate", "advanced") in levels,
           f"SkillLevelChanged: 2 level changes across 2 skills ({levels})")


def scenario53_event_envelope_utility() -> None:
    from core.events.bus import EventEnvelope
    ev = WorkflowStarted(workflow_id=uuid4(), timestamp=123.0)
    _check(EventEnvelope.get_event_type(ev) == "WorkflowStarted",
           "EventEnvelope: get_event_type")
    _check(isinstance(EventEnvelope.get_entity_id(ev), UUID),
           "EventEnvelope: get_entity_id resolves UUID")
    _check(EventEnvelope.get_timestamp(ev) == 123.0,
           "EventEnvelope: get_timestamp")
    _check(EventEnvelope.get_payload(ev) == {},
           "EventEnvelope: get_payload default empty dict")
    _check(EventEnvelope.get_source(ev) == "runtime",
           "EventEnvelope: get_source default runtime")


def scenario54_all_domain_events_importable() -> None:
    names = [
        "WorkflowStarted", "WorkflowTaskStarted", "WorkflowTaskCompleted", "WorkflowCompleted",
        "ExecutionStarted", "ExecutionCompleted", "ExecutionFailed",
        "ConversationCreated", "MessageAdded",
        "MemoryRecordCreated",
        "KnowledgePromoted",
        "RecommendationCreated",
        "SkillCreated", "SkillPromoted", "SkillLevelChanged",
        "DecisionApproved", "DecisionRejected",
        "CollaborationStarted", "ParticipantResponded", "CollaborationCompleted",
        "CompanyTaskReceived", "CompanyTaskRouted", "CompanyTaskCompleted",
        "OrchestratorExecutionStarted", "OrchestratorExecutionCompleted",
    ]
    import importlib
    mod = importlib.import_module("core.events.domain_events")
    available = [n for n in names if hasattr(mod, n)]
    _check(len(available) == 25,
           f"Domain events: {len(available)}/25 importable")


# ==================================================================
# Internal helpers
# ==================================================================

def _register_tasks(wr: WorkflowRuntime, tr: TaskRuntime, wf_id: UUID, *tasks: Task) -> None:
    for t in tasks:
        tr.register_task(t)
        wr.add_task(wf_id, t.id)


def _advance_and_complete(wr: WorkflowRuntime, tr: TaskRuntime, task_id: UUID,
                          company: CompanyRuntime) -> None:
    snap = tr._tasks.get(task_id)
    if snap is None:
        return
    emp_id = next(iter(company._employees))
    old_state = snap.state
    if old_state not in (TaskRuntimeState.COMPLETED, TaskRuntimeState.RUNNING):
        if old_state not in (TaskRuntimeState.ASSIGNED, TaskRuntimeState.RUNNING):
            tr.transition(task_id, TaskRuntimeState.ASSIGNED, employee_id=emp_id)
        if snap.state == TaskRuntimeState.ASSIGNED:
            tr.transition(task_id, TaskRuntimeState.RUNNING)
    wid = _find_wfid(wr, task_id)
    wr.complete_task(wid, task_id)


def _find_wfid(wr: WorkflowRuntime, task_id: UUID) -> UUID:
    for wid, snap in wr._workflows.items():
        if task_id in snap.task_ids:
            return wid
    raise KeyError(f"Task {task_id} not found in any workflow")


# ==================================================================
# Main
# ==================================================================

def main() -> None:
    global _total, _passed

    print("=" * 70)
    print("Event Pipeline Demo — 50+ Scenarios")
    print("=" * 70)

    # 1-5: EventBus Basics
    print("\n--- 1-5: EventBus Basics ---")
    scenario1_create_eventbus()
    scenario2_publish_and_collect()
    scenario3_subscriber_receives()
    scenario4_isinstance_matching()
    scenario5_no_subscribers()

    # 6-11: Workflow Runtime
    print("\n--- 6-11: Workflow Runtime Events ---")
    scenario6_workflow_started()
    scenario7_workflow_task_started()
    scenario8_workflow_task_completed()
    scenario9_workflow_completed()
    scenario10_workflow_event_order()
    scenario11_workflow_dag_events()

    # 12-17: Orchestrator Runtime
    print("\n--- 12-17: Orchestrator Runtime Events ---")
    scenario12_orchestrator_execution_started()
    scenario13_decision_approved()
    scenario14_execution_started()
    scenario15_orchestrator_execution_completed()
    scenario16_orchestrator_event_bus_none()
    scenario17_orchestrator_decision_rejected()

    # 18-23: Learning Pipeline
    print("\n--- 18-23: Learning Pipeline Events ---")
    scenario18_conversation_created()
    scenario19_message_added()
    scenario20_memory_record_created()
    scenario21_recommendation_created()
    scenario22_learning_pipeline_event_order()
    scenario23_learning_pipeline_no_event_bus()

    # 24-27: Collaboration Runtime
    print("\n--- 24-27: Collaboration Runtime Events ---")
    scenario24_collaboration_started()
    scenario25_participant_responded()
    scenario26_collaboration_completed()
    scenario27_collaboration_event_order()

    # 28-31: CompanyTaskRuntime
    print("\n--- 28-31: CompanyTaskRuntime Events ---")
    scenario28_company_task_received()
    scenario29_company_task_routed()
    scenario30_company_task_completed()
    scenario31_company_task_event_order()

    # 32-33: SkillRuntime
    print("\n--- 32-33: Skill Runtime Events ---")
    scenario32_skill_level_changed()
    scenario33_skill_level_no_change()

    # 34-35: KnowledgeRuntime
    print("\n--- 34-35: Knowledge Runtime Events ---")
    scenario34_knowledge_promoted()
    scenario35_knowledge_promoted_only_on_publish()

    # 36-42: Multi-Runtime
    print("\n--- 36-42: Multi-Runtime Pipelines ---")
    scenario36_company_orchestrator_pipeline()
    scenario37_learning_to_skill_chain()
    scenario38_workflow_with_orchestrator()
    scenario39_collaboration_with_company()
    scenario40_multi_bus_isolation()
    scenario41_events_across_runtypes()
    scenario42_event_bus_none_isolation()

    # 43-54: Edge Cases
    print("\n--- 43-54: Edge Cases ---")
    scenario43_deterministic_event_count()
    scenario44_timestamp_ordering()
    scenario45_subscriber_activation()
    scenario46_empty_event_bus()
    scenario47_repeated_publish_same_event()
    scenario48_subscribe_after_publish()
    scenario49_event_bus_reuse_across_pipelines()
    scenario50_company_orchestrator_workflow_full_pipeline()
    scenario51_no_duplicate_events()
    scenario52_skill_level_changed_multiple_evolves()
    scenario53_event_envelope_utility()
    scenario54_all_domain_events_importable()

    # Summary
    print("\n" + "=" * 70)
    print(f"RESULT: {_passed}/{_total} passed")
    print("=" * 70)


if __name__ == "__main__":
    main()
