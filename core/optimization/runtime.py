"""Auto Optimization Runtime — stateful execution engine for approved strategy plans.

Consumes ExecutionPlans from FoundationExecutionPlanRuntime, executes only
approved actions, tracks history, supports retry/rollback/cooldown,
and optionally integrates with EventBus and PersistenceRuntime.
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Any
from uuid import UUID, uuid4

from core.execution_plan.foundation import ExecutionAction, ExecutionPlan

# ------------------------------------------------------------------
# Constants
# ------------------------------------------------------------------

ACTION_STATE_PENDING = "PENDING"
ACTION_STATE_RUNNING = "RUNNING"
ACTION_STATE_COMPLETED = "COMPLETED"
ACTION_STATE_FAILED = "FAILED"
ACTION_STATE_ROLLED_BACK = "ROLLED_BACK"
ACTION_STATE_SKIPPED = "SKIPPED"
ACTION_STATE_MANUAL = "MANUAL"

DEFAULT_COOLDOWN_SECONDS: float = 60.0
DEFAULT_MAX_RETRIES: int = 3
DEFAULT_RETRY_DELAY_SECONDS: float = 5.0
OPTIMIZATION_DOMAIN: str = "optimization"

# ------------------------------------------------------------------
# Data models
# ------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class OptimizationActionState:
    """Immutable record of an action's execution state."""

    action_id: UUID
    recommendation_id: UUID
    title: str
    category: str
    priority: str
    state: str
    attempt: int
    can_execute: bool
    requires_manual_approval: bool
    started_at: float = 0.0
    completed_at: float = 0.0
    duration: float = 0.0
    error_message: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class OptimizationExecution:
    """Record of a single execution batch."""

    execution_id: UUID
    plan_created_at: float
    total_actions: int
    approved_count: int
    manual_count: int
    blocked_count: int
    completed_count: int
    failed_count: int
    rolled_back_count: int
    total_duration: float
    started_at: float
    completed_at: float
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class OptimizationSnapshot:
    """Complete current state of the optimization runtime."""

    actions: tuple[OptimizationActionState, ...] = field(default_factory=tuple)
    executions: tuple[OptimizationExecution, ...] = field(default_factory=tuple)
    total_completed: int = 0
    total_failed: int = 0
    total_rolled_back: int = 0
    total_retries: int = 0
    total_executions: int = 0
    created_at: float = 0.0
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class OptimizationTrace:
    """Metadata about an optimization operation."""

    stages: tuple[str, ...] = field(default_factory=tuple)
    duration_ms: float = 0.0
    actions_processed: int = 0
    metrics: dict[str, float] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class OptimizationResult:
    """Output of an optimization operation."""

    success: bool
    snapshot: OptimizationSnapshot | None = None
    trace: OptimizationTrace | None = None
    execution: OptimizationExecution | None = None
    error_message: str = ""


# ------------------------------------------------------------------
# Helpers
# ------------------------------------------------------------------


def _now() -> float:
    return time.time()


def _build_action_state(
    action: ExecutionAction,
    state: str,
    attempt: int = 1,
    started_at: float = 0.0,
    completed_at: float = 0.0,
    duration: float = 0.0,
    error_message: str = "",
) -> OptimizationActionState:
    return OptimizationActionState(
        action_id=action.action_id,
        recommendation_id=action.recommendation_id,
        title=action.title,
        category=action.category,
        priority=action.priority,
        state=state,
        attempt=attempt,
        can_execute=action.can_execute,
        requires_manual_approval=action.requires_manual_approval,
        started_at=started_at,
        completed_at=completed_at,
        duration=duration,
        error_message=error_message,
        metadata=dict(action.metadata),
    )


# ------------------------------------------------------------------
# AutoOptimizationRuntime
# ------------------------------------------------------------------


class AutoOptimizationRuntime:
    """Stateful runtime that executes approved optimization actions.

    Consumes ExecutionPlans, executes only approved actions, tracks
    history, supports retry and rollback, and optionally integrates
    with EventBus and PersistenceRuntime.
    """

    def __init__(
        self,
        event_bus: Any = None,
        persistence_runtime: Any = None,
        max_retries: int = DEFAULT_MAX_RETRIES,
        cooldown_seconds: float = DEFAULT_COOLDOWN_SECONDS,
        retry_delay_seconds: float = DEFAULT_RETRY_DELAY_SECONDS,
    ) -> None:
        self._event_bus = event_bus
        self._persistence = persistence_runtime
        self._max_retries = max_retries
        self._cooldown = cooldown_seconds
        self._retry_delay = retry_delay_seconds

        self._actions: dict[UUID, OptimizationActionState] = {}
        self._executions: list[OptimizationExecution] = []
        self._retry_tracker: dict[UUID, int] = {}  # action_id -> attempt count
        self._cooldown_tracker: dict[UUID, float] = {}  # action_id -> last execution timestamp
        self._metadata: dict[str, Any] = {}

    # --------------------------------------------------------------
    # Core execution
    # --------------------------------------------------------------

    def execute_plan(
        self,
        plan: ExecutionPlan,
        metadata: dict[str, Any] | None = None,
    ) -> OptimizationResult:
        """Execute all approved actions in an ExecutionPlan."""
        stages: list[str] = ["execute_plan"]
        start = _now()

        if plan is None:
            return OptimizationResult(
                success=False,
                error_message="ExecutionPlan is None",
            )

        approved = list(plan.approved_actions)
        manual = list(plan.manual_actions)
        blocked = list(plan.blocked_actions)

        execution_id = uuid4()
        started_at = _now()

        completed_count = 0
        failed_count = 0

        for action in approved:
            if self._is_on_cooldown(action.action_id):
                continue
            result = self.execute_action(action)
            if result.success:
                completed_count += 1
            else:
                failed_count += 1

        for action in manual:
            self._mark_manual(action)

        for action in blocked:
            self._mark_skipped(action)

        now = _now()
        total_duration = now - started_at

        exec_record = OptimizationExecution(
            execution_id=execution_id,
            plan_created_at=plan.created_at,
            total_actions=len(approved) + len(manual) + len(blocked),
            approved_count=len(approved),
            manual_count=len(manual),
            blocked_count=len(blocked),
            completed_count=completed_count,
            failed_count=failed_count,
            rolled_back_count=0,
            total_duration=total_duration,
            started_at=started_at,
            completed_at=now,
            metadata=metadata or {},
        )
        self._executions.append(exec_record)

        snap = self.snapshot()
        duration_ms = (now - start) * 1000.0
        trace = OptimizationTrace(
            stages=tuple(stages),
            duration_ms=duration_ms,
            actions_processed=len(approved),
            metrics={
                "total_actions": float(len(approved)),
                "completed": float(completed_count),
                "failed": float(failed_count),
                "manual": float(len(manual)),
                "blocked": float(len(blocked)),
            },
        )

        self._persist_snapshot(snap)

        return OptimizationResult(
            success=failed_count == 0,
            snapshot=snap,
            trace=trace,
            execution=exec_record,
        )

    def execute_action(
        self,
        action: ExecutionAction,
    ) -> OptimizationResult:
        """Execute a single approved action."""
        stages: list[str] = ["execute_action"]
        start = _now()

        if not action.can_execute:
            state = _build_action_state(action, ACTION_STATE_SKIPPED)
            self._actions[action.action_id] = state
            return OptimizationResult(
                success=False,
                error_message=f"Action '{action.title}' is not executable",
            )

        if self._is_duplicate(action.action_id):
            existing = self._actions.get(action.action_id)
            return OptimizationResult(
                success=False,
                error_message=f"Action '{action.title}' already executed",
            )

        attempt = self._retry_tracker.get(action.action_id, 0) + 1
        self._retry_tracker[action.action_id] = attempt
        self._cooldown_tracker[action.action_id] = _now()

        started_at = _now()
        success = self._simulate_execution(action)
        now = _now()
        duration = now - started_at

        state = ACTION_STATE_COMPLETED if success else ACTION_STATE_FAILED
        state_obj = _build_action_state(
            action, state, attempt=attempt,
            started_at=started_at, completed_at=now, duration=duration,
            error_message="" if success else "Simulated execution failure",
        )
        self._actions[action.action_id] = state_obj

        self._publish_event(action, state, duration)

        snap = self.snapshot()
        duration_ms = (now - start) * 1000.0
        trace = OptimizationTrace(
            stages=tuple(stages),
            duration_ms=duration_ms,
            actions_processed=1,
            metrics={"success": 1.0 if success else 0.0, "duration": duration},
        )

        self._persist_snapshot(snap)

        return OptimizationResult(
            success=success,
            snapshot=snap,
            trace=trace,
        )

    # --------------------------------------------------------------
    # Rollback & Retry
    # --------------------------------------------------------------

    def rollback(
        self,
        action_id: UUID,
    ) -> OptimizationResult:
        """Rollback a previously completed action."""
        stages: list[str] = ["rollback"]
        start = _now()

        existing = self._actions.get(action_id)
        if existing is None:
            return OptimizationResult(
                success=False,
                error_message=f"Action {action_id} not found",
            )

        if existing.state != ACTION_STATE_COMPLETED:
            return OptimizationResult(
                success=False,
                error_message=f"Action '{existing.title}' is in state '{existing.state}', cannot rollback",
            )

        now = _now()
        rolled = OptimizationActionState(
            action_id=existing.action_id,
            recommendation_id=existing.recommendation_id,
            title=existing.title,
            category=existing.category,
            priority=existing.priority,
            state=ACTION_STATE_ROLLED_BACK,
            attempt=existing.attempt,
            can_execute=existing.can_execute,
            requires_manual_approval=existing.requires_manual_approval,
            started_at=existing.started_at,
            completed_at=now,
            duration=now - existing.started_at,
            error_message="Rolled back",
            metadata=dict(existing.metadata),
        )
        self._actions[action_id] = rolled

        self._publish_event(None, ACTION_STATE_ROLLED_BACK, 0.0, action_id)

        snap = self.snapshot()
        duration_ms = (now - start) * 1000.0
        trace = OptimizationTrace(
            stages=tuple(stages),
            duration_ms=duration_ms,
            actions_processed=1,
            metrics={"action": 1.0},
        )
        self._persist_snapshot(snap)

        return OptimizationResult(success=True, snapshot=snap, trace=trace)

    def retry(
        self,
        action_id: UUID,
    ) -> OptimizationResult:
        """Retry a failed action."""
        stages: list[str] = ["retry"]
        start = _now()

        existing = self._actions.get(action_id)
        if existing is None:
            return OptimizationResult(
                success=False,
                error_message=f"Action {action_id} not found",
            )

        if existing.state != ACTION_STATE_FAILED:
            return OptimizationResult(
                success=False,
                error_message=f"Action '{existing.title}' is in state '{existing.state}', can only retry FAILED",
            )

        attempt = self._retry_tracker.get(action_id, 0) + 1
        if attempt > self._max_retries:
            return OptimizationResult(
                success=False,
                error_message=f"Action '{existing.title}' exceeded max retries ({self._max_retries})",
            )

        self._retry_tracker[action_id] = attempt

        started_at = _now()
        success = self._simulate_execution(None, force_success=(attempt <= 2))
        now = _now()
        duration = now - started_at

        state = ACTION_STATE_COMPLETED if success else ACTION_STATE_FAILED
        state_obj = OptimizationActionState(
            action_id=existing.action_id,
            recommendation_id=existing.recommendation_id,
            title=existing.title,
            category=existing.category,
            priority=existing.priority,
            state=state,
            attempt=attempt,
            can_execute=existing.can_execute,
            requires_manual_approval=existing.requires_manual_approval,
            started_at=started_at,
            completed_at=now,
            duration=duration,
            error_message="" if success else "Retry failed",
            metadata=dict(existing.metadata),
        )
        self._actions[action_id] = state_obj

        snap = self.snapshot()
        duration_ms = (now - start) * 1000.0
        trace = OptimizationTrace(
            stages=tuple(stages),
            duration_ms=duration_ms,
            actions_processed=1,
            metrics={"success": 1.0 if success else 0.0, "attempt": float(attempt)},
        )
        self._persist_snapshot(snap)

        return OptimizationResult(success=success, snapshot=snap, trace=trace)

    # --------------------------------------------------------------
    # Queries
    # --------------------------------------------------------------

    def snapshot(self) -> OptimizationSnapshot:
        """Return the current optimization state snapshot."""
        actions = list(self._actions.values())
        total_completed = sum(1 for a in actions if a.state == ACTION_STATE_COMPLETED)
        total_failed = sum(1 for a in actions if a.state == ACTION_STATE_FAILED)
        total_rolled_back = sum(1 for a in actions if a.state == ACTION_STATE_ROLLED_BACK)
        total_retries = sum(max(0, v - 1) for v in self._retry_tracker.values())
        return OptimizationSnapshot(
            actions=tuple(actions),
            executions=tuple(self._executions),
            total_completed=total_completed,
            total_failed=total_failed,
            total_rolled_back=total_rolled_back,
            total_retries=total_retries,
            total_executions=len(self._executions),
            created_at=_now(),
            metadata=dict(self._metadata),
        )

    def history(self) -> list[OptimizationExecution]:
        """Return all execution records."""
        return list(self._executions)

    def pending_manual(self) -> list[OptimizationActionState]:
        """Return actions pending manual approval (MANUAL state)."""
        return [a for a in self._actions.values() if a.state == ACTION_STATE_MANUAL]

    def completed(self) -> list[OptimizationActionState]:
        """Return completed actions."""
        return [a for a in self._actions.values() if a.state == ACTION_STATE_COMPLETED]

    def failed(self) -> list[OptimizationActionState]:
        """Return failed actions."""
        return [a for a in self._actions.values() if a.state == ACTION_STATE_FAILED]

    def statistics(self) -> dict[str, Any]:
        """Return execution statistics."""
        actions = list(self._actions.values())
        completed_actions = [a for a in actions if a.state == ACTION_STATE_COMPLETED]
        failed_actions = [a for a in actions if a.state == ACTION_STATE_FAILED]
        total_duration = sum(a.duration for a in completed_actions)
        avg_duration = total_duration / max(len(completed_actions), 1)
        return {
            "total_actions": len(actions),
            "completed": len(completed_actions),
            "failed": len(failed_actions),
            "rolled_back": sum(1 for a in actions if a.state == ACTION_STATE_ROLLED_BACK),
            "manual": sum(1 for a in actions if a.state == ACTION_STATE_MANUAL),
            "skipped": sum(1 for a in actions if a.state == ACTION_STATE_SKIPPED),
            "total_executions": len(self._executions),
            "total_retries": sum(max(0, v - 1) for v in self._retry_tracker.values()),
            "avg_duration": avg_duration,
            "total_duration": total_duration,
            "max_retries": self._max_retries,
            "cooldown_seconds": self._cooldown,
        }

    def clear(self) -> None:
        """Reset all runtime state."""
        self._actions.clear()
        self._executions.clear()
        self._retry_tracker.clear()
        self._cooldown_tracker.clear()
        self._metadata.clear()

    # --------------------------------------------------------------
    # Internal helpers
    # --------------------------------------------------------------

    def _is_on_cooldown(self, action_id: UUID) -> bool:
        last = self._cooldown_tracker.get(action_id, 0.0)
        if last == 0.0:
            return False
        return (_now() - last) < self._cooldown

    def _is_duplicate(self, action_id: UUID) -> bool:
        existing = self._actions.get(action_id)
        if existing is None:
            return False
        return existing.state in (ACTION_STATE_COMPLETED, ACTION_STATE_RUNNING)

    def _mark_manual(self, action: ExecutionAction) -> None:
        state = _build_action_state(action, ACTION_STATE_MANUAL)
        self._actions[action.action_id] = state

    def _mark_skipped(self, action: ExecutionAction) -> None:
        state = _build_action_state(action, ACTION_STATE_SKIPPED)
        self._actions[action.action_id] = state

    def _simulate_execution(
        self,
        action: ExecutionAction | None,
        force_success: bool = True,
    ) -> bool:
        """Simulate executing an action. In production this would call
        CompanyRuntime, WorkflowRuntime, etc."""
        return force_success

    def _publish_event(
        self,
        action: ExecutionAction | None,
        state: str,
        duration: float,
        action_id: UUID | None = None,
    ) -> None:
        if self._event_bus is None:
            return
        aid = action_id or (action.action_id if action else UUID(int=0))
        try:
            from core.events.domain_events import ExecutionCompleted, ExecutionFailed
            if state == ACTION_STATE_COMPLETED:
                event = ExecutionCompleted(
                    execution_id=aid,
                    output=f"Action completed in {duration:.3f}s",
                    timestamp=_now(),
                )
            elif state == ACTION_STATE_FAILED:
                event = ExecutionFailed(
                    execution_id=aid,
                    error_message="Execution failed",
                    timestamp=_now(),
                )
            else:
                event = ExecutionCompleted(
                    execution_id=aid,
                    output=f"Action state: {state}",
                    timestamp=_now(),
                )
            self._event_bus.publish(event)
        except ImportError:
            pass

    def _persist_snapshot(self, snap: OptimizationSnapshot) -> None:
        if self._persistence is None:
            return
        try:
            self._persistence.save_snapshot(
                snap, OPTIMIZATION_DOMAIN, f"snapshot_{_now()}",
            )
        except Exception:
            pass
