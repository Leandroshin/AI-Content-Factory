"""Knowledge contracts for AI Content Factory."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Protocol

from .models import KnowledgeContext, KnowledgeEntry, KnowledgeResult


class KnowledgeRegistryContract(Protocol):
    """Structural contract for knowledge registries."""

    def get(self, key: str) -> KnowledgeEntry | None:
        """Return a knowledge placeholder by key."""

    def list(self) -> list[KnowledgeEntry]:
        """Return knowledge placeholders."""


class KnowledgeRepositoryContract(Protocol):
    """Structural contract for knowledge repositories."""

    def fetch(self, key: str) -> KnowledgeEntry | None:
        """Fetch a knowledge placeholder by key."""

    def list(self) -> list[KnowledgeEntry]:
        """Return knowledge placeholders."""


class KnowledgeValidatorContract(Protocol):
    """Structural contract for knowledge validators."""

    def validate(self, entry: KnowledgeEntry) -> None:
        """Validate a knowledge placeholder."""


class BaseKnowledgeRegistry(ABC):
    """Base contract for knowledge registries."""

    @abstractmethod
    def get(self, key: str) -> KnowledgeEntry | None:
        """Return a knowledge placeholder by key."""

    @abstractmethod
    def list(self) -> list[KnowledgeEntry]:
        """Return knowledge placeholders."""


class BaseKnowledgeRepository(ABC):
    """Base contract for knowledge repositories."""

    @abstractmethod
    def fetch(self, key: str) -> KnowledgeEntry | None:
        """Fetch a knowledge placeholder by key."""

    @abstractmethod
    def list(self) -> list[KnowledgeEntry]:
        """Return knowledge placeholders."""


class BaseKnowledgeValidator(ABC):
    """Base contract for knowledge validators."""

    @abstractmethod
    def validate(self, entry: KnowledgeEntry) -> None:
        """Validate a knowledge placeholder."""
