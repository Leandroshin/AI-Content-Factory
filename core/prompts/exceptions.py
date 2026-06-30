"""Prompt exceptions for AI Content Factory."""

from __future__ import annotations

from core.exceptions import ConfigurationError


class PromptError(ConfigurationError):
    """Base exception for prompt subsystem contracts."""


class PromptTemplateError(PromptError):
    """Raised when a prompt template contract is invalid."""


class PromptContextError(PromptError):
    """Raised when a prompt context contract is invalid."""


class PromptRegistryError(PromptError):
    """Raised when a prompt registry contract is invalid."""


class PromptLoaderError(PromptError):
    """Raised when a prompt loader contract is invalid."""


class PromptRendererError(PromptError):
    """Raised when a prompt renderer contract is invalid."""


class PromptValidatorError(PromptError):
    """Raised when a prompt validator contract is invalid."""
