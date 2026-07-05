"""Skill exceptions for AI Content Factory."""

from __future__ import annotations


class SkillError(Exception):
    """Base exception for skill-related contracts."""


class SkillValidationError(SkillError):
    """Raised when a skill placeholder is structurally invalid."""


class SkillRegistryError(SkillError):
    """Raised when a skill registry placeholder cannot complete an operation."""


class SkillNotFoundError(SkillRegistryError):
    """Raised when a skill placeholder cannot be found."""