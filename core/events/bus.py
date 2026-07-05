"""Event bus for AI Content Factory."""

from __future__ import annotations

from collections import defaultdict
from typing import Any, Callable, DefaultDict

EventCallback = Callable[[Any], None]


class EventBus:
    """Deterministic in-memory event bus."""

    def __init__(self) -> None:
        self._subscribers: DefaultDict[type[Any], list[EventCallback]] = defaultdict(list)
        self._events: list[Any] = []

    def subscribe(self, event_type: type[Any], callback: EventCallback) -> None:
        self._subscribers[event_type].append(callback)

    def publish(self, event: Any) -> None:
        self._events.append(event)
        for event_type, callbacks in self._subscribers.items():
            if isinstance(event, event_type):
                for callback in list(callbacks):
                    callback(event)

    def events(self) -> list[Any]:
        return list(self._events)


class EventEnvelope:
    """Lightweight, non-invasive read-only utility to extract standard envelope fields from events."""

    @staticmethod
    def get_event_type(event: Any) -> str:
        """Extract event type name."""
        return event.__class__.__name__

    @staticmethod
    def get_source(event: Any) -> str:
        """Extract event source, default to 'runtime'."""
        return getattr(event, "source", "runtime")

    @staticmethod
    def get_entity_id(event: Any) -> UUID | None:
        """Resolve the target entity UUID from the event."""
        from uuid import UUID
        for attr in ("task_id", "workflow_id", "result_id", "knowledge_id", "skill_id", "employee_id", "department_id"):
            if hasattr(event, attr):
                val = getattr(event, attr)
                if isinstance(val, UUID):
                    return val
        return None

    @staticmethod
    def get_timestamp(event: Any) -> float:
        """Extract event timestamp, default to 0.0."""
        return getattr(event, "timestamp", 0.0)

    @staticmethod
    def get_payload(event: Any) -> dict[str, Any]:
        """Extract event payload dict, default to empty dict."""
        return getattr(event, "payload", {})
