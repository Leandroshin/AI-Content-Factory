"""Orchestrator contracts for AI Content Factory."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Protocol

from .models import ExecutionPlan, ExecutionResult, OrchestratorContext


class OrchestratorContract(Protocol):
    """Structural protocol for orchestration contracts."""

    def build_context(self, project_name: str | None = None) -> OrchestratorContext:
        """Build a context placeholder."""

    def create_plan(self, name: str) -> ExecutionPlan:
        """Create a plan placeholder."""

    def execute_plan(self, plan: ExecutionPlan, context: OrchestratorContext) -> ExecutionResult:
        """Execute a plan placeholder and return a result placeholder."""


class BaseOrchestrator(ABC):
    """Base contract for the orchestrator."""

    @abstractmethod
    def build_context(self, project_name: str | None = None) -> OrchestratorContext:
        """Build a context placeholder."""

    @abstractmethod
    def create_plan(self, name: str) -> ExecutionPlan:
        """Create a plan placeholder."""

    @abstractmethod
    def execute_plan(self, plan: ExecutionPlan, context: OrchestratorContext) -> ExecutionResult:
        """Execute a plan placeholder and return a result placeholder."""
