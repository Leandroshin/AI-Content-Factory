"""Prompt registry contracts for AI Content Factory."""

from __future__ import annotations

from abc import ABC, abstractmethod

from .contracts import BasePromptRegistry
from .models import PromptTemplate


class PromptRegistry(BasePromptRegistry, ABC):
    """Base prompt registry contract."""

    @abstractmethod
    def get(self, name: str) -> PromptTemplate | None:
        """Return a prompt placeholder by name."""

    @abstractmethod
    def list(self) -> list[PromptTemplate]:
        """Return prompt placeholders."""
