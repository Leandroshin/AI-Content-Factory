# Core Exceptions

## Responsabilidade

Este pacote reúne a hierarquia oficial de exceções do projeto.

## Escopo desta missão

- Definir classes-base para erros do sistema
- Organizar exceções por responsabilidade conceitual
- Servir como contrato comum para as demais camadas

## O que este módulo não faz

- Não implementa tratamento avançado de erro
- Não define política de retry
- Não contém lógica de negócio
- Não depende de engines

## Hierarquia oficial

- `AIContentFactoryError`
- `ConfigurationError`
- `EngineError`
- `ValidationError`
- `ProviderError`
- `PipelineError`
- `ProjectError`
- `AssetError`

## Observação arquitetural

As exceções aqui definidas são contratos-base para uso futuro por módulos e
camadas superiores. Elas não carregam comportamento adicional.