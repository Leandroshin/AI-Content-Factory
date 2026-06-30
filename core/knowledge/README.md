# Core Knowledge

## Responsabilidade

Este pacote define a fundação arquitetural do Knowledge System da AI Content
Factory.

## Escopo desta missão

- Definir contratos e modelos-base de conhecimento compartilhado
- Preparar a superfície pública para futura evolução
- Manter o subsistema completamente desacoplado de armazenamento, IA e busca

## O que este módulo não faz

- Não implementa banco de dados
- Não implementa memória vetorial
- Não implementa embeddings
- Não implementa IA
- Não implementa cache
- Não implementa RAG
- Não implementa busca semântica
- Não implementa armazenamento

## Interface pública

- `KnowledgeEntry`
- `KnowledgeCategory`
- `KnowledgeSource`
- `KnowledgeContext`
- `KnowledgeMetadata`
- `KnowledgeResult`
- `KnowledgeStatus`
- `KnowledgeRegistry`
- `KnowledgeRepository`
- `KnowledgeValidator`

## Evolução futura

Em missões futuras, este pacote poderá receber implementações concretas de
registro, repositório e validação, mantendo os contratos definidos nesta base.
