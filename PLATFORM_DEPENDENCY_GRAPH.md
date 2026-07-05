# PLATFORM DEPENDENCY GRAPH

**AI Content Factory — Mapa de Dependências entre Módulos**

---

## 1. Convenções

```
Módulo A → Módulo B   : A importa B (A depende de B)
Módulo A ⇄ Módulo B   : Dependência circular
[Módulo A]             : Módulo completo
(Módulo A)             : Módulo parcial
[!Módulo A]            : Módulo com anomalia
```

## 2. Dependências de Foundations

### Foundations puras (stateless, sem runtime)

```text
FoundationConversationRuntime
    → core/memory/runtime.py

FoundationMemoryRuntime
    → core/knowledge/ (TYPE_CHECKING)

FoundationKnowledgeRuntime
    → core/memory/runtime.py

FoundationLearningRuntime
    → core/knowledge/foundation.py

FoundationSkillRuntime
    → core/learning/foundation.py

FoundationWorkflowRuntime
    → (nenhuma)

FoundationExecutionRuntime
    → core/conversation/runtime.py
    → core/llm/models.py

FoundationExecutionPlanRuntime
    → core/policy/foundation.py
    → core/strategy/pipeline.py

FoundationPolicyRuntime
    → (nenhuma)

FoundationStrategyRuntime
    → core/analytics/runtime.py
    → core/monitoring/runtime.py
    → core/knowledge/foundation.py
    → core/learning/foundation.py
    → core/skills/foundation.py
    → core/skills/runtime.py
    → core/company/runtime.py
    → core/decision/runtime.py
    → core/llm/cost_tracker.py
    → core/workflows/runtime.py

FoundationFeedbackRuntime
    → (nenhuma)

FoundationHistoricalRuntime
    → (nenhuma)

FoundationPredictionRuntime
    → core/history/foundation.py
    → core/analytics/runtime.py
    → core/feedback/foundation.py
    → core/monitoring/runtime.py
    → core/strategy/foundation.py
    → core/learning/foundation.py
    → core/skills/foundation.py
    → core/workflows/runtime.py

CognitiveEmployeeFoundation
    → (nenhuma)

[CollaborationFoundation]
    → core/events/
```

## 3. Dependências de Stateful Runtimes

```text
[RuntimeStateManager]
    → core/employees/runtime.py
    → core/events/bus.py

[EmployeeRuntime]
    → core/events/bus.py

[KnowledgeRuntime]
    → core/knowledge/foundation.py
    → core/events/bus.py
    → core/persistence/_helpers.py

[SkillRuntime]
    → core/skills/foundation.py
    → core/events/bus.py
    → core/persistence/_helpers.py

[WorkflowRuntime (workflows/)]
    → core/workflow/foundation.py
    → core/events/bus.py
    → core/tasks/
    → core/runtime.py
    → core/persistence/_helpers.py

[OptimizationRuntime]
    → core/execution_plan/foundation.py
    → core/events/bus.py  (? — confirmar)

[OrchestratorRuntime]
    → core/runtime.py
    → core/events/bus.py
    → core/conversation/runtime.py
    → core/decision/runtime.py
    → core/execution/runtime.py
    → core/learning/pipeline.py
    → core/llm/models.py
    → core/results/models.py

[CompanyTaskRuntime]
    → core/runtime.py
    → core/events/bus.py
    → core/decision/runtime.py
    → core/execution/runtime.py
    → core/learning/pipeline.py
    → core/skills/runtime.py

[!DecisionRuntime]
    → core/policies/runtime.py
    → (sem __init__.py)

[PolicyEngine (policies/)]
    → core/exceptions/

[DepartmentRuntime]
    → core/events/bus.py

[TaskRuntime]
    → core/runtime.py
    → core/events/bus.py

[ResultRuntime]
    → core/events/bus.py
```

## 4. Dependências de Pipelines

```text
[StrategyPipeline]
    → core/strategy/foundation.py
    → core/policy/foundation.py

[LearningPipeline]
    → core/conversation/runtime.py
    → core/memory/runtime.py
    → core/knowledge/foundation.py
    → core/learning/foundation.py
    → core/skills/foundation.py
    → core/skills/runtime.py
    → core/events/bus.py
```

## 5. Dependências Camada por Camada

### Camada 0 — Infraestrutura Base
```text
core/exceptions/ → (nenhuma)
core/config/ → core/exceptions/
core/logging/ → core/exceptions/
core/models/ → (nenhuma)
core/container/ → (nenhuma)
core/pipeline/ → (nenhuma)  ← MORTO
core/prompts/ → core/exceptions/  ← MORTO
```

### Camada 1 — Eventos
```text
core/events/ → core/exceptions/
```

### Camada 2 — Foundation (Conversation, Memory)
```text
core/conversation/ → core/memory/
core/memory/ → core/knowledge/ (TYPE_CHECKING)
```

### Camada 3 — Foundation (Knowledge, Learning, Skills)
```text
core/knowledge/ → core/memory/ (foundation), core/events/ (runtime)
core/learning/ → core/knowledge/, core/conversation/, core/memory/, core/skills/
core/skills/ → core/learning/, core/events/, core/persistence/
```

### Camada 4 — Workflow
```text
core/workflow/ → (nenhuma)  ← Foundation
core/workflows/ → core/workflow/, core/events/, core/tasks/, core/runtime/, core/persistence/
```

### Camada 5 — Execução
```text
core/execution/ → core/conversation/, core/llm/models.py
core/execution_plan/ → core/policy/, core/strategy/
```

### Camada 6 — Monitoramento & Analytics
```text
core/monitoring/ → core/events/bus.py
core/analytics/ → core/company/, core/decision/, core/execution/, core/learning/, core/llm/, core/skills/, core/workflows/
```

### Camada 7 — Estratégia & Política
```text
core/strategy/ → core/analytics/, core/monitoring/, core/knowledge/, core/learning/,
                core/skills/, core/company/, core/decision/, core/llm/, core/workflows/, core/policy/
core/policy/ → (nenhuma)
core/policies/ → core/exceptions/  ← DUPLICADO
```

### Camada 8 — Otimização
```text
core/optimization/ → core/execution_plan/
```

### Camada 9 — Feedback, History, Prediction
```text
core/feedback/ → (nenhuma)
core/history/ → (nenhuma)
core/prediction/ → core/history/, core/analytics/, core/feedback/, core/monitoring/,
                  core/strategy/, core/learning/, core/skills/, core/workflows/
```

### Camada 10 — Colaboração
```text
core/collaboration/ → core/events/
```

### Camada 11 — Employees, Departments, Organization
```text
core/employees/ → core/events/
core/departments/ → core/exceptions/, core/events/
core/organization/ → core/exceptions/
```

### Camada 12 — Orquestração
```text
core/orchestrator/ → core/events/, core/runtime/, core/conversation/, core/decision/,
                    core/execution/, core/learning/, core/llm/
```

### Camada 13 — Company
```text
core/company/ → core/events/, core/decision/, core/execution/, core/learning/, core/skills/, core/runtime/
core/runtime.py → core/employees/, core/events/  (top-level)
```

### Camada 14 — Persistência
```text
core/persistence/ → (nenhuma)  ← sem __init__.py
```

### Independentes
```text
core/llm/ → (nenhuma interna)
core/results/ → core/exceptions/
core/tasks/ → core/exceptions/, core/runtime/
core/observability.py → múltiplos módulos (leitura de snapshots)
```

## 6. Grafos de Dependência por Pipeline

### Pipeline de Execução AI
```text
ExecutionRuntime
  ├── ConversationRuntime (para logging de conversa)
  └── LLMRequest/Response (models)
```
→ Nenhum evento. Nenhum snapshot. Input: task+employee snapshot. Output: ExecutionResult.

### Pipeline de Aprendizado (LearningPipeline)
```text
LearningPipeline.run()
  ├── ConversationRuntime.messages
  ├── MemoryRuntime.create_records_from_messages()
  ├── FoundationKnowledgeRuntime.promote_from_memory()
  ├── FoundationLearningRuntime.generate_recommendations()
  ├── FoundationSkillRuntime.promote_from_learning()
  └── SkillRuntime (stateful) → SkillRuntimeSnapshot
```
→ Eventos: ConversationCreated, MessageAdded, MemoryRecordCreated, KnowledgePromoted, RecommendationCreated

### Pipeline de Estratégia (StrategyPipeline)
```text
StrategyPipeline.run()
  ├── FoundationStrategyRuntime.analyze_*(snapshots) → StrategySnapshot
  ├── FoundationPolicyRuntime.evaluate_all(rules, recommendations) → PolicyResult
  └── _build_plan(evaluations, recommendations) → StrategyExecutionPlan
```
→ Sem eventos. Input: múltiplos snapshots. Output: StrategyExecutionPlan.

### Pipeline de Orquestração (OrchestratorRuntime)
```text
OrchestratorRuntime.execute_task()
  ├── DecisionEngine.evaluate() → DecisionResult
  │     └── PolicyEngine.evaluate() → PolicyResult
  ├── ExecutionRuntime.execute() → ExecutionResult
  │     └── LLMGateway.execute() → LLMResponse
  └── LearningPipeline.run() → PipelineResult
```
→ Eventos: OrchestratorExecutionStarted, OrchestratorExecutionCompleted,
  DecisionApproved/Rejected, ExecutionStarted/Completed/Failed

## 7. Ciclos Completos Verificados

### Ciclo Completo de uma Task (Orquestrador → Execução → Aprendizado)
```text
[ORCHESTRATOR]
CompanyRuntime.receive_task()
    → OrchestratorRuntime.receive_task()
        → CompanyRuntime.register_task() → TaskRecord
        → DepartmentRuntime.assign_task()
        → EmployeeRuntime.assign_task()
    → OrchestratorRuntime.execute_task()
        → DecisionEngine.evaluate()
            → PolicyEngine.evaluate_constraints()
        → ExecutionRuntime.execute()
            → LLMGateway.execute()
        → LearningPipeline.run()
            → MemoryRuntime.create_records()
            → KnowledgeRuntime.promote_from_memory()
            → LearningRuntime.generate_recommendations()
            → SkillRuntime.promote_from_learning()
    → CompanyRuntime.complete_task()
```

✅ Ciclo completo verificado e funcional (demo_company_runtime_complete.py).

### Ciclo Estratégia → Otimização → Feedback → Histórico → Predição
```text
[STRATEGY LOOP]
StrategyRuntime.analyze_all(snapshots) → StrategySnapshot
    → StrategyPipeline.run(rules) → StrategyExecutionPlan
        → ExecutionPlanFoundation.build() → ExecutionPlan
            → OptimizationRuntime.execute() → OptimizationSnapshot
                → FeedbackRuntime.compare(expected, actual) → FeedbackSnapshot
                    → HistoricalRuntime.compare(before, after) → HistoricalSnapshot
                        → PredictionRuntime.predict(snapshots, history) → PredictionSnapshot
```

✅ Ciclo completo verificado e funcional (demos individuais, faltando demo integrado único).

## 8. Dependências Circulares

**NENHUMA DEPENDÊNCIA CIRCULAR ENCONTRADA.** ✅

Todas as dependências seguem o fluxo:
```
Foundation → Foundation superior
Foundation → Core/Infra
Runtime → Foundation
Runtime → Eventos (opcional)
Pipeline → Foundation(s)
Camada inferior → Camada superior: ❌ PROIBIDO
```

## 9. Desequilíbrios no Grafo

| Problema | Detalhe |
|----------|---------|
| **13 publishers, 1 subscriber** | Events são produzidos por 13 módulos mas apenas `observability.py` consome. Nenhum módulo reage a eventos de outro módulo. |
| **Prediction no topo, sem consumidores** | `core/prediction/` é o módulo no topo da cadeia mas ninguém consome suas predições. |
| **Persistence sem `__init__.py`** | `core/persistence/` não pode ser importado como pacote. |
| **Decision sem `__init__.py`** | `core/decision/` não pode ser importado como pacote. |
| **Strategy depende de quase tudo** | `core/strategy/foundation.py` importa 10 outros módulos — maior fan-out do sistema. |
