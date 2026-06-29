# Shared

## Responsabilidade

Utilitários genéricos compartilhados entre múltiplos módulos. Funções que são úteis em mais de um engine mas que **não contêm lógica de negócio**.

## O Que Este Módulo NÃO Faz

- Não contém lógica de negócio
- Não acessa serviços externos
- Não depende de nenhuma engine ou do core (é o nível mais baixo de abstração)

## Exemplos de Utilitários Futuros

| Utilitário | Descrição |
|------------|-----------|
| `file_utils.py` | Operações de arquivos (criar diretórios, mover, hash de arquivos) |
| `retry.py` | Decorator de retry com backoff exponencial |
| `timing.py` | Context manager para medir tempo de execução |
| `hashing.py` | Funções de hash para cache |
| `validators.py` | Validações genéricas reutilizáveis |

## Regras

1. Nenhuma função neste módulo pode ter dependência em engines ou core
2. Tudo aqui deve ser **puro** — sem side effects inesperados
3. Cada utilitário deve ser testável isoladamente
