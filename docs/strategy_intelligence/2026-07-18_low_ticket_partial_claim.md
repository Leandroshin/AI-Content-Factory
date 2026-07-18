# Primeira Alegacao Low-Ticket Auditada

**Status:** `AUDITORIA PARCIAL - FALTA CORROBORACAO`
**Data do registro:** 2026-07-18
**Gate:** `TranscriptEvidenceAuditWorkflow`
**Decisao humana:** Leandro autorizou somente o registro controlado da Alegacao A nesta missao.

## Fonte vinculada

- Transcricao: `docs/external_llm_inbox/incoming/2026-07-17_low_ticket_do_zero_a_escala.txt`
- Fonte declarada na transcricao: `https://www.youtube.com/watch/46s3h_yyZWQ`
- SHA-256 esperado e confirmado: `8132b2619e04c0fe4eb8593318784b693bb044d2770f5041a81393dcb4aa319d`
- Localizador: `00:13:25.279-00:13:51.720`

## Alegacao registrada

> Uma entrega inicial simples pode reduzir o tempo e o custo de preparação antes de validar a demanda, dependendo do tipo de produto e do mercado.

## Trecho exato conferido

```text
00:13:25.279 comprar. Então eu precisava ser rápido.
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
00:13:51.720 pouco dinheiro.
```

## Contratos oficiais gerados

Os identificadores abaixo sao produzidos deterministicamente pelo gate e verificados por `demo_low_ticket_partial_claim.py`:

- `SourceArtifact`: `source-26928b900b9a11b3`
- `EvidenceRef`: `evidence-transcript-3d3b7a840152ae15`
- `ClaimRecord`: `claim-811fe1d3ec7b6313`
- `ClaimAudit`: `audit-811fe1d3ec7b6313`
- `KnowledgeCardDraft`: `knowledge-811fe1d3ec7b6313`

## Limites da evidencia

O trecho sustenta que o autor:

- preferiu velocidade a uma entrega completa naquele caso;
- escolheu preparar uma entrega simples antes de investir em aplicativo ou area de membros;
- declarou que essa escolha limitaria sua perda de tempo e dinheiro se a oferta nao vendesse.

O trecho nao sustenta que:

- uma entrega simples sempre reduz desperdicio;
- essa estrategia causa vendas ou melhora conversao;
- a abordagem e superior em todo produto, mercado ou canal;
- os resultados financeiros declarados em outras partes da fonte foram verificados.

Faltam corroboracao independente e experimento medido antes de qualquer conclusao operacional.

## Estado dos portoes

| Portao | Estado |
|---|---|
| Auditoria | `PARTIAL`, confianca `0.58` |
| Evidencia independente | Ausente |
| Knowledge Card | `PENDING_AUDIT`, candidato nao promovido |
| Experimento | `experiment-not-started` |
| Provider externo | Nao chamado; custo `USD 0.00` |
| Organizational Memory | Nao promovida |
| Funcionarios | Nenhuma instrucao alterada |
| Publicacao | Nao tentada |

## Reproducao

```powershell
python demo_low_ticket_partial_claim.py
```

Qualquer mudanca na transcricao invalida o hash esperado e faz o gate recusar a auditoria antiga.
