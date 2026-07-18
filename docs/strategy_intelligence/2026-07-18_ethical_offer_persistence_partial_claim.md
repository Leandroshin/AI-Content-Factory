# Primeira Alegacao Ethical Offer Intelligence Auditada

**Status:** `AUDITORIA PARCIAL - FALTA CORROBORACAO`
**Status inicial:** `CANDIDATO A EVIDENCIA - NAO AUDITADO`
**Data do registro:** 2026-07-18
**Gate:** `TranscriptEvidenceAuditWorkflow`
**Decisao humana:** Leandro autorizou somente a alegacao corrigida de persistencia nesta missao.

## Fonte vinculada

- Transcricao: `docs/external_llm_inbox/incoming/2026-07-17_offer_mining_cloning_video.txt`
- Fonte declarada na transcricao: `https://www.youtube.com/watch/odCjvopmUlc`
- SHA-256 esperado e confirmado: `b8fe57e9b08364167d35dd931723a84c890471c0a5016847e63517ec052e4c97`
- Localizador conferido diretamente: `00:10:21.600-00:10:33.959`
- Correcao prevalente: `docs/external_llm_inbox/deepseek/ideas/2026-07-17_ethical_offer_intelligence_REVIEW_NOTES.md`

## Alegacao registrada

> Registrar anuncios e repetir a observacao em datas diferentes pode demonstrar persistencia da atividade publicitaria durante o periodo observado.

## Trecho exato conferido

```text
00:10:21.600 encontrou aqui. Vou anotar 78 anúncios
00:10:23.959 ativos no dia de hoje. Nos outros dias
00:10:26.560 que a gente for analisando aqui, a gente
00:10:28.399 vai anotando também quantos anúncios
00:10:30.040 tinha ativa, que essa é basicamente a
00:10:31.880 espionagem, né? A gente vê que a oferta
00:10:33.959 se mantém constante,
```

O trecho foi delimitado antes da interpretacao posterior do autor sobre escala. Essa interpretacao nao foi incorporada ao registro.

## Contratos oficiais gerados

Os identificadores abaixo sao produzidos deterministicamente pelo gate e verificados por `demo_ethical_offer_persistence_partial_claim.py`:

- `SourceArtifact`: `source-0a6171c7ef2f3abc`
- `EvidenceRef`: `evidence-transcript-6f26ddeb77088df7`
- `ClaimRecord`: `claim-1cdcae45db56b855`
- `ClaimAudit`: `audit-1cdcae45db56b855`
- `KnowledgeCardDraft`: `knowledge-1cdcae45db56b855`

## Limites da evidencia

O trecho sustenta que o autor:

- recomenda registrar a quantidade de anuncios observada em uma data;
- recomenda repetir a observacao em outros dias;
- usa os registros datados para observar se a atividade publicitaria se mantem durante o periodo acompanhado.

O trecho nao sustenta que:

- persistencia equivale a escala;
- muitos anuncios significam investimento elevado;
- a oferta vende ou gera receita;
- a oferta e lucrativa ou boa;
- reclamacoes comprovam vendas.

A fonte prova somente o que o autor recomendou. Faltam observacoes datadas reais, corroboracao independente e dados privados antes de afirmar qualquer resultado comercial.

## Estado dos portoes

| Portao | Estado |
|---|---|
| Auditoria | `PARTIAL`, confianca `0.58` |
| Evidencia independente | Ausente |
| Knowledge Card | `PENDING_AUDIT`, candidato nao promovido |
| Experimento | `experiment-not-started`; nenhum experimento executado |
| Regra automatica | Nao criada |
| Provider externo | Nao chamado; custo `USD 0.00` |
| Organizational Memory | Nao promovida |
| Funcionarios | Nenhuma instrucao alterada |
| Telegram | Nao chamado |
| Publicacao | Nao tentada |

## Hierarquia preservada

```text
atividade observada != persistencia
persistencia != escala
escala != venda ou receita
receita != lucro
```

## Reproducao

```powershell
python demo_ethical_offer_persistence_partial_claim.py
```

Qualquer mudanca na transcricao invalida o hash esperado e faz o gate recusar a auditoria antiga.
