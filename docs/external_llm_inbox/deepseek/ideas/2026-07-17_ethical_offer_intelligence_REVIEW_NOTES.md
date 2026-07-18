# Ethical Offer Intelligence — Review Notes

**Status:** PROPOSTA - NAO IMPLEMENTADA
**Data da revisao:** 2026-07-17
**Documento revisado:** `2026-07-17_ethical_offer_intelligence_candidate.md`

Estas notas corrigem conclusoes do documento original sem apaga-lo. O Codex deve ler este REVIEW_NOTES antes do documento principal.

---

## 1. Hierarquia correta de sinais

O documento original trata anuncios ativos, persistencia, reclamacoes e escala como conceitos intercambiaveis. A hierarquia real e:

```
anuncios ativos
  nao equivalem a persistencia;

persistencia
  nao equivale a escala;

escala
  nao equivale a lucratividade;

reclamacoes
  nao equivalem a vendas.
```

### Definicoes

| Conceito | O que e | Pode ser observado? | Exige dados privados? |
|---|---|---|---|
| Atividade publicitaria | Presenca de anuncios na biblioteca em uma data | Sim | Nao |
| Persistencia da atividade | Repeticao da atividade em datas diferentes | Sim | Nao |
| Intensidade aparente | Quantidade de anuncios ativos em uma data | Sim | Nao |
| Escala | Volume de investimento e alcance real | Parcialmente (estimativas) | Sim (gasto real) |
| Vendas | Transacoes concluidas | Nao | Sim |
| Lucratividade | Receita - custos | Nao | Sim |

Os sinais publicos analisados nesta fonte — anuncios, persistencia e reclamacoes — nao permitem afirmar vendas ou lucratividade.

---

## 2. Correcao de M05

**Original (secao 3, M05):**
> "Distinguir oferta mantida (escalada) de campanha temporaria"

**Correcao:**
> "Identificar persistencia da atividade publicitaria ao longo do periodo observado."

Persistencia nao comprova:
- escala
- vendas
- lucro
- investimento elevado
- qualidade

O metodo documenta observacoes repetidas. Nada alem disso.

---

## 3. Correcao de M10 e KC-06

**Original (M10 saida):**
> "Indicador de atividade (vendas altas geram mais reclamacoes)"

**Original (KC-06):**
> "Volume de reclamacoes correlaciona com volume de vendas"

**Correcao:**
> "Reclamacoes publicas sao sinais ambiguos sobre experiencia do consumidor e exposicao da oferta. Sem volume total de clientes, periodo, natureza das reclamacoes e taxa de resolucao, nao permitem inferir vendas, qualidade ou lucratividade."

M10 passa de "metodo" para "hipotese que exige corroboracao".

---

## 4. Correcao dos Knowledge Cards

**KC-03 original:**
> "Anuncios mantidos por dias/semanas sugerem operacao escalada, nao teste."

**Correcao:**
> "Observacoes repetidas demonstram persistencia da atividade publicitaria no periodo observado, nao escala."

**KC-05 original:**
> "Muitos anuncios indicam investimento em escala, mas nao provam lucro."

**Correcao:**
> "Quantidade de anuncios e um sinal de atividade e diversidade de campanhas, nao prova de investimento elevado, venda ou lucro."

**KC-06 original:**
> "Volume de reclamacoes correlaciona com volume de vendas, nao com qualidade do produto."

**Correcao:**
> "Reclamacoes publicas precisam de contexto, denominador e classificacao antes de qualquer interpretacao."

Nenhum card deve ser cadastrado no MVP.

---

## 5. Correcao da Alegacao A

**Original:**
> "Combinar diferentes fontes publicas pode produzir uma avaliacao mais confiavel da atividade de uma oferta do que utilizar somente a quantidade de anuncios ativos."

**Correcao:**
> "Combinar diferentes fontes publicas pode produzir um registro de evidencias mais completo e auditavel do que utilizar um unico sinal, desde que a origem, a independencia e a qualidade de cada fonte sejam consideradas."

Quantidade de fontes nao garante confiabilidade. Uma fonte confiavel vale mais que tres fontes duvidosas.

---

## 6. Correcao da Alegacao B

**Original:**
> "Registrar anuncios e repetir a observacao em datas diferentes pode ajudar a distinguir campanhas temporarias de ofertas mantidas por mais tempo."

**Correcao:**
> "Registrar anuncios e repetir a observacao em datas diferentes pode demonstrar persistencia da atividade publicitaria durante o periodo observado."

Nao comprova escala, vendas ou lucratividade. Priorizar Alegacao B, mas apenas como sinal de persistencia.

---

## 7. Classificacao das praticas rejeitadas

### HARD BLOCK

Praticas operacionalmente proibidas pela AI Content Factory devido a risco elevado de fraude, evasao, manipulacao, uso indevido de credenciais ou apropriacao de conteudo de terceiros. Esta classificacao e operacional e nao constitui conclusao juridica:

- PR-01: Cartao falso para gerar compra negada
- PR-02: Compra negada deliberadamente para enganar algoritmo
- PR-03: Simulacao enganosa de comprador
- PR-04: Comprar perfis de terceiros
- PR-05: Usar perfis de terceiros sem consentimento
- PR-10: Clonar paginas (ArcTrix)
- PR-11: Substituir pixel e links em pagina copiada
- PR-12: Baixar e reutilizar criativos
- PR-13: Copiar funil completo
- PR-14: Reutilizar textos, imagens ou videos
- PR-16: Copiar estrutura expressiva de concorrente
- PR-09: Contornar ou quebrar cloaking
- PR-08: Manipular algoritmo de recomendacao

### RISK REVIEW

Praticas que podem ser legítimas em outros contextos, mas sao rejeitadas para o uso descrito no video:

- PR-06: Proxy para disfarcar identidade — rejeitado para evasao, nao para privacidade legitima
- PR-07: Multilogin para manipular plataforma — rejeitado para identidade falsa, nao para gerenciamento multiplo legitimo
- PR-15: Tratamento de dados de reclamacoes publicas — rejeitado sem anonimizacao
- PR-17: Anuncios de saude sem compliance — rejeitado por risco regulatorio
- PR-18, PR-19: Alegacoes financeiras nao verificadas — rejeitado como prova

Nao usar qualificacoes juridicas categoricas sem fonte oficial.

---

## 8. Quality Runtime

**Original (secao 7):**
> "Regras de compliance baseadas em PR-01 a PR-19 | Bloquear automaticamente praticas rejeitadas"

**Correcao:**
- Hard block somente para praticas inequivocas (HARD BLOCK acima)
- Risk finding para situacoes contextuais (RISK REVIEW acima)
- Revisao humana obrigatoria para qualquer bloqueio automatico
- Nenhuma nova regra no primeiro MVP

---

## 9. Correcoes do CODEX_HANDOFF

**Linha "~440 linhas":** O documento possui 333 linhas. Corrigir para "333 linhas".

**Linha "nao violam termos de servico":** Remover. Substituir por:
> "Os metodos foram reformulados para observacao de fontes publicas. A compatibilidade com politicas e termos de cada plataforma nao foi pesquisada nesta missao e permanece `PESQUISA - NAO VALIDADA`."

Adicionar ao final:
> "Revisao posterior disponivel em: `2026-07-17_ethical_offer_intelligence_REVIEW_NOTES.md`. O Codex deve ler o REVIEW_NOTES antes do documento principal."

---

## 10. Escopo final

Manter a missao futura restrita a:

1. Confirmar arquivo e hash
2. Inserir a fonte na Caixa de Aprendizado
3. Registrar Alegacao A corrigida
4. Registrar Alegacao B corrigida
5. Preservar timestamps
6. Produzir auditorias parciais
7. Mostrar no painel a hierarquia: atividade ≠ persistencia ≠ escala ≠ lucro
8. Registrar hard blocks e riscos somente no pacote auditado
9. Exportar Markdown/JSON
10. Registrar decisao humana

### Nao integrar

- Monitoramento
- Scraping
- Ferramentas
- Cards
- Regras automaticas
- Navegador
- Provider
- Clonagem
- Publicacao
- Gasto

---

## 11. Resumo executivo para Codex

**Valor legitimo da fonte:** O video ensina metodos de pesquisa em fontes publicas (biblioteca de anuncios, Reclame Aqui, Google) que podem ser adaptados para inteligencia competitiva etica. Contudo, estas tecnicas estao entrelacadas com praticas abusivas (clonagem, cartao falso, multilogin) que devem ser rejeitadas.

**Principais erros corrigidos neste REVIEW_NOTES:** (a) hierarquia de sinais estabelecida — anuncio ativo nao e persistencia, persistencia nao e escala, escala nao e lucro; (b) M05 e M10 reformulados para eliminar conclusoes sobre escala e vendas; (c) KC-03, KC-05 e KC-06 corrigidos para refletir apenas o que a observacao publica permite afirmar; (d) Alegacao A corrigida para "registro mais completo e auditavel" em vez de "avaliacao mais confiavel"; (e) Alegacao B limitada a "persistencia da atividade publicitaria"; (f) praticas rejeitadas separadas em HARD BLOCK e RISK REVIEW; (g) Quality Runtime nao deve bloquear automaticamente todas as 19 praticas.

**Duas alegacoes finais:** A (multiplas fontes como registro auditavel, nao garantia de confiabilidade) e B (persistencia como sinal, nao escala). Priorizar B.

**Diferenca entre sinal e prova:** Tudo que se observa em fontes publicas e sinal de atividade de marketing. Nada disso e prova de venda, lucro ou qualidade.

**Praticas bloqueadas:** 13 hard blocks (clonagem, cartao falso, perfis comprados, etc.) e 6 risk review (proxy, multilogin, reclamacoes, saude sem compliance, alegacoes financeiras).

**Unica missao pequena recomendada:** 10 passos na Caixa de Aprendizado — confirmar arquivo, inserir fonte, registrar duas alegacoes corrigidas, preservar timestamps, auditorias parciais, exibir hierarquia de sinais, registrar bloqueios, exportar, registrar decisao humana. Sem cards, regras, ferramentas, provider, scraping ou gasto.

---

REVISAO DOCUMENTAL ETHICAL OFFER INTELLIGENCE CONCLUIDA

STATUS: PROPOSTA - NAO IMPLEMENTADA

DOCUMENTO PRINCIPAL PRESERVADO

AGUARDANDO REVISAO FUTURA DO CODEX
