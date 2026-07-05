# core/tasks

Fundação arquitetural do subsistema de **Tasks** da AI Content Factory.

## Responsabilidade

Representar uma Task apenas como uma unidade de trabalho contratual, reutilizável
por qualquer produto da AI Company.

## O que este módulo faz

- define modelos-base de Task
- define contratos públicos de registry, factory, lifecycle e validator
- documenta a taxonomia de prioridade e estado

## O que este módulo não faz

- não executa filas
- não agenda tarefas
- não cria workers
- não cria concorrência
- não integra Employees
- não integra Engines
- não integra Providers
- não implementa comportamento funcional

## API pública

- `Task`
- `TaskId`
- `TaskStatus`
- `TaskPriority`
- `TaskType`
- `TaskContext`
- `TaskMetadata`
- `TaskResult`
- `TaskDependency`
- `TaskRegistryContract`
- `TaskValidatorContract`
- `TaskFactoryContract`
- `TaskLifecycleContract`

## Evolução futura

Quando a missão exigir comportamento funcional, este subsistema poderá receber
implementações concretas para validação, persistência, priorização operacional e
integração com orquestração.