"""Task registry architecture for AI Content Factory."""

from __future__ import annotations

from abc import ABC, abstractmethod

from .contracts import TaskRegistryContract
from .models import Task, TaskId


class BaseTaskRegistry(ABC):
    """Base contract for task registries."""

    @abstractmethod
    def get(self, task_id: TaskId) -> Task | None:
        """Return a task placeholder by identifier."""

    @abstractmethod
    def list(self) -> list[Task]:
        """Return task placeholders."""

    @abstractmethod
    def register(self, task: Task) -> None:
        """Register a task placeholder."""

    @abstractmethod
    def unregister(self, task_id: TaskId) -> None:
        """Remove a task placeholder from the registry."""


__all__ = ["BaseTaskRegistry", "TaskRegistryContract"]