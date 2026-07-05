"""Skill contracts for AI Content Factory."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Protocol

from .models import Skill, SkillContext, SkillId, SkillProfile


class SkillRegistryContract(Protocol):
    """Structural contract for skill registries."""

    def get(self, skill_id: SkillId) -> Skill | None:
        """Return a skill placeholder by identifier."""

    def list(self) -> list[Skill]:
        """Return skill placeholders."""


class SkillValidatorContract(Protocol):
    """Structural contract for skill validators."""

    def validate(self, skill: Skill) -> None:
        """Validate a skill placeholder."""

    def validate_context(self, context: SkillContext) -> None:
        """Validate a skill context placeholder."""

    def validate_profile(self, profile: SkillProfile) -> None:
        """Validate a skill profile placeholder."""


class BaseSkillRegistry(ABC):
    """Base contract for skill registries."""

    @abstractmethod
    def get(self, skill_id: SkillId) -> Skill | None:
        """Return a skill placeholder by identifier."""

    @abstractmethod
    def list(self) -> list[Skill]:
        """Return skill placeholders."""

    @abstractmethod
    def register(self, skill: Skill) -> None:
        """Register a skill placeholder."""

    @abstractmethod
    def unregister(self, skill_id: SkillId) -> None:
        """Remove a skill placeholder from the registry."""


class BaseSkillValidator(ABC):
    """Base contract for skill validators."""

    @abstractmethod
    def validate(self, skill: Skill) -> None:
        """Validate a skill placeholder."""

    @abstractmethod
    def validate_context(self, context: SkillContext) -> None:
        """Validate a skill context placeholder."""

    @abstractmethod
    def validate_profile(self, profile: SkillProfile) -> None:
        """Validate a skill profile placeholder."""