"""Asset model contracts."""

from __future__ import annotations

from pydantic import Field

from .base import IdentifiedModel


class Asset(IdentifiedModel):
    """Asset entity placeholder."""

    name: str = Field(default="")
    asset_type: str | None = None
    uri: str | None = None