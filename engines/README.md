# Engines

## Visão Geral

Este diretório contém todos os **módulos de domínio** (engines) que compõem o pipeline de produção de conteúdo da AI Content Factory.

Cada engine é um pacote Python independente, responsável por uma etapa específica do pipeline.

## Arquitetura

```
Tema → [Trend] → [Research] → [Script] → [Narration] → [Video] → [Subtitle] → [Publishing] → [Analytics]
```

## Engines Disponíveis

| Engine | Diretório | Responsabilidade | Prioridade |
|--------|-----------|-----------------|------------|
| Script Engine | `script/` | Gerar roteiros originais via LLM | 🔴 P0 |
| Narration Engine | `narration/` | Converter roteiro em áudio narrado | 🔴 P0 |
| Video Engine | `video/` | Montar vídeo final com áudio e visuais | 🔴 P0 |
| Subtitle Engine | `subtitle/` | Gerar legendas sincronizadas | 🔴 P0 |
| Trend Engine | `trend/` | Detectar tendências e temas relevantes | 🟡 P1 |
| Research Engine | `research/` | Pesquisar assuntos em profundidade | 🟡 P1 |
| Publishing Engine | `publishing/` | Publicar em múltiplas plataformas | 🟡 P1 |
| Thumbnail Engine | `thumbnail/` | Gerar thumbnails para vídeos | 🟢 P2 |
| Analytics Engine | `analytics/` | Coletar e analisar métricas | 🟢 P2 |

## Estrutura Padrão de uma Engine

Conforme definido no [AI Development Manual](../AI_DEVELOPMENT_MANUAL.md), toda engine segue esta estrutura:

```
engine_name/
├── __init__.py          # Exportações públicas
├── engine.py            # Classe principal
├── models.py            # Dataclasses/Pydantic models
├── exceptions.py        # Exceções específicas
├── providers/           # Adapter implementations
│   ├── __init__.py
│   └── provider_name.py
├── README.md            # Documentação do módulo
└── tests/
    ├── __init__.py
    └── test_engine.py
```

## Regras

1. **Cada engine é independente** — nenhuma engine importa diretamente de outra
2. **Comunicação por interfaces** — engines se comunicam através de contratos definidos em `core/`
3. **Adapter pattern obrigatório** — todo serviço externo é acessado via adapter
4. **Testes acompanham a implementação** — toda engine tem seus testes no subdiretório `tests/`
