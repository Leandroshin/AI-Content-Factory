"""Domain event models for AI Content Factory."""

from __future__ import annotations

from enum import StrEnum
from typing import Any
from uuid import UUID, uuid4

from pydantic import BaseModel, ConfigDict, Field


class EventStatus(StrEnum):
    """Lifecycle states for domain events."""

    DRAFT = "draft"
    READY = "ready"
    DISPATCHED = "dispatched"
    ACKNOWLEDGED = "acknowledged"
    REJECTED = "rejected"
    FAILED = "failed"


class EventPriority(StrEnum):
    """Priority levels for domain events."""

    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    CRITICAL = "critical"


class EventType(StrEnum):
    """Semantic event categories."""

    DOMAIN = "domain"
    SYSTEM = "system"
    INTEGRATION = "integration"
    AUDIT = "audit"


class EventMetadata(BaseModel):
    """Metadata placeholder for domain events."""

    model_config = ConfigDict(extra="ignore", populate_by_name=True)

    name: str | None = None
    source: str | None = None
    tags: list[str] = Field(default_factory=list)
    extra: dict[str, Any] = Field(default_factory=dict)


class EventContext(BaseModel):
    """Execution context placeholder for domain events."""

    model_config = ConfigDict(extra="ignore", populate_by_name=True)

    project_name: str | None = None
    engine_name: str | None = None
    correlation_id: str | None = None
    metadata: EventMetadata | None = None


class EventResult(BaseModel):
    """Result placeholder for event contracts."""

    model_config = ConfigDict(extra="ignore", populate_by_name=True)

    success: bool = False
    status: EventStatus = EventStatus.DRAFT
    message: str | None = None
    data: dict[str, Any] = Field(default_factory=dict)
    errors: list[str] = Field(default_factory=list)


class BaseEvent(BaseModel):
    """Base contract for domain events."""

    model_config = ConfigDict(extra="ignore", populate_by_name=True)

    id: UUID = Field(default_factory=uuid4)
    name: str
    type: EventType = EventType.DOMAIN
    priority: EventPriority = EventPriority.NORMAL
    status: EventStatus = EventStatus.DRAFT
    context: EventContext | None = None
    metadata: EventMetadata = Field(default_factory=EventMetadata)
    payload: dict[str, Any] = Field(default_factory=dict)
