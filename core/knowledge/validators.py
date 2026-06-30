"""Knowledge validator contracts for AI Content Factory."""

from __future__ import annotations

from abc import ABC, abstractmethod

from .contracts import BaseKnowledgeValidator
from .models import KnowledgeEntry


class KnowledgeValidator(BaseKnowledgeValidator, ABC):
    """Base knowledge validator contract."""

    @abstractmethod
    def validate(self, entry: KnowledgeEntry) -> None:
        """Validate a knowledge placeholder."""
