"""Knowledge registry contracts for AI Content Factory."""

from __future__ import annotations

from abc import ABC, abstractmethod

from .contracts import BaseKnowledgeRegistry
from .models import KnowledgeEntry


class KnowledgeRegistry(BaseKnowledgeRegistry, ABC):
    """Base knowledge registry contract."""

    @abstractmethod
    def get(self, key: str) -> KnowledgeEntry | None:
        """Return a knowledge placeholder by key."""

    @abstractmethod
    def list(self) -> list[KnowledgeEntry]:
        """Return knowledge placeholders."""
