"""Department exceptions for AI Content Factory."""

from __future__ import annotations

from core.exceptions import AIContentFactoryError


class DepartmentError(AIContentFactoryError):
    """Base exception for department contracts."""


class DepartmentRegistryError(DepartmentError):
    """Raised when a department registry contract is invalid."""


class DepartmentValidationError(DepartmentError):
    """Raised when a department validator contract is invalid."""
