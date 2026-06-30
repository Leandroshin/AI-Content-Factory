"""Core pipeline executor contracts for AI Content Factory."""

from __future__ import annotations

from abc import ABC, abstractmethod

from .models import Pipeline, PipelineContext, PipelineResult


class PipelineExecutor(ABC):
    """Base contract for pipeline execution."""

    @abstractmethod
    def execute(
        self,
        pipeline: Pipeline,
        context: PipelineContext,
    ) -> PipelineResult:
        """Execute a pipeline contract and return a result placeholder."""
