# Engines Base

## Responsabilidade

Este pacote reúne os contratos compartilhados por todas as engines do projeto.

## Escopo desta missão

- Definir a fundação comum das engines
- Criar modelos e contratos-base
- Preparar a extensão futura sem acoplamento entre engines

## O que este módulo não faz

- Não implementa comportamento funcional
- Não cria providers
- Não registra engines concretas
- Não coordena execução real
- Não depende de engines específicas

## Interface pública

- `BaseEngine`
- `EngineContext`
- `EngineRequest`
- `EngineResponse`
- `EngineStatus`
- `EngineCapability`

## Observação arquitetural

As engines concretas devem depender deste pacote para compartilhar contratos,
sem assumir dependências horizontais entre módulos de domínio.