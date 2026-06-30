"""Script model contracts."""

from __future__ import annotations

from pydantic import Field

from .base import IdentifiedModel


class Script(IdentifiedModel):
    """Script entity placeholder."""

    title: str = Field(default="")
    content: str = Field(default="")
    status: str | None = None