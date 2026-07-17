# CODEX HANDOFF — Market Intelligence & Learning

**Origem:** GPT da Web (estruturação) → DeepSeek (documentação no workspace seguro)
**Data:** 2026-07-16
**Status:** HANDOFF ESTRATEGICO - AGUARDANDO REVISAO DO CODEX

---

## Mensagem do GPT da Web

Codex,

Leandro concebeu esta nova camada ao perceber que podcasts, vídeos, entrevistas e estudos de caso frequentemente contêm ferramentas, processos, estruturas de funil e estratégias que poderiam beneficiar a AI Content Factory.

A proposta não é despejar transcrições na memória dos funcionários.

A proposta é criar um processo auditável:

fonte
→ evidência
→ extração
→ verificação
→ Knowledge Card
→ experimento
→ resultado medido
→ conhecimento aprovado ou arquivado.

O projeto atual já possui um embrião importante no DailyLearningRadar. Preserve esse trabalho e avalie se a solução correta é expansão, novo domínio, novo departamento ou uma arquitetura híbrida.

Nenhuma promessa financeira, propaganda ou estratégia não verificada deve virar instrução para os funcionários.

Nenhum gasto, publicação ou promoção de conhecimento deve ocorrer sem aprovação de Leandro e resultado mensurável.

— GPT da Web, em colaboração com Leandro Vieira

---

## O que foi criado

| Arquivo | Tamanho | Proposito |
|---|---|---|
| `ideas/2026-07-16_market_intelligence_learning.md` | ~22 secoes | Proposta completa do Market Intelligence & Learning |
| `ideas/2026-07-16_market_intelligence_learning_CODEX_HANDOFF.md` | Este arquivo | Handoff estrategico |

## Componentes existentes encontrados e avaliados

| Componente | Avaliação |
|---|---|
| DailyLearningRadar | Embrião importante; faz triagem, score, experimento, guardrails. Não faz transcrição, evidência visual, extração estruturada, Knowledge Cards, alocação de capital |
| StrategyIntelligencePipeline | Detecta ferramentas, métricas, padrões. Reutilizável como base para extração, mas sem auditoria cética ou Knowledge Cards |
| OrganizationalMemory | Armazenamento de conhecimento institucional. Pode receber Knowledge Cards aprovados |
| ApprovalRuntime | Reutilização completa para aprovação de experimentos |
| ProviderBudgetGuard | Reutilização completa para controle de custo |
| QualityRuntime | Pode validar Knowledge Cards com regras específicas |

## Arquivos que o Codex deve ler

- `ideas/2026-07-16_market_intelligence_learning.md` (proposta completa)
- `core/content_factory/daily_learning_radar.py` (embrião existente)
- `core/departments/strategy_intelligence/` (pipeline de extração)
- `core/company/organizational_memory.py` (destino de cards aprovados)
- `core/approval/runtime.py` (gate de aprovação)
- `core/tools/provider_control.py` (controle de orçamento)

## Recomendação arquitetural preliminar

**Híbrida:** novo domínio `core/market_intelligence_learning/` para a lógica, com departamento opcional `core/departments/market_intelligence/` no futuro. O DailyLearningRadar permanece intacto como triagem diária.

## Decisões pendentes que só Codex/Shin podem responder

### Arquiteturais
- Arquitetura híbrida (domínio + departamento futuro) ou abordagem diferente?
- Reutilizar StrategyIntelligencePipeline ou criar pipeline próprio?
- Knowledge Cards no OrganizationalMemory ou storage próprio?

### Implementação
- Fase 2 (protótipo visual): DeepSeek pode criar?
- Fase 3 (modelos MOCK): DeepSeek pode implementar?
- Qual a ordem correta de implementação?

### Legais/Financeiras
- Orçamento para transcrição via API?
- Limite por experimento?
- Screenshots para análise interna são permitidos?

### Produto
- Nome final aprovado?
- Validade padrão dos cards (90 dias)?
- Quantas fontes mínimas para "verified"?

## Status dos arquivos

Nenhum arquivo oficial foi alterado. Todos os arquivos criados estão em `docs/external_llm_inbox/deepseek/ideas/`, que é uma pasta não rastreada (diretório novo). O git não mostra modificações em `core/`, `apps/`, `demo_*.py`, `scripts/`, ou `AGENTS.md`.
