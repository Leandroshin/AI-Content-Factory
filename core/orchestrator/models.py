"""Orchestrator models for AI Content Factory."""

from __future__ import annotations

from abc import ABC, abstractmethod
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class ExecutionStatus(StrEnum):
    """Supported execution statuses."""

    DRAFT = "draft"
    PLANNED = "planned"
    READY = "ready"
    RUNNING = "running"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    CANCELLED = "cancelled"


class OrchestratorContext(BaseModel):
    """Execution context placeholder for the orchestrator."""

    model_config = ConfigDict(extra="ignore", populate_by_name=True)

    project_name: str | None = None
    orchestrator_name: str = "orchestrator"
    correlation_id: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class ExecutionStep(BaseModel):
    """Planned execution step placeholder."""

    model_config = ConfigDict(extra="ignore", populate_by_name=True)

    name: str
    description: str | None = None
    status: ExecutionStatus = ExecutionStatus.DRAFT
    metadata: dict[str, Any] = Field(default_factory=dict)


class ExecutionPlan(BaseModel):
    """Execution plan placeholder."""

    model_config = ConfigDict(extra="ignore", populate_by_name=True)

    name: str
    description: str | None = None
    status: ExecutionStatus = ExecutionStatus.DRAFT
    steps: list[ExecutionStep] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)


class ExecutionResult(BaseModel):
    """Execution result placeholder."""

    model_config = ConfigDict(extra="ignore", populate_by_name=True)

    plan_name: str
    status: ExecutionStatus
    success: bool = False
    results: dict[str, Any] = Field(default_factory=dict)
    errors: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)
