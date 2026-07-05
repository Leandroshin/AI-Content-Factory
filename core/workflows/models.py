"""Workflow models for AI Content Factory."""

from __future__ import annotations

from enum import StrEnum
from typing import Any
from uuid import UUID, uuid4

from pydantic import BaseModel, ConfigDict, Field

from core.tasks.models import TaskId


class WorkflowStatus(StrEnum):
    """Lifecycle states for workflows."""

    DRAFT = "draft"
    PLANNED = "planned"
    ACTIVE = "active"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    ARCHIVED = "archived"


class WorkflowStage(StrEnum):
    """High-level stages of a workflow."""

    INTAKE = "intake"
    ROUTING = "routing"
    DEPARTMENT = "department"
    ENGINE = "engine"
    RESULT = "result"


class WorkflowContext(BaseModel):
    """Context placeholder for workflow contracts."""

    model_config = ConfigDict(extra="ignore", populate_by_name=True)

    task_id: TaskId | None = None
    task_name: str | None = None
    workflow_name: str | None = None
    project_name: str | None = None
    department_name: str | None = None
    engine_name: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class WorkflowStep(BaseModel):
    """Workflow step placeholder."""

    model_config = ConfigDict(extra="ignore", populate_by_name=True)

    name: str
    stage: WorkflowStage = WorkflowStage.ROUTING
    order: int = 0
    department_name: str | None = None
    engine_name: str | None = None
    required: bool = True
    metadata: dict[str, Any] = Field(default_factory=dict)


class WorkflowResult(BaseModel):
    """Result placeholder for workflow contracts."""

    model_config = ConfigDict(extra="ignore", populate_by_name=True)

    success: bool = False
    status: WorkflowStatus = WorkflowStatus.DRAFT
    message: str | None = None
    data: dict[str, Any] = Field(default_factory=dict)
    errors: list[str] = Field(default_factory=list)


class Workflow(BaseModel):
    """Workflow placeholder."""

    model_config = ConfigDict(extra="ignore", populate_by_name=True)

    id: UUID = Field(default_factory=uuid4)
    name: str
    description: str | None = None
    status: WorkflowStatus = WorkflowStatus.DRAFT
    context: WorkflowContext | None = None
    steps: list[WorkflowStep] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)