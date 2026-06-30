# Script Engine

## Responsabilidade

Este pacote define a fundação oficial da primeira engine concreta do sistema.

## Escopo desta missão

- Criar contratos e modelos-base da Script Engine
- Separar internamente builders, validators, parser, factory e interfaces
- Preparar a fundação sem gerar texto real
- Documentar a intenção do subsistema

## O que este módulo não faz

- Não chama IA
- Não usa OpenAI, Gemini ou Claude
- Não gera texto
- Não implementa prompts reais
- Não cria integração externa

## Interface pública

- `ScriptEngine`
- `ScriptEnginePublicInterface`
- `ScriptRequest`
- `ScriptResponse`
- `PromptTemplate`
- `ScriptGenerationMode`

## Observação arquitetural

A Script Engine deve evoluir a partir destes contratos, sempre dependente de
`engines/base` e sem acoplamento com outras engines.
