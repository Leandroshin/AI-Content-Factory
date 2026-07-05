"""Typed image production models for the Image Department.

All models are frozen+slots for deterministic, low-overhead usage.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any
from uuid import UUID, uuid4


@dataclass(frozen=True, slots=True)
class DesignBrief:
    """Creative brief describing the design requirements."""
    brief_id: UUID = field(default_factory=uuid4)
    title: str = ""
    description: str = ""
    style: str = "modern"
    color_palette: tuple[str, ...] = field(default_factory=tuple)
    references: tuple[str, ...] = field(default_factory=tuple)
    target_audience: str = ""
    brand_guidelines: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class CanvasSpec:
    """Canvas/dimensions specification for the output image."""
    width: int = 1920
    height: int = 1080
    dpi: int = 72
    orientation: str = "landscape"
    background_color: str = "#FFFFFF"
    bleed_mm: float = 0.0
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class TextOverlay:
    """Text element placed on the canvas."""
    overlay_id: UUID = field(default_factory=uuid4)
    text: str = ""
    font_family: str = "Arial"
    font_size: int = 48
    font_color: str = "#000000"
    font_weight: str = "normal"
    alignment: str = "center"
    x: float = 0.0
    y: float = 0.0
    width: float = 1920.0
    height: float = 100.0
    rotation: float = 0.0
    opacity: float = 1.0
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class LayerSpec:
    """A single layer in the composition."""
    layer_id: UUID = field(default_factory=uuid4)
    name: str = "Layer 1"
    type: str = "shape"
    source: str = ""
    x: float = 0.0
    y: float = 0.0
    width: float = 1920.0
    height: float = 1080.0
    rotation: float = 0.0
    opacity: float = 1.0
    blend_mode: str = "normal"
    visible: bool = True
    order: int = 0
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class ExportProfile:
    """Export configuration for the final image output."""
    format: str = "png"
    quality: int = 95
    color_space: str = "sRGB"
    icc_profile: str = ""
    optimize_for_web: bool = True
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class ImageVariant:
    """A variant derived from the base design (resize, format, crop)."""
    variant_id: UUID = field(default_factory=uuid4)
    name: str = "default"
    width: int = 1920
    height: int = 1080
    format: str = "png"
    quality: int = 85
    crop: str = "center"
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class ImageAsset:
    """An image asset (source, overlay, or generated element)."""
    asset_id: UUID = field(default_factory=uuid4)
    type: str = "source"
    source: str = ""
    width: int = 0
    height: int = 0
    format: str = "png"
    file_size_bytes: int = 0
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class ImageTask:
    """A complete image production task assigned to ImageDesignerEmployee."""
    task_id: UUID
    title: str
    image_type: str = "thumbnail"
    canvas: CanvasSpec = field(default_factory=CanvasSpec)
    layers: tuple[LayerSpec, ...] = field(default_factory=tuple)
    text_overlays: tuple[TextOverlay, ...] = field(default_factory=tuple)
    assets: tuple[ImageAsset, ...] = field(default_factory=tuple)
    variants: tuple[ImageVariant, ...] = field(default_factory=tuple)
    design_brief: DesignBrief | None = None
    export_profile: ExportProfile | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    @property
    def requires_capabilities(self) -> tuple[str, ...]:
        needed = ["image_generation"]
        if self.layers:
            needed.append("image_editing")
        if self.variants:
            needed.append("storage")
        return tuple(needed)


@dataclass(frozen=True, slots=True)
class ImageProject:
    """A complete image project combining all production data."""
    project_id: UUID = field(default_factory=uuid4)
    title: str = ""
    image_type: str = "thumbnail"
    canvas: CanvasSpec = field(default_factory=CanvasSpec)
    layers: tuple[LayerSpec, ...] = field(default_factory=tuple)
    text_overlays: tuple[TextOverlay, ...] = field(default_factory=tuple)
    assets: tuple[ImageAsset, ...] = field(default_factory=tuple)
    variants: tuple[ImageVariant, ...] = field(default_factory=tuple)
    design_brief: DesignBrief = field(default_factory=DesignBrief)
    export_profile: ExportProfile = field(default_factory=ExportProfile)
    created_at: float = 0.0
    status: str = "created"
    metadata: dict[str, Any] = field(default_factory=dict)
