"""Domain event exceptions for AI Content Factory."""

from __future__ import annotations

from core.exceptions import AIContentFactoryError


class EventError(AIContentFactoryError):
    """Base exception for domain event contracts."""


class EventRegistryError(EventError):
    """Raised when an event registry contract is invalid."""


class EventDispatchError(EventError):
    """Raised when an event dispatcher contract is invalid."""


class EventSubscriberError(EventError):
    """Raised when an event subscriber contract is invalid."""


class EventValidationError(EventError):
    """Raised when a domain event contract is invalid."""
