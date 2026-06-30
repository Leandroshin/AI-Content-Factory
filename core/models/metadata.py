"""Metadata model contracts."""

from __future__ import annotations

from typing import Any

from pydantic import Field

from .base import CoreModel


class Metadata(CoreModel):
    """Generic metadata container."""

    source: str | None = None
    tags: list[str] = Field(default_factory=list)
    attributes: dict[str, Any] = Field(default_factory=dict)