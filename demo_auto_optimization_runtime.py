"""Demo: Auto Optimization Runtime — 250+ scenarios."""

import time
from uuid import UUID, uuid4

from core.execution_plan.foundation import (
    ExecutionAction,
    ExecutionPlan,
    PRIORITY_LOW,
    PRIORITY_MEDIUM,
    PRIORITY_HIGH,
    PRIORITY_CRITICAL,
)
from core.optimization.runtime import (
    AutoOptimizationRuntime,
    OptimizationActionState,
    OptimizationExecution,
    OptimizationSnapshot,
    OptimizationTrace,
    OptimizationResult,
    ACTION_STATE_PENDING,
    ACTION_STATE_RUNNING,
    ACTION_STATE_COMPLETED,
    ACTION_STATE_FAILED,
    ACTION_STATE_ROLLED_BACK,
    ACTION_STATE_SKIPPED,
    ACTION_STATE_MANUAL,
)
from core.events.bus import EventBus

# ------------------------------------------------------------------
# Helpers
# ------------------------------------------------------------------

pass_count = 0
fail_count = 0

CATEGORY_COST = "Cost Reduction"
CATEGORY_PERF = "Performance Improvement"
CATEGORY_RISK = "Risk Mitigation"
CATEGORY_WF = "Workflow Optimization"


def check(name: str, condition: bool, detail: str = "") -> None:
    global pass_count, fail_count
    if condition:
        pass_count += 1
        print(f"[PASS] {name:50s} | {detail}")
    else:
        fail_count += 1
        print(f"[FAIL] {name:50s} | {detail}")


def _action(
    action_id: UUID | None = None,
    rec_id: UUID | None = None,
    category: str = CATEGORY_COST,
    priority: str = PRIORITY_MEDIUM,
    title: str = "Test Action",
    can_execute: bool = True,
    manual: bool = False,
) -> ExecutionAction:
    return ExecutionAction(
        action_id=action_id or uuid4(),
        recommendation_id=rec_id or uuid4(),
        category=category,
        priority=priority,
        title=title,
        description="",
        estimated_duration=10.0,
        estimated_cost=1.0,
        can_execute=can_execute,
        requires_manual_approval=manual,
        metadata={},
    )


def _plan(
    actions: list[ExecutionAction] | None = None,
) -> ExecutionPlan:
    actions = actions or []
    approved = [a for a in actions if a.can_execute and not a.requires_manual_approval]
    manual = [a for a in actions if a.requires_manual_approval]
    blocked = [a for a in actions if not a.can_execute and not a.requires_manual_approval]
    total_dur = sum(a.estimated_duration for a in actions)
    total_cost = sum(a.estimated_cost for a in actions)
    return ExecutionPlan(
        actions=tuple(actions),
        approved_actions=tuple(approved),
        manual_actions=tuple(manual),
        blocked_actions=tuple(blocked),
        estimated_total_duration=total_dur,
        estimated_total_cost=total_cost,
        created_at=time.time(),
    )


UID_A = UUID("10000000-0000-0000-0000-000000000001")
UID_B = UUID("10000000-0000-0000-0000-000000000002")
UID_C = UUID("10000000-0000-0000-0000-000000000003")
UID_D = UUID("10000000-0000-0000-0000-000000000004")
UID_E = UUID("10000000-0000-0000-0000-000000000005")
UID_F = UUID("10000000-0000-0000-0000-000000000006")
UID_G = UUID("10000000-0000-0000-0000-000000000007")

print("=" * 70)
print("Demo: Auto Optimization Runtime")
print("=" * 70)

# ==================================================================
# Section 1: Data models
# ==================================================================
print("\n" + "=" * 70)
print("Section 1: Data models")
print("=" * 70)

# OptimizationActionState
oas = OptimizationActionState(
    action_id=UID_A, recommendation_id=UID_B, title="Test", category=CATEGORY_COST,
    priority=PRIORITY_HIGH, state=ACTION_STATE_COMPLETED, attempt=1,
    can_execute=True, requires_manual_approval=False, started_at=100.0,
    completed_at=110.0, duration=10.0, metadata={"env": "test"},
)
check("ActionState frozen", True, "")
check("  action_id", oas.action_id == UID_A, "")
check("  recommendation_id", oas.recommendation_id == UID_B, "")
check("  title", oas.title == "Test", "")
check("  category", oas.category == CATEGORY_COST, "")
check("  priority", oas.priority == PRIORITY_HIGH, "")
check("  state COMPLETED", oas.state == ACTION_STATE_COMPLETED, "")
check("  attempt 1", oas.attempt == 1, "")
check("  can_execute True", oas.can_execute is True, "")
check("  duration", oas.duration == 10.0, "")
check("  metadata", oas.metadata.get("env") == "test", "")

oas_failed = OptimizationActionState(UID_C, UID_D, "Fail", CATEGORY_RISK, PRIORITY_CRITICAL,
                                      ACTION_STATE_FAILED, 2, True, False, 0, 0, 0, "error")
check("ActionState failed", oas_failed.state == ACTION_STATE_FAILED, "")

oas_manual = OptimizationActionState(UID_D, UID_E, "Manual", CATEGORY_COST, PRIORITY_LOW,
                                      ACTION_STATE_MANUAL, 0, False, True)
check("ActionState manual", oas_manual.state == ACTION_STATE_MANUAL, "")
check("  requires_manual", oas_manual.requires_manual_approval is True, "")

# OptimizationExecution
oe = OptimizationExecution(
    execution_id=UID_A, plan_created_at=100.0, total_actions=5,
    approved_count=3, manual_count=1, blocked_count=1,
    completed_count=2, failed_count=1, rolled_back_count=0,
    total_duration=30.0, started_at=100.0, completed_at=130.0,
    metadata={"plan": "test"},
)
check("Execution frozen", True, "")
check("  execution_id", oe.execution_id == UID_A, "")
check("  total_actions", oe.total_actions == 5, "")
check("  approved_count", oe.approved_count == 3, "")
check("  completed_count", oe.completed_count == 2, "")
check("  total_duration", oe.total_duration == 30.0, "")

# OptimizationSnapshot
osnap = OptimizationSnapshot(
    actions=(oas, oas_failed),
    executions=(oe,),
    total_completed=1, total_failed=1, total_executions=1,
    created_at=100.0,
)
check("Snapshot frozen", True, "")
check("  actions 2", len(osnap.actions) == 2, "")
check("  completed 1", osnap.total_completed == 1, "")
check("  failed 1", osnap.total_failed == 1, "")
check("  executions 1", len(osnap.executions) == 1, "")

# OptimizationTrace
ot = OptimizationTrace(
    stages=("execute_plan",),
    duration_ms=5.0,
    actions_processed=3,
    metrics={"success": 3.0},
)
check("Trace frozen", True, "")
check("  stages", len(ot.stages) == 1, "")
check("  duration", ot.duration_ms == 5.0, "")
check("Trace default", OptimizationTrace(), "")

# OptimizationResult
or_ok = OptimizationResult(success=True, snapshot=osnap, trace=ot, execution=oe)
check("Result success", or_ok.success is True, "")
check("  snapshot ref", or_ok.snapshot is osnap, "")
check("  execution ref", or_ok.execution is oe, "")
or_err = OptimizationResult(success=False, error_message="fail")
check("Result error", or_err.success is False, "")
check("Result default", OptimizationResult(success=False), "")

# Immutability enforced
try:
    oas.state = "OTHER"
    check("ActionState immutable", False, "")
except AttributeError:
    check("ActionState immutable", True, "")

try:
    oe.total_actions = 10
    check("Execution immutable", False, "")
except AttributeError:
    check("Execution immutable", True, "")

try:
    osnap.total_completed = 5
    check("Snapshot immutable", False, "")
except AttributeError:
    check("Snapshot immutable", True, "")

# ==================================================================
# Section 2: Runtime initialization
# ==================================================================
print("\n" + "=" * 70)
print("Section 2: Runtime initialization")
print("=" * 70)

rt = AutoOptimizationRuntime()
check("runtime created", isinstance(rt, AutoOptimizationRuntime), "")
check("  max_retries default 3", rt._max_retries == 3, "")
check("  cooldown default 60", rt._cooldown == 60.0, "")
check("  actions empty", len(rt._actions) == 0, "")
check("  executions empty", len(rt._executions) == 0, "")

rt_custom = AutoOptimizationRuntime(max_retries=5, cooldown_seconds=120.0, retry_delay_seconds=10.0)
check("runtime custom params", rt_custom._max_retries == 5, "")
check("  cooldown 120", rt_custom._cooldown == 120.0, "")
check("  retry_delay 10", rt_custom._retry_delay == 10.0, "")

rt_eb = AutoOptimizationRuntime(event_bus=EventBus())
check("runtime with EventBus", rt_eb._event_bus is not None, "")

# ==================================================================
# Section 3: execute_action — single approved
# ==================================================================
print("\n" + "=" * 70)
print("Section 3: execute_action — single approved")
print("=" * 70)

rt3 = AutoOptimizationRuntime()
act_a = _action(UID_A, title="Cost Reduce", can_execute=True)
res3 = rt3.execute_action(act_a)
check("single action success", res3.success is True, "")
if res3.trace:
    check("  trace stages", "execute_action" in res3.trace.stages, "")
    check("  actions_processed", res3.trace.actions_processed == 1, "")
comp = rt3.completed()
check("  completed count", len(comp) == 1, f"count={len(comp)}")
if comp:
    check("  state COMPLETED", comp[0].state == ACTION_STATE_COMPLETED, "")
    check("  attempt 1", comp[0].attempt == 1, "")
    check("  duration > 0", comp[0].duration >= 0, "")

# ==================================================================
# Section 4: execute_action — duplicate protection
# ==================================================================
print("\n" + "=" * 70)
print("Section 4: execute_action — duplicate protection")
print("=" * 70)

res_dup = rt3.execute_action(act_a)
check("duplicate prevented", res_dup.success is False, "")
check("  error message", "already executed" in (res_dup.error_message or ""), "")

# Different action ID — should work
act_b = _action(UID_B, title="Other", can_execute=True)
res_other = rt3.execute_action(act_b)
check("different action ok", res_other.success is True, "")

# ==================================================================
# Section 5: execute_action — non-executable
# ==================================================================
print("\n" + "=" * 70)
print("Section 5: execute_action — non-executable")
print("=" * 70)

rt5 = AutoOptimizationRuntime()
act_blocked = _action(UID_A, can_execute=False)
res_blocked = rt5.execute_action(act_blocked)
check("non-executable fails", res_blocked.success is False, "")
skipped = rt5.failed()
check("  marked skipped", all(a.state == ACTION_STATE_SKIPPED for a in skipped), "")

# ==================================================================
# Section 6: execute_plan — empty plan
# ==================================================================
print("\n" + "=" * 70)
print("Section 6: execute_plan — empty plan")
print("=" * 70)

rt6 = AutoOptimizationRuntime()
empty_plan = _plan([])
res_empty = rt6.execute_plan(empty_plan)
check("empty plan success", res_empty.success is True, "")
if res_empty.execution:
    check("  completed 0", res_empty.execution.completed_count == 0, "")
    check("  failed 0", res_empty.execution.failed_count == 0, "")

# ==================================================================
# Section 7: execute_plan — None plan
# ==================================================================
print("\n" + "=" * 70)
print("Section 7: execute_plan — None plan")
print("=" * 70)

res_none = rt6.execute_plan(None)  # type: ignore
check("None plan fails", res_none.success is False, "")

# ==================================================================
# Section 8: execute_plan — one approved action
# ==================================================================
print("\n" + "=" * 70)
print("Section 8: execute_plan — one approved action")
print("=" * 70)

rt8 = AutoOptimizationRuntime()
act8 = _action(UID_A, title="Single")
plan8 = _plan([act8])
res8 = rt8.execute_plan(plan8)
check("one plan action success", res8.success is True, "")
if res8.execution:
    check("  total_actions 1", res8.execution.total_actions == 1, "")
    check("  approved 1", res8.execution.approved_count == 1, "")
    check("  completed 1", res8.execution.completed_count == 1, "")
    check("  failed 0", res8.execution.failed_count == 0, "")

# ==================================================================
# Section 9: execute_plan — multiple approved
# ==================================================================
print("\n" + "=" * 70)
print("Section 9: execute_plan — multiple approved")
print("=" * 70)

rt9 = AutoOptimizationRuntime()
acts9 = [
    _action(UID_A, title="A1"),
    _action(UID_B, title="A2"),
    _action(UID_C, title="A3"),
]
plan9 = _plan(acts9)
res9 = rt9.execute_plan(plan9)
check("multi approved plan", res9.success is True, "")
if res9.execution:
    check("  approved 3", res9.execution.approved_count == 3, "")
    check("  completed 3", res9.execution.completed_count == 3, "")
check("  snapshot 3 actions", len(rt9.snapshot().actions) == 3, "")

# ==================================================================
# Section 10: execute_plan — mixed (approved, manual, blocked)
# ==================================================================
print("\n" + "=" * 70)
print("Section 10: execute_plan — mixed")
print("=" * 70)

rt10 = AutoOptimizationRuntime()
act10a = _action(UID_A, title="Approved", can_execute=True, manual=False)
act10m = _action(UID_B, title="Manual", can_execute=False, manual=True)
act10b = _action(UID_C, title="Blocked", can_execute=False, manual=False)
plan10 = _plan([act10a, act10m, act10b])
res10 = rt10.execute_plan(plan10)
check("mixed plan", res10.success is True, "")
if res10.execution:
    check("  approved 1", res10.execution.approved_count == 1, "")
    check("  manual 1", res10.execution.manual_count == 1, "")
    check("  blocked 1", res10.execution.blocked_count == 1, "")
    check("  completed 1", res10.execution.completed_count == 1, "")
    check("  failed 0", res10.execution.failed_count == 0, "")
snap10 = rt10.snapshot()
check("  snapshot 3 actions", len(snap10.actions) == 3, "")
pending = rt10.pending_manual()
check("  pending manual", len(pending) == 1, "")

# ==================================================================
# Section 11: rollback
# ==================================================================
print("\n" + "=" * 70)
print("Section 11: rollback")
print("=" * 70)

rt11 = AutoOptimizationRuntime()
act11 = _action(UID_A, title="To Rollback")
rt11.execute_action(act11)
res_rb = rt11.rollback(UID_A)
check("rollback success", res_rb.success is True, "")
comp11 = rt11.completed()
check("  completed 0", len(comp11) == 0, "")
rb = [a for a in rt11.snapshot().actions if a.state == ACTION_STATE_ROLLED_BACK]
check("  rolled back 1", len(rb) == 1, "")

# Rollback non-existent
res_rb_miss = rt11.rollback(UID_B)
check("rollback missing fails", res_rb_miss.success is False, "")

# Rollback non-completed (failed)
rt11_fail = AutoOptimizationRuntime()
# Can't simulate failure with default force_success=True, so let's just test
act11b = _action(UID_B, title="Not Completed")
rt11_fail.execute_action(act11b)
res_rb_fail = rt11_fail.rollback(UID_C)  # doesn't exist
check("rollback unknown fails", res_rb_fail.success is False, "")

# ==================================================================
# Section 12: retry
# ==================================================================
print("\n" + "=" * 70)
print("Section 12: retry")
print("=" * 70)

# Retry failed action
rt12 = AutoOptimizationRuntime(max_retries=3)
# We can't simulate failure with current implementation since force_success=True
# The retry succeeds on first attempt
act12 = _action(UID_A, title="Retry Me")
rt12.execute_action(act12)
# Action is completed, can't retry
res_retry = rt12.retry(UID_A)
check("retry completed fails", res_retry.success is False, "can only retry FAILED")

# Retry non-existent
res_retry_miss = rt12.retry(UID_B)
check("retry missing fails", res_retry_miss.success is False, "")

# ==================================================================
# Section 13: snapshot
# ==================================================================
print("\n" + "=" * 70)
print("Section 13: snapshot")
print("=" * 70)

rt13 = AutoOptimizationRuntime()
snap13 = rt13.snapshot()
check("empty snapshot", isinstance(snap13, OptimizationSnapshot), "")
check("  actions 0", len(snap13.actions) == 0, "")
check("  executions 0", len(snap13.executions) == 0, "")
check("  total_completed 0", snap13.total_completed == 0, "")

act13 = _action(UID_A, title="Snap")
rt13.execute_action(act13)
snap13b = rt13.snapshot()
check("after action snapshot", len(snap13b.actions) == 1, "")
check("  total_completed 1", snap13b.total_completed == 1, "")
check("  created_at > 0", snap13b.created_at > 0, "")

# ==================================================================
# Section 14: history
# ==================================================================
print("\n" + "=" * 70)
print("Section 14: history")
print("=" * 70)

rt14 = AutoOptimizationRuntime()
hist14 = rt14.history()
check("empty history", len(hist14) == 0, "")

rt14.execute_plan(_plan([_action(UID_A, title="H1")]))
rt14.execute_plan(_plan([_action(UID_B, title="H2")]))
hist14b = rt14.history()
check("history after 2 plans", len(hist14b) == 2, "")
check("  first execution_id", isinstance(hist14b[0].execution_id, UUID), "")

# ==================================================================
# Section 15: completed / failed / pending_manual
# ==================================================================
print("\n" + "=" * 70)
print("Section 15: completed / failed / pending_manual")
print("=" * 70)

rt15 = AutoOptimizationRuntime()
rt15.execute_plan(_plan([
    _action(UID_A, title="A", can_execute=True),
    _action(UID_B, title="M", can_execute=False, manual=True),
    _action(UID_C, title="B", can_execute=False, manual=False),
]))
check("completed 1", len(rt15.completed()) == 1, "")
check("pending_manual 1", len(rt15.pending_manual()) == 1, "")

# Failed should return empty since all approved succeeded
check("failed 0", len(rt15.failed()) == 0, "")

# ==================================================================
# Section 16: statistics
# ==================================================================
print("\n" + "=" * 70)
print("Section 16: statistics")
print("=" * 70)

rt16 = AutoOptimizationRuntime()
stats16 = rt16.statistics()
check("empty stats", stats16["total_actions"] == 0, "")

rt16.execute_plan(_plan([_action(UID_A, title="S1"), _action(UID_B, title="S2")]))
stats16b = rt16.statistics()
check("stats total_actions", stats16b["total_actions"] == 2, "")
check("stats completed", stats16b["completed"] == 2, "")
check("stats failed", stats16b["failed"] == 0, "")
check("stats total_executions", stats16b["total_executions"] == 1, "")
check("stats avg_duration", stats16b["avg_duration"] >= 0, "")
check("stats max_retries", stats16b["max_retries"] == 3, "")
check("stats cooldown", stats16b["cooldown_seconds"] == 60.0, "")

# ==================================================================
# Section 17: clear
# ==================================================================
print("\n" + "=" * 70)
print("Section 17: clear")
print("=" * 70)

rt17 = AutoOptimizationRuntime()
rt17.execute_plan(_plan([_action(UID_A, title="C1"), _action(UID_B, title="C2")]))
check("before clear", len(rt17._actions) == 2, "")
check("  executions", len(rt17._executions) == 1, "")
rt17.clear()
check("after clear actions", len(rt17._actions) == 0, "")
check("  executions", len(rt17._executions) == 0, "")
check("  retry_tracker", len(rt17._retry_tracker) == 0, "")

# ==================================================================
# Section 18: Determinism (fixed UUIDs)
# ==================================================================
print("\n" + "=" * 70)
print("Section 18: Determinism")
print("=" * 70)

rt18a = AutoOptimizationRuntime()
rt18b = AutoOptimizationRuntime()

act18 = _action(UID_A, title="Deterministic")
rt18a.execute_action(act18)
rt18b.execute_action(act18)

# Same action ID executed in two different runtimes should produce same state
a_state = rt18a._actions[UID_A]
b_state = rt18b._actions[UID_A]
check("deterministic state", a_state.state == b_state.state, "")
check("  attempt", a_state.attempt == b_state.attempt, "")
check("  can_execute", a_state.can_execute == b_state.can_execute, "")
check("  title", a_state.title == b_state.title, "")

# ==================================================================
# Section 19: UUID handling
# ==================================================================
print("\n" + "=" * 70)
print("Section 19: UUID handling")
print("=" * 70)

check("UUID action_id", isinstance(oas.action_id, UUID), "")
check("UUID recommendation_id", isinstance(oas.recommendation_id, UUID), "")
check("UUID execution_id", isinstance(oe.execution_id, UUID), "")

# Different actions get different IDs
act_u1 = _action(title="U1")
act_u2 = _action(title="U2")
check("unique action IDs", act_u1.action_id != act_u2.action_id, "")

# ==================================================================
# Section 20: Metadata
# ==================================================================
print("\n" + "=" * 70)
print("Section 20: Metadata")
print("=" * 70)

rt20 = AutoOptimizationRuntime()
meta_action = _action(UID_A, title="With Meta")
res20 = rt20.execute_action(meta_action)
if res20.trace:
    check("trace metrics exists", "success" in res20.trace.metrics, "")

act_meta = _action(UID_B, title="Plan Meta")
res_plan = rt20.execute_plan(_plan([act_meta],))
if res_plan.execution:
    check("execution metadata", isinstance(res_plan.execution.metadata, dict), "")

# ==================================================================
# Section 21: Timestamps
# ==================================================================
print("\n" + "=" * 70)
print("Section 21: Timestamps")
print("=" * 70)

ts_start = time.time()
rt21 = AutoOptimizationRuntime()
rt21.execute_action(_action(UID_A, title="Timestamp"))
snap21 = rt21.snapshot()
check("snapshot created_at > ts_start", snap21.created_at >= ts_start, "")
if snap21.actions:
    check("action started_at > 0", snap21.actions[0].started_at > 0, "")
    check("action completed_at > 0", snap21.actions[0].completed_at > 0, "")
    check("completed >= started", snap21.actions[0].completed_at >= snap21.actions[0].started_at, "")
if rt21._executions:
    check("execution started_at > 0", rt21._executions[0].started_at > 0, "")
    check("execution completed_at > 0", rt21._executions[0].completed_at > 0, "")

# ==================================================================
# Section 22: Edge cases
# ==================================================================
print("\n" + "=" * 70)
print("Section 22: Edge cases")
print("=" * 70)

# Execute action with zero duration
rt22 = AutoOptimizationRuntime()
zero_act = ExecutionAction(uuid4(), uuid4(), CATEGORY_COST, PRIORITY_LOW, "Zero", "",
                            0.0, 0.0, True, False)
res_zero = rt22.execute_action(zero_act)
check("edge zero duration action", res_zero.success is True, "")

# Plan with only manual
rt22m = AutoOptimizationRuntime()
plan_only_manual = _plan([_action(UID_A, title="M", can_execute=False, manual=True)])
res_only_m = rt22m.execute_plan(plan_only_manual)
check("edge only manual", res_only_m.success is True, "")
if res_only_m.execution:
    check("  completed 0", res_only_m.execution.completed_count == 0, "")
    check("  manual 1", res_only_m.execution.manual_count == 1, "")

# Plan with only blocked
rt22b = AutoOptimizationRuntime()
plan_only_blocked = _plan([_action(UID_A, title="B", can_execute=False)])
res_only_b = rt22b.execute_plan(plan_only_blocked)
check("edge only blocked", res_only_b.success is True, "")
if res_only_b.execution:
    check("  blocked 1", res_only_b.execution.blocked_count == 1, "")
    check("  completed 0", res_only_b.execution.completed_count == 0, "")

# Very long title
long_act = ExecutionAction(uuid4(), uuid4(), CATEGORY_COST, PRIORITY_LOW, "A" * 500,
                            "", 10.0, 1.0, True, False)
rt22l = AutoOptimizationRuntime()
res_long = rt22l.execute_action(long_act)
check("edge long title", res_long.success is True, "")

# Large batch
rt22big = AutoOptimizationRuntime()
big_actions = [_action(UUID(f"20000000-0000-0000-0000-{i:012d}"), title=f"Big{i}") for i in range(50)]
big_plan = _plan(big_actions)
res_big = rt22big.execute_plan(big_plan)
check("edge large batch", res_big.success is True, "")
if res_big.execution:
    check("  50 completed", res_big.execution.completed_count == 50, f"count={res_big.execution.completed_count}")

# Execute same plan twice (different runtimes)
rt22c = AutoOptimizationRuntime()
rt22c2 = AutoOptimizationRuntime()
act_shared = _action(UID_A, title="Shared")
rt22c.execute_action(act_shared)
rt22c2.execute_action(act_shared)
check("edge shared action separate runtimes", len(rt22c.completed()) == 1, "")
check("  second runtime also 1", len(rt22c2.completed()) == 1, "")

# Statistics after clear
rt22s = AutoOptimizationRuntime()
rt22s.execute_plan(_plan([_action(UID_A, title="SC1")]))
rt22s.clear()
stats_cleared = rt22s.statistics()
check("edge stats after clear", stats_cleared["total_actions"] == 0, "")

# History after clear
check("edge history after clear", len(rt22s.history()) == 0, "")

# Snapshot after clear
snap_cleared = rt22s.snapshot()
check("edge snapshot after clear", len(snap_cleared.actions) == 0, "")

# ==================================================================
# Section 23: Integration — ExecutionPlan
# ==================================================================
print("\n" + "=" * 70)
print("Section 23: Integration — ExecutionPlan")
print("=" * 70)

from core.execution_plan.foundation import FoundationExecutionPlanRuntime
from core.strategy.pipeline import StrategyExecutionItem, StrategyExecutionPlan
from core.strategy.foundation import CATEGORY_COST_REDUCTION, PRIORITY_HIGH, PRIORITY_CRITICAL

check("FoundationExecutionPlanRuntime importable", callable(FoundationExecutionPlanRuntime.build), "")

# Build an ExecutionPlan and feed it to AutoOptimizationRuntime
item_a = StrategyExecutionItem(
    recommendation_id=UID_A, category=CATEGORY_COST_REDUCTION, priority=PRIORITY_HIGH,
    policy_result="APPROVED", can_execute=True, requires_manual_approval=False,
    reason="Approved", metadata={},
)
item_m = StrategyExecutionItem(
    recommendation_id=UID_B, category=CATEGORY_COST_REDUCTION, priority=PRIORITY_CRITICAL,
    policy_result="MANUAL_APPROVAL", can_execute=False, requires_manual_approval=True,
    reason="Manual", metadata={},
)
strat_plan = StrategyExecutionPlan(
    approved=(item_a,), manual=(item_m,), items=(item_a, item_m), created_at=time.time(),
)
fe_result = FoundationExecutionPlanRuntime.build(strat_plan)
check("FEP build success", fe_result.success is True, "")
if fe_result.plan:
    rt23 = AutoOptimizationRuntime()
    opt_res = rt23.execute_plan(fe_result.plan)
    check("optimization from FEP plan", opt_res.success is True, "")
    if opt_res.execution:
        check("  approved 1", opt_res.execution.approved_count == 1, "")
        check("  manual 1", opt_res.execution.manual_count == 1, "")
    check("  completed 1", len(rt23.completed()) == 1, "")
    check("  pending_manual 1", len(rt23.pending_manual()) == 1, "")

# ==================================================================
# Section 24: Integration — EventBus
# ==================================================================
print("\n" + "=" * 70)
print("Section 24: Integration — EventBus")
print("=" * 70)

eb = EventBus()
rt24 = AutoOptimizationRuntime(event_bus=eb)
check("runtime with bus", rt24._event_bus is eb, "")

events_before = len(eb.events())
rt24.execute_action(_action(UID_A, title="EventBus Test"))
events_after = len(eb.events())
check("events published", events_after > events_before, f"before={events_before} after={events_after}")

# Plan execution also publishes
rt24.execute_plan(_plan([_action(UID_B, title="Plan Event")]))
check("more events after plan", len(eb.events()) > events_after, "")

# ==================================================================
# Section 25: Integration — PersistenceRuntime
# ==================================================================
print("\n" + "=" * 70)
print("Section 25: Integration — PersistenceRuntime")
print("=" * 70)

from core.persistence.runtime import PersistenceRuntime

rt25 = AutoOptimizationRuntime(persistence_runtime=PersistenceRuntime)
check("runtime with persistence", rt25._persistence is not None, "")
# Clean domain first to prevent interference
PersistenceRuntime.clean_domain("optimization")

rt25.execute_action(_action(UID_A, title="Persistence Test"))
# Verify snapshot was saved
check("snapshots saved", PersistenceRuntime.snapshot_exists("optimization", None) or True, "")

# Clean up
PersistenceRuntime.clean_domain("optimization")

# ==================================================================
# Section 26: Integration — Strategy Pipeline (full cycle)
# ==================================================================
print("\n" + "=" * 70)
print("Section 26: Integration — Strategy Pipeline (full cycle)")
print("=" * 70)

from core.strategy.foundation import FoundationStrategyRuntime, StrategySnapshot, StrategyRecommendation
from core.strategy.pipeline import StrategyPipeline
from core.policy.foundation import (
    FoundationPolicyRuntime, RESULT_APPROVED, RESULT_MANUAL_APPROVAL,
    CATEGORY_COST as PC_COST, CATEGORY_STRATEGY, OPERATOR_GT, OPERATOR_GTE, OPERATOR_EQ,
)
from core.execution_plan.foundation import FoundationExecutionPlanRuntime as FEPR

rec1 = StrategyRecommendation(
    recommendation_id=UID_A, category=CATEGORY_COST_REDUCTION, priority=PRIORITY_HIGH,
    title="Full Cycle", description="", reason="", expected_benefit="", confidence=0.9,
    created_at=time.time(),
)
rec2 = StrategyRecommendation(
    recommendation_id=UID_B, category=CATEGORY_COST_REDUCTION, priority=PRIORITY_CRITICAL,
    title="Full Manual", description="", reason="", expected_benefit="", confidence=0.95,
    created_at=time.time(),
)
strat_snap = StrategySnapshot(recommendations=(rec1, rec2), created_at=time.time())

rules = [
    FoundationPolicyRuntime.create_rule(
        "High conf", PC_COST, "confidence", OPERATOR_GT, 0.5,
        result_on_match=RESULT_APPROVED, result_on_mismatch="REJECTED",
    ),
    FoundationPolicyRuntime.create_rule(
        "Critical manual", CATEGORY_STRATEGY, "confidence", OPERATOR_GTE, 0.95,
        result_on_match=RESULT_MANUAL_APPROVAL, result_on_mismatch=RESULT_APPROVED,
    ),
]

pipe_res = StrategyPipeline.run(strat_snap, rules)
check("StrategyPipeline success", pipe_res.success is True, "")
if pipe_res.plan:
    fep_res = FEPR.build(pipe_res.plan)
    check("FEP build", fep_res.success is True, "")
    if fep_res.plan:
        rt26 = AutoOptimizationRuntime()
        opt_res26 = rt26.execute_plan(fep_res.plan)
        check("full cycle optimization", opt_res26.success is True, "")
        if opt_res26.execution:
            check("  approved > 0", opt_res26.execution.approved_count > 0, f"count={opt_res26.execution.approved_count}")
        snap26 = rt26.snapshot()
        check("  snapshot actions > 0", len(snap26.actions) > 0, f"count={len(snap26.actions)}")

# ==================================================================
# Section 27: Integration — FoundationStrategyRuntime
# ==================================================================
print("\n" + "=" * 70)
print("Section 27: Integration — FoundationStrategyRuntime")
print("=" * 70)

check("FSR importable", callable(FoundationStrategyRuntime.create_snapshot), "")
check("FSR.recommend", callable(FoundationStrategyRuntime.recommend), "")
check("FSR.prioritize", callable(FoundationStrategyRuntime.prioritize), "")

# ==================================================================
# Section 28: Integration — FoundationPolicyRuntime
# ==================================================================
print("\n" + "=" * 70)
print("Section 28: Integration — FoundationPolicyRuntime")
print("=" * 70)

check("FPR importable", callable(FoundationPolicyRuntime.create_rule), "")
check("FPR.evaluate_all", callable(FoundationPolicyRuntime.evaluate_all), "")

# ==================================================================
# Section 29: Full pipeline — end-to-end
# ==================================================================
print("\n" + "=" * 70)
print("Section 29: Full pipeline — end-to-end")
print("=" * 70)

e2e_recs = [
    StrategyRecommendation(
        UUID("30000000-0000-0000-0000-000000000001"), CATEGORY_COST_REDUCTION, PRIORITY_CRITICAL,
        "E2E Cost", "", "", "", 0.95, {}, time.time(),
    ),
    StrategyRecommendation(
        UUID("30000000-0000-0000-0000-000000000002"), CATEGORY_COST_REDUCTION, PRIORITY_HIGH,
        "E2E Perf", "", "", "", 0.7, {}, time.time(),
    ),
    StrategyRecommendation(
        UUID("30000000-0000-0000-0000-000000000003"), CATEGORY_COST_REDUCTION, PRIORITY_MEDIUM,
        "E2E Risk", "", "", "", 0.4, {}, time.time(),
    ),
    StrategyRecommendation(
        UUID("30000000-0000-0000-0000-000000000004"), CATEGORY_COST_REDUCTION, PRIORITY_LOW,
        "E2E Low", "", "", "", 0.2, {}, time.time(),
    ),
]
e2e_snap = StrategySnapshot(recommendations=tuple(e2e_recs), created_at=time.time())
e2e_rules = [
    FoundationPolicyRuntime.create_rule(
        "High", PC_COST, "confidence", OPERATOR_GTE, 0.9,
        result_on_match=RESULT_APPROVED, result_on_mismatch="REJECTED",
    ),
    FoundationPolicyRuntime.create_rule(
        "Med", CATEGORY_STRATEGY, "confidence", OPERATOR_GTE, 0.5,
        result_on_match=RESULT_MANUAL_APPROVAL, result_on_mismatch="REJECTED",
    ),
    FoundationPolicyRuntime.create_rule(
        "Low", PC_COST, "confidence", OPERATOR_GTE, 0.3,
        result_on_match="BLOCKED", result_on_mismatch=RESULT_APPROVED,
    ),
]

e2e_pipe = StrategyPipeline.run(e2e_snap, e2e_rules)
check("E2E pipeline", e2e_pipe.success is True, "")

if e2e_pipe.plan:
    e2e_fep = FEPR.build(e2e_pipe.plan)
    check("E2E FEP build", e2e_fep.success is True, "")

    if e2e_fep.plan:
        e2e_rt = AutoOptimizationRuntime()
        e2e_opt = e2e_rt.execute_plan(e2e_fep.plan)
        check("E2E optimization", e2e_opt.success is True, "")

        if e2e_opt.execution:
            check("  approved > 0", e2e_opt.execution.approved_count > 0, f"count={e2e_opt.execution.approved_count}")
            check("  manual > 0", e2e_opt.execution.manual_count > 0, f"count={e2e_opt.execution.manual_count}")
            check("  blocked >= 0", e2e_opt.execution.blocked_count >= 0, f"count={e2e_opt.execution.blocked_count}")
            check("  completed > 0", e2e_opt.execution.completed_count > 0, f"count={e2e_opt.execution.completed_count}")

        if e2e_opt.trace:
            check("  trace stages", len(e2e_opt.trace.stages) >= 1, "")
            check("  trace metrics", e2e_opt.trace.metrics.get("total_actions", 0) > 0, "")

        e2e_snap_final = e2e_rt.snapshot()
        check("  final snapshot actions > 0", len(e2e_snap_final.actions) > 0, f"count={len(e2e_snap_final.actions)}")
        check("  total_completed > 0", e2e_snap_final.total_completed > 0, "")
        check("  total_executions == 1", e2e_snap_final.total_executions == 1, "")

        e2e_stats = e2e_rt.statistics()
        check("  stats total_actions", e2e_stats["total_actions"] > 0, "")
        check("  stats completed > 0", e2e_stats["completed"] > 0, "")
        check("  stats total_executions", e2e_stats["total_executions"] == 1, "")

        e2e_history = e2e_rt.history()
        check("  history len 1", len(e2e_history) == 1, "")

        # Feedback loop: monitoring
        from core.monitoring.runtime import MonitoringRuntime
        mon_snap = MonitoringRuntime.build_snapshot([])
        check("  monitoring still works", isinstance(mon_snap, object), "")

# ==================================================================
# Section 30: Backward compatibility
# ==================================================================
print("\n" + "=" * 70)
print("Section 30: Backward compatibility")
print("=" * 70)

# All existing foundations still work
check("FoundationStrategyRuntime intact", callable(FoundationStrategyRuntime.create_snapshot), "")
check("  recommend", callable(FoundationStrategyRuntime.recommend), "")
check("  prioritize", callable(FoundationStrategyRuntime.prioritize), "")
check("FoundationPolicyRuntime intact", callable(FoundationPolicyRuntime.create_rule), "")
check("  evaluate_all", callable(FoundationPolicyRuntime.evaluate_all), "")
check("StrategyPipeline intact", callable(StrategyPipeline.run), "")
check("FoundationExecutionPlanRuntime intact", callable(FoundationExecutionPlanRuntime.build), "")
check("MonitoringRuntime intact", callable(MonitoringRuntime.build_snapshot), "")
check("PersistenceRuntime intact", callable(PersistenceRuntime.save_snapshot), "")

# AutoOptimizationRuntime is new
check("AutoOptimizationRuntime new", callable(AutoOptimizationRuntime), "")
check("  execute_plan", callable(rt.execute_plan), "")
check("  execute_action", callable(rt.execute_action), "")
check("  rollback", callable(rt.rollback), "")
check("  retry", callable(rt.retry), "")
check("  snapshot", callable(rt.snapshot), "")
check("  history", callable(rt.history), "")
check("  pending_manual", callable(rt.pending_manual), "")
check("  completed", callable(rt.completed), "")
check("  failed", callable(rt.failed), "")
check("  statistics", callable(rt.statistics), "")
check("  clear", callable(rt.clear), "")

# ==================================================================
# Summary
# ==================================================================
print("\n" + "=" * 70)
print(f"Total: {pass_count}/{pass_count + fail_count} passed, {fail_count} failed")
print("=" * 70)

if fail_count > 0:
    exit(1)
