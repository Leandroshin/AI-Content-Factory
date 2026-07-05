"""Typed audio production models for the Audio Department.

All models are frozen+slots for deterministic, low-overhead usage.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any
from uuid import UUID, uuid4


@dataclass(frozen=True, slots=True)
class AudioTask:
    """A complete audio production task assigned to AudioEngineerEmployee."""
    task_id: UUID
    title: str
    audio_type: str = "voiceover"
    duration_seconds: int = 60
    tracks: tuple[AudioTrack, ...] = field(default_factory=tuple)
    voice_segments: tuple[VoiceSegment, ...] = field(default_factory=tuple)
    music_segments: tuple[MusicSegment, ...] = field(default_factory=tuple)
    sound_effects: tuple[SoundEffect, ...] = field(default_factory=tuple)
    mix_profile: MixProfile | None = None
    master_profile: MasterProfile | None = None
    quality_rules: tuple[str, ...] = field(default_factory=tuple)
    metadata: dict[str, Any] = field(default_factory=dict)

    @property
    def requires_capabilities(self) -> tuple[str, ...]:
        needed = ["audio_processing"]
        if any(v.text for v in self.voice_segments if v.text):
            needed.append("speech_generation")
        if self.master_profile is not None:
            needed.append("audio_editing")
        return tuple(needed)


@dataclass(frozen=True, slots=True)
class AudioAsset:
    """An audio media asset (recording, sample, stem)."""
    asset_id: UUID = field(default_factory=uuid4)
    type: str = "recording"
    source: str = ""
    duration_seconds: float = 0.0
    format: str = "wav"
    sample_rate: int = 48000
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class AudioTrack:
    """A single audio track in the production."""
    track_id: UUID = field(default_factory=uuid4)
    name: str = "Track 1"
    type: str = "voice"
    source: str = ""
    volume: float = 1.0
    pan: float = 0.0
    muted: bool = False
    effects: tuple[str, ...] = field(default_factory=tuple)
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class VoiceSegment:
    """A voice recording segment with text content."""
    segment_id: UUID = field(default_factory=uuid4)
    speaker: str = "default"
    text: str = ""
    start_time: float = 0.0
    end_time: float = 10.0
    style: str = "natural"
    speed: float = 1.0
    pitch: float = 0.0
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class MusicSegment:
    """A music segment for background or scoring."""
    segment_id: UUID = field(default_factory=uuid4)
    genre: str = "ambient"
    mood: str = "calm"
    tempo: int = 120
    start_time: float = 0.0
    end_time: float = 30.0
    volume: float = 0.3
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class SoundEffect:
    """A sound effect placed in the timeline."""
    effect_id: UUID = field(default_factory=uuid4)
    type: str = "impact"
    source: str = ""
    start_time: float = 0.0
    end_time: float = 2.0
    volume: float = 0.8
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class MixProfile:
    """Mixing configuration before mastering."""
    sample_rate: int = 48000
    bit_depth: int = 24
    channels: int = 2
    volume_normalize: bool = True
    noise_gate: bool = False
    compressor: str = "none"
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class MasterProfile:
    """Mastering / export configuration for final output."""
    format: str = "wav"
    codec: str = "pcm"
    bitrate: str = "1411k"
    loudness_target: float = -14.0
    sample_rate: int = 48000
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class AudioProject:
    """A complete audio project combining all production data."""
    project_id: UUID = field(default_factory=uuid4)
    title: str = ""
    audio_type: str = "voiceover"
    sample_rate: int = 48000
    tracks: tuple[AudioTrack, ...] = field(default_factory=tuple)
    voice_segments: tuple[VoiceSegment, ...] = field(default_factory=tuple)
    music_segments: tuple[MusicSegment, ...] = field(default_factory=tuple)
    sound_effects: tuple[SoundEffect, ...] = field(default_factory=tuple)
    mix_profile: MixProfile = field(default_factory=MixProfile)
    master_profile: MasterProfile = field(default_factory=MasterProfile)
    created_at: float = 0.0
    status: str = "created"
    metadata: dict[str, Any] = field(default_factory=dict)
