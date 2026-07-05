"""Image Department — specialized image production for AI Company."""

from __future__ import annotations

from .employee import ImageDesignerEmployee
from .models import (
    CanvasSpec,
    DesignBrief,
    ExportProfile,
    ImageAsset,
    ImageProject,
    ImageTask,
    ImageVariant,
    LayerSpec,
    TextOverlay,
)
from .pipeline import ImageProductionPipeline, PipelineStage

__all__ = [
    "CanvasSpec",
    "DesignBrief",
    "ExportProfile",
    "ImageAsset",
    "ImageDesignerEmployee",
    "ImageProductionPipeline",
    "ImageProject",
    "ImageTask",
    "ImageVariant",
    "LayerSpec",
    "PipelineStage",
    "TextOverlay",
]
