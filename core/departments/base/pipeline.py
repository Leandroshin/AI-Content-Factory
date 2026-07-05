"""Generic production pipeline infrastructure.

Fornece base reutilizável para pipelines departamentais.
Cada departamento estende ProductionPipeline com seus
próprios estágios e lógica específica.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True, slots=True)
class StageResult:
    """Result of a single pipeline stage execution.

    Totalmente genérico — usado por qualquer departamento.
    """
    stage: str
    success: bool
    summary: str = ""
    output: dict[str, Any] = field(default_factory=dict)
    error: str = ""
    next_stage: str | None = None


class ProductionPipeline(ABC):
    """Abstract base for all production pipelines.

    Subclasses definem seus próprios estágios e handlers.
    O contrato é: advance() retorna StageResult, stage/progress
    refletem o estado atual.
    """

    def __init__(self) -> None:
        self._stage: str = "created"
        self._stages_log: list[StageResult] = []

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    @property
    def stage(self) -> str:
        return self._stage

    @property
    def stages_log(self) -> tuple[StageResult, ...]:
        return tuple(self._stages_log)

    @property
    def progress(self) -> float:
        return 0.0

    @abstractmethod
    def advance(self) -> StageResult:
        """Execute current stage and transition to next."""

    def reset(self) -> None:
        self._stage = "created"
        self._stages_log.clear()
