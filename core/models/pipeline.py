"""Pipeline job contracts."""

from __future__ import annotations

from pydantic import Field

from .base import IdentifiedModel


class PipelineJob(IdentifiedModel):
    """Pipeline job entity placeholder."""

    name: str = Field(default="")
    step: str | None = None
    status: str | None = None