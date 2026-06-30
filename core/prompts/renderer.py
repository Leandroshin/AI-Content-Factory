"""Prompt renderer contracts for AI Content Factory."""

from __future__ import annotations

from abc import ABC, abstractmethod

from .contracts import BasePromptRenderer
from .models import PromptContext, PromptTemplate


class PromptRenderer(BasePromptRenderer, ABC):
    """Base prompt renderer contract."""

    @abstractmethod
    def render(self, template: PromptTemplate, context: PromptContext) -> str:
        """Render a prompt placeholder into text."""
