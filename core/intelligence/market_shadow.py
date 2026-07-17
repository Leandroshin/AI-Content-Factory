"""No-spend shadow workflow from owner evidence to a pending knowledge draft."""

from __future__ import annotations

import time

from core.approval import ApprovalRuntime
from core.intelligence.approval_binding import request_bound_approval
from core.intelligence.canonical import canonical_value, content_sha256, raw_sha256
from core.intelligence.contracts import (
    ClaimAudit,
    ClaimRecord,
    ClaimVerdict,
    EvidenceKind,
    EvidenceRef,
    ExperimentSpec,
    KnowledgeCardDraft,
    KnowledgeDraftStatus,
    MarketIntelligenceShadowResult,
    ShadowSourceInput,
    SourceArtifact,
)


class MarketIntelligenceShadowWorkflow:
    """Build a reviewable hypothesis without providers, memory, or publishing."""

    def __init__(self, approvals: ApprovalRuntime) -> None:
        self._approvals = approvals

    def run(self, source_input: ShadowSourceInput, *, now: float | None = None) -> MarketIntelligenceShadowResult:
        created_at = time.time() if now is None else now
        transcript_hash = raw_sha256(source_input.transcript_text)
        visual_hash = raw_sha256(source_input.visual_content)
        source_hash = content_sha256(
            {
                "source_uri": source_input.source_uri,
                "transcript_sha256": transcript_hash,
                "visual_sha256": visual_hash,
            }
        )
        source_id = f"source-{source_hash[:16]}"
        transcript = EvidenceRef(
            evidence_id=f"evidence-transcript-{transcript_hash[:16]}",
            kind=EvidenceKind.TRANSCRIPT,
            source_uri=source_input.source_uri,
            locator=source_input.transcript_locator,
            content_sha256=transcript_hash,
            collected_at=created_at,
            confidence=0.82,
            notes=("Owner-provided transcript; creator claims remain unverified.",),
        )
        visual = EvidenceRef(
            evidence_id=f"evidence-visual-{visual_hash[:16]}",
            kind=EvidenceKind.VISUAL,
            source_uri=source_input.visual_uri,
            locator=source_input.visual_locator,
            content_sha256=visual_hash,
            collected_at=created_at,
            confidence=0.72,
            notes=("Visual evidence from the same presentation is not independent corroboration.",),
        )
        evidence = (transcript, visual)
        source = SourceArtifact(
            source_id=source_id,
            title=source_input.title,
            source_uri=source_input.source_uri,
            creator=source_input.creator,
            collected_at=created_at,
            content_sha256=source_hash,
            evidence_ids=tuple(item.evidence_id for item in evidence),
        )
        claim_hash = content_sha256({"source_id": source_id, "text": source_input.claim_text})
        claim = ClaimRecord(
            claim_id=f"claim-{claim_hash[:16]}",
            source_id=source_id,
            text=source_input.claim_text,
            evidence_ids=source.evidence_ids,
            claimed_confidence=0.55,
            tags=source_input.tags,
        )
        audit = self._audit_claim(claim, evidence, created_at)
        experiment = ExperimentSpec(
            experiment_id=f"experiment-{claim_hash[:16]}",
            claim_id=claim.claim_id,
            title="Compare evidence-led offer selection with the current manual baseline",
            hypothesis=source_input.hypothesis,
            baseline="Manual product selection without a reconciled evidence scorecard.",
            variant="Offline scorecard using source freshness, traffic direction, commission, risk, and evidence quality.",
            primary_metric="decision_quality_score",
            success_threshold="Variant must improve decision quality without increasing false confidence or cost.",
            stop_conditions=(
                "Stop if source provenance is missing.",
                "Stop if any marketing claim is treated as measured fact.",
                "Stop if estimated provider cost becomes greater than USD 0.00.",
                "Stop if owner approval does not match the exact payload hash.",
            ),
            evidence_ids=claim.evidence_ids,
        )
        draft_payload = {
            "title": "Evidence-led offer selection is a testable hypothesis",
            "statement": (
                "Traffic direction, commission, offer age, and evidence quality may improve product selection, "
                "but the source alone does not prove profitability."
            ),
            "applicability": "Internal, offline comparison before Offer Intelligence or paid traffic decisions.",
            "risks": (
                "Creator revenue screenshots are not independently verified.",
                "Traffic estimates can be stale or vendor-derived.",
                "A profitable-looking commission can still fail after ad cost, refunds, and geography.",
            ),
            "evidence_ids": claim.evidence_ids,
            "audit_id": audit.audit_id,
            "experiment_id": experiment.experiment_id,
            "status": KnowledgeDraftStatus.PENDING_EXPERIMENT,
            "created_at": created_at,
            "schema_version": "1.0",
        }
        draft = KnowledgeCardDraft(
            card_id=f"knowledge-{claim_hash[:16]}",
            content_sha256=content_sha256(draft_payload),
            **draft_payload,
        )
        review_payload = {
            "action": "approve_offline_experiment",
            "source": canonical_value(source),
            "claim": canonical_value(claim),
            "audit": canonical_value(audit),
            "experiment": canonical_value(experiment),
            "knowledge_draft": canonical_value(draft),
            "memory_promotion_allowed": False,
            "provider_calls_allowed": False,
            "publication_allowed": False,
        }
        approval = request_bound_approval(
            self._approvals,
            title="Revisar experimento interno de Market Intelligence",
            preview_text=(
                f"{claim.text}\n\nVeredito: {audit.verdict.value}. "
                "A aprovação libera somente um experimento offline e não promove conhecimento."
            ),
            payload=review_payload,
            requester="MarketIntelligenceShadowWorkflow",
            subject_type="offline_learning_experiment",
            subject_id=experiment.experiment_id,
            risk_level="medium",
        )
        return MarketIntelligenceShadowResult(
            source=source,
            evidence=evidence,
            claim=claim,
            audit=audit,
            experiment=experiment,
            knowledge_draft=draft,
            approval=approval,
        )

    @staticmethod
    def review_payload(result: MarketIntelligenceShadowResult) -> dict[str, object]:
        return {
            "action": "approve_offline_experiment",
            "source": canonical_value(result.source),
            "claim": canonical_value(result.claim),
            "audit": canonical_value(result.audit),
            "experiment": canonical_value(result.experiment),
            "knowledge_draft": canonical_value(result.knowledge_draft),
            "memory_promotion_allowed": False,
            "provider_calls_allowed": False,
            "publication_allowed": False,
        }

    @staticmethod
    def _audit_claim(claim: ClaimRecord, evidence: tuple[EvidenceRef, ...], audited_at: float) -> ClaimAudit:
        independent = tuple(item.evidence_id for item in evidence if item.independent_source)
        audit_hash = content_sha256({"claim_id": claim.claim_id, "evidence_ids": claim.evidence_ids})
        return ClaimAudit(
            audit_id=f"audit-{audit_hash[:16]}",
            claim_id=claim.claim_id,
            verdict=ClaimVerdict.PARTIAL,
            confidence=0.48,
            supporting_evidence_ids=claim.evidence_ids,
            independent_evidence_ids=independent,
            missing_evidence=(
                "Independent source corroborating traffic and sales claims.",
                "Measured baseline-versus-variant experiment result.",
                "Reconciled commission, refund, geography, and acquisition-cost data.",
            ),
            conflicts=(),
            audited_at=audited_at,
            rationale=(
                "Transcript and screenshots document what the creator presented.",
                "They do not independently prove profitability or causal performance.",
                "The pattern is suitable for a zero-cost experiment, not organizational memory.",
            ),
        )
