# Core

## Responsabilidade

Infraestrutura central do projeto. Fornece os serviços fundamentais que **todas** as engines utilizam.

## O Que Este Módulo NÃO Faz

- Não contém lógica de negócio (essa é responsabilidade das engines)
- Não acessa serviços externos diretamente (essa é responsabilidade dos adapters/providers)
- Não depende de nenhuma engine (a dependência flui das engines para o core, nunca o contrário)

## Submódulos Planejados

| Submódulo | Responsabilidade | Status |
|-----------|-----------------|--------|
| `config/` | Sistema de configuração (YAML + env vars + validação) | 🔲 Missão 001 |
| `logging/` | Logging estruturado com structlog | 🔲 Planejado |
| `exceptions/` | Exceções base do projeto | 🔲 Planejado |
| `models/` | Modelos de dados compartilhados entre engines | 🔲 Planejado |

## Princípio de Dependência

```
engines/ → depende de → core/
core/    → NÃO depende de → engines/
```

Qualquer violação deste princípio é um erro arquitetural e deve ser corrigida imediatamente.

## Decisões Arquiteturais

- **Pydantic v2** para validação de configuração e modelos de dados
- **structlog** para logging estruturado em JSON
- **Configuração hierárquica**: defaults → config global → config de projeto → env vars → CLI args
