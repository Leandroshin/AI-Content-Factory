"""Result contract package for AI Content Factory."""

from __future__ import annotations

from .contracts import (
    BaseResultRegistry,
    BaseResultValidator,
    ResultRegistryContract,
    ResultValidatorContract,
)
from .exceptions import (
    ResultError,
    ResultNotFoundError,
    ResultRegistryError,
    ResultValidationError,
)
from .models import (
    Result,
    ResultArtifact,
    ResultContext,
    ResultMetadata,
    ResultMetric,
    ResultOutcome,
    ResultStatus,
    ResultSummary,
    ResultType,
)
from .runtime import ResultRuntime, ResultRuntimeState, ResultStateChangedEvent, ResultRuntimeSnapshot

__all__ = [
    "BaseResultRegistry",
    "BaseResultValidator",
    "Result",
    "ResultArtifact",
    "ResultContext",
    "ResultError",
    "ResultMetadata",
    "ResultMetric",
    "ResultNotFoundError",
    "ResultOutcome",
    "ResultRegistryContract",
    "ResultRegistryError",
    "ResultStatus",
    "ResultSummary",
    "ResultType",
    "ResultRuntime",
    "ResultRuntimeSnapshot",
    "ResultRuntimeState",
    "ResultStateChangedEvent",
    "ResultValidationError",
    "ResultValidatorContract",
]