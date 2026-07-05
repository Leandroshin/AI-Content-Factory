"""Generic production models for all departments.

Cada departamento pode estender com campos específicos.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True, slots=True)
class ProductionMetrics:
    """Generic production metrics shared across all departments.

    Subclasses/departments adicionam campos específicos.
    """
    total_stages: int = 0
    completed_stages: int = 0
    failed_stages: int = 0
    quality_passed: bool = False
    quality_corrections: tuple[str, ...] = field(default_factory=tuple)
    duration_minutes: float = 0.0
