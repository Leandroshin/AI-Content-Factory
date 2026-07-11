# MASTER ROADMAP — AI Company

Este documento é a referência máxima de evolução da AI Company. Ele consolida o
estado atual, a arquitetura já estabilizada, os módulos concluídos, as
pendências reais e a ordem oficial de evolução até a versão 1.0.

---

## Atualizacao canonica - 10/07/2026

O estado operacional atual esta em:

docs/CURRENT_STATE_2026-07-10.md

As contagens e pendencias abaixo preservam o roadmap original e parte da
historia arquitetural. Elas nao substituem o estado canonico mais novo.

Resumo atual:

- 96 demos presentes;
- regressao padronizada: 96/96 demos, 0 falhas;
- 1416 assertions explicitamente reportadas por 40 demos;
- departamentos adicionais: Affiliate Deals, Strategy Intelligence, Product
  Research e Creative Review;
- fluxo integrado: Strategy Intelligence -> Product Research -> Creative
  Review -> Affiliate Deals -> HITL Approval -> Telegram;
- dashboard local persistente com entrada manual, aprovacao, rejeicao e
  publicacao MOCK;
- proxima fronteira: dados reais de produto, APIs oficiais, Meta read-only,
  hospedagem, conversoes e ROI.

---

## 1. Estado atual

### Resumo objetivo da arquitetura existente

A plataforma já possui uma fundação arquitetural ampla, contract-first e em boa
parte operacionalizada em memória. O núcleo atual cobre:

- fundamentos de configuração, container e prompts;
- eventos internos e bus síncrono/determinístico;
- empresa, runtime global, departamentos, employees, tasks, workflows, results,
  knowledge e skills;
- orquestração, execução e projeções de observability;
- bases para ações estratégicas, políticas, memória, aprendizado, colaboração,
  estratégia e execução;
- diversos blueprints e documentos oficiais que definem fronteiras e relações
  entre subsistemas.

### Quantidades estimadas na base atual

> Observação: contagem baseada nos arquivos existentes em `core/` e nos
> documentos oficiais da raiz do projeto.

- Foundations: 18
- Runtimes stateful: 11
- Pipelines: 6
- Eventos: 10
- Snapshots: 8
- Módulos: 25
- Demos no baseline arquitetural original: 7 (o estado atual possui 96)

### Leitura curta do estado

- A plataforma já não é apenas conceitual: há runtimes vivos e fluxo integrado.
- A observability deixou de ser manual e passou a ser derivada de eventos.
- Ainda coexistem áreas de fundação, runtime e estratégia em diferentes níveis
  de maturidade.
- O ecossistema ficou suficientemente estável para consolidar, mas ainda não
  está maduro para expansão indiscriminada.

---

## 2. Arquitetura consolidada

### Hierarquia oficial da plataforma

```text
Foundation
↓
Runtime
↓
Pipeline
↓
Execution
↓
Feedback
↓
Learning
↓
Optimization
↓
Prediction
```

### Interpretação da hierarquia

- Foundation: contratos, modelos e definições estruturais.
- Runtime: entidades vivas em memória.
- Pipeline: encadeamento determinístico de etapas.
- Execution: trabalho coordenado, nunca acoplado ao planejador.
- Feedback: resultados e sinais pós-execução.
- Learning: consolidação de conhecimento e skills.
- Optimization: ajuste determinístico e estratégico.
- Prediction: camada futura, ainda não consolidada como capacidade central.

---

## 3. Módulos concluídos

| Nome | Status | Observações | Maturidade |
|---|---|---|---|
| `core/config` | Concluído | Fundação contract-first | Estável |
| `core/prompts` | Concluído | Contratos e carregamento conceitual | Estável |
| `core/events` | Concluído | EventBus interno e contratos de evento | Estável |
| `core/runtime` | Concluído | CompanyRuntime em memória | Estável |
| `core/employees` | Concluído | EmployeeRuntime vivo | Estável |
| `core/departments` | Concluído | DepartmentRuntime vivo | Estável |
| `core/tasks` | Concluído | TaskRuntime vivo | Estável |
| `core/workflows` | Concluído | WorkflowRuntime vivo | Estável |
| `core/results` | Concluído | ResultRuntime vivo | Estável |
| `core/knowledge` | Concluído | KnowledgeRuntime vivo | Estável |
| `core/skills` | Concluído | SkillRuntime vivo | Estável |
| `core/observability` | Concluído | Projector read-only baseado em eventos | Estável |
| `core/orchestrator` | Concluído | OrchestratorRuntime integrado | Estável |
| `core/organization` | Concluído | Fundação estrutural | Estável |
| `core/policies` | Concluído | Fundação estrutural | Estável |
| `core/company` | Concluído | Camada estrutural de empresa | Estável |
| `core/decision` | Concluído | Camada decisória estrutural | Estável |
| `core/execution` | Concluído | Núcleo de execução em construção | Experimental |
| `core/learning` | Concluído | Pipeline de aprendizado estrutural | Experimental |
| `core/strategy` | Concluído | Fundação estratégica | Experimental |
| `core/llm` | Concluído | Integração e runtime de IA | Estável |

---

## 4. Módulos parcialmente concluídos

### `core/execution`

O que já existe:
- runtime de execução;
- contrato de pipeline/planos;
- integração inicial com o fluxo da empresa.

O que ainda falta:
- consolidar fronteira clara entre execução e coordenação;
- formalizar o casamento com workflows e results em nível de produto;
- padronizar o vínculo com feedback e observability.

### `core/learning`

O que já existe:
- foundation e pipeline.

O que ainda falta:
- ligar o aprendizado de forma consistente a results, knowledge e skills;
- estabilizar a fronteira entre aprendizado e otimização.

### `core/strategy`

O que já existe:
- foundation e pipeline.

O que ainda falta:
- explicitar quando a estratégia influencia decisão e quando apenas observa;
- consolidar a integração com orchestrator e company runtime.

### `core/llm`

O que já existe:
- provider abstractions;
- adapters;
- runtime e request building.

O que ainda falta:
- alinhar o uso com a estratégia de AI Director e platform constraints;
- manter claramente separadas decisão, roteamento e execução de chamadas.

---

## 5. Módulos congelados

Os módulos abaixo não devem receber novas funcionalidades sem necessidade
arquitetural forte:

- `core/config`
- `core/prompts`
- `core/events`
- `core/organization`
- `core/policies`
- `core/company`
- `core/decision`
- `core/runtime`
- `core/observability`
- `core/orchestrator`
- `core/employees`
- `core/departments`
- `core/tasks`
- `core/workflows`
- `core/results`
- `core/knowledge`
- `core/skills`
- `core/llm`
- `core/container`

Motivo do congelamento:
- já cumprem seu papel estrutural;
- qualquer expansão deve preferir composição ou integração;
- novas abstrações só devem nascer se houver valor arquitetural real.

---

## 6. Pendências arquiteturais reais

Somente pendências necessárias:

1. Consolidar a projeção oficial de observability com cobertura completa e
   tipada para todos os eventos vivos.
2. Reduzir divergências entre documentos de roadmap antigos e o estado vivo
   atual.
3. Padronizar a semântica entre `Result`, `Knowledge` e `Skill` em nível de
   status e transição.
4. Finalizar a compatibilidade entre execução e aprendizado sem duplicar
   responsabilidades.
5. Eliminar duplicações documentais antigas que não representam mais a verdade
   da plataforma.
6. Formalizar a fronteira entre módulos de fundação congelada e runtimes vivos.

Sem sugerir novos módulos.

---

## 7. Ordem oficial das próximas fases

### Fase 1 — Consolidação da base viva

- estabilizar runtime comum;
- fechar a observability oficial;
- consolidar eventos e snapshots;
- reduzir inconsistências semânticas.

### Fase 2 — Fluxo organizacional completo

- tornar o caminho Task → Workflow → Result → Knowledge → Skill plenamente
  canônico;
- consolidar feedback e learning como consequência, não como atalho.

### Fase 3 — Integração estratégica

- reforçar orchestrator, policies e decision layers;
- conectar de forma consistente o que já existe, sem criar novos blocos
  desnecessários.

### Fase 4 — Execução de produção

- estabilizar execução, aprendizado e otimização;
- alinhar company runtime, observability e feedback com a operação completa.

### Fase 5 — Versão 1.0

- congelar a arquitetura principal;
- assegurar previsibilidade, rastreabilidade e extensibilidade controlada.

---

## 8. Checklist obrigatório antes de criar qualquer módulo novo

1. Já existe algo equivalente?
2. Pode ser extensão de outro módulo?
3. Resolve um problema arquitetural real?
4. Cria dependência circular?
5. É apenas conveniência?
6. Pode ser resolvido por composição?
7. Há um contrato existente que pode ser reutilizado?
8. O novo módulo altera responsabilidades já consolidadas?
9. O novo módulo aumenta complexidade sem valor estrutural?
10. O novo módulo viola o contract-first?

Se qualquer resposta indicar que o módulo é desnecessário, ele deve ser
rejeitado.

---

## 9. Dívidas técnicas

### Críticas

- Harmonizar definitivamente a semântica entre Result, Knowledge e Skill.
- Remover resquícios de atualizações manuais antigas onde ainda existirem em
  demonstrações legadas.
- Unificar a visão oficial da observability em torno do projector tipado.

### Importantes

- Revisar documentos de roadmap anteriores que ficaram defasados.
- Reduzir sobreposição entre foundation, runtime e pipeline em alguns módulos.
- Revisar o conjunto de demos para manter apenas as que representam fluxos
  canônicos.

### Baixa prioridade

- Melhorar o detalhamento de alguns snapshots.
- Reorganizar documentação auxiliar sem alterar o conteúdo arquitetural.
- Ajustar nomes menores onde ainda houver ambiguidade histórica.

---

## 10. Roadmap até versão 1.0

| Item | Status |
|---|---|
| Base contract-first | Concluído |
| EventBus interno | Concluído |
| Company Runtime | Concluído |
| Employee Runtime | Concluído |
| Department Runtime | Concluído |
| Task Runtime | Concluído |
| Workflow Runtime | Concluído |
| Result Runtime | Concluído |
| Knowledge Runtime | Concluído |
| Skill Runtime | Concluído |
| Observability Projector oficial | Em andamento |
| Consolidação da semântica Result/Knowledge/Skill | Em andamento |
| Fluxo organizacional completo | Em andamento |
| Estratégia e decisão consolidadas | Em andamento |
| Execução de produção | Pendente |
| Versão 1.0 | Pendente |

Sem incluir funcionalidades imaginárias.

---

## 11. Visão da plataforma final

Quando completa, a AI Company funcionará como uma empresa digital
determinística e rastreável:

- o CEO define direção e delegação;
- os Departments organizam a operação;
- os Employees executam trabalho;
- os LLMs entram apenas como capacidade substituível e controlada;
- os Pipelines estruturam a passagem do trabalho;
- a Execução produz outcomes;
- o Feedback fecha ciclos de correção;
- o Aprendizado transforma resultados em conhecimento;
- o Monitoramento observa o estado vivo da empresa;
- a Otimização ajusta capacidades e fluxos;
- tudo isso sem quebrar o desacoplamento entre domínio, runtime e projeção.

Não há novos módulos conceituais nesta visão — apenas a coordenação dos já
existentes.

---

## 12. Regras finais

- Não criar novo módulo sem validação arquitetural.
- Não expandir módulo congelado por conveniência.
- Não aceitar funcionalidades que existam apenas porque são “interessantes”.
- Não introduzir dependências circulares.
- Não alterar contratos sem necessidade.
- Não duplicar responsabilidades entre runtimes e projections.

Este documento deve ser tratado como a referência máxima para evolução da
plataforma.
