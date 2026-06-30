# Core Prompts

## Responsabilidade

Este pacote define a fundação arquitetural para o gerenciamento de prompts da
AI Content Factory.

## Escopo desta missão

- Definir contratos e modelos-base de prompts
- Preparar a superfície pública para futura evolução
- Manter o subsistema totalmente desacoplado de engines e providers

## O que este módulo não faz

- Não carrega arquivos reais
- Não renderiza prompts
- Não usa IA
- Não integra com OpenAI, Gemini, Claude ou qualquer provider
- Não cria cache
- Não cria registry funcional
- Não cria templates reais
- Não cria versionamento funcional

## Interface pública

- `PromptTemplate`
- `PromptContext`
- `PromptVariables`
- `PromptMetadata`
- `PromptVersion`
- `PromptRegistry`
- `PromptLoader`
- `PromptRenderer`
- `PromptValidator`
- `BasePromptRegistry`
- `BasePromptLoader`
- `BasePromptRenderer`
- `BasePromptValidator`

## Evolução futura

Em missões futuras, o módulo poderá evoluir para carregar definições a partir
de fontes de configuração e aplicar validações mais específicas.
