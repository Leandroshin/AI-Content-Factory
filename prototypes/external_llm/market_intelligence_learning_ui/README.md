# Market Intelligence — Prototipo Operacional Isolado (Fase 2.1)

## Proposito
Protótipo operacional isolado **Market Intelligence & Learning** (Inteligência e Aprendizado de Mercado).
Transforma fontes externas em conhecimento organizacional auditável sem usar IA.
Nenhuma transcrição bruta vira instrução automática.

## Fluxo
Fonte → Transcrição → Evidência Visual → Extração → Auditoria → Knowledge Card → Experimento → Aprovação ou Arquivamento

## 22 Arquivos (14 Motores + 8 Infra/UI)
| Engine | Versão | Propósito |
|--------|--------|-----------|
| source_scoring.js | source-learning-score-v1.0 | Score de aprendizado por fonte |
| transcript_parser.js | — | Parser de transcrição com detecção de speaker/timestamp |
| visual_cue_detector.js | — | Detecta necessidade de evidência visual (19 triggers) |
| extraction_engine.js | extraction-engine-v1.0 | Extração por regras (ToolMention, RevenueClaim, StrategyPattern) |
| claim_auditor.js | claim-audit-v1.0 | Auditoria cética (9 componentes) |
| knowledge_engine.js | knowledge-promotion-score-v1.0 | Score e validação de Knowledge Cards |
| experiment_engine.js | — | Gestão de experimentos com guardrails |
| pattern_engine.js | pattern-strength-v1.0 | Score por frequência + independência |
| software_opportunity_engine.js | software-opportunity-v1.0 | Score (8 critérios) |
| capital_allocator.js | capital-allocation-v1.0 | Alocação simulada (3 perfis) |
| narration.js | — | SpeechSynthesis local, sem API externa |
| security.js | — | Sanitização XSS, validação URL, validação JSON |
| storage.js | — | localStorage CRUD, export/import JSON seguro |
| charts.js | — | SVG charts (funnel, bar, donut, scatter, sparkline, timeline) |
| **i18n_states.js** | — | **Central de tradução (30+ estados pt-BR)** |

## Sidebar Recolhível (4 grupos, 17 views)
### ENTRADA
1. **Visão Geral** — cards clicáveis, funil de aprendizado, gráficos, top padrões, aprendizados recentes, alocação, atalhos de fluxo
2. **Caixa de Entrada** — 16 fontes agrupadas por status (Aguardando, Prontas, Análise, Auditoria, Candidatas, Arquivadas), busca, iniciar transcrição, excluir
3. **Nova Fonte** — formulário com título, URL, tipo, autor, tags, notas, adicionar MOCK

### ANÁLISE
4. **Transcrição** — segmentos por fonte com timestamp, speaker, busca no texto
5. **Evidência Visual** — 6 cues MOCK + resultados reais do VisualCueDetector, fonte, timestamp, trigger, prioridade, botões relacionar/upload
6. **Extrações** — agrupadas por tipo, busca, contagem, enviar para auditoria
7. **Auditoria** — score de credibilidade (0-100%), 9 componentes, busca, transformar em candidato

### CONHECIMENTO
8. **Knowledge Cards** — 12 candidatos + 8 promovidos, agrupados por status, score, issues, filtros, criação via modal, promover/rejeitar/criar experimento
9. **Experimentos** — 8 experimentos, status, métrica, custo, risco, validação, criar a partir de card
10. **Padrões de Mercado** — 14 padrões, força %, fontes independentes, busca
11. **Ferramentas** — 32+ ferramentas fictícias, frequência, categoria, busca
12. **Oportunidades de Software** — 6 oportunidades, score, 8 critérios, grid metadata, próximos passos

### OPERAÇÃO
13. **Aprendizados** — pendentes (aprovar) e aprovados, busca, promoção
14. **Funcionários** — departamentos impactados, cards + aprendizados aplicáveis
15. **Alocação de Capital** — 3 perfis (conservador/moderado/exploratorio), calcular carteira, alocações, rejeitados, reserva, conclusão, gráfico, recomendação de não gastar
16. **Histórico** — eventos combinados, busca
17. **Configurações** — modo Entender/Profissional, export/import JSON, reset, narração, sobre

## Tecnologia
HTML + CSS + JavaScript puro + SVG. Python apenas para servidor local.

## Como Executar

```batch
start_server.bat          # duplo clique no Windows Explorer
```

Ou manualmente no terminal (VS Code → Terminal → Novo Terminal):

```bash
cd "C:\Users\Shin\Documents\Novo_projeto_Ai_Content_Factory\prototypes\external_llm\market_intelligence_learning_ui"
python -m http.server 8766
```

Se o OpenCode encerrar o processo por timeout, use Start-Process no PowerShell:

```powershell
Start-Process -NoNewWindow -FilePath "python" -ArgumentList "-m http.server 8766"
```

URL local: **http://localhost:8766**

## Smoke Test
```bash
python prototypes\external_llm\smoke_test_market_intelligence.py
```
**432 assertions, 36 seções de validação.** Cobre: arquivos, HTML, CSS, engines, versões, dados, app.js, ordem de carga, consistência, segurança, docs, scripts, anti-IA, sem dependências, funções internas, versionamento, headers, views, fonte especial, interface, modo, busca, feedback, narração, charts, capital allocator, botões desabilitados, segurança de dados, ações por view, contagem real, regras, acessibilidade, responsividade, handoff, validações avançadas (sidebar, drawer, fluxos, i18n, marcas fictícias, ausência de null, disclaimer).

## Dados MOCK
- 16 fontes (1 com `transcript_needed`)
- 80+ segmentos com timestamps e speakers
- 32+ ferramentas catalogadas (todas fictícias: CheckoutFlow, ClipForge, VideoSprint, etc.)
- 18 estratégias/funis
- 26 alegações financeiras
- 12 Knowledge Candidates
- 8 Knowledge Cards promovidos
- 8 experimentos (1 ativo, 1 paused, 6 proposed)
- 14 padrões de mercado
- 6 oportunidades de software
- 8 Revenue Claims
- 8 aprendizados (2 aprovados, 6 pendentes)

**Todos os nomes, resultados, ferramentas e declarações desta demonstração são fictícios.** URLs usam domínio `exemplo.com` e `youtube.com/watch?v=mock`. Nenhuma marca real foi usada.

## Modos
- **Entender** (default): tons azuis (#3b82f6), explicativo
- **Profissional**: tons índigo (#6366f1), compacto
- Alternância via Configurações ou clique no indicador flutuante (canto inferior direito)

## Limitações / Funções Não Implementadas
- Edição de fonte: apenas exclusão com confirmação
- Edição de Knowledge Card: apenas criação via modal
- Edição/alteração de experimentos: apenas visualização
- Ordenação customizada: apenas busca textual
- Filtros por categoria/tipo: apenas busca textual (faz parte)
- Integração com `core/`: protótipo isolado
- Chamadas de API reais: MOCK apenas

## Estrutura de Arquivos
```
market_intelligence_learning_ui/
├── index.html                          (55 linhas, SPA shell)
├── styles.css                          (222 linhas, tema escuro, responsivo)
├── app.js                              (649 linhas, App v2.0)
├── mock_data.js                        (576 linhas, 16 fontes, 80+ segmentos)
├── source_scoring.js                   (44 linhas)
├── transcript_parser.js                (85 linhas)
├── visual_cue_detector.js              (62 linhas)
├── extraction_engine.js                (74 linhas)
├── claim_auditor.js                    (81 linhas)
├── knowledge_engine.js                 (71 linhas)
├── experiment_engine.js                (42 linhas)
├── pattern_engine.js                   (56 linhas)
├── software_opportunity_engine.js      (72 linhas)
├── capital_allocator.js                (72 linhas)
├── narration.js                        (34 linhas)
├── security.js                         (47 linhas)
├── storage.js                          (73 linhas)
├── charts.js                           (99 linhas)
├── start_server.bat                    (script de inicializacao)
├── README.md                           (este arquivo)
├── CODEX_HANDOFF.md                    (handoff para Codex)
└── smoke_test_market_intelligence.py   (371 assertions, 35 secoes)
```

Total: 22 arquivos.
