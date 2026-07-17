# Idea Proposal: Content Repurposing Department

Status: PROPOSTA - NAO IMPLEMENTADA.

## One-Sentence Idea

Criar um departamento que recebe um conteudo "raiz" (ex: video de 10 min, script longo, podcast) e produz multiplos derivados formatados para canais diferentes: shorts, posts de rede social, tweets, topicos de newsletter, citacoes visuais e artigos de blog — maximizando o ROI de cada producao.

## Why It Fits The AI Content Factory

Hoje cada departamento produz uma peca unica (1 video, 1 audio, 1 imagem, 1 script) de forma linear. Nao ha reaproveitamento transversal. Um video de 10 minutos contem material para 5 shorts, 3 tweets virais, 1 artigo de blog e 2 posts de Instagram. Sem repurposing, a fabrica esta usando 20% do potencial de cada ativo.

## User Value

- Shin produz UM video longo e ganha 8+ pecas de conteudo prontas para diferentes canais.
- O custo por peca de conteudo cai drasticamente — o trabalho pesado ja foi feito.
- Cada shorts pode ter CTA diferente: um para seguir, outro para comprar, outro para comentar.
- O departamento respeita a hierarquia: nunca corta um video longo arbitrariamente (herda regra do EditorialQualityValidator).

## Proposed Workflow

```
ReceivedTask{source_type, source_asset_path, target_formats, brand_voice}
  -> Pipeline stages:
     1. SOURCE_ANALYSIS            (analisar asset: duracao, topicos, momentos de alto impacto)
     2. SEGMENT_EXTRACTION        (identificar segmentos reaproveitaveis: hook, dica, CTA, conclusao)
     3. FORMAT_MAPPING            (mapear cada segmento para formato alvo: Shorts, Tweet, Post, Citação)
     4. DERIVATIVE_GENERATION     (gerar cada derivado: cortar video, resumir texto, extrair quote)
     5. CTA_VARIATION             (aplicar CTA diferente por formato: "sigame" vs "compre agora")
     6. PLATFORM_CAPTION_WRITING  (gerar legenda + hashtags para cada formato/plataforma)
     7. REPURPOSE_MANIFEST        (resumo: source, derivados criados, formatos, recomendacao de agenda)
```

## Required Employees

1. **ContentRepurposingEmployee** — herda ProductionEmployee, gerencia pipeline de reaproveitamento.
   - Hooks: `_check_reject()` rejeita se `source_type` desconhecido; `_build_pipeline()` monta RepurposingPipeline; `_build_output_from_stages()` extrai `repurpose_manifest`.

2. **SegmentExtractor** — helper interno que identifica cortes via heuristicas (MOCK: divisao por tempo fixo 60s).

## Required Capabilities

Todas ja existentes:
- `VIDEO_EDITING` (cortar segmentos)
- `TEXT_GENERATION` (reescrever para cada formato)
- `SOCIAL_MEDIA` (formatar para cada plataforma)
- `DOCUMENT_GENERATION` (manifesto)
- `STORAGE` (ler asset fonte, salvar derivados)

## Risks And Compliance

- **Crop arbitrario proibido**: a regra do `LongFormRepurposingValidator` (preservar capitulos, rejeitar cortes curtos sem contexto) deve ser herdada. Nenhum shorts pode ser extraido sem beat map.
- **Perda de contexto**: um corte de 15s sem setup pode ser enganoso. O pipeline deve incluir sempre uma linha de contexto.
- **Atribuicao**: se o conteudo original tem afiliado, os derivados tambem devem ter disclosure.
- **Qualidade**: nem todo segmento merece virar conteudo independente. O pipeline deve ter stage de qualidade.

## MVP Scope

1. Pipeline deterministico MOCK com 7 stages.
2. ContentRepurposingEmployee com hooks padrao.
3. Snapshot `ContentRepurposingSnapshot` (source_count, derivatives_created, formats_covered, avg_derivatives_per_source).
4. 1 asset fonte MOCK: script de 10 minutos (3000 palavras) → 5 derivados: 2 shorts hooks, 1 tweet, 1 post Instagram, 1 citacao visual.
5. Demo com 25+ assertions: source analysis, segment extraction, format mapping, derivados, CTA, captions, manifesto.
6. Regra: cada derivado deve ser >= 15s ou >= 50 palavras para manter contexto.

## Later Integrations

- Whisper/STT para extrair quotes de audio/video automaticamente
- Geracao de imagem para citacoes visuais (via ImageDepartment)
- Publicacao direta via Social Media Distribution Department
- Agendamento espacado dos derivados (via Content Scheduling Department)

## Open Questions For Shin/Codex

1. Os derivados devem ser gerados automaticamente ou Shin escolhe quais formatos quer?
2. Um video de 10 min pode gerar quantos shorts no maximo? (sugestao: 1 a cada 90s com beat)
3. O beat map deve vir do VideoDepartment ou o RepurposingDepartment cria o proprio?
4. Shin quer que os derivados ja saiam prontos para publicar ou como rascunhos para revisao?

## Sources

- Repurposing best practices: https://www.semrush.com/blog/content-repurposing/
- HubSpot guide: https://blog.hubspot.com/marketing/content-repurposing
- Long-form to short-form guidelines: ja documentadas em `core/departments/video/editorial_quality.py`
