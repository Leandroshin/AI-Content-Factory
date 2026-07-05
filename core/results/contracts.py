"""Result contracts for AI Content Factory."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Protocol

from .models import Result, ResultContext, ResultId, ResultMetadata, ResultSummary


class ResultRegistryContract(Protocol):
    """Structural contract for result registries."""

    def get(self, result_id: ResultId) -> Result | None:
        """Return a result placeholder by identifier."""

    def list(self) -> list[Result]:
        """Return result placeholders."""


class ResultValidatorContract(Protocol):
    """Structural contract for result validators."""

    def validate(self, result: Result) -> None:
        """Validate a result placeholder."""

    def validate_context(self, context: ResultContext) -> None:
        """Validate a result context placeholder."""

    def validate_metadata(self, metadata: ResultMetadata) -> None:
        """Validate a result metadata placeholder."""

    def validate_summary(self, summary: ResultSummary) -> None:
        """Validate a result summary placeholder."""


class BaseResultRegistry(ABC):
    """Base contract for result registries."""

    @abstractmethod
    def get(self, result_id: ResultId) -> Result | None:
        """Return a result placeholder by identifier."""

    @abstractmethod
    def list(self) -> list[Result]:
        """Return result placeholders."""

    @abstractmethod
    def register(self, result: Result) -> None:
        """Register a result placeholder."""

    @abstractmethod
    def unregister(self, result_id: ResultId) -> None:
        """Remove a result placeholder from the registry."""


class BaseResultValidator(ABC):
    """Base contract for result validators."""

    @abstractmethod
    def validate(self, result: Result) -> None:
        """Validate a result placeholder."""

    @abstractmethod
    def validate_context(self, context: ResultContext) -> None:
        """Validate a result context placeholder."""

    @abstractmethod
    def validate_metadata(self, metadata: ResultMetadata) -> None:
        """Validate a result metadata placeholder."""

    @abstractmethod
    def validate_summary(self, summary: ResultSummary) -> None:
        """Validate a result summary placeholder."""