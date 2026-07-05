"""Typed models for the Creative Review Department."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any
from uuid import UUID, uuid4


@dataclass(frozen=True, slots=True)
class CreativeAsset:
    """One product image, thumbnail, screenshot, or creative reference."""

    asset_id: UUID = field(default_factory=uuid4)
    title: str = ""
    asset_type: str = "product_image"
    product_name: str = ""
    platform: str = ""
    image_url: str = ""
    file_path: str = ""
    source_url: str = ""
    use_case: str = "affiliate_post"
    visual_quality: float = 6.0
    product_visibility: float = 6.0
    resolution_score: float = 6.0
    text_clutter: float = 3.0
    watermark_risk: float = 0.0
    brand_safety: float = 8.0
    face_emotion: float = 0.0
    proof_element: float = 0.0
    risk_flags: tuple[str, ...] = field(default_factory=tuple)
    notes: tuple[str, ...] = field(default_factory=tuple)
    metadata: dict[str, Any] = field(default_factory=dict)

    @property
    def has_image_reference(self) -> bool:
        return bool(self.image_url.strip() or self.file_path.strip())


@dataclass(frozen=True, slots=True)
class CreativeReviewBrief:
    """Creative review assignment."""

    task_id: UUID
    title: str
    objective: str = "Decide whether creative assets are ready or need improvement."
    assets: tuple[CreativeAsset, ...] = field(default_factory=tuple)
    target_platforms: tuple[str, ...] = field(default_factory=tuple)
    ready_threshold: float = 76.0
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class CreativeReviewFinding:
    """Review result for one creative asset."""

    asset: CreativeAsset
    score_total: float = 0.0
    readiness: str = "needs_review"
    recommended_action: str = "human_review"
    reasons: tuple[str, ...] = field(default_factory=tuple)
    improvement_tasks: tuple[str, ...] = field(default_factory=tuple)
    handoff_targets: tuple[str, ...] = field(default_factory=tuple)

    def to_public_dict(self) -> dict[str, Any]:
        return {
            "asset_id": str(self.asset.asset_id),
            "title": self.asset.title,
            "asset_type": self.asset.asset_type,
            "product_name": self.asset.product_name,
            "platform": self.asset.platform,
            "image_url": self.asset.image_url,
            "file_path": self.asset.file_path,
            "source_url": self.asset.source_url,
            "use_case": self.asset.use_case,
            "score_total": self.score_total,
            "readiness": self.readiness,
            "recommended_action": self.recommended_action,
            "reasons": list(self.reasons),
            "improvement_tasks": list(self.improvement_tasks),
            "handoff_targets": list(self.handoff_targets),
            "risk_flags": list(self.asset.risk_flags),
            "notes": list(self.asset.notes),
            "metadata": dict(self.asset.metadata),
        }


@dataclass(frozen=True, slots=True)
class CreativeReviewReport:
    """Final report delivered by Creative Review."""

    title: str
    total_assets: int = 0
    ready_count: int = 0
    improve_count: int = 0
    rebuild_count: int = 0
    human_review_count: int = 0
    findings: tuple[CreativeReviewFinding, ...] = field(default_factory=tuple)
    next_actions: tuple[str, ...] = field(default_factory=tuple)
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_public_dict(self) -> dict[str, Any]:
        return {
            "title": self.title,
            "total_assets": self.total_assets,
            "ready_count": self.ready_count,
            "improve_count": self.improve_count,
            "rebuild_count": self.rebuild_count,
            "human_review_count": self.human_review_count,
            "findings": [finding.to_public_dict() for finding in self.findings],
            "next_actions": list(self.next_actions),
            "metadata": dict(self.metadata),
        }


@dataclass(frozen=True, slots=True)
class CreativeReviewMetrics:
    """Metrics accumulated by creative review."""

    total_stages: int = 0
    completed_stages: int = 0
    failed_stages: int = 0
    assets_reviewed: int = 0
    ready_count: int = 0
    improve_count: int = 0
    rebuild_count: int = 0
    human_review_count: int = 0
    average_score: float = 0.0
    top_action: str = ""
    quality_passed: bool = True
    quality_corrections: tuple[str, ...] = field(default_factory=tuple)
    duration_minutes: float = 0.0
