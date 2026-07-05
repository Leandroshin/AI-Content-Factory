"""Organization exceptions for AI Content Factory."""

from __future__ import annotations


class OrganizationError(Exception):
    """Base exception for organization-related contracts."""


class OrganizationValidationError(OrganizationError):
    """Raised when an organization placeholder is structurally invalid."""


class OrganizationRegistryError(OrganizationError):
    """Raised when an organization registry placeholder cannot complete an operation."""


class OrganizationNotFoundError(OrganizationRegistryError):
    """Raised when an organization placeholder cannot be found."""