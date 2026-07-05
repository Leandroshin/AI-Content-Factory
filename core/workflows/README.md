# core/workflows

Fundação arquitetural do subsistema de **Workflows** da AI Content Factory.

## Responsabilidade

Modelar a relação entre `Task`, `Workflow`, `Department`, `Engine` e `Result`
como um caminho lógico, sem execução funcional.

## O que este módulo faz

- define modelos-base de workflow
- define contratos públicos de registry e validator
- documenta a posição do workflow como camada de relação entre subsistemas

## O que este módulo não faz

- não executa tarefas
- não agenda fluxo
- não cria filas
- não cria workers
- não chama departments
- não chama engines
- não integra providers
- não implementa automação

## API pública

- `Workflow`
- `WorkflowContext`
- `WorkflowStage`
- `WorkflowStatus`
- `WorkflowResult`
- `WorkflowStep`
- `WorkflowRegistryContract`
- `WorkflowValidatorContract`

## Evolução futura

Quando houver necessidade de comportamento operacional, este subsistema poderá
receber resolvers, planners, executors e integrações de observabilidade sem
romper o contrato atual.