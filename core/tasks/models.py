"""Task models for AI Content Factory."""

from __future__ import annotations

from enum import StrEnum
from typing import Any
from uuid import UUID, uuid4

from pydantic import BaseModel, ConfigDict, Field

from .priorities import TaskPriority

TaskId = UUID


class TaskStatus(StrEnum):
    """Lifecycle states for tasks."""

    DRAFT = "draft"
    READY = "ready"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    ARCHIVED = "archived"


class TaskType(StrEnum):
    """High-level task categories."""

    GENERIC = "generic"
    CONTENT = "content"
    RESEARCH = "research"
    OPERATIONS = "operations"
    SYSTEM = "system"


class TaskMetadata(BaseModel):
    """Metadata placeholder for tasks."""

    model_config = ConfigDict(extra="ignore", populate_by_name=True)

    name: str | None = None
    description: str | None = None
    tags: list[str] = Field(default_factory=list)
    extra: dict[str, Any] = Field(default_factory=dict)


class TaskContext(BaseModel):
    """Context placeholder for task contracts."""

    model_config = ConfigDict(extra="ignore", populate_by_name=True)

    project_name: str | None = None
    workspace_name: str | None = None
    metadata: TaskMetadata | None = None


class TaskDependency(BaseModel):
    """Dependency placeholder for tasks."""

    model_config = ConfigDict(extra="ignore", populate_by_name=True)

    depends_on: TaskId
    required: bool = True
    metadata: TaskMetadata | None = None


class TaskResult(BaseModel):
    """Result placeholder for task contracts."""

    model_config = ConfigDict(extra="ignore", populate_by_name=True)

    success: bool = False
    status: TaskStatus = TaskStatus.DRAFT
    message: str | None = None
    data: dict[str, Any] = Field(default_factory=dict)
    errors: list[str] = Field(default_factory=list)


class Task(BaseModel):
    """Task placeholder."""

    model_config = ConfigDict(extra="ignore", populate_by_name=True)

    id: TaskId = Field(default_factory=uuid4)
    name: str
    type: TaskType = TaskType.GENERIC
    priority: TaskPriority = TaskPriority.NORMAL
    status: TaskStatus = TaskStatus.DRAFT
    context: TaskContext | None = None
    metadata: TaskMetadata = Field(default_factory=TaskMetadata)
    dependencies: list[TaskDependency] = Field(default_factory=list)