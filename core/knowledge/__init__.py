"""Core knowledge package for AI Content Factory."""

from .contracts import (
    BaseKnowledgeRegistry,
    BaseKnowledgeRepository,
    BaseKnowledgeValidator,
    KnowledgeRegistryContract,
    KnowledgeRepositoryContract,
    KnowledgeValidatorContract,
)
from .exceptions import KnowledgeError, KnowledgeRegistryError, KnowledgeRepositoryError, KnowledgeValidationError
from .models import (
    KnowledgeCategory,
    KnowledgeContext,
    KnowledgeEntry,
    KnowledgeMetadata,
    KnowledgeResult,
    KnowledgeSource,
    KnowledgeStatus,
)
from .registry import KnowledgeRegistry
from .repository import KnowledgeRepository
from .validators import KnowledgeValidator

__all__ = [
    "BaseKnowledgeRegistry",
    "BaseKnowledgeRepository",
    "BaseKnowledgeValidator",
    "KnowledgeCategory",
    "KnowledgeContext",
    "KnowledgeEntry",
    "KnowledgeError",
    "KnowledgeMetadata",
    "KnowledgeRegistry",
    "KnowledgeRegistryContract",
    "KnowledgeRegistryError",
    "KnowledgeRepository",
    "KnowledgeRepositoryContract",
    "KnowledgeRepositoryError",
    "KnowledgeResult",
    "KnowledgeSource",
    "KnowledgeStatus",
    "KnowledgeValidationError",
    "KnowledgeValidator",
    "KnowledgeValidatorContract",
]
