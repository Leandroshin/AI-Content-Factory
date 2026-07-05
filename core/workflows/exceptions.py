"""Workflow exceptions for AI Content Factory."""

from __future__ import annotations


class WorkflowError(Exception):
    """Base exception for workflow-related contracts."""


class WorkflowValidationError(WorkflowError):
    """Raised when a workflow placeholder is structurally invalid."""


class WorkflowRegistryError(WorkflowError):
    """Raised when a workflow registry placeholder cannot complete an operation."""


class WorkflowNotFoundError(WorkflowRegistryError):
    """Raised when a workflow placeholder cannot be found."""


class WorkflowDependencyError(WorkflowError):
    """Raised when a workflow relationship is invalid."""