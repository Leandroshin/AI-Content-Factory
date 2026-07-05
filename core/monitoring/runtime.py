"""Monitoring Runtime — event-driven platform observability.

Stateless, side-effect-free monitoring using EventBus events.
All methods are @staticmethod. All models are frozen dataclasses.

Compatible with PersistenceRuntime (save/load snapshots natively)
and PerformanceRuntime (snapshot metrics can be aggregated).
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Any
from uuid import UUID

from core.events.bus import EventBus, EventEnvelope


# ------------------------------------------------------------------
# Domain inference helpers
# ------------------------------------------------------------------

_DOMAIN_BY_PREFIX: dict[str, str] = {
    "CompanyTask": "company_task",
    "Department": "department",
    "Employee": "employee",
    "Orchestrator": "orchestrator",
    "Collaboration": "collaboration",
    "Conversation": "conversation",
    "Knowledge": "knowledge",
    "Learning": "learning",
    "Recommendation": "learning",
    "Participant": "collaboration",
    "MessageAdded": "conversation",
    "MemoryRecord": "memory",
    "Memory": "memory",
    "Workflow": "workflow",
    "WorkflowTask": "workflow",
    "Execution": "execution",
    "Decision": "decision",
    "Skill": "skill",
    "Result": "result",
    "Task": "task",
    "Company": "company",
}

_DOMAIN_BY_SUFFIX: dict[str, str] = {
    "StateChangedEvent": "state",
    "CompanyTask": "company_task",
}


def _infer_domain(event: Any) -> str:
    """Determine the domain of an event based on its class name."""
    name = event.__class__.__name__
    for prefix, domain in _DOMAIN_BY_PREFIX.items():
        if name.startswith(prefix):
            return domain
    if "StateChangedEvent" in name:
        return _DOMAIN_BY_SUFFIX.get("StateChangedEvent", "state")
    return "unknown"


# ------------------------------------------------------------------
# Success inference helpers
# ------------------------------------------------------------------


def _detect_success(event: Any) -> bool | None:
    """Determine whether an event represents success, failure, or neutral."""
    if hasattr(event, "success"):
        return bool(event.success)
    name = event.__class__.__name__
    if any(x in name for x in ("Fail", "Reject")):
        return False
    if any(x in name for x in ("Approv", "Promot")):
        return True
    if "Complet" in name:
        return True
    return None


# ------------------------------------------------------------------
# Data models
# ------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class MonitoringEvent:
    """Normalised representation of a single observed event."""

    event_type: str
    domain: str
    source: str
    entity_id: UUID | None = None
    timestamp: float = 0.0
    success: bool | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class MonitoringSnapshot:
    """Immutable point-in-time view of all monitored events."""

    total_events: int = 0
    total_errors: int = 0
    total_success: int = 0
    events_by_type: dict[str, int] = field(default_factory=dict)
    events_by_domain: dict[str, int] = field(default_factory=dict)
    first_timestamp: float = 0.0
    last_timestamp: float = 0.0
    uptime: float = 0.0
    success_rate: float = 0.0
    error_rate: float = 0.0
    event_rate: float = 0.0
    health_score: float = 50.0
    timeline: tuple[MonitoringEvent, ...] = field(default_factory=tuple)
    metadata: dict[str, Any] = field(default_factory=dict)

    def timeline_sorted(self) -> tuple[MonitoringEvent, ...]:
        return tuple(sorted(self.timeline, key=lambda e: e.timestamp))


@dataclass(frozen=True, slots=True)
class MonitoringTrace:
    """Metadata about a monitoring operation."""

    events_consumed: int = 0
    operation: str = ""
    duration_ms: float = 0.0
    snapshot_size: int = 0


@dataclass(frozen=True, slots=True)
class MonitoringResult:
    """Output of a monitoring operation."""

    success: bool
    snapshot: MonitoringSnapshot | None = None
    trace: MonitoringTrace | None = None
    error_message: str = ""


# ------------------------------------------------------------------
# Helpers
# ------------------------------------------------------------------


def _now() -> float:
    return time.time()


def _to_monitoring_event(event: Any) -> MonitoringEvent:
    """Normalise any event into a MonitoringEvent."""
    return MonitoringEvent(
        event_type=EventEnvelope.get_event_type(event),
        domain=_infer_domain(event),
        source=EventEnvelope.get_source(event),
        entity_id=EventEnvelope.get_entity_id(event),
        timestamp=EventEnvelope.get_timestamp(event),
        success=_detect_success(event),
        metadata=EventEnvelope.get_payload(event),
    )


def _compute_metrics(
    events: list[MonitoringEvent],
    start_time: float,
) -> dict[str, Any]:
    """Compute all snapshot fields from a list of MonitoringEvents."""
    total = len(events)
    if total == 0:
        return {
            "total_events": 0,
            "total_errors": 0,
            "total_success": 0,
            "events_by_type": {},
            "events_by_domain": {},
            "first_timestamp": 0.0,
            "last_timestamp": 0.0,
            "uptime": 0.0,
            "success_rate": 0.0,
            "error_rate": 0.0,
            "event_rate": 0.0,
            "health_score": 35.0,
        }

    errors = sum(1 for e in events if e.success is False)
    successes = sum(1 for e in events if e.success is True)

    by_type: dict[str, int] = {}
    by_domain: dict[str, int] = {}
    first_ts = events[0].timestamp
    last_ts = events[0].timestamp

    for e in events:
        by_type[e.event_type] = by_type.get(e.event_type, 0) + 1
        by_domain[e.domain] = by_domain.get(e.domain, 0) + 1
        if e.timestamp < first_ts:
            first_ts = e.timestamp
        if e.timestamp > last_ts:
            last_ts = e.timestamp

    uptime = last_ts - first_ts if last_ts > first_ts else 0.0
    success_rate = successes / total * 100.0 if total > 0 else 0.0
    error_rate = errors / total * 100.0 if total > 0 else 0.0
    event_rate = total / uptime if uptime > 0 else 0.0

    health = 50.0
    health += success_rate * 0.3
    health -= error_rate * 0.3
    health = max(0.0, min(100.0, health))

    return {
        "total_events": total,
        "total_errors": errors,
        "total_success": successes,
        "events_by_type": dict(sorted(by_type.items())),
        "events_by_domain": dict(sorted(by_domain.items())),
        "first_timestamp": first_ts,
        "last_timestamp": last_ts,
        "uptime": uptime,
        "success_rate": round(success_rate, 6),
        "error_rate": round(error_rate, 6),
        "event_rate": round(event_rate, 6),
        "health_score": round(health, 6),
    }


# ------------------------------------------------------------------
# MonitoringRuntime
# ------------------------------------------------------------------


class MonitoringRuntime:
    """Stateless event-driven monitoring runtime.

    All methods are @staticmethod. No mutable state.
    Processes events from any source and produces snapshots.
    """

    # --------------------------------------------------------------
    # Core
    # --------------------------------------------------------------

    @staticmethod
    def create_monitor() -> MonitoringResult:
        """Create an empty monitoring result with no events."""
        snapshot = MonitoringSnapshot(
            health_score=35.0,
        )
        return MonitoringResult(
            success=True,
            snapshot=snapshot,
            trace=MonitoringTrace(
                events_consumed=0,
                operation="create_monitor",
                duration_ms=0.0,
                snapshot_size=0,
            ),
        )

    @staticmethod
    def consume_event(
        snapshot: MonitoringSnapshot,
        event: Any,
    ) -> MonitoringSnapshot:
        """Incrementally add a single event to an existing snapshot."""
        start = _now()
        me = _to_monitoring_event(event)
        all_events = list(snapshot.timeline) + [me]
        metrics = _compute_metrics(all_events, start)
        return MonitoringSnapshot(
            **metrics,
            timeline=tuple(all_events),
            metadata=snapshot.metadata,
        )

    @staticmethod
    def consume_events(
        snapshot: MonitoringSnapshot,
        events: list[Any],
    ) -> MonitoringSnapshot:
        """Incrementally add multiple events to an existing snapshot."""
        start = _now()
        new_events = [_to_monitoring_event(e) for e in events]
        all_events = list(snapshot.timeline) + new_events
        metrics = _compute_metrics(all_events, start)
        return MonitoringSnapshot(
            **metrics,
            timeline=tuple(all_events),
            metadata=snapshot.metadata,
        )

    @staticmethod
    def build_snapshot(
        events: list[Any],
    ) -> MonitoringSnapshot:
        """Build a fresh snapshot from a list of raw events."""
        start = _now()
        mes = [_to_monitoring_event(e) for e in events]
        metrics = _compute_metrics(mes, start)
        return MonitoringSnapshot(
            **metrics,
            timeline=tuple(mes),
        )

    @staticmethod
    def build_result(
        snapshot: MonitoringSnapshot,
        operation: str = "monitor",
    ) -> MonitoringResult:
        """Wrap a snapshot in a MonitoringResult with a trace."""
        start = _now()
        duration = (_now() - start) * 1000.0
        return MonitoringResult(
            success=True,
            snapshot=snapshot,
            trace=MonitoringTrace(
                events_consumed=snapshot.total_events,
                operation=operation,
                duration_ms=duration,
                snapshot_size=snapshot.total_events,
            ),
        )

    @staticmethod
    def build_trace(
        snapshot: MonitoringSnapshot,
        operation: str = "monitor",
        duration_ms: float = 0.0,
    ) -> MonitoringTrace:
        """Create a MonitoringTrace from a snapshot."""
        return MonitoringTrace(
            events_consumed=snapshot.total_events,
            operation=operation,
            duration_ms=duration_ms,
            snapshot_size=snapshot.total_events,
        )

    # --------------------------------------------------------------
    # Metrics calculators
    # --------------------------------------------------------------

    @staticmethod
    def calculate_health(snapshot: MonitoringSnapshot) -> float:
        """Calculate health score [0, 100] from snapshot metrics."""
        return snapshot.health_score

    @staticmethod
    def calculate_uptime(snapshot: MonitoringSnapshot) -> float:
        """Return uptime (last - first timestamp) in seconds."""
        return snapshot.uptime

    @staticmethod
    def calculate_event_rate(snapshot: MonitoringSnapshot) -> float:
        """Return events per second."""
        return snapshot.event_rate

    @staticmethod
    def calculate_error_rate(snapshot: MonitoringSnapshot) -> float:
        """Return error rate as a percentage [0, 100]."""
        return snapshot.error_rate

    @staticmethod
    def calculate_success_rate(snapshot: MonitoringSnapshot) -> float:
        """Return success rate as a percentage [0, 100]."""
        return snapshot.success_rate

    # --------------------------------------------------------------
    # Snapshot operations
    # --------------------------------------------------------------

    @staticmethod
    def merge_snapshots(
        snapshots: list[MonitoringSnapshot],
    ) -> MonitoringSnapshot:
        """Merge multiple snapshots into one consolidated snapshot."""
        start = _now()
        all_events: list[MonitoringEvent] = []
        merged_metadata: dict[str, Any] = {}
        for s in snapshots:
            all_events.extend(s.timeline)
            merged_metadata.update(s.metadata)

        metrics = _compute_metrics(all_events, start)
        return MonitoringSnapshot(
            **metrics,
            timeline=tuple(all_events),
            metadata=merged_metadata,
        )

    # --------------------------------------------------------------
    # Event filtering and grouping
    # --------------------------------------------------------------

    @staticmethod
    def filter_events(
        events: list[Any],
        event_type: str | None = None,
        domain: str | None = None,
        success: bool | None = None,
    ) -> list[Any]:
        """Filter raw events by type name, inferred domain, or success status."""
        result = list(events)
        if event_type is not None:
            result = [e for e in result if e.__class__.__name__ == event_type]
        if domain is not None:
            result = [e for e in result if _infer_domain(e) == domain]
        if success is not None:
            result = [e for e in result if _detect_success(e) is success]
        return result

    @staticmethod
    def group_by_type(
        events: list[Any],
    ) -> dict[str, list[Any]]:
        """Group raw events by their class name."""
        groups: dict[str, list[Any]] = {}
        for e in events:
            name = e.__class__.__name__
            groups.setdefault(name, []).append(e)
        return dict(sorted(groups.items()))

    @staticmethod
    def group_by_domain(
        events: list[Any],
    ) -> dict[str, list[Any]]:
        """Group raw events by their inferred domain."""
        groups: dict[str, list[Any]] = {}
        for e in events:
            domain = _infer_domain(e)
            groups.setdefault(domain, []).append(e)
        return dict(sorted(groups.items()))

    @staticmethod
    def timeline(
        events: list[Any],
    ) -> list[MonitoringEvent]:
        """Convert raw events to a chronologically sorted timeline of MonitoringEvents."""
        mes = [_to_monitoring_event(e) for e in events]
        mes.sort(key=lambda x: x.timestamp)
        return mes

    # --------------------------------------------------------------
    # EventBus integration
    # --------------------------------------------------------------

    @staticmethod
    def consume_from_bus(
        bus: EventBus,
    ) -> MonitoringSnapshot:
        """Consume all events currently stored on an EventBus and build a snapshot."""
        return MonitoringRuntime.build_snapshot(bus.events())
