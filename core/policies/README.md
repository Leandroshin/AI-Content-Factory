# core/policies

Fundação arquitetural do subsistema de **Policies** da AI Content Factory.

## Responsabilidade

Representar as políticas organizacionais da AI Company como contratos e modelos
estruturais, sem avaliação, sem autorização e sem comportamento operacional.

## O que este módulo faz

- define modelos-base de policy
- define contratos públicos de registry e validator
- documenta tipos, escopos, condições e restrições

## O que este módulo não faz

- não executa políticas
- não avalia condições
- não realiza autorização
- não integra engines
- não integra providers
- não integra employees, departments, tasks ou workflows

## API pública

- `Policy`
- `PolicyType`
- `PolicyScope`
- `PolicyContext`
- `PolicyCondition`
- `PolicyConstraint`
- `PolicyMetadata`
- `PolicyStatus`
- `PolicyResult`
- `PolicyRegistryContract`
- `PolicyValidatorContract`

## Evolução futura

Quando houver necessidade de comportamento funcional, este subsistema poderá
receber mecanismos especializados de governança e compliance sem romper a
superfície contratual atual.