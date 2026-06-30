"""Video model contracts."""

from __future__ import annotations

from pydantic import Field

from .base import IdentifiedModel


class Video(IdentifiedModel):
    """Video entity placeholder."""

    title: str = Field(default="")
    duration_seconds: int | None = None
    status: str | None = None