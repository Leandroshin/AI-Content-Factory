# ARCHITECTURE INDEX

**AI Content Factory — Índice Navegável da Arquitetura**
*Consulte este documento para localizar rapidamente qualquer módulo, sua responsabilidade, dependências, pipelines e demos.*

---

## Como usar

Cada entrada contém:

```
Módulo:         nome do pacote
Responsabilidade: descrição concisa
Dependências:   módulos dos quais depende
Dependentes:    módulos que dependem deste
Pipeline:       pipeline(s) que utiliza este módulo
Demo:           demo(s) que cobrem este módulo
Status:         COMPLETO / PARCIAL / PENDENTE / MORTO
```

---

## Módulos Core (26 ativos + 2 mortos)

### 1. `core/exceptions/`

| Campo | Valor |
|-------|-------|
| **Responsabilidade** | Hierarquia base de exceções |
| **Dependências** | Nenhuma |
| **Dependentes** | Todos os módulos |
| **Pipeline** | N/A (infraestrutura) |
| **Demo** | Nenhuma dedicada |
| **Status** | ✅ COMPLETO |

### 2. `core/config/`

| Campo | Valor |
|-------|-------|
| **Responsabilidade** | Contratos de configuração |
| **Dependências** | `core/exceptions/` |
| **Dependentes** | Nenhum (contratos apenas) |
| **Pipeline** | N/A |
| **Demo** | Nenhuma dedicada |
| **Status** | ⚠️ PARCIAL (contract-first, placeholders) |

### 3. `core/events/`

| Campo | Valor |
|-------|-------|
| **Responsabilidade** | EventBus, 25 eventos de domínio, contratos |
| **Dependências** | `core/exceptions/` |
| **Dependentes** | Todos os runtimes stateful |
| **Pipeline** | Todos (eventos transversais) |
| **Demo** | `demo_event_bus_runtime.py`, `demo_event_pipeline.py` |
| **Status** | ✅ COMPLETO |

### 4. `core/conversation/`

| Campo | Valor |
|-------|-------|
| **Responsabilidade** | Sessões de conversa, mensagens, contexto |
| **Dependências** | `core/memory/runtime.py` |
| **Dependentes** | `core/execution/runtime.py`, `core/learning/pipeline.py`, `core/orchestrator/runtime.py` |
| **Pipeline** | Execução, Aprendizado, Orquestração |
| **Demo** | `demo_conversation_runtime_foundation.py`, `demo_conversation_memory_integration.py` |
| **Status** | ⚠️ PARCIAL (sem snapshot, sem foundation separada) |

### 5. `core/memory/`

| Campo | Valor |
|-------|-------|
| **Responsabilidade** | Registros de memória, snapshots |
| **Dependências** | `core/knowledge/` (TYPE_CHECKING) |
| **Dependentes** | `core/knowledge/foundation.py`, `core/learning/pipeline.py` |
| **Pipeline** | Aprendizado |
| **Demo** | `demo_memory_runtime_foundation.py`, `demo_memory_knowledge_pipeline.py` |
| **Status** | ⚠️ PARCIAL (sem eventos, sem foundation separada) |

### 6. `core/knowledge/`

| Campo | Valor |
|-------|-------|
| **Responsabilidade** | Registros de conhecimento, promoção de memória |
| **Dependências** | `core/memory/runtime.py`, `core/events/bus.py` |
| **Dependentes** | `core/learning/foundation.py`, `core/strategy/foundation.py` |
| **Pipeline** | Aprendizado |
| **Demo** | `demo_knowledge_runtime_foundation.py` |
| **Status** | ✅ COMPLETO |

### 7. `core/learning/`

| Campo | Valor |
|-------|-------|
| **Responsabilidade** | Recomendações de aprendizado + pipeline |
| **Dependências** | `core/knowledge/`, `core/conversation/`, `core/memory/`, `core/skills/`, `core/events/` |
| **Dependentes** | `core/skills/foundation.py`, `core/strategy/foundation.py`, `core/orchestrator/runtime.py` |
| **Pipeline** | Aprendizado |
| **Demo** | `demo_learning_runtime_foundation.py`, `demo_learning_pipeline.py` |
| **Status** | ⚠️ PARCIAL (sem runtime separado) |

### 8. `core/skills/`

| Campo | Valor |
|-------|-------|
| **Responsabilidade** | Registros de skills Foundation + Runtime |
| **Dependências** | `core/learning/`, `core/events/`, `core/persistence/` |
| **Dependentes** | `core/strategy/foundation.py`, `core/analytics/runtime.py` |
| **Pipeline** | Aprendizado |
| **Demo** | `demo_skill_runtime_foundation.py`, `demo_skill_runtime.py`, `demo_skill_runtime_integration.py` |
| **Status** | ✅ COMPLETO |

### 9. `core/workflow/` (singular)

| Campo | Valor |
|-------|-------|
| **Responsabilidade** | Definição de workflows — Foundation |
| **Dependências** | Nenhuma |
| **Dependentes** | `core/workflows/runtime.py` |
| **Pipeline** | Workflow |
| **Demo** | `demo_workflow_runtime_foundation.py` |
| **Status** | ⚠️ PARCIAL (⚠️ naming collision com `workflows/runtime.py`) |

### 10. `core/workflows/` (plural)

| Campo | Valor |
|-------|-------|
| **Responsabilidade** | Coordenação stateful de workflows com DAG |
| **Dependências** | `core/workflow/`, `core/events/`, `core/tasks/`, `core/runtime/`, `core/persistence/` |
| **Dependentes** | `core/strategy/foundation.py`, `core/analytics/runtime.py` |
| **Pipeline** | Workflow |
| **Demo** | `demo_workflow_dag.py`, `demo_workflow_runtime.py`, `demo_workflow_runtime_integration.py` |
| **Status** | ⚠️ PARCIAL |

### 11. `core/tasks/`

| Campo | Valor |
|-------|-------|
| **Responsabilidade** | Ciclo de vida de tarefas |
| **Dependências** | `core/exceptions/`, `core/runtime/` |
| **Dependentes** | `core/workflows/runtime.py` |
| **Pipeline** | Traversal (usado por workflows) |
| **Demo** | `demo_task_runtime.py` |
| **Status** | ⚠️ PARCIAL |

### 12. `core/execution/`

| Campo | Valor |
|-------|-------|
| **Responsabilidade** | Pipeline AI: prepare → execute → validate → result |
| **Dependências** | `core/conversation/`, `core/llm/models.py` |
| **Dependentes** | `core/orchestrator/runtime.py`, `core/company/runtime.py`, `core/analytics/runtime.py` |
| **Pipeline** | Execução, Orquestração, Company |
| **Demo** | `demo_execution_runtime_foundation.py`, `demo_execution_llm_integration.py`, `demo_execution_conversation_integration.py` |
| **Status** | ⚠️ PARCIAL (sem snapshot, sem foundation separada) |

### 13. `core/execution_plan/`

| Campo | Valor |
|-------|-------|
| **Responsabilidade** | Transforma StrategyExecutionPlan em ações concretas |
| **Dependências** | `core/policy/foundation.py`, `core/strategy/pipeline.py` |
| **Dependentes** | `core/optimization/runtime.py`, `core/feedback/foundation.py` |
| **Pipeline** | Estratégia → Otimização |
| **Demo** | `demo_execution_plan_foundation.py` |
| **Status** | ⚠️ PARCIAL |

### 14. `core/monitoring/`

| Campo | Valor |
|-------|-------|
| **Responsabilidade** | Observabilidade orientada a eventos, health scores |
| **Dependências** | `core/events/bus.py` |
| **Dependentes** | `core/strategy/foundation.py`, `core/prediction/foundation.py`, `core/analytics/runtime.py` |
| **Pipeline** | Transversal (consome eventos de todos) |
| **Demo** | `demo_monitoring_runtime.py` |
| **Status** | ⚠️ PARCIAL (sem foundation separada) |

### 15. `core/analytics/`

| Campo | Valor |
|-------|-------|
| **Responsabilidade** | Agregação de métricas de performance |
| **Dependências** | `core/company/`, `core/decision/`, `core/execution/`, `core/learning/`, `core/llm/`, `core/skills/`, `core/workflows/` |
| **Dependentes** | `core/strategy/foundation.py` |
| **Pipeline** | Estratégia (análise) |
| **Demo** | `demo_performance_runtime.py` |
| **Status** | ⚠️ PARCIAL (sem foundation separada) |

### 16. `core/strategy/`

| Campo | Valor |
|-------|-------|
| **Responsabilidade** | Recomendações estratégicas + pipeline |
| **Dependências** | 10 módulos (maior fan-out) |
| **Dependentes** | `core/execution_plan/`, `core/prediction/` |
| **Pipeline** | Estratégia |
| **Demo** | `demo_strategy_runtime_foundation.py`, `demo_strategy_pipeline.py` |
| **Status** | ⚠️ PARCIAL |

### 17. `core/policy/` (singular)

| Campo | Valor |
|-------|-------|
| **Responsabilidade** | Avaliação de regras de política (Foundation) |
| **Dependências** | Nenhuma |
| **Dependentes** | `core/strategy/pipeline.py`, `core/execution_plan/foundation.py` |
| **Pipeline** | Estratégia |
| **Demo** | `demo_policy_runtime_foundation.py`, `demo_policy_engine.py` |
| **Status** | ⚠️ PARCIAL (⚠️ duplicado com `core/policies/`) |

### 18. `core/policies/` (plural)

| Campo | Valor |
|-------|-------|
| **Responsabilidade** | Contratos + runtime de política |
| **Dependências** | `core/exceptions/` |
| **Dependentes** | `core/decision/runtime.py` |
| **Pipeline** | Decisão |
| **Demo** | `demo_policy_engine.py` |
| **Status** | ⚠️ PARCIAL (⚠️ duplicado com `core/policy/`) |

### 19. `core/optimization/`

| Campo | Valor |
|-------|-------|
| **Responsabilidade** | Execução de planos com retry/rollback/cooldown |
| **Dependências** | `core/execution_plan/` |
| **Dependentes** | `core/feedback/foundation.py` |
| **Pipeline** | Otimização |
| **Demo** | `demo_auto_optimization_runtime.py` |
| **Status** | ⚠️ PARCIAL |

### 20. `core/feedback/`

| Campo | Valor |
|-------|-------|
| **Responsabilidade** | Comparação expected vs actual |
| **Dependências** | Nenhuma |
| **Dependentes** | `core/history/foundation.py`, `core/prediction/foundation.py` |
| **Pipeline** | Feedback → Histórico → Predição |
| **Demo** | `demo_feedback_runtime_foundation.py` |
| **Status** | ⚠️ PARCIAL |

### 21. `core/history/`

| Campo | Valor |
|-------|-------|
| **Responsabilidade** | Comparação temporal de snapshots |
| **Dependências** | Nenhuma |
| **Dependentes** | `core/prediction/foundation.py` |
| **Pipeline** | Histórico → Predição |
| **Demo** | `demo_historical_runtime_foundation.py` |
| **Status** | ⚠️ PARCIAL |

### 22. `core/prediction/`

| Campo | Valor |
|-------|-------|
| **Responsabilidade** | Projeção heurística de futuro |
| **Dependências** | 8 módulos |
| **Dependentes** | Nenhum (⚠️ topo da cadeia sem consumidores) |
| **Pipeline** | Feedback → Histórico → Predição |
| **Demo** | `demo_prediction_runtime_foundation.py` |
| **Status** | ⚠️ PARCIAL (sem consumidores) |

### 23. `core/collaboration/`

| Campo | Valor |
|-------|-------|
| **Responsabilidade** | Orquestração de colaboração entre employees |
| **Dependências** | `core/events/` |
| **Dependentes** | Nenhum |
| **Pipeline** | Colaboração |
| **Demo** | `demo_collaboration_runtime.py` |
| **Status** | ⚠️ PARCIAL (sem snapshot) |

### 24. `core/employees/`

| Campo | Valor |
|-------|-------|
| **Responsabilidade** | Ciclo de vida de employees + cognição |
| **Dependências** | `core/events/` |
| **Dependentes** | `core/orchestrator/runtime.py`, `core/runtime.py` |
| **Pipeline** | Cognição, Orquestração |
| **Demo** | `demo_employee_cognition.py`, `_employee_runtime_demo.py` |
| **Status** | ✅ COMPLETO |

### 25. `core/orchestrator/`

| Campo | Valor |
|-------|-------|
| **Responsabilidade** | Pipeline completo: decisão → execução → aprendizado |
| **Dependências** | 7 módulos |
| **Dependentes** | `core/company/runtime.py` |
| **Pipeline** | Orquestração |
| **Demo** | `demo_orchestrator_conversation_flow.py` |
| **Status** | ⚠️ PARCIAL |

### 26. `core/company/`

| Campo | Valor |
|-------|-------|
| **Responsabilidade** | Company Runtime completo, task lifecycle |
| **Dependências** | 6 módulos |
| **Dependentes** | `core/strategy/foundation.py`, `core/analytics/runtime.py` |
| **Pipeline** | Company |
| **Demo** | `demo_company_runtime.py`, `demo_company_execution_flow.py`, `demo_company_runtime_complete.py` |
| **Status** | ⚠️ PARCIAL |

### 27. `core/decision/`

| Campo | Valor |
|-------|-------|
| **Responsabilidade** | Motor de decisão, avalia candidatos |
| **Dependências** | `core/policies/runtime.py` |
| **Dependentes** | `core/orchestrator/runtime.py`, `core/company/runtime.py`, `core/strategy/foundation.py` |
| **Pipeline** | Orquestração, Decisão |
| **Demo** | `demo_decision_engine.py`, `demo_decision_engine_foundation.py`, `demo_decision_policy_integration.py`, `demo_decision_skill_integration.py` |
| **Status** | 🔴 PENDENTE (sem `__init__.py`) |

### 28. `core/persistence/`

| Campo | Valor |
|-------|-------|
| **Responsabilidade** | Persistência JSON via pathlib |
| **Dependências** | Nenhuma |
| **Dependentes** | `core/knowledge/runtime.py`, `core/skills/runtime.py`, `core/workflows/runtime.py` |
| **Pipeline** | Transversal (persistência de snapshots) |
| **Demo** | `demo_persistence_runtime.py`, `demo_persistence_runtime_integration.py` |
| **Status** | 🔴 PENDENTE (sem `__init__.py`) |

### 29. `core/llm/`

| Campo | Valor |
|-------|-------|
| **Responsabilidade** | LLM Gateway, adapters, prompts, cost tracking |
| **Dependências** | Nenhuma (interna) |
| **Dependentes** | `core/execution/runtime.py`, `core/orchestrator/runtime.py` |
| **Pipeline** | Execução |
| **Demo** | `demo_llm_gateway.py`, `demo_cost_tracker.py`, `demo_openai_adapter.py`, `demo_prompt_builder.py`, `demo_request_builder.py` |
| **Status** | ⚠️ PARCIAL |

### 30. `core/prompts/` 💀 MORTO

| Campo | Valor |
|-------|-------|
| **Responsabilidade** | Contratos de prompt (ABANDONADO) |
| **Evidência** | Zero imports de produção. `core/llm/prompts.py` é a implementação real. |
| **Status** | 💀 MORTO — remover |

### 31. `core/pipeline/` 💀 MORTO

| Campo | Valor |
|-------|-------|
| **Responsabilidade** | Contratos de pipeline (ABANDONADO) |
| **Evidência** | Zero imports de produção. Pipelines reais são independentes. |
| **Status** | 💀 MORTO — remover |

---

## Pipelines

### 1. Execution Pipeline

| Campo | Valor |
|-------|-------|
| **Fluxo** | `prepare_context → execute_llm → validate_output → build_result` |
| **Módulo** | `core/execution/runtime.py` |
| **Dependências** | Conversation, LLM |
| **Demo** | `demo_execution_runtime_foundation.py` |

### 2. Cognition Pipeline

| Campo | Valor |
|-------|-------|
| **Fluxo** | `receive → analyze → plan → prioritize → execute → result` |
| **Módulo** | `core/employees/cognition.py` |
| **Dependências** | Nenhuma |
| **Demo** | `demo_employee_cognition.py` |

### 3. Collaboration Pipeline

| Campo | Valor |
|-------|-------|
| **Fluxo** | `create_request → add_participants → simulate → consolidate → result` |
| **Módulo** | `core/collaboration/foundation.py` |
| **Dependências** | Events |
| **Demo** | `demo_collaboration_runtime.py` |

### 4. Learning Pipeline

| Campo | Valor |
|-------|-------|
| **Fluxo** | `Conversation → Memory → Knowledge → Learning → Skills` |
| **Módulo** | `core/learning/pipeline.py` |
| **Dependências** | Conversation, Memory, Knowledge, Learning, Skills, Events |
| **Demo** | `demo_learning_pipeline.py` |

### 5. Strategy Pipeline

| Campo | Valor |
|-------|-------|
| **Fluxo** | `Strategy → Policy → ExecutionPlan` |
| **Módulo** | `core/strategy/pipeline.py` |
| **Dependências** | Strategy, Policy |
| **Demo** | `demo_strategy_pipeline.py` |

### 6. Optimization Pipeline

| Campo | Valor |
|-------|-------|
| **Fluxo** | `ExecutionPlan → execute approved → retry/rollback → snapshot` |
| **Módulo** | `core/optimization/runtime.py` |
| **Dependências** | ExecutionPlan |
| **Demo** | `demo_auto_optimization_runtime.py` |

### 7. Orchestration Pipeline

| Campo | Valor |
|-------|-------|
| **Fluxo** | `receive → assign → decide → execute → learn → complete` |
| **Módulo** | `core/orchestrator/runtime.py` |
| **Dependências** | Company, Decision, Execution, Learning, Conversation, Events |
| **Demo** | `demo_orchestrator_conversation_flow.py` |

### 8. Company Pipeline

| Campo | Valor |
|-------|-------|
| **Fluxo** | `receive → route → execute → learn → complete` |
| **Módulo** | `core/company/runtime.py` |
| **Dependências** | Orchestrator, Decision, Execution, Learning, Skills |
| **Demo** | `demo_company_runtime_complete.py` |

---

## Foundations vs Runtimes

### Modules with both Foundation AND Runtime (✅ correct pattern)

| Módulo | Foundation | Runtime |
|--------|------------|---------|
| knowledge | `foundation.py` | `runtime.py` |
| skills | `foundation.py` | `runtime.py` |

### Modules with Foundation only (stateless, no runtime needed yet)

| Módulo | Foundation |
|--------|------------|
| learning | `foundation.py` + `pipeline.py` |
| workflow | `foundation.py` |
| execution_plan | `foundation.py` |
| policy | `foundation.py` |
| strategy | `foundation.py` + `pipeline.py` |
| feedback | `foundation.py` |
| history | `foundation.py` |
| prediction | `foundation.py` |
| collaboration | `foundation.py` |
| employees | `cognition.py` (faz papel de foundation) |

### Modules with Runtime only (foundation logic mixed in)

| Módulo | Runtime | ⚠️ Problema |
|--------|---------|-------------|
| conversation | `runtime.py` | @staticmethod mas nome "Runtime" |
| memory | `runtime.py` | @staticmethod mas nome "Runtime" |
| execution | `runtime.py` | @staticmethod mas nome "Runtime" |
| monitoring | `runtime.py` | @staticmethod mas nome "Runtime" |
| analytics | `runtime.py` | @staticmethod mas nome "Runtime" |
| decision | `runtime.py` | @staticmethod mas nome "Runtime", sem `__init__.py` |

### Modules with Stateful Runtime only (genuinely stateful)

| Módulo | Runtime |
|--------|---------|
| employees | `runtime.py` (estado mutável) |
| knowledge | `runtime.py` (estado + eventos) |
| skills | `runtime.py` (estado + eventos) |
| workflows | `runtime.py` (estado + DAG) |
| optimization | `runtime.py` (estado + retry) |
| orchestrator | `runtime.py` (estado + eventos) |
| company | `runtime.py` (estado + eventos) |
| departments | `runtime.py` (estado) |
| tasks | `runtime.py` (estado) |

---

## Eventos por Módulo

| Módulo | Publica | Consome |
|--------|---------|---------|
| `core/runtime.py` | CompanyStateChangedEvent | — |
| `core/events/domain_events.py` | (definições) | — |
| `core/events/bus.py` | (transporte) | — |
| `core/knowledge/runtime.py` | KnowledgePromoted | — |
| `core/skills/runtime.py` | SkillCreated, SkillPromoted, SkillLevelChanged | — |
| `core/workflows/runtime.py` | WorkflowStarted, WorkflowTaskStarted, WorkflowTaskCompleted, WorkflowCompleted | — |
| `core/orchestrator/runtime.py` | OrchestratorExecutionStarted, OrchestratorExecutionCompleted, DecisionApproved, DecisionRejected, ExecutionStarted, ExecutionCompleted, ExecutionFailed | — |
| `core/company/runtime.py` | CompanyTaskReceived, CompanyTaskRouted, CompanyTaskCompleted | — |
| `core/collaboration/foundation.py` | CollaborationStarted, ParticipantResponded, CollaborationCompleted | — |
| `core/learning/pipeline.py` | ConversationCreated, MessageAdded, MemoryRecordCreated, RecommendationCreated | — |
| `core/employees/runtime.py` | EmployeeStateChangedEvent | — |
| `core/optimization/runtime.py` | (eventos internos) | — |
| `core/monitoring/runtime.py` | — | ✅ Todos os eventos |
| `core/observability.py` | — | ✅ Eventos específicos |
| `core/departments/runtime.py` | DepartmentStateChangedEvent | — |
| `core/tasks/runtime.py` | TaskStateChangedEvent | — |
| `core/results/runtime.py` | ResultStateChangedEvent | — |

---

## Legenda de Status

| Símbolo | Significado |
|---------|-------------|
| ✅ COMPLETO | Foundation + Runtime + Snapshot + Events |
| ⚠️ PARCIAL | Funcional, mas falta algum elemento do padrão |
| 🔴 PENDENTE | Tem anomalia crítica que impede uso como pacote |
| 💀 MORTO | Zero imports de produção — remover |

---

*Consulte `PLATFORM_CONSTITUTION.md` para a especificação completa de cada módulo.*
*Consulte `PLATFORM_DEPENDENCY_GRAPH.md` para o mapa de dependências detalhado.*
