"""Engine result contracts."""

from __future__ import annotations

from typing import Any

from pydantic import Field

from .base import IdentifiedModel


class EngineResult(IdentifiedModel):
    """Generic engine result placeholder."""

    success: bool = Field(default=False)
    engine_name: str | None = None
    payload: dict[str, Any] = Field(default_factory=dict)
    error_message: str | None = None