"""Knowledge exceptions for AI Content Factory."""

from __future__ import annotations

from core.exceptions import AIContentFactoryError


class KnowledgeError(AIContentFactoryError):
    """Base exception for knowledge contracts."""


class KnowledgeRegistryError(KnowledgeError):
    """Raised when a knowledge registry contract is invalid."""


class KnowledgeRepositoryError(KnowledgeError):
    """Raised when a knowledge repository contract is invalid."""


class KnowledgeValidationError(KnowledgeError):
    """Raised when a knowledge validator contract is invalid."""
