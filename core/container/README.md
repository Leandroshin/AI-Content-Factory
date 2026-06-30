# Core Container

## Responsabilidade

Este pacote define a fundação do container de dependências da AI Content Factory.

## Escopo desta missão

- Criar contratos e placeholders do container
- Preparar a fundação para registro e resolução futura
- Documentar a intenção do subsistema

## O que este módulo não faz

- Não resolve dependências de forma real
- Não instancia objetos
- Não registra engines
- Não acopla a execução do sistema a serviços concretos
- Não depende de nenhuma engine

## Interface pública

- `ServiceContainer`
- `ServiceRegistry`
- `ServiceProvider`
- `DependencyResolver`
- `Lifetime`
- `ContainerProvider`

## Observação arquitetural

Esta missão fornece apenas contratos estruturais. A implementação funcional do
container será adicionada futuramente sem quebrar o isolamento das camadas.
