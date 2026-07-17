"""Regression proof for the zero-cost transcript evidence gate."""

from dataclasses import FrozenInstanceError, replace

from core.intelligence import (
    ClaimVerdict,
    KnowledgeDraftStatus,
    TranscriptClaimInput,
    TranscriptEvidenceAuditWorkflow,
    raw_sha256,
)


def run_demo() -> int:
    assertions = 0
    transcript = (
        "00:00 A ferramenta recebe uma descrição do sistema e organiza uma representação intermediária. "
        "00:12 Depois valida os elementos antes de renderizar o diagrama para revisão humana."
    )
    workflow = TranscriptEvidenceAuditWorkflow()
    source = TranscriptClaimInput(
        title="Archify como documentação visual candidata",
        source_uri="https://www.youtube.com/watch?v=0NelhyQwP-w",
        creator="Owner-provided source",
        transcript_text=transcript,
        expected_transcript_sha256=raw_sha256(transcript),
        evidence_excerpt=transcript,
        evidence_locator="00:00-00:20",
        claim_text="A ferramenta propõe representação intermediária, validação e renderização visual.",
        candidate_statement="Testar diagramas derivados de contratos reais para explicar fluxos da fábrica.",
        applicability="Documentação visual interna, nunca fonte de verdade operacional.",
        risks=("O diagrama pode ficar desatualizado.",),
        tags=("architecture", "visual_documentation"),
    )
    result = workflow.run(source, now=1_784_294_400.0)
    assert result.audit.verdict == ClaimVerdict.PARTIAL
    assertions += 1
    assert result.audit.independent_evidence_ids == ()
    assertions += 1
    assert result.evidence.content_sha256 == raw_sha256(transcript)
    assertions += 1
    assert result.knowledge_draft.status == KnowledgeDraftStatus.PENDING_AUDIT
    assertions += 1
    assert result.knowledge_draft.experiment_id == "experiment-not-started"
    assertions += 1
    assert not result.provider_called and result.provider_cost == 0.0
    assertions += 2
    assert not result.experiment_started and not result.memory_promoted and not result.publication_attempted
    assertions += 3
    try:
        result.claim.text = "tampered"  # type: ignore[misc]
    except FrozenInstanceError:
        assertions += 1
    else:
        raise AssertionError("Audit contracts must remain immutable")

    for bad_input in (
        replace(source, expected_transcript_sha256="0" * 64),
        replace(source, evidence_excerpt="trecho que não existe na transcrição e deve ser recusado"),
    ):
        try:
            workflow.run(bad_input)
        except ValueError:
            assertions += 1
        else:
            raise AssertionError("Tampered transcript hash was accepted")

    print(f"All {assertions} assertions passed")
    return assertions


if __name__ == "__main__":
    run_demo()
