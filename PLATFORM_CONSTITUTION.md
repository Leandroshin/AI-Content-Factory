# PLATFORM CONSTITUTION

**AI Content Factory — Constituição Oficial da Plataforma**
*Atualizada em Julho de 2026 — Reflete o estado real da arquitetura após auditoria completa.*

---

## 1. Visão da Plataforma

### Objetivo

A AI Content Factory é uma **Empresa Digital de IA** — uma plataforma modular de criação de conteúdo que orquestra employees digitais, workflows, decisões, execução de tarefas, aprendizado contínuo, estratégia e otimização para operar qualquer vertical de negócio de forma autônoma, determinística e rastreável.

A plataforma **é a empresa**. Ela não é um sistema especializado em um único nicho. Ela é uma companhia digital completa que pode ser especializada para qualquer mercado.

### Problema que resolve

- **Automação de ponta a ponta**: desde o recebimento de uma tarefa até a execução, aprendizado e otimização contínua, sem intervenção humana.
- **Determinismo e rastreabilidade**: cada decisão é registrada, cada execução é rastreável, cada resultado é mensurável.
- **Separação Foundation vs. Runtime**: toda lógica de negócio vive em Foundations stateless; runtimes stateful gerenciam apenas ciclo de vida e estado.
- **Frozen Dataclasses como contratos imutáveis**: snapshots são a verdade única — nunca objetos mutáveis.
- **Sem dependências externas no core**: o pacote core não depende de banco de dados, filas, serviços externos ou frameworks pesados.
- **Vertical-agnóstico**: a mesma empresa digital pode operar criação de conteúdo, análise de mercado, trading, e-commerce ou qualquer outro domínio.

### O que a plataforma NÃO pretende ser

- **Não é um sistema de cortes** — não é um editor de vídeo.
- **Não é um sistema para GTA 6** — GTA 6 é apenas uma especialização possível, não o propósito da plataforma.
- **Não é um framework web** — não há rotas HTTP, controllers, ou middlewares no core.
- **Não é um ORM** — não há mapeamento objeto-relacional. A persistência é JSON puro via pathlib.
- **Não é um sistema de filas distribuídas** — o EventBus é síncrono e in-memory.
- **Não é um serviço SaaS** — não há autenticação, multi-tenancy, ou API REST pública.
- **Não é um motor de inferência ML** — predições são puramente heurísticas; não há modelos treinados no core.
- **Não é um sistema de tempo real** — não há websockets, streaming, ou processamento assíncrono.
- **Não é opinativo sobre provedores de LLM** — o LLM Gateway é agnóstico via adapter pattern.

---

## 2. Filosofia Arquitetural

### Princípios Fundamentais

| # | Princípio | Descrição |
|---|-----------|-----------|
| 1 | **Foundation primeiro** | Toda funcionalidade começa como Foundation (stateless) antes de se tornar Runtime (stateful). |
| 2 | **Runtime depois** | Runtimes stateful só existem quando o Foundation está completo e validado. |
| 3 | **Stateless antes de Stateful** | A lógica de negócio nunca depende de estado. Estado é gerenciado separadamente. |
| 4 | **Frozen Dataclasses** | Todos os modelos de dados são frozen dataclasses imutáveis. Nada é mutável. |
| 5 | **Determinismo** | Dado o mesmo input, o mesmo método retorna o mesmo output. Sem side effects. |
| 6 | **Compatibilidade reversa obrigatória** | Nenhuma mudança quebra demos existentes. Regressão completa obrigatória. |
| 7 | **Sem dependências circulares** | A cadeia de dependência é estritamente unidirecional. |
| 8 | **Sempre criar demo** | Todo módulo novo precisa de um demo com 200+ cenários antes de ser aceito. |
| 9 | **Sempre executar compileall** | `python -m compileall core/` obrigatório antes de qualquer commit. |
| 10 | **Sempre executar regressão** | Todos os demos existentes devem passar com 0 falhas. |
| 11 | **Sempre entregar relatório padrão** | PASS/FAIL contabilizado com `Total: X/Y passed, Z failed`. |
| 12 | **Contract-First** | Módulos com contratos (Protocol/ABC) antes de implementações concretas. |
| 13 | **Eventos como contratos**, não como transporte | Eventos são frozen dataclasses, não dicionários soltos. |
| 14 | **Dependency Injection para IO** | LLM, persistência, eventos são injetados via callables. |
| 15 | **Um módulo, uma responsabilidade** | Nenhum módulo faz mais de uma coisa. |
| 16 | **Snapshots como fonte da verdade** | Toda comunicação entre módulos usa snapshots. |
| 17 | **EventBus opcional** | Nenhum runtime é obrigado a usar EventBus. |
| 18 | **PersistenceRuntime opcional** | Nenhum runtime é obrigado a persistir. |
| 19 | **Sem dependências de engine no core** | `core/` não importa nada de `engines/`. |
| 20 | **Zero AI no core** | O core não faz chamadas de LLM, embeddings, ou qualquer inferência. |
| 21 | **Vertical-agnóstico** | A plataforma é uma empresa digital, não um sistema de nicho. |

### Princípios de Desenvolvimento

- Nenhum arquivo existente é modificado durante a criação de um novo módulo.
- Novos módulos são sempre adicionados, nunca alteram os existentes.
- Toda nova funcionalidade começa como um problema arquitetural, não como uma feature.
- Nomenclatura consistente: Foundation, Runtime, Pipeline, Snapshot, Trace, Result.

---

## 3. Camadas da Plataforma

### Ordem hierárquica (de baixo para cima)

```text
Fundação (Core Base)
    ↓
Infraestrutura (Config, Logging, Exceptions, Models)
    ↓
Container / Pipeline / Prompts (Contratos — módulos mortos não utilizados)
    ↓
Eventos (Events)
    ↓
Conversação (Conversation)
    ↓
Memória (Memory)
    ↓
Conhecimento (Knowledge)
    ↓
Aprendizado (Learning)
    ↓
Habilidades (Skills)
    ↓
Workflow Fundacional (Workflow Foundation)
    ↓
Workflow Stateful (Workflows)
    ↓
Tarefas (Tasks)
    ↓
Execução (Execution)
    ↓
Monitoramento (Monitoring)
    ↓
Analytics (Analytics / Performance)
    ↓
Estratégia (Strategy Foundation)
    ↓
Políticas (Policy Foundation)
    ↓
Pipeline de Estratégia (Strategy Pipeline)
    ↓
Plano de Execução (Execution Plan)
    ↓
Otimização (Optimization)
    ↓
Feedback (Feedback)
    ↓
Histórico (Historical)
    ↓
Predição (Prediction)
    ↓
Colaboração (Collaboration)
    ↓
Empregados (Employees)
    ↓
Departamentos (Departments)
    ↓
Organização (Organization)
    ↓
Orquestração (Orchestrator)
    ↓
Company Runtime
    ↓
LLM Gateway (Infraestrutura transversal)
    ↓
Persistence (Infraestrutura transversal — sem __init__.py)
```

### Responsabilidade de cada camada

| Camada | Responsabilidade |
|--------|------------------|
| **Core Base** | Módulos raiz: logging, config, exceptions, models. Nenhuma dependência de runtime. |
| **Infraestrutura** | Contêiner DI, pipeline executor (morto), prompts (morto). |
| **Eventos** | EventBus, 25 eventos de domínio, contratos de subscrição/publicação. |
| **Conversação** | Sessões de conversa, mensagens, contexto. Foundation stateless (sem snapshot). |
| **Memória** | Registros de memória, snapshots. Foundation stateless. |
| **Conhecimento** | Registros de conhecimento, promoção de memória. Foundation + Runtime stateful. |
| **Aprendizado** | Recomendações de aprendizado + pipeline integrado. Foundation stateless. |
| **Habilidades** | Registros de skills, níveis, XP. Foundation stateless + Runtime stateful. |
| **Workflow Foundation** | Definição de workflows, steps, execuções. ⚠️ Naming collision com WorkflowRuntime. |
| **Workflows Stateful** | Coordenação de workflows com DAG, paralelismo, branching. |
| **Tarefas** | Ciclo de vida de tarefas, estados, transições. |
| **Execução** | Pipeline: prepare → execute → validate → result. LLM via DI. |
| **Monitoramento** | Observabilidade orientada a eventos, health scores, snapshots. |
| **Analytics** | Agregação de métricas de performance. |
| **Estratégia** | Recomendações estratégicas a partir de múltiplos snapshots. |
| **Políticas** | Avaliação de regras de política (approve/reject/escalate). ⚠️ Duplicado com core/policies/. |
| **Pipeline de Estratégia** | Conecta Estratégia → Políticas → Plano de Execução. |
| **Plano de Execução** | Transforma plano validado em ações concretas. |
| **Otimização** | Executa ações aprovadas com retry/rollback/cooldown. |
| **Feedback** | Compara resultados esperados vs reais. |
| **Histórico** | Comparação temporal de snapshots before/after. |
| **Predição** | Projeção heurística de futuro baseada em tendências históricas. ⚠️ Sem consumidores. |
| **Colaboração** | Orquestração de request/response entre employees. |
| **Empregados** | Ciclo de vida de employees + cognição (thought pipeline). |
| **Departamentos** | Ciclo de vida de departamentos, registro de employees. |
| **Organização** | Hierarquia organizacional, business units, divisões. |
| **Orquestração** | Pipeline completo: decisão → execução → aprendizado. |
| **Company Runtime** | Runtime central da empresa, gerencia estado global e tarefas. |
| **LLM Gateway** | Gateway de LLM, adapters, prompts, cost tracking. Transversal. |
| **Persistence** | Persistência JSON via pathlib. ⚠️ Sem `__init__.py`. |

### Regras de Dependência

**Permitido:**
- Foundation → Foundation (apenas se estritamente necessário)
- Foundation → Core/Infraestrutura (sempre permitido)
- Runtime → Foundation (sempre permitido)
- Pipeline → Foundation(s) (sempre permitido)
- Camadas superiores → camadas inferiores (sempre permitido)

**Proibido:**
- Foundation → Runtime (Foundation nunca depende de Runtime)
- Camada inferior → camada superior (dependência ascendente)
- Core → Engines (core nunca importa engines)
- Qualquer módulo → módulo que ele ajudaria a criar (dependência circular)
- Runtime A → Runtime B diretamente (comunicação via snapshots, não via objetos runtime)

---

## 4. Mapa Completo dos Módulos

### Legenda

| Símbolo | Significado |
|---------|-------------|
| ✅ | Completo (Foundation + Runtime + Snapshot + Events) |
| ⚠️ | Parcial (falta algum elemento) |
| 🔴 | Pendente (tem anomalia crítica) |
| 💀 | Morto (zero imports de produção) |

### 4.1 `core/conversation/` ⚠️ PARCIAL

| Campo | Valor |
|-------|-------|
| **Responsabilidade** | Sessões de conversa, mensagens, contexto |
| **Snapshots** | ❌ Nenhum |
| **Eventos** | ❌ Nenhum |
| **Dependências** | `core/memory/runtime.py` |
| **Demo** | `demo_conversation_runtime_foundation.py` (259 linhas) |
| **Observação** | Foundation lógica embutida no runtime.py (padrão inconsistente) |

### 4.2 `core/memory/` ⚠️ PARCIAL

| Campo | Valor |
|-------|-------|
| **Responsabilidade** | Registros de memória, snapshots |
| **Snapshots** | ✅ `MemorySnapshot` (frozen) |
| **Eventos** | ❌ (LearningPipeline publica indiretamente) |
| **Dependências** | `core/knowledge/` (TYPE_CHECKING) |
| **Demo** | `demo_memory_runtime_foundation.py` (275 linhas) |

### 4.3 `core/knowledge/` ✅ COMPLETO

| Campo | Valor |
|-------|-------|
| **Responsabilidade** | Registros de conhecimento, promoção de memória |
| **Snapshots** | ✅ `KnowledgeSnapshot` (frozen) |
| **Eventos** | ✅ `KnowledgePromoted` |
| **Dependências** | `core/memory/`, `core/events/` |
| **Demo** | `demo_knowledge_runtime_foundation.py` (266 linhas) |

### 4.4 `core/learning/` ⚠️ PARCIAL

| Campo | Valor |
|-------|-------|
| **Responsabilidade** | Recomendações de aprendizado + pipeline |
| **Snapshots** | ✅ `LearningSnapshot` (frozen) |
| **Eventos** | ✅ (pipeline publica) |
| **Dependências** | `core/knowledge/`, `core/conversation/`, `core/memory/`, `core/skills/` |
| **Demo** | `demo_learning_pipeline.py` (512 linhas) |

### 4.5 `core/skills/` ✅ COMPLETO

| Campo | Valor |
|-------|-------|
| **Responsabilidade** | Registros de skills Foundation + Runtime |
| **Snapshots** | ✅ `SkillSnapshot` (frozen), `SkillRuntimeSnapshot` |
| **Eventos** | ✅ `SkillCreated`, `SkillPromoted`, `SkillLevelChanged` |
| **Dependências** | `core/learning/`, `core/events/`, `core/persistence/` |
| **Demo** | `demo_skill_runtime_foundation.py` (446 linhas) |

### 4.6 `core/workflow/` (singular) ⚠️ PARCIAL

| Campo | Valor |
|-------|-------|
| **Responsabilidade** | Definição de workflows — Foundation |
| **Snapshots** | ❌ Nenhum |
| **Eventos** | ❌ Nenhum |
| **⚠️ Naming collision** | Classe `WorkflowRuntime` colide com `core/workflows/runtime.py` |
| **Demo** | `demo_workflow_runtime_foundation.py` (631 linhas) |

### 4.7 `core/workflows/` (plural) ⚠️ PARCIAL

| Campo | Valor |
|-------|-------|
| **Responsabilidade** | Coordenação stateful de workflows com DAG |
| **Snapshots** | ✅ `WorkflowRuntimeSnapshot` |
| **Eventos** | ✅ `WorkflowStarted`, `WorkflowTaskStarted`, `WorkflowTaskCompleted`, `WorkflowCompleted` |
| **Dependências** | `core/workflow/`, `core/events/`, `core/tasks/`, `core/runtime/`, `core/persistence/` |
| **Demo** | `demo_workflow_dag.py` (1060 linhas) |

### 4.8 `core/execution/` ⚠️ PARCIAL

| Campo | Valor |
|-------|-------|
| **Responsabilidade** | Pipeline AI: prepare → execute → validate → result |
| **Snapshots** | ❌ Nenhum |
| **Eventos** | ❌ Nenhum |
| **Dependências** | `core/conversation/`, `core/llm/models.py` |
| **Demo** | `demo_execution_runtime_foundation.py` (240 linhas) |

### 4.9 `core/execution_plan/` ⚠️ PARCIAL

| Campo | Valor |
|-------|-------|
| **Responsabilidade** | Transforma StrategyExecutionPlan em ações concretas |
| **Snapshots** | ❌ Nenhum |
| **Eventos** | ❌ Nenhum |
| **Dependências** | `core/policy/foundation.py`, `core/strategy/pipeline.py` |
| **Demo** | `demo_execution_plan_foundation.py` (885 linhas) |

### 4.10 `core/policy/` (singular) ⚠️ PARCIAL — DUPLICADO

| Campo | Valor |
|-------|-------|
| **Responsabilidade** | Avaliação de regras de política (Foundation) |
| **Snapshots** | ✅ `PolicySnapshot` (frozen) |
| **Eventos** | ❌ Nenhum |
| **⚠️ Duplicação** | Coexiste com `core/policies/` — ambos fazem avaliação de política |
| **Demo** | `demo_policy_runtime_foundation.py` (744 linhas) |

### 4.11 `core/policies/` (plural) ⚠️ PARCIAL — DUPLICADO

| Campo | Valor |
|-------|-------|
| **Responsabilidade** | Contratos + runtime de política (versão anterior) |
| **Snapshots** | ❌ Nenhum |
| **Eventos** | ❌ Nenhum |
| **⚠️ Duplicação** | Coexiste com `core/policy/` |
| **Demo** | `demo_policy_engine.py` (233 linhas) |

### 4.12 `core/strategy/` ⚠️ PARCIAL

| Campo | Valor |
|-------|-------|
| **Responsabilidade** | Recomendações estratégicas + pipeline |
| **Snapshots** | ✅ `StrategySnapshot` (frozen) |
| **Eventos** | ❌ Nenhum |
| **Dependências** | 10 módulos (maior fan-out do sistema) |
| **Demo** | `demo_strategy_runtime_foundation.py` (931 linhas) |

### 4.13 `core/monitoring/` ⚠️ PARCIAL

| Campo | Valor |
|-------|-------|
| **Responsabilidade** | Observabilidade orientada a eventos, health scores |
| **Snapshots** | ✅ `MonitoringSnapshot` (frozen) |
| **Eventos** | ❌ (consome, não publica) |
| **Dependências** | `core/events/bus.py` |
| **Demo** | `demo_monitoring_runtime.py` (854 linhas) |

### 4.14 `core/analytics/` ⚠️ PARCIAL

| Campo | Valor |
|-------|-------|
| **Responsabilidade** | Agregação de métricas de performance |
| **Snapshots** | ✅ `PerformanceSnapshot` (frozen) |
| **Eventos** | ❌ Nenhum |
| **Dependências** | 7 módulos |
| **Demo** | `demo_performance_runtime.py` (548 linhas) |

### 4.15 `core/optimization/` ⚠️ PARCIAL

| Campo | Valor |
|-------|-------|
| **Responsabilidade** | Execução de planos com retry/rollback/cooldown |
| **Snapshots** | ✅ `OptimizationSnapshot` (frozen) |
| **Eventos** | ✅ |
| **Dependências** | `core/execution_plan/` |
| **Demo** | `demo_auto_optimization_runtime.py` (813 linhas) |

### 4.16 `core/feedback/` ⚠️ PARCIAL

| Campo | Valor |
|-------|-------|
| **Responsabilidade** | Comparação expected vs actual |
| **Snapshots** | ✅ `FeedbackSnapshot` (frozen) |
| **Eventos** | ❌ Nenhum |
| **Dependências** | Nenhuma |
| **Demo** | `demo_feedback_runtime_foundation.py` (939 linhas) |

### 4.17 `core/history/` ⚠️ PARCIAL

| Campo | Valor |
|-------|-------|
| **Responsabilidade** | Comparação temporal de snapshots |
| **Snapshots** | ✅ `HistoricalSnapshot` (frozen) |
| **Eventos** | ❌ Nenhum |
| **Dependências** | Nenhuma |
| **Demo** | `demo_historical_runtime_foundation.py` (805 linhas) |

### 4.18 `core/prediction/` ⚠️ PARCIAL

| Campo | Valor |
|-------|-------|
| **Responsabilidade** | Projeção heurística de futuro |
| **Snapshots** | ✅ `PredictionSnapshot` (frozen) |
| **Eventos** | ❌ Nenhum |
| **Dependências** | 8 módulos |
| **⚠️ Sem consumidores** | Nenhum módulo consome predições |
| **Demo** | `demo_prediction_runtime_foundation.py` (1062 linhas) |

### 4.19 `core/collaboration/` ⚠️ PARCIAL

| Campo | Valor |
|-------|-------|
| **Responsabilidade** | Orquestração de colaboração entre employees |
| **Snapshots** | ❌ Nenhum |
| **Eventos** | ✅ `CollaborationStarted`, `ParticipantResponded`, `CollaborationCompleted` |
| **Dependências** | `core/events/` |
| **Demo** | `demo_collaboration_runtime.py` (889 linhas) |

### 4.20 `core/employees/` ✅ COMPLETO

| Campo | Valor |
|-------|-------|
| **Responsabilidade** | Ciclo de vida de employees + cognição |
| **Snapshots** | ✅ `EmployeeRuntimeSnapshot` |
| **Eventos** | ✅ `EmployeeStateChangedEvent` |
| **Dependências** | `core/events/` |
| **Demo** | `demo_employee_cognition.py` (681 linhas) |

### 4.21 `core/orchestrator/` ⚠️ PARCIAL

| Campo | Valor |
|-------|-------|
| **Responsabilidade** | Pipeline completo: decisão → execução → aprendizado |
| **Snapshots** | ✅ `OrchestratorTaskSnapshot` |
| **Eventos** | ✅ 7 eventos de domínio |
| **Dependências** | 7 módulos |
| **Demo** | `demo_orchestrator_conversation_flow.py` (547 linhas) |

### 4.22 `core/company/` ⚠️ PARCIAL

| Campo | Valor |
|-------|-------|
| **Responsabilidade** | Company Runtime completo, task lifecycle |
| **Snapshots** | ❌ Nenhum dedicado |
| **Eventos** | ✅ `CompanyTaskReceived`, `CompanyTaskRouted`, `CompanyTaskCompleted` |
| **Dependências** | 6 módulos |
| **Demo** | `demo_company_runtime_complete.py` (882 linhas) |

### 4.23 `core/decision/` 🔴 PENDENTE

| Campo | Valor |
|-------|-------|
| **Responsabilidade** | Motor de decisão, avalia candidatos, aplica políticas |
| **Snapshots** | ❌ Nenhum |
| **Eventos** | ❌ Nenhum |
| **🔴 Anomalia** | **Sem `__init__.py`** — não pode ser importado como `core.decision` |
| **Demo** | `demo_decision_engine.py` (125 linhas) |

### 4.24 `core/persistence/` 🔴 PENDENTE

| Campo | Valor |
|-------|-------|
| **Responsabilidade** | Persistência JSON via pathlib |
| **Snapshots** | ✅ `PersistenceSnapshot` (frozen) |
| **Eventos** | ❌ Nenhum |
| **🔴 Anomalia** | **Sem `__init__.py`** — não pode ser importado como `core.persistence` |

### 4.25 `core/llm/` ⚠️ PARCIAL

| Campo | Valor |
|-------|-------|
| **Responsabilidade** | LLM Gateway, adapters, prompts, cost tracking |
| **Snapshots** | ❌ Nenhum |
| **Eventos** | ❌ Nenhum |
| **Dependências** | Nenhuma (interna) |
| **Demo** | `demo_llm_gateway.py` (167 linhas) |

### 4.26 `core/events/` ✅ COMPLETO

| Campo | Valor |
|-------|-------|
| **Responsabilidade** | EventBus, 25 eventos de domínio |
| **Snapshots** | ❌ N/A |
| **Eventos** | ✅ 25 eventos de domínio |
| **Dependências** | `core/exceptions/` |

### 4.27 `core/prompts/` 💀 MORTO

| Campo | Valor |
|-------|-------|
| **Responsabilidade** | Contratos de prompt (não utilizado) |
| **Evidência** | Zero imports de produção. `core/llm/prompts.py` é a implementação real. |
| **Ação** | Remover |

### 4.28 `core/pipeline/` 💀 MORTO

| Campo | Valor |
|-------|-------|
| **Responsabilidade** | Contratos de pipeline (não utilizado) |
| **Evidência** | Zero imports de produção. Pipelines reais são independentes. |
| **Ação** | Remover |

---

## 5. Pipelines Existentes

### 5.1 Pipeline de Execução (ExecutionRuntime)

```
prepare_context → execute_llm → validate_output → build_result
```

- **Input**: Task snapshot, employee snapshot, LLMRequest
- **Output**: ExecutionResult
- **Stateless**: Sim
- **Eventos**: Nenhum
- **Onde**: `core/execution/runtime.py`

### 5.2 Pipeline de Cognição (CognitiveEmployee)

```
receive_task → analyze_task → build_plan → prioritize_steps → execute_next_step → build_result
```

- **Input**: Task, employee context
- **Output**: CognitionResult
- **Stateless**: Sim
- **Onde**: `core/employees/cognition.py`

### 5.3 Pipeline de Colaboração (CollaborationRuntime)

```
create_request → add_participants → send_request → simulate_responses → consolidate → build_result
```

- **Input**: CollaborationRequest
- **Output**: CollaborationResult
- **Stateless**: Sim
- **Eventos**: CollaborationStarted, ParticipantResponded, CollaborationCompleted
- **Onde**: `core/collaboration/foundation.py`

### 5.4 Pipeline de Aprendizado (LearningPipeline)

```
Conversation → Memory → Knowledge → Learning → Skills
```

- **Input**: ConversationSession
- **Output**: PipelineResult
- **Stateless**: Sim
- **Eventos**: ConversationCreated, MessageAdded, MemoryRecordCreated, KnowledgePromoted, RecommendationCreated
- **Onde**: `core/learning/pipeline.py`

### 5.5 Pipeline de Estratégia (StrategyPipeline)

```
StrategyRecommendation → FoundationPolicyRuntime.evaluate_all() → StrategyExecutionPlan
```

- **Input**: StrategySnapshot, PolicyRule[]
- **Output**: StrategyPipelineResult
- **Stateless**: Sim
- **Eventos**: Nenhum
- **Onde**: `core/strategy/pipeline.py`

### 5.6 Pipeline de Otimização (AutoOptimizationRuntime)

```
ExecutionPlan → executar ações aprovadas → retry/rollback/cooldown → OptimizationSnapshot
```

- **Input**: ExecutionPlan
- **Output**: OptimizationSnapshot
- **Stateful**: Sim
- **Eventos**: Sim
- **Onde**: `core/optimization/runtime.py`

### 5.7 Pipeline de Orquestração (OrchestratorRuntime)

```
receive_task → assign_employee → execute_decision → execute_task → run_learning_pipeline → complete
```

- **Input**: Task title
- **Output**: OrchestratorExecutionResult
- **Stateful**: Sim
- **Eventos**: OrchestratorExecutionStarted, OrchestratorExecutionCompleted, DecisionApproved, DecisionRejected, ExecutionStarted, ExecutionCompleted, ExecutionFailed
- **Onde**: `core/orchestrator/runtime.py`

### 5.8 Pipeline Company Completo (CompanyTaskRuntime)

```
receive → route → execute → learn → complete
```

- **Input**: Task
- **Output**: CompanyExecutionResult
- **Stateful**: Sim
- **Eventos**: CompanyTaskReceived, CompanyTaskRouted, CompanyTaskCompleted
- **Onde**: `core/company/runtime.py`

### 5.9 Pipeline Predição (cadeia completa conceitual)

```
Feedback → Historical → Prediction
```

- **Status**: ⚠️ Módulos existem individualmente, pipeline integrado não implementado
- **Input**: OptimizationSnapshot, FeedbackSnapshot
- **Output**: PredictionSnapshot
- **Stateless**: Sim (todos os módulos são Foundation)

---

## 6. Snapshots

### Snapshots Frozen Dataclass (estatísticos, imutáveis)

| Snapshot | Produzido por | Consumido por | Persistível |
|----------|---------------|---------------|-------------|
| `MonitoringSnapshot` | MonitoringRuntime | StrategyFoundation, PredictionFoundation, PerformanceRuntime | Sim |
| `PerformanceSnapshot` | PerformanceRuntime | StrategyFoundation | Sim |
| `StrategySnapshot` | StrategyFoundation | StrategyPipeline, PredictionFoundation | Sim |
| `PolicySnapshot` | PolicyFoundation | StrategyPipeline | Sim |
| `StrategyExecutionPlan` | StrategyPipeline | ExecutionPlanFoundation, OptimizationRuntime | Sim |
| `ExecutionPlan` | ExecutionPlanFoundation | OptimizationRuntime | Sim |
| `OptimizationSnapshot` | OptimizationRuntime | FeedbackFoundation, PersistenceRuntime | Sim |
| `FeedbackSnapshot` | FeedbackFoundation | HistoricalFoundation, PredictionFoundation | Sim |
| `HistoricalSnapshot` | HistoricalFoundation | PredictionFoundation | Sim |
| `PredictionSnapshot` | PredictionFoundation | — (sem consumidores) | Sim |
| `MemorySnapshot` | MemoryRuntime | KnowledgeFoundation | Sim |
| `KnowledgeSnapshot` | KnowledgeFoundation | LearningFoundation | Sim |
| `LearningSnapshot` | LearningFoundation | SkillFoundation | Sim |
| `SkillSnapshot` | SkillFoundation | SkillRuntime | Sim |
| `PersistenceSnapshot` | PersistenceRuntime | PersistenceRuntime | Sim (arquivo JSON) |

### Snapshots Mutáveis (runtime stateful tracking)

| Snapshot | Produzido por | Consumido por |
|----------|---------------|---------------|
| `SkillRuntimeSnapshot` | SkillRuntime | PerformanceRuntime |
| `WorkflowRuntimeSnapshot` | WorkflowRuntime | PerformanceRuntime |
| `EmployeeRuntimeSnapshot` | EmployeeRuntime | OrchestratorRuntime |
| `OrchestratorTaskSnapshot` | OrchestratorRuntime | — |
| `DepartmentRuntimeSnapshot` | DepartmentRuntime | — |
| `TaskRuntimeSnapshot` | TaskRuntime | — |
| `ResultRuntimeSnapshot` | ResultRuntime | — |
| `KnowledgeRuntimeSnapshot` | KnowledgeRuntime | — |

### Snapshots de Observabilidade (projetor, mutáveis)

| Snapshot | Produzido por |
|----------|---------------|
| `ObservabilitySnapshot` | ObservabilityProjector |

### Módulos sem Snapshot

conversation, execution, collaboration, workflow, execution_plan, decision, company, policies

---

## 7. Eventos

### Eventos de Domínio (25 eventos)

Todos em `core/events/domain_events.py`. Todos são frozen dataclasses.

| # | Evento | Publicado por | Consumido por |
|---|--------|---------------|---------------|
| 1 | `WorkflowStarted` | WorkflowRuntime | MonitoringRuntime |
| 2 | `WorkflowTaskStarted` | WorkflowRuntime | MonitoringRuntime |
| 3 | `WorkflowTaskCompleted` | WorkflowRuntime | MonitoringRuntime |
| 4 | `WorkflowCompleted` | WorkflowRuntime | MonitoringRuntime |
| 5 | `ExecutionStarted` | OrchestratorRuntime | MonitoringRuntime |
| 6 | `ExecutionCompleted` | OrchestratorRuntime | MonitoringRuntime |
| 7 | `ExecutionFailed` | OrchestratorRuntime | MonitoringRuntime |
| 8 | `ConversationCreated` | ConversationRuntime | MonitoringRuntime, LearningPipeline |
| 9 | `MessageAdded` | ConversationRuntime | MonitoringRuntime, LearningPipeline |
| 10 | `MemoryRecordCreated` | LearningPipeline | MonitoringRuntime |
| 11 | `KnowledgePromoted` | KnowledgeRuntime | MonitoringRuntime |
| 12 | `RecommendationCreated` | LearningPipeline | MonitoringRuntime |
| 13 | `SkillCreated` | SkillRuntime | MonitoringRuntime |
| 14 | `SkillPromoted` | SkillRuntime | MonitoringRuntime |
| 15 | `SkillLevelChanged` | SkillRuntime | MonitoringRuntime |
| 16 | `DecisionApproved` | OrchestratorRuntime | MonitoringRuntime |
| 17 | `DecisionRejected` | OrchestratorRuntime | MonitoringRuntime |
| 18 | `CollaborationStarted` | CollaborationFoundation | MonitoringRuntime |
| 19 | `ParticipantResponded` | CollaborationFoundation | MonitoringRuntime |
| 20 | `CollaborationCompleted` | CollaborationFoundation | MonitoringRuntime |
| 21 | `CompanyTaskReceived` | CompanyRuntime | MonitoringRuntime |
| 22 | `CompanyTaskRouted` | CompanyRuntime | MonitoringRuntime |
| 23 | `CompanyTaskCompleted` | CompanyRuntime | MonitoringRuntime |
| 24 | `OrchestratorExecutionStarted` | OrchestratorRuntime | MonitoringRuntime |
| 25 | `OrchestratorExecutionCompleted` | OrchestratorRuntime | MonitoringRuntime |

### Eventos Internos (não são eventos de domínio)

| Evento | Publicado por | Consumido por |
|--------|---------------|---------------|
| `CompanyStateChangedEvent` | RuntimeStateManager | — |
| `EmployeeStateChangedEvent` | EmployeeRuntime | — |
| `WorkflowStateChangedEvent` | WorkflowRuntime | — |
| `OrchestratorTaskEvent` | OrchestratorRuntime | OrchestratorRuntime |

### Quem publica

- 13 módulos publicam eventos via `event_bus.publish()`
- Foundations stateless NUNCA publicam eventos
- EventBus é opcional e injetado

### Quem consome

- **MonitoringRuntime**: consome eventos para construir snapshots de métricas
- **ObservabilityProjector**: único subscriber que reage a eventos específicos
- **LearningPipeline**: consome eventos opcionalmente

⚠️ **13 publishers, 1 subscriber real** — sistema event-driven incompleto.

---

## 8. Foundations

### Lista completa

| Foundation | Classe | Arquivo | Status |
|------------|--------|---------|--------|
| **ConversationRuntime** | `ConversationRuntime` | `core/conversation/runtime.py` | ⚠️ Nome "Runtime" mas stateless |
| **MemoryRuntime** | `MemoryRuntime` | `core/memory/runtime.py` | ⚠️ Nome "Runtime" mas stateless |
| **KnowledgeRuntime** | `KnowledgeRuntime` (stateless) | `core/knowledge/foundation.py` | ✅ |
| **LearningRuntime** | `LearningRuntime` | `core/learning/foundation.py` | ✅ |
| **SkillRuntime** | `SkillRuntime` (stateless) | `core/skills/foundation.py` | ✅ |
| **WorkflowRuntime** | `WorkflowRuntime` | `core/workflow/foundation.py` | ⚠️ Naming collision com stateful |
| **ExecutionRuntime** | `ExecutionRuntime` | `core/execution/runtime.py` | ⚠️ Nome "Runtime" mas stateless |
| **ExecutionPlanRuntime** | `FoundationExecutionPlanRuntime` | `core/execution_plan/foundation.py` | ✅ Nome correto |
| **PolicyRuntime** | `FoundationPolicyRuntime` | `core/policy/foundation.py` | ✅ |
| **StrategyRuntime** | `FoundationStrategyRuntime` | `core/strategy/foundation.py` | ✅ |
| **FeedbackRuntime** | `FoundationFeedbackRuntime` | `core/feedback/foundation.py` | ✅ |
| **HistoricalRuntime** | `FoundationHistoricalRuntime` | `core/history/foundation.py` | ✅ |
| **PredictionRuntime** | `FoundationPredictionRuntime` | `core/prediction/foundation.py` | ✅ |
| **CollaborationRuntime** | `CollaborationRuntime` | `core/collaboration/foundation.py` | ⚠️ Nome "Runtime" mas stateless |
| **CognitiveEmployee** | `CognitiveEmployeeFoundation` | `core/employees/cognition.py` | ✅ |
| **MonitoringRuntime** | `MonitoringRuntime` | `core/monitoring/runtime.py` | ⚠️ Nome "Runtime" mas stateless |
| **PerformanceRuntime** | `PerformanceRuntime` | `core/analytics/runtime.py` | ⚠️ Nome "Runtime" mas stateless |

### Inconsistências de nomenclatura

8 módulos usam sufixo "Runtime" em classes que são puramente stateless (`@staticmethod`):
conversation, memory, execution, monitoring, analytics, collaboration, llm, decision

Isso viola o princípio de nomenclatura onde "Runtime" deveria indicar estado mutável.

---

## 9. Stateful Runtimes

### Lista completa

| Runtime | Classe | Arquivo | Eventos | Persistência |
|---------|--------|---------|---------|--------------|
| **RuntimeStateManager** | `RuntimeStateManager` | `core/runtime.py` | CompanyStateChangedEvent | ❌ |
| **CompanyRuntime** | `CompanyRuntime` | `core/runtime.py` | — | ❌ |
| **EmployeeRuntime** | `EmployeeRuntime` | `core/employees/runtime.py` | EmployeeStateChangedEvent | ❌ |
| **KnowledgeRuntime** | `KnowledgeRuntime` (stateful) | `core/knowledge/runtime.py` | KnowledgePromoted | ✅ |
| **SkillRuntime** | `SkillRuntime` (stateful) | `core/skills/runtime.py` | SkillCreated, SkillPromoted, SkillLevelChanged | ✅ |
| **WorkflowRuntime** | `WorkflowRuntime` | `core/workflows/runtime.py` | 4 eventos workflow | ✅ |
| **OptimizationRuntime** | `OptimizationRuntime` | `core/optimization/runtime.py` | Sim | ❌ |
| **OrchestratorRuntime** | `OrchestratorRuntime` | `core/orchestrator/runtime.py` | 7 eventos | ❌ |
| **DepartmentRuntime** | `DepartmentRuntime` | `core/departments/runtime.py` | Sim | ❌ |
| **TaskRuntime** | `TaskRuntime` | `core/tasks/runtime.py` | Sim | ❌ |

### O que nenhum Runtime stateful faz

- Não contém lógica de negócio (delega para Foundations)
- Não faz decisões (delega para DecisionEngine)
- Não gera recomendações (delega para StrategyFoundation)
- Não projeta futuro (delega para PredictionFoundation)

---

## 10. Persistência

### Estratégia

- **JSON + pathlib** — sem banco de dados, sem SQLite, sem ORM
- **PersistenceRuntime** (`core/persistence/runtime.py`) — classe stateless
- **STORAGE_ROOT** = `storage/` — raiz de todos os snapshots
- **Serialização**: `dataclasses.asdict()` + `json.dump()`
- **Deserialização**: `importlib` + `dataclasses.field()`

### 🔴 Anomalia

`core/persistence/` **não tem `__init__.py`** — o pacote não pode ser importado como `from core.persistence import ...`. A importação atual é feita via caminho absoluto (`core.persistence._helpers`).

### Limitações conhecidas

1. Sem concorrência (sem locks)
2. Sem queries (apenas listagem por domínio)
3. Sem índices
4. Sem migrations
5. Sem compressão
6. Sem validação de schema
7. Sem relacionamento entre snapshots
8. IO síncrono
9. UUID como única chave
10. Não versionado

---

## 11. Checklist Obrigatório Antes de Criar um Novo Módulo

### Perguntas obrigatórias

```
1. Qual problema arquitetural este módulo resolve?
   → Se não houver um problema arquitetural claro, NÃO implemente.

2. Ele fecha uma lacuna da cadeia existente?
   → A cadeia essencial está completa. Lacunas são de refinamento, não de funcionalidade.

3. Pode ser resolvido por um módulo existente?
   → A maioria dos problemas pode ser resolvida estendendo módulos existentes.
   → NÃO crie um novo se um existente pode ser estendido.

4. Introduz dependência circular?
   → Verifique contra PLATFORM_DEPENDENCY_GRAPH.md.

5. É Foundation ou Runtime?
   → Se precisar de estado, comece como Foundation primeiro.

6. Precisa realmente existir?
   → Responda honestamente: isto é necessário ou apenas "interessante"?
   → Módulos "interessantes" são proibidos.
```

### Regras de ouro

- Se o módulo não fecha uma lacuna real na cadeia, ele não deve existir.
- Se um módulo existente pode ser estendido, estenda-o.
- Se introduz dependência circular, reprojete ou cancele.
- Se é "interessante" mas não necessário, arquive.
- Se o módulo replica funcionalidade já coberta (ex: `core/prompts/` vs `core/llm/prompts.py`), NÃO implemente.

---

## 12. Auditoria Arquitetural

### Classificação Atualizada

#### Essenciais (23 módulos)

`core/exceptions/`, `core/events/`, `core/conversation/`, `core/memory/`, `core/knowledge/`, `core/learning/`, `core/skills/`, `core/execution/`, `core/monitoring/`, `core/strategy/`, `core/policy/`, `core/strategy/pipeline.py`, `core/execution_plan/`, `core/optimization/`, `core/feedback/`, `core/history/`, `core/prediction/`, `core/orchestrator/`, `core/company/runtime.py`, `core/employees/`, `core/llm/`, `core/persistence/`, `core/runtime.py`

#### Importantes (9 módulos)

`core/collaboration/`, `core/decision/`, `core/analytics/`, `core/policies/`, `core/workflow/`, `core/workflows/`, `core/tasks/`, `core/employees/cognition.py`, `core/organization/`, `core/departments/`, `core/config/`

#### Opcionais (3 módulos)

`core/results/`, `core/logging/`, `core/models/`, `core/observability.py`

#### Mortos (2 módulos — remover)

`core/prompts/` (zero imports, duplicado por `core/llm/prompts.py`),
`core/pipeline/` (zero imports, pipelines reais são independentes)

### Total: 26 módulos (3 completos, 22 parciais, 1 pendente, 2 mortos)

---

## 13. Roadmap Arquitetural

### Estado atual

**A plataforma já possui todas as camadas essenciais implementadas.**

Não há lacunas arquiteturais reais. O roadmap detalhado está em `ROADMAP_EXECUTION.md`.

### Módulos que ainda faltam

**Nenhum.** A fase de expansão da arquitetura está encerrada.

O foco agora é **refinamento** dos módulos existentes:
- Corrigir anomalias (`__init__.py` ausentes)
- Remover módulos mortos
- Unificar módulos duplicados
- Padronizar nomenclatura Foundation/Runtime

---

## 14. Estado Atual da Plataforma

### A plataforma já possui todas as camadas essenciais?

**SIM.** A plataforma possui todas as camadas essenciais implementadas e funcionais:

| Camada | Status |
|--------|--------|
| Foundation Conversation | ✅ Funcional (⚠️ padrão inconsistente) |
| Foundation Memory | ✅ Funcional |
| Foundation Knowledge | ✅ COMPLETO |
| Foundation Learning | ✅ Funcional |
| Foundation Skills | ✅ COMPLETO |
| Foundation Workflow | ✅ Funcional (⚠️ naming collision) |
| Foundation Execution | ✅ Funcional |
| Foundation Execution Plan | ✅ Funcional |
| Foundation Policy | ✅ Funcional (⚠️ duplicado) |
| Foundation Strategy | ✅ Funcional |
| Foundation Feedback | ✅ Funcional |
| Foundation Historical | ✅ Funcional |
| Foundation Prediction | ✅ Funcional (⚠️ sem consumidores) |
| Foundation Collaboration | ✅ Funcional |
| Foundation Cognitive Employee | ✅ Funcional |
| Runtime State Manager | ✅ Funcional |
| Runtime Company | ✅ Funcional |
| Runtime Employee | ✅ Funcional |
| Runtime Knowledge | ✅ Funcional |
| Runtime Skill | ✅ Funcional |
| Runtime Workflow | ✅ Funcional |
| Runtime Optimization | ✅ Funcional |
| Runtime Orchestrator | ✅ Funcional |
| Runtime Department | ✅ Funcional |
| Runtime Task | ✅ Funcional |
| EventBus + 25 domain events | ✅ COMPLETO |
| Persistence JSON | ✅ Funcional (⚠️ sem `__init__.py`) |
| LLM Gateway | ✅ Funcional |

### O projeto está em qual fase?

**Fase de Refinamento (Fase 1).** A expansão arquitetural está encerrada.

### Próximos passos imediatos

1. 🔴 Criar `__init__.py` para `core/decision/` e `core/persistence/`
2. 💀 Remover `core/prompts/` e `core/pipeline/`
3. ⚠️ Renomear `WorkflowRuntime` em `core/workflow/foundation.py`
4. ⚠️ Unificar `core/policy/` + `core/policies/`
5. 📋 Ver `ROADMAP_EXECUTION.md` para roadmap completo

---

*Esta Constituição reflete o estado real da plataforma após auditoria completa em Julho de 2026.*

*A fase de expansão da arquitetura está oficialmente encerrada.*

*Inicia-se a fase de refinamento.*

*Consulte `ARCHITECTURE_INDEX.md` para navegação rápida entre módulos.*
*Consulte `ROADMAP_EXECUTION.md` para o roadmap oficial.*
*Consulte `BUSINESS_VISION.md` para a visão de negócio.*
