"""Typed models for the Strategy Intelligence Department."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any
from uuid import UUID, uuid4


@dataclass(frozen=True, slots=True)
class StrategySource:
    """One learning source analyzed by the strategy team.

    transcript_text is intentionally not exposed by to_public_dict(); raw
    transcripts are local inputs, while the project stores derived knowledge.
    """

    source_id: UUID = field(default_factory=uuid4)
    title: str = ""
    creator: str = ""
    source_url: str = ""
    source_type: str = "transcript"
    transcript_text: str = ""
    tags: tuple[str, ...] = field(default_factory=tuple)
    metadata: dict[str, Any] = field(default_factory=dict)

    @property
    def has_text(self) -> bool:
        return bool(self.transcript_text.strip())

    def to_public_dict(self) -> dict[str, Any]:
        return {
            "source_id": str(self.source_id),
            "title": self.title,
            "creator": self.creator,
            "source_url": self.source_url,
            "source_type": self.source_type,
            "tags": list(self.tags),
            "word_count": len(self.transcript_text.split()),
            "metadata": dict(self.metadata),
        }


@dataclass(frozen=True, slots=True)
class ToolMention:
    """Detected tool or platform mention."""

    name: str
    category: str
    confidence: float = 0.5
    sources: tuple[str, ...] = field(default_factory=tuple)
    notes: tuple[str, ...] = field(default_factory=tuple)

    def to_public_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "category": self.category,
            "confidence": self.confidence,
            "sources": list(self.sources),
            "notes": list(self.notes),
        }


@dataclass(frozen=True, slots=True)
class MetricMention:
    """Detected metric or decision signal."""

    name: str
    use_case: str
    confidence: float = 0.5
    sources: tuple[str, ...] = field(default_factory=tuple)
    notes: tuple[str, ...] = field(default_factory=tuple)

    def to_public_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "use_case": self.use_case,
            "confidence": self.confidence,
            "sources": list(self.sources),
            "notes": list(self.notes),
        }


@dataclass(frozen=True, slots=True)
class StrategyPattern:
    """Reusable strategy extracted from one or more sources."""

    pattern_id: str
    title: str
    category: str
    confidence: float = 0.5
    routes_to: tuple[str, ...] = field(default_factory=tuple)
    evidence_points: tuple[str, ...] = field(default_factory=tuple)
    guardrails: tuple[str, ...] = field(default_factory=tuple)

    def to_public_dict(self) -> dict[str, Any]:
        return {
            "pattern_id": self.pattern_id,
            "title": self.title,
            "category": self.category,
            "confidence": self.confidence,
            "routes_to": list(self.routes_to),
            "evidence_points": list(self.evidence_points),
            "guardrails": list(self.guardrails),
        }


@dataclass(frozen=True, slots=True)
class StrategyIntelligenceTask:
    """Learning assignment for strategy extraction."""

    task_id: UUID
    title: str
    objective: str = "Extract reusable content and commerce strategy."
    sources: tuple[StrategySource, ...] = field(default_factory=tuple)
    focus_areas: tuple[str, ...] = field(default_factory=tuple)
    max_patterns: int = 8
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class StrategyIntelligenceReport:
    """Final strategy intelligence report."""

    title: str
    sources_analyzed: int = 0
    tools_detected: tuple[ToolMention, ...] = field(default_factory=tuple)
    metrics_detected: tuple[MetricMention, ...] = field(default_factory=tuple)
    patterns: tuple[StrategyPattern, ...] = field(default_factory=tuple)
    warnings: tuple[str, ...] = field(default_factory=tuple)
    next_actions: tuple[str, ...] = field(default_factory=tuple)
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_public_dict(self) -> dict[str, Any]:
        return {
            "title": self.title,
            "sources_analyzed": self.sources_analyzed,
            "tools_detected": [tool.to_public_dict() for tool in self.tools_detected],
            "metrics_detected": [metric.to_public_dict() for metric in self.metrics_detected],
            "patterns": [pattern.to_public_dict() for pattern in self.patterns],
            "warnings": list(self.warnings),
            "next_actions": list(self.next_actions),
            "metadata": dict(self.metadata),
        }


@dataclass(frozen=True, slots=True)
class StrategyIntelligenceMetrics:
    """Metrics accumulated by strategy intelligence."""

    total_stages: int = 0
    completed_stages: int = 0
    failed_stages: int = 0
    sources_analyzed: int = 0
    tools_detected: int = 0
    metrics_detected: int = 0
    patterns_extracted: int = 0
    warnings_count: int = 0
    top_pattern: str = ""
    quality_passed: bool = True
    quality_corrections: tuple[str, ...] = field(default_factory=tuple)
    duration_minutes: float = 0.0
