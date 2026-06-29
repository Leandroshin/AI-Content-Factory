# AI Content Factory

**Plataforma modular de criação, automação, publicação e análise de conteúdo utilizando Inteligência Artificial.**

---

## Visão Geral

A AI Content Factory é uma plataforma que transforma temas em conteúdo publicado de forma automatizada. O sistema é **agnóstico a nicho** — o assunto é configuração, a plataforma permanece a mesma.

```
Tema → Pesquisa → Roteiro → Narração → Vídeo → Legendas → Publicação → Analytics
```

## Status do Projeto

| Fase | Status |
|------|--------|
| Arquitetura | ✅ Concluída (Missão 000) |
| Manual Operacional | ✅ Concluído (Missão 000.5) |
| Estrutura do Repositório | ✅ Concluída (Missão 000) |
| Core Configuration | 🔲 Próxima (Missão 001) |
| MVP | 🔲 Planejado |

## Arquitetura

O projeto segue uma arquitetura modular com 5 camadas:

| Camada | Responsabilidade | Diretório |
|--------|-----------------|-----------|
| **Apresentação** | Interface humana (CLI, Dashboard, API) | `api/`, `dashboard/` |
| **Orquestração** | Coordenação do pipeline | `core/` |
| **Domínio** | Lógica de negócio | `engines/` |
| **Integração** | Serviços externos | `engines/*/providers/` |
| **Infraestrutura** | Persistência, logs, config | `core/`, `config/`, `shared/` |

## Estrutura do Repositório

```
ai-content-factory/
├── engines/                # Módulos de domínio (pipeline de produção)
│   ├── trend/              # Detecção de tendências
│   ├── research/           # Pesquisa de assuntos
│   ├── script/             # Geração de roteiros
│   ├── narration/          # Conversão texto → áudio (TTS)
│   ├── video/              # Montagem de vídeo
│   ├── subtitle/           # Geração de legendas
│   ├── thumbnail/          # Geração de thumbnails
│   ├── publishing/         # Publicação em plataformas
│   └── analytics/          # Coleta de métricas
├── core/                   # Infraestrutura central
│   ├── config/             # Sistema de configuração
│   ├── logging/            # Logging estruturado
│   ├── exceptions/         # Exceções base
│   └── models/             # Modelos compartilhados
├── shared/                 # Utilitários compartilhados
├── config/                 # Arquivos de configuração global
├── projects/               # Configurações por projeto/nicho
├── docs/                   # Documentação
│   ├── adrs/               # Architecture Decision Records
│   └── rfcs/               # Requests for Comments
├── tests/                  # Testes (espelha estrutura do src)
├── assets/                 # Mídia e recursos estáticos
├── output/                 # Vídeos e artefatos gerados
└── temp/                   # Arquivos temporários de processamento
```

## Módulos (Engines)

Cada engine é um módulo independente responsável por uma etapa do pipeline:

| Engine | Responsabilidade | Prioridade |
|--------|-----------------|------------|
| `script` | Gerar roteiros originais via LLM | 🔴 P0 — MVP |
| `narration` | Converter texto em áudio narrado | 🔴 P0 — MVP |
| `video` | Montar vídeo final | 🔴 P0 — MVP |
| `subtitle` | Gerar legendas sincronizadas | 🔴 P0 — MVP |
| `trend` | Detectar tendências e temas relevantes | 🟡 P1 |
| `research` | Pesquisar assuntos em profundidade | 🟡 P1 |
| `publishing` | Publicar em múltiplas plataformas | 🟡 P1 |
| `thumbnail` | Gerar thumbnails | 🟢 P2 |
| `analytics` | Coletar e analisar métricas | 🟢 P2 |

## Quick Start

### Pré-requisitos

- Python 3.12+
- FFmpeg instalado e no PATH

### Instalação

```bash
# Clonar repositório
git clone https://github.com/seu-usuario/ai-content-factory.git
cd ai-content-factory

# Criar ambiente virtual
python -m venv .venv
source .venv/bin/activate  # Linux/Mac
.venv\Scripts\activate     # Windows

# Instalar dependências
pip install -r requirements.txt

# Configurar variáveis de ambiente
cp .env.example .env
# Editar .env com suas API keys
```

### Uso (após implementação do MVP)

```bash
python main.py --config projects/gta6.yaml --topic "5 segredos do GTA 6"
```

## Documentação

| Documento | Descrição |
|-----------|-----------|
| [AI Development Manual](AI_DEVELOPMENT_MANUAL.md) | Manual operacional — leitura obrigatória |
| [docs/adrs/](docs/adrs/) | Decisões arquiteturais |
| [docs/rfcs/](docs/rfcs/) | Propostas de mudança |
| [docs/IDEAS.md](docs/IDEAS.md) | Banco de ideias futuras |

## Princípios

1. **Qualidade antes de escala** — Um vídeo excelente vale mais que trinta medíocres
2. **Tema é configuração** — O software nunca depende de um assunto específico
3. **Todo módulo é uma ilha** — Componentes desacoplados, comunicação por interfaces
4. **Toda tecnologia é substituível** — Adapter pattern obrigatório para serviços externos
5. **Automatize apenas o validado** — Primeiro funcionar, depois automatizar, depois escalar

## Licença

Projeto privado. Todos os direitos reservados.
