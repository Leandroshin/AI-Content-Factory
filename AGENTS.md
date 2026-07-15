## Goal
- Implementar ciclo de vida completo dos Tool Adapters, infraestrutura para execução real (HTTP, Secrets, Providers, ExecutionMode), camadas de persistência/memória/qualidade, execução REAL dos adapters, e primeiro departamento real (Video Department)
- Consolidar padrão arquitetural com `core/departments/base/` para eliminar duplicação em futuros departamentos

## Constraints & Preferences
- NÃO alterar contratos públicos existentes; NÃO remover APIs; NÃO quebrar compatibilidade reversa; NÃO modificar CEO, DM, SE, ToolRuntime, CapabilityRegistry, ToolRegistry, Adapter Lifecycle, Persistence, OrganizationalMemory, QualityRuntime ou CompanyOrchestrator
- Toda implementação aditiva; frozen+slots; compileall + regressão completa obrigatórios
- NÃO copiar arquitetura/código do OpenAgent; NÃO criar dependência com OpenCode, MCP ou SDK externo
- NÃO criar novos runtimes genéricos — foco em construir departamentos reais da empresa
- ProductionEmployee (base) → VideoEditorEmployee (vídeo): departamentos herdam da camada base, nunca de SpecialistEmployee diretamente
- Priorizar reutilização, extensibilidade e baixo acoplamento
- LLMs externas que acessam apenas GitHub devem escrever propostas em `docs/external_llm_inbox/qwen/` usando os templates de `docs/external_llm_inbox/`; não devem editar `core/`, `demo_*.py`, providers, dependências ou outputs gerados

## Architecture — Base Department Layer

### Inheritance Chain
```
SpecialistEmployee                      (core/company/specialist_employee.py)
            └── ProductionEmployee              (core/departments/base/employee.py)  ← GENÉRICO
            ├── VideoEditorEmployee     (core/departments/video/employee.py) ← VÍDEO
            ├── AudioEngineerEmployee   (core/departments/audio/employee.py)
            ├── ImageDesignerEmployee   (core/departments/image/employee.py)
            ├── ScriptWriterEmployee    (core/departments/script/employee.py)
            └── ...
```

### What belongs to the Base Layer (`core/departments/base/`)
| Component | File | Purpose |
|---|---|---|
| `StageResult` | `pipeline.py` | Resultado de um stage individual (frozen+slots, genérico) |
| `ProductionPipeline` (ABC) | `pipeline.py` | Contrato abstrato: `advance()`, `stage`, `progress`, `stages_log`, `reset()` |
| `ProductionMetrics` | `models.py` | Métricas genéricas: stages, quality, duration (frozen+slots) |
| `ProductionEmployee` | `employee.py` | Herda SpecialistEmployee; gerencia pipeline, quality, metrics, state, execute_task genérico |

### What belongs to each Department
Cada departamento (ex: Video) fornece:
1. **Models específicos** — `VideoTask`, `AudioAsset`, `RenderProfile`, etc.
2. **Pipeline concreto** — estende `ProductionPipeline` com stages e handlers do domínio
3. **Employee específico** — herda `ProductionEmployee`, implementa `_build_pipeline()`, `receive_task()`, `analyze_capability_needs()`, hooks de output

### ProductionEmployee Hooks (override pattern)
Novos departamentos sobrescrevem apenas estes métodos:

| Hook | Quando override | Exemplo (Video) |
|---|---|---|
| `_check_reject(task)` | Rejeitar por departamento/workload | `"video" not in department` |
| `_build_pipeline(task)` | **Obrigatório** | `VideoProductionPipeline(video_task)` |
| `_estimate_duration(ctx)` | Calcular tempo estimado | Baseado em `video_type` e `duration_seconds` |
| `_build_output_from_stages(output, parts)` | Extrair output de stages específicos | Puxar `render` do RENDERING, `summary` do DELIVERING |
| `_build_metrics(completed, failed, output, duration)` | Métricas específicas | `assets_validated`, `render_format` |
| `_build_summary(success, parts)` | Mensagem final | `"Video production completed"` |
| `_run_quality_check(output)` | Campos adicionais de qualidade | `output_format`, `output_resolution` |
| `analyze_capability_needs()` | **Recomendado** | `VIDEO_EDITING`, `TRANSLATION`, etc. |
| `state()` | Adicionar campos ao dict | `video_capabilities`, `current_video_task` |

### Observability Hierarchy
```
ProductionSnapshot                  (genérico: task_id, stages, quality, duration)
    └── VideoProductionSnapshot     (específico: + video_type)
```

### How to Create a New Department
1. Create `core/departments/<name>/models.py` (frozen+slots)
2. Create `core/departments/<name>/pipeline.py` (extends ProductionPipeline)
3. Create `core/departments/<name>/employee.py` (extends ProductionEmployee, override hooks)
4. Create `core/departments/<name>/__init__.py`
5. Add snapshot(s) to `core/observability.py` (extends ProductionSnapshot if needed)
6. Create demo with assertions
7. compileall + regressão

## Progress
### Done
- **Adapter Lifecycle (FASE 1-3, 5, 7):** AdapterStatus, CredentialRequirement, OwnerGuidance, AdapterConfigStatus; 4 adapters concretos com validação real e owner guidance
- **ToolRuntime Credential Store:** `_credential_store`, `provide_credential()`, `get_credentials()`, `list_credential_keys()`
- **HTTP Layer (FASE 1):** `core/tools/http/` — HttpMethod, HttpRequest/HttpResponse, RetryPolicy/TimeoutPolicy/RateLimitConfig, HttpClient(ABC) + MockHttpClient
- **HTTP Errors (FASE 5):** 7 tipos de erro tipados (TimeoutError, RetryExhaustedError, RateLimitError, AuthExpiredError, QuotaExceededError, NetworkUnavailableError)
- **Secrets (FASE 2):** `core/tools/secrets/` — SecretKey, SecretValue (repr/str mascarado), SecretProvider(ABC) + MockSecretProvider
- **Providers (FASE 3):** 6 providers (Google, GitHub, OpenAI, ElevenLabs, Playwright, Telegram)
- **ExecutionMode (FASE 4):** MOCK (default) / REAL — injetável via setters, compatibilidade reversa
- **Observability:** HttpSnapshot (total_requests, retries, failures, auth, quota, rate_limit, timeouts, latency_ms, success_rate)
- **Execution Persistence:** `core/company/persistence.py` — PersistenceRuntime, ExecutionRecord, SessionState, CompanySnapshot, ExecutionEvidence (todos frozen+slots), persistência JSON em `.ai_company/{sessions,evidence,snapshots,logs}/`
- **Organizational Memory:** `core/company/organizational_memory.py` — OrganizationalMemoryRuntime, OrganizationalDocument com versionamento, CRUD completo
- **Conversation→Memory Timestamp:** `ConversationRuntime.create_memory_record()` preserva `message.timestamp` via `MemoryRecord.create_with_timestamp()`; remove falha intermitente em integração Conversation/Memory
- **Quality Loop:** `core/company/quality.py` — QualityRuntime, QualityRule, QualityResult, QualityReport, QualityIssue (rule-based, sem IA); 4 categorias built-in (completeness, quality, process, consistency)
- **Session Continuity:** carregar CompanySnapshot, reconstruir estado, reativar components, continuar do ponto parado
- **EventBus Integration:** 11 novos eventos (SessionCreated/Loaded/Saved, SnapshotCreated/Loaded, ExecutionPersisted/Restored, MemoryDocumentCreated/Updated/Archived, QualityValidationStarted/Finished)
- **Observability Snapshots:** 4 novos (PersistenceSnapshot, OrganizationalMemorySnapshot, QualitySnapshot, SessionSnapshot)
- **REAL Execution Adapters (FASE 1-3):** YouTubeAdapter, GitHubAdapter, ElevenLabsAdapter, PlaywrightAdapter, TelegramAdapter — `execute()` bifurca em MOCK (dados deterministicos) / REAL (chamadas HTTP reais via HttpClient + Provider + SecretProvider); SecretProvider injetado via `set_secret_provider()` (aditivo)
- **HTTP Events (FASE 4):** `core/tools/http/events.py` — 7 eventos (HttpRequestStarted, Completed, Failed, HttpRetry, HttpRateLimited, HttpAuthenticationFailed, HttpQuotaExceeded); ObservabilityProjector handlers auto-projetam HttpSnapshot
- **RateLimiter (FASE 5):** `core/tools/http/rate_limiter.py` — token-bucket com `acquire()`, `release()`, `retry_delay()` (exponential backoff + jitter), `with_retry()`, `available/remaining` properties
- **RealHttpClient:** `core/tools/http/real_client.py` — urllib-based, publica todos os 7 eventos HTTP, suporta retry automático e rate limiting
- **Base Department Layer:** `core/departments/base/` — StageResult, ProductionPipeline (ABC), ProductionMetrics, ProductionEmployee
- **Video Department — Models:** `core/departments/video/models.py` — VideoTask, VideoAsset, AudioAsset, ImageAsset, TimelineSegment, SubtitleSegment, RenderProfile, VideoProject (todos frozen+slots)
- **Video Department — Pipeline:** `core/departments/video/pipeline.py` — PipelineStage, VideoProductionPipeline (extends ProductionPipeline), 8 stages determinísticos
- **VideoEditorEmployee:** Herda ProductionEmployee (→ SpecialistEmployee), pipeline de 8 stages, 11 video-capabilities, QualityRuntime pós-render
- **HyperFrames Editorial Layer:** `EditorialQualityValidator` exige beat map, captions, proveniencia, audio prioritario e revisao visual; `LongFormRepurposingValidator` preserva capitulos e rejeita cortes curtos arbitrarios
- **HyperFramesRenderAdapter:** MOCK/REAL local via CLI oficial; REAL executa lint + check estrito antes de renderizar MP4 e mantem FFmpeg como encoder/fallback
- **Audio Department:** `core/departments/audio/` — AudioEngineerEmployee, pipeline deterministico, voz por `Capability.SPEECH_GENERATION`, export opcional de asset WAV/MP3 fisico
- **Image Department:** `core/departments/image/` — ImageDesignerEmployee, pipeline deterministico, export opcional de PNG fisico para capa/asset visual
- **Script Department:** `core/departments/script/` — ScriptWriterEmployee, roteiro, hook, CTA, variantes, export markdown e quality loop
- **Affiliate Deals Department:** `core/departments/affiliate_deals/` — AffiliateDealsEmployee, score deterministico de ofertas, copy estilo Telegram/WhatsApp manual, criativo, compliance de afiliado, plano de publicacao e funil Facebook warmup -> Telegram
- **Strategy Intelligence Department:** `core/departments/strategy_intelligence/` — fontes rastreaveis, padroes, evidencias e recomendacoes sem transformar transcricao bruta em ordem
- **TikTok Shop 8s Learning Pattern:** Strategy Intelligence reconhece Gemini Omni Flash/Google Flow, trata 8 segundos como experimento comparativo, bloqueia uso de rostos aleatorios do Pinterest e exige metricas proprias antes de aceitar alegacoes de receita
- **Gemini Omni Flash Provider:** chave validada por inventario oficial e guardada em `secrets/gemini.env`; `GeminiOmniVideoAdapter` oferece MOCK/REAL, output MP4 e bloqueio REAL obrigatorio por requests, segundos e custo (baseline oficial aproximado de USD 0.10/s em 720p)
- **Product Research Department:** `core/departments/product_research/` — normalizacao e shortlist de candidatos com score, sinais de marketplace e motivos auditaveis
- **Creative Review Department:** `core/departments/creative_review/` — decide manter, melhorar, substituir ou bloquear criativo antes da publicacao
- **Content Factory Workflow:** `core/content_factory/` — esteira concreta `Brief -> Script -> Audio -> Image -> Video -> Quality -> Observability`
- **Managed Content Workflow:** `ManagedContentProductionWorkflow` cria `ExecutivePlan`, registra funcionarios produtivos no `CompanyRuntime`, aciona `DepartmentManager` (`assign -> start -> complete`) para todas as tarefas e expõe progresso/saúde via `CompanyTaskRuntime`
- **Affiliate Commerce Workflow:** `core/content_factory/affiliate_workflow.py` conecta Strategy Intelligence -> Product Research -> Creative Review -> Affiliate Deals -> HITL Approval -> Telegram
- **HITL Approval Gateway:** aprovar, rejeitar, expirar e auditar decisoes antes de qualquer publicacao
- **Affiliate Approval Dashboard:** renderer HTML operacional para fila, score, compliance, preview e decisoes
- **Affiliate Dashboard Server:** backend local persistente com entrada manual, aprovacao, rejeicao e publicacao MOCK-safe
- **Factory Dashboard V2:** `apps/factory_dashboard/` agora usa areas independentes (Central, Oportunidades, Producao, Canais, Historico e Configuracoes), busca global, fila filtravel, fontes clicaveis por oportunidade, temas Operacional/Matrix persistidos e menu mobile com fechamento por backdrop
- **Gaming Radar Dashboard Intake:** endpoint aditivo `POST /api/intake/gaming`, desativado sem segredo, valida payload limitado e fontes HTTPS e faz upsert idempotente de oportunidades sem produzir, publicar ou gastar
- **Factory Dashboard Hosted:** Central de Comando publicada em modo privado no Sites com D1 persistente e `DASHBOARD_INTAKE_TOKEN` secreto ativo em `https://central-ai-content-factory.leandro-az-v.chatgpt.site`
- **Gaming Dashboard Bridge:** `GamingDashboardBridge` entrega somente decisoes `review` ao intake hospedado, ignora `no_news`, bloqueia por padrao e nao reenvia pautas aprovadas ou bloqueadas
- **Commerce Dashboard Bridge:** `CommerceDashboardBridge` envia produtos completos com link afiliado e previews de workflow ainda pendentes de HITL para `/api/intake/commerce`; itens incompletos ficam bloqueados e a decisao visual nunca libera publicacao
- **Product Dashboard Intake:** area privada `Produtos` recebe URL comum + link afiliado opcional, persiste a fila em D1 e mostra cinco etapas sem confundir coleta, Creative Review, afiliacao e decisao
- **Product Dashboard Worker:** `ProductDashboardWorker` busca a fila autenticada somente com opt-in, executa `ProductUrlIntake` uma vez por item e devolve evidencias; nunca fabrica link afiliado nem declara imagem aprovada
- **Product Queue Automation:** automacao Codex `Analisar fila de produtos` verifica a fila hospedada a cada hora, encerra silenciosamente quando vazia e mantem Creative Review/publicacao fora desta etapa
- **Product Research Missions:** painel recebe objetivo em linguagem simples, marketplace, periodo, preco, quantidade e canal; worker opt-in consulta catalogo somente leitura, usa o Product Research existente e devolve shortlist auditavel sem fabricar link afiliado, chamar provider pago ou publicar
- **Dashboard Production Queue:** aprovar uma oportunidade cria somente uma solicitacao MOCK persistida; `DashboardProductionWorker` usa o Script Department para devolver hook, roteiro, CTA e plano visual em `review`, mantendo audio, video, providers pagos e publicacao bloqueados
- **Production Review UX + Gates:** trabalhos da fila sao selecionaveis e exibem estado, canal, fontes e imagem honesta da marca; ofertas sem URL real/link afiliado e rotinas de monitoramento sem noticia concreta falham antes do roteiro; rascunhos de teste podem ser descartados sem publicar
- **FFmpegRenderAdapter:** `core/tools/adapters/ffmpeg_adapter.py` — MOCK deterministico e REAL via `ffmpeg/ffprobe`, com consumo de `audio_file_path`/`image_file_path` quando existem
- **ElevenLabs physical assets:** `ElevenLabsAdapter` escreve WAV deterministico em MOCK e grava bytes de audio no modo REAL quando `output_dir`/`write_file` sao passados
- **Provider Budget Guard:** `core/tools/provider_control.py` — ProviderBudget, ProviderPricing, ProviderBudgetGuard, decisões pre-flight e usage summary para bloquear REAL antes de HTTP quando faltar aprovação ou budget
- **Provider Control Center:** `core/tools/provider_settings.py` — estado de painel para providers: secret slots mascarados, modo MOCK/REAL, budgets, approval, snapshots e dashboard_state
- **Provider Panel UI:** `core/tools/provider_panel.py` — renderer HTML interativo alimentado por `ProviderControlCenter.dashboard_state()`, com chaves mascaradas, MOCK/REAL, busca, filtros, seleção de provider, budgets, aprovação e usage/custo
- **ElevenLabs REAL controlado:** `ElevenLabsAdapter` aceita `set_budget_guard()`; em REAL, `synthesize` só chama HTTP se owner approval + limites de requests/unidades/custo permitirem; erros HTTP reais viram `AdapterExecutionResult(success=False)` em vez de traceback
- **Telegram Publishing Adapter:** `core/tools/adapters/telegram_adapter.py` + `TelegramProvider` — `get_me`, `send_message` e `send_photo` em MOCK/REAL; envio REAL exige `bot_token`, `chat_id`, `approved=True` e budget guard; teste REAL enviou mensagem técnica para `@achadosbaratosBrasil` com `message_id=2`
- **Telegram Publication Queue:** o painel mostra a copy exata, exige confirmação comercial e uma aprovação final separada, fixa o destino em `@achadosbaratosBrasil` e registra status, horário e `message_id`; usa foto oficial quando a URL pública passa na validação, exige `#publi`, expira preço/pacote em duas horas, bloqueia link duplicado e publica no máximo um item aprovado por execução; WhatsApp permanece fora desta fase
- **HTTP secret redaction:** `RealHttpClient` mascara URLs do Telegram no formato `/bot<TOKEN>/...` antes de publicar eventos HTTP
- **Observability Snapshots:** ProductionSnapshot (genérico) + Video/Audio/Image/Script/AffiliateDeals production + department/detail snapshots — todos declarados em `core/observability.py`
- **Stage Counts in Snapshots:** `ProductionStageAdvanced` carrega `stages_completed`/`stages_failed`; handlers no ObservabilityProjector propagam para production snapshots genérico + departamental
- **Quality→Department Propagation:** `_task_department_map` no ObservabilityProjector mapeia task_id→departamento; `handle_quality_finished` atualiza snapshots específicos (video/audio/image_production.quality_passed)
- **Demo de Falha + Correção:** Pipeline failure (invalid video_type→stage fail) + Quality correction (strict rule→completeness fail→corrections) — ambos refletidos na observability
- **Primeiro short fisico:** `demo_short_video_factory.py` gera WAV mockado, PNG fisico e MP4 final de 60s; com FFmpeg local, o render consome os arquivos reais
- **Hotmart Webhook:** pacote `core/integrations/hotmart/` com autenticacao HOTTOK em tempo constante, payload v2, idempotencia por event ID, redacao de PII, fila local/Neon, retry/dead-letter e endpoint Vercel; configuracao oficial ativa e quatro testes Hotmart confirmados como `202 - Processado`
- **Audience Growth Planner:** `core/content_factory/audience_growth.py` conecta evidencias de tendencias a shortlist auditavel e `ContentBrief`; bloqueia riscos e exige aprovacao do owner antes da producao/publicacao TikTok
- **Gaming News Desk:** `core/content_factory/gaming_news_desk.py` deduplica o radar diario, rejeita rumor/fonte fraca/noticia antiga, retorna `no_news` quando nada merece pauta e conecta aprovados ao Audience Growth Planner; automacao Codex roda diariamente as 09:00
- **Kokoro Local TTS:** `KokoroTTSAdapter` oferece MOCK deterministico e REAL local isolado por subprocesso; usa pt-BR `lang_code="p"`, voz `pm_alex`, nao exige chave e nao importa dependencias opcionais no runtime principal
- **Segundo corte Fase Nova Games:** Meccha Chameleon 2.6.0 agora usa oito trechos de gameplay oficial, microcortes, zoom, cinco transicoes, motion graphics, voz Kokoro pt-BR e ambiente; V2 fisica de 40,90s em `output/fase_nova_games/`
- **Product URL Intake:** `core/content_factory/product_url_intake.py` recebe URLs fornecidas pelo owner, aceita apenas marketplaces HTTPS allowlisted, bloqueia hosts locais/privados/credenciais, extrai JSON-LD/Open Graph, registra hash/timestamp/evidencia, preserva fallback manual e entrega `ProductCandidate` ao fluxo completo de afiliados
- **Meta Ads Analytics Read-Only:** `MetaAdsAnalyticsAdapter` + `MetaMarketingProvider` oferecem apenas cinco operacoes GET (permissoes, contas, conta, campanhas e insights), campos/datas/limites allowlisted, token Bearer redigido, paginacao sem URLs sensiveis e bloqueio pre-HTTP de toda escrita; Provider Control Center exige token + limite + aprovacao
- **Meta Ads REAL Smoke:** `demo_meta_ads_real_smoke.py` e seco por padrao e limita o opt-in REAL a tres leituras; primeiro inventario REAL aguarda novo token `ads_read` em `secrets/meta_ads.env`
- **Factory Command Center:** `apps/factory_dashboard/` fornece cockpit Matrix responsivo com D1, fila HITL, decisoes persistentes, producao, canais, providers, custos e auditoria; aprovar producao nao publica nem gera custo
- **Second Media Approval Gate:** rascunhos aprovados entram em uma fila separada; Audio, Image e Video Departments geram planos tecnicos MOCK para nova revisao, com provider `not_called`, asset final `not_generated` e publicacao bloqueada
- **Affiliate onboarding real:** Amazon Associados ativo com ID registrado e Mercado Livre app criado com Client Credentials; segredos ficam em `secrets/`, fora do Git; status operacional em `docs/operations/AFFILIATE_PLATFORM_STATUS.md`
- **Mercado Livre Catalog Read-Only:** `MercadoLivreCatalogAdapter` oferece apenas quatro operacoes GET allowlisted (item, busca, multiget e categoria), token Bearer redigido, limites de consulta e bloqueio pre-HTTP de publicacao, mensagens, compras e vendas
- **Private Sites Worker Auth:** filas locais de produto e producao usam `OAI-Sites-Authorization` separado do token do intake; o painel permanece privado e os dois segredos ficam fora do Git
- **DeepSeek Safe Workspace:** `docs/external_llm_inbox/deepseek/00_START_HERE.md` fornece prompt reutilizavel, pastas permitidas, prototipos isolados e handoff obrigatorio para revisao do Codex
- **Media Provider Quote Gate:** `core/tools/provider_quote.py` compara o plano local gratuito e alternativas pagas antes de qualquer chamada; custo parcial ou provider sem preco mantem a execucao bloqueada
- **Narration-to-Evidence Visual Sync:** beats editoriais agora registram finalidade visual, aderencia a narracao e proveniencia; captura de tela, demonstracao de navegador e evidencia que nao corresponde a fala falham no quality gate
- **OmniRoute Quarantine Audit:** OmniRoute 3.8.48 foi instalado fora do projeto, limitado a `127.0.0.1`, com autenticacao obrigatoria e sem contas conectadas; o catalogo keyless OpenCode Free declara `tos: avoid` e permanece proibido
- **Affiliate Network Portfolio:** Strategy Intelligence separa redes digitais/CPA de alta comissao de marketplaces fisicos complementares; Digistore24 e o primeiro onboarding, seguido de Braip e ClickBank, sem excluir Amazon/Mercado Livre dos testes organicos
- **Regressão padronizada:** `python scripts/run_all_demos.py`; **114/114 demos, 0 falhas** em 2026-07-15; 57 demos reportaram numericamente 1844 assertions, 57 nao emitem total comparavel

## Key Decisions
- **Adapter lifecycle ≠ Tool lifecycle**: AdapterStatus independente de ToolStatus — complementares
- **ExecutionMode default MOCK**: Garante compatibilidade reversa total — adapters existentes continuam idênticos
- **SecretProvider injetado**: Adicionar `set_secret_provider()` ao AbstractToolAdapter é aditivo — não quebra contratos
- **RealHttpClient usa urllib**: Sem dependências externas (requests/httpx) — compatível com qualquer ambiente
- **Video Pipeline determinístico**: Stages avançam por state machine rule-based sem AI — QualityRuntime faz validação pós-render
- **ProductionEmployee como base**: Todos os departamentos herdam de ProductionEmployee, não de SpecialistEmployee diretamente — garante pipeline, quality, metrics consistentes
- **Hook pattern para departamentos**: `_build_pipeline()`, `_build_metrics()`, `_build_output_from_stages()`, `_run_quality_check()` — departamentos só sobrescrevem o que varia
- **Departamentos como padrão arquitetural**: Video Department é o template comprovado para Audio, Image, Research, Script, Publishing
- **CapabilityRegistry para descoberta**: Employee nunca cita ferramentas específicas, sempre capabilities (VIDEO_EDITING, STORAGE, BROWSER_AUTOMATION)
- **Render Profile via Context**: receive_task() extrai render_profile, timeline, assets, subtitles do dict context — sem quebrar contrato ReceivedTask
- **Quality→Department via task_department_map**: quality events não carregam departamento explicitamente; lookup por execution_id (que é o task_id) é suficiente e aditivo
- **Stage counts via event fields**: `stages_completed`/`stages_failed` adicionados a `ProductionStageAdvanced` — propagam para snapshots sem criar estado extra no projector
- **Snapshots populados por evento, não manualmente**: Handlers no ObservabilityProjector usam department do evento e `_task_department_map` para bifurcar em Video/Audio/Image
- **Assets fisicos opcionais**: departamentos continuam deterministicos e retrocompativeis; quando `output_dir`/`write_file` existem, Audio/Image materializam arquivos e Video/FFmpeg consomem por path
- **Edicao editorial em camadas**: HyperFrames compoe motion/captions/layout de forma deterministica, FFmpeg codifica e permanece fallback, e geracao de imagem/video continua provider opcional com proveniencia e budget
- **Long-form nao vira Short por crop**: capitulos e candidatos mantem timestamps da fonte, gancho, contexto e payoff; cada variante 9:16 passa por revisao propria
- **Affiliate Deals sem spam**: a vertical prepara curadoria, score, compliance, criativo e plano de publicacao; Telegram é o primeiro canal real controlado, e WhatsApp fica manual/semi-automatico nesta fase
- **Telegram REAL só com freios**: o adapter só publica em REAL com `approved=True`, `chat_id` explícito e budget configurado; token fica em SecretProvider/local ignored path, nunca em Git
- 0 dependências circulares, 0 violações core→engines

## Next Steps
1. **Digistore24 Affiliate onboarding** — criar a conta oficial, configurar recebimento e selecionar uma oferta verificavel; nenhum anuncio pago antes de validar termos, pagina, geografia, reembolso e link de promocao
2. **Affiliate portfolio validation** — comparar Digistore24, Braip e ClickBank por comissao, conversao, cookie, restricoes, payout e evidencia; MaxWeb, MediaScalers e BuyGoods entram depois da candidatura/aprovacao
3. **Meta Ads REAL authorization** — recuperar/gerar token `ads_read`, salvar fora do Git e executar o smoke de tres leituras; nenhuma permissao `ads_management`
4. **Gateway LLM oficial** — manter OmniRoute isolado e integrar somente providers com API/OAuth autorizado; OpenCode Free, cookies de sessao, anti-ban e pooling de contas ficam proibidos
5. **Metricas de negocio** — cliques, vendas, comissao, custo e ROI alimentando aprendizado aprovado
6. **Landing page e compliance** — dominio, privacidade, termos, disclosure e eventos de conversao
7. **Aprovar voz editorial** — Kokoro local e gratuito e o baseline atual; ElevenLabs permanece opcional apos regularizar `payment_issue` e comparar qualidade/custo
8. **Imagem provider real** — escolher por custo, qualidade e licenca antes de texto-para-video
9. **2.5D operacional** — visualizar uma operacao real ja funcional, sem substituir o dashboard

## Critical Context
- **compileall**: ✅ (core/ compila sem erros)
- **Regressão atual**: **114/114 demos, 0 falhas**; 1844 assertions explicitamente reportadas por 57 demos
- **Prova da fila de producao:** `demo_dashboard_production_worker.py` valida 20 assertions: opt-in, autenticacao, modo MOCK, evidencia preservada, Script Department real, rascunho para revisao e ausencia de chamadas de audio, video ou publicacao
- **Prova do dashboard**: lint, build vinext, teste Node, D1 local, GET da API, sincronizacao, filtros, menu mobile e QA visual em 1440x900 e 390x844 passaram; Sites privado, D1 hospedado e intake secreto foram publicados em 2026-07-13
- **RealHttpClient** com urllib — sem requests/httpx, sem dependências externas
- **RateLimiter** com token-bucket, exponential backoff + jitter, thread-safe
- **Base Layer comprovada**: ProductionEmployee + ProductionPipeline + StageResult como template; Video, Audio, Image e Script funcionando
- **Arquitetura extensível**: Novo departamento = ~4 arquivos (models, pipeline, employee, __init__) + snapshots + demo
- **Observability real agora**: Snapshots populados por eventos de produção; handlers em `core/observability.py`; 3 novos eventos em `core/events/domain_events.py`; qualidade propaga para snapshots específicos via `_task_department_map`
- **Stages tracking**: `ProductionStageAdvanced` carrega `stages_completed`/`stages_failed` — snapshots refletem contagem acumulada
- **Failure + Correction na demo**: Cenário de falha de pipeline (invalid video_type) + falha de qualidade (missing required field) + correção via QualityRuntime
- **Prova fisica atual**: `output/short_video_factory/` contem MP4s gerados; o demo mais recente validou WAV + PNG + MP4 final com FFmpeg consumindo ambos
- **Prova HyperFrames REAL**: `examples/hyperframes/editorial_smoke/index.html` passou lint e check estrito e gerou MP4 vertical fisico via `HyperFramesRenderAdapter` (603697 bytes)
- **Prova editorial Fase Nova Games**: segundo corte Meccha Chameleon passou lint/check estrito, 43/43 contrastes e QA de mídia; gerou H.264+AAC de 40,90s com oito trechos de gameplay, voz Kokoro, motion graphics e sem IDs técnicos públicos
- **Prova Kokoro local**: `demo_kokoro_tts_adapter.py` valida 28 assertions sem download/modelo; smoke REAL local gerou seis WAVs pt-BR a 24 kHz para a V2
- **Prova gerencial atual**: `demo_managed_content_factory_workflow.py` valida plano executivo + DM + CompanyTaskRuntime + produção real de departamentos; 18/18 tarefas gerenciais concluídas e progresso 100%
- **Prova de provider controlado**: `demo_provider_budget_guard.py` valida aprovação obrigatória, budget de caracteres/custo/requests, bloqueio antes de HTTP e usage summary; sem chamada externa
- **Prova de config/painel provider**: `demo_provider_control_center.py` valida ProviderControlCenter, chave mascarada, modo REAL, aprovação com budget explícito, wiring no ElevenLabs e dashboard_state
- **Prova visual do painel provider**: `demo_provider_panel_ui.py` gera `output/provider_control_panel/index.html` com três providers, chave mascarada, modo MOCK/REAL, busca, filtros, seleção, budget, aprovação e usage/custo; sem chamada externa
- **Prova REAL opt-in ElevenLabs**: `demo_elevenlabs_real_smoke.py` roda seco na regressão; o smoke antigo registrou 401 sem expor a chave. A chave restrita atual valida leitura de vozes, mas TTS retorna `payment_issue` ate a fatura ser regularizada
- **Prova Affiliate Deals**: `demo_affiliate_deals_department.py` valida 79 assertions: oferta forte `post_now` pendente de aprovacao, oferta fraca `skip`/rejeitada, oferta sem affiliate URL bloqueada por compliance, funil Facebook warmup -> Telegram e observability `deal_metrics`
- **Prova Telegram REAL controlado**: `demo_telegram_publishing_adapter.py` valida 40 assertions em MOCK/MockHttpClient; smoke REAL local validou `@achados_baratos_br_bot` via `getMe` e enviou mensagem técnica para `@achadosbaratosBrasil` (`message_id=2`) com token fora do Git
- **Prova da fila Telegram**: `demo_telegram_publication_worker.py` valida 23 assertions: opt-in, intake autenticado, destino allowlisted, copy curta com `#publi`, foto oficial, callback `sent` com `message_id`, bloqueio de canal desconhecido e rejeicao de oferta expirada antes da API; nenhum envio REAL ocorre na regressao
- **Correção Conversation/Memory**: `demo_conversation_memory_integration.py` valida timestamp preservado sem depender de igualdade acidental de `time.time()`
- 0 dependências circulares; nenhuma classe existente foi modificada (exceto adições aditivas em domain_events.py, base/employee.py, observability.py)

## Relevant Files
### Base Department Layer
- `core/departments/base/__init__.py`: exports públicos
- `core/departments/base/pipeline.py`: StageResult (frozen+slots), ProductionPipeline (ABC)
- `core/departments/base/models.py`: ProductionMetrics (frozen+slots, genérico)
- `core/departments/base/employee.py`: ProductionEmployee — pipeline flow, quality, metrics, hooks

### Video Department
- `core/departments/video/__init__.py`: exports do Video Department
- `core/departments/video/models.py`: VideoTask, VideoAsset, AudioAsset, ImageAsset, TimelineSegment, SubtitleSegment, RenderProfile, VideoProject
- `core/departments/video/pipeline.py`: PipelineStage, VideoProductionPipeline (extends ProductionPipeline), 8 stages + helpers
- `core/departments/video/employee.py`: VideoEditorEmployee (extends ProductionEmployee) — VideoCapability, ProductionMetrics (vídeo), 11 domain capabilities, resolve render input files fisicos
- `core/departments/video/editorial_quality.py`: beat map, captions, quality gate, capitulos e validacao long-form -> Shorts

### Affiliate Deals Department
- `core/departments/affiliate_deals/models.py`: MarketplaceSource, PriceSnapshot, CouponInfo, AffiliateLink, ProductOffer, DealScore, OfferMessage, OfferCreative, PublishingPlan, ComplianceCheck, AudienceGrowthPlan, FunnelMetrics, DealCampaign, AffiliateDealTask
- `core/departments/affiliate_deals/scoring.py`: score deterministico por desconto, confianca, cupom, urgencia, faixa de preco e risco
- `core/departments/affiliate_deals/compliance.py`: disclosure obrigatorio, link afiliado, bloqueio de WhatsApp automatico e termos enganosos
- `core/departments/affiliate_deals/formatter.py`: mensagem compacta estilo Telegram/WhatsApp manual com disclosure
- `core/departments/affiliate_deals/pipeline.py`: AffiliateDealsPipeline com 12 stages produtivos
- `core/departments/affiliate_deals/employee.py`: AffiliateDealsEmployee (extends ProductionEmployee)

### External LLM Inbox
- `docs/external_llm_inbox/README.md`: regras para Qwen/outros LLMs escreverem propostas sem quebrar o projeto
- `docs/external_llm_inbox/IDEA_TEMPLATE.md`: template de ideia/vertical
- `docs/external_llm_inbox/EMPLOYEE_SPEC_TEMPLATE.md`: template de funcionario
- `docs/external_llm_inbox/DEPARTMENT_SPEC_TEMPLATE.md`: template de departamento
- `docs/external_llm_inbox/qwen/`: pasta de entrada para arquivos novos vindos do Qwen

### Infraestrutura
- `apps/factory_dashboard/`: Central de Comando web responsiva, privada e hospedavel pelo Sites
- `apps/factory_dashboard/app/api/`: leitura da fila e decisoes HITL persistidas no D1
- `docs/dashboard/CENTRAL_DE_COMANDO.md`: guia visual de uso no desktop e celular
- `core/company/quality.py`: QualityRuntime (regras, validação, correções)
- `core/conversation/runtime.py`: bridge Conversation→Memory preservando timestamp original da mensagem
- `core/observability.py`: ProductionSnapshot + Video/Audio/Image production/department/detail snapshots + task_department_map + qualité→dept propagation
- `core/tools/http/events.py`, `rate_limiter.py`, `real_client.py`
- `core/tools/adapters/elevenlabs_adapter.py`: MOCK/REAL de TTS + escrita opcional de audio fisico
- `core/tools/adapters/kokoro_adapter.py`: MOCK/REAL local de TTS via runner Python isolado, sem chave de API
- `core/tools/adapters/meta_ads_adapter.py`: Meta Ads somente leitura, GET allowlisted, token redigido e bloqueio de escrita antes do HTTP
- `core/tools/adapters/mercado_livre_adapter.py`: catalogo Mercado Livre somente leitura, GET allowlisted, OAuth Bearer redigido e bloqueio de toda escrita antes do HTTP
- `core/tools/providers/meta_marketing.py`: contrato versionavel da Meta Marketing API
- `core/tools/providers/mercado_livre.py`: contrato da API Mercado Livre brasileira
- `core/tools/adapters/gemini_omni_video_adapter.py`: Gemini Omni Flash MOCK/REAL com MP4 fisico e bloqueio pago por aprovacao, segundos, requests e custo
- `core/tools/providers/gemini.py`: contrato versionavel da Gemini API com autenticacao em header
- `scripts/kokoro_tts_runner.py`: protocolo JSON stdin/stdout para Kokoro pt-BR e WAV 24 kHz
- `core/tools/adapters/telegram_adapter.py`: Telegram Bot API MOCK/REAL com aprovação, `chat_id`, budget guard e limite de 4096 caracteres
- `core/tools/providers/telegram.py`: Provider contract da Telegram Bot API
- `core/tools/provider_control.py`: budget guard e usage summary para providers externos
- `core/tools/provider_settings.py`: estado de painel para providers, secrets mascarados, budgets, approval, snapshots e ligação com adapters
- `core/tools/provider_panel.py`: renderer HTML interativo para preview do painel de APIs/custos
- `core/tools/adapters/ffmpeg_adapter.py`: render local MOCK/REAL + consumo opcional de audio/imagem fisicos
- `core/tools/adapters/hyperframes_adapter.py`: composicao HTML-to-video MOCK/REAL com lint + check antes do render
- `core/content_factory/workflow.py`: orquestra departamentos e propaga paths fisicos entre audio, imagem e video
- `core/content_factory/managed_workflow.py`: ponte concreta com ExecutivePlan, DepartmentManager e CompanyTaskRuntime
- `core/content_factory/affiliate_workflow.py`: fluxo integrado da estrategia ate aprovacao/publicacao
- `core/content_factory/product_url_intake.py`: coleta controlada de uma URL, evidencia estruturada, fallback manual e conversao para `ProductCandidate`
- `core/content_factory/commerce_dashboard_bridge.py`: ponte review-only de Product URL Intake/Affiliate Workflow para o painel hospedado
- `core/content_factory/product_dashboard_worker.py`: worker controlado da fila visual para coleta de evidencia e devolucao segura
- `core/content_factory/gaming_dashboard_bridge.py`: ponte review-only do radar para o intake privado hospedado
- `core/content_factory/affiliate_dashboard.py`: renderer da fila operacional
- `core/content_factory/affiliate_dashboard_server.py`: persistencia e API local da fila HITL
- `core/events/domain_events.py`: ProductionStarted, ProductionStageAdvanced (+stages_completed/failed), ProductionCompleted, QualityValidationStarted/Finished
- `scripts/run_all_demos.py`: executor padronizado, remove opt-ins REAL, aplica timeout e grava relatorio JSON local ignorado pelo Git

### Demos
- `demo_tool_runtime.py`: 38 assertions
- `demo_adapter_execution.py`: 20 assertions
- `demo_adapter_lifecycle.py`: 49 assertions
- `demo_capability_resolver.py`: 32 assertions
- `demo_persistence.py`: 26 assertions
- `demo_organizational_memory.py`: 37 assertions
- `demo_quality_loop.py`: 34 assertions
- `demo_session_recovery.py`: 30 assertions
- `demo_real_adapters.py`: 24 assertions
- `demo_video_department.py`: 56 assertions
- `demo_audio_department.py`: 56 assertions
- `demo_image_department.py`: 57 assertions
- `demo_department_observability.py`: 62 assertions
- `demo_content_factory_workflow.py`: 43 assertions
- `demo_ffmpeg_render_adapter.py`: 14 assertions
- `demo_elevenlabs_audio_asset.py`: 11 assertions
- `demo_kokoro_tts_adapter.py`: 28 assertions, prova contrato MOCK/REAL local sem baixar modelo na regressao
- `demo_product_url_intake.py`: 39 assertions, prova extracao, bloqueios de URL/host, fallback manual, Adidas multiloja e URL -> HITL sem publicacao automatica
- `demo_commerce_dashboard_bridge.py`: 21 assertions, prova gates de produto/link afiliado/HITL e entrega visual sem publicar
- `demo_product_dashboard_worker.py`: 21 assertions, prova fila -> coleta -> painel, link afiliado ausente e Creative Review pendente sem publicacao
- `demo_meta_ads_read_only.py`: 56 assertions, prova provider/painel, GET de contas/campanhas/insights, limites, redacao e bloqueio de escrita
- `demo_meta_ads_real_smoke.py`: 3 assertions em dry-run; opt-in REAL limitado a permissoes, conta e campanhas com relatorio redigido
- `demo_gemini_omni_video_adapter.py`: 18 assertions, prova chave mascarada, MOCK padrao, bloqueio pre-HTTP, budget, REST `steps`, 9:16 e MP4 fisico sem chamada paga
- `demo_gaming_dashboard_bridge.py`: 21 assertions, prova bridge desativada por padrao, review-only, no-news skip, token no header e payload auditavel
- `demo_short_video_factory.py`: 43 assertions, prova WAV + PNG + MP4 fisico
- `demo_editorial_video_quality.py`: 28 assertions, prova quality gate, rejeicao de crop arbitrario e adapter HyperFrames
- `demo_managed_content_factory_workflow.py`: 38 assertions, prova DM + CompanyTaskRuntime + 18/18 tarefas gerenciais + produção concreta
- `demo_provider_budget_guard.py`: 26 assertions, prova provider REAL controlado sem gastar API
- `demo_provider_control_center.py`: 32 assertions, prova backend de configuração/painel de providers
- `demo_provider_panel_ui.py`: 30 assertions, gera preview HTML interativo local do painel de APIs/custos
- `demo_elevenlabs_real_smoke.py`: 3 assertions em dry-run; opt-in REAL com teto de gasto e relatório redigido
- `demo_affiliate_deals_department.py`: 79 assertions, prova Affiliate Deals + funil de crescimento + compliance + observability
- `demo_telegram_publishing_adapter.py`: 40 assertions, prova Telegram Bot API seguro + mensagem Affiliate Deals pronta para publicação
- `demo_hitl_approval_gateway.py`: prova bloqueio, aprovacao, rejeicao e auditoria HITL
- `demo_product_research_department.py`: prova shortlist e score de pesquisa
- `demo_strategy_intelligence_department.py`: 29 assertions, prova extracao de padroes, evidencias e aprendizado seguro do formato TikTok Shop de 8 segundos
- `demo_creative_review_department.py`: prova gate de qualidade do criativo
- `demo_affiliate_factory_workflow.py`: prova Strategy -> Research -> Creative -> Deals -> HITL -> Telegram
- `demo_affiliate_approval_dashboard.py`: prova estado e UI da fila de aprovacao
- `demo_affiliate_dashboard_server.py`: prova backend, persistencia e entrada manual
