"""Task contracts for AI Content Factory."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Protocol

from .lifecycle import TaskLifecycle
from .models import Task, TaskContext, TaskDependency, TaskId, TaskResult, TaskStatus


class TaskRegistryContract(Protocol):
    """Structural contract for task registries."""

    def get(self, task_id: TaskId) -> Task | None:
        """Return a task placeholder by identifier."""

    def list(self) -> list[Task]:
        """Return task placeholders."""


class TaskValidatorContract(Protocol):
    """Structural contract for task validators."""

    def validate(self, task: Task) -> None:
        """Validate a task placeholder."""

    def validate_dependency(self, dependency: TaskDependency) -> None:
        """Validate a task dependency placeholder."""


class TaskFactoryContract(Protocol):
    """Structural contract for task factories."""

    def create(self, context: TaskContext) -> Task:
        """Create a task placeholder from context."""


class TaskLifecycleContract(Protocol):
    """Structural contract for task lifecycle services."""

    def describe(self, task: Task) -> TaskLifecycle:
        """Describe the lifecycle snapshot for a task."""

    def get_available_transitions(self, status: TaskStatus) -> list[TaskStatus]:
        """Return available lifecycle transitions for a status."""


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


class BaseTaskValidator(ABC):
    """Base contract for task validators."""

    @abstractmethod
    def validate(self, task: Task) -> None:
        """Validate a task placeholder."""

    @abstractmethod
    def validate_dependency(self, dependency: TaskDependency) -> None:
        """Validate a task dependency placeholder."""


class BaseTaskFactory(ABC):
    """Base contract for task factories."""

    @abstractmethod
    def create(self, context: TaskContext) -> Task:
        """Create a task placeholder from context."""


class BaseTaskLifecycle(ABC):
    """Base contract for task lifecycle services."""

    @abstractmethod
    def describe(self, task: Task) -> TaskLifecycle:
        """Describe the lifecycle snapshot for a task."""

    @abstractmethod
    def get_available_transitions(self, status: TaskStatus) -> list[TaskStatus]:
        """Return available lifecycle transitions for a status."""