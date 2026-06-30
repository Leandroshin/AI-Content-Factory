# Core Departments

## Responsabilidade

Este pacote define a fundação arquitetural do Department System da AI Content
Factory.

## Escopo desta missão

- Definir contratos e modelos-base de departamentos
- Preparar a superfície pública para futura evolução
- Manter o subsistema desacoplado de execução, tarefas e comunicação entre departamentos

## O que este módulo não faz

- Não implementa departamentos concretos
- Não cria funcionários
- Não cria agentes
- Não cria lógica de execução
- Não cria comunicação entre departamentos
- Não implementa gerenciamento de tarefas

## Interface pública

- `Department`
- `DepartmentType`
- `DepartmentMetadata`
- `DepartmentContext`
- `DepartmentStatus`
- `DepartmentCapability`
- `DepartmentResult`
- `DepartmentRegistry`
- `DepartmentValidator`

## Evolução futura

Em missões futuras, este pacote poderá ganhar implementações concretas de
registro e validação sem quebrar a API pública definida nesta base.
