"""Regression proof for the first audited low-ticket claim."""

from dataclasses import replace
from pathlib import Path

from core.intelligence import (
    ClaimVerdict,
    KnowledgeDraftStatus,
    TranscriptClaimInput,
    TranscriptEvidenceAuditWorkflow,
    raw_sha256,
)


TRANSCRIPT_PATH = Path(
    "docs/external_llm_inbox/incoming/2026-07-17_low_ticket_do_zero_a_escala.txt"
)
EXPECTED_TRANSCRIPT_SHA256 = "8132b2619e04c0fe4eb8593318784b693bb044d2770f5041a81393dcb4aa319d"
CLAIM_TEXT = (
    "Uma entrega inicial simples pode reduzir o tempo e o custo de preparação antes de "
    "validar a demanda, dependendo do tipo de produto e do mercado."
)
EVIDENCE_EXCERPT = """00:13:25.279 comprar. Então eu precisava ser rápido.
00:13:27.600 Se eu passasse semanas criando um
00:13:29.279 aplicativo, uma área de membros completa
00:13:31.720 ou uma entrega perfeita, eu poderia
00:13:33.720 descobrir depois que a oferta nem
00:13:35.279 vendia. Por isso, o caminho mais
00:13:37.120 inteligente era montar uma entrega
00:13:39.240 simples, criar a página, criar os
00:13:41.560 criativos e subir os testes. Subir o
00:13:44.279 teste e deixar o mercado responder. Se
00:13:47.000 vendesse, aí sim eu melhoraria. Se não
00:13:49.519 vendesse, eu teria perdido pouco tempo e
00:13:51.720 pouco dinheiro."""


def build_audit_input(transcript: str) -> TranscriptClaimInput:
    return TranscriptClaimInput(
        title="Low-ticket: entrega inicial simples antes da validacao",
        source_uri="https://www.youtube.com/watch/46s3h_yyZWQ",
        creator="Guia Manuel (identidade declarada na fonte; nao confirmada)",
        transcript_text=transcript,
        expected_transcript_sha256=EXPECTED_TRANSCRIPT_SHA256,
        evidence_excerpt=EVIDENCE_EXCERPT,
        evidence_locator="00:13:25.279-00:13:51.720",
        claim_text=CLAIM_TEXT,
        candidate_statement=CLAIM_TEXT,
        applicability=(
            "Hipotese condicional para comparar a preparacao inicial de uma oferta simples "
            "com uma entrega mais sofisticada; nao autoriza adocao operacional."
        ),
        risks=(
            "A fonte descreve apenas a escolha e a experiencia do proprio autor.",
            "Nao existe corroboracao independente nem medicao causal.",
            "O resultado pode variar por produto, mercado, oferta, canal e execucao.",
        ),
        tags=("low_ticket", "validation", "conditional_claim"),
    )


def run_demo() -> int:
    assertions = 0
    transcript = TRANSCRIPT_PATH.read_bytes().decode("utf-8")
    assert raw_sha256(transcript) == EXPECTED_TRANSCRIPT_SHA256
    assertions += 1

    audit_input = build_audit_input(transcript)
    result = TranscriptEvidenceAuditWorkflow().run(audit_input, now=1_784_352_000.0)

    assert result.source.source_id == "source-26928b900b9a11b3"
    assertions += 1
    assert result.evidence.evidence_id == "evidence-transcript-3d3b7a840152ae15"
    assertions += 1
    assert result.claim.claim_id == "claim-811fe1d3ec7b6313"
    assertions += 1
    assert result.audit.audit_id == "audit-811fe1d3ec7b6313"
    assertions += 1
    assert result.knowledge_draft.card_id == "knowledge-811fe1d3ec7b6313"
    assertions += 1
    assert result.source.source_uri == audit_input.source_uri
    assertions += 1
    assert result.source.content_sha256 and len(result.source.content_sha256) == 64
    assertions += 1
    assert result.evidence.locator == "00:13:25.279-00:13:51.720"
    assertions += 1
    assert result.evidence.content_sha256 == raw_sha256(EVIDENCE_EXCERPT)
    assertions += 1
    assert not result.evidence.independent_source
    assertions += 1
    assert result.claim.text == CLAIM_TEXT
    assertions += 1
    assert result.claim.evidence_ids == (result.evidence.evidence_id,)
    assertions += 1
    assert result.audit.verdict == ClaimVerdict.PARTIAL
    assertions += 1
    assert result.audit.confidence == 0.58
    assertions += 1
    assert result.audit.independent_evidence_ids == ()
    assertions += 1
    assert "Independent corroboration is required before a supported verdict." in result.audit.missing_evidence
    assertions += 1
    assert result.knowledge_draft.status == KnowledgeDraftStatus.PENDING_AUDIT
    assertions += 1
    assert result.knowledge_draft.experiment_id == "experiment-not-started"
    assertions += 1
    assert not result.provider_called and result.provider_cost == 0.0
    assertions += 2
    assert not result.experiment_started
    assertions += 1
    assert not result.memory_promoted
    assertions += 1
    assert not result.publication_attempted
    assertions += 1

    changed_transcript = transcript + "\nconteudo alterado"
    try:
        TranscriptEvidenceAuditWorkflow().run(
            replace(audit_input, transcript_text=changed_transcript)
        )
    except ValueError:
        assertions += 1
    else:
        raise AssertionError("A changed transcript retained an obsolete audit")

    print(f"SourceArtifact: {result.source.source_id}")
    print(f"EvidenceRef: {result.evidence.evidence_id}")
    print(f"ClaimRecord: {result.claim.claim_id}")
    print(f"ClaimAudit: {result.audit.audit_id}")
    print(f"KnowledgeCardDraft: {result.knowledge_draft.card_id} ({result.knowledge_draft.status})")
    print(f"All {assertions} assertions passed")
    return assertions


if __name__ == "__main__":
    run_demo()
