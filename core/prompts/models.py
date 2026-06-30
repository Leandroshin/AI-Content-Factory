"""Prompt models for AI Content Factory."""

from __future__ import annotations

from enum import StrEnum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class PromptVersion(BaseModel):
    """Version placeholder for prompt definitions."""

    model_config = ConfigDict(extra="ignore", populate_by_name=True)

    major: int = 1
    minor: int = 0
    patch: int = 0
    label: str | None = None


class PromptVariables(BaseModel):
    """Container for prompt variables."""

    model_config = ConfigDict(extra="ignore", populate_by_name=True)

    values: dict[str, Any] = Field(default_factory=dict)


class PromptMetadata(BaseModel):
    """Metadata placeholder for prompts."""

    model_config = ConfigDict(extra="ignore", populate_by_name=True)

    name: str
    description: str | None = None
    tags: list[str] = Field(default_factory=list)
    engine_name: str | None = None
    version: PromptVersion = Field(default_factory=PromptVersion)
    extra: dict[str, Any] = Field(default_factory=dict)


class PromptContext(BaseModel):
    """Context placeholder for prompt processing."""

    model_config = ConfigDict(extra="ignore", populate_by_name=True)

    project_name: str | None = None
    engine_name: str | None = None
    variables: PromptVariables = Field(default_factory=PromptVariables)
    metadata: PromptMetadata | None = None


class PromptTemplate(BaseModel):
    """Prompt template placeholder."""

    model_config = ConfigDict(extra="ignore", populate_by_name=True)

    name: str
    body: str | None = None
    metadata: PromptMetadata
    context: PromptContext | None = None
    active_version: PromptVersion = Field(default_factory=PromptVersion)
