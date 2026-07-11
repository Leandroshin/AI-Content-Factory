"""Video Department — specialized video production for AI Company."""

from __future__ import annotations

from .editorial_quality import (
    EditorialBeat,
    EditorialCaptionCue,
    EditorialChapter,
    EditorialEditingProfile,
    EditorialQualityResult,
    EditorialQualityValidator,
    EditorialVideoPlan,
    LongFormRepurposingPlan,
    LongFormRepurposingValidator,
    ShortExtractionCandidate,
)
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
    "EditorialBeat",
    "EditorialCaptionCue",
    "EditorialChapter",
    "EditorialEditingProfile",
    "EditorialQualityResult",
    "EditorialQualityValidator",
    "EditorialVideoPlan",
    "ImageAsset",
    "LongFormRepurposingPlan",
    "LongFormRepurposingValidator",
    "PipelineStage",
    "RenderProfile",
    "ShortExtractionCandidate",
    "SubtitleSegment",
    "TimelineSegment",
    "VideoAsset",
    "VideoEditorEmployee",
    "VideoProductionPipeline",
    "VideoProject",
    "VideoTask",
]
