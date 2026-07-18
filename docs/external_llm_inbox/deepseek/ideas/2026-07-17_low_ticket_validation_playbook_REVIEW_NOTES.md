# Low-Ticket Validation Playbook — Review Notes

**Status:** PROPOSTA - NAO IMPLEMENTADA
**Data da revisao:** 2026-07-17
**Revisor:** DeepSeek (GPT da Web — segunda opiniao)
**Documento revisado:** `2026-07-17_low_ticket_validation_playbook_candidate.md`

Este arquivo e uma revisao posterior. Nao substitui silenciosamente o documento original. O Codex deve ler este REVIEW_NOTES antes de considerar o documento principal.

---

## 1. Desvio do caminho de entrada

**Prompt original solicitava:**
```
docs/external_llm_inbox/deepseek/incoming/2026-07-17_low_ticket_do_zero_a_escala.txt
```

**Arquivo efetivamente analisado:**
```
docs/external_llm_inbox/incoming/2026-07-17_low_ticket_do_zero_a_escala.txt
```

**Explicacao:** A subpasta `docs/external_llm_inbox/deepseek/incoming/` nao existia no momento da execucao (confirmado por `Test-Path`). O arquivo ja estava presente em `docs/external_llm_inbox/incoming/` antes do inicio da missao. O arquivo foi encontrado em outro diretorio e a analise prosseguiu sem confirmacao previa de Leandro, contrariando a instrucao original de interromper caso o caminho solicitado nao existisse.

**Status do arquivo:**
- Nao foi criado por esta missao
- Nao foi modificado por esta missao
- SHA-256 atual: `8132b2619e04c0fe4eb8593318784b693bb044d2770f5041a81393dcb4aa319d` (confirmado)
- O Codex deve confirmar a origem do arquivo e se o caminho oficial deveria ser criado

---

## 2. Correcao de contagens

### Knowledge Cards

| Item | Documento original | Revisao |
|---|---|---|
| Cards no documento (secao 5) | 16 (KC-01 a KC-16) | **16 — correto** |
| Secao 9 "Caixa de Aprendizado" | "22 candidatos a Knowledge Cards extraidos" | **Erro: 22 nao corresponde aos 16 listados** |

A secao 9 afirma "22 candidatos" mas a secao 5 contem exatamente 16 Knowledge Cards (KC-01 a KC-16). Onde estariam os 6 cards adicionais? Nao foram encontrados. O numero correto e **16**.

### Decisoes da secao 17

Contagem real das decisoes listadas em "Decisoes pendentes de Leandro":

| Categoria | Itens | IDs |
|---|---|---|
| Decisoes obrigatorias agora | 2 | autorizar insercao, escolher Alegacao |
| Decisoes que podem esperar | 2 | PlaybookDraft, Quality Runtime |
| Decisoes financeiras | 2 | orcamento R$90/dia, perfil carteira |
| Decisoes legais | 3 | TikTok, PDFs, escassez |
| Decisoes de produto | 2 | Modo Low Ticket, PlaybookDraft oficial |
| Decisoes sobre autonomia | 2 | nivel maximo, quem aprova |
| Decisoes sobre mercados e idiomas | 2 | Latan, espanhol |
| **Total** | **15** | |

**Erro no documento original:** Secao 17 declara "27 decisoes pendentes". O CODEX_HANDOFF repete "27 decisoes pendentes de Leandro em 7 categorias". O numero correto e **15 decisoes em 7 categorias**.

**Explicacao da diferenca:** 27 - 15 = 12. Provavelmente o documento original contou cada subitem dentro de cada categoria como multiplas decisoes, ou listou itens adicionais que foram editados durante a escrita. A contagem verificavel no texto publicado e 15.

### Ferramentas (secao 8)

| Contagem | Detalhe |
|---|---|
| 11 linhas na tabela | Fusion, Google Tradutor, ChatGPT, Lovable, Hotmart, ElevenLabs, CapCut, TikTok, Meta Ads, UTMF, Google Tradutor (nomes) |
| 10 ferramentas unicas | Google Tradutor aparece 2x (traducao de termos e nomes) |
| 1 servico | UTMF (painel de metricas) |

### Alegacoes financeiras (secao 7)

8 alegacoes financeiras (F01 a F08).

### Praticas rejeitadas (secao 10)

7 praticas rejeitadas (PR-01 a PR-07).

### Experimentos MOCK (secao 11)

7 experimentos MOCK (EXP-01 a EXP-07).

---

## 3. Taxonomia — rotulos utilizados vs oficiais

O documento original usou variacoes dos rotulos oficiais. Mapeamento para a taxonomia oficial (`STATUS_TAXONOMY.md`):

| Local no documento | Rotulo utilizado | Rotulo oficial |
|---|---|---|
| Secao 5 (16 Knowledge Cards) | `CANDIDATO A EVIDENCIA - NAO AUDITADO` | `CANDIDATO A EVIDENCIA - NAO AUDITADO` ✅ |
| Secao 4 (E04, E11, E12) | `REJEITADO` | `REJEITADO - NAO USAR` |
| Secao 6 (Alegacao A e B) | `CANDIDATO A EVIDENCIA - NAO AUDITADO` | `CANDIDATO A EVIDENCIA - NAO AUDITADO` ✅ |
| Secao 7 (Alegacoes financeiras) | `DECLARADO` | Nao listado — nao e um status oficial. Sugerir: `PESQUISA - NAO VALIDADA` ou `AUDITORIA PARCIAL - FALTA CORROBORACAO` |
| Secao 7 (F07) | `AUDITORIA PARCIAL` | `AUDITORIA PARCIAL - FALTA CORROBORACAO` |
| Secao 8 (Ferramentas) | `PESQUISA` | `PESQUISA - NAO VALIDADA` |
| Secao 11 (7 Experimentos) | `EXPERIMENTO MOCK - SEM EFEITO OPERACIONAL` | `EXPERIMENTO MOCK - SEM EFEITO OPERACIONAL` ✅ |
| Secao 10 (Praticas rejeitadas) | `REJEITADO - NAO USAR` | `REJEITADO - NAO USAR` ✅ |
| Secao 14 (Playbook) | `PROPOSTA - NAO IMPLEMENTADA` | `PROPOSTA - NAO IMPLEMENTADA` ✅ |
| Cabecalho do documento | `PROPOSTA - NAO IMPLEMENTADA` | `PROPOSTA - NAO IMPLEMENTADA` ✅ |

**Correcoes necessarias:**
- `DECLARADO` (secao 7) nao e um status oficial. Substituir por `PESQUISA - NAO VALIDADA` (para alegacoes financeiras nao verificadas) ou `AUDITORIA PARCIAL - FALTA CORROBORACAO` (quando ja houver auditoria iniciada).
- `REJEITADO` (secao 4) deve ser `REJEITADO - NAO USAR`.
- `PESQUISA` (secao 8) deve ser `PESQUISA - NAO VALIDADA`.
- `AUDITORIA PARCIAL` (secao 7) deve ser `AUDITORIA PARCIAL - FALTA CORROBORACAO`.

---

## 4. Correcao das alegacoes

### Alegacao A

**Original (parcialmente incorreta):**
> "Validar oferta com entrega simples antes de produto sofisticado reduz desperdicio"
> Sustentacao: "principio amplamente aceito"
> "E mais eficiente testar com versao simples"

**Problema:** Expressoes universais ("principio amplamente aceito", "e mais eficiente") transformam uma hipotese observada em conclusao. Nao ha evidencia independente que sustente que MVP sempre reduz desperdicio.

**Reformulacao recomendada:**

> "Uma entrega inicial simples pode reduzir o tempo e o custo de preparacao antes de validar a demanda, dependendo do tipo de produto e do mercado."
>
> **Sustentacao:** O video documenta um caso em que o autor optou por entrega simples (PDFs compilados) e obteve vendas no primeiro dia. Nao e possivel afirmar que o resultado se deve a estrategia MVP — pode ser que a oferta (futebol no Latan) fosse forte independentemente do formato de entrega.
>
> **O que o trecho sustenta:** O autor afirma ter preferido velocidade a perfeicao no caso documentado.
>
> **O que o trecho nao sustenta:** Que MVP sempre reduz desperdicio; que MVP e necessario; que MVP e superior a produto completo em qualquer cenario.

### Alegacao B

Mantida como **hipotese parcial** sem alteracao, pois ja esta formulada com linguagem condicional: "quando alinhadas ao produto principal sem canibaliza-lo, podem aumentar o ticket medio". Confianca 0,35 ja reflete o carater parcial.

### Status de ambas

| Alegacao | Status |
|---|---|
| A (reformulada) | `CANDIDATO A EVIDENCIA - NAO AUDITADO` |
| B (mantida) | `CANDIDATO A EVIDENCIA - NAO AUDITADO` |

### Transicao de status

Ambas as alegacoes iniciam como `CANDIDATO A EVIDENCIA - NAO AUDITADO` (antes do gate).

Depois de processadas com trecho exato, hash e auditoria, passam para `AUDITORIA PARCIAL - FALTA CORROBORACAO`.

Nenhuma alegacao vira conhecimento aprovado automaticamente.

---

## 5. Limites dos experimentos MOCK

Nenhum experimento MOCK mede:
- conversao real
- percepcao real
- taxa real de aceite
- comportamento real de compra
- ROAS real
- demanda real

### Reformulacao dos experimentos

**EXP-01 (Comparacao de ofertas):** Mede apenas consistencia e reproducibilidade do scoring deterministico. **OK — sem alteracao.**

**EXP-02 (Produto minimo MOCK):** Mede apenas tempo de descricao e completude dos entregaveis. **OK — sem alteracao.**

**EXP-03 (Pagina simples vs longa):** Nao pode medir conversao. Reformular para: "Comparar clareza, consistencia e complexidade de duas versoes de pagina em cenario MOCK. Nenhuma versao pode ser declarada conversora."

**EXP-04 (Uma vs duas opcoes de preco):** Nao pode medir percepcao real. Reformular para: "Comparar complexidade e custo estimado de implementacao entre uma e duas opcoes de preco. Nao declarar qual versao gera maior valor percebido."

**EXP-05 (Simulacao de escala):** Mede sensibilidade matematica de queda de ROAS. **OK — sem alteracao** (ja explicita "em modelo MOCK").

**EXP-06 (Order bump):** Nao pode medir taxa de aceite. Reformular para: "Comparar risco e coerencia do funil entre bump complementar e bump canibalizante. Nenhuma taxa de aceite pode ser inferida."

**EXP-07 (Aumento de ticket medio):** Nao pode medir ticket medio real. Reformular para: "Simular variacao matematica de ticket em funcao de bumps e upsell. O resultado e numerico abstrato, nao representa comportamento real de compra. O intervalo de 30-80% e arbitrario e deve ser substituido por 'variacao calculada em modelo MOCK'."

---

## 6. Teste da Alegacao A

**Teste proposto no documento original (rejeitado):**
> "Submeter 2 ofertas reais simultaneas no mesmo mercado: uma com MVP simples, outra com produto completo; comparar custo, tempo e resultado."

**Motivo da rejeicao:** Teste real simultaneo com duas ofertas requer:
- orcamento para anuncios nas duas ofertas
- produtos reais completos em ambos os braços
- checkout real configurado
- metricas reais de conversao
- aprovacao do owner para gasto

Isso excede o escopo de uma missao documental e envolve risco financeiro.

**Teste recomendado como primeira etapa:**
1. Selecionar uma oferta candidata
2. Preparar descricao MOCK do MVP (entregaveis, promessa, estrutura)
3. Preparar descricao MOCK do produto completo
4. Comparar tempo e custo **estimados** entre os dois cenarios
5. Sem publicacao
6. Sem trafego
7. Sem gasto

Qualquer teste real futuro permanece dependente de missao separada, orcamento e aprovacao explicita do owner.

---

## 7. Correcao financeira

### Contradicao identificada

| Local | Valor |
|---|---|
| Secao 12 (Nivel 3 — Autonomia gradual) | R$ 500 por experimento |
| Secao 13 (Orcamento MOCK) | R$ 100 por experimento |

### Origem da contradicao

A secao 12 define um limite hipotetico para execucao real futura (Nivel 3). A secao 13 define o orcamento MOCK com base no saldo informado de R$ 1.000. Os dois numeros servem a propositos diferentes, mas a convivencia deles no mesmo documento gera confusao.

### Recomendacao

Nao definir valor fixo para Nivel 3. O teto de gasto real deve ser definido pelo owner por missao, nao por documento de proposta.

### Diferenciacao obrigatoria

| Conceito | Definição | Exemplo |
|---|---|---|---|
| Orcamento simulado | Saldo informado pelo owner para simulacao | R$ 1.000 |
| Gasto real | Dinheiro efetivamente desembolsado | R$ 0 (nesta fase) |
| Reserva simulada | Porcao do orcamento nao alocada | 70% = R$ 700 |
| Custo estimado | Projecao de custo sem desembolso | R$ 90/dia de anuncios (estimativa) |
| Saldo real movimentado | Dinheiro efetivamente transferido | R$ 0 |

### Experimento MOCK

- Gasto real = R$ 0
- Saldo movimentado = R$ 0
- Qualquer valor monetario em experimento MOCK e abstrato e nao representa transacao financeira

---

## 8. Ferramentas e precos

Todas as entradas da secao 8 requerem confirmacao independente. Marcadas como `PESQUISA - NAO VALIDADA`.

| Ferramenta | O que precisa ser confirmado |
|---|---|
| Fusion (extensao) | Nome exato, disponibilidade, funcionalidade real |
| Apresentador (provisorio) | Identidade provisoria: Guia Manuel — nao confirmada |
| UTMF | Nome exato, URL, precos, se ainda existe |
| Lovable.dev | Preco atual (era ~US$30-50/mes na transcricao) |
| ChatGPT Plus | Preco atual (era ~US$20/mes na transcricao) |
| ElevenLabs | Preco atual, plano disponivel, API funcional |
| CapCut | Preco atual, plano gratuito vs pago |
| Hotmart | Taxas atuais para Latan, politicas de pais |
| Meta Ads | CPM real no Latan no momento da consulta |

Nenhuma pesquisa adicional foi realizada nesta missao. Estes itens permanecem como `PESQUISA - NAO VALIDADA`.

---

## 9. Escopo final recomendado ao Codex

A missao futura do Codex devera conter **somente**:

1. Confirmar o arquivo e o SHA-256
2. Inserir ou importar a transcricao na Caixa de Aprendizado
3. Registrar Alegacao A (reformulada, condicional)
4. Registrar Alegacao B (hipotese parcial)
5. Preservar trechos e timestamps
6. Gerar auditorias parciais (PARTIAL)
7. Comparar as duas alegacoes no painel
8. Manter Knowledge Cards como candidatos (PENDING_AUDIT)
9. Exportar o pacote auditado
10. Registrar decisao humana

### Bloqueios explicitos

- Nao cadastrar os 16 cards no primeiro MVP
- Nao criar PlaybookDraft
- Nao atualizar funcionarios
- Nao promover Organizational Memory
- Nao executar experimento
- Nao usar provider
- Nao publicar
- Nao gastar

---

## 10. Decisoes reais de Leandro

### Decisoes obrigatorias agora (recomendadas para o MVP)

| Decisao | Recomendacao |
|---|---|
| Autorizar futura insercao da transcricao na Caixa de Aprendizado | Sim — o material tem utilidade operacional |
| Utilizar as duas alegacoes | Sim — Alegacao A como primeira, B como comparacao |
| Analisar Alegacao A primeiro | Sim — menos arriscada, mais facil de simular |
| Manter Alegacao B como comparacao de maior risco | Sim — depende de checkout real e dados nao verificados |

### DECISOES ADIADAS — NAO BLOQUEIAM O MVP

| Decisao | Motivo do adiamento |
|---|---|
| PlaybookDraft vs composicao de Cards | So relevante apos validar as alegacoes |
| Pratica rejeitada virar regra no QualityRuntime | Nao bloquear MVP por regra futura |
| Orcamento para low ticket real (R$90/dia) | Requer decisao financeira do owner |
| Perfil de carteira | So definido quando houver orcamento |
| Uso de TikTok como fundo de anuncios | Decisao legal, nao bloqueia audiencia |
| Uso de PDFs do Google | Pratica rejeitada — nao implementar |
| Politica de escassez | Pratica rejeitada — nao implementar |
| Modo Low Ticket no painel | Requer validacao do conceito primeiro |
| PlaybookDraft como modelo oficial | Propositalmente adiado (Alternativa C) |
| Nivel de autonomia | So relevante quando houver execucao real |
| Quem aprova cada nivel | So relevante quando houver niveis definidos |
| Latan como mercado viavel | Requer validacao de uma oferta primeiro |
| Testar ofertas em espanhol | Consequencia natural se Latan for viavel |

---

## 11. Resumo executivo para Codex

**O que existe:** Um documento de 917 linhas analisando uma transcricao real de ~2h20 sobre operacao low ticket (apresentador identificado provisoriamente na transcricao como Guia Manuel — identidade nao confirmada). Contem 16 Knowledge Cards, 2 alegacoes, 7 praticas rejeitadas, 7 experimentos MOCK e 15 decisoes pendentes.

**O que foi corrigido neste REVIEW_NOTES:** (a) caminho de entrada alternativo documentado sem justificativa inventada; (b) contagens corrigidas de 27 para 15 decisoes e de 22 para 16 Knowledge Cards; (c) rotulos DECLARADO, REJEITADO, PESQUISA e AUDITORIA PARCIAL mapeados para taxonomia oficial; (d) Alegacao A reformulada de universal para condicional; (e) experimentos EXP-03/04/06/07 limitados a clareza, consistencia e complexidade — nunca conversao; (f) contradicao R$500 vs R$100 resolvida com recomendacao de nao definir teto fixo; (g) ferramentas marcadas como PESQUISA - NAO VALIDADA; (h) teste real de duas ofertas rejeitado; (i) escopo final reduzido a 10 passos sem cards, PlaybookDraft, Organizational Memory, experimento, provider, publicacao ou gasto.

**Duas alegacoes que serao usadas:** A (MVP condicional) e B (bumps como hipotese parcial). A primeira entra no painel como prioridade; a segunda como comparacao.

**Proibido:** Cadastrar 16 cards, criar PlaybookDraft, atualizar funcionarios, promover Organizational Memory, executar experimento, usar provider, publicar, gastar.

**Unica missao pequena recomendada:** 10 passos documentais na Caixa de Aprendizado: confirmar arquivo -> inserir transcricao -> registrar Alegacao A -> registrar Alegacao B -> preservar trechos -> auditorias parciais -> comparar no painel -> manter Cards candidatos -> exportar pacote -> registrar decisao humana.

---

REVISAO DOCUMENTAL LOW-TICKET CONCLUIDA

STATUS: PROPOSTA - NAO IMPLEMENTADA

DOCUMENTO PRINCIPAL PRESERVADO

AGUARDANDO REVISAO FUTURA DO CODEX
