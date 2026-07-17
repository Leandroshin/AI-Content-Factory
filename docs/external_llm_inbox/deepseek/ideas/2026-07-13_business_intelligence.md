# Idea Proposal: Business Intelligence Department

Status: PROPOSTA - NAO IMPLEMENTADA.

## One-Sentence Idea

Criar um departamento que coleta dados de performance dos canais de publicacao, calcula metricas de negocio (cliques, vendas, comissao, custo, ROI), produz relatorios periodicos e alimenta a memoria organizacional com aprendizados de o que esta funcionando.

## Why It Fits The AI Content Factory

A AGENTS.md lista explicitamente como Next Step #5: "Metricas de negocio — cliques, vendas, comissao, custo e ROI alimentando aprendizado aprovado". Hoje nao existe nenhum departamento que fecha o loop de feedback. A fabrica produz conteudo e publica (ou prepara para publicar), mas nunca mede se aquilo gerou resultado. Sem metricas, nao ha como otimizar.

## User Value

- Shin ve, em um relatorio unico, qual conteudo gerou mais cliques, qual canal converteu melhor, qual produto de afiliado teve mais saida.
- Decisoes de briefings futuros sao baseadas em dados, nao em achismo.
- O departamento pode alertar quando uma campanha esta performando abaixo do esperado (ex: ROI negativo apos 7 dias).

## Proposed Workflow

```
ReceivedTask{report_type, date_range, platforms, metrics_requested}
  -> Pipeline stages:
     1. DATA_COLLECTION           (coletar dados de cada canal — MOCK: dados sinteticos historicos)
     2. METRIC_CALCULATION        (calcular CTR, CPC, comissao total, ROI, custo por lead)
     3. TREND_ANALYSIS            (comparar com periodos anteriores, detectar tendencias)
     4. INSIGHT_EXTRACTION        (o que funcionou, o que nao funcionou, recomendacoes)
     5. REPORT_ASSEMBLY           (montar relatorio estruturado com tabelas e graficos em ASCII)
     6. ORGANIZATIONAL_MEMORY     (salvar aprendizados como OrganizationalDocument versionado)
     7. DELIVERY                  (entregar relatorio como output para o dashboard ou CEO)
```

## Required Employees

1. **BusinessIntelligenceEmployee** — herda ProductionEmployee, gerencia o pipeline de BI.
   - Hooks: `_check_reject()` rejeita se `report_type` desconhecido; `_build_pipeline()` monta BIPipeline; `_build_metrics()` expoe `total_revenue`, `total_cost`, `roi`, `best_channel`, `best_product`.

2. (Opcional) **ReportFormatter** — helper interno que gera versao texto simples e versao HTML basica do relatorio.

## Required Capabilities

Todas ja existentes:
- `DATABASE` (para ler dados de performance persistidos)
- `DOCUMENT_GENERATION` (relatorios)
- `TEXT_GENERATION` (insights em linguagem natural)
- `STORAGE` (relatorios salvos)

Nao precisa de novas capacidades no MVP. As fontes de dados sao MOCK (dados sinteticos pre-programados).

## Risks And Compliance

- **Dados financeiros**: comissao, custo e ROI sao dados sensiveis. O departamento nunca deve expor esses dados em logs publicos ou outputs nao autorizados.
- **Atribuicao correta**: atribuir uma venda a um unico canal e delicado. O MVP deve usar "ultimo clique" como modelo simples e documentar essa limitacao.
- **Privacidade**: dados de performance devem ser agregados, nunca conter informacao pessoal de compradores.
- **Aprendizado vs ruido**: uma amostra pequena pode gerar conclusoes enganosas. O relatorio deve incluir intervalo de confianca ou tamanho da amostra.

## MVP Scope

1. Pipeline deterministico MOCK com 7 stages.
2. BusinessIntelligenceEmployee com hooks padrao.
3. Snapshot `BusinessIntelligenceSnapshot` (total_reports, metrics_count, insights_generated, last_report_date).
4. Dados MOCK realistas: 3 canais (telegram, youtube, instagram), 5 produtos, 30 dias de historico sintetico com variacao.
5. Demo com 30+ assertions: coleta, calculo, tendencia, insight, relatorio, memoria organizacional.
6. Relatorio de saida estruturado com: resumo executivo, tabela por canal, tabela por produto, top 3 insights, recomendacoes.

## Later Integrations

- YouTube Analytics API (visualizacoes, tempo de exibicao, receita)
- Instagram Insights API (alcance, engajamento)
- TikTok Analytics API
- Telegram (contagem de visualizacoes, cliques em links)
- Meta Ads API (custo por clique, impressoes, conversoes)
- Hotmart/Shopee/Afiliados (comissao reportada)
- Google Analytics / Tag Manager (conversoes no site)

## Open Questions For Shin/Codex

1. As metricas devem ser puxadas sob demanda (task unica) ou em schedule fixo (diario/semanal)?
2. Os dados reais devem vir de adapters existentes (ex: MetaAdsAnalyticsAdapter) ou de uma nova integracao?
3. Shin quer visualizacao no dashboard existente ou so o relatorio como artefato?
4. O departamento deve poder "aprender" (ex: mudar recomendacao baseado em performance passada) ou apenas reportar?

## Sources

- YouTube Analytics API: https://developers.google.com/youtube/analytics
- Instagram Insights: https://developers.facebook.com/docs/instagram-api/guides/insights
- Meta Ads Insights: https://developers.facebook.com/docs/marketing-api/insights
- Hotmart API (comissoes): https://developers.hotmart.com/
