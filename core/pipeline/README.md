# Core Pipeline

## Responsabilidade

Este pacote define a arquitetura base do pipeline da AI Content Factory.

## Escopo desta missão

- Criar contratos e modelos-base do pipeline
- Preparar a fundação para execução futura
- Documentar a intenção do subsistema

## O que este módulo não faz

- Não executa etapas reais
- Não chama engines
- Não cria filas
- Não implementa paralelismo
- Não implementa retry
- Não depende de nenhuma engine

## Interface pública

- `Pipeline`
- `PipelineContext`
- `PipelineState`
- `PipelineResult`
- `PipelineStep`
- `PipelineExecutor`

## Observação arquitetural

O pipeline é apenas o contrato estrutural nesta missão. A coordenação real de
etapas será introduzida apenas em missões futuras, sem violar o isolamento entre
camadas.
