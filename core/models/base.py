"""Base contracts for core models."""

from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID, uuid4

from pydantic import BaseModel, ConfigDict, Field


class CoreModel(BaseModel):
    """Shared base model for core entities."""

    model_config = ConfigDict(extra="ignore", populate_by_name=True)


class IdentifiedModel(CoreModel):
    """Base model with identity and timestamps."""

    id: UUID = Field(default_factory=uuid4)
    created_at: datetime | None = None
    updated_at: datetime | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)