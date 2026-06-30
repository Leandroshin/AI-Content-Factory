"""Domain event subscriber contracts for AI Content Factory."""

from __future__ import annotations

from abc import ABC, abstractmethod

from .contracts import BaseEventSubscriber
from .models import EventType


class EventSubscriber(BaseEventSubscriber, ABC):
    """Base event subscriber contract."""

    @abstractmethod
    def accepts(self, event_type: EventType) -> bool:
        """Return whether the subscriber can accept an event type."""
