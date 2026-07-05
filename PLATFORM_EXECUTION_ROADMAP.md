# PLATFORM EXECUTION ROADMAP

**AI Content Factory — Roadmap de Execução Definitivo**

---

## Visão Geral

O roadmap está dividido em 5 fases. Cada fase contém etapas executáveis com critérios de conclusão objetivos.

---

## Fase 1 — Refinamento (1-2 sprints)

### 1.1 Corrigir `__init__.py` ausentes

| Etapa | `core/decision/__init__.py` |
|-------|---------------------------|
| **Objetivo** | Criar `__init__.py` para `core/decision/` com exports |
| **Arquivos** | `core/decision/__init__.py` (novo) |
| **Impacto** | Permite `from core.decision import DecisionEngine` |
| **Complexidade** | Mínima |
| **Dependências** | Nenhuma |
| **Critério** | `python -c "from core.decision import DecisionEngine"` funciona |

| Etapa | `core/persistence/__init__.py` |
|-------|-------------------------------|
| **Objetivo** | Criar `__init__.py` para `core/persistence/` com exports |
| **Arquivos** | `core/persistence/__init__.py` (novo) |
| **Impacto** | Permite `from core.persistence import PersistenceRuntime` |
| **Complexidade** | Mínima |
| **Dependências** | Nenhuma |
| **Critério** | `python -c "from core.persistence import PersistenceRuntime"` funciona |

### 1.2 Remover módulos mortos

| Etapa | Remover `core/prompts/` |
|-------|------------------------|
| **Objetivo** | Remover módulo não utilizado (zero imports de produção) |
| **Arquivos** | Todo `core/prompts/` (8 arquivos) |
| **Impacto** | Zero — ninguém importa |
| **Complexidade** | Mínima |
| **Dependências** | Nenhuma |
| **Critério** | `compileall core/` passa, regressão intacta |

| Etapa | Remover `core/pipeline/` |
|-------|-------------------------|
| **Objetivo** | Remover módulo não utilizado (zero imports de produção) |
| **Arquivos** | Todo `core/pipeline/` (4 arquivos) |
| **Impacto** | Zero — ninguém importa |
| **Complexidade** | Mínima |
| **Dependências** | Nenhuma |
| **Critério** | `compileall core/` passa, regressão intacta |

### 1.3 Renomear classes com naming collision

| Etapa | Renomear `WorkflowRuntime` em `core/workflow/foundation.py` |
|-------|------------------------------------------------------------|
| **Objetivo** | Eliminar colisão com `core/workflows/runtime.py.WorkflowRuntime` |
| **Arquivos** | `core/workflow/foundation.py`, `core/workflows/runtime.py` (imports) |
| **Impacto** | Quebra imports em `core/workflows/runtime.py` — requer atualização |
| **Complexidade** | Baixa |
| **Dependências** | Nenhuma |
| **Critério** | `FoundationWorkflowRuntime` não colide com `WorkflowRuntime` |

### 1.4 Unificar `core/policy/` e `core/policies/`

| Etapa | Unificar avaliação de políticas |
|-------|-------------------------------|
| **Objetivo** | Unificar `core/policy/` (Foundation) e `core/policies/` (Runtime) em um único pacote |
| **Arquivos** | `core/policy/foundation.py`, `core/policies/runtime.py`, `core/strategy/pipeline.py`, `core/execution_plan/foundation.py`, `core/decision/runtime.py` |
| **Impacto** | Médio — afeta imports em 4 módulos |
| **Complexidade** | Média |
| **Dependências** | Etapas 1.1, 1.2, 1.3 |
| **Critério** | Ambos os consumers (strategy/pipeline, decision/runtime) funcionam com o pacote unificado |

### 1.5 Padronizar Foundation/Runtime split

| Etapa | Extrair Foundations dos módulos que misturam padrão |
|-------|-----------------------------------------------------|
| **Objetivo** | 8 módulos (conversation, memory, execution, monitoring, analytics, optimization, company, decision) têm lógica foundation embutida em runtime.py. Extrair para `foundation.py`. |
| **Arquivos** | `core/conversation/foundation.py` (novo), `core/conversation/runtime.py` (refatorado), +7 pares similares |
| **Impacto** | Alto — muda estrutura de pacotes, afeta imports |
| **Complexidade** | Alta |
| **Dependências** | Etapas 1.1-1.4 |
| **Critério** | Todos os módulos têm `foundation.py` com `@staticmethod` e `runtime.py` separado |

---

## Fase 2 — Integrações (2-3 sprints)

### 2.1 Conectar Prediction a consumidores

| Etapa | PredictionRuntime ou consumidores |
|-------|----------------------------------|
| **Objetivo** | `core/prediction/` está no topo da cadeia sem consumidores. Criar consumidor ou runtime stateful que usa predições. |
| **Arquivos** | `core/prediction/` (existente), novo consumidor |
| **Impacto** | Fecha a última lacuna da cadeia |
| **Complexidade** | Média |
| **Dependências** | Fase 1 completa |
| **Critério** | Predição é consumida por pelo menos 1 módulo |

### 2.2 Conectar Feedback → Histórico → Predição em pipeline único

| Etapa | Pipeline Feedback-Histórico-Predição |
|-------|-------------------------------------|
| **Objetivo** | Criar pipeline integrado que conecta Feedback → Historical → Prediction |
| **Arquivos** | Novo pipeline ou integração em runtime existente |
| **Impacto** | Fecha o ciclo completo de aprendizado |
| **Complexidade** | Média |
| **Dependências** | Etapa 2.1 |
| **Critério** | Pipeline integrado funcional com demo |

### 2.3 Implementar event reactors

| Etapa | Reatores de evento por módulo |
|-------|------------------------------|
| **Objetivo** | Módulos devem reagir a eventos de outros módulos (ex: Optimization reagir a DecisionApproved) |
| **Arquivos** | Múltiplos runtimes |
| **Impacto** | Torna o sistema verdadeiramente event-driven |
| **Complexidade** | Alta |
| **Dependências** | Fase 1 completa |
| **Critério** | Pelo menos 3 módulos reagem a eventos de outros módulos |

### 2.4 Integrar Persistence com todos os runtimes

| Etapa | Persistência automática |
|-------|------------------------|
| **Objetivo** | Todos os runtimes stateful devem salvar snapshots automaticamente via PersistenceRuntime |
| **Arquivos** | Todos os runtimes stateful |
| **Impacto** | Garante durabilidade dos dados |
| **Complexidade** | Média |
| **Dependências** | Etapa 1.1 (__init__.py) |
| **Critério** | Cada runtime stateful tem integração com persistence |

---

## Fase 3 — Produto (3-4 sprints)

### 3.1 Criar suíte de testes automatizados

| Etapa | Testes unitários e de integração |
|-------|----------------------------------|
| **Objetivo** | Substituir demos por testes automatizados com pytest |
| **Arquivos** | `tests/` (novo diretório) |
| **Impacto** | Qualidade, confiabilidade, CI/CD |
| **Complexidade** | Alta |
| **Dependências** | Fases 1-2 completas |
| **Critério** | Cobertura > 60% nos módulos essenciais |

### 3.2 Documentação técnica completa

| Etapa | Documentação |
|-------|-------------|
| **Objetivo** | Docstrings, READMEs, diagramas atualizados |
| **Arquivos** | Todos os módulos |
| **Impacto** | Manutenibilidade |
| **Complexidade** | Média |
| **Dependências** | Fases 1-2 completas |
| **Critério** | Cada módulo público tem docstring |

### 3.3 CI/CD pipeline

| Etapa | Integração contínua |
|-------|-------------------|
| **Objetivo** | GitHub Actions: compileall + regressão + testes |
| **Arquivos** | `.github/workflows/` |
| **Impacto** | Automação de qualidade |
| **Complexidade** | Média |
| **Dependências** | Etapa 3.1 |
| **Critério** | PRs são validados automaticamente |

### 3.4 Melhorias de performance

| Etapa | Performance |
|-------|-----------|
| **Objetivo** | Otimizar hot paths (strategy, prediction), adicionar caching se necessário |
| **Arquivos** | `core/strategy/`, `core/prediction/`, `core/persistence/` |
| **Impacto** | Velocidade |
| **Complexidade** | Média |
| **Dependências** | Fases 1-2 completas |
| **Critério** | Demos executam em < 2s |

---

## Fase 4 — Interface 2.5D (2-3 sprints)

### 4.1 Escritório 2.5D MVP

| Etapa | Interface visual |
|-------|-----------------|
| **Objetivo** | Criar projeção visual 2.5D do estado da empresa usando `ObservabilitySnapshot` |
| **Arquivos** | `office/` (novo diretório) |
| **Impacto** | Visualização do sistema |
| **Complexidade** | Alta |
| **Dependências** | Fases 1-3 completas |
| **Critério** | Escritório 2.5D funcional com employees animados |

### 4.2 WebSocket bridge

| Etapa | Comunicação em tempo real |
|-------|--------------------------|
| **Objetivo** | Bridge entre EventBus e WebSocket para frontend |
| **Arquivos** | `core/events/ws_bridge.py` (novo) |
| **Impacto** | Tempo real |
| **Complexidade** | Alta |
| **Dependências** | Etapa 4.1 |
| **Critério** | Eventos aparecem no frontend em < 100ms |

---

## Fase 5 — Automação Completa (4-6 sprints)

### 5.1 Scheduler/Agendador

| Etapa | Execução programada |
|-------|-------------------|
| **Objetivo** | Agendar execuções de otimização e tarefas |
| **Arquivos** | `core/scheduler/` (novo) |
| **Impacto** | Automação temporal |
| **Complexidade** | Alta |
| **Dependências** | Fases 1-4 completas |
| **Critério** | Tarefa agendada executa automaticamente |

### 5.2 Alerting Runtime

| Etapa | Notificações proativas |
|-------|----------------------|
| **Objetivo** | Detectar anomalias em MonitoringSnapshot e notificar |
| **Arquivos** | `core/alerting/` (novo) |
| **Impacto** | Confiabilidade |
| **Complexidade** | Média |
| **Dependências** | Fase 3 completa |
| **Critério** | Alerta gerado quando health_score < 30 |

### 5.3 Dashboard Analytics

| Etapa | Dashboard gerencial |
|-------|-------------------|
| **Objetivo** | Agregar PerformanceSnapshot + MonitoringSnapshot + OptimizationSnapshot em dashboard |
| **Arquivos** | `core/dashboard/` (novo) |
| **Impacto** | Visibilidade |
| **Complexidade** | Média |
| **Dependências** | Fases 1-3 completas |
| **Critério** | Dashboard com métricas atualizadas em tempo real |

### 5.4 Providers reais para engines

| Etapa | Implementar engines |
|-------|-------------------|
| **Objetivo** | Substituir placeholders vazios em `engines/` por implementações reais |
| **Arquivos** | `engines/script/`, `engines/video/`, `engines/audio/`, etc. |
| **Impacto** | Produção de conteúdo real |
| **Complexidade** | Muito alta |
| **Dependências** | Fases 1-4 completas |
| **Critério** | Pipeline completo de conteúdo (texto → áudio → vídeo → legenda → thumbnail → publicação) |

---

## Resumo Cronológico

```text
Fase 1 — Refinamento:       semanas 1-2   🔴 FAZER AGORA
  1.1 __init__.py ausentes
  1.2 Remover módulos mortos
  1.3 Renomear naming collision
  1.4 Unificar policy/policies
  1.5 Padronizar Foundation/Runtime

Fase 2 — Integrações:        semanas 3-5
  2.1 Prediction consumidores
  2.2 Pipeline Feedback→Historical→Prediction
  2.3 Event reactors
  2.4 Persistence universal

Fase 3 — Produto:            semanas 6-9
  3.1 Testes automatizados
  3.2 Documentação técnica
  3.3 CI/CD
  3.4 Performance

Fase 4 — Interface 2.5D:     semanas 10-12
  4.1 Escritório 2.5D MVP
  4.2 WebSocket bridge

Fase 5 — Automação Completa: semanas 13-18
  5.1 Scheduler
  5.2 Alerting
  5.3 Dashboard
  5.4 Engines reais
```
