# CODEX HANDOFF — Low Ticket Validation Playbook Candidate

**Data:** 2026-07-17
**Origem:** DeepSeek no OpenCode/VS Code
**Destino:** Codex
**Status do documento-fonte:** PROPOSTA - NAO IMPLEMENTADA

---

## O que foi produzido

### Proposta principal
`docs/external_llm_inbox/deepseek/ideas/2026-07-17_low_ticket_validation_playbook_candidate.md` (917 linhas, 18 secoes)

### Fonte analisada
`docs/external_llm_inbox/incoming/2026-07-17_low_ticket_do_zero_a_escala.txt` (208.467 bytes, 4.019 linhas, SHA-256 `8132b2619e04c0fe4eb8593318784b693bb044d2770f5041a81393dcb4aa319d`)
- Video: "Eu Documentei a Criacao de um Low Ticket do Zero a Escala" (Guia Manuel, ~2h20)
- URL: https://www.youtube.com/watch/46s3h_yyZWQ

## Estrutura da proposta

| Secao | Conteudo |
|---|---|
| 1 | Identificacao, separacao fato/declarado/inferido/nao verificado |
| 2 | Resumo executivo — utilidade operacional vs alegacoes nao verificadas |
| 3 | Tratamento da transcricao — metodo de segmentacao, hash, timestamps |
| 4 | Linha do tempo dos 17 dias (24/fev a 12/mar) com 23 eventos |
| 5 | **16 Knowledge Cards candidatos** (KC-01 a KC-16), cada um com: titulo, timestamp, trecho exato (max 3 linhas), categoria, aplicabilidade, confianca, risco e 7 experimentos propostos |
| 6 | **2 alegacoes rastreaveis** com ClaimRecord, EvidenceRef e auditoria parcial |
| 7 | Auditoria cetica aplicada — 14 achados (3 fontes de erro, 4 pontos de dissonancia, 7 limites de validade) |
| 8 | Score de utilidade operacional (64/100) |
| 9 | **7 praticas rejeitadas** (PR-01 a PR-07) com justificativa |
| 10 | Riscos autorais, publicitarios e financeiros |
| 11 | Metricas reais relevantes (CPM R$10, CPC R$1,60, taxa de lead 10-20%, APR 3,63%) |
| 12 | **7 experimentos MOCK propostos** com votacao minima, orcamento, duracao e criterio de parada |
| 13 | Custos (R$90/dia anuncios + ~R$200 ferramentas/mes) |
| 14 | Alternativas de playbook — recomendacao: composicao de Knowledge Cards sem novo contrato |
| 15 | MVP recomendado ao Codex (10 passos, 7 bloqueios) |
| 16 | Criterios de aceitacao (19/21 atendidos, 2 pendentes do Codex) |
| 17 | **27 decisoes pendentes de Leandro** em 7 categorias |
| 18 | 16 pontos de revisao solicitada ao Codex |

## Praticas rejeitadas (nao copiar)

| ID | Pratica | Motivo |
|---|---|---|
| PR-01 | PDF do Google como produto vendavel | Risco autoral |
| PR-02 | Depoimento com foto do Google | Risco de imagem/privacidade |
| PR-03 | Escassez falsa ("so hoje") | Pratica enganosa |
| PR-04 | Ocultar formato de entrega (PDF como "treinamento") | Propaganda enganosa |
| PR-05 | Video do TikTok como anuncio | Licenca de uso do criador |
| PR-06 | Precos em dolar sem aviso de IOF/taxa | Transparencia |
| PR-07 | Confundir lucro com faturamento na exposicao | Metrica enganosa |

## Contratos existentes que cobrem o MVP

- `core/intelligence/transcript_audit.py`: TranscriptEvidenceAuditWorkflow — fluxo hash -> trecho -> auditoria -> Knowledge Card candidato
- `core/intelligence/contracts.py`: EvidenceRef, SourceArtifact, ClaimRecord, ClaimAudit, KnowledgeCardDraft — todos os contratos necessarios
- `core/intelligence/canonical.py`: raw_sha256() — hash disponivel

## O que o Codex deve revisar

1. **Proposta principal:** `ideas/2026-07-17_low_ticket_validation_playbook_candidate.md`
2. **Handoff atual:** `ideas/2026-07-17_low_ticket_validation_playbook_CODEX_HANDOFF.md`
3. **Compatibilidade** com TranscriptEvidenceAuditWorkflow existente
4. Se **PlaybookDraft** e necessario ou composicao de Knowledge Cards (Alternativa C) e suficiente
5. Se alguma **pratica rejeitada** merece regra automatica no QualityRuntime
6. **MVP de 10 passos** esta alinhado com a arquitetura atual?
7. **7 experimentos MOCK** — viaveis sem gasto real?
8. **Nenhum arquivo oficial foi alterado** em `core/`, `apps/`, `demos/`, `scripts/`, providers, adapters

## Decisoes que so o Codex/Shin podem tomar

- Autorizar insercao da transcricao na Caixa de Aprendizado (painel)
- Nivel de autonomia para experimentos low ticket
- Interesse em mercado Latan (espanhol)
- Orcamento disponivel (R$90/dia anuncios)
- Se alguma pratica rejeitada vira regra de QualityRuntime

## Testes

Nenhum teste foi executado (documento exclusivamente textual).
Nenhum prototipo foi criado.
Nenhum codigo foi escrito.
Nenhuma API foi chamada.
Nenhum gasto foi realizado.

## Review Notes

Revisao posterior disponivel em:
`2026-07-17_low_ticket_validation_playbook_REVIEW_NOTES.md`

O Codex deve ler o REVIEW_NOTES antes de considerar o documento principal.

## Rollback

Nao aplicavel — nenhum arquivo oficial foi alterado.
