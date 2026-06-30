"""Base exception hierarchy for AI Content Factory."""

from __future__ import annotations


class AIContentFactoryError(Exception):
    """Base exception for the entire AI Content Factory project."""


class ConfigurationError(AIContentFactoryError):
    """Raised when configuration is invalid, incomplete, or unavailable."""


class EngineError(AIContentFactoryError):
    """Raised when an engine cannot complete its responsibility."""


class ValidationError(AIContentFactoryError):
    """Raised when input or model validation fails."""


class ProviderError(AIContentFactoryError):
    """Raised when an external provider fails or is unreachable."""


class PipelineError(AIContentFactoryError):
    """Raised when pipeline coordination or execution fails."""


class ProjectError(AIContentFactoryError):
    """Raised when project-level configuration or data is invalid."""


class AssetError(AIContentFactoryError):
    """Raised when asset-related operations fail."""