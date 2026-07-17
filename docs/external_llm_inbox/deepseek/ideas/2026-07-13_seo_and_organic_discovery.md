# Idea Proposal: SEO & Organic Discovery Department

Status: PROPOSTA - NAO IMPLEMENTADA.

## One-Sentence Idea

Criar um departamento que otimiza todo conteudo produzido pela fabrica para descoberta organica: pesquisa de palavras-chave, otimizacao de titulo/descricao/tags para YouTube, SEO de blog para artigo de afiliado, tags para Pinterest e praticas de descoberta multiplataforma — sem depender de anuncios pagos.

## Why It Fits The AI Content Factory

A fabrica produz conteudo de qualidade (video, audio, imagem, script) mas nenhum departamento otimiza esse conteudo para ser encontrado. Um video incrivel sem titulo SEO, tags e descricao ricas nunca sera visto. O YouTube e o maior motor de busca do mundo depois do Google; o Pinterest e um motor de busca visual. Ignorar descoberta organica e deixar dinheiro na mesa.

## User Value

- Shin nao precisa pesquisar keywords manualmente — o departamento gera lista de palabras-chave para cada nicho.
- Cada video sai com titulo otimizado, descricao rica com links de afiliado e 15 tags.
- Artigos de blog para afiliados sao escritos com densidade de keyword ideal e heading estruturado.
- Relatorio mensal de "oportunidades organicas" mostra gaps de keyword que a fabrica pode explorar.

## Proposed Workflow

```
ReceivedTask{content_type, content_topic, target_platform, existing_asset_path}
  -> Pipeline stages (action=OPTIMIZE):
     1. KEYWORD_RESEARCH           (gerar lista de keywords curta, media e long-tail via fontes MOCK)
     2. COMPETITOR_SCAN            (analisar titulos/tags de concorrentes para o mesmo topico — MOCK)
     3. TITLE_GENERATION           (criar 3 opcoes de titulo otimizado com keyword principal)
     4. DESCRIPTION_ASSEMBLY       (montar descricao rica: keyword, CTA, links, timestamps)
     5. TAG_GENERATION             (gerar 10-15 tags por plataforma: YouTube vs Pinterest vs Blog)
     6. STRUCTURED_DATA_CHECK      (verificar se asset tem metadados minimos: thumb, caption, alt text)
     7. SEO_REPORT                 (resumo: keyword_alvo, search_volume_estimado, concorrencia, acoes tomadas)
```

## Required Employees

1. **SEOContentOptimizerEmployee** — herda ProductionEmployee, gerencia pipeline de otimizacao.
   - Hooks: `_check_reject()` rejeita se `content_type` ou `target_platform` nao suportados; `_build_pipeline()` monta SEOOptimizationPipeline; `_build_output_from_stages()` extrai `seo_report` e `optimized_metadata`.

## Required Capabilities

Todas ja existentes:
- `WEB_SEARCH` (pesquisa de keywords e concorrentes — MOCK)
- `TEXT_GENERATION` (titulo, descricao, tags, artigo)
- `DOCUMENT_GENERATION` (relatorio SEO)
- `TRANSLATION` (se precisar gerar keywords em ingles para alcance global)

## Risks And Compliance

- **Keyword stuffing**: o pipeline deve evitar excesso de repeticoao da mesma keyword. Regra: densidade maxima de 2.5% no texto.
- **Praticas enganosas**: nao gerar titulos clickbait que nao correspondem ao conteudo. Checklist de compliance contra clickbait.
- **Atualizacao de algoritmo**: as praticas de SEO mudam. O departamento deve usar heuristicas conservadoras e documentar premissas.

## MVP Scope

1. Pipeline deterministico MOCK com 7 stages.
2. SEOContentOptimizerEmployee com hooks padrao.
3. Snapshot `SEOOptimizationSnapshot` (contents_optimized, keywords_mapped, platforms_covered, avg_competition_score).
4. 3 plataformas suportadas no MVP: youtube, blog, pinterest.
5. Base MOCK de keywords por nicho: games, ofertas, tecnologia.
6. Demo com 25+ assertions: keyword research, competitor scan, titulo, descricao, tags, structured data, relatorio.

## Later Integrations

- YouTube Search API (sugestoes de keywords reais)
- Google Keyword Planner (volume de busca real)
- Ahrefs / SEMrush API (dados de concorrencia e backlinks)
- Pinterest Trends API
- Google Search Console API (performance de busca real)

## Open Questions For Shin/Codex

1. O departamento deve apenas sugerir otimizacoes ou aplicar automaticamente nos metadados dos assets?
2. As keywords devem ser fornecidas por Shin ou descobertas automaticamente?
3. Deve existir um artigo de blog para cada oferta de afiliado? Ou apenas para ofertas com alto potencial de busca?
4. Shin quer otimizar o que ja foi produzido (backlog) ou apenas conteudo novo?

## Sources

- YouTube SEO: https://backlinko.com/youtube-ranking-factors
- Google Keyword Planner: https://ads.google.com/home/tools/keyword-planner/
- Pinterest Trends: https://trends.pinterest.com/
- Keyword density best practices: https://moz.com/blog/keyword-density
