"""Deterministic transcript evidence audit without providers or promotion."""

from __future__ import annotations

from dataclasses import dataclass
import time

from core.intelligence.canonical import content_sha256, raw_sha256
from core.intelligence.contracts import (
    ClaimAudit,
    ClaimRecord,
    ClaimVerdict,
    EvidenceKind,
    EvidenceRef,
    KnowledgeCardDraft,
    KnowledgeDraftStatus,
    SourceArtifact,
)


@dataclass(frozen=True, slots=True)
class TranscriptClaimInput:
    title: str
    source_uri: str
    creator: str
    transcript_text: str
    expected_transcript_sha256: str
    evidence_excerpt: str
    evidence_locator: str
    claim_text: str
    candidate_statement: str
    applicability: str
    risks: tuple[str, ...] = ()
    tags: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class TranscriptAuditResult:
    source: SourceArtifact
    evidence: EvidenceRef
    claim: ClaimRecord
    audit: ClaimAudit
    knowledge_draft: KnowledgeCardDraft
    provider_called: bool = False
    provider_cost: float = 0.0
    experiment_started: bool = False
    memory_promoted: bool = False
    publication_attempted: bool = False


class TranscriptEvidenceAuditWorkflow:
    """Bind one human-selected claim to an exact transcript version and excerpt."""

    def run(self, audit_input: TranscriptClaimInput, *, now: float | None = None) -> TranscriptAuditResult:
        created_at = time.time() if now is None else now
        transcript_hash = raw_sha256(audit_input.transcript_text)
        if transcript_hash != audit_input.expected_transcript_sha256:
            raise ValueError("Transcript hash does not match the reviewed version.")
        excerpt = audit_input.evidence_excerpt.strip()
        if len(excerpt) < 40 or excerpt not in audit_input.transcript_text:
            raise ValueError("Evidence excerpt must be an exact transcript passage with at least 40 characters.")
        if not audit_input.source_uri.startswith("https://"):
            raise ValueError("source_uri must use HTTPS.")

        evidence_hash = raw_sha256(excerpt)
        source_hash = content_sha256(
            {
                "source_uri": audit_input.source_uri,
                "transcript_sha256": transcript_hash,
            }
        )
        source_id = f"source-{source_hash[:16]}"
        evidence = EvidenceRef(
            evidence_id=f"evidence-transcript-{evidence_hash[:16]}",
            kind=EvidenceKind.TRANSCRIPT,
            source_uri=audit_input.source_uri,
            locator=audit_input.evidence_locator,
            content_sha256=evidence_hash,
            collected_at=created_at,
            confidence=0.82,
            independent_source=False,
            notes=(
                "Exact owner-reviewed excerpt from the hash-bound transcript.",
                "This proves what the source states, not that the statement is independently true.",
            ),
        )
        source = SourceArtifact(
            source_id=source_id,
            title=audit_input.title,
            source_uri=audit_input.source_uri,
            creator=audit_input.creator,
            collected_at=created_at,
            content_sha256=source_hash,
            evidence_ids=(evidence.evidence_id,),
        )
        claim_hash = content_sha256(
            {
                "source_id": source_id,
                "claim_text": audit_input.claim_text,
                "evidence_id": evidence.evidence_id,
            }
        )
        claim = ClaimRecord(
            claim_id=f"claim-{claim_hash[:16]}",
            source_id=source_id,
            text=audit_input.claim_text,
            evidence_ids=(evidence.evidence_id,),
            claimed_confidence=0.55,
            tags=audit_input.tags,
        )
        audit = ClaimAudit(
            audit_id=f"audit-{claim_hash[:16]}",
            claim_id=claim.claim_id,
            verdict=ClaimVerdict.PARTIAL,
            confidence=0.58,
            supporting_evidence_ids=(evidence.evidence_id,),
            independent_evidence_ids=(),
            missing_evidence=(
                "Independent corroboration is required before a supported verdict.",
                "A measured experiment is required before operational adoption.",
            ),
            conflicts=(),
            audited_at=created_at,
            rationale=(
                "The selected excerpt supports that the source made the statement.",
                "A single transcript is not independent proof of effectiveness.",
            ),
        )
        draft_payload = {
            "title": audit_input.title,
            "statement": audit_input.candidate_statement,
            "applicability": audit_input.applicability,
            "risks": audit_input.risks,
            "evidence_ids": (evidence.evidence_id,),
            "audit_id": audit.audit_id,
            "experiment_id": "experiment-not-started",
            "status": KnowledgeDraftStatus.PENDING_AUDIT,
            "created_at": created_at,
            "schema_version": "1.0",
        }
        draft = KnowledgeCardDraft(
            card_id=f"knowledge-{claim_hash[:16]}",
            content_sha256=content_sha256(draft_payload),
            **draft_payload,
        )
        return TranscriptAuditResult(
            source=source,
            evidence=evidence,
            claim=claim,
            audit=audit,
            knowledge_draft=draft,
        )
