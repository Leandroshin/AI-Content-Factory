"""Typed script production models for the Script Department.

All models are frozen+slots for deterministic, low-overhead usage.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any
from uuid import UUID, uuid4


@dataclass(frozen=True, slots=True)
class ScriptBrief:
    """Creative brief describing the script goal and audience."""
    brief_id: UUID = field(default_factory=uuid4)
    topic: str = ""
    objective: str = ""
    target_audience: str = ""
    tone: str = "clear"
    language: str = "pt-BR"
    platform: str = "youtube"
    key_points: tuple[str, ...] = field(default_factory=tuple)
    constraints: tuple[str, ...] = field(default_factory=tuple)
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class ScriptSection:
    """A logical section in the script structure."""
    section_id: UUID = field(default_factory=uuid4)
    name: str = "section"
    purpose: str = ""
    target_duration_seconds: int = 10
    content: str = ""
    order: int = 0
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class HookVariant:
    """Opening hook candidate for retention."""
    hook_id: UUID = field(default_factory=uuid4)
    text: str = ""
    style: str = "curiosity"
    platform: str = ""
    retention_score: float = 0.0
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class CallToAction:
    """Call to action used in the script."""
    cta_id: UUID = field(default_factory=uuid4)
    text: str = ""
    action_type: str = "engagement"
    placement: str = "end"
    urgency: str = "medium"
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class NarrationBlock:
    """Narration segment with speaker, timing, and text."""
    block_id: UUID = field(default_factory=uuid4)
    speaker: str = "narrator"
    text: str = ""
    start_time: float = 0.0
    duration_seconds: float = 5.0
    style: str = "natural"
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class RetentionBeat:
    """A planned retention moment in the script."""
    beat_id: UUID = field(default_factory=uuid4)
    timestamp_seconds: float = 0.0
    technique: str = "pattern_interrupt"
    message: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class ScriptVariant:
    """A version of the script for a different angle or language."""
    variant_id: UUID = field(default_factory=uuid4)
    name: str = "default"
    angle: str = ""
    hook: str = ""
    body: str = ""
    call_to_action: str = ""
    language: str = "pt-BR"
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class ScriptExportProfile:
    """Export configuration for final script delivery."""
    format: str = "markdown"
    language: str = "pt-BR"
    include_timestamps: bool = True
    include_narration: bool = True
    include_sections: bool = True
    platform_template: str = "youtube"
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class ScriptTask:
    """A complete script production task assigned to ScriptWriterEmployee."""
    task_id: UUID
    title: str
    script_type: str = "video"
    duration_seconds: int = 60
    brief: ScriptBrief = field(default_factory=ScriptBrief)
    sections: tuple[ScriptSection, ...] = field(default_factory=tuple)
    hooks: tuple[HookVariant, ...] = field(default_factory=tuple)
    call_to_action: CallToAction | None = None
    narration_blocks: tuple[NarrationBlock, ...] = field(default_factory=tuple)
    retention_beats: tuple[RetentionBeat, ...] = field(default_factory=tuple)
    variants: tuple[ScriptVariant, ...] = field(default_factory=tuple)
    export_profile: ScriptExportProfile | None = None
    quality_rules: tuple[str, ...] = field(default_factory=tuple)
    metadata: dict[str, Any] = field(default_factory=dict)

    @property
    def requires_capabilities(self) -> tuple[str, ...]:
        needed = ["text_generation", "document_generation"]
        if self.brief.key_points or self.metadata.get("requires_research"):
            needed.append("web_search")
        source_language = self.metadata.get("source_language")
        target_language = self.brief.language
        if source_language and source_language != target_language:
            needed.append("translation")
        if self.variants:
            needed.append("storage")
        return tuple(dict.fromkeys(needed))


@dataclass(frozen=True, slots=True)
class ScriptProject:
    """A complete script project combining all production data."""
    project_id: UUID = field(default_factory=uuid4)
    title: str = ""
    script_type: str = "video"
    duration_seconds: int = 60
    brief: ScriptBrief = field(default_factory=ScriptBrief)
    sections: tuple[ScriptSection, ...] = field(default_factory=tuple)
    hooks: tuple[HookVariant, ...] = field(default_factory=tuple)
    call_to_action: CallToAction | None = None
    narration_blocks: tuple[NarrationBlock, ...] = field(default_factory=tuple)
    retention_beats: tuple[RetentionBeat, ...] = field(default_factory=tuple)
    variants: tuple[ScriptVariant, ...] = field(default_factory=tuple)
    export_profile: ScriptExportProfile = field(default_factory=ScriptExportProfile)
    created_at: float = 0.0
    status: str = "created"
    metadata: dict[str, Any] = field(default_factory=dict)
