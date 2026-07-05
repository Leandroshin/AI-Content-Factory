"""Employee exceptions for AI Content Factory."""

from __future__ import annotations


class EmployeeError(Exception):
    """Base exception for employee-related contracts."""


class EmployeeValidationError(EmployeeError):
    """Raised when an employee placeholder is structurally invalid."""


class EmployeeRegistryError(EmployeeError):
    """Raised when an employee registry placeholder cannot complete an operation."""


class EmployeeNotFoundError(EmployeeRegistryError):
    """Raised when an employee placeholder cannot be found."""


class EmployeeIdentityError(EmployeeError):
    """Raised when an employee identity placeholder is invalid."""