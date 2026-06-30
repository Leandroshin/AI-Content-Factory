"""Project model contracts."""

from __future__ import annotations

from pydantic import Field

from .base import IdentifiedModel


class Project(IdentifiedModel):
    """Project entity placeholder."""

    name: str = Field(default="")
    niche: str | None = None
    description: str | None = None
    status: str | None = None