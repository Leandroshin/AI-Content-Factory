"""Core pipeline step contracts for AI Content Factory."""

from __future__ import annotations

from abc import ABC, abstractmethod

from .models import PipelineContext, PipelineResult


class PipelineStep(ABC):
    """Base contract for a pipeline step."""

    name: str

    @abstractmethod
    def describe(self) -> str:
        """Return a human-readable description of the step."""

    @abstractmethod
    def build_result(
        self,
        context: PipelineContext,
    ) -> PipelineResult:
        """Return a placeholder result for the step."""
