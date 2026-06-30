# Core Logging

## Responsabilidade

Este módulo define a arquitetura base do sistema de logging da AI Content Factory.

## Escopo desta missão

- Definir contratos públicos de logging
- Preparar modelos de contexto e entradas estruturadas
- Preparar abstrações para formatters e handlers
- Documentar a intenção do subsistema

## O que este módulo não faz

- Não implementa logging funcional completo
- Não escreve em console, arquivo ou rotação real
- Não cria integração com dashboard
- Não depende de nenhuma engine

## Interface pública

- `LogLevel`
- `LogFormat`
- `LoggerContext`
- `CorrelationContext`
- `LogEntry`
- `LogFormatter`
- `TextLogFormatter`
- `JsonLogFormatter`
- `BaseLogHandler`
- `ConsoleLogHandler`
- `FileLogHandler`
- `LogManager`
- `get_logger`

## Capacidades futuras previstas

Este pacote foi preparado para suportar, em missões futuras:

- Console Logging
- File Logging
- Rotating Logs
- JSON Logs
- Engine Identification
- Project Identification
- Correlation IDs
- Log Levels
- Custom Formatters
- Future Dashboard Integration

## Observação arquitetural

Esta missão cria apenas a fundação estrutural. A implementação real de logging
fica para uma etapa posterior, sem alterar o contrato definido aqui.