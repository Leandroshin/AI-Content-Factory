# Handoff do GPT da Web para o Codex — Offer Intelligence

**Status:** HANDOFF ESTRATEGICO - AGUARDANDO REVISAO DO CODEX

---

## Contexto

Leandro Vieira discutiu com o GPT da Web a criação da vertical **Offer Intelligence** durante o período sem créditos do Codex.

O GPT da Web estruturou a visão, o fluxo, os modelos, o sistema de pontuação, as fontes de dados e as fases de desenvolvimento, usando como referência funcional ferramentas de inteligência de ofertas (Flow Spy e similares), **sem copiar código, marca, identidade visual ou textos de concorrentes**.

O DeepSeek foi usado exclusivamente para:
1. Investigar o projeto local (auditoria de arquitetura, componentes existentes, caminhos reais);
2. Produzir documentação formal dentro das pastas permitidas (`docs/external_llm_inbox/deepseek/`);
3. Preparar este handoff.

Nenhum protótipo foi criado ainda. Nenhum arquivo do `core/`, `apps/`, demos ou configurações foi alterado.

---

## Visão aprovada

Fluxo conceitual completo:

```
URL ou oferta
→ coleta de evidências
→ identificação e normalização do produto
→ análise de demanda e tendência
→ análise de presença publicitária
→ comparação com outras ofertas
→ pontuação determinística e transparente (0-100)
→ explicação por IA (apenas explica, não modifica o score)
→ recomendação de teste
→ aprovação humana
→ futura criação de campanha
→ futura publicação
→ cliques, vendas, comissão, custo e ROI
→ aprendizado controlado
```

MVP: entrada por URL ou manual → identificação → evidências → score → IA explica → comparação.

---

## Decisões tomadas

- Implementação original (não copiar concorrentes);
- Score determinístico (IA não modifica a nota);
- LLM apenas explica forças, riscos, evidências ausentes e possíveis testes;
- Toda evidência carrega fonte, data, confiança e tipo (real/estimado/manual/inferido);
- Dados reais e estimados sempre separados visualmente;
- Aprovação humana obrigatória antes de qualquer publicação ou gasto;
- Protótipos do DeepSeek não são produção (servem para validar conceitos);
- APIs reais dependem de pesquisa oficial antes de qualquer implementação.

---

## Arquivos que o Codex deve ler

1. **Documento principal da ideia:**
   `docs/external_llm_inbox/deepseek/ideas/2026-07-16_offer_intelligence.md`

2. **Índice do workspace:**
   `docs/external_llm_inbox/deepseek/INDEX.md`

3. **Checklist de handoff:**
   `docs/external_llm_inbox/deepseek/HANDOFF_CHECKLIST.md`

4. **Arquivos de arquitetura do projeto (já lidos pelo DeepSeek):**
   - `AGENTS.md`
   - `docs/CURRENT_STATE_2026-07-10.md`
   - `core/departments/product_research/` (models, pipeline, employee)
   - `core/departments/strategy_intelligence/` (models, pipeline, employee)
   - `core/departments/creative_review/` (models, pipeline, employee)
   - `core/departments/affiliate_deals/` (models, scoring, pipeline, compliance, platforms)
   - `core/content_factory/product_url_intake.py`
   - `core/approval/runtime.py` + `models.py`
   - `core/company/persistence.py` + `quality.py`
   - `core/tools/provider_control.py` + `provider_settings.py`
   - `core/observability.py`
   - `apps/factory_dashboard/` (estrutura)

5. **Estado do repositório:**
   Executar `git status`, `git diff`, `git log --oneline -5` antes de qualquer alteração.

---

## Correções técnicas importantes

| Item | Correção |
|---|---|
| Google Trends | API oficial está em alpha/acesso limitado (anunciada 2025). pytrends é biblioteca não oficial. Não chamar de API oficial. Não usar como dependência crítica. |
| Google Ads API | KeywordPlanIdeaService existe, mas exige developer token + OAuth + customer ID. Custos e limites requerem pesquisa oficial. |
| Meta Ad Library | Diferenciar interface pública, API oficial, consulta manual, armazenamento e redistribuição comercial. Termos de uso exigem pesquisa oficial. |
| TikTok | Research API tem critérios institucionais — não é base comercial. Creative Center é fonte pública/manual. |
| Dados públicos | Informação visível publicamente não significa autorização para coleta em massa, armazenamento indefinido, redistribuição ou revenda. |
| Similarweb/Semrush | Fontes potencialmente pagas; uso comercial pode exigir licença específica. |
| Kokoro | É TTS para geração de voz, **não é LLM**. A camada de score é determinística; um LLM (futuro) explicará os resultados. |

---

## Próxima ação recomendada ao Codex

1. **Verificar estado do repositório:** `git status`, `git diff`, preservar mudanças locais.
2. **Ler a proposta completa** em `ideas/2026-07-16_offer_intelligence.md`.
3. **Validar a decisão arquitetural:** domínio `core/offer_intelligence/` + departamento fino, ou apenas departamento?
4. **Revisar contratos dos modelos** (Offer, OfferScore, EvidenceRecord, etc.) e compatibilidade com `frozen+slots`.
5. **Decidir a ordem das fases** (fase 2 protótipo DeepSeek pode avançar enquanto Codex revisa).
6. **Integrar apenas depois de aprovação de Leandro.**
7. **Rodar compileall + regressão completa** antes de qualquer merge.
8. **Atualizar documentação oficial** após integração.

---

## Mensagem do GPT da Web ao Codex

> Codex,
>
> esta ideia foi estruturada em conjunto com Leandro após análise da arquitetura atual da AI Content Factory e de ferramentas de inteligência de ofertas disponíveis no mercado.
>
> Não trate documentos ou protótipos do DeepSeek como código pronto para produção. Eles existem para validar conceitos, modelos, score, comparação e fluxo antes da integração oficial.
>
> Preserve os controles atuais da fábrica:
> - execução MOCK por padrão;
> - aprovação humana;
> - evidências rastreáveis;
> - orçamento;
> - qualidade;
> - observabilidade;
> - compatibilidade retroativa;
> - nenhum gasto ou publicação sem aprovação.
>
> A prioridade não é copiar uma ferramenta concorrente.
>
> A prioridade é construir uma vertical original que transforme dados rastreáveis de ofertas em decisões explicáveis e, futuramente, em campanhas mensuráveis.
>
> — GPT da Web, em colaboração com Leandro Vieira

---

## Status

**Status:** HANDOFF ESTRATEGICO - AGUARDANDO REVISAO DO CODEX

**Arquivo de proposta principal:** `ideas/2026-07-16_offer_intelligence.md`

**Arquivos de handoff:** `ideas/2026-07-16_offer_intelligence_CODEX_HANDOFF.md` (este)

**INDEX.md e HANDOFF_CHECKLIST.md:** atualizados

**Prot tipo(s) planejado(s):** Fase 2 — ainda não executado (aguardando autorização)
