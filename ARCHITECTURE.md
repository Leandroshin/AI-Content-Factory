# ARCHITECTURE

## 1. Visão Geral

Este documento é o índice mestre oficial da arquitetura da AI Company. Ele
centraliza todos os documentos arquiteturais, conceituais, de relacionamento,
de execução, de runtime, de observabilidade, do escritório 2.5D, de mensagens,
de roadmaps e de blueprints de engenharia produzidos até o momento.

## 2. Arquitetura Principal

- `ARCHITECTURE_RELATIONSHIPS.md` — contratos de relacionamento entre os
  subsistemas do core.
- `DECISION_ARCHITECTURE.md` — modelo conceitual de tomada de decisão da AI
  Company.
- `INTEGRATION_ARCHITECTURE.md` — arquitetura conceitual de integração entre os
  subsistemas existentes.
- `EXECUTION_FLOW_ARCHITECTURE.md` — fluxo conceitual completo de uma Task pela
  empresa.

## 3. Arquitetura de Boot e Runtime

- `COMPANY_BOOT_ARCHITECTURE.md` — sequência conceitual de inicialização da AI
  Company até o estado `READY`.
- `COMPANY_RUNTIME_ARCHITECTURE.md` — arquitetura conceitual da camada
  Company Runtime.

## 4. Arquitetura de Observabilidade

- `OBSERVABILITY_ARCHITECTURE.md` — camada conceitual de observabilidade da AI
  Company.

## 5. Arquitetura do Escritório 2.5D

- `OFFICE_BEHAVIOR_ARCHITECTURE.md` — comportamento visual do escritório 2.5D
  como projeção do estado real da empresa.

## 6. Arquitetura de Mensagens

- `MESSAGE_SYSTEM_ARCHITECTURE.md` — sistema interno de comunicação da AI
  Company.

## 7. Documentos de Ciclo de Vida e Fluxo Organizacional

- `EMPLOYEE_LIFECYCLE_ARCHITECTURE.md` — ciclo de vida conceitual de um
  Employee.
- `IMPLEMENTATION_ROADMAP_PHASE2.md` — plano oficial da Fase 2 para introdução
  incremental dos primeiros componentes vivos.

## 8. Blueprints de Engenharia

### 8.1 Core Runtime and Coordination

- `ENGINEERING_BLUEPRINT_COMPANY_RUNTIME.md` — blueprint técnico do Company
  Runtime.
- `ENGINEERING_BLUEPRINT_ORCHESTRATOR.md` — blueprint técnico do CEO /
  Orchestrator.
- `ENGINEERING_BLUEPRINT_OPERATIONS_DIRECTOR.md` — blueprint técnico do
  Operations Director.

### 8.2 AI and Platform Strategy

- `ENGINEERING_BLUEPRINT_AI_DIRECTOR.md` — blueprint técnico do AI Director.
- `ENGINEERING_BLUEPRINT_PLATFORM_DIRECTOR.md` — blueprint técnico do Platform
  Director.

### 8.3 Knowledge Strategy

- `ENGINEERING_BLUEPRINT_KNOWLEDGE_DIRECTOR.md` — blueprint técnico do
  Knowledge Director.

### 8.4 Employee Engineering

- `ENGINEERING_BLUEPRINT_EMPLOYEE.md` — blueprint técnico do Employee.

## 9. Subsistemas Fundacionais do Core

Os pacotes fundacionais do core foram estruturados em modo contract-first para
representar os conceitos centrais da AI Company.

- `core/config/`
- `core/events/`
- `core/knowledge/`
- `core/departments/`
- `core/employees/`
- `core/tasks/`
- `core/workflows/`
- `core/skills/`
- `core/organization/`
- `core/policies/`
- `core/results/`

## 10. Documentos Auxiliares

- `AI_DEVELOPMENT_MANUAL.md` — manual geral da AI Company.

## 11. Organização por Categoria

### Arquitetura Principal

- `ARCHITECTURE_RELATIONSHIPS.md`
- `DECISION_ARCHITECTURE.md`
- `INTEGRATION_ARCHITECTURE.md`
- `EXECUTION_FLOW_ARCHITECTURE.md`

### Arquitetura de Boot e Runtime

- `COMPANY_BOOT_ARCHITECTURE.md`
- `COMPANY_RUNTIME_ARCHITECTURE.md`

### Arquitetura de Observabilidade

- `OBSERVABILITY_ARCHITECTURE.md`

### Arquitetura do Escritório 2.5D

- `OFFICE_BEHAVIOR_ARCHITECTURE.md`

### Arquitetura de Mensagens

- `MESSAGE_SYSTEM_ARCHITECTURE.md`

### Roadmaps

- `IMPLEMENTATION_ROADMAP_PHASE2.md`

### Blueprints de Engenharia

- `ENGINEERING_BLUEPRINT_EMPLOYEE.md`
- `ENGINEERING_BLUEPRINT_COMPANY_RUNTIME.md`
- `ENGINEERING_BLUEPRINT_ORCHESTRATOR.md`
- `ENGINEERING_BLUEPRINT_AI_DIRECTOR.md`
- `ENGINEERING_BLUEPRINT_PLATFORM_DIRECTOR.md`
- `ENGINEERING_BLUEPRINT_KNOWLEDGE_DIRECTOR.md`
- `ENGINEERING_BLUEPRINT_OPERATIONS_DIRECTOR.md`

## 12. Contagem de Documentos

- Total de documentos arquiteturais na raiz: 14
- Total de blueprints de engenharia: 7
- Total de documentos conceituais principais: 7
- Total de documentos de engenharia/roadmap: 8

## 13. Critérios de Integridade

### Referências garantidas

Todos os documentos arquiteturais da raiz estão listados acima e devem ser
mantidos sincronizados com futuras adições ou remoções.

### Referências duplicadas

Alguns documentos aparecem em mais de uma categoria por intenção, para facilitar
navegação temática. Isso não representa duplicação indevida; representa um
índice multidimensional.

### Documentos órfãos

Não há documentos arquiteturais oficiais esperados fora deste índice mestre.

## 14. Regra do Índice Mestre

Este arquivo é a referência oficial para a documentação arquitetural da AI
Company. Qualquer novo documento arquitetural raiz deve ser adicionado aqui.
