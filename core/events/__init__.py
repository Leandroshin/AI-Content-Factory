"""Core events package for AI Content Factory."""

from .contracts import (
    BaseEventDispatcher,
    BaseEventRegistry,
    BaseEventSubscriber,
    BaseEventValidator,
    EventDispatcherContract,
    EventRegistryContract,
    EventSubscriberContract,
    EventValidatorContract,
)
from .dispatcher import EventDispatcher
from .exceptions import (
    EventDispatchError,
    EventError,
    EventRegistryError,
    EventSubscriberError,
    EventValidationError,
)
from .models import (
    BaseEvent,
    EventContext,
    EventMetadata,
    EventPriority,
    EventResult,
    EventStatus,
    EventType,
)
from .registry import EventRegistry
from .subscribers import EventSubscriber
from .validators import EventValidator

__all__ = [
    "BaseEvent",
    "BaseEventDispatcher",
    "BaseEventRegistry",
    "BaseEventSubscriber",
    "BaseEventValidator",
    "EventContext",
    "EventDispatchError",
    "EventDispatcher",
    "EventDispatcherContract",
    "EventError",
    "EventMetadata",
    "EventPriority",
    "EventRegistry",
    "EventRegistryContract",
    "EventRegistryError",
    "EventResult",
    "EventStatus",
    "EventSubscriber",
    "EventSubscriberContract",
    "EventSubscriberError",
    "EventType",
    "EventValidationError",
    "EventValidator",
    "EventValidatorContract",
]
