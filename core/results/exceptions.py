"""Result exceptions for AI Content Factory."""

from __future__ import annotations


class ResultError(Exception):
    """Base exception for result-related contracts."""


class ResultValidationError(ResultError):
    """Raised when a result placeholder is structurally invalid."""


class ResultRegistryError(ResultError):
    """Raised when a result registry placeholder cannot complete an operation."""


class ResultNotFoundError(ResultRegistryError):
    """Raised when a result placeholder cannot be found."""