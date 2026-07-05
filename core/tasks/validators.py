"""Task validators for AI Content Factory."""

from __future__ import annotations

from abc import ABC, abstractmethod

from .models import Task, TaskDependency


class BaseTaskValidator(ABC):
    """Base contract for task validators."""

    @abstractmethod
    def validate(self, task: Task) -> None:
        """Validate a task placeholder."""

    @abstractmethod
    def validate_dependency(self, dependency: TaskDependency) -> None:
        """Validate a task dependency placeholder."""