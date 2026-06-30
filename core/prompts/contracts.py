"""Prompt contracts for AI Content Factory."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Protocol

from .models import PromptContext, PromptTemplate, PromptVariables


class PromptRegistryContract(Protocol):
    """Structural contract for prompt registries."""

    def get(self, name: str) -> PromptTemplate | None:
        """Return a prompt placeholder by name."""

    def list(self) -> list[PromptTemplate]:
        """Return prompt placeholders."""


class PromptLoaderContract(Protocol):
    """Structural contract for prompt loaders."""

    def load(self, name: str) -> PromptTemplate | None:
        """Load a prompt placeholder by name."""


class PromptRendererContract(Protocol):
    """Structural contract for prompt renderers."""

    def render(self, template: PromptTemplate, context: PromptContext) -> str:
        """Render a prompt placeholder into text."""


class PromptValidatorContract(Protocol):
    """Structural contract for prompt validators."""

    def validate(self, template: PromptTemplate, variables: PromptVariables) -> None:
        """Validate a prompt placeholder."""


class BasePromptRegistry(ABC):
    """Base contract for prompt registries."""

    @abstractmethod
    def get(self, name: str) -> PromptTemplate | None:
        """Return a prompt placeholder by name."""

    @abstractmethod
    def list(self) -> list[PromptTemplate]:
        """Return prompt placeholders."""


class BasePromptLoader(ABC):
    """Base contract for prompt loaders."""

    @abstractmethod
    def load(self, name: str) -> PromptTemplate | None:
        """Load a prompt placeholder by name."""


class BasePromptRenderer(ABC):
    """Base contract for prompt renderers."""

    @abstractmethod
    def render(self, template: PromptTemplate, context: PromptContext) -> str:
        """Render a prompt placeholder into text."""


class BasePromptValidator(ABC):
    """Base contract for prompt validators."""

    @abstractmethod
    def validate(self, template: PromptTemplate, variables: PromptVariables) -> None:
        """Validate a prompt placeholder."""
