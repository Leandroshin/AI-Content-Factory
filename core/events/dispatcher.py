"""Domain event dispatcher contracts for AI Content Factory."""

from __future__ import annotations

from abc import ABC, abstractmethod

from .contracts import BaseEventDispatcher
from .models import BaseEvent, EventContext, EventResult


class EventDispatcher(BaseEventDispatcher, ABC):
    """Base event dispatcher contract."""

    @abstractmethod
    def dispatch(self, event: BaseEvent, context: EventContext | None = None) -> EventResult:
        """Dispatch an event placeholder."""
