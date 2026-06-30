"""Exceptions for the configuration subsystem."""

from __future__ import annotations

from core.exceptions import ConfigurationError as BaseConfigurationError


class ConfigurationError(BaseConfigurationError):
    """Base exception for configuration issues."""


class ConfigurationNotFoundError(ConfigurationError):
    """Raised when a configuration source cannot be located."""


class ConfigurationValidationError(ConfigurationError):
    """Raised when a configuration placeholder is invalid."""