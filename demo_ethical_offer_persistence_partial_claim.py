"""Regression proof for the first audited Ethical Offer Intelligence claim."""

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
    "docs/external_llm_inbox/incoming/2026-07-17_offer_mining_cloning_video.txt"
)
EXPECTED_TRANSCRIPT_SHA256 = "b8fe57e9b08364167d35dd931723a84c890471c0a5016847e63517ec052e4c97"
CLAIM_TEXT = (
    "Registrar anuncios e repetir a observacao em datas diferentes pode demonstrar "
    "persistencia da atividade publicitaria durante o periodo observado."
)
EVIDENCE_EXCERPT = """00:10:21.600 encontrou aqui. Vou anotar 78 anúncios
00:10:23.959 ativos no dia de hoje. Nos outros dias
00:10:26.560 que a gente for analisando aqui, a gente
00:10:28.399 vai anotando também quantos anúncios
00:10:30.040 tinha ativa, que essa é basicamente a
00:10:31.880 espionagem, né? A gente vê que a oferta
00:10:33.959 se mantém constante,"""
FORBIDDEN_INFERENCES = (
    "escala",
    "venda",
    "receita",
    "investimento elevado",
    "lucro",
    "lucratividade",
    "qualidade da oferta",
)


def build_audit_input(transcript: str) -> TranscriptClaimInput:
    return TranscriptClaimInput(
        title="Ethical Offer Intelligence: persistencia publicitaria observada",
        source_uri="https://www.youtube.com/watch/odCjvopmUlc",
        creator="Fonte fornecida pelo owner; identidade do autor nao confirmada",
        transcript_text=transcript,
        expected_transcript_sha256=EXPECTED_TRANSCRIPT_SHA256,
        evidence_excerpt=EVIDENCE_EXCERPT,
        evidence_locator="00:10:21.600-00:10:33.959",
        claim_text=CLAIM_TEXT,
        candidate_statement=CLAIM_TEXT,
        applicability=(
            "Registro datado de observacoes publicas repetidas para documentar somente a "
            "persistencia da atividade durante o periodo efetivamente observado."
        ),
        risks=(
            "Persistencia publicitaria nao comprova escala, vendas, receita ou lucro.",
            "A quantidade de anuncios nao comprova investimento elevado ou qualidade.",
            "Uma unica transcricao nao constitui corroboracao independente.",
        ),
        tags=(
            "ethical_offer_intelligence",
            "advertising_persistence",
            "conditional_claim",
        ),
    )


def run_demo() -> int:
    assertions = 0
    transcript = TRANSCRIPT_PATH.read_bytes().decode("utf-8")
    assert raw_sha256(transcript) == EXPECTED_TRANSCRIPT_SHA256
    assertions += 1

    audit_input = build_audit_input(transcript)
    result = TranscriptEvidenceAuditWorkflow().run(audit_input, now=1_784_438_400.0)

    assert result.source.source_id == "source-0a6171c7ef2f3abc"
    assertions += 1
    assert result.evidence.evidence_id == "evidence-transcript-6f26ddeb77088df7"
    assertions += 1
    assert result.claim.claim_id == "claim-1cdcae45db56b855"
    assertions += 1
    assert result.audit.audit_id == "audit-1cdcae45db56b855"
    assertions += 1
    assert result.knowledge_draft.card_id == "knowledge-1cdcae45db56b855"
    assertions += 1
    assert result.source.source_uri == audit_input.source_uri
    assertions += 1
    assert result.evidence.locator == "00:10:21.600-00:10:33.959"
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

    normalized_claim = result.claim.text.casefold()
    assert all(term not in normalized_claim for term in FORBIDDEN_INFERENCES)
    assertions += 1
    assert "persistencia" in normalized_claim and "periodo observado" in normalized_claim
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
    print(
        "KnowledgeCardDraft: "
        f"{result.knowledge_draft.card_id} ({result.knowledge_draft.status})"
    )
    print(f"All {assertions} assertions passed")
    return assertions


if __name__ == "__main__":
    run_demo()
