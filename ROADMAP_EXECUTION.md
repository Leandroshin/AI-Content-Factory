# ROADMAP EXECUTION

**AI Content Factory — Roadmap Oficial de Execução**
*Julho de 2026 — Fase de Refinamento*

---

## Preâmbulo

A fase de expansão arquitetural está encerrada. A plataforma possui todas as camadas essenciais implementadas.

Este roadmap define a sequência executável para transformar a plataforma de um conjunto de módulos funcionais em um produto coeso, testado, documentado e preparado para operar qualquer vertical de negócio.

Cada fase tem critérios de conclusão objetivos. Nenhuma fase avança sem que a anterior esteja completa.

---

## Fase 1 — Refinamento

**Objetivo:** Corrigir anomalias críticas, remover código morto, unificar módulos duplicados, padronizar nomenclatura.

### Etapa 1.1 — Criar `__init__.py` ausentes

| Módulo | Problema | Ação | Complexidade |
|--------|----------|------|-------------|
| `core/decision/` | 🔴 Sem `__init__.py` | Criar com exports de `DecisionEngine`, `DecisionContext`, `DecisionResult`, `DecisionTrace`, `DecisionContextBuilder` | Mínima |
| `core/persistence/` | 🔴 Sem `__init__.py` | Criar com exports de `PersistenceRuntime`, `PersistenceSnapshot`, `PersistenceResult`, `PersistenceTrace` | Mínima |

**Critério de conclusão:**
```python
python -c "from core.decision import DecisionEngine"
python -c "from core.persistence import PersistenceRuntime"
```
Ambos funcionam sem erro.

**Dependências:** Nenhuma.
**Status:** 🔴 Pendente.

---

### Etapa 1.2 — Remover módulos mortos

| Módulo | Evidência | Ação |
|--------|-----------|------|
| `core/prompts/` | Zero imports de produção. `core/llm/prompts.py` é a implementação real. | Remover diretório completo (8 arquivos) |
| `core/pipeline/` | Zero imports de produção. `StrategyPipeline` e `LearningPipeline` são independentes. | Remover diretório completo (4 arquivos) |

**Critério de conclusão:**
- `python -m compileall core/` passa sem erros
- Nenhum demo quebra (regressão completa)

**Dependências:** Nenhuma.
**Status:** 🔴 Pendente.

---

### Etapa 1.3 — Renomear naming collision

| Módulo | Problema | Ação |
|--------|----------|------|
| `core/workflow/foundation.py` | Classe `WorkflowRuntime` colide com `core/workflows/runtime.py.WorkflowRuntime` | Renomear para `FoundationWorkflowRuntime` |

**Impacto:** Quebra imports em `core/workflows/runtime.py` — requer atualização de 1 import.
**Complexidade:** Mínima.
**Critério de conclusão:** Nenhum erro de import após renomeação.
**Dependências:** Nenhuma.
**Status:** 🔴 Pendente.

---

### Etapa 1.4 — Unificar `core/policy/` e `core/policies/`

| Ação | Detalhe |
|------|---------|
| **Problema** | Ambos avaliam políticas com modelos diferentes. Ambos são importados por consumers diferentes. |
| **Solução** | Unificar em um único pacote `core/policy/` (Foundation) + `core/policies/` (Runtime). Manter a separação conceitual mas eliminar duplicação de modelos. |
| **Consumers** | `core/strategy/pipeline.py` importa `policy/`. `core/decision/runtime.py` importa `policies/`. |

**Complexidade:** Média.
**Dependências:** Etapas 1.1, 1.2, 1.3.
**Status:** 🟡 Pendente.

---

### Etapa 1.5 — Padronizar Foundation/Runtime split

| Problema | 8 módulos têm lógica foundation embutida em arquivos chamados `runtime.py` |
|----------|---------------------------------------------------------------------------|
| **Módulos** | conversation, memory, execution, monitoring, analytics, optimization, company, decision |
| **Ação** | Para cada um: extrair métodos `@staticmethod` para `foundation.py` (novo), manter `runtime.py` apenas para estado mutável |

**Complexidade:** Alta (afeta múltiplos imports em demos e dependentes).
**Dependências:** Etapas 1.1-1.4.
**Status:** 🟡 Pendente.

---

### Fase 1 — Critérios de conclusão

- [ ] `core/decision/` e `core/persistence/` têm `__init__.py`
- [ ] `core/prompts/` e `core/pipeline/` removidos
- [ ] `FoundationWorkflowRuntime` não colide com `WorkflowRuntime`
- [ ] `core/policy/` e `core/policies/` unificados sem quebra de consumers
- [ ] 8 módulos com Foundation/Runtime split padronizado
- [ ] Regressão completa (todos os demos) passa com 0 falhas
- [ ] `python -m compileall core/` sem erros

---

## Fase 2 — Integrações

**Objetivo:** Conectar módulos que estão isolados, implementar event reactors, tornar o sistema verdadeiramente event-driven.

### Etapa 2.1 — Conectar Prediction a consumidores

| Item | Detalhe |
|------|---------|
| **Problema** | `core/prediction/` está no topo da cadeia sem consumidores |
| **Solução** | Criar integração entre Prediction e CompanyRuntime ou OptimizationRuntime para usar predições no planejamento |
| **Complexidade** | Média |
| **Dependências** | Fase 1 completa |

### Etapa 2.2 — Pipeline Feedback → Historical → Prediction

| Item | Detalhe |
|------|---------|
| **Problema** | Módulos existem individualmente, mas não há pipeline integrado |
| **Solução** | Criar pipeline que conecta Feedback → Historical → Prediction em um fluxo |
| **Complexidade** | Média |
| **Dependências** | Etapa 2.1 |

### Etapa 2.3 — Event reactors

| Item | Detalhe |
|------|---------|
| **Problema** | 13 módulos publicam eventos, apenas 1 subscriber |
| **Solução** | Implementar reactors em módulos-chave (ex: Optimization reagir a DecisionApproved) |
| **Complexidade** | Alta |
| **Dependências** | Fase 1 completa |

### Etapa 2.4 — Persistência universal

| Item | Detalhe |
|------|---------|
| **Problema** | Apenas Knowledge, Skill, Workflow integram com PersistenceRuntime |
| **Solução** | Todos os runtimes stateful salvam snapshots automaticamente |
| **Complexidade** | Média |
| **Dependências** | Etapa 1.1 (__init__.py) |

---

## Fase 3 — Empresa Virtual

**Objetivo:** Transformar a plataforma em uma empresa digital funcional e autônoma, capaz de operar qualquer vertical de negócio.

### Etapa 3.1 — Sistema de receita e custos

| Item | Detalhe |
|------|---------|
| **Problema** | Plataforma não tem noção de receita, lucro ou ROI |
| **Solução** | Implementar módulo de contabilidade que rastreia receita por task, custos de LLM, ROI por vertical |
| **Complexidade** | Alta |
| **Dependências** | Fase 2 completa |

### Etapa 3.2 — Especialização por vertical

| Item | Detalhe |
|------|---------|
| **Problema** | A empresa é genérica demais para operar sem configuração |
| **Solução** | Sistema de templates de vertical que configura employees, workflows, políticas e estratégia para um mercado específico |
| **Complexidade** | Média |
| **Dependências** | Etapa 3.1 |

### Etapa 3.3 — Automação de ciclo completo

| Item | Detalhe |
|------|---------|
| **Problema** | Pipeline termina na predição sem loop de feedback contínuo |
| **Solução** | Implementar scheduler que executa Strategy → Policy → Execution Plan → Optimization → Feedback → Historical → Prediction em loop |
| **Complexidade** | Alta |
| **Dependências** | Etapas 2.2, 3.1 |

### Etapa 3.4 — Testes automatizados

| Item | Detalhe |
|------|---------|
| **Problema** | 53 demos manuais (24K linhas) sem testes automatizados |
| **Solução** | Criar suíte pytest com fixtures para todos os módulos |
| **Complexidade** | Muito alta |
| **Dependências** | Fase 1 completa |

### Etapa 3.5 — CI/CD

| Item | Detalhe |
|------|---------|
| **Solução** | GitHub Actions: compileall + regressão + pytest |
| **Complexidade** | Média |
| **Dependências** | Etapa 3.4 |

---

## Fase 4 — Interface 2.5D

**Objetivo:** Criar representação visual da empresa digital.

### Etapa 4.1 — Escritório 2.5D MVP

| Item | Detalhe |
|------|---------|
| **Problema** | Sem interface visual para o estado da empresa |
| **Solução** | Renderização 2.5D do escritório com employees animados, baseada em `ObservabilitySnapshot` |
| **Complexidade** | Muito alta |
| **Dependências** | Fase 3 completa |

### Etapa 4.2 — WebSocket bridge

| Item | Detalhe |
|------|---------|
| **Solução** | Bridge entre EventBus e WebSocket para atualização em tempo real |
| **Complexidade** | Alta |
| **Dependências** | Etapa 4.1 |

---

## Fase 5 — Especializações de Negócio

**Objetivo:** Aplicar a empresa digital a verticais reais de negócio.

### Etapa 5.1 — Providers de engine reais

| Item | Detalhe |
|------|---------|
| **Problema** | `engines/` tem apenas Script Engine implementado; demais são placeholders vazios |
| **Solução** | Implementar engines reais para vídeo, áudio, thumbnail, legenda |
| **Complexidade** | Muito alta |
| **Dependências** | Fase 3 completa |

### Etapa 5.2 — Verticais de negócio

| Vertical | Descrição |
|----------|-----------|
| **GTA 6** | Criação automatizada de conteúdo sobre GTA 6 |
| **Podcasts** | Geração e publicação de podcasts |
| **TikTok Shop** | Automação de loja TikTok |
| **Afiliados** | Marketing de afiliados automatizado |
| **Polymarket** | Análise e trading em mercados preditivos |
| **Cursos** | Criação e venda de cursos online |
| **Jogos Indie** | Desenvolvimento e publicação de jogos |
| **Produtos Digitais** | Criação e venda de produtos digitais |

Cada vertical é uma **configuração** da mesma empresa digital — não uma nova plataforma.

---

## Resumo Cronológico

```text
Fase 1 — Refinamento:           agora       🔴 5 etapas
  1.1 __init__.py ausentes
  1.2 Remover módulos mortos
  1.3 Renomear naming collision
  1.4 Unificar policy/policies
  1.5 Padronizar Foundation/Runtime

Fase 2 — Integrações:           próximo      🟡 4 etapas
  2.1 Prediction consumidores
  2.2 Pipeline Feedback→Historical→Prediction
  2.3 Event reactors
  2.4 Persistence universal

Fase 3 — Empresa Virtual:       médio prazo  🟢 5 etapas
  3.1 Receita e custos
  3.2 Especialização por vertical
  3.3 Automação de ciclo completo
  3.4 Testes automatizados
  3.5 CI/CD

Fase 4 — Interface 2.5D:       longo prazo  🟢 2 etapas
  4.1 Escritório 2.5D MVP
  4.2 WebSocket bridge

Fase 5 — Especializações:       futuro       🟢 2 etapas
  5.1 Providers de engine reais
  5.2 Verticais de negócio (GTA 6, Podcasts, etc.)
```

---

## Anexo: Modelo de Relatório de Progresso

Cada etapa concluída deve gerar:

```text
Etapa: {nome}
Status: ✅ CONCLUÍDA
Arquivos modificados: {lista}
Regressão: {X}/{Y} passed, {Z} failed
Compileall: OK/FAIL
Duração: {horas}
```

---

*Roadmap oficial — atualizado em Julho de 2026.*
*Nenhuma fase avança sem que a anterior esteja 100% completa.*
