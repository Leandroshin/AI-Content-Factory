# Idea Proposal: Social Media Distribution Department

Status: PROPOSTA - NAO IMPLEMENTADA.

## One-Sentence Idea

Criar um departamento que recebe conteudo finalizado (video, imagem, texto) da fabrica e faz publicacao multiplataforma (YouTube, Instagram, TikTok, Facebook, Pinterest, Twitter/X) com formatacao, hashtags, agendamento e relatorio basico de entrega.

## Why It Fits The AI Content Factory

A fabrica ja produz conteudo (VideoDepartment -> MP4, ImageDepartment -> PNG, ScriptDepartment -> texto + hook + CTA) mas o unico canal de publicacao e o Telegram (via TelegramAdapter). Todo o resto do conteudo gerado nunca chega ao publico. Este departamento fecha o gap de distribuicao sem depender de APIs pagas no MVP — usa saida estruturada para publicacao manual ou agendada.

## User Value

- Shin nao precisa copiar manualmente o MP4 do video para cada rede social.
- Um unico comando "publicar no YouTube, Instagram e TikTok" dispara tres saidas formatadas com a descricao e hashtags certas para cada plataforma.
- O relatorio de entrega mostra se o conteudo esta "pronto para publicar", "pendente de aprovacao manual" ou "bloqueado por compliance da plataforma".

## Proposed Workflow

```
ReceivedTask{content_type, asset_paths, caption, hook, platform_list, schedule}
  -> Pipeline stages:
     1. PLATFORM_VALIDATION     (validar que platform_list contem plataformas suportadas)
     2. FORMAT_CONVERSION       (converter aspect ratio, duracao, formato para cada plataforma)
     3. CAPTION_ASSEMBLY        (montar legenda + hashtags + CTA por plataforma)
     4. COMPLIANCE_SCAN         (checklist basico: palavras proibidas, conteudo marcado 18+, direitos autorais)
     5. QUEUE                   (persistir na fila de publicacao com schedule ou "pronto")
     6. PUBLISH                 (apenas MOCK — registrar "Publicado em {platform}" no log)
     7. DELIVERY_REPORT         (resumo: plataforma, status, asset_path, schedule_time)
```

## Required Employees

1. **SocialMediaPublisherEmployee** — herda ProductionEmployee, gerencia o pipeline de publicacao multiplataforma.
   - Hooks: `_check_reject()` rejeita se plataforma nao suportada; `_build_pipeline()` monta SocialMediaPipeline com os 7 stages; `_build_output_from_stages()` extrai `delivery_report` do DELIVERY_REPORT.

2. (Futuro) **PlatformAdapter** por rede — cada plataforma seria um adapter separado (YouTubeAdapter, InstagramAdapter, TikTokAdapter) com MOCK/REAL.

## Required Capabilities

Todas ja existentes:
- `SOCIAL_MEDIA` (ja declarada em core/tools/capabilities.py)
- `STORAGE` (para ler os assets gerados)
- `TEXT_GENERATION` (para montar legenda por plataforma)
- `VIDEO_RENDERING` (se precisar re-encode para formato especifico)
- `DOCUMENT_GENERATION` (relatorio de entrega)

## Risks And Compliance

- **Termos de servico**: cada plataforma tem regras sobre postagem automatizada. O MOCK nunca viola — apenas prepara. O REAL so deve publicar apos Shin aprovar cada canal individualmente.
- **Rate limiting**: plataformas limitam numero de posts/dia. O departamento precisa de um rate limiter interno.
- **Conteudo duplicado**: postar o mesmo video em 3 plataformas ao mesmo tempo pode ser considerado spam. O pipeline deve sugerir intervalos.
- **Atribuicao**: todo conteudo publicado deve ter disclosure de afiliado quando aplicavel (herdar do Creative Review ou Affiliate Deals).

## MVP Scope

1. Pipeline deterministico MOCK com 7 stages, sem API real.
2. SocialMediaPublisherEmployee com os hooks padrao + `analyze_capability_needs()` retornando `SOCIAL_MEDIA`.
3. Snapshot `SocialMediaDistributionSnapshot` em observability (platforms_published, total_assets, schedule_count).
4. Demo com 25+ assertions: validacao de plataforma, format conversion, caption assembly, compliance scan, fila, publicacao MOCK e relatorio.
5. Tabela interna de plataformas suportadas: youtube, instagram, tiktok, facebook, pinterest, twitter.

## Later Integrations

- YouTube Data API v3 (upload de video + descricao + tags)
- Instagram Graph API (reels + posts)
- TikTok Content Posting API
- Facebook Pages API
- Pinterest API (pins)
- Twitter/X API v2 (tweets com midia)
- Agendamento real com cron ou Cloudflare Workers

## Open Questions For Shin/Codex

1. As plataformas devem ser configuradas por ambiente (MOCK vs REAL) ou globais?
2. O scheduling deve ser feito pelo departamento ou por um componente externo (ex: fila no D1)?
3. Shin prefere um adapter por plataforma ou um adapter unificado com dispatch interno?
4. Deve herdar compliance do Creative Review Department ou ter o proprio compliance scan?

## Sources

- YouTube Data API: https://developers.google.com/youtube/v3
- Instagram Graph API: https://developers.facebook.com/docs/instagram-api
- TikTok Content Posting: https://developers.tiktok.com/products/content-posting/
- Facebook Pages API: https://developers.facebook.com/docs/pages
- Pinterest API: https://developers.pinterest.com/api/v5/
