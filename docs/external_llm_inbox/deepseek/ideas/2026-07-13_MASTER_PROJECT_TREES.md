# Arvores Genealogicas dos 12 Projetos

Status: PROPOSTA - NAO IMPLEMENTADA.

Este documento detalha cada um dos 12 projetos em arvores de dependencia: o que ja existe, o que precisa ser construido, o que depende de pagamento e o que depende de decisao humana. No final, uma auto-critica do que eu (DeepSeek) posso ter deixado passar.

---

## PARTE 0: MAPA DE DEPENDENCIA ENTRE PROJETOS

```
Foundation Layer (infra compartilhada)
     |
     +--[Canais]-- SocialMediaDistribution ───┐
     |                                         |
     +--[Metricas] Business Intelligence ──────┤
     |                                         |
     +--[Audiencia] EmailMarketing ────────────┤
     |                                         |
     +--[Planejamento] ContentScheduling ──────┤
     |                                         |
     +--[Descoberta] SEOOptimization ──────────┤
     |                                         |
     +--[Maximizacao] ContentRepurposing ──────┤
     |                                         |
     +--[Conversao] LandingPageOptimizer ──────┤
     |                                         |
     +--[Audio] PodcastProducer ───────────────┤
     |                                         |
     +--[PROJETOS DE CONTEUDO] ────────────────┘
     |
     +-- PROJETO A: Bible Animation
     |    consome: Script + Audio + Image + Video + SEO + SocialMedia
     |
     +-- PROJETO B: Home Exercise Course
     |    consome: Script + Audio + Image + Video + LandingPage + SocialMedia + Email + BI + AdOps
     |
     +-- PROJETO C: Animated Storytelling (Contos do Pixel)
     |    consome: Script + Audio + Image + Video + SEO + SocialMedia + Scheduling
     |
     +-- PROJETO D: Science Curiosity Shorts
          consome: Script + Audio + Image + Video + Scheduling + SEO
```

**Insight crucial**: construir os 8 departamentos de infra primeiro (Foundation Layer) desbloqueia os 4 projetos de conteudo com custo marginal baixissimo. Se Shin construir so os 4 projetos sem a fundacao, cada um vai precisar reinventar publicacao, metrica, email e agenda.

---

## PARTE 1: FOUNDATION LAYER (8 departamentos de infra)

Cada arvore abaixo mostra: o que ja existe (checklist), o que precisa ser construido (diamante), risco de pagamento (cifrao) e decision point (interrogacao).

---

### ARVORE 1: Social Media Distribution

```
NIVEL 0 - DEPARTAMENTO EXISTE?
   Nao. Criar SocialMediaPublisherEmployee (herda ProductionEmployee)

NIVEL 1 - PIPELINE BASE
   ├── PlatformValidator: aceita quais plataformas?
   │     MOCK: youtube, instagram, tiktok, facebook, pinterest, twitter
   │     DECISAO: Shin quer todas ou so algumas no MVP?
   │     RISCO: cada plataforma tem ToS diferente sobre automacao
   │
NIVEL 2 - FORMAT CONVERSION
   ├── VideoFormatConverter:
   │     YouTube: MP4 H.264 1920x1080, max 12h
   │     Instagram: MP4/MOV H.264 1080x1920 (Reels), max 90s
   │     TikTok: MP4 H.264 1080x1920, max 10 min (60s para organic)
   │     RISCO: FFmpeg existente da conta? Sim (FFmpegRenderAdapter)
   │     PRECISA: adapter de re-encode automatico ou manual?
   │
NIVEL 3 - CAPTION ASSEMBLY
   ├── CaptionGenerator:
   │     Por plataforma: YouTube (descricao longa), Instagram (caption + hashtags)
   │     TikTok (caption curta), Twitter (280 chars)
   │     RISCO: character limits mudam com frequencia
   │     PRECISA: tabela atualizavel de limites por plataforma
   │
NIVEL 4 - COMPLIANCE SCAN
   ├── PlatformComplianceChecker:
   │     YouTube: conteudo marcado para criancas? (COPPA)
   │     Instagram: nudez, violencia, desinformacao
   │     DECISAO: Shin quer bloqueio automatico ou apenas alerta?
   │
NIVEL 5 - QUEUE
   ├── PublishingQueue:
   │     Onde persiste? D1 ja existe? Sim (factory_dashboard)
   │     Pode reusar? PARCIAL -> D1 e para fila HITL, nao para publicacao
   │     PRECISA: nova tabela D1 ou persistence local?
   │
NIVEL 6 - PUBLISH (MOCK)
   ├── MockPublisher:
   │     OK: loga "Published to {platform}" com timestamp
   │     NAO PRECISA de API real no MVP
   │
NIVEL 7 - DELIVERY REPORT
   ├── DeliveryReportGenerator:
   │     Resumo por lote: quantos publicados, falhas, schedule
   │     Formato: dict estruturado + snapshot de observability

NIVEL 8 - INTEGRACOES FUTURAS (NIVEL PAGO)
   ├── YouTube Data API v3: upload + descricao + thumb (gratis ate 10k calls/dia)
   ├── Instagram Graph API: precisa de Facebook App + review
   │     RISCO: Instagram demora dias para aprovar app
   ├── TikTok Content Posting: precisa de Developer Account
   │     RISCO: TikTok e rigoroso com automacao
   ├── Pinterest API: acesso basico gratis
   └── Twitter/X API v2: plano free (1500 posts/mes)

AUTO-CRITICA (o que eu nao pensei):
   ? OAuth flow: cada plataforma tem fluxo de login diferente. Nao pensei em como
     Shin vai autorizar cada conta. YouTube = Google OAuth, Instagram = Facebook
     Login, TikTok = Developer Portal. Isso exige um OAuthManager generico.
   ? Refresh token: tokens expiram (Instagram: 60 dias). Ninguem renova.
   ? Duplicate detection: e se o mesmo video for enviado 2x para mesma plataforma?
     YouTube bloqueia, Instagram pode shadowban.
   ? Rate limit por plataforma: Instagram: 200 requests/hora, TikTok: 1000/dia.
     Precisa de rate limiter por plataforma (nao existe hoje).
   ? Thumbnail customizada: cada plataforma tem requisito de resolucao diferente
     para thumb. O ImageDepartment precisaria gerar 6 variantes de thumbnail.
```

---

### ARVORE 2: Business Intelligence

```
NIVEL 0 - DEPARTAMENTO EXISTE?
   Nao. Criar BusinessIntelligenceEmployee (herda ProductionEmployee)

NIVEL 1 - DATA COLLECTION
   ├── MetricDataSource (MOCK):
   │     3 canais (telegram, youtube, instagram)
   │     5 produtos, 30 dias de historico
   │     PRECISA: gerador de dados sinteticos realistas
   │
NIVEL 2 - METRIC CALCULATION
   ├── MetricCalculator:
   │     CTR = cliques / impressoes
   │     CPC = custo total / cliques
   │     Comissao total = soma das vendas * comissao %
   │     ROI = (receita - custo) / custo
   │     RISCO: calculo de ROI ignora custo de producao (horas de Shin)
   │     DECISAO: Shin quer incluir custo de tempo como "custo"?
   │
NIVEL 3 - TREND ANALYSIS
   ├── TrendDetector:
   │     Comparar mes atual vs mes anterior
   │     Detectar: aumento, queda, estavel
   │     RISCO: amostra pequena (1 mes) = ruido, nao tendencia
   │     PRECISA: intervalo de confianca minimo (ex: 30 dias de dados)
   │
NIVEL 4 - INSIGHT EXTRACTION
   ├── InsightEngine:
   │     "Produto X converte 3x mais no Telegram que no Instagram"
   │     "Videos com duracao >5min tem 40% mais cliques"
   │     RISCO: correlacao != causalidade. O relatorio deve alertar isso.
   │
NIVEL 5 - REPORT ASSEMBLY
   ├── ReportBuilder:
   │     Formato: dict estruturado + texto simples
   │     Secoes: resumo executivo, por canal, por produto, top insights, recomendacoes
   │
NIVEL 6 - ORGANIZATIONAL MEMORY
   ├── MemoryLogger:
   │     Salva cada relatorio como OrganizationalDocument versionado
   │     OK: OrganizationalMemoryRuntime ja existe
   │
NIVEL 7 - DELIVERY
   ├── ReportOutput:
   │     Para onde? Dashboard? CEO? Telegram?
   │     DECISAO: Shin quer receber onde?

NIVEL 8 - INTEGRACOES REAIS
   ├── YouTube Analytics API (gratis)
   ├── Instagram Insights API (gratis)
   ├── Meta Ads Insights API (precisa de token ads_read - ja existe em secrets/meta_ads.env)
   ├── Hotmart API (comissoes reais - webhook existe)
   └── Google Analytics (se tiver site)

AUTO-CRITICA:
   ? Dados de custo: de onde vem o custo? ElevenLabs, Suno, providers pagos.
     Nao existe um "cost tracker" centralizado que some gastos de todos os
     adapters. Sem isso, ROI e impreciso.
   ? Granularidade: metrica por video ou por campanha? Precisa decidir.
   ? Quem consome o relatorio? Shin ou a fabrica toma acao automatica?
   ? E se nao houver dados (mes 1 de operacao)? O relatorio deve dizer
     "dados insuficientes" em vez de inventar conclusao.
   ? Comparacao com benchmark: sem dados de mercado, "bom" e "ruim" sao
     subjetivos. Sugerir comparacao mes a mes como baseline.
```

---

### ARVORE 3: Email Marketing

```
NIVEL 0 - DEPARTAMENTO EXISTE?
   Nao. Criar EmailMarketerEmployee.

NIVEL 1 - SEGMENT IDENTIFICATION
   ├── SegmentManager:
   │     Segmentos MOCK: novos_assinantes, compradores_recentes, inativos_30d, afiliados_top
   │     DECISAO: Shin fornece lista ou o departamento gera segmentos?
   │     PRECISA: armazenamento de contatos (DATABASE existe, mas tabela de contatos nao)
   │
NIVEL 2 - CONTENT ASSEMBLY
   ├── EmailContentBuilder:
   │     Reutiliza output do ScriptDepartment + hook + CTA
   │     OK: ScriptDepartment ja gera CTA
   │     PRECISA: templates de email (HTML responsivo basico)
   │
NIVEL 3 - SUBJECT LINE
   ├── SubjectLineGenerator:
   │     3 opcoes: informativo, urgente, curioso
   │     Risco: SPAM trigger words ("gratis", "dinheiro", "urgente")
   │     PRECISA: blacklist de palavras SPAM
   │
NIVEL 4 - COMPLIANCE CHECK
   ├── EmailComplianceChecker:
   │     LGPD: opt-out visivel, remetente identificado
   │     Decisao: link de unsubscribe obrigatorio
   │     Risco: multa LGPD de 2% do faturamento
   │
NIVEL 5 - FORMAT RENDER
   ├── EmailRenderer:
   │     Texto simples + HTML basico
   │     PRECISA: template inline CSS (sem depender de CSS externo)
   │
NIVEL 6 - QUEUE
   ├── EmailQueue:
   │     Persistir na fila de envio com schedule
   │     PRECISA: nova tabela de fila ou reusa da PublishingQueue?
   │
NIVEL 7 - CAMPAIGN SUMMARY
   ├── CampaignSummary:
   │     Resumo: segmento, email_type, schedule, variantes

NIVEL 8 - INTEGRACOES REAIS
   ├── Mailchimp API (gratis ate 500 contatos)
   ├── SendGrid API (gratis 100 emails/dia)
   ├── Resend API (gratis 100 emails/dia)
   └── SMTP proprio (precisa configurar DNS, DKIM, SPF)
        RISCO ALTO: configuracao de email e complexa e pode cair em SPAM

AUTO-CRITICA:
   ? Sending infrastructure: quem envia o email de verdade? Nao pensei nisso.
     Precisa de um EmailAdapter concreto (MOCK/REAL). O MOCK so registra no log.
   ? Unsubscribe list: obrigatorio por lei. Onde fica? Como o departamento
     consulta antes de enviar?
   ? Bounce handling: emails invalidos, caixa cheia, servidor rejeitou.
     Precisa de tratamento senao a reputacao cai.
   ? Template versioning: Shin vai querer editar o template manualmente?
     O departamento precisa exportar HTML editavel, nao so codigo interno.
   ? Lista inicial: Shin tem lista de contatos ou comeca do zero?
     Se comeca do zero, precisa de lead magnet primeiro -> depende de LandingPage.
```

---

### ARVORE 4: Content Scheduling & Calendar

```
NIVEL 0 - DEPARTAMENTO EXISTE?
   Nao. Criar ContentSchedulerEmployee.

NIVEL 1 - GOAL ANALYSIS
   ├── GoalInterpreter:
   │     "3 posts/semana" -> 12 posts/mes
   │     "2 videos + 1 newsletter" -> 2 tasks pra Video, 1 pra Email
   │     DECISAO: metas fixas (Shin define) ou variaveis (fabrica sugere)?
   │
NIVEL 2 - CAPACITY CHECK
   ├── CapacityCalculator:
   │     Cada departamento tem capacidade? Ex: Video: 2 tarefas/dia
   │     PRECISA: capacidade por departamento (configuravel)
   │     RISCO: se a capacidade for muito alta, superlotacao. Muito baixa, ocioso.
   │     DECISAO: Shin define capacidade ou calculamos baseado em historico?
   │
NIVEL 3 - TIMELINE BUILD
   ├── TimelineBuilder:
   │     Distribuir tarefas nos dias uteis
   │     Respeitar: feriados, fins de semana, preferencias de Shin
   │     PRECISA: calendario de feriados (tabela fixa 2026-2027)
   │
NIVEL 4 - SEASONALITY SCAN
   ├── SeasonalityDetector:
   │     Feriados: Natal, Black Friday, Carnaval
   │     Eventos de nicho: E3/games, lanca consoles
   │     DECISAO: Shin fornece eventos ou departamento descobre (WEB_SEARCH)?
   │
NIVEL 5 - DEPARTMENT DISPATCH
   ├── TaskDistributor:
   │     Usa CompanyTaskRuntime para criar tasks nos departamentos
   │     OK: CompanyTaskRuntime ja existe
   │     PRECISA: interface entre Scheduler e DM (DepartmentManager)
   │
NIVEL 6 - CALENDAR ASSEMBLY
   ├── CalendarBuilder:
   │     Visualizacao: texto (tabela) ou HTML (calendario grafico)
   │     Cores: verde (ok), amarelo (pendente), vermelho (atrasado)
   │
NIVEL 7 - PROGRESS TRACKING
   ├── ProgressMonitor:
   │     Consultar status de cada task periodicamente
   │     Alertas: "3 tarefas atrasadas. Replanejar?"
   │     PRECISA: scheduler de verificacao (cada hora? cada dia?)

AUTO-CRITICA:
   ? Como o scheduler sabe a capacidade real de cada departamento? Hoje nenhum
     departamento reporta "estou ocupado". Sem isso, o scheduler vai alocar
     mais tarefas que a fabrica aguenta.
   ? Prioridade: tarefa urgente vs tarefa normal. Como decidir qual vai primeiro?
   ? E se um departamento rejeitar a tarefa (capability check fail)?
   ? Feriados moveis (Carnaval, Pascoa) mudam todo ano. A tabela precisa ser
     atualizada anualmente.
   ? Integracao com Google Calendar: Shin quer ver no celular? Isso exige API.
```

---

### ARVORE 5: SEO & Organic Discovery

```
NIVEL 0 - DEPARTAMENTO EXISTE?
   Nao. Criar SEOContentOptimizerEmployee.

NIVEL 1 - KEYWORD RESEARCH
   ├── KeywordGenerator (MOCK):
   │     Keyword curta: "exercicios em casa"
   │     Keyword media: "exercicios em casa para mulheres"
   │     Keyword long-tail: "melhores exercicios em casa para perder barriga"
   │     DECISAO: keywords manuais (Shin fornece) ou geradas por IA?
   │     PRECISA: base de palavras-chave por nicho (games, ofertas, saude, tecnologia)
   │
NIVEL 2 - COMPETITOR SCAN
   ├── CompetitorAnalyzer (MOCK):
   │     Ver titulos e tags de concorrentes simulados
   │     RISCO: MOCK e obvio — dados reais exigem WEB_SEARCH ou scraping
   │     PRECISA: dados MOCK de concorrentes por nicho
   │
NIVEL 3 - TITLE GENERATION
   ├── TitleOptimizer:
   │     3 opcoes com keyword principal no inicio
   │     YouTube: max 70 chars (senao corta)
   │     Blog: max 60 chars (SEO snippet)
   │
NIVEL 4 - DESCRIPTION ASSEMBLY
   ├── DescriptionBuilder:
   │     YouTube: keyword nos primeiros 150 caracteres
   │     Links de afiliado + timestamps (se video)
   │     Templates de descricao por tipo de conteudo
   │
NIVEL 5 - TAG GENERATION
   ├── TagGenerator:
   │     YouTube: 10-15 tags (keyword principal, variacoes, topicos relacionados)
   │     Pinterest: 5-10 hashtags visuais
   │     Blog: categorias + tags
   │
NIVEL 6 - STRUCTURED DATA
   ├── StructuredDataChecker:
   │     Thumbnail presente? Alt text nas imagens? Schema.org markup?
   │     OK: ImageDepartment gera imagens, mas sem alt text automatico
   │     PRECISA: alt text generator
   │
NIVEL 7 - SEO REPORT
   ├── SEOReport:
   │     Keyword alvo, search volume estimado, concorrencia, acoes tomadas
   │     Snapshot: SEOOptimizationSnapshot

NIVEL 8 - INTEGRACOES REAIS
   ├── YouTube Search API (gratis, 100 queries/dia)
   ├── Google Keyword Planner (precisa de Google Ads account)
   ├── Google Search Console API (gratis se tiver site)
   └── Pinterest Trends API (gratis)

AUTO-CRITICA:
   ? Keyword stuffing detector: como garantir que o texto nao fique repetitivo?
     Precisa de um validador de densidade de keyword (max 2.5%).
   ? Atualizacao de algoritmo SEO: YouTube e Google mudam o ranking toda hora.
     O departamento MOCK nao acompanha. O REAL precisaria de fontes atualizadas.
   ? Sinonimos: o departamento gera keywords mas nao considera latente semantic
     indexing (LSI). Ex: "emagrecer" e "perder peso" sao relacionados mas o
     sistema pode nao conectar.
   ? Backlog vs novo: Shin tem centenas de videos/posts antigos sem SEO.
     O departamento consegue otimizar o backlog automaticamente?
```

---

### ARVORE 6: Content Repurposing

```
NIVEL 0 - DEPARTAMENTO EXISTE?
   Nao. Criar ContentRepurposingEmployee.

NIVEL 1 - SOURCE ANALYSIS
   ├── SourceAnalyzer:
   │     Identificar: tipo (video, texto, audio), duracao, topicos
   │     MOCK: divisao por marcadores de tempo fixos (60s)
   │     RISCO: MOCK ignora beats naturais do conteudo
   │
NIVEL 2 - SEGMENT EXTRACTION
   ├── SegmentExtractor:
   │     Hook (0-15s): melhor parte para Shorts
   │     Dica (meio): conteudo de valor para post
   │     Conclusao (final): CTA ou reflexao final
   │     REGRA: herdar LongFormRepurposingValidator — rejeitar cortes <15s sem contexto
   │     PRECISA: implementar as regras de validacao em codigo
   │
NIVEL 3 - FORMAT MAPPING
   ├── FormatMapper:
   │     Hook -> Shorts (vertical, <60s)
   │     Dica -> Tweet (texto <280 chars)
   │     Citacao -> Imagem com quote (gerado pelo ImageDepartment)
   │     Conteudo -> Post Instagram (carrossel de imagens)
   │
NIVEL 4 - DERIVATIVE GENERATION
   ├── DerivativeFactory:
   │     Video: cortar trecho usando FFmpeg (existe)
   │     Texto: resumir automaticamente
   │     Quote: extrair frase + ImageDepartment gera visual
   │     RISCO: corte de video com transicoes abruptas — precisa de crossfade
   │
NIVEL 5 - CTA VARIATION
   ├── CTAVariator:
   │     Short: "Sigame para mais dicas"
   │     Tweet: "Compre agora com 20% de desconto (link)"
   │     Post: "O que voce acha? Comente abaixo!"
   │
NIVEL 6 - PLATFORM CAPTION
   ├── CaptionPerPlatform:
   │     Reusa CaptionGenerator do SocialMediaDistribution
   │     PRECISA: compartilhar o mesmo modulo (evitar duplicacao)
   │
NIVEL 7 - REPURPOSE MANIFEST
   ├── ManifestGenerator:
   │     Lista de derivados + formato + plataforma recomendada
   │     Snapshot: ContentRepurposingSnapshot

AUTO-CRITICA:
   ? Beat detection real: sem analise de video (transcricao + edicao), a
     extracao de segmentos e MOCK e imprecisa. Futuramente precisa de
     SPEECH_TO_TEXT para detectar topicos por fala.
   ? Qualidade do derivado: nem todo segmento de 15s e interessante.
     Precisa de um threshold de qualidade — ou avaliação humana.
   ? Conflito com EditorialQualityValidator: ja existe uma regra "nao cortar
     video longo arbitrariamente". O RepurposingDepartment precisa reusa-la,
     nao ignora-la.
   ? Cross-linking: cada derivado deve linkar de volta ao video original
     (para views no conteudo principal). Nao pensei nisso.
```

---

### ARVORE 7: Podcast & Audio Content

```
NIVEL 0 - DEPARTAMENTO EXISTE?
   Nao. Criar PodcastProducerEmployee.

NIVEL 1 - EPISODE STRUCTURE
   ├── StructureGenerator:
   │     Tipos: monologo (1 voz), entrevista (2+ vozes), mesa (3+)
   │     Template: intro (30s) + blocos (10 min cada) + CTA + encerramento
   │     DECISAO: Shin define estrutura ou o departamento gera?
   │
NIVEL 2 - SCRIPT GENERATION
   ├── ScriptWriter:
   │     Roteiro do host com marcas de tempo
   │     OK: ScriptDepartment existe mas e focado em video/blog
   │     PRECISA: adaptar para formato de podcast (mais conversacional)
   │
NIVEL 3 - VOICE RECORDING
   ├── VoiceRecorder:
   │     Host: KokoroAdapter (gratis, local)
   │     Convidado (MOCK): segunda voz Kokoro com tom diferente
   │     RISCO: Kokoro pode soar robotico para podcast longo
   │     DECISAO: Shin quer ElevenLabs para voz mais natural? (custo)
   │
NIVEL 4 - VINHETA ASSEMBLY
   ├── VinhetaBuilder:
   │     Intro: musica + "Voce esta ouvindo [NOME]" + efeito
   │     Outro: "Obrigado por ouvir. Siga nas redes..."
   │     RISCO: musica precisa ser royalty-free (CC0 ou Suno)
   │
NIVEL 5 - CHAPTER MARKING
   ├── ChapterMarker:
   │     Timestamps: "00:00 - Intro", "02:30 - Bloco 1"
   │     Padrao: Podcast RSS chapters (Apple spec)
   │     PRECISA: formatador de chapters XML
   │
NIVEL 6 - SHOW NOTES
   ├── ShowNotesBuilder:
   │     Descricao, links, CTA, disclosure de afiliado
   │     OK: hereda compliance do AffiliateDeals
   │
NIVEL 7 - EPISODE PACKAGE
   ├── PackageAssembler:
   │     MP3 final (ou WAV) + capa + show notes .md + RSS entry .xml
   │     PRECISA: RSS feed generator (para Spotify/Apple)
   │
NIVEL 8 - INTEGRACOES REAIS
   ├── Spotify for Podcasters API (gratis)
   ├── Apple Podcasts Connect (manual, precisa de aprovacao)
   └── Hosting RSS (buzzsprout, transistor, anchor)

AUTO-CRITICA:
   ? RSS hosting: onde o RSS fica? Precisa de um servidor HTTP para servir
     o XML. O D1 do Sites pode servir? Talvez, mas nao foi feito para isso.
   ? Audio quality standard: Spotify exige -16 LUFS, Apple -16 LUFS.
     Precisa de normalizacao. O FFmpeg consegue (loudnorm filter).
   ? Entrevista simulada: se for "convidado MOCK", precisa de disclaimer
     explicito que e IA, senao e enganoso.
   ? Periodicidade: podcast semanal ou diario? Depende do ContentScheduler.
   ? Capa do podcast: ImageDepartment precisa gerar capa nos padroes
     Apple (3000x3000px, JPEG/PNG).
```

---

### ARVORE 8: Landing Page & Conversion

```
NIVEL 0 - DEPARTAMENTO EXISTE?
   Nao. Criar LandingPageOptimizerEmployee.

NIVEL 1 - BRIEF ASSEMBLY
   ├── BriefBuilder:
   │     Oferta, publico-alvo, objetivo (venda, lead, inscricao), tom
   │     DECISAO: Shin fornece ou departamento extrai do ProductResearch?
   │
NIVEL 2 - HEADLINE VARIATION
   ├── HeadlineVariator:
   │     3 variantes: racional ("Perca peso em 30 dias"), emocional ("Seja a
   │     melhor versao de voce"), curioso ("O segredo que a academia nao conta")
   │
NIVEL 3 - COPY WRITING
   ├── CopyWriter:
   │     Secoes: dor, solucao, beneficios, prova social, objecoes, CTA
   │     OK: ScriptDepartment ja faz copy, mas e para video/blog
   │     PRECISA: adaptar para conversao (mais escaneavel, bullets, negrito)
   │
NIVEL 4 - COMPLIANCE CHECK
   ├── ComplianceChecker:
   │     LGPD: formulario com consentimento
   │     Disclosure afiliado: antes do CTA
   │     Nao enganoso: "resultados variam" em promessas
   │
NIVEL 5 - LAYOUT GENERATION
   ├── LayoutGenerator:
   │     HTML responsivo com: hero, beneficios, depoimento, FAQ, CTA, footer
   │     PRECISA: template engine que gere HTML estatico
   │     RISCO: HTML basico pode nao converter bem. Shin vai querer editar.
   │     DECISAO: Shin prefere HTML puro ou exportar para Webflow/Carrd?
   │
NIVEL 6 - VARIANT CREATION
   ├── VariantFactory:
   │     A: pagina longa (tudo na mesma pagina)
   │     B: pagina curta (so hero + CTA)
   │     C: pagina com video (embed do YouTube)
   │
NIVEL 7 - PAGE PACKAGE
   ├── PackageBuilder:
   │     3 HTMLs + assets + AB test plan

NIVEL 8 - INFRAESTRUTURA DE HOSTING
   ├── Onde hospedar?
   │     Opcao A: Vercel (gratis, 100GB largura)
   │     Opcao B: Cloudflare Pages (gratis, 500 builds/mes)
   │     Opcao C: Sites da OpenAI (ja existe, mas e privado)
   │     DECISAO: Shin quer dominio proprio? ex: curso.achadosbaratos.com.br
   │     PRECISA: configurar DNS, SSL (Cloudflare faz gratis)
   │

AUTO-CRITICA:
   ? DEPLOY: quem faz deploy da pagina? Nao pensei em como a pagina sai do
     departamento e vai para o ar. Precisa de um "PageDeployer" que publique
     os HTMLs no servidor de escolha.
   ? Acompanhamento de performance: depois que a pagina esta no ar, quem mede
     conversao? Precisa de integracao com Business Intelligence.
   ? Formularios: se a pagina captura leads, para onde os dados vao?
     EmailMarketing precisa receber. Nao pensei na integracao.
   ? Mobile-first: 80% do trafego brasileiro e mobile. O layout PRECISA ser
     responsivo desde o MVP. Nao especifiquei isso claramente.
   ? Velocidade de carregamento: Google penaliza paginas lentas. O HTML
     gerado precisa ser leve (<200KB total).
```

---

## PARTE 2: PROJETOS DE CONTEUDO (4 projetos)

Estes projetos CONSONEM os 8 departamentos de infra acima. Se a fundacao nao existir, eles precisarao de mais trabalho manual.

---

### ARVORE 9: Bible Animation Pipeline

```
DEPENDENCIAS: Script + Audio + Image + Video + SEO + SocialMedia

NIVEL 0 - TEXTO FONTE
   ├── BibleSourceAdapter:
   │     Qual traducao? Almeida (dominio publico), NVI (com direitos)?
   │     DECISAO CRITICA: Shin precisa escolher a traducao. NVI tem direitos
   │     autorais e nao pode ser usada comercialmente sem licenca.
   │     PRECISA: Bible API (gratis: https://bible-api.com/)
   │
NIVEL 1 - SCRIPT (roteiro)
   ├── ScriptDepartment produz:
   │     - Dialogo fiel ao texto
   │     - Narracao de ligacao
   │     - Stage directions (cenas, expressoes)
   │     PRECISA: "BiblicalScriptWriter" — extensao do ScriptDepartment com
   │     conhecimento de contexto historico e geografico
   │     RISCO: interpretacao teologica tendenciosa. Manter-se no texto.
   │
NIVEL 2 - AUDIO (dublagem)
   ├── AudioDepartment produz:
   │     - 1 voz por personagem (ElevenLabs com timbres diferentes)
   │     - Narrador (voz neutra, constante)
   │     - Efeitos sonoros (agua, vento, passos, multidão)
   │     PRECISA: mapeamento voz-personagem persistente (memoria)
   │     PRECISA: 5+ vozes diferentes no ElevenLabs ou Kokoro
   │     CUSTO REAL: ElevenLabs TTS ~$0.30 por 5 min de dialogo
   │
NIVEL 3 - IMAGE (visuais)
   ├── ImageDepartment produz:
   │     - Personagens consistentes (Jesus, Pedro, Maria, etc.)
   │     - Cenarios (deserto, templo, barco, monte)
   │     - Objetos (cajado, cruz, peixes, moedas)
   │     RISCO: consistencia visual entre episodios. Personagem Jesus nao pode
   │     mudar de rosto do EP 1 para o EP 2.
   │     PRECISA: "CharacterSheet" salvo no OrganizationalMemory
   │
NIVEL 4 - VIDEO (animacao)
   ├── VideoDepartment produz:
   │     - Cena com personagem + fundo + animacao basica
   │     - Labia sincronizada com audio
   │     - Transicoes entre cenas
   │     - Legenda da passagem
   │
NIVEL 5 - COMPILACAO (editor)
   ├── VideoEditorEmployee (ou extensao) produz:
   │     - Unir multiplas passagens em video tematico
   │     - Abertura padrao do canal
   │     - Color grading consistente
   │     - MP4 final
   │     PRECISA: regras de compilacao (ordem cronologica vs tematica)
   │
NIVEL 6 - QUALIDADE
   ├── CreativeReview:
   │     - Fidelidade teologica (o video corresponde a passagem?)
   │     - Qualidade visual (personagens consistentes?)
   │     - Audio sincronizado?
   │     PRECISA: "TheologicalReviewRule" — regra de qualidade especifica
   │

NIVEL 7 - PUBLICACAO
   ├── SEOOptimizer: titulo, descricao, tags
   ├── SocialMediaDistributor: YouTube + Instagram Reel
   └── Schedule: 1x/semana (via ContentScheduler)

CUSTO POR EPISODIO (5 min, 4 personagens)
   ├── MOCK: $0.00
   └── REAL: ~$0.45 (ElevenLabs ~$0.30 + Provider imagem ~$0.10 + Suno ~$0.05)

AUTO-CRITICA:
   ? VOZ FIXA: cada personagem precisa da MESMA voz em todo episodio.
     ElevenLabs tem voice cloning, mas nao usei no planejamento. Shin
     precisa gerar as vozes uma vez e reusar.
   ? JESUS COM ROSTO: culturas diferentes tem representacoes diferentes de
     Jesus. Isso e um hot button teologico. Precisa de decisao de Shin.
   ? CRIANCAS NO PUBLICO: se o canal for infantil, YouTube exige COPPA
     compliance. Isso afeta recomendacoes e anuncios.
   ? LICENCA DA TRADUCAO: NVI, NTLH, Ave Maria tem direitos autorais.
     Almeida e dominio publico. Almeida corrigida tem direitos?
     PRECISA: pesquisa juridica rapida.
```

---

### ARVORE 10: Home Exercise Course + Hotmart Funnel

```
DEPENDENCIAS: Script + Audio + Image + Video + LandingPage + SocialMedia
              + Email + BI + AdOps (novo)

NIVEL 0 - CURSO DESIGN
   ├── Publico alvo: mulheres 25-45, iniciante, 30 dias
   ├── Estrutura: 5 modulos, 30 aulas de 5-10 min cada
   ├── Bonus: planilha treino, guia dieta, acesso grupo Telegram
   └── DECISAO: Shin escolhe o nicho (feminino, masculino, senior, gestante)?

NIVEL 1 - CONTEUDO DO CURSO
   ├── ScriptDepartment:
   │     - Roteiro de cada aula (explicacao + demonstracao)
   │     - Guia de alimentacao (cardapio semanal)
   │     - PDFs: planilha, checklist, diario
   │
   ├── ImageDepartment:
   │     - Ilustracao de cada exercicio em 3 tempos
   │     - Diagrama anatomico (musculos trabalhados)
   │     - Thumbnail/capa do curso
   │
   ├── AudioDepartment:
   │     - Voz de instrutora (firme, motivacional)
   │     - Countdown/timer sounds
   │     - Musica de fundo (Suno ou royalty-free)
   │
   ├── VideoDepartment:
   │     - Animacao do personagem fazendo exercicio
   │     - Efeitos: setas, contagem, destaque muscular
   │     - Intro/outro padrao
   │     - 30 aulas finalizadas
   │
   └── CreativeReview:
        - Exercicio fisiologicamente correto?
        - Disclaimer medico presente?
        - Qualidade visual consistente?

NIVEL 2 - PRODUTO Hotmart
   ├── Criar produto na Hotmart (manual, Shin faz)
   ├── Gerar link de afiliado
   ├── Configurar checkout
   └── PRECISA: integracao entre LandingPage e Hotmart (webhook ja existe!)

NIVEL 3 - FUNIL DE VENDAS
   ├── Landing Page de vendas:
   │     - Headline + copy + beneficios + depoimentos MOCK + CTA
   │     - Variantes A/B (longa, curta, video)
   │
   ├── Lead Magnet:
   │     - "Guia de 7 dias para comecar" (PDF gratuito)
   │     - Pagina de captura com formulario
   │     - Email de entrega automatico
   │
   ├── Email Sequence (5 emails):
   │     - D1: Problema
   │     - D2: Solucao (curso)
   │     - D3: Prova social
   │     - D4: Escassez
   │     - D5: Oferta + bonus
   │
   └── Checkout Hotmart (link no CTA)

NIVEL 4 - AQUISICAO DE TRAFEGO
   ├── Post organico Instagram:
   │     - 5 posts + 3 Reels + 2 Facebook
   │     - Hashtags do nicho fitness
   │
   ├── (FUTURO) Meta Ads:
   │     - Criativo video + imagem + copy
   │     - Publico: mulheres 25-45, fitness, Brasil
   │     - Landing page por anuncio (UTM)
   │     - Budget: R$500-2000 para teste
   │     - PRECISA: AdOperationsEmployee (novo departamento)
   │
   └── (FUTURO) Google Ads:
        - Palavras-chave: "curso exercicios em casa", "emagrecer em casa"

NIVEL 5 - ANALISE E OTIMIZACAO
   ├── BusinessIntelligence:
   │     - Visitas -> leads -> vendas -> comissao
   │     - Custo de trafego vs receita
   │     - Qual headline/converteu mais?
   │     - Sugerir melhorias baseadas em dados
   │

CUSTO TOTAL ESTIMADO (lancamento)
   ├── Producao do curso (MOCK): $0
   ├── Landing Page (MOCK): $0
   ├── Email (SendGrid gratis): $0
   ├── Trafego pago: R$500-2000 (opcional)
   ├── Dominio: ~R$40/ano
   └── Hotmart taxa: ~10% + R$1.50 por venda

PRECO SUGERIDO: R$ 47-67
PONTO DE EQUILIBRIO: 15-25 vendas (cobrindo trafego + taxas)

AUTO-CRITICA:
   ? DISCLAIMER MEDICO: exercicios sem supervisao podem causar lesao.
     O departamento PRECISA incluir "consulte um medico antes de comecar"
     em destaque. Sem isso, Shin pode ser responsabilizado.
   ? EXERCICIOS INSEGUROS: o roteiro nunca deve sugerir exercicios de alto
     risco (ex: agachamento com barra pesada sem supervisao). Precisa de
     whitelist de exercicios seguros.
   ? DEPOIMENTOS MOCK: se forem gerados, precisam estar marcados como
     "resultados simulados" ou "depoimento ilustrativo". Lei de defesa do
     consumidor.
   ? GRUPO TELEGRAM: se o curso incluir grupo, Shin precisa moderar.
     Ou criar regras claras de uso.
   ? TRAFEGO PAGO: nao lance com trafego pago sem testar a pagina primeiro.
     Sugiro 2 semanas de trafego organico antes de pagar por click.
```

---

### ARVORE 11: Animated Storytelling Channel ("Contos do Pixel")

```
DEPENDENCIAS: Script + Audio + Image + Video + SEO + SocialMedia + Scheduling

NIVEL 0 - UNIVERSO
   ├── Criar "Biblia do Universo":
   │     - Personagens fixos (nome, personalidade, voz, design)
   │     - Regras do mundo (dentro de um videogave retro)
   │     - Tom: humor adulto, nostalgia games
   │     - DECISAO: Shin define os personagens ou a fabrica gera?
   │
NIVEL 1 - ROTEIRO (cada episodio)
   ├── ScriptDepartment:
   │     - 3 ideias de episodio por brainstorming MOCK
   │     - Dialogo para 3-5 personagens
   │     - Narracao de transicao
   │     - Stage directions
   │     - PRECISA: "ContinuousStoryline" — cada episodio referencia o anterior
   │
NIVEL 2 - AUDIO
   ├── AudioDepartment:
   │     - Vozes FIXAS para cada personagem (registradas no OrganizationalMemory)
   │     - Efeitos 8-bit (pulo, morte, moeda, power-up)
   │     - Trilha chip-tune (Suno: prompt "8-bit chip-tune music")
   │     - RISCO: consistencia de voz entre episodios
   │     - PRECISA: reusar a mesma configuracao de voz ElevenLabs
   │
NIVEL 3 - VISUAL
   ├── ImageDepartment:
   │     - Sprites (personagens em 4 direcoes)
   │     - Cenarios pixel art
   │     - UI elements (dialog box, health bar)
   │     - PRECISA: "PixelArtConverter" ou desenho manual
   │     - RISCO: Shin sabe desenhar pixel art? Se nao, o ImageDepartment
   │       MOCK vai gerar imagens genericas, nao pixel art de verdade.
   │
NIVEL 4 - ANIMACAO
   ├── VideoDepartment:
   │     - Scene layout (sprite + cenario + UI)
   │     - Animacao (andar, falar, interagir)
   │     - Legenda sincronizada
   │
NIVEL 5 - POS-PRODUCAO
   ├── VideoEditor:
   │     - Abertura padrao do canal (animada)
   │     - Encerramento com "inscreva-se"
   │     - Transicoes retro (scanline, fade)
   │     - MP4 final 1080p60
   │
NIVEL 6 - QUALIDADE
   ├── CreativeReview:
   │     - Historia tem comeco, meio, fim?
   │     - Personagens estao identicos ao EP anterior?
   │     - Audio sincronizado?
   │
NIVEL 7 - PUBLICACAO
   ├── SEOOptimizer: "NPC REBELDE - Contos do Pixel EP 12"
   ├── SocialMedia: YouTube + Reel teaser + Twitter/X
   ├── Scheduling: 1x/semana no sabado as 10h
   └── Playlist: "Temporada 1" no YouTube

CUSTO POR EPISODIO (10 min)
   ├── MOCK: $0.00
   └── REAL: ~$0.73 (ElevenLabs $0.50 + Provider imagem $0.20 + Suno $0.03)

MONETIZACAO
   ├── YouTube ads (CPM medio BR ~R$1.50)
   ├── Hotmart: "Temporada 1 Completa" R$ 29
   ├── Merch: camisetas (print on demand)
   └── Apoia-se: financiamento recorrente

AUTO-CRITICA:
   ? CONSISTENCIA DE PERSONAGEM: o maior risco. Se o sprite do protagonista
     mudar do EP 1 para o EP 2, o publico nota. Precisa de um sistema de
     "Character Sheet" que o ImageDepartment SEMPRE consulte.
   ? VOZ DO PERSONAGEM: ElevenLabs voice cloning permitiria a mesma voz
     sempre, mas o plano free nao oferece. Precisa do plano paid (~$5/mes).
   ? UNIVERSO COMPARTILHADO: se Shin criar um segundo canal no mesmo universo,
     os eventos de um afetam o outro? Isso e complexo demais para MVP.
   ? DIREITOS AUTORAIS DE GAMES: se usar nomes de jogos reais (Mario, Sonic)
     pode ter problemas. O universo "Contos do Pixel" e generico, mas
     cuidado com referencias muito obvias.
   ? AUDIENCIA INICIAL: canal novo no YouTube demora 6-12 meses para crescer.
     Shin precisa de paciencia ou trafego pago para acelerar.
```

---

### ARVORE 12: Science Curiosity Shorts ("Curious Byte")

```
DEPENDENCIAS: Script + Audio + Image + Video + Scheduling + SEO

NIVEL 0 - FORMATO
   ├── Duracao: 60s cada
   ├── Estilo: fundo escuro, elementos coloridos, narracao calma
   ├── Frequencia: 1 video/dia (30 por batch)
   └── Publico: todas as idades, curiosos em geral

NIVEL 1 - ROTEIRO (batch de 30)
   ├── ScriptDepartment:
   │     - 30 perguntas de curiosidade cientifica
   │     - Hook + explicacao + CTA (15s + 35s + 10s)
   │     - Fonte: Wikipedia, Britannica, ciencia popular
   │     - PRECISA: "FactCheckRule" — verificar se a resposta e correta
   │     - RISCO: desinformacao cientifica. Um fato errado descredibiliza o canal
   │
NIVEL 2 - AUDIO (batch)
   ├── AudioDepartment:
   │     - Narracao unica (30 audios com mesma voz e tom)
   │     - 1 trilha ambiente de fundo (reutilizavel)
   │     - Efeitos: "ding" (descoberta), "whoosh" (transicao)
   │
NIVEL 3 - TEMPLATE VISUAL
   ├── ImageDepartment:
   │     - Paleta fixa (fundo #1a1a2e, elementos #e94560, #0f3460)
   │     - 5 templates de cena:
   │       1. Pergunta (texto grande, icone de interrogacao)
   │       2. Explicacao (texto + diagrama simples)
   │       3. Exemplo (animacao ou icone)
   │       4. Curiosidade extra (texto destacado)
   │       5. CTA ("E amanha: ...")
   │     - PRECISA: Template system (reutilizar entre videos)
   │
NIVEL 4 - VIDEO (render batch)
   ├── VideoDepartment:
   │     - Para cada um dos 30 scripts:
   │       1. Selecionar template adequado
   │       2. Inserir texto + icone
   │       3. Sincronizar narracao
   │       4. Adicionar legenda
   │       5. Renderizar 60s
   │     - PRECISA: "BatchRenderPipeline" que processa 30 videos de uma vez
   │     - VANTAGEM: templates compartilhados reduzem custo em ~90%
   │
NIVEL 5 - QUALIDADE
   ├── CreativeReview:
   │     - Precisao cientifica (cada um dos 30)
   │     - Audio sincronizado
   │     - Legenda correta
   │     - Contraste acessivel
   │
NIVEL 6 - AGENDAMENTO
   ├── ContentScheduler:
   │     - 1 video/dia para os proximos 30 dias
   │     - Horario fixo: 10h da manha
   │     - Descricao curta com hashtags
   │
NIVEL 7 - MONETIZACAO
   ├── YouTube Shorts Fund (~$0.01-0.03/1000 views)
   ├── Compilados de 10 shorts em video longo (com anuncio)
   ├── Hotmart: ebook "101 Curiosidades" R$ 17
   └── (FUTURO) Versao em ingles para 2x audiencia

CUSTO POR BATCH (30 videos)
   ├── MOCK: $0.00
   └── REAL: ~$1.65 ($0.055/video)
        ElevenLabs: $0.60 | Provider imagem: $1.00 | Suno: $0.05

AUTO-CRITICA:
   ? BATCH RENDER: nao especifiquei COMO renderizar 30 videos de uma vez.
     Precisa de um loop no VideoDepartment: para cada script, montar cena,
     sincronizar, renderizar. Isso e viavel tecnicamente (FFmpeg em lote).
   ? TEMPLATE SYSTEM: os templates precisam ser flexiveis. Um video sobre
     "Por que o ceu e azul" precisa de layout diferente de "Como funciona
     um ima". Talvez 5 templates nao sejam suficientes — talvez 10-15.
   ? FATO ERRADO: se um video contiver erro cientifico, Shin precisa
     corrigir e reenviar. O lote de 30 torna a correcao cara. Sugiro
     publicar 1 video por dia e ter 1 dia de buffer para revisao.
   ? PUBLICO INFANTIL: se o YouTube classificar como "feito para criancas",
     perdera comentarios e recomendacoes personalizadas. O ideal e
     marcar como "nao feito para criancas" mas educacional.
   ? INTRO VOICE: a mesma voz todo dia cria familiaridade. Mas se Shin
     enjoar, trocar a voz no meio da serie quebra consistencia.
```

---

## PARTE 3: CAMINHO CRITICO — O QUE CONSTRUIR PRIMEIRO

### FASE 0: Ja existe (pode usar hoje)
- Script Department
- Audio Department
- Image Department
- Video Department
- Creative Review Department
- Affiliate Deals Department
- Hotmart Webhook
- QualityRuntime

### FASE 1: Construir primeiro (desbloqueia multiplos projetos)
```
1. Social Media Distribution Department
   Motivo: sem ele, nenhum conteudo sai da fabrica
   Impacto: desbloqueia Bible, Storytelling, Shorts

2. Content Scheduling & Calendar Department
   Motivo: sem planejamento, producao e reativa e inconsistente
   Impacto: desbloqueia frequencia para Bible, Shorts, Podcast

3. SEO & Organic Discovery Department
   Motivo: sem SEO, conteudo excelente nao e encontrado
   Impacto: aumenta ROI de Bible, Storytelling, Shorts
```

### FASE 2: Construir para monetizar
```
4. Landing Page & Conversion Department
   Motivo: necessario para vender qualquer produto digital
   Impacto: desbloqueia Home Exercise Course, ebooks, colecoes

5. Email Marketing Department
   Motivo: necessario para nutrir leads e vender
   Impacto: desbloqueia funil de vendas completo

6. Business Intelligence Department
   Motivo: necessario para saber o que esta funcionando
   Impacto: otimiza todos os projetos
```

### FASE 3: Projetos de conteudo (escolher 1 para comecar)
```
7. Science Curiosity Shorts  (mais barato, mais rapido, batch de 30)
8. Bible Animation Pipeline  (maior potencial, mais complexo)
9. Animated Storytelling     (criativo, mas demora a crescer)
10. Home Exercise Course     (maior potencial financeiro, mas requer FASE 2)
```

### FASE 4: Maximizacao
```
11. Content Repurposing Department  (maximiza ROI de tudo que ja foi produzido)
12. Podcast & Audio Content         (canal de autoridade adicional)
```

---

## PARTE 4: AUTO-CRITICA GERAL

### O que eu (DeepSeek) POSSO TER DEIXADO PASSAR:

1. **CUSTO DE PRODUCAO HUMANO**: todo custo estimado e de API/providers. Nao
   considerei o TEMPO de Shin para revisar, aprovar, configurar. Isso e o
   maior custo real, mas invisivel nos meus documentos.

2. **MANUTENCAO**: cada departamento novo precisa ser mantido. Atualizar
   templates, renovar tokens, ajustar compliance. Nenhum documento fala
   sobre manutencao continua.

3. **FALHA DE API**: se ElevenLabs cair, o Bible Animation para. Se o
   YouTube API mudar, o Social Media quebra. Nao ha plano de fallback
   para dependencias externas.

4. **CAPACIDADE DA FABRICA**: a fabrica atual roda 107 demos em alguns
   minutos. Produzir 30 videos de Shorts + 1 episodio de Bible + posts
   de rede social TUDO AO MESMO TEMPO pode sobrecarregar. Nao pensei
   em limite de concorrencia.

5. **QUALIDADE vs VELOCIDADE**: Shin pode querer 30 Shorts por batch,
   mas a qualidade de cada um vai ser menor que de um video feito
   individualmente. Qual o trade-off aceitavel?

6. **DEPENDENCIA CIRCULAR**: ContentScheduler cria tasks para
   SocialMediaDistributor, que publica e reporta para BusinessIntelligence,
   que sugere mudancas para ContentScheduler. Existe risco de loop
   infinito de recomendacoes.

7. **TESTES**: cada departamento novo precisa de demo com assertions.
   Com 12 novos departamentos, seriam ~360 novas assertions. A regressao
   atual tem 107 demos com 1701 assertions. Quase dobraria o suite de
   testes. Shin e Codex precisam considerar o custo de manutencao dos
   testes.

8. **ONBOARDING DE SHIN**: com 12 departamentos, Shin vai precisar saber
   o que cada um faz, quando usar qual, como configurar. Sem documentacao
   clara, a fabrica vira uma "caixa preta" que Shin nao entende.

9. **MONETIZACAO REALISTA**: Shorts Fund paga centavos. O ebook de R$ 17
   precisa vender 60 unidades para pagar o dominio. O curso de R$ 47 precisa
   vender 12 unidades para pagar o trafego. Nao coloquei essas contas nos
   documentos — o ROI realista e importante.

10. **DECISAO MAIS DIFICIL**: qual projeto comecar PRIMEIRO? Minha
    recomendacao sincera: **Science Curiosity Shorts**. Por que?
    - Custo mais baixo ($0.055/video)
    - Batch de 30 = producao rapida
    - Nao requer API paga (MOCK funciona)
    - Nao requer novos departamentos (usa so os existentes + Scheduling)
    - Resultado visivel em 30 dias
    - Se falhar, o prejuizo e zero

---

## SUMARIO: O QUE CODEX DEVE REVISAR

1. `2026-07-13_MASTER_PROJECT_TREES.md` (este arquivo)
2. `2026-07-13_social_media_distribution.md`
3. `2026-07-13_business_intelligence.md`
4. `2026-07-13_email_marketing.md`
5. `2026-07-13_content_scheduling_and_calendar.md`
6. `2026-07-13_seo_and_organic_discovery.md`
7. `2026-07-13_content_repurposing.md`
8. `2026-07-13_podcast_and_audio_content.md`
9. `2026-07-13_landing_page_and_conversion.md`
10. `2026-07-13_bible_animation_pipeline.md`
11. `2026-07-13_home_exercise_course_funnel.md`
12. `2026-07-13_animated_storytelling_channel.md`
13. `2026-07-13_science_curiosity_shorts.md`

Codex deve verificar: preciso das arvores? Os riscos estao corretos? O caminho
critico faz sentido? As auto-criticas sao validas ou exageradas?
