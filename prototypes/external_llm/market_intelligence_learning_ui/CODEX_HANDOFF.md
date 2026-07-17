# CODEX HANDOFF — Market Intelligence & Learning UI (Protótipo Operacional)

## Status
PROTOTIPO ISOLADO — NAO INTEGRADO

## O que foi construído
14 motores determinísticos + 17 views SPA em `prototypes/external_llm/market_intelligence_learning_ui/`:
- **Engines:** source_scoring, transcript_parser, visual_cue_detector, extraction_engine, claim_auditor, knowledge_engine, experiment_engine, pattern_engine, software_opportunity_engine, capital_allocator, narration, security (v2.0), storage, charts
- **UI:** index.html (modeIndicator), styles.css, app.js (v2.0 — 649 linhas)
- **Dados:** mock_data.js (16 fontes, 80+ segmentos, 32 ferramentas, 18 estratégias, 26 alegações, 12 candidatos, 8 cards, 8 experimentos, 14 padrões, 6 oportunidades, 8 aprendizados)
- **Infra:** start_server.bat, README.md, CODEX_HANDOFF.md, smoke_test_market_intelligence.py

## O que NÃO foi feito
- Nenhuma integração com core/, apps/, demos, providers, adapters
- Nenhuma IA usada para extração, auditoria ou decisão
- Nenhuma URL real acessada
- Nenhum commit, push, deploy
- Edição de fontes (apenas exclusão com confirmação)
- Edição de Knowledge Cards (apenas criação via modal)
- Edição/alteração de experimentos (apenas visualização)

## Revisão e Corrigido (Sessão 2026-07-16f)
### Bugs Críticos Corrigidos
1. `Storage.init()` removido — função inexistente travava o app na inicialização
2. `VisualCueDetector.analyzeSegments(segs)` → `VisualCueDetector.detect(segs)` — nome de método errado

### Melhorias (app.js v2.0)
- Busca textual em 10 views (`_searchBar()` + `_matchesSearch()`)
- `_toast()` com auto-dismiss (3s) para feedback visual
- `_confirm()` com modal overlay para ações destrutivas
- `_transcribeSource(id)` — altera status real de fonte
- `_deleteSource(id)` — remove fonte + segmentos vinculados
- `_mockAddSource()` — formulário funcional
- `_approveLearning(id)` — aprova aprendizado com confirmação
- `_openNewKnowledgeCard()` / `_saveNewKnowledgeCard()` — modal de criação
- `_recalcCapital()` — recalcula alocação com input dinâmico
- `_exportData()` / `_importData()` / `_resetAll()` — com confirmações
- `_disabledBtn(label)` — funções não implementadas
- `modeIndicator` (índice fixo no canto inferior direito)

### security.js expandido
- `sanitizeText(string)` — alias público
- `sanitizeUrl(string)` — alias público

### Smoke Test Expandido
- **371 assertions, 35 seções** — todas passando
- Cobre: arquivos, HTML, CSS, engines, versões, dados, app.js, ordem, consistência, segurança, docs, scripts, anti-IA, dependências, funções internas, versionamento, headers, views, fonte especial, busca, feedback, narração, charts, capital allocator, botões não-implementados, segurança de dados, ações por view, contagem real, regras, acessibilidade, responsividade, handoff

### Servidor HTTP
- `python -m http.server 8766`
- 18/18 arquivos retornam 200 OK

## Decisões Tomadas
- Modo Entender (default, azul) / Profissional (índigo) com preferência em localStorage
- Alternância via Configurações ou clique no modeIndicator flutuante
- Fonte especial "Podcast sobre Ecossistema de Funis e Coprodução" com status `transcript_needed` — sem conteúdo inventado
- 14 versões de motores congeladas (source-learning-score-v1.0, claim-audit-v1.0, etc.)
- Nenhuma alegação pode ser tratada como verdade — auditoria cética obrigatória
- Score de 9 componentes na auditoria de alegações

## O que Codex precisa revisar
- **Docs atualizados:** README.md, CODEX_HANDOFF.md
- **INDEX.md:** entrada atualizada com 371/371
- **HANDOFF_CHECKLIST.md:** nova sessao 2026-07-16f registrada
- **Todos os 14 engines:** lógica determinística, regras sem IA (inalterados)
- **app.js v2.0:** busca, confirmações, toasts, botoes funcionais, modeIndicator
- **security.js:** sanitizeText/sanitizeUrl adicionados
- **index.html:** modeIndicator adicionado
- **smoke_test_market_intelligence.py:** 371 assertions, 35 seções

## Correção de Bug Crítico (Modal Vazio)
### Causa
1. **CSS `.hidden { display: none !important; }` ausente** do styles.css — sem esta regra, o modal-overlay ficava sempre visível.
2. **`openModal(html)` sem validação** — aceitava `html || ''`, exibindo modal vazio.

### Correção
| O que | Onde |
|---|---|
| `.hidden` adicionado ao CSS | `styles.css:24` |
| `openModal()` valida conteúdo | `app.js` |
| `closeModal()` limpa e restaura overflow | `app.js` |
| Escape key handler global | `app.js` |
| `navigate()` fecha modal automaticamente | `app.js` |
| `_confirm()` valida mensagem antes de exibir | `app.js` |

## Verificação Final (Fase 2.2 — Correção de Modal)
| Verificação | Resultado |
|---|---|
| 17 views HTML vs app.js | ✅ Todas coincidem |
| Sidebar recolhível (4 grupos) | ✅ Desktop collapsible + mobile drawer |
| Navegação horizontal removida | ✅ Substituída por sidebar 240px |
| Páginas vazias preenchidas | ✅ Evidência Visual (6 cues), Knowledge (20 cards), Oportunidades (6), Alocação, Inbox (16) |
| Marcas reais removidas | ✅ 34+ nomes substituídos por fictícios (CheckoutFlow, ClipForge, etc.) |
| i18n central (I18n.t) | ✅ 30+ estados traduzidos pt-BR |
| Null/undefined sanitizados | ✅ Fallback "Nao informado" em toda interface |
| 6 fluxos conectados | ✅ Fonte→Transcrição→Extração→Auditoria→Card→Experimento→Aprendizado |
| Botões auditados | ✅ Todos com função ou _disabledBtn |
| Contadores dinâmicos | ✅ Visão Geral calculada de state real |
| Disclaimer persistente | ✅ Barra fixa: "Todos os nomes... são fictícios" |
| Servidor HTTP (19 arquivos) | ✅ Todos 200 |
| Smoke test | ✅ 432/432 |
| 14 engines anti-IA | ✅ Nenhum usa IA |

## Próximos passos (para Shin/Codex)
1. Leandro fazer **QA visual real** no navegador: abrir http://localhost:8766
2. Se aprovado: integrar na arquitetura oficial da fábrica
3. Coletar dados reais quando existirem para aprendizagem contextual
