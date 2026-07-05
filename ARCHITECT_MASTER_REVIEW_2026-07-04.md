# Architect Master Review - 2026-07-04

## Contexto

Esta revisao foi feita depois de reler:

- `conversa inteira.txt`;
- `AGENTS.md`;
- camada de departamentos da AI Content Factory;
- memorias centrais do `New project`;
- transcript local sobre Graphify;
- documentacao oficial do Graphify.

## Conclusao principal

A AI Content Factory esta no caminho certo, mas deve mudar de fase.

Antes, fazia sentido criar infraestrutura.

Agora, o foco deve ser producao real.

## Marco novo

Foi criada a primeira camada concreta de workflow de conteudo:

`core/content_factory/`

Arquivos:

- `core/content_factory/models.py`;
- `core/content_factory/workflow.py`;
- `core/content_factory/__init__.py`.

Fluxo comprovado:

Brief -> Script -> Audio -> Image -> Video -> Quality -> Observability.

Resultado:

- Script gera roteiro;
- Audio gera voiceover deterministico;
- Image gera capa vertical;
- Video monta timeline, assets, legenda e render mp4 vertical;
- QualityRuntime valida os quatro departamentos;
- ObservabilityProjector registra sucesso departamental;
- `demo_content_factory_workflow.py` consome `ContentProductionWorkflow`;
- Audio resolve `Capability.SPEECH_GENERATION` via `ToolRegistry` e executa
  ElevenLabs em MOCK quando registrado;
- metadata de voz (`voice_id`, `model_id`, `voice_settings`) atravessa o
  workflow ate o adapter;
- `AudioEngineerEmployee` libera a ferramenta em `finally` para evitar tool presa
  em chamada real com erro;
- `ElevenLabsAdapter` materializa WAV em MOCK e grava bytes de audio em REAL
  quando `output_dir`/`write_file` sao passados;
- Audio propaga `asset_file_path`/`physical_asset` quando a narracao vira arquivo;
- Image exporta PNG fisico opcional para capa/asset visual;
- `FFmpegRenderAdapter` foi criado como adapter local de render, com MOCK e REAL
  via `ffmpeg/ffprobe`;
- `Capability.VIDEO_RENDERING` separa render de edicao/upload;
- `VideoEditorEmployee` resolve render por capability de forma opcional;
- `VideoEditorEmployee` descobre `audio_file_path`/`image_file_path` em assets
  fisicos e o FFmpeg consome esses inputs reais no MP4 final;
- `demo_content_factory_workflow.py` agora tem 43 assertions;
- `demo_ffmpeg_render_adapter.py` tem 14 assertions, incluindo render REAL
  temporario;
- `demo_short_video_factory.py` foi criado como primeiro passe pratico de video
  curto de 60s, com roteiro, WAV fisico mockado por capability, PNG fisico,
  timeline e MP4 fisico quando `ffmpeg/ffprobe` estao no PATH;
- `demo_elevenlabs_audio_asset.py` foi criado para provar escrita de WAV em MOCK
  e escrita de bytes no caminho REAL simulado por `MockHttpClient`, sem gastar
  creditos;
- `ManagedContentProductionWorkflow` foi criado como ponte concreta com o
  `DepartmentManager` e `CompanyTaskRuntime`: ele cria `ExecutivePlan`, registra
  funcionarios produtivos no runtime operacional, executa `assign -> start ->
  complete` para todas as tarefas gerenciais e preserva a esteira concreta de
  departamentos;
- `demo_managed_content_factory_workflow.py` validou 18/18 tarefas gerenciais,
  progresso 100%, health/progress de empresa e produção final do pacote;
- `ProviderBudgetGuard` foi criado para uso REAL controlado: aprovação do dono,
  limite de requests, limite de unidades/caracteres, limite de custo estimado e
  bloqueio antes de qualquer HTTP;
- `ElevenLabsAdapter` agora aceita `set_budget_guard()` e respeita essa trava em
  `ExecutionMode.REAL` para TTS;
- `demo_provider_budget_guard.py` validou 26 assertions sem chamada externa;
- `ProviderControlCenter` foi criado como estado de painel: secret slots
  mascarados, modo MOCK/REAL, budgets, approval explícito, snapshots,
  `dashboard_state()` e ligação com ElevenLabs;
- `demo_provider_control_center.py` validou 32 assertions sem chamada externa;
- `ProviderPanelRenderer` foi criado em `core/tools/provider_panel.py`, gerando
  um HTML interativo a partir do `ProviderControlCenter.dashboard_state()`;
- `demo_provider_panel_ui.py` validou 30 assertions e gerou
  `output/provider_control_panel/index.html` com providers, chave mascarada,
  modo MOCK/REAL, busca, filtro de bloqueados, seleção, budgets, aprovação e
  uso/custo estimado, sem chamada externa;
- `demo_elevenlabs_real_smoke.py` foi criado como teste REAL opt-in: na
  regressão roda seco; com `AI_COMPANY_RUN_REAL_ELEVENLABS=1`, tentou uma
  chamada REAL de 14 caracteres com teto local de US$0.002, recebeu
  `AuthExpiredError`/401 da chave local atual e registrou relatório redigido em
  `output/elevenlabs_real_smoke/report.json`;
- `core/departments/affiliate_deals/` foi criado como nova vertical
  **Affiliate Deals Factory**: score deterministico de ofertas, copy estilo
  Telegram/WhatsApp manual, criativo, compliance de afiliado, plano de
  publicacao e funil Facebook warmup -> Telegram;
- `demo_affiliate_deals_department.py` validou 79 assertions: oferta forte
  `post_now` pendente de aprovacao, oferta fraca `skip`/rejeitada, oferta sem
  affiliate URL bloqueada por compliance e observability `deal_metrics`;
- prompt visual para o GPT da Web salvo em
  `00_CENTRAL_CONTEXT/05_PROMPT_VISUAL_AI_CONTENT_FACTORY.md`;
- imagens conceituais do GPT da Web revisadas: as telas de dashboard,
  tarefas/pipeline, APIs/custos, funcionário, aprovação e mobile estão boas
  como direção; as 4 imagens novas do ambiente 2.5D ficaram boas como blueprint
  estático, mas o movimento dos funcionários precisa ser implementado no app;
- regressao completa: 83 demos, 3335 assertions, 0 falhas.

## Nao fazer agora

- criar mais runtimes genericos sem necessidade;
- copiar arquitetura externa;
- mover fisicamente projetos;
- rodar Graphify no disco inteiro;
- construir editor de video do zero;
- criar TTS do zero;
- criar transcricao do zero;
- prometer publicacao automatica em plataformas sem API oficial validada.

## Fazer agora

1. consolidar contexto mestre;
2. usar Graphify com escopo pequeno;
3. manter Obsidian como mapa humano;
4. escolher adapters reais por capacidade, nao por hype;
5. criar `TelegramPublishingAdapter` como primeiro canal real da Affiliate Deals Factory;
6. atualizar a chave ElevenLabs e repetir o smoke REAL com teto pequeno.
7. usar as imagens 2.5D como blueprint para a interface animada dos
   funcionários.

## Radar novo de ideias e APIs

As ideias novas do Shin foram registradas sem virar codigo imediato:

`C:/Users/Shin/Documents/New project/00_CENTRAL_CONTEXT/04_RADAR_IDEIAS_E_APIS_2026-07-04.md`

Inclui:

- estrategia de APIs e custos;
- configuracoes futuras de providers/secrets/budgets;
- WhatsApp por voz com ElevenLabs/Meta como possivel produto Luma Secretaria;
- Polymarket/mercados como futuro departamento de pesquisa, sem operacao
  automatica com dinheiro real;
- uso futuro de automacoes do Codex;
- decisao sobre Impeccable para frontend;
- onde abrir novas sessoes.

## Status do Graphify

Graphify foi instalado com escopo de projeto apenas em:

`C:/Users/Shin/Documents/New project/00_CENTRAL_CONTEXT/graphify-corpus`

Isso criou as instrucoes e hooks locais do Codex nesse corpus.

Depois foi gerada uma semente segura do grafo, sem API externa:

- 34 nos;
- 48 conexoes;
- 6 comunidades;
- `graphify-out/graph.html`;
- `graphify-out/GRAPH_REPORT.md`;
- `graphify-out/graph.json`.

Depois o grafo foi expandido para o estado atual:

- 134 nos;
- 88 conexoes;
- 47 comunidades;
- diagnostico limpo;
- consulta recupera WhatsApp por voz, Polymarket, voz por capability,
  `demo_short_video_factory`, o preview HTML interativo do painel de providers
  e o smoke REAL da ElevenLabs.

Esse grafo nao e uma varredura completa. Ele e um mapa inicial para preservar o
fio da meada entre Shin, os projetos principais, AI Content Factory,
ferramentas prontas, Graphify, Obsidian e a regra da prova real.

## Decisao sobre ferramentas prontas

Usar ferramentas prontas e correto.

O projeto deve criar adapters e contratos, nao reinventar:

- FFmpeg;
- ElevenLabs;
- Whisper/Groq/faster-whisper;
- Playwright/browser automation;
- APIs oficiais;
- storage.

## Regra de continuidade

Cada nova sessao deve consultar:

- `New project/00_CENTRAL_CONTEXT/00_LEIA_PRIMEIRO_CONTEXTO_MESTRE.md`;
- `New project/00_CENTRAL_CONTEXT/01_MAPA_DOS_PROJETOS.md`;
- `New project/00_CENTRAL_CONTEXT/02_AI_CONTENT_FACTORY_ARQUITETO_MESTRE.md`;
- `New project/00_CENTRAL_CONTEXT/03_GRAPHIFY_E_OBSIDIAN_PLANO.md`.
- `New project/00_CENTRAL_CONTEXT/04_RADAR_IDEIAS_E_APIS_2026-07-04.md`.
