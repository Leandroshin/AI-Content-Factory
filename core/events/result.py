"""Event result models for AI Content Factory."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class EventResult(BaseModel):
    """Result placeholder for event processing."""

    model_config = ConfigDict(extra="ignore", populate_by_name=True)

    accepted: bool = False
    handler_name: str | None = None
    details: dict[str, Any] = Field(default_factory=dict)
    error_message: str | None = None
