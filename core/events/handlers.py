"""Event handler contracts for AI Content Factory."""

from __future__ import annotations

from abc import ABC, abstractmethod

from .models import Event
from .result import EventResult


class EventHandler(ABC):
    """Base contract for event handlers."""

    name: str

    @abstractmethod
    def can_handle(self, event: Event) -> bool:
        """Return whether the handler can process an event."""

    @abstractmethod
    def handle(self, event: Event) -> EventResult:
        """Return a placeholder result for the event."""
