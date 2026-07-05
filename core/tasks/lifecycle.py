"""Task lifecycle architecture for AI Content Factory."""

from __future__ import annotations

from abc import ABC, abstractmethod

from pydantic import BaseModel, ConfigDict, Field

from .models import Task, TaskStatus


class TaskLifecycle(BaseModel):
    """Lifecycle snapshot placeholder for tasks."""

    model_config = ConfigDict(extra="ignore", populate_by_name=True)

    status: TaskStatus = TaskStatus.DRAFT
    previous_status: TaskStatus | None = None
    available_transitions: list[TaskStatus] = Field(default_factory=list)


class BaseTaskLifecycle(ABC):
    """Base contract for task lifecycle services."""

    @abstractmethod
    def describe(self, task: Task) -> TaskLifecycle:
        """Return the lifecycle snapshot for a task."""

    @abstractmethod
    def get_available_transitions(self, status: TaskStatus) -> list[TaskStatus]:
        """Return the next lifecycle states for a task status."""