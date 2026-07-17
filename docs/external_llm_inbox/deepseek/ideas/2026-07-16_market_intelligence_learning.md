# Market Intelligence & Learning — Departamento de Inteligência e Aprendizado de Mercado

**Status:** PROPOSTA - NAO IMPLEMENTADA

**Origem estratégica:** Leandro Vieira, com estruturação do GPT da Web

**Executor documental desta fase:** DeepSeek, exclusivamente dentro do workspace seguro

**Revisor e integrador esperado:** Codex

---

# 1. Visão do sistema

## Problema resolvido

Leandro consome diariamente vídeos, podcasts, entrevistas, aulas públicas, estudos de caso e conteúdos de especialistas. Cada fonte pode conter estratégias, ferramentas, funis, processos, métricas, erros e oportunidades de software. Hoje o processo é manual: Leandro transcreve e envia para análise, sem rastreabilidade, sem repetibilidade e sem acúmulo institucional.

O sistema proposto **não é um resumidor de vídeos**. É uma camada permanente de inteligência que:

- recebe links ou conteúdos brutos;
- transcreve com timestamps;
- extrai ferramentas, estratégias, alegações e processos;
- verifica credibilidade;
- cria fichas de conhecimento (Knowledge Cards);
- propõe experimentos controlados;
- submete ao proprietário;
- executa testes pequenos e mensuráveis;
- arquiva ou promove conhecimento;
- atualiza seletivamente os funcionários da fábrica.

## Público interno

- **Leandro (CEO/proprietário):** consumidor de fontes, aprovador de experimentos, decisor de aprendizado.
- **StrategyIntelligenceEmployee:** consumidor direto dos Knowledge Cards.
- **ProductResearchEmployee:** recebe ferramentas, estratégias e oportunidades de produto.
- **CreativeReviewEmployee:** recebe padrões criativos e riscos visuais.
- **AffiliateDealsEmployee:** recebe estruturas de funil e ofertas.
- **Futuros departamentos:** alimentados por conhecimento verificado.

## Relação com a fábrica

O sistema se posiciona entre a **fonte bruta** e os **departamentos produtivos**:

```
Fonte bruta (link, PDF, transcricao)
  → Market Intelligence & Learning
    → verificacao
    → Knowledge Card
    → experimento
    → aprovacao
    → conhecimento aprovado
      → OrganizationalMemory
        → departamentos aplicaveis
```

Conhecimento não verificado **nunca** entra na memória organizacional. Transcrição bruta **nunca** vira instrução de funcionário.

## Por que isso não é apenas um resumidor de vídeos

Resumidores respondem "sobre o que é este vídeo?".

O Market Intelligence & Learning responde:
- "Que ferramenta foi citada no minuto 14:23?"
- "Esta alegação de faturamento tem evidência independente?"
- "Este funil pode ser adaptado para afiliado brasileiro?"
- "Qual o risco de copiar esta estratégia?"
- "Vale a pena gastar R\$ 200 para testar esta hipótese?"

## Geração de novos projetos, produtos e fontes de renda

- **Software Opportunities:** ferramentas citadas que podem ser substituídas por solução própria.
- **Funnels adaptados:** estruturas testadas por terceiros que podem virar oferta da fábrica.
- **Padrões de mercado:** consenso entre múltiplas fontes vira tendência confiável.
- **Conhecimento empacotado:** cards aprovados podem alimentar conteúdo (posts, vídeos, infoprodutos).

---

# 2. Estado atual da fábrica

Componentes existentes que podem ser reutilizados:

| Componente | Caminho | Função atual | Possível reutilização | Lacunas |
|---|---|---|---|---|
| DailyLearningRadar | `core/content_factory/daily_learning_radar.py` | Triage de candidatos a aprendizado com score, experimento, guardrails | Base do fluxo de seleção; fornece LearningCandidate, LearningExperiment, guardrails | Não faz transcrição, evidência visual, extração estruturada, Knowledge Cards, alocação de capital |
| StrategyIntelligenceEmployee | `core/departments/strategy_intelligence/employee.py` | Extrai padrões, ferramentas, métricas de fontes | Pipeline de extração e detecção reutilizável | Não faz auditoria cética, Knowledge Cards, experimentos controlados |
| StrategyIntelligencePipeline | `core/departments/strategy_intelligence/pipeline.py` | 8 stages: validação, detecção de ferramentas, métricas, padrões, guardrails, handoff | DETECTING_TOOLS, DETECTING_METRICS podem ser reutilizados | Não faz análise visual, captura de frames, verificação de credibilidade |
| OrganizationalMemoryRuntime | `core/company/organizational_memory.py` | Memória institucional permanente com versionamento | Armazenamento de Knowledge Cards aprovados | Sem modelo para cards, experimentos, aprendizado; sem integração automática |
| QualityRuntime | `core/company/quality.py` | Qualidade rule-based com 4 categorias | Pode validar Knowledge Cards e experimentos | Sem regras específicas para alegações, credibilidade, fontes |
| ApprovalRuntime | `core/approval/runtime.py` | Fila de aprovação HITL | Reutilização completa para aprovação de experimentos e conhecimento | Sem integração com LearningPromotionReviewer |
| ProviderBudgetGuard | `core/tools/provider_control.py` | Controle de gasto REAL antes de chamadas | Reutilização completa para controle de custo de experimentos | Sem modelo para alocação de capital entre múltiplos experimentos |
| PersistenceRuntime | `core/company/persistence.py` | Persistência JSON de sessões, evidências, snapshots | Pode persistir decisões de aprendizado, Knowledge Cards | Sem schema específico |
| AudienceGrowthPlanner | `core/content_factory/audience_growth.py` | Conexão de evidências de tendências a briefs | Potencial consumidor de Knowledge Cards sobre tendências | Sem integração com fonte externa |
| GamingNewsDesk | `core/content_factory/gaming_news_desk.py` | Deduplicação e triagem de notícias de games | Padrão de deduplicação reutilizável | Domínio específico |
| ProductionEmployee (base) | `core/departments/base/employee.py` | Pipeline genérico com quality, metrics, hooks | Template para employee de aprendizado | Sem modelo específico para aprendizado |

## Cobertura do DailyLearningRadar

O DailyLearningRadar atual já cobre:

| Funcionalidade | Coberta? | Detalhes |
|---|---|---|
| Transcrição | **NÃO** | Espera transcript_text preenchido externamente |
| Evidência visual | **NÃO** | Espera screenshot_evidence preenchido externamente |
| Deduplicação | **SIM** | fingerprint por URL+título |
| Scoring | **SIM** | 4 dimensões (relevance, novelty, credibility, actionability) + risco |
| Risco promocional | **SIM** | _CLAIM_TERMS e _COPY_TERMS |
| Risco de compliance | **SIM** | Campo compliance_risk no LearningCandidate |
| Experimentos | **SIM** | LearningExperiment com hipótese, steps, métricas, guardrails |
| Aprovação do proprietário | **SIM** | owner_approval_required = True |
| Limites diários | **SIM** | max_selected (default 3) |
| Proibição de promoção automática | **SIM** | Guardrails explícitos |
| Captura de frames | **NÃO** | Fora do escopo atual |
| Ferramentas detectadas | **NÃO** | Sem extração estruturada |
| Knowledge Cards | **NÃO** | Saída é DailyLearningReport, não card reutilizável |
| Auditoria cética | **NÃO** | Sem verificação de credibilidade independente |
| Alocação de capital | **NÃO** | Sem modelo de custo ou orçamento |

---

# 3. Fluxo completo

```
Fonte bruta
  → [1] Source Collector
    → registra: título, URL, criador, data, duração, tema
    → saída: SourceRecord

  → [2] Transcript Indexer
    → recebe ou gera transcrição
    → preserva timestamps, falante, capítulos
    → saída: IndexedTranscript

  → [3] Visual Evidence Analyst
    → identifica trechos visuais candidatos
    → propõe captura de frames
    → saída: VisualEvidenceCandidates

  → [4] Intelligence Extractor
    → extrai ferramentas, estratégias, funis, processos, métricas, alegações
    → saída: ExtractionResult

  → [5] Skeptical Auditor
    → verifica credibilidade, conflito de interesse, evidência independente
    → classifica alegações
    → saída: AuditReport

  → [6] Knowledge Curator
    → transforma em Knowledge Cards
    → registra fonte, timestamps, confiança, riscos, validade
    → saída: tuple[KnowledgeCard, ...]

  → [7] Experiment Designer
    → transforma hipótese em teste controlado
    → define custo, métricas, condição de parada
    → saída: ExperimentProposal

  → [8] Aprovação do proprietário (ApprovalRuntime)
    → Leandro aprova, rejeita, ou modifica
    → saída: ApprovalDecision

  → [9] Execução do experimento
    → orçamento controlado, métricas registradas
    → saída: ExperimentResult

  → [10] Learning Promotion Reviewer
    → decide: aprovado, observação, rejeitado, arquivado
    → saída: LearningPromotionDecision

  → [11] Atualização de funcionários (futuro)
    → cards aprovados → OrganizationalMemory → departamentos
    → saída: EmployeeUpdateRecord
```

## Estados possíveis por etapa

| Etapa | Estados |
|---|---|
| SourceRecord | `received`, `transcribed`, `indexed`, `extracted`, `audited`, `card_created`, `experiment_proposed`, `owner_review`, `approved`, `rejected`, `archived` |
| KnowledgeCard | `draft`, `audited`, `owner_review`, `approved`, `experiment_pending`, `experiment_running`, `experiment_completed`, `promoted`, `archived` |
| ExperimentProposal | `draft`, `owner_review`, `approved`, `rejected`, `running`, `stopped`, `completed`, `inconclusive`, `promoted`, `archived` |
| LearningPromotionDecision | `promoted`, `observation`, `rejected`, `archived` |

---

# 4. Tipos de conteúdo aceitos

## Aceitos

- Podcasts (áudio + metadados)
- Entrevistas (vídeo ou áudio)
- Vídeos (YouTube, Vimeo, etc.)
- Aulas públicas
- Documentos (PDF, DOCX, Markdown)
- Estudos de caso
- Páginas web
- Transcrições fornecidas por Leandro
- Screenshots fornecidos
- Apresentações (slides)
- Relatórios
- Documentação oficial de ferramentas/APIs
- Artigos e newsletters

## Classificação por natureza

| Natureza | Definição | Tratamento |
|---|---|---|
| Fonte primária | Dado original (ex: print de dashboard, documentação oficial) | Maior peso, preservar origem |
| Fonte secundária | Relato de terceiros sobre o dado | Menor peso, exigir corroboração |
| Opinião | Análise ou interpretação pessoal | Não vira Knowledge Card sem evidência |
| Marketing | Conteúdo promocional | Marcado como promotional_claim |
| Prova | Evidência verificável | Preservar metadados de verificação |
| Alegação | Afirmação sem prova | Exigir auditoria cética |

---

# 5. Transcrição e indexação

## Modelo conceitual: TranscriptSource

```
TranscriptSource:
  source_id: string (hash)
  title: string
  url: string
  creator: string
  guests: tuple[string, ...]
  published_at: datetime
  duration_seconds: int
  language: string
  chapters: tuple[Chapter, ...]
  segments: tuple[TranscriptSegment, ...]
  tools_mentioned: tuple[string, ...]
  numbers_cited: tuple[string, ...]
  strategies_mentioned: tuple[string, ...]
  claims_made: tuple[string, ...]
  visual_candidates: tuple[VisualCandidate, ...]
  source_type: string  // "youtube", "podcast", "pdf", "manual"
  provided_by_owner: bool
  ingested_at: datetime
  fingerprint: string (SHA256)
```

## Modelo: TranscriptSegment

```
TranscriptSegment:
  timestamp_seconds: float
  speaker: string
  text: string
  chapter: string
  tools_detected: tuple[string, ...]
  metrics_detected: tuple[string, ...]
  has_visual_evidence: bool
  is_promotional: bool
  is_claim: bool
  confidence: float
```

---

# 6. Evidência visual

## Identificação de trechos que exigem screenshots

O sistema deve detectar frases gatilho na transcrição:
- "olha aqui na tela"
- "esse é o painel"
- "vou mostrar o funil"
- "esse gráfico"
- "essa ferramenta"
- "aqui no [nome do sistema]"
- "deixa eu abrir aqui"
- "como você pode ver"

## Modelo: VisualCandidate

```
VisualCandidate:
  transcript_segment_index: int
  timestamp_seconds: float
  trigger_phrase: string
  context_before: string
  context_after: string
  frame_before_offset: float  // -2s
  frame_during_offset: float  // 0s
  frame_after_offset: float   // +2s
  classification: VisualClassification
  confidence: float
  screenshot_path: string  // futuro: path do frame capturado
  related_transcript: string
```

## Classificação visual

| Classe | Descrição | Ação |
|---|---|---|
| visual_complementar | A tela mostra o que está sendo dito | Capturar frame, anexar ao segmento |
| visual_essencial | A informação só existe visualmente (dashboard, gráfico) | Capturar múltiplos frames, priorizar |
| demonstração | Uso de ferramenta passo-a-passo | Capturar sequência de frames |
| ferramenta | UI de ferramenta específica | Capturar, marcar para extração de ferramenta |
| gráfico | Dado quantitativo visual | Capturar, marcar para auditoria |
| número | Número na tela (faturamento, métrica) | Capturar, cruzar com transcrição |
| processo | Fluxograma, diagrama | Capturar frame completo |
| publicidade | Propaganda explícita | Descartar ou marcar como promotional |
| irrelevante | Rosto do apresentador, cena sem informação | Não capturar |

## Regras

- Capturar no máximo 3 frames por candidato visual (antes, durante, depois).
- Não capturar frames de rosto ou imagem pessoal sem relação com o conteúdo.
- Cada frame deve ter timestamp preciso e referência ao segmento da transcrição.
- Frames não devem ser reutilizados como criativo de publicação.
- Preservar URL e timestamp de origem para auditoria.

---

# 7. Extração de inteligência

## Modelos conceituais

### ToolMention

```
ToolMention:
  tool_id: string
  name: string
  category: string        // "affiliate_network", "marketplace", "creative_design", "checkout", "llm_gateway"...
  timestamp: float
  transcript_context: string
  screenshot_ref: string | null
  purpose_declared: string
  official_url: string | null
  pricing: string | null  // extraído ou "unknown"
  has_api: bool | null
  confidence: float
  nature: string          // "real", "claim", "inferred"
```

### StrategyPattern

Reutilizar modelo existente em `core/departments/strategy_intelligence/models.py`, adicionando:
- `source_timestamps: tuple[float, ...]`
- `screenshot_refs: tuple[str, ...]`
- `audit_status: str`  // "unverified", "partially_supported", "verified", "contradicted"

### FunnelPattern

```
FunnelPattern:
  funnel_id: string
  name: string
  traffic_source: string
  creative_type: string
  lead_capture: string
  front_end_product: string
  checkout: string
  upsell: string
  backend: string
  recurring: bool
  support: string
  metrics_cited: tuple[MetricMention, ...]
  costs_cited: tuple[CostClaim, ...]
  revenue_claims: tuple[RevenueClaim, ...]
  dependencies: tuple[string, ...]
  risks: tuple[string, ...]
  maturity_level: string  // "startup", "growth", "scale"
  timestamps: tuple[float, ...]
  screenshot_refs: tuple[str, ...]
  confidence: float
  audit_status: string
```

### ProcessPattern

```
ProcessPattern:
  process_id: string
  name: string
  steps: tuple[string, ...]
  tools_required: tuple[string, ...]
  estimated_effort: string
  estimated_cost: string
  risks: tuple[string, ...]
  alternatives: tuple[string, ...]
  timestamps: tuple[float, ...]
  confidence: float
  audit_status: string
```

### BusinessModelPattern

```
BusinessModelPattern:
  model_id: string
  name: string
  revenue_streams: tuple[string, ...]
  cost_structure: tuple[string, ...]
  customer_acquisition: string
  unit_economics: string
  scalability: string
  risks: tuple[string, ...]
  timestamps: tuple[float, ...]
  confidence: float
  audit_status: string
```

### FailurePattern

```
FailurePattern:
  failure_id: string
  title: string
  context: string
  mistake: string
  consequence: string
  lesson: string
  avoidable: bool
  timestamps: tuple[float, ...]
  screenshot_refs: tuple[str, ...]
  confidence: float
  audit_status: string
```

### MetricMention

Reutilizar modelo existente (`core/departments/strategy_intelligence/models.py`), adicionando:
- `timestamp: float`
- `screenshot_ref: string | null`
- `context: string`

### RevenueClaim

```
RevenueClaim:
  claim_id: string
  amount: float | null
  currency: string | null
  period: string | null        // "monthly", "annual", "lifetime"
  is_profit: bool | null       // true = lucro, false = faturamento, null = ambíguo
  source_timestamp: float
  source_context: string
  screenshot_ref: string | null
  has_independent_evidence: bool
  audit_result: string         // "verified", "unverified", "contradicted", "promotional"
```

### CostClaim

```
CostClaim:
  cost_id: string
  description: string
  amount: float | null
  currency: string | null
  period: string | null
  source_timestamp: float
  source_context: string
  audit_result: string
```

### SoftwareOpportunity

```
SoftwareOpportunity:
  opportunity_id: string
  tool_name: string
  problem_solved: string
  current_pricing: string | null
  api_available: bool | null
  competitors: tuple[string, ...]
  our_advantage: string | null
  estimated_build_effort: string
  estimated_cost: string
  revenue_potential: string | null
  risks: tuple[string, ...]
  timestamps: tuple[float, ...]
  confidence: float
  status: string  // "identified", "researching", "proposed", "approved", "building", "built", "rejected"
```

### KnowledgeCandidate

```
KnowledgeCandidate:
  candidate_id: string
  source_id: string
  source_url: string
  source_timestamps: tuple[float, ...]
  title: string
  summary: string
  patterns: tuple[StrategyPattern | FunnelPattern | ProcessPattern | ...]
  tools: tuple[ToolMention, ...]
  metrics: tuple[MetricMention, ...]
  claims: tuple[RevenueClaim | CostClaim, ...]
  failures: tuple[FailurePattern, ...]
  opportunities: tuple[SoftwareOpportunity, ...]
  visual_evidence: tuple[VisualCandidate, ...]
  audit_report: AuditReport
  confidence: float
  departments_interested: tuple[string, ...]
  created_at: datetime
  status: string
```

### KnowledgeCard

```
KnowledgeCard:
  card_id: string
  version: int
  title: string
  summary: string
  hypothesis: string
  sources: tuple[KnowledgeCandidate, ...]
  tools: tuple[ToolMention, ...]
  patterns: tuple[Pattern, ...]
  confidence: float
  applicability: string  // "broad", "niche", "experimental"
  departments: tuple[string, ...]
  risks: tuple[string, ...]
  estimated_cost: float
  restrictions: tuple[string, ...]
  created_at: datetime
  valid_until: datetime | null
  next_review: datetime | null
  experiment_id: string | null
  experiment_result: ExperimentResult | null
  status: string  // "draft", "audited", "owner_review", "approved", "experiment_pending", "experiment_running", "experiment_completed", "promoted", "archived"
  promoted_at: datetime | null
  archived_at: datetime | null
```

### ExperimentProposal

```
ExperimentProposal:
  experiment_id: string
  card_id: string
  hypothesis: string
  baseline: string
  variant: string
  max_budget_usd: float
  max_duration_days: int
  success_metric: string
  success_threshold: float
  stop_condition: string
  risks: tuple[string, ...]
  approval_id: UUID | null
  approval_status: string
  providers_required: tuple[string, ...]
  channel: string
  auto_publish: bool  // sempre false para aprendizado
  storage_path: string
  created_at: datetime
  started_at: datetime | null
  completed_at: datetime | null
  status: string  // "proposed", "owner_review", "approved", "rejected", "running", "stopped", "completed", "inconclusive", "promoted", "archived"
```

### ExperimentResult

```
ExperimentResult:
  experiment_id: string
  metric_value: float
  baseline_value: float | null
  improvement_pct: float | null
  cost_usd: float
  duration_days: int
  conclusions: tuple[string, ...]
  recommendations: tuple[string, ...]
  raw_data: dict
  measured_at: datetime
```

### LearningPromotionDecision

```
LearningPromotionDecision:
  decision_id: string
  card_id: string
  experiment_id: string | null
  result: ExperimentResult | null
  decision: string  // "promoted", "observation", "rejected", "archived"
  decided_by: string
  reason: string
  decided_at: datetime
  valid_until: datetime | null
  next_review: datetime | null
```

---

# 8. Ferramentas mencionadas

## Fluxo para cada ferramenta descoberta

```
Nome citado + timestamp + screenshot
  → finalidade declarada (extraída da transcrição)
  → pesquisa oficial futura (fora do escopo MOCK)
  → preço (se disponível)
  → API disponível?
  → alternativas conhecidas
  → risco de dependência
  → possível integração com a fábrica
  → decisão: integrar, monitorar, ignorar
```

## Regras

- O sistema não presume que uma ferramenta mencionada é boa ou necessária.
- Ferramentas sem site oficial, documentação ou preço público são marcadas como `unverifiable`.
- Ferramentas de scraping, automação de contas, ou anti-detecção são marcadas como `policy_risk`.
- Cada menção preserva o contexto original para evitar interpretação isolada.

---

# 9. Estratégias e funis

## Estrutura para registrar

```
FunnelRecord:
  funnel_id: string
  name: string
  problem_solved: string
  traffic_source: string     // "organico", "pago", "indicacao", "parceria"
  creative_type: string       // "post", "video", "landing_page"
  landing_page: string | null
  lead_capture: string | null
  front_end: string           // produto inicial
  checkout: string            // plataforma de checkout
  upsell: string | null
  backend: string | null     // produto de alto valor
  recurring: bool
  support: string | null
  metrics_cited: tuple[string, ...]
  costs_cited: tuple[string, ...]
  revenue_cited: tuple[string, ...]
  dependencies: tuple[string, ...]
  risks: tuple[string, ...]
  target_audience: string
  maturity_required: string   // "founder", "team", "agency"
  timestamps: tuple[float, ...]
  screenshot_refs: tuple[str, ...]
  confidence: float
  audit_status: string
```

---

# 10. Auditoria cética

## Regras para identificar problemas

| Problema | Gatilho | Classificação |
|---|---|---|
| Promessa financeira | "ganhe dinheiro", "fature", "renda extra" | promotional_claim |
| Faturamento sem lucro | menciona receita, não menciona custo | unverified |
| Cherry-picking | "esse produto deu certo" sem mostrar fracassos | partially_supported |
| Resultado acumulado | "já faturei X" sem período | unverified |
| Resultado sem período | "estou faturando X" sem desde quando | unverified |
| Ausência de custo | menciona receita, não menciona tráfego/ferramentas/equipe | unverified |
| Viés de sobrevivência | só mostra winners | partially_supported |
| Conflito de interesse | está vendendo curso/mentoria sobre o assunto | promotional_claim |
| Venda de curso | "meu curso ensina", "compre meu método" | promotional_claim |
| Link afiliado | URL com hoplink, ref, ou parâmetro de afiliado | promotional_claim |
| Dependência de autoridade | "eu consegui porque tenho audiência" | not_applicable (para quem não tem) |
| Dependência de equipe | "meu time faz isso" sem detalhar o processo | not_applicable |
| Informação antiga | data > 6 meses para estratégia digital | outdated |
| Plataforma alterada | "Facebook era assim" (mudou) | outdated |
| Política proibida | "automatiza WhatsApp", "clona criativo" | policy_violation |
| Prova insuficiente | alegação sem print, dado, ou referência | unverified |

## Classificações de alegação

| Classe | Significado | Ação |
|---|---|---|
| verified | Evidência independente encontrada | Pode virar Knowledge Card |
| partially_supported | Parte da alegação tem suporte | Exigir mais fontes |
| unverified | Sem evidência independente | Não virar card sem corroboração |
| promotional_claim | Propaganda ou venda | Descartar ou marcar |
| contradicted | Outra fonte contradiz | Investigar |
| outdated | Informação desatualizada | Arquivar |
| not_applicable | Depende de recurso que não temos | Ignorar |

---

# 11. Knowledge Cards

## Campos obrigatórios

```
KnowledgeCard:
  card_id: string
  version: int
  title: string
  summary: string (max 500 chars)
  hypothesis: string
  sources: tuple[SourceRef, ...]     // cada SourceRef: url, timestamp, screenshot
  confidence: float                  // 0.0 a 1.0
  applicability: string              // "broad", "niche", "experimental"
  departments: tuple[string, ...]    // departamentos interessados
  risks: tuple[string, ...]
  estimated_cost_usd: float
  restrictions: tuple[string, ...]   // pré-requisitos
  created_at: datetime
  valid_until: datetime | null
  next_review: datetime | null
  experiment_id: string | null
  experiment_result_ref: string | null
  status: string                     // ver seção 3
```

## Regras

- Nenhum Knowledge Card é criado a partir de uma frase isolada.
- Mínimo de 2 fontes independentes para confiança > 0.7.
- Cards com confiança < 0.5 não entram em experimento sem aprovação explícita do proprietário.
- Todo card tem data de validade (default 90 dias).
- Cards arquivados podem ser reativados com nova evidência.

---

# 12. Experimentos controlados

## Estrutura do experimento

```
ExperimentProposal:
  experiment_id: string
  card_id: string
  hypothesis: string
  baseline: string                    // comportamento atual
  variant: string                     // o que testar
  max_budget_usd: float
  max_duration_days: int
  success_metric: string              // ex: "click_through_rate"
  success_threshold: float            // ex: 0.05 (5% de melhora)
  stop_condition: string              // ex: "se custo > 2x estimado"
  risks: tuple[string, ...]
  owner_approval_required: bool       // sempre true
```

## Estados possíveis

| Estado | Significado |
|---|---|
| proposed | Rascunho criado pelo sistema |
| owner_review | Aguardando Leandro |
| approved | Liberado para execução |
| rejected | Negado por Leandro |
| running | Em execução com orçamento controlado |
| stopped | Interrompido por condição de parada |
| completed | Executado com métricas |
| inconclusive | Resultado não permite conclusão |
| promoted | Conhecimento promovido após resultado |
| archived | Arquivado sem promoção |

---

# 13. Atualização dos funcionários

## Fluxo futuro

1. Apenas cards com status `promoted` podem ser enviados a funcionários.
2. O sistema envia apenas para departamentos listados em `card.departments`.
3. Cada envio preserva versão (cards são imutáveis, versão nova = novo card).
4. O OrganizationalMemoryRuntime registra:
   - `card_id`
   - `version`
   - `promoted_at`
   - `promoted_by` (quem aprovou)
   - `departments` (quem recebeu)
   - `next_review` (data de revisão obrigatória)
5. Cards vencidos ou refutados geram notificação de revisão.

## O que NÃO é enviado

- Transcrição inteira
- Opinião bruta
- Propaganda
- Promessa financeira
- Instrução sem teste

---

# 14. Inteligência em massa

## Padrões que múltiplas fontes podem gerar

- **Padrões recorrentes:** mesma ferramenta/estratégia citada por 3+ fontes independentes.
- **Consenso:** múltiplas fontes concordam sobre um método.
- **Divergência:** fontes discordam — investigar e registrar contradição.
- **Ferramentas emergentes:** mesma ferramenta citada por múltiplas fontes recentes.
- **Estratégias em queda:** estratégia que fontes antigas recomendavam e fontes novas abandonaram.
- **Oportunidades de software:** mesmo problema resolvido por diferentes ferramentas pagas.
- **Problemas comuns:** mesmo erro cometido por diferentes pessoas.
- **Modelos de receita:** padrão de monetização que aparece em múltiplos contextos.
- **Sinais fracos:** menção isolada de algo potencialmente relevante.
- **Ideias de novos braços:** combinação de padrões que sugere um novo departamento.

## Limites

- Quantidade de menções **não** substitui verificação.
- 3 menções da mesma ferramenta = "mencionada por 3 fontes", não "ferramenta essencial".
- Consenso entre fontes do mesmo segmento não é evidência universal.
- Divergência entre fontes deve ser registrada, não resolvida por votação.

---

# 15. CEO e alocação de capital

## Fluxo

```
Orçamento disponível (definido por Leandro)
  → oportunidades aprovadas (cards com experimento aprovado)
  → risco (score do Skeptical Auditor)
  → confiança (score do Knowledge Card)
  → custo estimado (do ExperimentProposal)
  → retorno possível (estimado, sem promessa)
  → carteira de experimentos (distribuição proposta)
  → aprovação de Leandro
  → execução (orçamento controlado via ProviderBudgetGuard)
  → monitoramento (métricas em tempo real)
  → interrupção (se stop_condition for atingida)
  → escala (apenas após resultado medido e nova aprovação)
```

## Regras

- O CEO pode recomendar **não investir** — e essa decisão é registrada.
- Nenhuma promessa de lucro é aceita como justificativa de gasto.
- Nenhuma movimentação automática de dinheiro.
- Nenhum gasto sem autorização individual por experimento.
- Escala apenas após resultado medido e nova aprovação.

---

# 16. Interface futura (dashboard)

## Telas propostas

1. **Caixa de entrada de fontes** — URLs pendentes de processamento.
2. **Transcrições** — transcrições indexadas com busca por timestamp, falante, ferramenta.
3. **Linha do tempo visual** — frames capturados organizados por timestamp.
4. **Ferramentas descobertas** — catálogo de ferramentas com fontes, preço, API.
5. **Estratégias** — padrões extraídos com confiança e status de auditoria.
6. **Funis** — estruturas de funil registradas com diagrama conceitual.
7. **Alegações** — claims com resultado da auditoria cética.
8. **Knowledge Cards** — fichas de conhecimento com versões e histórico.
9. **Experimentos** — propostas, execução, resultados.
10. **Aprendizados aprovados** — cards promovidos que viraram conhecimento oficial.
11. **Padrões de mercado** — consenso/divergência entre múltiplas fontes.
12. **Oportunidades de software** — tools que podemos construir.
13. **Alocação de capital** — orçamento, carteira de experimentos, resultados financeiros.

Não implementar ainda.

---

# 17. Arquitetura proposta

## Opções avaliadas

### A. Expandir DailyLearningRadar

Vantagens:
- Aproveita estrutura existente (LearningCandidate, LearningExperiment, guardrails, score)
- Mínimo esforço inicial
- Consistência com o que já foi validado

Riscos:
- DailyLearningRadar foi desenhado para triagem diária, não para fluxo completo de aprendizado
- Adicionar transcrição, captura de frames, extração estruturada, auditoria cética, Knowledge Cards sobrecarregaria a classe
- Violaria o princípio de responsabilidade única

### B. Criar novo domínio: `core/market_intelligence_learning/`

Vantagens:
- Separação clara de responsabilidades
- Pode crescer sem afetar o DailyLearningRadar existente
- Modelos específicos sem poluir outros domínios

Riscos:
- Código novo sem validação prévia
- Risco de duplicação com StrategyIntelligence
- Precisa de pipeline, employee, modelos do zero

### C. Criar novo departamento: `core/departments/market_intelligence/`

Vantagens:
- Segue o padrão arquitetural comprovado (ProductionEmployee → hooks → pipeline)
- Reutiliza base department layer
- Pode ser orquestrado pelo CompanyOrchestrator
- Observabilidade via snapshots

Riscos:
- Departamento pressupõe produção (pipeline com stages), mas o fluxo de aprendizado não é exatamente "produção"
- Employee de aprendizado seria diferente de um ProductionEmployee típico
- Experimentos e conhecimento não são "produtos" como vídeo/áudio/imagem

### D. Arquitetura híbrida (RECOMENDADA)

```
core/market_intelligence_learning/     ← domínio
  collector.py                         ← Source Collector
  transcript_indexer.py                 ← Transcript Indexer
  visual_analyst.py                     ← Visual Evidence Analyst
  extractor.py                          ← Intelligence Extractor
  auditor.py                            ← Skeptical Auditor
  curator.py                            ← Knowledge Curator
  experiment_designer.py                ← Experiment Designer
  promotion_reviewer.py                 ← Learning Promotion Reviewer
  capital_allocator.py                  ← CEO Capital Allocation Advisor
  models.py                             ← todos os modelos conceituais
  adapter.py                            ← ponte para o DailyLearningRadar

core/departments/market_intelligence/  ← departamento (opcional, fase futura)
  employee.py                          ← MarketIntelligenceEmployee
  pipeline.py                          ← MarketIntelligencePipeline (se virar produção)
  models.py                            ← modelos específicos do departamento
```

A camada de domínio contém a lógica. O departamento (futuro) é a interface com o CompanyOrchestrator se o aprendizado precisar ser orquestrado como produção.

O DailyLearningRadar permanece intacto como triagem diária. O novo domínio pode consumir candidatos do radar ou receber fontes diretamente de Leandro.

## Árvore futura (conceitual, sem criar arquivos)

```
core/market_intelligence_learning/
  __init__.py
  models.py                 # Todos os modelos frozen+slots
  collector.py              # SourceCollector: recebe links, registra
  transcript_indexer.py     # TranscriptIndexer: processa transcrição
  visual_analyst.py         # VisualEvidenceAnalyst: detecta frames
  extractor.py              # IntelligenceExtractor: ferramentas/metricas/padroes
  auditor.py                # SkepticalAuditor: verifica credibilidade
  curator.py                # KnowledgeCurator: cria Knowledge Cards
  experiment_designer.py    # ExperimentDesigner: propõe experimentos
  promotion_reviewer.py     # LearningPromotionReviewer: decide promoção
  capital_allocator.py      # CapitalAllocationAdvisor: aloca orçamento
  daily_bridge.py           # Ponte para DailyLearningRadar
```

---

# 18. Fases do projeto

| Fase | Descrição | Responsável | Dependência | Risco | Critério de conclusão | DeepSeek pode? | Codex? | Leandro? |
|---|---|---|---|---|---|---|---|---|
| 1 | Documentação estratégica (esta) | DeepSeek | Nenhuma | Baixo | Documento aprovado | SIM | Revisar | Ler |
| 2 | Protótipo visual isolado | DeepSeek | Fase 1 | Baixo | UI funcional navegável | SIM | Revisar | Validar |
| 3 | Modelos MOCK frozen+slots | DeepSeek | Fase 1 | Baixo | 0 erros de compilação | SIM | Revisar | — |
| 4 | Análise de transcrição fornecida por Leandro | DeepSeek | Fase 3 | Baixo | Extração de 1 fonte real com dados MOCK | SIM | Revisar | Fornecer transcrição |
| 5 | Indexação e timestamps | DeepSeek | Fase 3 | Médio | TranscriptSource funcional | SIM | Revisar | — |
| 6 | Evidência visual simulada | DeepSeek | Fase 5 | Médio | VisualCandidate funcional | SIM | Revisar | — |
| 7 | Knowledge Cards | Codex | Fase 3-6 | Médio | Card persiste e versiona | NÃO | SIM | — |
| 8 | Experimentos | Codex | Fase 7 | Alto (custo) | Experimento executa em MOCK | NÃO | SIM | Aprovar |
| 9 | Integração DailyLearningRadar | Codex | Fase 3 | Médio | Radar alimenta o novo fluxo | NÃO | SIM | — |
| 10 | Integração OrganizationalMemory | Codex | Fase 7 | Médio | Cards aprovados persistem | NÃO | SIM | — |
| 11 | Dashboard | Codex + Shin | Fase 7-10 | Médio | Aba funcional no dashboard | NÃO | SIM | Validar |
| 12 | Transcrição real (API) | Codex | Fase 5 | Alto (custo, termos) | 1 transcrição real via API contratada | NÃO | SIM | Contratar |
| 13 | Captura real de frames | Codex | Fase 6 | Alto (termos, copyright) | 1 frame capturado com permissão | NÃO | SIM | Autorizar |
| 14 | Pesquisa e verificação | Codex | Fase 12 | Alto | SkepticalAuditor funcional com fonte real | NÃO | SIM | — |
| 15 | Aprendizado em massa | Codex | Fase 10-14 | Alto | 10+ fontes processadas | NÃO | SIM | — |
| 16 | Alocação de capital | Codex | Fase 8, 15 | Muito alto | Orçamento alocado e monitorado | NÃO | SIM | Definir orçamento |

---

# 19. Riscos

| Risco | Probabilidade | Impacto | Mitigação |
|---|---|---|---|
| Direitos autorais da transcrição | Alta | Médio | Usar apenas fontes fornecidas por Leandro; não baixar vídeos automaticamente |
| Termos de plataforma (YouTube, Spotify) | Alta | Alto | Não fazer scraping; usar APIs oficiais ou conteúdo manual |
| Download de vídeos | Média | Muito alto | **Proibido.** Apenas transcrições fornecidas |
| Transcrição via IA (alucinação) | Alta | Médio | Preservar timestamps; permitir verificação humana |
| Screenshots de terceiros (copyright) | Alta | Alto | Não reutilizar como criativo; apenas para análise interna |
| Privacidade (voz, rosto, dados) | Média | Alto | Não armazenar biometria; não publicar imagem sem consentimento |
| Informação falsa na fonte | Alta | Médio | Auditoria cética antes de qualquer card |
| Propaganda disfarçada de conteúdo | Alta | Médio | Regras de detecção promocional |
| Alucinação da IA na extração | Alta | Médio | Confiança decrescente; revisão humana obrigatória |
| Viés do especialista | Alta | Baixo | Múltiplas fontes exigidas para confiança > 0.7 |
| Conteúdo antigo | Média | Médio | Data de validade em todo card |
| Custo de transcrição (API paga) | Média | Médio | Apenas após aprovação de orçamento |
| Armazenamento de transcrições/frames | Média | Baixo | Compressão e limite de retenção |
| Uso excessivo de contexto LLM | Alta | Médio | Processamento segmentado; índice antes da extração |
| Conhecimento contraditório | Alta | Baixo | Sistema registra divergência; não resolve automaticamente |
| Atualização indevida de funcionários | Baixa | Muito alto | Múltiplos gates (auditoria → experimento → aprovação → promoção) |
| Promessa financeira nos cards | Média | Alto | Auditoria cética obrigatória; "promotional_claim" bloqueia card |
| Gasto automático sem autorização | Baixa | Muito alto | ProviderBudgetGuard + aprovação explícita por experimento |

---

# 20. Decisões pendentes

## Obrigatórias agora

- [ ] Leandro confirma que quer seguir com esta vertical?
- [ ] Nome final: "Market Intelligence & Learning" ou "Departamento de Inteligência e Aprendizado de Mercado"?

## Produto

- [ ] Knowledge Cards entram no OrganizationalMemory ou em storage próprio?
- [ ] Cards têm validade padrão de 90 dias? Quem define por card?
- [ ] Quantas fontes mínimas para um card ser "verified"?

## Técnicas

- [ ] Arquitetura híbrida (domínio + departamento futuro) é a recomendada?
- [ ] Reutilizar StrategyIntelligencePipeline ou criar pipeline próprio?
- [ ] Integration tests rodam contra dados MOCK ou reais anonimizados?

## Legais

- [ ] Leandro confirma que as fontes são de consumo próprio e não violam termos?
- [ ] Screenshots para análise interna são permitidas?
- [ ] Transcrições de podcasts públicos podem ser armazenadas?

## Financeiras

- [ ] Orçamento para transcrição via API (ex: Whisper, AssemblyAI)?
- [ ] Orçamento para experimentos (ex: R$ 200/mês para testes controlados)?
- [ ] Limite por experimento individual?

## Fontes

- [ ] Leandro fornecerá as primeiras 3-5 fontes para teste manual?
- [ ] Formato preferido: link YouTube, PDF, transcrição colada, ou áudio?
- [ ] Há preferência por nicho/assunto específico?

## Dashboard

- [ ] Aba separada no dashboard existente ou link externo?
- [ ] Prioridade: qual tela primeiro (caixa de entrada, cards, experimentos)?

## IA

- [ ] DeepSeek pode criar protótipo visual (Fase 2)?
- [ ] DeepSeek pode implementar modelos MOCK (Fase 3)?

## Armazenamento

- [ ] Transcrições são mantidas indefinidamente ou expiram?
- [ ] Frames capturados são mantidos ou descartados após análise?

## Automação

- [ ] Alguma etapa pode ser automatizada sem revisão humana?
- [ ] Score mínimo para extração automática vs. revisão obrigatória?

## Aprovação

- [ ] Leandro quer aprovar cada experimento individualmente?
- [ ] Ou prefere aprovar um orçamento mensal e delegar execução?

---

# 21. Segurança do repositório

- Existem mudanças locais do Codex no working tree (CRLF warnings, arquivos pré-modificados).
- A pasta `docs/external_llm_inbox/deepseek/` é não rastreada (git ignore ou novo diretório).
- Nenhum arquivo oficial (`core/`, `apps/`, `demo_*.py`, `scripts/`, etc.) foi alterado.
- Qualquer integração ao core deve esperar revisão e implementação do Codex.
- Protótipos futuros (Fase 2) devem permanecer em `prototypes/external_llm/market_intelligence_learning/`.

---

# 22. Status

**Status:** PROPOSTA - NAO IMPLEMENTADA

**Origem estratégica:** Leandro Vieira, com estruturação do GPT da Web

**Executor documental desta fase:** DeepSeek, exclusivamente dentro do workspace seguro

**Revisor e integrador esperado:** Codex
