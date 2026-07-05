"""Policy exceptions for AI Content Factory."""

from __future__ import annotations


class PolicyError(Exception):
    """Base exception for policy-related contracts."""


class PolicyValidationError(PolicyError):
    """Raised when a policy placeholder is structurally invalid."""


class PolicyRegistryError(PolicyError):
    """Raised when a policy registry placeholder cannot complete an operation."""


class PolicyNotFoundError(PolicyRegistryError):
    """Raised when a policy placeholder cannot be found."""