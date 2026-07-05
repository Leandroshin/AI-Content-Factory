"""Workflow contracts for AI Content Factory."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Protocol

from .models import Workflow, WorkflowContext, WorkflowResult, WorkflowStep


class WorkflowRegistryContract(Protocol):
    """Structural contract for workflow registries."""

    def get(self, name: str) -> Workflow | None:
        """Return a workflow placeholder by name."""

    def list(self) -> list[Workflow]:
        """Return workflow placeholders."""


class WorkflowValidatorContract(Protocol):
    """Structural contract for workflow validators."""

    def validate(self, workflow: Workflow) -> None:
        """Validate a workflow placeholder."""

    def validate_step(self, step: WorkflowStep) -> None:
        """Validate a workflow step placeholder."""

    def validate_context(self, context: WorkflowContext) -> None:
        """Validate a workflow context placeholder."""


class BaseWorkflowRegistry(ABC):
    """Base contract for workflow registries."""

    @abstractmethod
    def get(self, name: str) -> Workflow | None:
        """Return a workflow placeholder by name."""

    @abstractmethod
    def list(self) -> list[Workflow]:
        """Return workflow placeholders."""

    @abstractmethod
    def register(self, workflow: Workflow) -> None:
        """Register a workflow placeholder."""

    @abstractmethod
    def unregister(self, name: str) -> None:
        """Remove a workflow placeholder from the registry."""


class BaseWorkflowValidator(ABC):
    """Base contract for workflow validators."""

    @abstractmethod
    def validate(self, workflow: Workflow) -> None:
        """Validate a workflow placeholder."""

    @abstractmethod
    def validate_step(self, step: WorkflowStep) -> None:
        """Validate a workflow step placeholder."""

    @abstractmethod
    def validate_context(self, context: WorkflowContext) -> None:
        """Validate a workflow context placeholder."""