"""Demonstrate one real owner source entering the no-spend shadow workflow."""

from __future__ import annotations

import dataclasses
from pathlib import Path

from core.approval import ApprovalRuntime, ApprovalStatus
from core.company.organizational_memory import OrganizationalMemoryRuntime
from core.intelligence import (
    ApprovalBindingError,
    ClaimAudit,
    ClaimVerdict,
    KnowledgeDraftStatus,
    MarketIntelligenceShadowWorkflow,
    ShadowSourceInput,
    canonical_json,
    content_sha256,
    verify_bound_approval,
)


ROOT = Path(__file__).resolve().parent
TRANSCRIPT_PATH = ROOT / "youtube" / "tactiq-free-transcript-_Tnjul-5E8s.txt"
VISUAL_PATH = ROOT / "youtube" / "Screenshot_1.jpg"
COUNT = 0

TRANSCRIPT_EXCERPT = """# COMO ESCOLHER PRODUTOS QUE ESTAO EXPLODINDO AGORA (EM 5 MINUTOS)
# https://www.youtube.com/watch/_Tnjul-5E8s
00:00:16.400 Se eu te entregasse R$ 10.000 para vender como afiliado hoje,
00:00:20.519 conseguiria encontrar bons produtos para vender?
00:01:19.799 E muito dificil ter lucro de verdade com comissoes muito baixas.
00:03:35.400 A relacao de trafego e tempo ajuda a entender quais produtos vender.
"""

VISUAL_MANIFEST = (
    "owner_visual_manifest|youtube/Screenshot_1.jpg|"
    "sha256=1000b4c460975ea95a1184e9447b27008d5dea0fe76beb00a8ac4a4114f20134|"
    "observed=creator presenting product and traffic evidence in FlowSpy"
).encode("utf-8")


def check(condition: bool, label: str) -> None:
    global COUNT
    COUNT += 1
    print(f"  [{'PASS' if condition else 'FAIL'}] {COUNT:>2}. {label}")
    if not condition:
        raise AssertionError(label)


def raises(error_type: type[BaseException], callback: object, label: str) -> None:
    try:
        callback()  # type: ignore[operator]
    except error_type:
        check(True, label)
    else:
        check(False, label)


def main() -> None:
    transcript = TRANSCRIPT_PATH.read_text(encoding="utf-8") if TRANSCRIPT_PATH.exists() else TRANSCRIPT_EXCERPT
    visual_content = VISUAL_PATH.read_bytes() if VISUAL_PATH.exists() else VISUAL_MANIFEST
    approvals = ApprovalRuntime()
    memory = OrganizationalMemoryRuntime()
    workflow = MarketIntelligenceShadowWorkflow(approvals)

    result = workflow.run(
        ShadowSourceInput(
            title="Como escolher produtos que estao explodindo agora",
            source_uri="https://www.youtube.com/watch?v=_Tnjul-5E8s",
            creator="Thiago Boeira",
            transcript_text=transcript,
            transcript_locator="00:00:00-00:18:22",
            visual_uri="owner-evidence://youtube/Screenshot_1.jpg",
            visual_content=visual_content,
            visual_locator="FlowSpy dashboard and traffic comparison shown by the creator",
            claim_text=(
                "Traffic direction, offer age, and commission can help identify affiliate products worth testing."
            ),
            hypothesis=(
                "A reconciled evidence scorecard will produce safer product decisions than intuition alone."
            ),
            tags=("affiliate", "offer_intelligence", "traffic", "flowspy"),
        ),
        now=1784246400.0,
    )

    print("\nSource and immutable evidence")
    check(result.source.source_uri.endswith("_Tnjul-5E8s"), "Uses the real owner-provided video")
    check(len(result.evidence) == 2, "Records transcript and visual evidence")
    check(all(len(item.content_sha256) == 64 for item in result.evidence), "Every evidence item has SHA-256")
    check(result.source.evidence_ids == tuple(item.evidence_id for item in result.evidence), "Source binds evidence IDs")
    raises(dataclasses.FrozenInstanceError, lambda: setattr(result.claim, "text", "changed"), "Contracts are frozen")
    check(canonical_json({"b": 2, "a": 1}) == canonical_json({"a": 1, "b": 2}), "Canonical JSON ignores key order")
    check(content_sha256({"b": 2, "a": 1}) == content_sha256({"a": 1, "b": 2}), "Content hash is deterministic")

    print("\nCautious audit and bounded experiment")
    check(result.audit.verdict == ClaimVerdict.PARTIAL, "Single creator source remains partial")
    check(not result.audit.independent_evidence_ids, "Same-video screenshot is not independent evidence")
    check(any("Independent source" in item for item in result.audit.missing_evidence), "Audit requests corroboration")
    check(any("Measured" in item for item in result.audit.missing_evidence), "Audit requests measured outcome")
    check(result.experiment.estimated_cost == 0.0, "Experiment has zero provider cost")
    check(result.experiment.owner_approval_required, "Experiment requires owner approval")
    check(result.knowledge_draft.status == KnowledgeDraftStatus.PENDING_EXPERIMENT, "Knowledge remains pending")
    check(not result.provider_called and result.provider_cost == 0.0, "No provider was called")
    check(not result.publication_attempted, "No publication was attempted")
    check(not result.memory_promoted and not memory.list_documents(), "Organizational memory remains untouched")
    raises(
        ValueError,
        lambda: ClaimAudit(
            audit_id="audit-invalid",
            claim_id=result.claim.claim_id,
            verdict=ClaimVerdict.SUPPORTED,
            confidence=0.9,
            supporting_evidence_ids=result.claim.evidence_ids,
            independent_evidence_ids=(),
            missing_evidence=(),
            conflicts=(),
            audited_at=1784246400.0,
            rationale=("Invalid optimistic audit.",),
        ),
        "Supported verdict cannot exist without independent evidence",
    )

    print("\nHash-bound human approval")
    request = approvals.require(result.approval.approval_id)
    check(request.status == ApprovalStatus.PENDING, "Real HITL request starts pending")
    check(request.subject_type == "offline_learning_experiment", "Approval scope is offline experiment only")
    check(request.metadata["promotion_allowed"] is False, "Approval explicitly blocks memory promotion")
    approvals.approve(request.approval_id, decided_by="Leandro", reason="Approved only for offline comparison.")
    expected_payload = workflow.review_payload(result)
    released = verify_bound_approval(approvals, result.approval, expected_payload)
    check(released["memory_promotion_allowed"] is False, "Approved payload still blocks memory")
    check(released["provider_calls_allowed"] is False, "Approved payload still blocks providers")
    check(released["publication_allowed"] is False, "Approved payload still blocks publication")

    altered_execution = workflow.review_payload(result)
    altered_execution["publication_allowed"] = True
    raises(
        ApprovalBindingError,
        lambda: verify_bound_approval(approvals, result.approval, altered_execution),
        "Changed execution payload is rejected after approval",
    )
    request.payload["knowledge_draft"]["title"] = "Tampered after owner review"
    raises(
        ApprovalBindingError,
        lambda: verify_bound_approval(approvals, result.approval, expected_payload),
        "Stored payload tampering is detected",
    )
    check(not memory.list_documents(), "Approval alone never promotes organizational memory")

    print(f"\nAll {COUNT} assertions passed.")


if __name__ == "__main__":
    main()
