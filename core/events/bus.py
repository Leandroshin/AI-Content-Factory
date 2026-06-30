"""Event bus contracts for AI Content Factory."""

from __future__ import annotations

from abc import ABC, abstractmethod

from .models import Event
from .result import EventResult


class EventBus(ABC):
    """Base contract for event buses."""

    @abstractmethod
    def publish(self, event: Event) -> EventResult:
        """Publish an event placeholder and return a result placeholder."""
