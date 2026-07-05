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
from .foundation import KnowledgeRecord, KnowledgeResult as FoundationKnowledgeResult, KnowledgeRuntime as FoundationKnowledgeRuntime, KnowledgeSnapshot, KnowledgeTrace
from .models import (
    KnowledgeCategory,
    KnowledgeContext,
    KnowledgeEntry,
    KnowledgeMetadata,
    KnowledgeResult,
    KnowledgeSource,
    KnowledgeStatus,
)
from .runtime import KnowledgeRuntime, KnowledgeRuntimeState, KnowledgeStateChangedEvent, KnowledgeRuntimeSnapshot, KnowledgeType
from .registry import KnowledgeRegistry
from .repository import KnowledgeRepository
from .validators import KnowledgeValidator

__all__ = [
    "BaseKnowledgeRegistry",
    "BaseKnowledgeRepository",
    "BaseKnowledgeValidator",
    "FoundationKnowledgeResult",
    "FoundationKnowledgeRuntime",
    "KnowledgeCategory",
    "KnowledgeContext",
    "KnowledgeEntry",
    "KnowledgeError",
    "KnowledgeMetadata",
    "KnowledgeRecord",
    "KnowledgeRegistry",
    "KnowledgeRegistryContract",
    "KnowledgeRegistryError",
    "KnowledgeRepository",
    "KnowledgeRepositoryContract",
    "KnowledgeRepositoryError",
    "KnowledgeResult",
    "KnowledgeRuntime",
    "KnowledgeRuntimeSnapshot",
    "KnowledgeRuntimeState",
    "KnowledgeSnapshot",
    "KnowledgeStateChangedEvent",
    "KnowledgeTrace",
    "KnowledgeType",
    "KnowledgeValidationError",
    "KnowledgeValidator",
    "KnowledgeValidatorContract",
]
