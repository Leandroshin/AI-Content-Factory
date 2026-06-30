"""Orchestrator exceptions for AI Content Factory."""

from __future__ import annotations

from core.exceptions import PipelineError


class OrchestratorError(PipelineError):
    """Base exception for orchestrator contracts."""


class OrchestratorPlanError(OrchestratorError):
    """Raised when a plan contract is invalid."""


class OrchestratorContextError(OrchestratorError):
    """Raised when a context contract is invalid."""


class OrchestratorExecutionError(OrchestratorError):
    """Raised when an execution result contract is invalid."""
