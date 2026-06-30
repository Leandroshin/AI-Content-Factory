"""Prompt loader contracts for AI Content Factory."""

from __future__ import annotations

from abc import ABC, abstractmethod

from .contracts import BasePromptLoader
from .models import PromptTemplate


class PromptLoader(BasePromptLoader, ABC):
    """Base prompt loader contract."""

    @abstractmethod
    def load(self, name: str) -> PromptTemplate | None:
        """Load a prompt placeholder by name."""
