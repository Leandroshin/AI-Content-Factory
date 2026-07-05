"""Typed video production models for the Video Department.

All models are frozen+slots for deterministic, low-overhead usage.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any
from uuid import UUID, uuid4


# ==================================================================
# Video Task
# ==================================================================


@dataclass(frozen=True, slots=True)
class VideoTask:
    """A complete video production task assigned to VideoEditorEmployee."""
    task_id: UUID
    title: str
    video_type: str = "horizontal"
    duration_seconds: int = 60
    assets: tuple[VideoAsset, ...] = field(default_factory=tuple)
    subtitles: tuple[SubtitleSegment, ...] = field(default_factory=tuple)
    timeline: tuple[TimelineSegment, ...] = field(default_factory=tuple)
    render_profile: RenderProfile | None = None
    quality_rules: tuple[str, ...] = field(default_factory=tuple)
    metadata: dict[str, Any] = field(default_factory=dict)

    @property
    def requires_capabilities(self) -> tuple[str, ...]:
        needed = ["video_editing", "video_rendering"]
        if self.subtitles:
            needed.append("translation")
        if any(a.type == "browser" for a in self.assets):
            needed.append("browser_automation")
        if any(a.type == "code" for a in self.assets):
            needed.append("repository_management")
        return tuple(needed)


# ==================================================================
# Media Assets
# ==================================================================


@dataclass(frozen=True, slots=True)
class VideoAsset:
    """A video or media asset used in production."""
    asset_id: UUID = field(default_factory=uuid4)
    type: str = "video"
    source: str = ""
    duration_seconds: float = 0.0
    format: str = "mp4"
    resolution: tuple[int, int] = (1920, 1080)
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class AudioAsset:
    """An audio asset (voiceover, music, SFX)."""
    asset_id: UUID = field(default_factory=uuid4)
    type: str = "music"
    source: str = ""
    duration_seconds: float = 0.0
    format: str = "mp3"
    sample_rate: int = 44100
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class ImageAsset:
    """A static image asset (thumbnail, overlay, background)."""
    asset_id: UUID = field(default_factory=uuid4)
    type: str = "thumbnail"
    source: str = ""
    format: str = "png"
    resolution: tuple[int, int] = (1920, 1080)
    metadata: dict[str, Any] = field(default_factory=dict)


# ==================================================================
# Timeline & Subtitles
# ==================================================================


@dataclass(frozen=True, slots=True)
class TimelineSegment:
    """A single segment on the video timeline."""
    segment_id: UUID = field(default_factory=uuid4)
    asset_id: UUID | None = None
    start_time: float = 0.0
    end_time: float = 10.0
    layer: int = 0
    effects: tuple[str, ...] = field(default_factory=tuple)
    transitions: tuple[str, ...] = field(default_factory=tuple)
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class SubtitleSegment:
    """A single subtitle/caption entry."""
    subtitle_id: UUID = field(default_factory=uuid4)
    start_time: float = 0.0
    end_time: float = 3.0
    text: str = ""
    style: str = "default"
    metadata: dict[str, Any] = field(default_factory=dict)


# ==================================================================
# Render & Project
# ==================================================================


@dataclass(frozen=True, slots=True)
class RenderProfile:
    """Export/encoding configuration for video output."""
    profile_id: UUID = field(default_factory=uuid4)
    format: str = "mp4"
    codec: str = "h264"
    resolution: tuple[int, int] = (1920, 1080)
    fps: int = 30
    bitrate: str = "8M"
    quality: str = "standard"
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class VideoProject:
    """A complete video project combining all production data."""
    project_id: UUID = field(default_factory=uuid4)
    title: str = ""
    video_type: str = "horizontal"
    resolution: tuple[int, int] = (1920, 1080)
    fps: int = 30
    assets: tuple[VideoAsset | AudioAsset | ImageAsset, ...] = field(default_factory=tuple)
    timeline: tuple[TimelineSegment, ...] = field(default_factory=tuple)
    subtitles: tuple[SubtitleSegment, ...] = field(default_factory=tuple)
    render_profile: RenderProfile = field(default_factory=RenderProfile)
    created_at: float = 0.0
    status: str = "created"
    metadata: dict[str, Any] = field(default_factory=dict)
