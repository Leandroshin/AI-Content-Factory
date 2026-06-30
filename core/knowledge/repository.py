"""Knowledge repository contracts for AI Content Factory."""

from __future__ import annotations

from abc import ABC, abstractmethod

from .contracts import BaseKnowledgeRepository
from .models import KnowledgeEntry


class KnowledgeRepository(BaseKnowledgeRepository, ABC):
    """Base knowledge repository contract."""

    @abstractmethod
    def fetch(self, key: str) -> KnowledgeEntry | None:
        """Fetch a knowledge placeholder by key."""

    @abstractmethod
    def list(self) -> list[KnowledgeEntry]:
        """Return knowledge placeholders."""
