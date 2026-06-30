# Core Events

## Responsabilidade

Este pacote define a fundação arquitetural do subsistema de Domain Events da
AI Content Factory.

## Escopo desta missão

- Definir contratos e modelos-base de eventos
- Preparar a superfície pública para comunicação futura entre módulos
- Manter o subsistema desacoplado de engines e providers

## O que este módulo não faz

- Não cria Event Bus
- Não cria publish()
- Não cria subscribe()
- Não cria listeners reais
- Não cria filas
- Não usa threads
- Não usa async
- Não usa providers externos

## Interface pública

- `BaseEvent`
- `EventMetadata`
- `EventContext`
- `EventResult`
- `EventStatus`
- `EventPriority`
- `EventType`
- `EventRegistry`
- `EventDispatcher`
- `EventSubscriber`
- `EventValidator`

## Evolução futura

Em missões futuras, este pacote poderá evoluir para suportar roteamento
explicitamente configurado, observabilidade e mecanismos de integração, sem
romper o contrato base definido aqui.
