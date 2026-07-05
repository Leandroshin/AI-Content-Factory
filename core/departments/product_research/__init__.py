"""Product Research Department - product discovery and shortlisting."""

from __future__ import annotations

from .employee import ProductResearchCapability, ProductResearchEmployee
from .models import (
    MarketplaceSignal,
    ProductCandidate,
    ProductResearchBrief,
    ProductResearchFinding,
    ProductResearchMetrics,
    ProductResearchReport,
)
from .pipeline import PipelineStage, ProductResearchPipeline

__all__ = [
    "MarketplaceSignal",
    "PipelineStage",
    "ProductCandidate",
    "ProductResearchBrief",
    "ProductResearchCapability",
    "ProductResearchEmployee",
    "ProductResearchFinding",
    "ProductResearchMetrics",
    "ProductResearchPipeline",
    "ProductResearchReport",
]
