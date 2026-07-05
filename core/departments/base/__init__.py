"""Base Department Layer — template for all specialized departments.

Fornece infraestrutura reutilizável:
- ProductionPipeline (ABC) com StageResult
- ProductionMetrics genérico
- ProductionEmployee (herda SpecialistEmployee)
"""

from __future__ import annotations

from .employee import ProductionEmployee
from .models import ProductionMetrics
from .pipeline import ProductionPipeline, StageResult

__all__ = [
    "ProductionEmployee",
    "ProductionMetrics",
    "ProductionPipeline",
    "StageResult",
]
