"""Core pipeline models for AI Content Factory."""

from __future__ import annotations

from enum import StrEnum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class PipelineState(StrEnum):
    """Pipeline lifecycle states."""

    DRAFT = "draft"
    READY = "ready"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class PipelineContext(BaseModel):
    """Execution context placeholder for a pipeline."""

    model_config = ConfigDict(extra="ignore", populate_by_name=True)

    project_name: str | None = None
    pipeline_name: str
    correlation_id: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class Pipeline(BaseModel):
    """Pipeline definition placeholder."""

    model_config = ConfigDict(extra="ignore", populate_by_name=True)

    name: str
    description: str | None = None
    state: PipelineState = PipelineState.DRAFT
    step_names: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)


class PipelineResult(BaseModel):
    """Pipeline result placeholder."""

    model_config = ConfigDict(extra="ignore", populate_by_name=True)

    pipeline_name: str
    state: PipelineState
    success: bool = False
    outputs: dict[str, Any] = Field(default_factory=dict)
    errors: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)
