"""Video Department — specialized video production for AI Company."""

from __future__ import annotations

from .employee import VideoEditorEmployee
from .models import (
    AudioAsset,
    ImageAsset,
    RenderProfile,
    SubtitleSegment,
    TimelineSegment,
    VideoAsset,
    VideoProject,
    VideoTask,
)
from .pipeline import PipelineStage, VideoProductionPipeline

__all__ = [
    "AudioAsset",
    "ImageAsset",
    "PipelineStage",
    "RenderProfile",
    "SubtitleSegment",
    "TimelineSegment",
    "VideoAsset",
    "VideoEditorEmployee",
    "VideoProductionPipeline",
    "VideoProject",
    "VideoTask",
]
