"""Task exceptions for AI Content Factory."""

from __future__ import annotations


class TaskError(Exception):
    """Base exception for task-related contracts."""


class TaskValidationError(TaskError):
    """Raised when a task placeholder is structurally invalid."""


class TaskRegistryError(TaskError):
    """Raised when a task registry placeholder cannot complete an operation."""


class TaskNotFoundError(TaskRegistryError):
    """Raised when a task placeholder cannot be found."""


class TaskLifecycleError(TaskError):
    """Raised when a task lifecycle placeholder is inconsistent."""


class TaskDependencyError(TaskError):
    """Raised when a task dependency placeholder is invalid."""


class TaskFactoryError(TaskError):
    """Raised when a task factory placeholder cannot create a task."""