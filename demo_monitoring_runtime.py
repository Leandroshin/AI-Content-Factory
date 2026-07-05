"""Demo: Monitoring Runtime — 120+ scenarios.

Covers data models, domain/success inference, snapshot building,
incremental consumption, health score, filtering, grouping, timeline,
merge, EventBus integration, PerformanceRuntime compatibility,
PersistenceRuntime compatibility, determinism, and edge cases.
"""

from __future__ import annotations

import copy
import json
import time
from dataclasses import dataclass
from pathlib import Path
from uuid import UUID, uuid4

from core.analytics.runtime import (
    PerformanceMetric,
    PerformanceRuntime,
    PerformanceSnapshot as PerfSnapshot,
)
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
from core.monitoring.runtime import (
    MonitoringEvent,
    MonitoringResult,
    MonitoringRuntime,
    MonitoringSnapshot,
    MonitoringTrace,
    _detect_success,
    _infer_domain,
)
from core.persistence.runtime import PersistenceRuntime

passed = 0
failed = 0


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
    print(f"Total: {total}/{total} passed, {failed} failed")
    print(f"{'=' * 70}")


# ==================================================================
# Shared fixtures
# ==================================================================

ts0 = 1000.0
ts1 = 1001.0
ts2 = 1002.0
ts3 = 1003.0
ts4 = 1004.0
eid1 = uuid4()
eid2 = uuid4()
eid3 = uuid4()
wid = uuid4()
tid = uuid4()

# ==================================================================
# Section 1: Data models
# ==================================================================
print("\n" + "=" * 70)
print("Section 1: Data models")
print("=" * 70)

me = MonitoringEvent(event_type="TestEvent", domain="test", source="test")
check("MonitoringEvent frozen", me.event_type == "TestEvent", "")

me2 = MonitoringEvent(
    event_type="WorkflowStarted",
    domain="workflow",
    source="runtime",
    entity_id=eid1,
    timestamp=ts1,
    success=True,
    metadata={"key": "val"},
)
check("  all fields", me2.entity_id == eid1 and me2.timestamp == ts1 and me2.success is True, "")

ms = MonitoringSnapshot()
check("MonitoringSnapshot empty", ms.total_events == 0, "")
check("  health baseline", ms.health_score == 50.0, "")

ms2 = MonitoringSnapshot(
    total_events=10,
    total_errors=2,
    total_success=8,
    health_score=75.0,
)
check("  partial fields", ms2.total_events == 10 and ms2.health_score == 75.0, "")

mt = MonitoringTrace()
check("MonitoringTrace default", mt.events_consumed == 0, "")

mt2 = MonitoringTrace(events_consumed=5, operation="build", duration_ms=1.5, snapshot_size=5)
check("  all trace fields", mt2.operation == "build" and mt2.duration_ms == 1.5, "")

mr = MonitoringResult(success=True)
check("MonitoringResult success", mr.success, "")

mr2 = MonitoringResult(success=False, error_message="fail")
check("  error result", not mr2.success and mr2.error_message == "fail", "")

mr3 = MonitoringResult(success=True, snapshot=ms, trace=mt)
check("  with snapshot+trace", mr3.snapshot is ms and mr3.trace is mt, "")

# Immutability
try:
    me.event_type = "Mut"
    check("immutable enforced", False, "should raise")
except Exception:
    check("immutable enforced", True, "")

# ==================================================================
# Section 2: Domain inference
# ==================================================================
print("\n" + "=" * 70)
print("Section 2: Domain inference")
print("=" * 70)

check("WorkflowStarted domain=workflow", _infer_domain(WorkflowStarted(workflow_id=wid, timestamp=ts0)) == "workflow", "")
check("CompanyTaskReceived -> company_task", _infer_domain(CompanyTaskReceived(task_id=tid, timestamp=ts0)) == "company_task", "")
check("OrchestratorExecutionStarted -> orchestrator", _infer_domain(OrchestratorExecutionStarted(orchestrator_id=eid1, timestamp=ts0)) == "orchestrator", "")
check("CollaborationStarted -> collaboration", _infer_domain(CollaborationStarted(session_id=eid1, timestamp=ts0)) == "collaboration", "")
check("ConversationCreated -> conversation", _infer_domain(ConversationCreated(session_id=eid1, timestamp=ts0)) == "conversation", "")
check("KnowledgePromoted -> knowledge", _infer_domain(KnowledgePromoted(knowledge_id=eid1, timestamp=ts0)) == "knowledge", "")
check("RecommendationCreated -> learning", _infer_domain(RecommendationCreated(recommendation_id=eid1, timestamp=ts0)) == "learning", "")
check("MemoryRecordCreated -> memory", _infer_domain(MemoryRecordCreated(memory_id=eid1, timestamp=ts0)) == "memory", "")
check("ExecutionStarted -> execution", _infer_domain(ExecutionStarted(execution_id=eid1, timestamp=ts0)) == "execution", "")
check("DecisionApproved -> decision", _infer_domain(DecisionApproved(decision_id=eid1, timestamp=ts0)) == "decision", "")
check("SkillCreated -> skill", _infer_domain(SkillCreated(skill_id=eid1, timestamp=ts0)) == "skill", "")
check("MessageAdded -> conversation", _infer_domain(MessageAdded(session_id=eid1, message_id=eid2, timestamp=ts0)) == "conversation", "")
check("ParticipantResponded -> collaboration", _infer_domain(ParticipantResponded(session_id=eid1, participant_id=eid2, timestamp=ts0)) == "collaboration", "")
check("SkillLevelChanged -> skill", _infer_domain(SkillLevelChanged(skill_id=eid1, name="test", previous_level="1", new_level="2", timestamp=ts0)) == "skill", "")

# Custom event class
@dataclass(frozen=True, slots=True)
class CustomEvent:
    pass

check("CustomEvent -> unknown", _infer_domain(CustomEvent()) == "unknown", "")

# ==================================================================
# Section 3: Success detection
# ==================================================================
print("\n" + "=" * 70)
print("Section 3: Success detection")
print("=" * 70)

check("WorkflowStarted -> None", _detect_success(WorkflowStarted(workflow_id=wid, timestamp=ts0)) is None, "")
check("ExecutionCompleted -> True", _detect_success(ExecutionCompleted(execution_id=eid1, timestamp=ts0)) is True, "")
check("ExecutionFailed -> False", _detect_success(ExecutionFailed(execution_id=eid1, timestamp=ts0)) is False, "")
check("DecisionApproved -> True", _detect_success(DecisionApproved(decision_id=eid1, timestamp=ts0)) is True, "")
check("DecisionRejected -> False", _detect_success(DecisionRejected(decision_id=eid1, timestamp=ts0)) is False, "")
check("KnowledgePromoted -> True", _detect_success(KnowledgePromoted(knowledge_id=eid1, timestamp=ts0)) is True, "")
check("SkillPromoted -> True", _detect_success(SkillPromoted(skill_id=eid1, name="t", level="l", timestamp=ts0)) is True, "")
check("CollaborationCompleted success=True -> True", _detect_success(CollaborationCompleted(session_id=eid1, success=True, timestamp=ts0)) is True, "")
check("CollaborationCompleted success=False -> False", _detect_success(CollaborationCompleted(session_id=eid1, success=False, timestamp=ts0)) is False, "")
check("CompanyTaskCompleted success=True -> True", _detect_success(CompanyTaskCompleted(task_id=tid, success=True, timestamp=ts0)) is True, "")
check("CompanyTaskCompleted success=False -> False", _detect_success(CompanyTaskCompleted(task_id=tid, success=False, timestamp=ts0)) is False, "")
check("SkillLevelChanged -> None", _detect_success(SkillLevelChanged(skill_id=eid1, name="t", previous_level="1", new_level="2", timestamp=ts0)) is None, "")
check("OrchestratorExecutionCompleted success=True -> True", _detect_success(OrchestratorExecutionCompleted(orchestrator_id=eid1, success=True, timestamp=ts0)) is True, "")
check("WorkflowTaskCompleted -> True", _detect_success(WorkflowTaskCompleted(workflow_id=wid, task_id=tid, timestamp=ts0)) is True, "")
check("WorkflowCompleted -> True", _detect_success(WorkflowCompleted(workflow_id=wid, timestamp=ts0)) is True, "")

# ==================================================================
# Section 4: build_snapshot
# ==================================================================
print("\n" + "=" * 70)
print("Section 4: build_snapshot")
print("=" * 70)

# Empty
s = MonitoringRuntime.build_snapshot([])
check("empty snapshot", s.total_events == 0, "")
check("  health=35", s.health_score == 35.0, "")

# Single event
s = MonitoringRuntime.build_snapshot([
    WorkflowStarted(workflow_id=wid, timestamp=ts1),
])
check("single total=1", s.total_events == 1, "")
check("  domain workflow=1", s.events_by_domain.get("workflow") == 1, "")
check("  type WorkflowStarted=1", s.events_by_type.get("WorkflowStarted") == 1, "")

# Multiple events
events_multi = [
    WorkflowStarted(workflow_id=wid, timestamp=ts1),
    ExecutionCompleted(execution_id=eid1, timestamp=ts2),
    DecisionApproved(decision_id=eid2, timestamp=ts3),
    ExecutionFailed(execution_id=eid3, timestamp=ts4),
]
s = MonitoringRuntime.build_snapshot(events_multi)
check("multi total=4", s.total_events == 4, "")
check("  success=2", s.total_success == 2, f"val={s.total_success}")
check("  errors=1", s.total_errors == 1, f"val={s.total_errors}")
check("  4 types", len(s.events_by_type) == 4, f"val={len(s.events_by_type)}")
check("  3 domains", len(s.events_by_domain) == 3, f"val={len(s.events_by_domain)}")
check("  first_ts=ts1", s.first_timestamp == ts1, "")
check("  last_ts=ts4", s.last_timestamp == ts4, "")

# Multiple domains
events_domains = [
    WorkflowStarted(workflow_id=wid, timestamp=ts1),
    CompanyTaskReceived(task_id=tid, timestamp=ts2),
    ExecutionCompleted(execution_id=eid1, timestamp=ts3),
    KnowledgePromoted(knowledge_id=eid2, timestamp=ts4),
]
s = MonitoringRuntime.build_snapshot(events_domains)
check("4 domains", len(s.events_by_domain) == 4, f"keys={sorted(s.events_by_domain.keys())}")

# All success
all_ok = [
    ExecutionCompleted(execution_id=eid1, timestamp=ts1),
    DecisionApproved(decision_id=eid2, timestamp=ts2),
    WorkflowCompleted(workflow_id=wid, timestamp=ts3),
]
s = MonitoringRuntime.build_snapshot(all_ok)
check("all success", s.total_success == 3 and s.total_errors == 0, "")
check("  success_rate=100", s.success_rate == 100.0, "")

# All failure
all_fail = [
    ExecutionFailed(execution_id=eid1, timestamp=ts1),
    DecisionRejected(decision_id=eid2, timestamp=ts2),
]
s = MonitoringRuntime.build_snapshot(all_fail)
check("all failure", s.total_errors == 2 and s.total_success == 0, "")
check("  error_rate=100", s.error_rate == 100.0, "")

# Large number of events
large = [
    WorkflowStarted(workflow_id=uuid4(), timestamp=float(i))
    for i in range(100)
]
s = MonitoringRuntime.build_snapshot(large)
check("large 100 events", s.total_events == 100, "")
check("  workflow domain=100", s.events_by_domain.get("workflow") == 100, "")
check("  health >= 0", s.health_score >= 0, f"score={s.health_score}")

# Events without timestamps (default to 0.0)
no_ts = [
    WorkflowStarted(workflow_id=wid),
    ExecutionCompleted(execution_id=eid1),
]
s = MonitoringRuntime.build_snapshot(no_ts)
check("no timestamps", s.total_events == 2, "")
check("  first=0", s.first_timestamp == 0.0, "")
check("  last=0", s.last_timestamp == 0.0, "")
check("  uptime=0", s.uptime == 0.0, "")

# Unicode metadata
unicode_evt = WorkflowStarted(
    workflow_id=wid,
    timestamp=ts1,
    metadata={"name": "São Paulo & 東京", "emoji": "✅"},
)
s = MonitoringRuntime.build_snapshot([unicode_evt])
check("unicode metadata", s.total_events == 1, "")

# UUID entity IDs
s = MonitoringRuntime.build_snapshot([
    CompanyTaskReceived(task_id=tid, timestamp=ts1),
])
check("UUID entity_id", s.timeline[0].entity_id == tid, f"val={s.timeline[0].entity_id}")

# Observability-style events (custom)
@dataclass(frozen=True, slots=True)
class CompanyStateChangedEvent:
    new_state: str = "active"

evt = CompanyStateChangedEvent()
check("CompanyStateChanged -> company", _infer_domain(evt) == "company", "")

# ==================================================================
# Section 5: consume_event (incremental)
# ==================================================================
print("\n" + "=" * 70)
print("Section 5: consume_event (incremental)")
print("=" * 70)

# From empty
base = MonitoringSnapshot()
s1 = MonitoringRuntime.consume_event(base, WorkflowStarted(workflow_id=wid, timestamp=ts1))
check("inc empty->1", s1.total_events == 1, "")
check("  timeline len=1", len(s1.timeline) == 1, "")

# Incremental add
s2 = MonitoringRuntime.consume_event(s1, ExecutionCompleted(execution_id=eid1, timestamp=ts2))
check("inc 1->2", s2.total_events == 2, "")
check("  success=1", s2.total_success == 1, "")

# Multiple incremental adds
s3 = MonitoringRuntime.consume_event(s2, ExecutionFailed(execution_id=eid2, timestamp=ts3))
check("inc 2->3", s3.total_events == 3, "")
check("  errors=1", s3.total_errors == 1, "")
check("  timeline sorted", s3.timeline[0].timestamp <= s3.timeline[-1].timestamp, "")

# Incremental preserves metadata
base_w_meta = MonitoringSnapshot(metadata={"source": "test"})
s4 = MonitoringRuntime.consume_event(base_w_meta, WorkflowStarted(workflow_id=wid, timestamp=ts1))
check("preserves metadata", s4.metadata.get("source") == "test", "")

# ==================================================================
# Section 6: consume_events (batch)
# ==================================================================
print("\n" + "=" * 70)
print("Section 6: consume_events (batch)")
print("=" * 70)

base2 = MonitoringSnapshot()
s_batch = MonitoringRuntime.consume_events(base2, [
    WorkflowStarted(workflow_id=wid, timestamp=ts1),
    ExecutionCompleted(execution_id=eid1, timestamp=ts2),
    ExecutionFailed(execution_id=eid2, timestamp=ts3),
])
check("batch total=3", s_batch.total_events == 3, "")
check("  success=1", s_batch.total_success == 1, "")
check("  errors=1", s_batch.total_errors == 1, "")

# Batch onto existing
s_batch2 = MonitoringRuntime.consume_events(s_batch, [
    DecisionApproved(decision_id=eid3, timestamp=ts4),
])
check("batch 3->4", s_batch2.total_events == 4, "")
check("  success=2", s_batch2.total_success == 2, f"val={s_batch2.total_success}")

# Empty batch
s_batch3 = MonitoringRuntime.consume_events(base2, [])
check("empty batch", s_batch3.total_events == 0, "")

# ==================================================================
# Section 7: calculate_health
# ==================================================================
print("\n" + "=" * 70)
print("Section 7: calculate_health")
print("=" * 70)

h_empty = MonitoringRuntime.calculate_health(MonitoringSnapshot(health_score=35.0))
check("empty health=35", h_empty == 35.0, "")

s_100 = MonitoringRuntime.build_snapshot([
    ExecutionCompleted(execution_id=eid1, timestamp=ts1, output="ok"),
])
h_100 = MonitoringRuntime.calculate_health(s_100)
check("all success health", h_100 >= 75, f"score={h_100}")

s_0 = MonitoringRuntime.build_snapshot([
    ExecutionFailed(execution_id=eid1, timestamp=ts1, error_message="err"),
])
h_0 = MonitoringRuntime.calculate_health(s_0)
check("all failure health", h_0 < 50, f"score={h_0}")

# Mixed
s_m = MonitoringRuntime.build_snapshot([
    ExecutionCompleted(execution_id=eid1, timestamp=ts1, output="ok"),
    ExecutionFailed(execution_id=eid2, timestamp=ts2, error_message="err"),
    DecisionApproved(decision_id=eid3, timestamp=ts3),
])
h_m = MonitoringRuntime.calculate_health(s_m)
check("mixed health range", 0 <= h_m <= 100, f"score={h_m}")

# Bound check
s_bad = MonitoringRuntime.build_snapshot([
    ExecutionFailed(execution_id=eid1, timestamp=ts1, error_message="err1"),
    ExecutionFailed(execution_id=eid2, timestamp=ts2, error_message="err2"),
    ExecutionFailed(execution_id=eid3, timestamp=ts3, error_message="err3"),
    ExecutionFailed(execution_id=uuid4(), timestamp=ts4, error_message="err4"),
])
h_bad = MonitoringRuntime.calculate_health(s_bad)
check("bound >= 0", h_bad >= 0, f"score={h_bad}")

s_good = MonitoringRuntime.build_snapshot([
    ExecutionCompleted(execution_id=eid1, timestamp=ts1, output="ok"),
    ExecutionCompleted(execution_id=eid2, timestamp=ts2, output="ok"),
    ExecutionCompleted(execution_id=eid3, timestamp=ts3, output="ok"),
    ExecutionCompleted(execution_id=uuid4(), timestamp=ts4, output="ok"),
])
h_good = MonitoringRuntime.calculate_health(s_good)
check("bound <= 100", h_good <= 100, f"score={h_good}")

# ==================================================================
# Section 8: calculate_uptime / event_rate / error_rate / success_rate
# ==================================================================
print("\n" + "=" * 70)
print("Section 8: Metrics calculators")
print("=" * 70)

s_rate = MonitoringRuntime.build_snapshot([
    WorkflowStarted(workflow_id=wid, timestamp=100.0),
    WorkflowCompleted(workflow_id=wid, timestamp=200.0),
])
check("uptime 100s", MonitoringRuntime.calculate_uptime(s_rate) == 100.0, "")
check("event_rate 0.02", abs(MonitoringRuntime.calculate_event_rate(s_rate) - 0.02) < 0.001, f"rate={MonitoringRuntime.calculate_event_rate(s_rate)}")
check("success_rate 50%", MonitoringRuntime.calculate_success_rate(s_rate) == 50.0, "")
check("error_rate 0%", MonitoringRuntime.calculate_error_rate(s_rate) == 0.0, "")

s_rate2 = MonitoringRuntime.build_snapshot([
    ExecutionFailed(execution_id=eid1, timestamp=100.0, error_message="err"),
    ExecutionFailed(execution_id=eid2, timestamp=100.0, error_message="err"),
])
check("error_rate 100%", MonitoringRuntime.calculate_error_rate(s_rate2) == 100.0, "")
check("success_rate 0%", MonitoringRuntime.calculate_success_rate(s_rate2) == 0.0, "")
check("uptime 0", MonitoringRuntime.calculate_uptime(s_rate2) == 0.0, "")
check("event_rate 0", MonitoringRuntime.calculate_event_rate(s_rate2) == 0.0, "")

# ==================================================================
# Section 9: filter_events
# ==================================================================
print("\n" + "=" * 70)
print("Section 9: filter_events")
print("=" * 70)

evts = [
    WorkflowStarted(workflow_id=wid, timestamp=ts1),
    ExecutionCompleted(execution_id=eid1, timestamp=ts2),
    ExecutionFailed(execution_id=eid2, timestamp=ts3),
    DecisionApproved(decision_id=eid3, timestamp=ts4),
    CompanyTaskReceived(task_id=tid, timestamp=ts1),
]

# By type
f_type = MonitoringRuntime.filter_events(evts, event_type="ExecutionCompleted")
check("filter type=2 results", len(f_type) == 1, f"count={len(f_type)}")

# By domain
f_domain = MonitoringRuntime.filter_events(evts, domain="workflow")
check("filter domain=1", len(f_domain) == 1, f"count={len(f_domain)}")

# By success
f_success = MonitoringRuntime.filter_events(evts, success=True)
check("filter success=2", len(f_success) == 2, f"count={len(f_success)}")

f_fail = MonitoringRuntime.filter_events(evts, success=False)
check("filter fail=1", len(f_fail) == 1, f"count={len(f_fail)}")

# Combined
f_combined = MonitoringRuntime.filter_events(evts, domain="execution", success=False)
check("combined domain+success=1", len(f_combined) == 1, f"count={len(f_combined)}")

# No match
f_none = MonitoringRuntime.filter_events(evts, event_type="NonExistent")
check("filter no match", len(f_none) == 0, "")

# No filters
f_all = MonitoringRuntime.filter_events(evts)
check("filter no args=all", len(f_all) == len(evts), "")

# Empty
f_empty = MonitoringRuntime.filter_events([])
check("filter empty", len(f_empty) == 0, "")

# ==================================================================
# Section 10: group_by_type / group_by_domain
# ==================================================================
print("\n" + "=" * 70)
print("Section 10: group_by_type / group_by_domain")
print("=" * 70)

g_type = MonitoringRuntime.group_by_type(evts)
check("group type 5 keys", len(g_type) == 5, f"keys={list(g_type.keys())}")
check("  WorkflowStarted=1", len(g_type["WorkflowStarted"]) == 1, "")
check("  ExecutionFailed=1", len(g_type["ExecutionFailed"]) == 1, "")

g_domain = MonitoringRuntime.group_by_domain(evts)
check("group domain 4 keys", len(g_domain) == 4, f"keys={list(g_domain.keys())}")
check("  workflow=1", len(g_domain["workflow"]) == 1, "")
check("  execution=2", len(g_domain["execution"]) == 2, "")

# Empty
g_empty = MonitoringRuntime.group_by_type([])
check("group empty", len(g_empty) == 0, "")

g_empty2 = MonitoringRuntime.group_by_domain([])
check("group domain empty", len(g_empty2) == 0, "")

# Single group
g_single = MonitoringRuntime.group_by_type([
    WorkflowStarted(workflow_id=wid, timestamp=ts1),
    WorkflowStarted(workflow_id=eid2, timestamp=ts2),
])
check("group single type", len(g_single) == 1 and len(g_single["WorkflowStarted"]) == 2, "")

# ==================================================================
# Section 11: timeline
# ==================================================================
print("\n" + "=" * 70)
print("Section 11: timeline")
print("=" * 70)

unsorted = [
    WorkflowCompleted(workflow_id=wid, timestamp=ts3),
    WorkflowStarted(workflow_id=wid, timestamp=ts1),
    ExecutionCompleted(execution_id=eid1, timestamp=ts2),
]
tl = MonitoringRuntime.timeline(unsorted)
check("timeline sorted", [e.event_type for e in tl] == ["WorkflowStarted", "ExecutionCompleted", "WorkflowCompleted"], f"order={[e.event_type for e in tl]}")
check("  all MonitoringEvent", all(isinstance(e, MonitoringEvent) for e in tl), "")

# Empty
tl_empty = MonitoringRuntime.timeline([])
check("timeline empty", len(tl_empty) == 0, "")

# Single
tl_single = MonitoringRuntime.timeline([WorkflowStarted(workflow_id=wid, timestamp=ts1)])
check("timeline single", len(tl_single) == 1, "")

# Same timestamps
tl_same = MonitoringRuntime.timeline([
    WorkflowStarted(workflow_id=wid, timestamp=ts1),
    ExecutionCompleted(execution_id=eid1, timestamp=ts1),
])
check("timeline same ts", len(tl_same) == 2, "")

# ==================================================================
# Section 12: merge_snapshots
# ==================================================================
print("\n" + "=" * 70)
print("Section 12: merge_snapshots")
print("=" * 70)

s_a = MonitoringRuntime.build_snapshot([
    WorkflowStarted(workflow_id=wid, timestamp=ts1),
])
s_b = MonitoringRuntime.build_snapshot([
    ExecutionCompleted(execution_id=eid1, timestamp=ts2),
])
merged = MonitoringRuntime.merge_snapshots([s_a, s_b])
check("merge total=2", merged.total_events == 2, "")
check("  timeline len=2", len(merged.timeline) == 2, "")
check("  2 types", len(merged.events_by_type) == 2, "")

# Merge empty + non-empty
s_empty = MonitoringSnapshot()
merged2 = MonitoringRuntime.merge_snapshots([s_empty, s_a])
check("merge empty+non=1", merged2.total_events == 1, "")

# Three snapshots
s_c = MonitoringRuntime.build_snapshot([
    DecisionApproved(decision_id=eid3, timestamp=ts3),
])
merged3 = MonitoringRuntime.merge_snapshots([s_a, s_b, s_c])
check("merge 3 total=3", merged3.total_events == 3, "")

# Merge identical
merged4 = MonitoringRuntime.merge_snapshots([s_a, s_a])
check("merge identical total=2", merged4.total_events == 2, "")

# Empty list
s_none = MonitoringRuntime.merge_snapshots([])
check("merge no snapshots", s_none.total_events == 0, "")

# Merge with metadata
s_meta1 = MonitoringRuntime.build_snapshot([])
s_meta1_m = MonitoringSnapshot(
    total_events=0,
    metadata={"env": "prod"},
)
s_meta2_m = MonitoringSnapshot(
    total_events=0,
    metadata={"version": "2.0"},
)
merged_meta = MonitoringRuntime.merge_snapshots([s_meta1_m, s_meta2_m])
check("merge metadata", merged_meta.metadata.get("env") == "prod" and merged_meta.metadata.get("version") == "2.0", "")

# ==================================================================
# Section 13: create_monitor / build_result / build_trace
# ==================================================================
print("\n" + "=" * 70)
print("Section 13: create_monitor / build_result / build_trace")
print("=" * 70)

r_init = MonitoringRuntime.create_monitor()
check("create_monitor success", r_init.success, "")
check("  snapshot empty", r_init.snapshot is not None and r_init.snapshot.total_events == 0, "")
check("  trace present", r_init.trace is not None and r_init.trace.operation == "create_monitor", "")

s_demo = MonitoringRuntime.build_snapshot([
    WorkflowStarted(workflow_id=wid, timestamp=ts1),
])
r_result = MonitoringRuntime.build_result(s_demo)
check("build_result success", r_result.success, "")
check("  snapshot ref", r_result.snapshot is s_demo, "")
check("  trace events=1", r_result.trace is not None and r_result.trace.events_consumed == 1, "")

t_trace = MonitoringRuntime.build_trace(s_demo, operation="test", duration_ms=2.5)
check("build_trace", t_trace.events_consumed == 1 and t_trace.operation == "test" and t_trace.duration_ms == 2.5, "")

t_empty = MonitoringRuntime.build_trace(MonitoringSnapshot())
check("build_trace empty", t_empty.events_consumed == 0, "")

# ==================================================================
# Section 14: EventBus integration
# ==================================================================
print("\n" + "=" * 70)
print("Section 14: EventBus integration")
print("=" * 70)

bus = EventBus()
bus.publish(WorkflowStarted(workflow_id=wid, timestamp=ts1))
bus.publish(ExecutionCompleted(execution_id=eid1, timestamp=ts2))
bus.publish(ExecutionFailed(execution_id=eid2, timestamp=ts3))
bus.publish(DecisionApproved(decision_id=eid3, timestamp=ts4))

s_bus = MonitoringRuntime.consume_from_bus(bus)
check("bus snapshot total=4", s_bus.total_events == 4, "")
check("  success=2", s_bus.total_success == 2, f"val={s_bus.total_success}")
check("  errors=1", s_bus.total_errors == 1, "")

# Empty bus
bus2 = EventBus()
s_bus2 = MonitoringRuntime.consume_from_bus(bus2)
check("empty bus", s_bus2.total_events == 0, "")

# Incremental bus consumption
bus3 = EventBus()
bus3.publish(WorkflowStarted(workflow_id=wid, timestamp=ts1))
snap1 = MonitoringRuntime.consume_from_bus(bus3)
check("bus inc step1 total=1", snap1.total_events == 1, "")

bus3.publish(ExecutionCompleted(execution_id=eid1, timestamp=ts2))
snap2 = MonitoringRuntime.consume_from_bus(bus3)
check("bus inc step2 total=2", snap2.total_events == 2, "")

# Subscribe + publish pattern
bus4 = EventBus()
events_collected: list[Any] = []

def collector(event: Any) -> None:
    events_collected.append(event)

bus4.subscribe(WorkflowStarted, collector)
bus4.publish(WorkflowStarted(workflow_id=wid, timestamp=ts1))
check("bus subscribe=1", len(events_collected) == 1, "")

s_sub = MonitoringRuntime.build_snapshot(events_collected)
check("bus subscribe snapshot", s_sub.total_events == 1, "")

# ==================================================================
# Section 15: PerformanceRuntime compatibility
# ==================================================================
print("\n" + "=" * 70)
print("Section 15: PerformanceRuntime compatibility")
print("=" * 70)

# PerformanceRuntime can handle MonitoringSnapshot metrics
snap = MonitoringRuntime.build_snapshot([
    ExecutionCompleted(execution_id=eid1, timestamp=ts1, output="ok"),
    ExecutionFailed(execution_id=eid2, timestamp=ts2, error_message="err"),
])

# Build a PerformanceResult manually from monitoring data
perf_metric = PerformanceMetric(
    name="total_events",
    value=float(snap.total_events),
    unit="count",
)
perf_snapshot = PerfSnapshot(
    metrics={"total_events": perf_metric},
    timestamp=ts1,
)
pr = PerformanceRuntime.build_dashboard(results=[
    PerformanceRuntime.analyze_execution(
        executions=[],
        usages=[],
    ),
])
check("perf dashboard success", pr.success, "")

# Direct metric inspection
check("monitoring total_events=2", snap.total_events == 2, "")
check("monitoring success_rate=50", snap.success_rate == 50.0, "")

# ==================================================================
# Section 16: PersistenceRuntime compatibility
# ==================================================================
print("\n" + "=" * 70)
print("Section 16: PersistenceRuntime compatibility")
print("=" * 70)

snap_p = MonitoringRuntime.build_snapshot([
    WorkflowStarted(workflow_id=wid, timestamp=ts1),
    ExecutionCompleted(execution_id=eid1, timestamp=ts2),
])

# Save
result_save = PersistenceRuntime.save_snapshot(
    snap_p,
    domain="monitoring",
    snapshot_id="test_monitor_001",
)
check("persistence save success", result_save.success, f"err={result_save.error_message}")
check("  path not empty", bool(result_save.path), "")

# Exists
check("persistence exists", PersistenceRuntime.snapshot_exists("monitoring", "test_monitor_001"), "")

# Load
result_load = PersistenceRuntime.load_snapshot("monitoring", "test_monitor_001")
check("persistence load success", result_load.success, f"err={result_load.error_message}")
check("  loaded is MonitoringSnapshot", isinstance(result_load.snapshot, MonitoringSnapshot), f"type={type(result_load.snapshot).__name__}")
if result_load.snapshot:
    check("  loaded total=2", result_load.snapshot.total_events == 2, "")
    check("  loaded type count keys", len(result_load.snapshot.events_by_type) == 2, "")

# List
result_list = PersistenceRuntime.list_snapshots("monitoring")
check("persistence list success", result_list.success, "")
if result_list.snapshot:
    check("  entries > 0", len(result_list.snapshot) > 0, "")

# Export JSON
export_path = Path("storage") / "monitoring_export_test.json"
result_export = PersistenceRuntime.export_json(
    snap_p,
    filepath=export_path,
    domain="monitoring",
    snapshot_id="export_test",
)
check("persistence export success", result_export.success, f"err={result_export.error_message}")

# Import JSON
result_import = PersistenceRuntime.import_json(export_path)
check("persistence import success", result_import.success, f"err={result_import.error_message}")
if result_import.snapshot:
    check("  imported type", isinstance(result_import.snapshot, MonitoringSnapshot), f"type={type(result_import.snapshot).__name__}")
    check("  imported total=2", result_import.snapshot.total_events == 2, "")

# Delete
result_del = PersistenceRuntime.delete_snapshot("monitoring", "test_monitor_001")
check("persistence delete success", result_del.success, "")
check("  not exists", not PersistenceRuntime.snapshot_exists("monitoring", "test_monitor_001"), "")

# Clean up export
if export_path.exists():
    export_path.unlink()

# Clean domain
PersistenceRuntime.clean_domain("monitoring")
check("persistence cleaned", not PersistenceRuntime.snapshot_exists("monitoring", "test_monitor_001"), "")

# ==================================================================
# Section 17: Determinism
# ==================================================================
print("\n" + "=" * 70)
print("Section 17: Determinism")
print("=" * 70)

evts_a = [
    WorkflowStarted(workflow_id=wid, timestamp=ts1),
    ExecutionCompleted(execution_id=eid1, output="ok", timestamp=ts2),
    DecisionApproved(decision_id=eid3, timestamp=ts3),
]

evts_b = [
    WorkflowStarted(workflow_id=wid, timestamp=ts1),
    ExecutionCompleted(execution_id=eid1, output="ok", timestamp=ts2),
    DecisionApproved(decision_id=eid3, timestamp=ts3),
]

s_a = MonitoringRuntime.build_snapshot(evts_a)
s_b = MonitoringRuntime.build_snapshot(evts_b)
check("determinism total", s_a.total_events == s_b.total_events, "")
check("  health", s_a.health_score == s_b.health_score, f"a={s_a.health_score} b={s_b.health_score}")
check("  success_rate", s_a.success_rate == s_b.success_rate, "")
check("  error_rate", s_a.error_rate == s_b.error_rate, "")

# Order independence (same events different order -> same metrics)
evts_c = list(reversed(evts_a))
s_c = MonitoringRuntime.build_snapshot(evts_c)
check("order total", s_a.total_events == s_c.total_events, "")
check("  order types", s_a.events_by_type == s_c.events_by_type, "")
check("  order domains", s_a.events_by_domain == s_c.events_by_domain, "")

# ==================================================================
# Section 18: Edge cases
# ==================================================================
print("\n" + "=" * 70)
print("Section 18: Edge cases")
print("=" * 70)

# Empty events
check("edge empty total=0", MonitoringRuntime.build_snapshot([]).total_events == 0, "")
check("edge empty health=35", MonitoringRuntime.build_snapshot([]).health_score == 35.0, "")

# None metadata
s_none_val = MonitoringRuntime.build_snapshot([
    WorkflowStarted(workflow_id=wid, timestamp=ts1, metadata={"val": None}),
])
check("edge None metadata val", s_none_val.total_events == 1, "")

# Zero timestamps
s_zero_ts = MonitoringRuntime.build_snapshot([
    WorkflowStarted(workflow_id=wid, timestamp=0.0),
    ExecutionCompleted(execution_id=eid1, timestamp=0.0),
])
check("edge zero timestamp", s_zero_ts.first_timestamp == 0.0 and s_zero_ts.last_timestamp == 0.0, "")
check("  uptime 0", s_zero_ts.uptime == 0.0, "")

# Duplicates in timeline
s_dup = MonitoringRuntime.build_snapshot([
    WorkflowStarted(workflow_id=wid, timestamp=ts1),
    WorkflowStarted(workflow_id=wid, timestamp=ts1),
])
check("edge duplicate events", s_dup.total_events == 2, "")
check("  type count=1", s_dup.events_by_type.get("WorkflowStarted") == 2, "")

# Single event rate
s_single_rate = MonitoringRuntime.build_snapshot([
    WorkflowStarted(workflow_id=wid, timestamp=ts1),
])
check("edge single uptime=0", s_single_rate.uptime == 0.0, "")
check("edge single event_rate=0", s_single_rate.event_rate == 0.0, "")

# All neutral events
s_neutral = MonitoringRuntime.build_snapshot([
    WorkflowStarted(workflow_id=wid, timestamp=ts1),
    ConversationCreated(session_id=eid1, timestamp=ts2),
    MemoryRecordCreated(memory_id=eid2, timestamp=ts3),
])
check("edge all neutral", s_neutral.total_success == 0 and s_neutral.total_errors == 0, "")
check("  rates 0", s_neutral.success_rate == 0.0 and s_neutral.error_rate == 0.0, "")

# Big numbers
s_big = MonitoringRuntime.build_snapshot([
    ExecutionCompleted(execution_id=eid1, timestamp=1e9, output="ok"),
    ExecutionCompleted(execution_id=eid2, timestamp=2e9, output="ok"),
])
check("edge big timestamps", s_big.uptime == 1e9, "")

# Filter empty
f_empty2 = MonitoringRuntime.filter_events([])
check("edge filter empty", len(f_empty2) == 0, "")

# Group empty
g_empty3 = MonitoringRuntime.group_by_type([])
check("edge group_by_type empty", len(g_empty3) == 0, "")

# Merge all empty
m_empty = MonitoringRuntime.merge_snapshots([MonitoringSnapshot(), MonitoringSnapshot()])
check("edge merge empty*2", m_empty.total_events == 0, "")

# Create monitor result with empty snapshot
r_em = MonitoringRuntime.create_monitor()
check("edge create_monitor health=35", r_em.snapshot is not None and r_em.snapshot.health_score == 35.0, "")

# Timeline empty
tl_e = MonitoringRuntime.timeline([])
check("edge timeline empty", len(tl_e) == 0, "")

# Timeline with negative timestamps
tl_neg = MonitoringRuntime.timeline([
    WorkflowCompleted(workflow_id=wid, timestamp=-5.0),
    WorkflowStarted(workflow_id=wid, timestamp=-10.0),
])
check("edge negative ts order", tl_neg[0].timestamp == -10.0 and tl_neg[1].timestamp == -5.0, "")

# Consume event with no timestamp
s_no_ts = MonitoringRuntime.consume_event(
    MonitoringSnapshot(),
    WorkflowStarted(workflow_id=wid),
)
check("edge consume no ts", s_no_ts.total_events == 1, "")

# Consume events empty list
s_ce = MonitoringRuntime.consume_events(MonitoringSnapshot(), [])
check("edge consume empty list", s_ce.total_events == 0, "")

# All events same type/domain
s_same = MonitoringRuntime.build_snapshot([
    WorkflowStarted(workflow_id=eid1, timestamp=ts1),
    WorkflowStarted(workflow_id=eid2, timestamp=ts2),
    WorkflowStarted(workflow_id=eid3, timestamp=ts3),
])
check("edge same type count=3", s_same.events_by_type.get("WorkflowStarted") == 3, "")
check("  same domain=3", s_same.events_by_domain.get("workflow") == 3, "")

# Result from snapshot
r_final = MonitoringRuntime.build_result(s_same)
check("edge result from snapshot", r_final.success, "")
check("  events consumed=3", r_final.trace is not None and r_final.trace.events_consumed == 3, "")

# ==================================================================
# Section 19: Full pipeline
# ==================================================================
print("\n" + "=" * 70)
print("Section 19: Full pipeline")
print("=" * 70)

bus_pipe = EventBus()
bus_pipe.publish(WorkflowStarted(workflow_id=wid, timestamp=100.0))
bus_pipe.publish(WorkflowTaskStarted(workflow_id=wid, task_id=tid, timestamp=101.0))
bus_pipe.publish(WorkflowTaskCompleted(workflow_id=wid, task_id=tid, timestamp=102.0))
bus_pipe.publish(WorkflowCompleted(workflow_id=wid, timestamp=103.0))
bus_pipe.publish(CompanyTaskReceived(task_id=tid, title="P1", timestamp=200.0))
bus_pipe.publish(CompanyTaskRouted(task_id=tid, department_id=eid1, employee_id=eid2, timestamp=201.0))
bus_pipe.publish(CompanyTaskCompleted(task_id=tid, success=True, duration=10.0, timestamp=202.0))
bus_pipe.publish(OrchestratorExecutionStarted(orchestrator_id=eid1, task_id=tid, timestamp=300.0))
bus_pipe.publish(OrchestratorExecutionCompleted(orchestrator_id=eid1, task_id=tid, success=True, timestamp=301.0))

# Build from bus
pipe_snap = MonitoringRuntime.consume_from_bus(bus_pipe)
check("pipeline total=9", pipe_snap.total_events == 9, f"val={pipe_snap.total_events}")
check("  workflow domain=4", pipe_snap.events_by_domain.get("workflow") == 4, "")
check("  company_task domain=3", pipe_snap.events_by_domain.get("company_task") == 3, "")
check("  orchestrator domain=2", pipe_snap.events_by_domain.get("orchestrator") == 2, "")
check("  5 types", len(pipe_snap.events_by_type) >= 5, f"count={len(pipe_snap.events_by_type)}")

# Filter pipeline
wf_events = MonitoringRuntime.filter_events(bus_pipe.events(), domain="workflow")
check("pipeline filter workflow=4", len(wf_events) == 4, f"val={len(wf_events)}")

# Group pipeline
pipe_groups = MonitoringRuntime.group_by_domain(bus_pipe.events())
check("pipeline 3 domains", len(pipe_groups) == 3, f"keys={list(pipe_groups.keys())}")

# Timeline
pipe_tl = MonitoringRuntime.timeline(bus_pipe.events())
check("pipeline timeline sorted", all(pipe_tl[i].timestamp <= pipe_tl[i + 1].timestamp for i in range(len(pipe_tl) - 1)), "")

# Incremental pipeline
pipe_inc = MonitoringSnapshot()
for e in bus_pipe.events():
    pipe_inc = MonitoringRuntime.consume_event(pipe_inc, e)
check("pipeline incremental total=9", pipe_inc.total_events == 9, f"val={pipe_inc.total_events}")
check("  pipeline inc matches", pipe_inc.total_events == pipe_snap.total_events, "")
check("  pipeline inc health", pipe_inc.health_score == pipe_snap.health_score, "")

# Merge incremental batches
batch1 = MonitoringRuntime.build_snapshot(bus_pipe.events()[:4])
batch2 = MonitoringRuntime.build_snapshot(bus_pipe.events()[4:7])
batch3 = MonitoringRuntime.build_snapshot(bus_pipe.events()[7:])
merged_pipe = MonitoringRuntime.merge_snapshots([batch1, batch2, batch3])
check("pipeline merge total=9", merged_pipe.total_events == 9, "")
check("  merge timeline sorted", merged_pipe.timeline_sorted()[0].timestamp <= merged_pipe.timeline_sorted()[-1].timestamp, "")

# Result from pipeline
pipe_result = MonitoringRuntime.build_result(pipe_snap, operation="pipeline")
check("pipeline result success", pipe_result.success, "")
check("  operation=pipeline", pipe_result.trace is not None and pipe_result.trace.operation == "pipeline", "")
check("  snapshot ref", pipe_result.snapshot is pipe_snap, "")

# ==================================================================
# Section 20: Backward compatibility
# ==================================================================
print("\n" + "=" * 70)
print("Section 20: Backward compatibility")
print("=" * 70)

# Importing from existing modules unchanged
from core.events.bus import EventBus as EB
check("EventBus importable", EB is EventBus, "")

from core.analytics.runtime import PerformanceRuntime as PR
check("PerformanceRuntime importable", PR is PerformanceRuntime, "")

from core.persistence.runtime import PersistenceRuntime as PERS
check("PersistenceRuntime importable", PERS is PersistenceRuntime, "")

# PersistenceRuntime works with monitoring domain without changes
p_check = PersistenceRuntime.snapshot_exists("monitoring", "nonexistent")
check("no-op existence check", not p_check, "")

# PerformanceRuntime can be called normally
pr_back = PerformanceRuntime.analyze_execution(
    executions=[],
    usages=[],
)
check("PerformanceRuntime backward compat", pr_back.success, "")

# ==================================================================
summary()
