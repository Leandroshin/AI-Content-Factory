"""Skill contract package for AI Content Factory."""

from __future__ import annotations

from .contracts import (
    BaseSkillRegistry,
    BaseSkillValidator,
    SkillRegistryContract,
    SkillValidatorContract,
)
from .exceptions import (
    SkillError,
    SkillNotFoundError,
    SkillRegistryError,
    SkillValidationError,
)
from .foundation import (
    SkillRecord,
    SkillResult,
    SkillRuntime as FoundationSkillRuntime,
    SkillSnapshot,
    SkillTrace,
)
from .models import (
    Skill,
    SkillCapability,
    SkillCategory,
    SkillContext,
    SkillLevel,
    SkillMetadata,
    SkillProfile,
    SkillStatus,
)
from .runtime import SkillRuntime, SkillRuntimeState, SkillStateChangedEvent, SkillRuntimeSnapshot

__all__ = [
    "BaseSkillRegistry",
    "BaseSkillValidator",
    "FoundationSkillRuntime",
    "Skill",
    "SkillCapability",
    "SkillCategory",
    "SkillContext",
    "SkillError",
    "SkillLevel",
    "SkillMetadata",
    "SkillNotFoundError",
    "SkillProfile",
    "SkillRecord",
    "SkillRegistryContract",
    "SkillRegistryError",
    "SkillResult",
    "SkillRuntime",
    "SkillRuntimeSnapshot",
    "SkillRuntimeState",
    "SkillSnapshot",
    "SkillStateChangedEvent",
    "SkillStatus",
    "SkillTrace",
    "SkillValidationError",
    "SkillValidatorContract",
]