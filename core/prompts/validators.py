"""Prompt validator contracts for AI Content Factory."""

from __future__ import annotations

from abc import ABC, abstractmethod

from .contracts import BasePromptValidator
from .models import PromptTemplate, PromptVariables


class PromptValidator(BasePromptValidator, ABC):
    """Base prompt validator contract."""

    @abstractmethod
    def validate(self, template: PromptTemplate, variables: PromptVariables) -> None:
        """Validate a prompt placeholder."""
