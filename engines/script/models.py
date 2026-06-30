"""Script engine models for AI Content Factory."""

from __future__ import annotations

from enum import StrEnum
from typing import Any

from pydantic import ConfigDict, Field

from engines.base import EngineRequest, EngineResponse


class ScriptGenerationMode(StrEnum):
    """Supported script generation modes."""

    DRAFT = "draft"
    OUTLINE = "outline"
    FULL = "full"


class ScriptRequest(EngineRequest):
    """Script engine request placeholder."""

    model_config = ConfigDict(extra="ignore", populate_by_name=True)

    mode: ScriptGenerationMode = ScriptGenerationMode.DRAFT
    topic: str | None = None
    source_notes: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)


class ScriptResponse(EngineResponse):
    """Script engine response placeholder."""

    model_config = ConfigDict(extra="ignore", populate_by_name=True)

    mode: ScriptGenerationMode = ScriptGenerationMode.DRAFT
    script_text: str | None = None
    outline: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)
