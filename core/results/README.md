# core/results

Fundação arquitetural do subsistema de **Results** da AI Content Factory.

## Responsabilidade

Representar os resultados oficiais produzidos pela AI Company, sem
armazenamento, sem persistência, sem métricas reais e sem comportamento
operacional.

## O que este módulo faz

- define modelos-base de result
- define contratos públicos de registry e validator
- documenta artefatos, métricas, resumo e outcome

## O que este módulo não faz

- não armazena resultados
- não implementa banco de dados
- não calcula métricas
- não integra engines
- não integra providers
- não integra employees, tasks ou workflows

## API pública

- `Result`
- `ResultType`
- `ResultStatus`
- `ResultContext`
- `ResultArtifact`
- `ResultMetric`
- `ResultSummary`
- `ResultMetadata`
- `ResultOutcome`
- `ResultRegistryContract`
- `ResultValidatorContract`

## Evolução futura

Quando houver necessidade de comportamento funcional, este subsistema poderá
servir como base para auditoria, aprendizado organizacional e geração de
conhecimento sem romper a superfície contratual atual.