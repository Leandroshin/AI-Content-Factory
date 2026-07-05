"""Result models for AI Content Factory."""

from __future__ import annotations

from enum import StrEnum
from typing import Any
from uuid import UUID, uuid4

from pydantic import BaseModel, ConfigDict, Field


ResultId = UUID


class ResultStatus(StrEnum):
    """Lifecycle states for results."""

    DRAFT = "draft"
    GENERATED = "generated"
    VERIFIED = "verified"
    ARCHIVED = "archived"


class ResultType(StrEnum):
    """High-level result categories."""

    GENERIC = "generic"
    CONTENT = "content"
    ANALYSIS = "analysis"
    ORGANIZATIONAL = "organizational"
    KNOWLEDGE = "knowledge"


class ResultOutcome(StrEnum):
    """Outcome states for results."""

    SUCCESS = "success"
    WARNING = "warning"
    FAILURE = "failure"
    PARTIAL = "partial"


class ResultArtifact(BaseModel):
    """Artifact placeholder for results."""

    model_config = ConfigDict(extra="ignore", populate_by_name=True)

    name: str | None = None
    kind: str | None = None
    uri: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class ResultMetric(BaseModel):
    """Metric placeholder for results."""

    model_config = ConfigDict(extra="ignore", populate_by_name=True)

    name: str | None = None
    value: float | int | str | None = None
    unit: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class ResultSummary(BaseModel):
    """Summary placeholder for results."""

    model_config = ConfigDict(extra="ignore", populate_by_name=True)

    title: str | None = None
    description: str | None = None
    highlights: list[str] = Field(default_factory=list)


class ResultMetadata(BaseModel):
    """Metadata placeholder for results."""

    model_config = ConfigDict(extra="ignore", populate_by_name=True)

    name: str | None = None
    description: str | None = None
    attributes: dict[str, Any] = Field(default_factory=dict)


class ResultContext(BaseModel):
    """Context placeholder for result contracts."""

    model_config = ConfigDict(extra="ignore", populate_by_name=True)

    source_name: str | None = None
    project_name: str | None = None
    metadata: ResultMetadata | None = None


class Result(BaseModel):
    """Result placeholder."""

    model_config = ConfigDict(extra="ignore", populate_by_name=True)

    id: ResultId = Field(default_factory=uuid4)
    name: str
    type: ResultType = ResultType.GENERIC
    status: ResultStatus = ResultStatus.DRAFT
    outcome: ResultOutcome = ResultOutcome.SUCCESS
    summary: ResultSummary = Field(default_factory=ResultSummary)
    artifacts: list[ResultArtifact] = Field(default_factory=list)
    metrics: list[ResultMetric] = Field(default_factory=list)
    context: ResultContext | None = None
    metadata: ResultMetadata = Field(default_factory=ResultMetadata)