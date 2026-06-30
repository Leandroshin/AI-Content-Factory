"""Domain event registry contracts for AI Content Factory."""

from __future__ import annotations

from abc import ABC, abstractmethod

from .contracts import BaseEventRegistry
from .models import BaseEvent


class EventRegistry(BaseEventRegistry, ABC):
    """Base event registry contract."""

    @abstractmethod
    def get(self, name: str) -> BaseEvent | None:
        """Return an event placeholder by name."""

    @abstractmethod
    def list(self) -> list[BaseEvent]:
        """Return event placeholders."""
