"""Immutable contracts shared by market and offer intelligence workflows."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from uuid import UUID


class EvidenceKind(StrEnum):
    TRANSCRIPT = "transcript"
    VISUAL = "visual"
    WEB_PAGE = "web_page"
    METRIC = "metric"
    DOCUMENT = "document"


class ClaimVerdict(StrEnum):
    UNSUPPORTED = "unsupported"
    PARTIAL = "partial"
    SUPPORTED = "supported"
    CONFLICTED = "conflicted"


class ExperimentStatus(StrEnum):
    PROPOSED = "proposed"
    APPROVED = "approved"
    RUNNING = "running"
    MEASURED = "measured"
    REJECTED = "rejected"


class KnowledgeDraftStatus(StrEnum):
    PENDING_EXPERIMENT = "pending_experiment"
    PENDING_AUDIT = "pending_audit"
    ELIGIBLE_FOR_PROMOTION = "eligible_for_promotion"
    REJECTED = "rejected"


@dataclass(frozen=True, slots=True)
class EvidenceRef:
    evidence_id: str
    kind: EvidenceKind
    source_uri: str
    locator: str
    content_sha256: str
    collected_at: float
    confidence: float
    independent_source: bool = False
    expires_at: float | None = None
    notes: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        _require_text(self.evidence_id, "evidence_id")
        _require_text(self.source_uri, "source_uri")
        _require_hash(self.content_sha256, "content_sha256")
        _require_unit_interval(self.confidence, "confidence")


@dataclass(frozen=True, slots=True)
class SourceArtifact:
    source_id: str
    title: str
    source_uri: str
    creator: str
    collected_at: float
    content_sha256: str
    evidence_ids: tuple[str, ...]
    owner_provided: bool = True

    def __post_init__(self) -> None:
        _require_text(self.source_id, "source_id")
        _require_text(self.title, "title")
        if not self.source_uri.startswith("https://"):
            raise ValueError("source_uri must use HTTPS.")
        _require_hash(self.content_sha256, "content_sha256")
        if not self.evidence_ids:
            raise ValueError("SourceArtifact requires evidence_ids.")


@dataclass(frozen=True, slots=True)
class ClaimRecord:
    claim_id: str
    source_id: str
    text: str
    evidence_ids: tuple[str, ...]
    claimed_confidence: float
    tags: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        _require_text(self.claim_id, "claim_id")
        _require_text(self.source_id, "source_id")
        _require_text(self.text, "text")
        if not self.evidence_ids:
            raise ValueError("ClaimRecord requires evidence_ids.")
        _require_unit_interval(self.claimed_confidence, "claimed_confidence")


@dataclass(frozen=True, slots=True)
class ClaimAudit:
    audit_id: str
    claim_id: str
    verdict: ClaimVerdict
    confidence: float
    supporting_evidence_ids: tuple[str, ...]
    independent_evidence_ids: tuple[str, ...]
    missing_evidence: tuple[str, ...]
    conflicts: tuple[str, ...]
    audited_at: float
    rationale: tuple[str, ...]

    def __post_init__(self) -> None:
        _require_text(self.audit_id, "audit_id")
        _require_text(self.claim_id, "claim_id")
        _require_unit_interval(self.confidence, "confidence")
        if self.verdict == ClaimVerdict.SUPPORTED and not self.independent_evidence_ids:
            raise ValueError("A supported claim requires independent evidence.")


@dataclass(frozen=True, slots=True)
class ExperimentSpec:
    experiment_id: str
    claim_id: str
    title: str
    hypothesis: str
    baseline: str
    variant: str
    primary_metric: str
    success_threshold: str
    stop_conditions: tuple[str, ...]
    evidence_ids: tuple[str, ...]
    estimated_cost: float = 0.0
    currency: str = "USD"
    status: ExperimentStatus = ExperimentStatus.PROPOSED
    owner_approval_required: bool = True

    def __post_init__(self) -> None:
        _require_text(self.experiment_id, "experiment_id")
        _require_text(self.claim_id, "claim_id")
        _require_text(self.hypothesis, "hypothesis")
        _require_text(self.primary_metric, "primary_metric")
        if self.estimated_cost < 0:
            raise ValueError("estimated_cost cannot be negative.")


@dataclass(frozen=True, slots=True)
class KnowledgeCardDraft:
    card_id: str
    title: str
    statement: str
    applicability: str
    risks: tuple[str, ...]
    evidence_ids: tuple[str, ...]
    audit_id: str
    experiment_id: str
    status: KnowledgeDraftStatus
    created_at: float
    content_sha256: str
    schema_version: str = "1.0"

    def __post_init__(self) -> None:
        _require_text(self.card_id, "card_id")
        _require_text(self.title, "title")
        _require_text(self.statement, "statement")
        _require_hash(self.content_sha256, "content_sha256")


@dataclass(frozen=True, slots=True)
class ShadowSourceInput:
    title: str
    source_uri: str
    creator: str
    transcript_text: str
    transcript_locator: str
    visual_uri: str
    visual_content: bytes
    visual_locator: str
    claim_text: str
    hypothesis: str
    tags: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        _require_text(self.title, "title")
        if not self.source_uri.startswith("https://"):
            raise ValueError("source_uri must use HTTPS.")
        _require_text(self.transcript_text, "transcript_text")
        _require_text(self.visual_uri, "visual_uri")
        if not self.visual_content:
            raise ValueError("visual_content is required.")
        _require_text(self.claim_text, "claim_text")


@dataclass(frozen=True, slots=True)
class BoundApprovalRef:
    approval_id: UUID
    payload_sha256: str
    subject_id: str
    binding_version: str = "1.0"

    def __post_init__(self) -> None:
        _require_hash(self.payload_sha256, "payload_sha256")
        _require_text(self.subject_id, "subject_id")


@dataclass(frozen=True, slots=True)
class MarketIntelligenceShadowResult:
    source: SourceArtifact
    evidence: tuple[EvidenceRef, ...]
    claim: ClaimRecord
    audit: ClaimAudit
    experiment: ExperimentSpec
    knowledge_draft: KnowledgeCardDraft
    approval: BoundApprovalRef
    provider_called: bool = False
    provider_cost: float = 0.0
    memory_promoted: bool = False
    publication_attempted: bool = False


def _require_text(value: str, name: str) -> None:
    if not value.strip():
        raise ValueError(f"{name} is required.")


def _require_hash(value: str, name: str) -> None:
    if len(value) != 64 or any(char not in "0123456789abcdef" for char in value):
        raise ValueError(f"{name} must be a lowercase SHA-256 hash.")


def _require_unit_interval(value: float, name: str) -> None:
    if not 0.0 <= value <= 1.0:
        raise ValueError(f"{name} must be between 0 and 1.")
