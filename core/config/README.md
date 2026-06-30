# Core Configuration

## Responsabilidade

Este pacote define a fundação arquitetural do sistema de configuração da
AI Content Factory.

## Escopo desta missão

- Definir contratos e modelos-base de configuração
- Manter o subsistema desacoplado de engines e providers
- Preparar uma API pública estável para evolução futura

## O que este módulo não faz

- Não carrega arquivos reais
- Não lê `.env`
- Não interpreta YAML, JSON ou TOML
- Não lê variáveis de ambiente
- Não cria cache
- Não cria hot reload
- Não cria providers
- Não integra com engines
- Não implementa lógica de configuração

## Interface pública

- `ConfigModel`
- `AppConfig`
- `EnvironmentConfig`
- `ProjectConfig`
- `ConfigLoader`
- `ConfigRegistry`
- `ConfigValidator`
- `ConfigurationError`
- `ConfigurationNotFoundError`
- `ConfigurationValidationError`

## Evolução futura

Em missões futuras, este módulo poderá receber fontes reais de configuração,
resolução de perfis e validações específicas, sem quebrar a API pública
definida nesta fundação.