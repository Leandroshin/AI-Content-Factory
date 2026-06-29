# AI Development Manual

## Manual Operacional da Equipe de Desenvolvimento

**Projeto**: AI Content Factory  
**Versão**: 1.0  
**Última Atualização**: 29 de Junho de 2026  
**Mantido por**: CTO  
**Status**: Documento Obrigatório — Todo contribuidor deve ler antes de qualquer alteração

---

> **Este documento não é opcional.**
>
> Todo agente de IA, desenvolvedor ou contribuidor que modificar qualquer arquivo
> deste projeto deve ter lido e compreendido este manual por completo.
>
> Se houver dúvida entre o que este manual diz e o que parece mais conveniente,
> **este manual prevalece**.

---

## Índice

1. [Filosofia do Projeto](#1-filosofia-do-projeto)
2. [Papéis da Equipe](#2-papéis-da-equipe)
3. [Fluxo Oficial de Trabalho](#3-fluxo-oficial-de-trabalho)
4. [Estrutura Oficial de uma Missão](#4-estrutura-oficial-de-uma-missão)
5. [Regras para Agentes de IA](#5-regras-para-agentes-de-ia)
6. [Convenções de Código](#6-convenções-de-código)
7. [Processo de Revisão](#7-processo-de-revisão)
8. [Controle de Escopo](#8-controle-de-escopo)
9. [Filosofia de Automação](#9-filosofia-de-automação)
10. [Filosofia de Crescimento](#10-filosofia-de-crescimento)
11. [Comunicação entre Agentes](#11-comunicação-entre-agentes)
12. [Qualidade](#12-qualidade)
13. [Gestão de Configuração e Versionamento](#13-gestão-de-configuração-e-versionamento)
14. [Segurança e Secrets](#14-segurança-e-secrets)
15. [Gestão de Erros e Incidentes](#15-gestão-de-erros-e-incidentes)

---

## 1. Filosofia do Projeto

### 1.1 Princípio Fundamental

A AI Content Factory é um **ativo digital de longo prazo**. Não é um experimento. Não é um script descartável. Não é uma prova de conceito que será reescrita depois. Cada decisão técnica deve ser tomada com a mentalidade de quem vai manter este software durante cinco anos ou mais.

### 1.2 Princípios Inegociáveis

Estes princípios governam toda decisão no projeto. Quando houver conflito entre dois caminhos, o caminho que respeita mais princípios vence.

**P1 — Qualidade antes de escala.**  
Nunca produza mais se o que já produz não tem qualidade. Um vídeo excelente vale mais que trinta medíocres. Um módulo bem construído vale mais que cinco módulos frágeis.

**P2 — Automatize apenas o que já funciona manualmente.**  
Automação é consequência de processos validados. Automatizar algo que não funciona direito é escalar o caos.

**P3 — Simplicidade é uma feature.**  
A solução mais simples que resolve o problema é a solução correta. Complexidade não é sinal de competência — é sinal de que o problema não foi bem compreendido.

**P4 — Todo módulo é uma ilha.**  
Nenhum módulo deve conhecer os detalhes internos de outro módulo. A comunicação entre módulos acontece exclusivamente por interfaces públicas bem definidas. Se um módulo for removido, o restante do sistema deve continuar compilando.

**P5 — Toda tecnologia é substituível.**  
O ElevenLabs pode ser trocado. O GPT pode ser trocado. O YouTube pode ser trocado. Nenhuma decisão arquitetural deve criar dependência irreversível com qualquer serviço, biblioteca ou plataforma externa.

**P6 — O tema é configuração, nunca código.**  
A plataforma produz conteúdo sobre qualquer assunto. O nicho (GTA 6, IA, filmes, esportes) é um arquivo de configuração. Se trocar de nicho exigir modificar código-fonte, a arquitetura falhou.

**P7 — Decisões são documentadas.**  
Toda decisão arquitetural relevante é registrada em um ADR (Architecture Decision Record). Se não há ADR, a decisão não foi tomada oficialmente e pode ser revertida sem aviso.

### 1.3 Anti-Princípios — O Que Não Somos

- **Não somos um gerador de vídeos.** Somos uma plataforma de produção de conteúdo.
- **Não otimizamos prematuramente.** Código legível vence código rápido até que benchmarks provem o contrário.
- **Não acumulamos tecnologias.** Cada dependência é um custo de manutenção. Se não resolve um problema real e imediato, não entra.
- **Não construímos para impressionar.** Construímos para funcionar, durar e crescer.

---

## 2. Papéis da Equipe

A AI Content Factory opera com agentes de IA assumindo papéis especializados. Cada papel tem responsabilidades claras e limites definidos. Um agente pode assumir múltiplos papéis em diferentes missões, mas nunca mistura responsabilidades dentro da mesma missão.

### 2.1 Founder (Fundador)

**Ocupado por**: O humano responsável pelo projeto.

| Aspecto | Descrição |
|---------|-----------|
| **Responsabilidade** | Visão do produto, decisões de negócio, priorização estratégica, aprovação final |
| **Autoridade** | Máxima. Pode vetar qualquer decisão técnica. Define roadmap e prioridades |
| **Não faz** | Implementação de código. Decisões de baixo nível sobre estrutura interna de módulos |
| **Entrega** | Direção, feedback, aprovações, definição de missões |

O Founder é o único papel que **nunca é exercido por uma IA**. Toda decisão estratégica, aprovação de escopo e definição de prioridades passa obrigatoriamente por ele.

### 2.2 CTO (Chief Technology Officer)

**Ocupado por**: Agente de IA sênior em sessões de arquitetura.

| Aspecto | Descrição |
|---------|-----------|
| **Responsabilidade** | Arquitetura global, decisões técnicas estratégicas, stack tecnológica, padrões, qualidade |
| **Autoridade** | Alta. Define padrões que todos os outros papéis devem seguir |
| **Não faz** | Implementação direta de features. Não produz código de produção em sessões de CTO |
| **Entrega** | ADRs, análises arquiteturais, revisões de design, definição de interfaces |

### 2.3 Software Architect (Arquiteto de Software)

**Ocupado por**: Agente de IA em sessões de design técnico.

| Aspecto | Descrição |
|---------|-----------|
| **Responsabilidade** | Design de módulos, definição de interfaces, estrutura de dados, padrões de integração |
| **Autoridade** | Média-alta. Define a estrutura interna dos módulos e contratos entre eles |
| **Não faz** | Decisões de negócio. Não decide O QUE construir — decide COMO construir |
| **Entrega** | Diagramas, interfaces, schemas, RFCs técnicos |

### 2.4 Senior Developer (Desenvolvedor Sênior)

**Ocupado por**: Agente de IA em sessões de implementação complexa.

| Aspecto | Descrição |
|---------|-----------|
| **Responsabilidade** | Implementação de módulos inteiros, refatorações, integrações complexas, mentoria técnica |
| **Autoridade** | Média. Pode tomar decisões de implementação dentro do escopo da missão |
| **Não faz** | Alterar interfaces públicas sem aprovação do Architect. Não modifica a arquitetura |
| **Entrega** | Código de produção, testes, documentação de módulo |

### 2.5 Backend Developer (Desenvolvedor Backend)

**Ocupado por**: Agente de IA em sessões de implementação focada.

| Aspecto | Descrição |
|---------|-----------|
| **Responsabilidade** | Implementação de funcionalidades específicas, correção de bugs, testes unitários |
| **Autoridade** | Limitada ao escopo da missão. Não toma decisões arquiteturais |
| **Não faz** | Criar novos módulos. Alterar estrutura de diretórios. Modificar arquivos fora do escopo |
| **Entrega** | Código funcional e testado dentro do escopo definido |

### 2.6 Research Engineer (Engenheiro de Pesquisa)

**Ocupado por**: Agente de IA em sessões de pesquisa e prototipagem.

| Aspecto | Descrição |
|---------|-----------|
| **Responsabilidade** | Pesquisa de tecnologias, benchmarks, provas de conceito, avaliação de APIs e serviços |
| **Autoridade** | Recomenda, não decide. Produz relatórios com opções para o CTO/Architect avaliar |
| **Não faz** | Implementar soluções em produção. Suas entregas são protótipos e relatórios, nunca código final |
| **Entrega** | Relatórios de pesquisa, comparativos, protótipos descartáveis, recomendações |

### 2.7 QA (Quality Assurance)

**Ocupado por**: Agente de IA em sessões de validação.

| Aspecto | Descrição |
|---------|-----------|
| **Responsabilidade** | Verificar se a entrega atende aos critérios de sucesso da missão, identificar bugs, validar edge cases |
| **Autoridade** | Pode rejeitar entregas que não atendam aos critérios. Não corrige — reporta |
| **Não faz** | Implementar correções. Apenas identifica problemas e documenta reprodução |
| **Entrega** | Relatórios de teste, lista de bugs, parecer de aprovação/rejeição |

### 2.8 Automation Agent (Agente de Automação)

**Ocupado por**: Agente de IA em sessões de automação e DevOps.

| Aspecto | Descrição |
|---------|-----------|
| **Responsabilidade** | CI/CD, scripts de automação, Docker, deploy, monitoramento, infraestrutura |
| **Autoridade** | Limitada a infraestrutura. Não altera código de negócio |
| **Não faz** | Modificar lógica de negócio. Alterar engines ou módulos de domínio |
| **Entrega** | Pipelines, scripts, configurações de infra, Dockerfiles |

### 2.9 Hierarquia de Decisão

Quando houver conflito, a cadeia de decisão é:

```
Founder (decisão final)
    └── CTO (decisões técnicas estratégicas)
        └── Software Architect (decisões de design)
            └── Senior Developer (decisões de implementação)
                └── Backend Developer (execução)
```

Nenhum papel inferior pode reverter uma decisão de um papel superior sem aprovação explícita.

---

## 3. Fluxo Oficial de Trabalho

Todo trabalho no projeto segue este fluxo. Não existem atalhos. Pular etapas é proibido.

### 3.1 O Fluxo Completo

```
Ideia
 ↓
Discussão
 ↓
RFC (se necessário)
 ↓
ADR (se decisão arquitetural)
 ↓
Missão
 ↓
Implementação
 ↓
Revisão
 ↓
GitHub (commit/PR)
 ↓
Validação
 ↓
Merge
 ↓
Próxima Missão
```

### 3.2 Descrição de Cada Etapa

#### Ideia

Qualquer pessoa (humano ou agente) pode sugerir uma ideia. Ideias são anotadas no **Banco de Ideias** (`docs/IDEAS.md`). Uma ideia nunca entra diretamente em uma sprint. Toda ideia precisa ser avaliada antes de virar trabalho.

#### Discussão

O Founder e o CTO (ou Architect) discutem a ideia. Perguntas feitas nesta etapa:

- Isso resolve um problema real e imediato?
- Isso está dentro do escopo da sprint atual?
- Qual é o custo de implementação?
- Qual é o custo de NÃO implementar?
- Isso pode esperar?

Se a resposta para "isso pode esperar?" for **sim**, a ideia permanece no Banco de Ideias.

#### RFC (Request for Comments)

Para mudanças significativas que afetam múltiplos módulos ou alteram comportamento existente, um RFC é escrito. O RFC descreve:

- O problema
- A solução proposta
- Alternativas consideradas
- Impacto nos módulos existentes
- Riscos

RFCs são armazenados em `docs/rfcs/` com numeração sequencial (`RFC-001.md`, `RFC-002.md`).

Nem toda mudança precisa de RFC. Correções de bugs, implementações dentro de um módulo já planejado e melhorias cosméticas não exigem RFC.

#### ADR (Architecture Decision Record)

Quando a discussão ou o RFC resulta em uma **decisão arquitetural** (escolha de tecnologia, mudança de padrão, definição de interface), ela é registrada como ADR em `docs/adrs/`.

ADRs são permanentes. Podem ser **substituídas** por novos ADRs, mas nunca deletadas. Isso garante que qualquer agente futuro entenda por que uma decisão foi tomada.

Formato de ADR:

```markdown
# ADR-NNN — Título da Decisão

**Data**: YYYY-MM-DD
**Status**: Proposto | Aceito | Substituído por ADR-NNN
**Decisor**: Founder / CTO

## Contexto
O que motivou esta decisão.

## Decisão
O que foi decidido.

## Consequências
O que muda por causa desta decisão.

## Alternativas Consideradas
O que foi avaliado e por que foi rejeitado.
```

#### Missão

Uma missão é uma unidade de trabalho atômica. Toda implementação acontece dentro de uma missão. A estrutura de uma missão é detalhada no [Capítulo 4](#4-estrutura-oficial-de-uma-missão).

#### Implementação

O agente designado executa a missão dentro do escopo definido. Durante a implementação:

- Apenas os arquivos listados no escopo podem ser modificados
- Novos arquivos podem ser criados apenas se a missão autoriza
- Qualquer dúvida deve ser levantada antes de assumir uma resposta
- Toda decisão não-trivial deve ser documentada no corpo da entrega

#### Revisão

Toda entrega passa por revisão antes de ser aceita. A revisão segue o processo descrito no [Capítulo 7](#7-processo-de-revisão).

#### GitHub (Commit/PR)

Após revisão aprovada:

- O código é commitado em uma branch nomeada segundo o padrão do projeto
- Um Pull Request é criado com descrição clara
- O PR referencia a missão correspondente

#### Validação

O código no PR é validado:

- Testes passam
- Linting passa
- Nenhum arquivo fora do escopo foi modificado
- A documentação foi atualizada (se aplicável)

#### Merge

Após validação, o PR é mergeado na branch principal. O Founder é o único com autoridade de merge no estágio atual do projeto (equipe solo).

#### Próxima Missão

Com o merge concluído, o ciclo recomeça com a próxima missão da sprint.

---

## 4. Estrutura Oficial de uma Missão

Toda missão deve conter os seguintes campos. Missões incompletas não são aceitas para execução.

### 4.1 Template Obrigatório

```markdown
# MISSÃO NNN — Título Descritivo

## Objetivo
Uma frase clara e mensurável que define o que esta missão entrega.
Deve ser possível responder "sim" ou "não" se o objetivo foi alcançado.

## Contexto
Por que esta missão existe. O que aconteceu antes dela.
Quais decisões anteriores a motivam (referenciar ADRs e missões anteriores).

## Arquivos Envolvidos
Lista explícita de todos os arquivos que podem ser criados ou modificados.

### Arquivos a Criar
- `caminho/para/novo_arquivo.py` — Descrição breve

### Arquivos a Modificar
- `caminho/para/arquivo_existente.py` — O que será alterado e por quê

## Arquivos Proibidos de Alterar
Lista explícita de arquivos que NÃO devem ser tocados nesta missão.
Na dúvida, qualquer arquivo não listado em "Arquivos Envolvidos" é proibido.

## Critérios de Sucesso
Lista de condições que devem ser verdadeiras para a missão ser considerada completa.
- [ ] Critério 1
- [ ] Critério 2
- [ ] Critério N

## Critérios de Falha
Condições que indicam que a missão falhou ou precisa ser refeita.
- Qualquer arquivo fora do escopo foi modificado
- Testes existentes quebraram
- Dependências não justificadas foram adicionadas

## Entrega Esperada
O que exatamente o agente deve produzir ao final da missão.

## Próximos Passos
O que vem depois desta missão (para dar contexto ao agente sobre o futuro).
```

### 4.2 Regras de Missão

1. **Uma missão = um objetivo.** Se há dois objetivos, são duas missões.
2. **Escopo é lei.** O que está fora do escopo não existe durante a missão.
3. **Missões são sequenciais.** A missão N+1 só começa após a missão N ser aceita.
4. **Missões podem ser subdivididas.** Se uma missão é grande demais, divida em sub-missões (NNN.1, NNN.2, etc.).
5. **Toda missão tem dono.** Um único agente é responsável por cada missão. Responsabilidade compartilhada é responsabilidade de ninguém.

---

## 5. Regras para Agentes de IA

Estas regras são **obrigatórias**. Não são sugestões. Todo agente que trabalha neste projeto deve segui-las sem exceção.

### 5.1 Regras Absolutas (Violação = Rejeição Imediata)

| # | Regra | Justificativa |
|---|-------|---------------|
| R1 | **Nunca alterar arquivos fora do escopo da missão** | Mudanças não rastreadas são a principal fonte de bugs em projetos com múltiplos agentes |
| R2 | **Nunca criar dependências externas sem justificativa documentada** | Cada dependência é dívida técnica. Deve resolver um problema que não pode ser resolvido com código próprio de forma razoável |
| R3 | **Nunca renomear módulos, classes públicas ou funções de interface sem autorização do Architect ou CTO** | Renomeações quebram contratos e afetam todos os consumidores |
| R4 | **Nunca remover código funcional sem explicação** | Código funcional foi validado. Removê-lo exige justificativa |
| R5 | **Nunca fazer commit de secrets, API keys, tokens ou credenciais** | Violação de segurança irrecuperável. Uma key commitada está comprometida para sempre |
| R6 | **Nunca modificar este manual sem aprovação do Founder e do CTO** | Este é o documento constitucional do projeto |

### 5.2 Regras Comportamentais (Esperado de Todo Agente)

**Sempre explicar decisões.** Se você escolheu o caminho A em vez do caminho B, diga por quê. Código sem explicação é código que será reescrito pelo próximo agente que não entendeu a intenção.

**Sempre informar riscos.** Se uma implementação tem um ponto frágil, uma limitação conhecida ou uma premissa que pode não se manter, documente explicitamente. Omitir riscos é pior que não resolver o problema.

**Sempre separar melhorias opcionais da entrega principal.** Se durante a implementação você identificar melhorias possíveis que estão fora do escopo, liste-as em uma seção separada chamada "Melhorias Sugeridas" no final da entrega. Nunca implemente melhorias fora do escopo sem autorização.

**Sempre verificar o estado atual antes de modificar.** Antes de alterar um arquivo, leia-o por completo. Nunca assuma que o arquivo está no estado que você espera. Outro agente pode ter modificado entre a sua última leitura e agora.

**Sempre manter a consistência existente.** Se o projeto usa snake_case, use snake_case. Se os imports estão organizados de uma forma, siga a mesma forma. Consistência é mais importante que preferência pessoal.

**Nunca mentir sobre capacidade.** Se você não sabe algo, diga "não sei". Se não tem certeza, diga "não tenho certeza". Respostas fabricadas com confiança são mais destrutivas que respostas honestas com incerteza.

### 5.3 Checklist de Pré-Entrega

Todo agente deve verificar antes de considerar uma missão concluída:

```
□ Li o escopo da missão por completo?
□ Alterei APENAS os arquivos autorizados?
□ Meu código segue as convenções definidas no Capítulo 6?
□ Expliquei todas as decisões não-óbvias?
□ Informei todos os riscos que identifiquei?
□ Os testes existentes continuam passando?
□ Criei testes para o código novo?
□ Atualizei a documentação relevante?
□ Listei melhorias sugeridas separadamente?
□ Minha entrega atende a todos os critérios de sucesso?
```

---

## 6. Convenções de Código

### 6.1 Princípios Gerais

**Legibilidade é a prioridade número um.**  
Código é lido muito mais vezes do que é escrito. Especialmente neste projeto, onde múltiplos agentes de IA trabalham no mesmo codebase. Se um agente não consegue entender seu código em 30 segundos, o código precisa ser reescrito.

**Funções pequenas com responsabilidade única.**  
Cada função faz uma coisa. Se o nome da função contém "e" (ex: `process_and_save`), provavelmente deveria ser duas funções.

**Baixo acoplamento, alta coesão.**  
Módulos que fazem coisas relacionadas ficam juntos (coesão). Módulos que não precisam se conhecer não se conhecem (acoplamento). Quando dois módulos precisam se comunicar, usam interfaces, não implementações.

### 6.2 Python — Convenções Específicas

#### Estilo

- **PEP 8** como base, sem exceções
- **Comprimento de linha**: 88 caracteres (padrão Black)
- **Formatter**: Black
- **Linter**: Ruff
- **Type Checker**: mypy (modo strict para código novo)

#### Nomenclatura

| Elemento | Convenção | Exemplo |
|----------|-----------|---------|
| Módulos | `snake_case` | `script_engine.py` |
| Classes | `PascalCase` | `ScriptEngine` |
| Funções | `snake_case` | `generate_script()` |
| Constantes | `UPPER_SNAKE_CASE` | `MAX_RETRY_COUNT` |
| Variáveis | `snake_case` | `video_duration` |
| Variáveis privadas | `_snake_case` | `_internal_cache` |
| Interfaces (ABC) | `PascalCase` com sufixo claro | `NarrationProvider` |
| Type aliases | `PascalCase` | `VideoConfig` |

#### Imports

Organizar imports em três blocos, separados por linha em branco:

```python
# 1. Biblioteca padrão
import os
from pathlib import Path

# 2. Bibliotecas de terceiros
from fastapi import FastAPI
from pydantic import BaseModel

# 3. Módulos do projeto
from engines.script import ScriptEngine
from core.config import ProjectConfig
```

#### Type Hints

Type hints são **obrigatórios** em:

- Assinaturas de funções públicas (parâmetros e retorno)
- Atributos de classes
- Variáveis cujo tipo não é óbvio

```python
# Correto
def generate_script(topic: str, config: ScriptConfig) -> Script:
    ...

# Incorreto
def generate_script(topic, config):
    ...
```

#### Docstrings

Docstrings são obrigatórias em:

- Todas as classes públicas
- Todas as funções públicas
- Módulos (`__init__.py` ou no topo do arquivo)

Formato Google Style:

```python
def generate_script(topic: str, config: ScriptConfig) -> Script:
    """Generate a video script based on the given topic.

    Uses the configured LLM provider to generate an original script
    following the project's content style and constraints.

    Args:
        topic: The subject matter for the script.
        config: Script generation configuration including
            tone, length, and style parameters.

    Returns:
        A Script object containing the generated text,
        estimated duration, and metadata.

    Raises:
        LLMProviderError: If the LLM provider fails after all retries.
        InvalidConfigError: If the config contains invalid parameters.
    """
```

Funções privadas e funções curtas autoexplicativas não exigem docstring, mas um comentário de uma linha é bem-vindo quando a intenção não é óbvia.

#### Tratamento de Erros

```python
# Correto — específico, informativo
try:
    audio = provider.generate(text, voice_config)
except ProviderRateLimitError as e:
    logger.warning("TTS rate limit reached", provider=provider.name, retry_after=e.retry_after)
    raise
except ProviderError as e:
    logger.error("TTS generation failed", provider=provider.name, error=str(e))
    raise NarrationError(f"Failed to generate narration: {e}") from e

# Incorreto — genérico, silencioso
try:
    audio = provider.generate(text, voice_config)
except Exception:
    pass
```

Regras:

- Nunca usar `except Exception: pass` (exceções silenciosas)
- Sempre capturar exceções específicas
- Sempre incluir contexto na mensagem de erro
- Usar `from e` para preservar a cadeia de exceções

#### Configuração

Toda configuração vem de **fora do código**:

```python
# Correto — configuração externa
config = ProjectConfig.from_yaml("projects/gta6.yaml")
provider = ElevenLabsProvider(api_key=config.narration.api_key)

# Incorreto — hardcoded
API_KEY = "sk-abc123..."
VOICE_ID = "xyz789"
```

### 6.3 Estrutura de um Módulo

Todo módulo (engine) segue esta estrutura mínima:

```
engine_name/
├── __init__.py          # Exportações públicas (e APENAS as públicas)
├── engine.py            # Classe principal do módulo
├── models.py            # Dataclasses/Pydantic models do módulo
├── exceptions.py        # Exceções específicas do módulo
├── providers/           # Adapter implementations (se aplicável)
│   ├── __init__.py
│   └── provider_name.py
├── README.md            # Documentação do módulo
└── tests/
    ├── __init__.py
    ├── test_engine.py
    └── test_providers.py
```

O `__init__.py` raiz exporta **apenas** o que outros módulos precisam usar:

```python
"""Script Engine — Generates video scripts from topics."""

from .engine import ScriptEngine
from .models import Script, ScriptConfig
from .exceptions import ScriptError

__all__ = ["ScriptEngine", "Script", "ScriptConfig", "ScriptError"]
```

---

## 7. Processo de Revisão

Nenhuma entrega é aceita sem revisão. Não importa quão simples, quão urgente ou quão confiável o agente seja.

### 7.1 Cinco Perguntas Obrigatórias

Toda revisão responde estas cinco perguntas:

#### 1. O que foi feito?

Descrição clara e concisa das mudanças. Não o "como" técnico, mas o "o quê" funcional.

```
Bom:   "Implementado o ScriptEngine com suporte a geração via Claude e GPT."
Ruim:  "Criei vários arquivos e classes."
```

#### 2. Quais arquivos mudaram?

Lista completa com tipo de mudança:

```
[CRIADO]     engines/script/engine.py
[CRIADO]     engines/script/models.py
[MODIFICADO] config/default.yaml — adicionado bloco "script"
```

#### 3. Existe risco?

Todo risco identificado deve ser listado com severidade:

```
[BAIXO]  O provider de fallback (GPT) não foi testado com prompts longos.
[MÉDIO]  O timeout de 30s pode não ser suficiente para modelos lentos.
[ALTO]   Sem cache, cada regeneração consome tokens pagos.
```

Se não há risco identificado, dizer explicitamente: "Nenhum risco identificado."

#### 4. O que ainda falta?

Transparência sobre trabalho incompleto:

```
- Testes de integração com provider real (apenas mock foi testado)
- Documentação de configuração avançada
- Tratamento de respostas malformadas do LLM
```

Se tudo está completo: "Todos os critérios de sucesso foram atendidos."

#### 5. Como testar?

Instruções reproduzíveis para validar a entrega:

```bash
# Rodar testes unitários
pytest engines/script/tests/ -v

# Teste manual (requer API key configurada)
python -m engines.script --topic "5 segredos do GTA 6" --config projects/gta6.yaml
```

### 7.2 Critérios de Aprovação

Uma entrega é **aprovada** quando:

- Todos os critérios de sucesso da missão são atendidos
- Nenhum arquivo fora do escopo foi modificado
- Testes existentes continuam passando
- O código segue as convenções do Capítulo 6
- As cinco perguntas foram respondidas satisfatoriamente

Uma entrega é **rejeitada** quando:

- Qualquer critério de falha da missão foi acionado
- Arquivos fora do escopo foram modificados sem autorização
- Testes existentes quebram
- Código contém secrets ou credenciais
- O agente não explicou decisões não-triviais

### 7.3 Rejeição e Retrabalho

Quando uma entrega é rejeitada:

1. O motivo da rejeição é documentado
2. O agente recebe feedback específico sobre o que corrigir
3. A missão é reenviada ao mesmo agente (preferencialmente) ou a um novo agente com o contexto completo
4. Rejeições não são punitivas — são parte do processo de qualidade

---

## 8. Controle de Escopo

### 8.1 O Problema

Scope creep (expansão de escopo) é o assassino número um de projetos de software, especialmente projetos solo. Ele se manifesta de formas sutis:

- "Já que estou mexendo aqui, aproveito e melhoro isso"
- "Seria fácil adicionar essa feature agora"
- "Esse módulo ficaria melhor se eu também fizesse aquilo"
- "Vi que o concorrente tem essa feature, devemos ter também"

Cada uma dessas frases, isoladamente, parece razoável. Juntas, transformam um MVP de 2 meses em um projeto inacabado de 12 meses.

### 8.2 As Regras

**Regra 1: Toda ideia nova vai para o Banco de Ideias.**  
O arquivo `docs/IDEAS.md` é o destino de qualquer sugestão que não está no escopo da sprint atual. Não importa quão boa a ideia seja. Se não é prioridade agora, ela espera.

**Regra 2: Nenhuma ideia entra diretamente na sprint atual.**  
Uma ideia do Banco de Ideias só vira trabalho real se for promovida durante o **planejamento da próxima sprint**. Promoção durante a sprint em andamento só é permitida se o Founder decidir explicitamente e aceitar o impacto no cronograma.

**Regra 3: Se uma melhoria é encontrada durante a implementação, registre e continue.**  
O agente está implementando o módulo de narração e percebe que o módulo de configuração poderia ser melhorado. O que ele faz? Registra no Banco de Ideias e continua sua missão. Não toca no módulo de configuração.

**Regra 4: O escopo da missão é o escopo máximo.**  
A missão diz "implementar ScriptEngine com geração via Claude". O agente não implementa "geração via Claude + GPT + Gemini + cache + métricas". Implementa exatamente o que foi pedido.

### 8.3 Por Que Isso Protege o Projeto

Um projeto solo com orçamento limitado tem um recurso escasso: o tempo e a energia do fundador. Cada feature adicional consome:

- Tempo de implementação
- Tempo de teste
- Tempo de manutenção futura
- Complexidade cognitiva para entender o sistema
- Superfície de bugs potenciais

Controle de escopo não é limitação — é proteção. Ele garante que o que **precisa** ser feito será feito antes do que **poderia** ser feito.

### 8.4 Formato do Banco de Ideias

```markdown
# Banco de Ideias

## Em Avaliação
- [ ] [DATA] Descrição da ideia — Origem (quem sugeriu/onde surgiu)

## Aprovadas para Sprint Futura
- [ ] [DATA] Descrição — Sprint estimada

## Descartadas
- [x] [DATA] Descrição — Motivo de descarte
```

---

## 9. Filosofia de Automação

### 9.1 Princípio Central

> Automação é consequência. Não é objetivo.

A tentação em projetos de IA é automatizar tudo desde o dia um. Isso é um erro. Automação prematura cristaliza processos que ainda não foram validados. Quando o processo muda — e ele vai mudar — a automação vira obstáculo, não ajuda.

### 9.2 As Três Fases

#### Fase 1 — Funcionar

O processo funciona manualmente. O humano está no controle de cada etapa. Os resultados são avaliados.

Nesta fase, o objetivo é:
- Validar que o output tem qualidade
- Entender os pontos de falha
- Calibrar expectativas de tempo e custo
- Identificar quais etapas realmente precisam de intervenção humana

#### Fase 2 — Automatizar

Os processos validados são automatizados, um por vez. Cada automação inclui:
- Pontos de verificação (quality gates)
- Capacidade de rollback
- Logging detalhado
- Alertas em caso de falha

Nesta fase, o humano muda de **operador** para **supervisor**. Ele não executa — ele monitora e intervém quando necessário.

#### Fase 3 — Escalar

Os processos automatizados e monitorados são escalados: mais vídeos, mais canais, mais nichos, mais plataformas.

Escalar só é seguro quando:
- A qualidade é consistente sem supervisão
- Os custos são previsíveis
- Os pontos de falha são tratados automaticamente
- O monitoramento funciona

### 9.3 Aplicação Prática no Pipeline

| Etapa do Pipeline | Fase 1 (Manual) | Fase 2 (Automático) | Fase 3 (Escala) |
|-------------------|-----------------|---------------------|-----------------|
| Escolha de tema | Fundador decide | Trend Engine sugere, Fundador aprova | Trend Engine decide |
| Roteiro | LLM gera, Fundador revisa | LLM gera, QA automático filtra | Pipeline completo |
| Narração | Fundador ouve e aprova | Geração automática com threshold | Batch processing |
| Vídeo | Fundador assiste antes de publicar | Checklist automático | Pipeline completo |
| Publicação | Upload manual | Upload automático com scheduling | Multi-plataforma |

---

## 10. Filosofia de Crescimento

### 10.1 As Cinco Fases

```
MVP → Validação → Otimização → Escala → Monetização → Expansão
```

#### MVP — Provar que funciona

Objetivo: Produzir um único vídeo completo, do tema ao arquivo final, utilizando o pipeline.

Métricas de sucesso:
- O vídeo foi produzido sem intervenção manual no código
- A qualidade é suficiente para publicação (avaliação subjetiva do Founder)
- O tempo total é inferior a 30 minutos
- O custo é inferior a R$ 5 por vídeo

Prazo estimado: Sprint 1-3.

#### Validação — Provar que funciona repetidamente

Objetivo: Produzir 10-20 vídeos e publicar. Coletar dados reais de audiência.

Métricas de sucesso:
- Processo é repetível sem bugs bloqueantes
- Audiência é consistente (não importa o número absoluto, importa a consistência)
- Custo por vídeo é sustentável dentro do orçamento
- O Founder está satisfeito com a qualidade

Prazo estimado: Sprint 3-5.

#### Otimização — Fazer melhor

Objetivo: Melhorar qualidade, reduzir tempo, reduzir custo.

Métricas de sucesso:
- Tempo por vídeo cai 30% ou mais
- Qualidade sobe (medida por retenção e views)
- Custo por vídeo cai ou se mantém

Prazo estimado: Sprint 5-8.

#### Escala — Fazer mais

Objetivo: Aumentar volume e/ou adicionar canais/nichos.

Pré-requisitos:
- Qualidade validada
- Processo automatizado
- Custos previsíveis
- Monitoramento funcionando

Prazo estimado: Sprint 8-12.

#### Monetização — Gerar receita

Objetivo: O conteúdo gera receita que cobre os custos e gera lucro.

Fontes possíveis (não no escopo atual):
- Monetização do YouTube/TikTok
- Afiliados
- Patrocínios
- Licenciamento da tecnologia

#### Expansão — Crescer o negócio

Objetivo: Novos nichos, novos idiomas, novos formatos, potencialmente novos clientes.

Esta fase está anos no futuro. Decisões sobre ela serão tomadas quando chegarmos lá, com os dados que tivermos.

### 10.2 A Regra de Ouro do Crescimento

> Nunca avançar para a próxima fase sem ter evidência concreta de que a fase atual está funcionando.

Cada fase tem métricas de sucesso. Se as métricas não são atingidas, a fase não está concluída. Avançar prematuramente é acumular dívida técnica e operacional.

---

## 11. Comunicação entre Agentes

### 11.1 O Problema

Agentes de IA não têm memória persistente entre sessões. O que foi discutido com o agente A às 14h não existe para o agente B às 15h, nem para o agente A às 16h em uma nova sessão.

O projeto **nunca** pode depender da memória de um único modelo.

### 11.2 A Solução: Documentação como Memória

Toda informação necessária para continuar o trabalho deve existir em **arquivos do repositório**, não na memória de conversas. Se um agente precisa de contexto, ele lê os documentos. Se um agente produz contexto, ele escreve em documentos.

### 11.3 O que Todo Agente Deve Entregar

Ao finalizar uma missão, o agente entrega:

1. **O código** (óbvio, mas incompleto sozinho)
2. **Um relatório de entrega** respondendo as cinco perguntas do Capítulo 7
3. **README do módulo atualizado** (se o módulo foi criado ou significativamente alterado)
4. **Decisões documentadas** (se alguma decisão não-trivial foi tomada)
5. **Contexto para o próximo agente** — uma seção explícita no relatório que responde: "Se outro agente precisar continuar este trabalho, o que ele precisa saber?"

### 11.4 Formato do Handoff (Passagem de Bastão)

```markdown
## Contexto para Continuação

### Estado Atual
Descrição do estado em que o módulo/feature se encontra.

### O que Funciona
Lista do que está implementado e testado.

### O que Não Funciona / Falta
Lista do que não foi implementado ou tem problemas conhecidos.

### Dependências
O que este módulo precisa de outros módulos para funcionar.

### Decisões Tomadas
Resumo das decisões feitas durante a implementação (com link para ADRs se aplicável).

### Armadilhas Conhecidas
Coisas que podem confundir o próximo agente.
```

### 11.5 Regra de Contexto Suficiente

> Se um agente precisa de mais de 10 minutos para entender o estado do projeto antes de começar a trabalhar, a documentação está insuficiente.

O teste é simples: um agente novo, sem nenhum contexto prévio, recebe a missão. Se ele consegue entender o que precisa fazer lendo apenas:

1. Este manual
2. A missão
3. O README do módulo relevante
4. O ADR relevante (se existir)

...então a documentação está funcionando.

---

## 12. Qualidade

### 12.1 Definição de Qualidade Neste Projeto

Qualidade não é perfeição. Qualidade é **confiabilidade ao longo do tempo**.

Código de qualidade é código que:
- Funciona corretamente hoje
- Continuará funcionando amanhã sem surpresas
- Pode ser modificado sem medo
- Pode ser entendido por qualquer agente que o leia

### 12.2 Hierarquia de Prioridades

Quando houver conflito, respeitar esta ordem:

```
1. Correção    — O código faz o que deveria fazer?
2. Clareza     — Outro agente entende o que o código faz?
3. Robustez    — O código lida com falhas sem quebrar?
4. Simplicidade — O código é o mais simples possível?
5. Performance — O código é rápido o suficiente?
```

Performance é a **última** prioridade. Ela só sobe na lista quando dados concretos (benchmarks, profiling) mostram que é um gargalo real, não teórico.

### 12.3 Dívida Técnica

Dívida técnica é aceitável em doses controladas, quando:

- É consciente (documentada com `# TODO:` ou `# HACK:`)
- É temporária (tem uma missão planejada para resolvê-la)
- É localizada (não se espalha para outros módulos)

Dívida técnica é inaceitável quando:

- É silenciosa (não documentada)
- É permanente (ninguém planeja resolver)
- É sistêmica (afeta a arquitetura)

Formato obrigatório para dívida técnica no código:

```python
# TODO(missão): Descrição do que precisa ser feito
# Razão pela qual foi deixado assim: ...
# Impacto se não for resolvido: ...
```

### 12.4 Testes

Testes não são opcionais. Eles são **parte da entrega**.

| Tipo de Teste | Quando | Responsabilidade |
|---------------|--------|------------------|
| Unitário | Sempre, para toda função pública | O agente que implementa |
| Integração | Quando módulos interagem | O agente da missão de integração |
| E2E (End-to-end) | Quando o pipeline completo é validado | Missão específica de QA |

Cobertura mínima esperada:
- Funções públicas: 100% dos caminhos principais (happy path + erros esperados)
- Edge cases: documentados mesmo quando não testados

Framework de teste: **pytest**.

---

## 13. Gestão de Configuração e Versionamento

> [!NOTE]
> **Capítulo adicionado pelo CTO.** Justificativa: com múltiplos agentes contribuindo código, regras claras de versionamento evitam conflitos destrutivos e perda de trabalho. Este capítulo é tão crítico quanto as convenções de código.

### 13.1 Branching Strategy

No estágio atual (equipe solo), adotamos **GitHub Flow** simplificado:

```
main (sempre funcional)
  └── mission/NNN-descricao-curta (branch por missão)
```

- `main` deve **sempre** estar em estado funcional. Nunca commitar código quebrado diretamente em `main`.
- Cada missão trabalha em uma branch própria.
- A branch é mergeada em `main` após aprovação.
- Branches são deletadas após merge.

### 13.2 Commits

Formato de mensagem de commit:

```
[MISSÃO-NNN] tipo: descrição curta

Corpo opcional com detalhes adicionais.
```

Tipos permitidos:

| Tipo | Uso |
|------|-----|
| `feat` | Nova funcionalidade |
| `fix` | Correção de bug |
| `docs` | Documentação |
| `refactor` | Refatoração sem mudança funcional |
| `test` | Adição ou correção de testes |
| `config` | Mudança de configuração |
| `infra` | Mudança de infraestrutura (Docker, CI, etc.) |

Exemplos:

```
[MISSÃO-001] feat: implement ScriptEngine with Claude provider
[MISSÃO-001] test: add unit tests for script generation
[MISSÃO-002] fix: handle empty response from ElevenLabs API
```

### 13.3 Tags e Releases

Após marcos significativos (fim de sprint, MVP funcional), criar tags:

```
v0.1.0 — MVP: primeiro vídeo gerado
v0.2.0 — Pipeline com publicação automática
```

Seguir Semantic Versioning quando o projeto atingir estabilidade.

---

## 14. Segurança e Secrets

> [!NOTE]
> **Capítulo adicionado pelo CTO.** Justificativa: o projeto utiliza múltiplas API keys de serviços pagos (ElevenLabs, LLMs, YouTube). Um único vazamento pode gerar custos financeiros imediatos. Agentes de IA são particularmente propensos a incluir credenciais em código se não receberem instruções explícitas.

### 14.1 Regra Absoluta

> **Nenhuma credencial, API key, token ou secret deve existir em qualquer arquivo versionado no Git. Nunca. Sem exceção.**

### 14.2 Como Gerenciar Secrets

**Desenvolvimento local**: Arquivo `.env` na raiz do projeto (listado no `.gitignore`).

```env
ELEVENLABS_API_KEY=sk-...
OPENAI_API_KEY=sk-...
YOUTUBE_CLIENT_SECRET=...
```

**No código**: Acessar via variáveis de ambiente com validação.

```python
import os

api_key = os.environ.get("ELEVENLABS_API_KEY")
if not api_key:
    raise ConfigurationError("ELEVENLABS_API_KEY environment variable is not set")
```

**No repositório**: Arquivo `.env.example` com as variáveis necessárias, sem valores reais.

```env
ELEVENLABS_API_KEY=your_key_here
OPENAI_API_KEY=your_key_here
```

### 14.3 .gitignore Obrigatório

O `.gitignore` deve conter, no mínimo:

```
.env
.env.*
!.env.example
*.key
*.pem
__pycache__/
*.pyc
.venv/
output/
temp/
```

### 14.4 Verificação

Antes de qualquer commit, verificar que nenhuma credencial está incluída. Ferramentas como `git-secrets` ou hooks de pre-commit podem ser configurados para automatizar essa verificação.

---

## 15. Gestão de Erros e Incidentes

> [!NOTE]
> **Capítulo adicionado pelo CTO.** Justificativa: com um pipeline que depende de múltiplas APIs externas, falhas vão acontecer regularmente. Sem um protocolo claro, cada agente vai lidar com erros de forma diferente, criando inconsistência e dificultando debugging.

### 15.1 Classificação de Erros

| Severidade | Descrição | Exemplo | Ação |
|------------|-----------|---------|------|
| **CRITICAL** | Pipeline parado, impossível produzir | API key expirada, banco corrompido | Parar tudo, resolver imediatamente |
| **HIGH** | Funcionalidade principal degradada | TTS retornando áudio cortado | Resolver antes de continuar |
| **MEDIUM** | Funcionalidade secundária falhando | Thumbnail não gerada | Registrar, continuar, resolver na próxima sprint |
| **LOW** | Cosmético ou inconveniente | Log com formato errado | Registrar no backlog |

### 15.2 Logging Estruturado

Todo módulo deve utilizar logging estruturado com os seguintes campos mínimos:

```python
logger.info(
    "Script generated successfully",
    module="script_engine",
    topic=topic,
    word_count=len(script.text.split()),
    duration_seconds=elapsed,
    provider="claude",
)
```

Campos obrigatórios em todo log:
- `module` — qual módulo gerou o log
- Contexto relevante da operação

Níveis de log e quando usar:

| Nível | Quando |
|-------|--------|
| `DEBUG` | Detalhes internos úteis apenas para debugging |
| `INFO` | Operações normais completadas com sucesso |
| `WARNING` | Algo inesperado aconteceu, mas o sistema se recuperou |
| `ERROR` | Uma operação falhou e não foi possível recuperar |
| `CRITICAL` | O sistema inteiro está comprometido |

### 15.3 Tratamento de Falhas Externas

Toda chamada a serviço externo deve implementar:

1. **Timeout**: Nunca esperar indefinidamente
2. **Retry com backoff exponencial**: 1s → 2s → 4s → desistir
3. **Fallback** (quando disponível): ElevenLabs falhou → tentar OpenAI TTS
4. **Circuit Breaker** (fase futura): Se um serviço falhou N vezes seguidas, parar de tentar por X minutos

```
Chamada Externa
    ↓
  Timeout?  → Retry (até N vezes)
    ↓              ↓
  Sucesso      Todas falharam?
    ↓              ↓
  Retornar     Fallback disponível?
                   ↓           ↓
                  Sim          Não
                   ↓           ↓
              Tentar fallback  Registrar erro
                               Notificar
                               Parar gracefully
```

---

## Apêndice A — Glossário

| Termo | Definição |
|-------|-----------|
| **ADR** | Architecture Decision Record — documento que registra uma decisão arquitetural |
| **Adapter** | Padrão de design que abstrai um serviço externo atrás de uma interface interna |
| **Banco de Ideias** | Arquivo onde ideias fora do escopo atual são registradas para avaliação futura |
| **DAG** | Directed Acyclic Graph — grafo direcionado sem ciclos, usado para modelar o pipeline |
| **Engine** | Módulo de domínio responsável por uma etapa do pipeline de produção |
| **Handoff** | Passagem de contexto de um agente para outro |
| **Human-in-the-loop** | Ponto no pipeline onde um humano revisa e aprova antes de prosseguir |
| **Missão** | Unidade atômica de trabalho com escopo, critérios de sucesso e entrega definidos |
| **MVP** | Minimum Viable Product — versão mínima do produto que valida a proposta |
| **Pipeline** | Sequência de processamento do conteúdo, do tema ao vídeo publicado |
| **Provider** | Implementação concreta de um adapter para um serviço específico |
| **Quality Gate** | Ponto de verificação de qualidade entre etapas do pipeline |
| **RFC** | Request for Comments — proposta de mudança significativa aberta para discussão |
| **Scope Creep** | Expansão descontrolada do escopo do projeto |
| **Sprint** | Período fixo de trabalho (2 semanas) com entregas definidas |

---

## Apêndice B — Checklist Rápido para Novos Agentes

Você é um agente de IA que acabou de receber uma missão neste projeto. Antes de começar:

```
□ Li este manual por completo
□ Li a missão designada e entendi todos os campos
□ Identifiquei os arquivos que posso modificar
□ Identifiquei os arquivos que NÃO posso modificar
□ Li os READMEs dos módulos relevantes
□ Li os ADRs referenciados na missão
□ Entendi os critérios de sucesso
□ Entendi os critérios de falha
□ Sei como formatar minha entrega (Capítulo 7)
□ Sei que melhorias fora do escopo vão para "Melhorias Sugeridas", não para o código
```

Se algum item acima não pode ser completado por falta de informação, **pergunte antes de assumir**.

---

## Apêndice C — Atualizações deste Manual

Este manual é um documento vivo. Ele será atualizado conforme o projeto evolui.

Toda atualização segue as regras:
- Deve ser proposta e justificada
- Deve ser aprovada pelo Founder e pelo CTO
- Deve ser versionada (a versão no cabeçalho deve ser incrementada)
- As mudanças devem ser descritas nesta seção

### Histórico de Versões

| Versão | Data | Alteração |
|--------|------|-----------|
| 1.0 | 2026-06-29 | Versão inicial — Todos os 15 capítulos |

---

*Este documento é propriedade do projeto AI Content Factory.*  
*Mantido pelo CTO. Aprovado pelo Founder.*  
*Nenhuma contribuição é aceita sem leitura prévia deste manual.*
