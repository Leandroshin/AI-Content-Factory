"""Task contract package for AI Content Factory."""

from __future__ import annotations

from .contracts import (
    BaseTaskFactory,
    BaseTaskLifecycle,
    BaseTaskRegistry,
    BaseTaskValidator,
    TaskFactoryContract,
    TaskLifecycleContract,
    TaskRegistryContract,
    TaskValidatorContract,
)
from .exceptions import (
    TaskDependencyError,
    TaskError,
    TaskFactoryError,
    TaskLifecycleError,
    TaskNotFoundError,
    TaskRegistryError,
    TaskValidationError,
)
from .lifecycle import TaskLifecycle
from .models import (
    Task,
    TaskContext,
    TaskDependency,
    TaskId,
    TaskMetadata,
    TaskResult,
    TaskStatus,
    TaskType,
)
from .priorities import TaskPriority
from .runtime import TaskRuntime, TaskRuntimeState, TaskStateChangedEvent, TaskRuntimeSnapshot

__all__ = [
    "BaseTaskFactory",
    "BaseTaskLifecycle",
    "BaseTaskRegistry",
    "BaseTaskValidator",
    "Task",
    "TaskContext",
    "TaskDependency",
    "TaskDependencyError",
    "TaskError",
    "TaskFactoryContract",
    "TaskFactoryError",
    "TaskId",
    "TaskLifecycle",
    "TaskLifecycleContract",
    "TaskLifecycleError",
    "TaskMetadata",
    "TaskNotFoundError",
    "TaskPriority",
    "TaskRuntime",
    "TaskRuntimeSnapshot",
    "TaskRuntimeState",
    "TaskStateChangedEvent",
    "TaskRegistryContract",
    "TaskRegistryError",
    "TaskResult",
    "TaskStatus",
    "TaskType",
    "TaskValidationError",
    "TaskValidatorContract",
]