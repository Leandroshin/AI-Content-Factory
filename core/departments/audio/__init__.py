"""Audio Department — specialized audio production for AI Company."""

from __future__ import annotations

from .employee import AudioEngineerEmployee
from .models import (
    AudioAsset,
    AudioProject,
    AudioTask,
    AudioTrack,
    MasterProfile,
    MixProfile,
    MusicSegment,
    SoundEffect,
    VoiceSegment,
)
from .pipeline import AudioProductionPipeline, PipelineStage

__all__ = [
    "AudioAsset",
    "AudioEngineerEmployee",
    "AudioProductionPipeline",
    "AudioProject",
    "AudioTask",
    "AudioTrack",
    "MasterProfile",
    "MixProfile",
    "MusicSegment",
    "PipelineStage",
    "SoundEffect",
    "VoiceSegment",
]
