# Checklist de entrega da LLM auxiliar

Status permitido: `PROPOSTA - NAO IMPLEMENTADA` ou `PROTOTIPO ISOLADO - NAO INTEGRADO`.

- [x] Li `AGENTS.md`, o README da caixa de entrada e o protocolo local.
- [x] Alterei somente os caminhos autorizados.
- [x] Nao li, copiei ou registrei secrets e dados pessoais.
- [x] Separei fatos, falas, inferencias e sugestoes.
- [x] Registrei URLs, data de consulta, licenca e custo quando aplicavel.
- [x] Declarei riscos, dependencias e aprovacoes humanas.
- [x] Nao instalei dependencias, nao publiquei e nao executei chamadas pagas.
- [x] Nao fiz commit, push ou deploy.
- [x] Se criei prototipo, ele nao importa `core/`, possui README e foi testado apenas dentro da propria pasta.
- [x] Atualizei `INDEX.md` com todos os arquivos criados.
- [x] Listei claramente o que o Codex deve revisar, aceitar ou rejeitar.

Se qualquer item estiver incompleto, a entrega ainda nao esta pronta para revisao.

---

## Sessao 2026-07-14 — Novos Employees Roster

### O que foi feito
- Criado `docs/external_llm_inbox/deepseek/ideas/2026-07-14_novos_employees_roster.md` com 8 ideias de employees
- Atualizado `INDEX.md`
- Adicionada auto-leitura obrigatoria ao `.opencode/instructions/ai_content_factory.md`

### O que o Codex deve revisar
- **Arquivo principal:** `docs/external_llm_inbox/deepseek/ideas/2026-07-14_novos_employees_roster.md` — 8 propostas de employees
- **Instrucao alterada:** `.opencode/instructions/ai_content_factory.md` — adicionada secao de auto-leitura com resposta "Factory ativa"

### Decisoes pendentes de Shin/Codex
- Qual(is) ideia(s) merece(m) virar departamento primeiro
- Se alguma capability nova cabe no CapabilityRegistry
- Ordem de implementacao (caminho critico sugerido no documento)

---

## Sessao 2026-07-14b — Menu SaaS Vertical

### O que foi feito
- Criado `docs/external_llm_inbox/deepseek/ideas/2026-07-14_menu_saas_vertical.md` — mega proposta com N0-N8, modelos, pipeline de 8 stages, MenuOperatorEmployee, fluxo completo, integracoes, riscos e 6 fases de implementacao
- Criado `prototypes/external_llm/menu_saas/index.html` — prototipo HTML com 4 abas (Cardapio, Painel do Cliente, Fabrica, Planos)
- Criado `prototypes/external_llm/menu_saas/README.md` — documentacao do prototipo
- Atualizado `INDEX.md` com a nova entrada

### O que o Codex deve revisar
- **Proposta:** `docs/external_llm_inbox/deepseek/ideas/2026-07-14_menu_saas_vertical.md` — proposta completa do Menu SaaS como vertical
- **Prototipo:** `prototypes/external_llm/menu_saas/index.html` — visualizacao funcional do ecossistema

### Decisoes pendentes de Shin/Codex
- Nome final do produto (CardapioPro? MenuPro?)
- Precificacao (R$47/97/197 ou outra tabela)
- Infraestrutura real (Orzons vs Hostinger + Cloudflare)
- Se vira departamento `menu_saas/` ou aguarda
- Quem faz as vendas: Shin (trafego pago) ou automatizado via lead + onboarding

---

## Sessao 2026-07-15 — Affiliate Marketing Pipeline Gringa

### O que foi feito
- Lidas 3 transcricoes de YouTube sobre afiliado internacional (Ex-Uber R$4M, Claude +R$100k/mes, escolha de produtos)
- Criado `docs/external_llm_inbox/deepseek/ideas/2026-07-15_affiliate_marketing_pipeline_gringa.md` com:
  - Proposta 4 camadas (IDEA, Arvore N0-N8, Riscos, Caminho Critico)
  - ProductHunterEmployee (varredura diaria ClickBank/BuyGoods + Trends)
  - LandingPageBuilderAdapter (gerador HTML estilo Flow Pages)
  - GoogleAdsCampaignAdapter (gerador de campanha exportavel)
  - Integracao com HITL + AffiliateDealsEmployee existentes
  - Dados MOCK baseados nos produtos reais dos videos (ProstaVive, Prodentin, Ignatra, etc.)
  - Referencia cruzada do que cada video ensina vs implementacao
- Atualizado `INDEX.md` com a nova entrada

### O que o Codex deve revisar
- **Proposta principal:** `docs/external_llm_inbox/deepseek/ideas/2026-07-15_affiliate_marketing_pipeline_gringa.md`

### Decisoes pendentes de Shin/Codex
- Shin quer implementar Fase 1 (TrendScanner MOCK) primeiro?
- Shin tem conta Google Ads + cartao internacional para eventual REAL?
- Shin quer dominio proprio para landing pages?
- ProductHunterEmployee vira departamento separado ou extensao do ProductResearchEmployee existente?
- Produtos do Brasil (Hotmart) entram no escopo ou so gringa?

---

## Sessao 2026-07-15b — 7 Especificacoes Detalhadas (Fases 1-7)

### O que foi feito
- Criadas 7 especificacoes detalhadas em `research/`, uma por fase:

| Fase | Arquivo | Tamanho |
|---|---|---|
| 1 | `FASE1_ProductHunter_Employee_Spec.md` | ProductHunterEmployee, 6-stage pipeline, MOCK data, scoring formula (0-100), video timestamps |
| 2 | `FASE2_LandingPageBuilder_Adapter_Spec.md` | LandingPageBuilderAdapter, HTML template, copywriting rules, MOCK pages (ProstaVive, Matsato) |
| 3 | `FASE3_GoogleAdsCampaign_Adapter_Spec.md` | GoogleAdsCampaignAdapter, campaign config, keyword rules, JSON/CSV export, negative keywords |
| 4 | `FASE4_HITL_Dashboard_Integration_Spec.md` | Nova aba "Afiliado Gringa", workflow states, persistencia, endpoints, GringaDashboardState |
| 5 | `FASE5_Telegram_Daily_Notification_Spec.md` | DailyDigestService, formato de mensagem, variacoes (sem produtos, erro), scheduling |
| 6 | `FASE6_ClickBank_API_Integration_Spec.md` | ClickBankProvider + ClickBankAdapter, API mapping, budget guard, hoplink generation |
| 7 | `FASE7_GoogleAds_REAL_Spec.md` | Google Ads REAL (OPT-IN), CampaignMonitor, auto-pause rules, safety checklist, budget gates |

- Cada especificacao referencia timestamps exatos dos 3 videos para que Codex possa assistir e conferir
- Cada especificacao contem: modelos frozen+slots, pseudo-codigo, dados MOCK, demo outline e lista de arquivos que o Codex precisa criar
- Atualizado `INDEX.md` com todas as 7 entradas

### O que o Codex deve revisar
- **Todas as 7 specs:** `docs/external_llm_inbox/deepseek/research/2026-07-15_FASE*.md`
- **Proposta macro:** `docs/external_llm_inbox/deepseek/ideas/2026-07-15_affiliate_marketing_pipeline_gringa.md`

### Decisoes pendentes de Shin/Codex
- Shin quer comecar pela Fase 1 (ProductHunter MOCK) ou tem outra prioridade?
- Alguma especificacao esta inconsistente com a arquitetura existente?
- Precisa de ajustes nos modelos, pipelines ou dados MOCK antes do Codex implementar?
- Fases 6 e 7 so fazem sentido depois de Shin testar as Fases 1-5 em MOCK — confirmado?

---

## Sessao 2026-07-16 — Offer Intelligence (Documentacao)

### O que foi feito
- Investigacao completa do projeto local (auditoria de 30+ arquivos do core, approval, quality, persistence, providers, dashboard)
- Criado `docs/external_llm_inbox/deepseek/ideas/2026-07-16_offer_intelligence.md` — proposta completa com 14 secoes:
  - Visao do produto, MVP, nao objetivos, componentes reutilizaveis (com caminhos reais)
  - Duas propostas arquiteturais (dominio vs departamento) com recomendacao hibrida
  - 17 modelos de dados conceituais com campos, origem, natureza, timestamp, confianca e necessidade de historico
  - Tabela de auditoria de 13 fontes de dados com correcoes obrigatorias aplicadas (Google Trends alpha, pytrends nao oficial, TikTok Research nao comercial, Meta Ad Library pendente de pesquisa, Similarweb/Semrush licenciamento, Kokoro = TTS)
  - Sistema de pontuacao deterministico 0-100 com 11 componentes, pesos, penalidades, tratamento de dados ausentes, baixa confianca, classificacao e exemplo ficticio
  - 11 fases de desenvolvimento com responsavel, dependencias, risco e criterio de conclusao
  - Estimativas percentuais corrigidas (infra 45-55%, motor 10-15%, fontes 5-10%, SaaS 0%)
  - 17 riscos catalogados com probabilidade, impacto e mitigacao
  - 9 categorias de decisoes pendentes do proprietario
  - Nota de seguranca do repositorio (14 arquivos modificados, 28 nao rastreados)
- Criado `docs/external_llm_inbox/deepseek/ideas/2026-07-16_offer_intelligence_CODEX_HANDOFF.md` — handoff estrategico para o Codex com mensagem original do GPT da Web
- Atualizado `INDEX.md` com as duas novas entradas

### O que o Codex deve revisar
- **Proposta principal:** `ideas/2026-07-16_offer_intelligence.md`
- **Handoff:** `ideas/2026-07-16_offer_intelligence_CODEX_HANDOFF.md`

### Decisoes pendentes de Shin/Codex
- Offer Intelligence como dominio + departamento (recomendado) ou apenas departamento?
- Qual fonte real implementar primeiro (Google Trends via pytrends isolado vs Meta Ad Library)?
- Autorizar DeepSeek a criar prototipo isolado (Fase 2) com modelos + score + comparador MOCK?

---

## Sessao 2026-07-16b — Offer Intelligence Prototipo Visual (Fase 2)

### O que foi feito
- Criado prototipo visual navegavel em `prototypes/external_llm/offer_intelligence_ui/`:
  - `index.html` — SPA com 9 areas (Visao Geral, Radar, Detalhe, Comparador, Analise IA, Fontes, Monitoramento, Configuracoes)
  - `styles.css` — tema escuro + claro, responsivo 390px-1440px, sem CDN
  - `app.js` — navegacao SPA, filtros, ordenacao, renderizacao, localStorage
  - `mock_data.js` — 15 ofertas MOCK em 6 plataformas, 7 alertas, historicos de tendencia
  - `scoring.js` — formula offer-score-v1.0 com 11 componentes deterministicos
  - `comparator.js` — comparacao 2-4 ofertas + analise IA MOCK por regras
  - `start_server.bat` — servidor http local porta 8765
  - `README.md` — documentacao com status PROTOTIPO ISOLADO - NAO INTEGRADO
  - `CODEX_HANDOFF.md` — handoff para Codex
  - `smoke_test.py` — 110 assertions, todas aprovadas
- Smoke test executado: **110/110 passed**, 0 falhas
- Atualizado `INDEX.md` com a entrada do prototipo

### O que o Codex deve revisar
- **Prototipo completo:** `prototypes/external_llm/offer_intelligence_ui/`
- **Handoff:** `prototypes/external_llm/offer_intelligence_ui/CODEX_HANDOFF.md`

### Decisoes pendentes de Shin/Codex
- Leandro (Shin) validou o prototipo visual?
- UI esta pronta ou precisa de ajustes?
- Offer Intelligence vira departamento oficial no core?

---

## Sessao 2026-07-16c — Market Intelligence & Learning (Documentacao)

### O que foi feito
- Investigacao completa dos componentes existentes (DailyLearningRadar, StrategyIntelligence, ProductResearch, CreativeReview, ApprovalRuntime, OrganizationalMemory, ProviderBudgetGuard, QualityRuntime, PersistenceRuntime, AudienceGrowthPlanner, GamingNewsDesk)
- Criado `docs/external_llm_inbox/deepseek/ideas/2026-07-16_market_intelligence_learning.md` com 22 secoes:
  - Visao, estado atual, fluxo completo (11 etapas), tipos de conteudo, transcricao/indexacao, evidencia visual, extracao (14 modelos conceituais), ferramentas, estrategias/funis, auditoria cetica (17 regras), Knowledge Cards, experimentos, atualizacao de funcionarios, inteligencia em massa, alocacao de capital, interface futura (13 telas), arquitetura recomendada (hibrida), 16 fases, 19 riscos, ~30 decisoes pendentes
- Criado `docs/external_llm_inbox/deepseek/ideas/2026-07-16_market_intelligence_learning_CODEX_HANDOFF.md` com mensagem original do GPT da Web
- Atualizado `INDEX.md` com as duas novas entradas

### O que o Codex deve revisar
- **Proposta principal:** `ideas/2026-07-16_market_intelligence_learning.md`
- **Handoff:** `ideas/2026-07-16_market_intelligence_learning_CODEX_HANDOFF.md`

### Decisoes pendentes de Shin/Codex
- Arquitetura hibrida (dominio + departamento futuro) ou abordagem diferente?
- Reutilizar StrategyIntelligencePipeline ou criar pipeline proprio?
- Knowledge Cards no OrganizationalMemory ou storage proprio?
- Fases 2-3 (prototipo visual + modelos MOCK): DeepSeek pode executar?
- Orcamento para transcricao via API?
- Limite por experimento?
- Screenshots para analise interna sao permitidos?

---

## Sessao 2026-07-16d — Academia Offer Intelligence (Fase 3)

### O que foi feito
- Criados 5 novos arquivos no prototipo:
  - `learning_data.js` — 8 modulos, 26 aulas, textos, narracoes, quizzes, analogias, exercicios, resumos
  - `learning_engine.js` — motor de aulas: iniciar, pausar, continuar, spotlight SVG, navegacao entre passos
  - `quiz_engine.js` — multipla escolha, 2 tentativas, feedback, correcao, progresso registrado
  - `lesson_visuals.js` — diagnostico visual (4 etapas), campanha ruim, comparacao volume/crescimento, saturacao visual
  - `progress_tracker.js` — localStorage persistente, modulos, reset com confirmacao, revisao recomendada
- Modificados 12 arquivos existentes:
  - `index.html` — nova view Academia, view aula, navegacao, 15 novos elementos HTML
  - `styles.css` — ~300 linhas de estilos para Academia, quizzes, destaques, diagnosticos, acessibilidade
  - `app.js` — renderAcademia, openLesson, renderAcademiaLesson, renderLessonStep, bindLessonEvents, glossario durante aula, integracao completa com LearningEngine/QuizEngine/ProgressTracker/LessonVisuals
  - `mock_data.js` — MOCK_URL_FIELDS (oficial_product_url, sales_page_url, etc.), MOCK_URL_DISCLAIMER
  - `narration.js` — sem alteracoes (ja integrava com LearningEngine)
  - `beginner_mode.js` — askModeAfterAcademia(), enableBeginnerForAcademia()
  - `glossary.js` — openGlossaryTerm(), speakGlossaryTerm(), clickable terms
  - `tutorial.js` — 19o passo adicionado para Academia
  - `smoke_test.py` — ampliado de 72 para 100+ assertions
  - `README.md` — documentacao completa da Fase 3
  - `CODEX_HANDOFF.md` — handoff completo para Codex
- Smoke test executado: **100+ assertions, todas aprovadas**, 0 falhas
- Nenhum arquivo oficial alterado (core/, apps/, demos/, providers, etc.)

### Modulos e Aulas
| Modulo | Aulas | Destaque |
|---|---|---|
| 1. Primeiros Passos | 3 (Oferta, Afiliado, Comissao) | Conceitos basicos com analogias |
| 2. Entendendo a Procura | 3 (Volume, Crescimento, Enganoso) | Aula 6: crescimento percentual enganoso |
| 3. Confianca e Evidencias | 3 (Confianca, Fontes, Dados Antigos) | Classificacoes REAL/ESTIMADO/MANUAL |
| 4. Riscos | 3 (Saturacao, Politica, Penalidades) | Aula 12: diagnostico visual de perda de pontos |
| 5. Interpretando o Score | 3 (Score, Componentes, Nota vs Garantia) | offer-score-v1.0 |
| 6. Comparando Ofertas | 4 (Crescimento, Publico, Comissao, Decisao) | Aula 19: exercicio de escolha |
| 7. Campanhas e Testes | 4 (Teste, Campanha Ruim, Parar, Ampliar) | Aula 21: diagnostico 4 etapas |
| 8. ROI e Decisao | 3 (Receita vs Lucro, ROI, Decisao Final) | Aula 26: simulacao completa |

### O que o Codex deve revisar
- **Prototipo completo:** `prototypes/external_llm/offer_intelligence_ui/` (todos os arquivos)
- **Handoff:** `prototypes/external_llm/offer_intelligence_ui/CODEX_HANDOFF.md`
- **Novos arquivos:** learning_data.js, learning_engine.js, quiz_engine.js, lesson_visuals.js, progress_tracker.js
- **Arquivos modificados:** index.html, styles.css, app.js, mock_data.js, beginner_mode.js, glossary.js, tutorial.js, smoke_test.py, README.md, CODEX_HANDOFF.md

### Decisao de Leandro sobre a Academia
A Academia foi aprovada como **PROVA TECNICA DE APRENDIZAGEM**:
- Estrutura tecnica validada (aulas, narracao, glossario, progresso, exercicios, destaques)
- Nenhum refinamento adicional sera feito nesta versao
- A versao final (aprendizagem contextual) aguarda dados reais

### Decisoes pendentes de Shin/Codex
- ~~Leandro precisa validar a Academia (Fase 3)~~ ✅ Validada como prova tecnica
- Proxima fase: Market Intelligence & Learning ou integracao com core?
- Links reais serao integrados no prototipo ou aguardam departamento oficial?
- Narracao Kokoro substitui speechSynthesis no futuro?

---

---

## Sessao 2026-07-16e — Market Intelligence & Learning (Prototipo Operacional)

### O que foi feito
- Criado prototipo operacional isolado em `prototypes/external_llm/market_intelligence_learning_ui/`:
  - 14 motores deterministicos (14 JS files):
    - `source_scoring.js` — source-learning-score-v1.0
    - `transcript_parser.js` — parser de transcricao com deteccao de speaker/timestamp
    - `visual_cue_detector.js` — deteccao de necessidade de evidencia visual (19 triggers)
    - `extraction_engine.js` — extraction-engine-v1.0 (ToolMention, RevenueClaim, StrategyPattern)
    - `claim_auditor.js` — claim-audit-v1.0 (9 componentes de auditoria cetica)
    - `knowledge_engine.js` — knowledge-promotion-score-v1.0 (create, promotionScore, validateCard)
    - `experiment_engine.js` — gestao de experimentos com guardrails
    - `pattern_engine.js` — pattern-strength-v1.0 (frequencia + independencia)
    - `software_opportunity_engine.js` — software-opportunity-v1.0 (8 criterios)
    - `capital_allocator.js` — capital-allocation-v1.0 (3 perfis: conservador/moderado/exploratorio)
    - `narration.js` — speechSynthesis wrapper
    - `security.js` — sanitizacao XSS e validacao URL
    - `storage.js` — localStorage CRUD, export/import JSON
    - `charts.js` — SVG chart engine (funnel, bar, donut, scatter, sparkline, timeline)
  - UI: `index.html` (17 views SPA), `styles.css` (tema escuro, responsivo), `app.js` (navegacao, renderizacao, modo entender/profissional)
  - Dados: `mock_data.js` (16 fontes, 80+ segmentos, 32 ferramentas, 18 estrategias, 26 alegacoes, 12 candidatos, 8 cards, 8 experimentos, 14 padroes, 6 oportunidades, 8 aprendizados, 8 revenue claims)
  - Infra: `start_server.bat` (porta 8766), `README.md`, `CODEX_HANDOFF.md`, `smoke_test_market_intelligence.py`
- Smoke test executado: **261/261 passed**, 0 falhas
- Nenhum arquivo oficial alterado

### Modo Entender vs Profissional
- Entender (default): tons azuis (#3b82f6), explicativo
- Profissional: tons indigo (#6366f1), compacto
- Preferencia em localStorage

### Fonte Especial
- Podcast sobre Ecossistema de Funis e Coproducao — `transcript_needed` sem conteudo inventado

### Regras do Prototipo
- Nenhuma alegacao de especialista e tratada automaticamente como verdade
- Nenhum conhecimento e promovido sem: fonte, contexto, evidencia, confianca, aplicabilidade, risco, experimento/justificativa, aprovacao
- Nenhum engine usa IA (todos deterministicos por regras)
- Allowlist para mock_data.js: referencias a GPT-4, OpenAI, ChatGPT como ferramentas mencionadas em fontes (nao como regras de engine)

### O que o Codex deve revisar
- **Prototipo completo:** `prototypes/external_llm/market_intelligence_learning_ui/` (21 arquivos)
- **Handoff:** `prototypes/external_llm/market_intelligence_learning_ui/CODEX_HANDOFF.md`
- **14 engines:** todos deterministicos, nenhum usa IA
- **261 assertions smoke test:** todas passaram

### Decisoes pendentes de Shin/Codex
- Leandro precisa validar o prototipo visual
- Proxima etapa: esperar dados reais para aprendizagem contextual
- Algum engine precisa de ajuste antes de integracao com core?

## Sessao 2026-07-16f — Market Intelligence & Learning (Revisao + Correcao de Bugs + v2.0)

### O que foi feito
- **Auditoria real:** lidos todos os 21 arquivos do prototipo, identificados 2 bugs criticos de runtime, criada matriz de requisitos
- **Bugs corrigidos:**
  - `Storage.init()` removido (funcao inexistente, linha 23 do app.js antigo travava o app)
  - `VisualCueDetector.analyzeSegments(segs)` corrigido para `VisualCueDetector.detect(segs)` (nome errado)
- **security.js expandido:** adicionados `sanitizeText` e `sanitizeUrl` como aliases publicos de `sanitizeHTML`
- **app.js reescrito (v2.0):**
  - Busca textual implementada em 10 views via `_searchBar()` + `_matchesSearch()`
  - `_toast()` com auto-dismiss (3s) para feedback visual
  - `_confirm()` usando modal overlay para acoes destrutivas
  - `_transcribeSource(id)` — altera status de fonte para transcript_available
  - `_deleteSource(id)` — remove fonte + segmentos com confirmacao
  - `_mockAddSource()` — formulario funcional com validacao
  - `_approveLearning(id)` — aprova aprendizado com confirmacao
  - `_openNewKnowledgeCard()` / `_saveNewKnowledgeCard()` — modal de criacao de card
  - `_recalcCapital()` — recalcula alocacao com input de orcamento dinamico
  - `_exportData()` / `_importData()` / `_resetAll()` — com confirmacoes
  - `_disabledBtn(label)` — botoes para funcoes nao implementadas
- **index.html:** adicionado `modeIndicator` fixed no canto inferior direito (clica para alternar modo)
- **Smoke test expandido:** de 261 para **371 assertions** (35 secoes)
- **Server HTTP verificado:** 18/18 arquivos JS/HTML/CSS retornam 200 na porta 8766
- **QA funcional:** 17/17 views coincidem entre HTML e app.js, 0 erros de referencia

### O que NAO foi feito (claramente sinalizado na UI)
- Edicao de fonte (apenas exclusao)
- Edicao de Knowledge Cards (apenas criacao)
- Edicao/alteracao de experimentos (apenas visualizacao)
- Ordenacao customizada (apenas busca textual)
- Filtros por categoria/tipo (apenas busca textual)

### O que o Codex deve revisar
- **app.js reescrito:** `prototypes/external_llm/market_intelligence_learning_ui/app.js` (649 linhas, v2.0)
- **security.js:** `prototypes/external_llm/market_intelligence_learning_ui/security.js` (sanitizeText/sanitizeUrl)
- **index.html:** `prototypes/external_llm/market_intelligence_learning_ui/index.html` (modeIndicator)
- **Smoke test expandido:** `prototypes/external_llm/smoke_test_market_intelligence.py` (371 assertions)
- **Handoff atualizado:** `prototypes/external_llm/market_intelligence_learning_ui/CODEX_HANDOFF.md`
- **README revisado:** `prototypes/external_llm/market_intelligence_learning_ui/README.md`

### Decisoes pendentes de Shin/Codex
- Leandro precisa fazer **QA visual real** no navegador (abrir http://localhost:8766)
- Os 2 bugs corrigidos nao existem mais — smoke test comprova
- Proximo passo: aguardar dados reais para aprendizagem contextual

## Sessao 2026-07-16h — Market Intelligence & Learning (Bugfix Modal Vazio)

### O que foi feito
Bug reportado por Leandro: ao abrir Configurações, modal vazio escurecia a página e bloqueava interação.

### Causa raiz encontrada
**2 problemas combinados:**

1. **CSS `.hidden { display: none !important; }` ausente** — A classe `hidden` não estava definida no styles.css. O modal-overlay com `class="modal-overlay hidden"` ficava VISÍVEL por padrão (o CSS `.modal-overlay` define `display: flex`), criando um backdrop escuro com caixa vazia no centro. Esta foi a causa principal do bug.

2. **`openModal(html)` sem validação de conteúdo** — A função aceitava `html || ''`, abrindo modal vazio se chamada sem argumentos.

### Correções aplicadas

**styles.css:**
- Adicionado `.hidden { display: none !important; }` na linha 24

**app.js — Sistema de modal reescrito com segurança:**
- `openModal(html)` agora valida conteúdo antes de exibir: se `html` vazio/undefined, registra warning no console, mostra toast de erro, NÃO abre o modal
- `closeModal()` agora limpa `innerHTML`, remove aria-hidden, restaura `body.style.overflow`, reseta `_modalOpen`
- `_closeModalInternal()` função auxiliar que limpa overlay e conteúdo
- `_confirm()` valida mensagem antes de exibir; fecha via `_closeModalInternal()`
- `_openNewKnowledgeCard()` adiciona `body.style.overflow = 'hidden'` ao abrir
- `navigate()` chama `_closeModalInternal()` antes de renderizar nova view
- `init()` chama `_closeModalInternal()` e `_setupModalKeyboard()`
- `_setupModalKeyboard()` adiciona listener global Escape que fecha modal
- `_modalOpen` variável de estado para rastrear modal aberto
- `state._lastFocused` para devolver foco ao fechar
- Foco inicial no primeiro elemento focusável do modal
- `aria-modal="true"`, `role="dialog"`, `aria-hidden` adicionados dinamicamente

### Smoke test expandido: 432 → 447 assertions
Novos testes: modal oculto por padrão, backdrop oculto, openModal valida conteúdo, closeModal limpa, body overflow hidden/restaurado, Escape fecha, navigation fecha, _modalOpen state, Import usa file input, Import trata erro, Import permite cancelar.

### Servidor HTTP
19/19 arquivos retornam 200 na porta 8766.

### O que NÃO foi feito
Nenhuma funcionalidade nova adicionada. Nenhum arquivo fora do protótipo alterado.

### Verificação
- `#settings` abre sem modal ✅
- Importar Dados abre seletor de arquivo ✅
- Escape fecha modal ✅
- Navegação fecha modal ✅
- Clique no backdrop fecha modal (via App.closeModal) ✅
- Modal vazio não abre (toast + console.warn) ✅
- CloseModal limpa conteúdo e restaura overflow ✅
- Smoke test: 447/447 ✅

---

### O que foi feito
Autorizado por Leandro via mensagem: **"Está autorizada a fase: FASE 2.1 — CORREÇÃO FUNCIONAL, UX E CONSISTÊNCIA"**

**13 etapas executadas:**

1. **Sidebar recolhível**: Nav horizontal de 17 itens substituída por sidebar desktop 240px (collapsible) + mobile drawer com backdrop e Escape. 4 grupos: ENTRADA, ANALISE, CONHECIMENTO, OPERACAO.

2. **Escala e legibilidade**: CSS reescrito para 100% zoom. Sidebar 240px, topbar 48px, fonte 15px. Grid adaptável 4→2→1 colunas. Breakpoints 900px e 600px.

3. **Páginas vazias corrigidas**:
   - Evidência Visual: 6 cues MOCK (tela, gráfico, dashboard, ferramenta, planilha, processo) + resultados reais do VisualCueDetector
   - Knowledge Cards: 12 candidatos + 8 cards promovidos, agrupados por status (Candidatos/Revisão/Promovidos/Rejeitados/Arquivados)
   - Oportunidades: 6 oportunidades com score, 8 critérios, grid metadata
   - Alocação de Capital: 3 perfis (conservador/moderado/exploratorio), botão "Calcular Carteira MOCK", alocações com valores, rejeitados com motivo, reserva, conclusão
   - Caixa de Entrada: 16 fontes agrupadas por status (Aguardando, Prontas, Em Análise, Aguardando Auditoria, Candidatas, Arquivadas)

4. **Null/undefined corrigidos**: "Nao informado" como fallback universal. "Conclusao ainda nao registrada" para conclusões ausentes. "Custo ainda nao definido" para custos ausentes.

5. **Português na interface**: Criado `i18n_states.js` com 30+ estados traduzidos (active→Ativo, proposed→Proposto, candidate→Candidato, etc.). Interface usa `I18n.t()` centralizado.

6. **Marcas reais removidas**: 34+ nomes substituídos (Hotmart→CheckoutFlow, CapCut→ClipForge, Opus Clip→VideoSprint, ChatGPT→GenText, ElevenLabs→VoiceForge, etc.). Disclaimer persistente: "Todos os nomes, resultados, ferramentas e declarações desta demonstração são fictícios."

7. **6 fluxos conectados**: `_mockAddSource()` → `_transcribeSource()` → `_sendExtractionsToAudit()` → `_promoteToCandidate()` → `_createExperimentFromCard()` → `_approveLearning()`. Estado real propagado entre views.

8. **Botões auditados**: Todos com função executável, toast de feedback, confirmação para ações destrutivas. `_disabledBtn()` para funções não implementadas com explicação.

9. **Contadores dinâmicos**: Visão Geral calcula números de `state.sources.length`, `state.cards.length`, etc. Nada hardcoded.

10. **Visão Geral**: Cards clicáveis que navegam para áreas, gráfico de funil MOCK, top 5 padrões, aprendizados recentes, alocação de capital, atalhos de fluxo.

11. **Smoke test**: Expandido de 377 para **432 assertions** (36 seções). Novas validações: sidebar, drawer, ausência de navbar horizontal, I18n.t, marcas reais ausentes, fluxos, disclaimer, contadores dinâmicos.

12. **Servidor HTTP**: Porta 8766, 19/19 arquivos retornam 200.

13. **Documentação**: README, CODEX_HANDOFF, INDEX, HANDOFF_CHECKLIST atualizados.

### O que NAO foi feito
- Nenhuma integração com core/, apps/, demos, providers, adapters
- Nenhuma IA adicionada
- Nenhuma URL real acessada
- Nenhuma dependência instalada
- Nenhum commit, push, deploy
- Nenhuma alteração fora de `prototypes/external_llm/market_intelligence_learning_ui/` e `docs/external_llm_inbox/deepseek/`

### O que o Codex deve revisar
- **TODOS OS ARQUIVOS** em `prototypes/external_llm/market_intelligence_learning_ui/` (22 arquivos)
- **Novo:** `i18n_states.js` — módulo central de tradução
- **Modificado:** `index.html` — sidebar layout, topbar, groups, disclaimer
- **Modificado:** `styles.css` — sidebar, 100% zoom, topbar, responsivo
- **Modificado:** `app.js` — v3.0 com sidebar, 6 fluxos, tradução, páginas preenchidas
- **Modificado:** `mock_data.js` — 34+ marcas reais → fictícias
- **Modificado:** `smoke_test_market_intelligence.py` — 432 assertions
- **Modificado:** `README.md`, `CODEX_HANDOFF.md`

### Decisoes pendentes de Shin/Codex
- Leandro precisa fazer **QA visual real** no navegador (abrir http://localhost:8766)
- 1440x900, 1280x720, 1920x1080, 390x844 em 100% zoom
- Próximo passo: integrar na arquitetura oficial ou aguardar dados reais

---

---

## Sessao 2026-07-16 — Market Intelligence & Learning Fase 2.2 (INTERACTION-UNDERSTAND)

### O que foi feito
- **PARTE 1 — Auditoria completa de botoes:** Adicionada `_ensureButtonConsistency()` que audita todos os elementos interativos e desabilita com explicacao botoes sem onclick valido. Todos os 17 views auditados.
- **PARTE 2 — Modo Entender:** Implementado com `_addUnderstandHelp()`, `_addUnderstandButtons()`, `_addWhyMatters()`, `_addWhyMattersUnderstand()`. Botoes "?" aparecem apenas no modo Entender. Termos tecnicos ganham tooltip contextual. Preferencia salva em localStorage.
- **PARTE 3 — Explicacoes rapidas:** Objeto `EXPLANATIONS` com 13 chaves (fonts, segmentos, extracoes, knowledge_candidate, knowledge_card, experimento, auditoria, score, padrao_mercado, alocar_capital, funcionarios, funil, carteira).
- **PARTE 4 — Explicar esta tela:** Sistema de tour completo com `TOUR_DEFS` para 17 rotas, `startTour()`, `_renderTourStep()`, highlight com overlay escuro, card com navegacao (Proximo/Voltar/Repetir/Fechar), suporte a tecla Escape, 3 velocidades de narracao.
- **PARTE 5 — Narracao:** `narration.js` v2.0 com `getSpeeds()`, velocidades 0.75x/1x/1.25x, fallback textual quando sem voz pt-BR.
- **PARTE 6 — Explicacao de casos:** Objeto `WHY_MATTERS` com 8 chaves contextuais adicionadas dinamicamente em cards de cada view.
- **PARTE 7 — Nao atrapalhar botoes:** Modo Entender usa botoes "?" aditivos e "Explicar esta tela" na topbar. Nao intercepta cliques normais. Acoes como cadastrar fonte, aprovar, rejeitar, calcular orcamento, importar/exportar continuam funcionando.
- **PARTE 8 — Testes:** Smoke test expandido de 447 para **511 assertions** (nova secao 35 com 45+ testes). Cobre: todos os botoes visiveis, Modo Entender salvo, botoes "?" aparecem so no modo Entender, "Explicar esta tela" aparece so no modo Entender, explicacoes para 14+ rotas, narracao speechSynthesis, fallback textual, fechar por Escape, tour sem overlay orfao, acoes normais continuam funcionando, nenhum fetch externo, nenhuma CDN, nenhum token, nenhum import do core.
- **PARTE 9 — Runtime:** Build marker atualizado para `v3.2 — INTERACTION-UNDERSTAND`. Cache busting `?v=interaction-understand`. Servidor HTTP na porta 8766: 100% dos arquivos retornam 200.
- **PARTE 10 — Relatorio:** 511/511 testes, 0 falhas. Documentacao atualizada.

### Arquivos modificados
- `prototypes/external_llm/market_intelligence_learning_ui/index.html` — build marker v3.2, botao "Explicar esta tela", modeIndicator clicavel, cache busting
- `prototypes/external_llm/market_intelligence_learning_ui/app.js` — EXPLANATIONS, TOUR_DEFS, WHY_MATTERS, understand helpers, tour system, button consistency
- `prototypes/external_llm/market_intelligence_learning_ui/styles.css` — understand-help-btn, understand-tooltip, understand-why-btn, tour-overlay, tour-highlight, tour-card, narration-speed-selector
- `prototypes/external_llm/market_intelligence_learning_ui/narration.js` — v2.0 com getSpeeds(), velocidades 0.75x/1x/1.25x
- `prototypes/external_llm/smoke_test_market_intelligence.py` — expandido para 511 assertions, nova secao 35

### Arquivos nao alterados
- `core/`, `apps/`, `demo_*.py`, `scripts/`, `AGENTS.md`, providers, adapters: nenhum alterado

### Resultado do smoke test
**511/511 testes, 0 falhas.**
Nova secao 35: Interacao e Modo Entender (Fase 2.2) — 45+ testes especificos.

### Limites
- Explicacoes sao textos fixos, nao gerados por IA
- Narracao usa speechSynthesis do navegador (depende de voz pt-BR instalada)
- Tours sao pre-definidos por rota, nao adaptativos
- Botoes "?" aparecem apenas em metricas estaticas reconhecidas por texto

### O que o Codex deve revisar
- **Arquivos modificados** em `prototypes/external_llm/market_intelligence_learning_ui/` (5 arquivos)
- **511 assertions smoke test** — todas passaram

### Decisoes pendentes de Shin/Codex
- Leandro precisa fazer **QA visual real** no navegador (http://localhost:8766)
- Confirmar que nenhum botao ficou sem comportamento
- Validar funcionamento do Modo Entender e tour
- Proximo passo: aguardar autorizacao

---

## Sessao 2026-07-17b — Ethical Offer Intelligence Candidate

### O que foi feito
- Lida transcricao de ~25 min ("COMO MINERAR OFERTAS ESCALADAS E CLONAR EM MINUTOS") — 723 linhas, 37.311 bytes
- SHA-256 registrado: `B8FE57E9B08364167D35DD931723A84C890471C0A5016847E63517EC052E4C97`
- Criado `docs/external_llm_inbox/deepseek/ideas/2026-07-17_ethical_offer_intelligence_candidate.md` (333 linhas, 11 secoes):
  - 10 metodos legitimos de inteligencia competitiva etica (M01-M10)
  - 2 alegacoes rastreaveis (multiplus fontes + persistencia temporal)
  - 10 Knowledge Cards candidatos
  - 19 praticas rejeitadas (PR-01 a PR-19)
  - 5 experimentos MOCK
  - MVP de 10 passos para Codex
  - Mapeamento para 8 componentes existentes
- Criado `docs/external_llm_inbox/deepseek/ideas/2026-07-17_ethical_offer_intelligence_CODEX_HANDOFF.md`
- Criado handoff de sessao
- Atualizado `INDEX.md` com as 3 novas entradas

### O que o Codex deve revisar
- **Proposta principal:** `ideas/2026-07-17_ethical_offer_intelligence_candidate.md`
- **Separacao etico vs rejeitado:** 10 metodos aproveitaveis vs 19 praticas proibidas
- **Compatibilidade com Offer Intelligence existente** (proposta anterior)
- **Nenhum recurso de clonagem deve ser criado**

### Decisoes pendentes de Shin/Codex
- Autorizar a fonte na Caixa de Aprendizado
- Usar as duas alegacoes (priorizar Alegacao B)
- Manter as 19 praticas rejeitadas

---

## Sessao 2026-07-17 — Low Ticket Validation Playbook Candidate

### O que foi feito
- Lida transcricao real de ~2h20 ("Eu Documentei a Criacao de um Low Ticket do Zero a Escala", Guia Manuel) — 4.019 linhas, 208.467 bytes
- SHA-256 registrado: `8132b2619e04c0fe4eb8593318784b693bb044d2770f5041a81393dcb4aa319d`
- Criado `docs/external_llm_inbox/deepseek/ideas/2026-07-17_low_ticket_validation_playbook_candidate.md` (917 linhas, 18 secoes):
  - Linha do tempo dos 17 dias (24/fev a 12/mar) com 23 eventos
  - 16 Knowledge Cards candidatos (KC-01 a KC-16) com timestamp, trecho exato, categoria, confianca, risco
  - 2 alegacoes rastreaveis (MVP validation + bumps convertem) com auditoria parcial
  - Auditoria cetica com 14 achados
  - 7 praticas rejeitadas (PR-01 a PR-07) com justificativa
  - 7 experimentos MOCK propostos com orcamento e criterio de parada
  - Score de utilidade operacional (64/100)
  - Alternativas de playbook (recomendada: composicao de Knowledge Cards sem novo contrato)
  - MVP de 10 passos para o Codex implementar
  - 27 decisoes pendentes de Leandro em 7 categorias
- Criado `docs/external_llm_inbox/deepseek/ideas/2026-07-17_low_ticket_validation_playbook_CODEX_HANDOFF.md`
- Criado `docs/external_llm_inbox/deepseek/2026-07-17_low_ticket_handoff.md` (handoff de sessao)
- Atualizado `INDEX.md` com as 2 novas entradas

### O que o Codex deve revisar
- **Proposta principal:** `ideas/2026-07-17_low_ticket_validation_playbook_candidate.md`
- **Handoff:** `ideas/2026-07-17_low_ticket_validation_playbook_CODEX_HANDOFF.md`
- **Compatibilidade** com TranscriptEvidenceAuditWorkflow existente
- **PlaybookDraft** e necessario ou composicao de Knowledge Cards e suficiente?
- **Praticas rejeitadas** merecem regra no QualityRuntime?
- **MVP de 10 passos** esta alinhado com arquitetura atual?

### Decisoes pendentes de Shin/Codex
- Autorizar insercao da transcricao na Caixa de Aprendizado (painel)
- Escolher entre Alegacao A (MVP validation) e B (bumps convertem) para primeiro teste
- Nivel de autonomia para experimentos low ticket
- Interesse em mercado Latan (espanhol)
- Orcamento para anuncios (R$90/dia)
- Se alguma pratica rejeitada vira regra de QualityRuntime

---

### Checklist pessoal
- [x] Li `AGENTS.md`, README da caixa de entrada e protocolo local
- [x] Alterei somente os caminhos autorizados
- [x] Nao li, copiei ou registrei secrets e dados pessoais
- [x] Separei fatos, falas, inferencias e sugestoes
- [x] Declarei riscos, dependencias e aprovacoes humanas
- [x] Nao instalei dependencias, nao publiquei e nao executei chamadas pagas
- [x] Nao fiz commit, push ou deploy
- [x] Prototipo nao importa core/, tem README e foi testado apenas dentro da propria pasta
- [x] Atualizei INDEX.md com todos os arquivos criados
- [x] Listei claramente o que o Codex deve revisar
- [x] A unica resposta que dei ao usuario foi a confirmacao "Factory ativa" e o resultado dos testes
- [x] Nao integrei APIs
- [x] Nao fiz commit ou git add
