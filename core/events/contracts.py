"""Domain event contracts for AI Content Factory."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Protocol

from .models import BaseEvent, EventContext, EventResult, EventStatus, EventType


class EventRegistryContract(Protocol):
    """Structural contract for event registries."""

    def get(self, name: str) -> BaseEvent | None:
        """Return an event placeholder by name."""

    def list(self) -> list[BaseEvent]:
        """Return event placeholders."""


class EventDispatcherContract(Protocol):
    """Structural contract for event dispatchers."""

    def dispatch(self, event: BaseEvent, context: EventContext | None = None) -> EventResult:
        """Dispatch an event placeholder."""


class EventSubscriberContract(Protocol):
    """Structural contract for event subscribers."""

    def accepts(self, event_type: EventType) -> bool:
        """Return whether the subscriber can accept an event type."""


class EventValidatorContract(Protocol):
    """Structural contract for event validators."""

    def validate(self, event: BaseEvent) -> None:
        """Validate a domain event placeholder."""


class BaseEventRegistry(ABC):
    """Base contract for event registries."""

    @abstractmethod
    def get(self, name: str) -> BaseEvent | None:
        """Return an event placeholder by name."""

    @abstractmethod
    def list(self) -> list[BaseEvent]:
        """Return event placeholders."""


class BaseEventDispatcher(ABC):
    """Base contract for event dispatchers."""

    @abstractmethod
    def dispatch(self, event: BaseEvent, context: EventContext | None = None) -> EventResult:
        """Dispatch an event placeholder."""


class BaseEventSubscriber(ABC):
    """Base contract for event subscribers."""

    @abstractmethod
    def accepts(self, event_type: EventType) -> bool:
        """Return whether the subscriber can accept an event type."""


class BaseEventValidator(ABC):
    """Base contract for event validators."""

    @abstractmethod
    def validate(self, event: BaseEvent) -> None:
        """Validate a domain event placeholder."""
