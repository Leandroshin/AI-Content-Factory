# Offer Intelligence — Vertical de Inteligência de Ofertas para Afiliados, Infoprodutores e Gestores de Tráfego

**Status:** PROPOSTA - NAO IMPLEMENTADA

**Origem estratégica:** GPT da Web, trabalhando em conversa com Leandro Vieira

**Executor documental desta fase:** DeepSeek, exclusivamente dentro do workspace seguro

**Revisor e integrador esperado:** Codex, responsável por validar arquitetura, contratos, testes, regressão e integração oficial

---

# 1. Visão do produto

## Problema que será resolvido

Afiliados, infoprodutores e gestores de tráfego tomam decisões de oferta baseadas em:
- palpites;
- recomendações de terceiros sem transparência;
- dados superficiais (apenas preço e comissão);
- falta de contexto de tendência, concorrência publicitária e sazonalidade.

O mercado tem ferramentas como Flow Spy, mas elas são pagas, fechadas e não se integram a um ecossistema de produção de conteúdo como a AI Content Factory.

## Público-alvo

- **Afiliados** que precisam escolher entre centenas de ofertas qual merece tempo e investimento criativo;
- **Infoprodutores** que querem validar nicho, preço e demanda antes de criar;
- **Gestores de tráfego** que precisam de dados de concorrência publicitária para decidir onde anunciar;
- **O próprio ecossistema AI Content Factory**, que poderá usar o score de ofertas para priorizar production pipelines.

## Relação com a AI Content Factory

Offer Intelligence não substitui nada existente. Ela se posiciona como uma camada **anterior** ao fluxo atual:

```
Offer Intelligence (análise e seleção de ofertas)
  → Strategy Intelligence (tendências e padrões)
    → Product Research (shortlist de candidatos)
      → Creative Review (qualidade do criativo)
        → Affiliate Deals (preparação de oferta)
          → HITL Approval (aprovação humana)
            → Publicação (Telegram, futuro: mais canais)
              → Métricas de negócio (ROI)
                → Aprendizado organizacional
```

A vertical fornece dados e scores para que os departments existentes trabalhem com ofertas mais bem validadas.

## Potencial SaaS comercial

Offer Intelligence pode futuramente ser oferecida como:
- **camada gratuita:** score básico + fontes públicas (URL, dados manuais, mercado livre);
- **camada paga:** fontes de anúncio, monitoramento, alertas, análise por IA, histórico de ROI;
- **integração White Label:** embedding do score e comparador em sites de afiliados.

## Diferencial

Offer Intelligence não é "mais uma ferramenta de métricas". O diferencial é:
1. **Score determinístico e transparente** — cada ponto tem origem, data e confiança;
2. **Explicação por IA** — o score é calculado por regras; a IA interpreta forças, riscos e evidências ausentes;
3. **Integração com produção** — a oferta aprovada alimenta automaticamente Script, Audio, Image, Video, Publishing;
4. **Ciclo de aprendizado** — ROI real realimenta o score (ofertas que converteram bem ganham peso).

---

# 2. Escopo do MVP

O MVP (primeira versão funcional, pós-integração no core) deve permitir:

### 2.1 Entrada por URL ou cadastro manual
- Usuário cola uma URL de produto (Amazon, Mercado Livre, Hotmart, etc.);
- Usuário cadastra manualmente nome, preço, plataforma, comissão;
- Sistema valida a URL (HTTPS, domínio allowlisted, sem credenciais);
- Sistema extrai JSON-LD / Open Graph para preencher automaticamente.

### 2.2 Identificação da oferta
- Produto, domínio, marca, nicho, preço, plataforma;
- Normalização por marketplace (Amazon, ML, Shopee, Hotmart, Digistore24, Braip, etc.);
- Classificação inicial de nicho (tech, gamer, saúde, finanças, casa, etc.);
- Listagem em múltiplas plataformas quando disponível.

### 2.3 Evidências de demanda, tendência e anúncios
- Score usa dados disponíveis; dados ausentes não impedem análise (usam valor conservador);
- Fontes atuais: preço, plataforma, comissão, reviews (manual ou via URL);
- Futuras: Google Trends, Meta Ad Library, Google Ads.

### 2.4 Score transparente (0-100)
- Fórmula determinística com 13 componentes;
- Cada componente mostra valor, peso, origem e confiança;
- IA explica o resultado mas não altera a nota.

### 2.5 Comparação entre ofertas
- 2 a 4 ofertas lado a lado;
- Score total, breakdown por componente, pontos fortes/fracos de cada uma;
- Ranking final por categoria (melhor score, melhor comissão, menor risco, etc.).

---

# 3. Não objetivos

Offer Intelligence **não deve**:

- Prometer produtos "vencedores" ou "garantidos";
- Fabricar métricas (toda estimativa deve ser claramente marcada);
- Copiar código, layout, marca, textos ou identidade visual de concorrentes;
- Contornar login, paywall ou assinatura de terceiros;
- Acessar endpoints privados sem autorização;
- Executar scraping agressivo ou em volume que viole termos de uso;
- Publicar ou gastar sem aprovação humana;
- Tratar estimativas como vendas reais;
- Permitir que a IA modifique o score (IA apenas explica);
- Depender de pytrends ou bibliotecas não oficiais como fonte crítica.

---

# 4. Componentes existentes reutilizáveis

| Componente | Caminho | Como ajuda |
|---|---|---|
| Product Research Department | `core/departments/product_research/` | Models (ProductCandidate, MarketplaceSignal, ProductResearchFinding), scoring pipeline, employee — base para Offer |
| Strategy Intelligence Department | `core/departments/strategy_intelligence/` | Extração de padrões, ferramentas e métricas de fontes; pode alimentar análise de IA |
| Creative Review Department | `core/departments/creative_review/` | Revisão de criativos de ofertas; decisões use_as_is / rebuild / human_review |
| Affiliate Deals Department | `core/departments/affiliate_deals/` | ProductOffer, DealScore, scoring determinístico, compliance, formatter, publishing plan, platform profiles |
| Product URL Intake | `core/content_factory/product_url_intake.py` | Coleta de URL, extração JSON-LD/OG, validação de domínio, ProductUrlEvidence → ProductCandidate |
| Approval Runtime | `core/approval/runtime.py` + `models.py` | ApprovalRequest, ApprovalDecision, ApprovalQueueSnapshot — gate humano |
| Persistence Runtime | `core/company/persistence.py` | ExecutionRecord, CompanySnapshot, ExecutionEvidence — salvamento de estado |
| Quality Runtime | `core/company/quality.py` | QualityRule, QualityReport, validação rule-based pós-execução |
| Organizational Memory | `core/company/organizational_memory.py` | OrganizationalDocument com versionamento — aprendizado controlado |
| Provider Budget Guard | `core/tools/provider_control.py` | ProviderBudget, ProviderBudgetGuard — controle de gasto em fontes pagas |
| Provider Settings | `core/tools/provider_settings.py` | ProviderControlProfile, secret slots mascarados, modo MOCK/REAL |
| Observability | `core/observability.py` | Snapshots (ProductionSnapshot, ApprovalSnapshot, HttpSnapshot) — rastreabilidade |
| Factory Dashboard (hosted) | `apps/factory_dashboard/` | Interface web com D1, filas, decisões, produção, canais — base para futuras telas |
| Dashboard Bridges | `core/content_factory/commerce_dashboard_bridge.py`, `gaming_dashboard_bridge.py` | Padrão de bridge para enviar dados ao dashboard hospedado |
| Dashboard Workers | `core/content_factory/product_dashboard_worker.py`, `dashboard_production_worker.py` | Workers opt-in que buscam fila e executam tarefas |
| Affiliate Dashboard (local) | `core/content_factory/affiliate_dashboard.py` + `server.py` | Fila HITL local com entrada manual, aprovação, rejeição — referência de UI |
| Content Factory Workflows | `core/content_factory/workflow.py`, `affiliate_workflow.py`, `managed_workflow.py` | Orquestração de departments, ExecutivePlan, DepartmentManager |
| Telegram Adapter | `core/tools/adapters/telegram_adapter.py` | Canal de notificação/públicação (alertas de ofertas) |
| Mercado Livre Adapter | `core/tools/adapters/mercado_livre_adapter.py` | Leitura de catálogo ML (preço, seller, estoque) |
| Hotmart Webhook | `core/content_factory/hotmart_webhook.py` | Eventos de compra/cancelamento/reembolso — métricas reais |
| Audience Growth Planner | `core/content_factory/audience_growth.py` | Planejamento de audiência e warmup — pós-seleção de oferta |
| Gaming News Desk | `core/content_factory/gaming_news_desk.py` | Radar de oportunidades — padrão de monitoramento reutilizável |
| Provider Quote Gate | `core/tools/provider_quote.py` | Comparação de plano gratuito vs pago antes de chamada |
| Platform Profiles | `core/departments/affiliate_deals/platforms.py` | AffiliatePlatformProfile, AffiliatePlatformEvaluation — perfis de plataforma |
| Content Factory Models | `core/content_factory/models.py` | ContentBrief, ContentWorkflowResult, ContentProductionPackage |
| Base Department Layer | `core/departments/base/` | ProductionEmployee, ProductionPipeline, StageResult — template para novo departamento |

---

# 5. Arquitetura proposta

## Duas possibilidades

### A. Domínio separado: `core/offer_intelligence/`

```
core/offer_intelligence/
    __init__.py
    models.py
    scoring.py
    collector.py
    comparator.py
```

**Vantagens:**
- Domínio leve, sem acoplamento com ProductionEmployee/Pipeline;
- Pode ser usado por outros departamentos como biblioteca;
- Mais fácil de extrair para SaaS independente.

**Riscos:**
- Não segue o padrão departamental da fábrica;
- Perde hooks de ProductionEmployee (QualityRuntime, metrics, eventos);
- Precisaria de uma camada extra para integração com DM/CompanyRuntime.

### B. Novo departamento: `core/departments/offer_intelligence/`

```
core/departments/offer_intelligence/
    __init__.py
    models.py
    scoring.py
    pipeline.py
    employee.py
```

**Vantagens:**
- Segue o padrão comprovado (ProductionEmployee → ProductionPipeline);
- Herda QualityRuntime, métricas, eventos, observabilidade;
- Integra nativamente com DepartmentManager e workflows;
- department snapshot em `core/observability.py`.

**Riscos:**
- Mais overhead (pipeline, employee) para um domínio que pode ser apenas consulta;
- Pode forçar Offer Intelligence a ser "tarefa" em vez de "serviço".

### Recomendação

Usar **A + B**: `core/offer_intelligence/` como domínio de dados e lógica (models, scoring, collector, comparator), e `core/departments/offer_intelligence/` como departamento fino que embrulha o domínio para execução via ProductionEmployee.

```
core/offer_intelligence/
    __init__.py          # exports públicos
    models.py            # Offer, OfferScore, EvidenceRecord, etc.
    scoring.py           # score_offer() → OfferScore
    comparator.py        # compare() → Comparison

core/departments/offer_intelligence/
    __init__.py           # exports do departamento
    models.py             # OfferIntelligenceTask, OfferIntelligenceMetrics
    pipeline.py           # OfferIntelligencePipeline (extends ProductionPipeline)
    employee.py           # OfferIntelligenceEmployee (extends ProductionEmployee)
```

---

# 6. Modelo de dados

## Offer
| Campo | Tipo | Origem | Natureza | Timestamp | Confiança | Histórico |
|---|---|---|---|---|---|---|
| `offer_id` | UUID | sistema | calculado | criação | — | não |
| `product_name` | str | URL / manual | real / manual | coleta | alta | sim |
| `identity` | OfferIdentity | derivado | calculado | coleta | média | não |
| `source_url` | str | entrada | real | coleta | alta | não |
| `platform_listings` | tuple[OfferPlatformListing] | coleta | real / manual | coleta | por fonte | sim |
| `affiliate_program` | AffiliateProgram \| None | pesquisa | manual / estimado | pesquisa | média | sim |
| `affiliate_platform` | AffiliatePlatform \| None | pesquisa | manual | pesquisa | média | sim |
| `niche` | str | inferido | inferido | análise | baixa-média | não |
| `created_at` | float | sistema | real | criação | — | não |

## OfferIdentity
| Campo | Tipo | Origem | Natureza |
|---|---|---|---|
| `domain` | str | URL | real |
| `brand` | str | extraído / manual | inferido / manual |
| `category` | str | inferido | inferido |
| `marketplace` | str | URL / profile | real |

## AffiliatePlatform
| Campo | Tipo | Origem | Natureza |
|---|---|---|---|
| `name` | str | manual | manual |
| `display_name` | str | manual | manual |
| `commission_range` | tuple[float,float] | manual | manual |
| `cookie_days` | int | manual | manual |
| `payout_threshold` | float | manual | manual |
| `payment_methods` | tuple[str] | manual | manual |
| `allowed_traffic` | tuple[str] | manual | manual |
| `signup_status` | str | manual | manual |

## AffiliateProgram
| Campo | Tipo | Origem | Natureza |
|---|---|---|---|
| `platform` | str | manual | manual |
| `commission_percent` | float | manual / API | manual / real |
| `commission_fixed` | float \| None | manual / API | manual / real |
| `cookie_window_days` | int | manual / API | manual / real |
| `epc` | float \| None | plataforma | estimado |
| `gravity` | float \| None | plataforma | estimado |
| `terms_url` | str | manual | manual |

## OfferPlatformListing
| Campo | Tipo | Origem | Natureza | Confiança |
|---|---|---|---|---|
| `platform` | str | URL / profile | real | alta |
| `url` | str | coleta | real | alta |
| `current_price` | float | coleta | real | alta |
| `old_price` | float \| None | coleta | real / ausente | média |
| `currency` | str | coleta | real | alta |
| `availability` | str | coleta | real | média |
| `fetched_at` | float | sistema | real | — |
| `seller` | str | coleta | real | média |
| `reviews` | int \| None | coleta | real / ausente | média |
| `rating` | float \| None | coleta | real / ausente | média |

## EvidenceSource
| Campo | Tipo | Origem |
|---|---|---|
| `source_type` | str | sistema |
| `source_name` | str | sistema |
| `api_used` | bool | sistema |
| `access_type` | str (public, api, manual) | sistema |
| `confidence_base` | float | sistema |

## EvidenceRecord
| Campo | Tipo | Origem | Natureza | Confiança |
|---|---|---|---|---|
| `source` | EvidenceSource | sistema | — | — |
| `evidence_type` | str | sistema | — | — |
| `value` | Any | coleta | real | por fonte |
| `unit` | str | coleta | real | — |
| `collected_at` | float | sistema | real | — |
| `confidence` | float | calculada | estimada | — |
| `notes` | str | sistema / IA | — | — |

## DemandMetric
| Campo | Tipo | Origem | Natureza |
|---|---|---|---|
| `trend_direction` | str (up/flat/down) | Trends | estimado |
| `trend_volume` | float | Trends | estimado |
| `growth_rate` | float \| None | Trends | estimado |
| `seasonality` | str \| None | inferido | inferido |
| `search_volume_absolute` | int \| None | Keyword Planner | estimado |

## TrafficMetric
| Campo | Tipo | Origem | Natureza |
|---|---|---|---|
| `ad_platform` | str | coleta | real / público |
| `ad_count` | int | Ad Library | real |
| `advertiser_count` | int | Ad Library | real |
| `estimated_spend` | float \| None | estimativa | estimado |
| `active_days` | int | Ad Library | real |

## AdvertisingSignal
| Campo | Tipo | Origem | Natureza |
|---|---|---|---|
| `platform` | str | coleta | real |
| `has_active_ads` | bool | coleta | real |
| `ad_count_7d` | int \| None | coleta | real/ausente |
| `top_creatives` | tuple[str] | coleta | real |
| `advertiser_count` | int \| None | coleta | real/ausente |
| `collected_at` | float | sistema | real |

## TrendSnapshot
| Campo | Tipo | Origem | Natureza |
|---|---|---|---|
| `metric_name` | str | sistema | — |
| `value` | float | coleta | real / estimado |
| `period` | str | sistema | — |
| `source` | str | sistema | — |
| `confidence` | float | calculada | estimada |

## OfferScore
| Campo | Tipo | Origem | Natureza |
|---|---|---|---|
| `score_total` | float (0-100) | calculado | calculado |
| `components` | tuple[ScoreComponent] | calculado | calculado |
| `formula_version` | str | sistema | — |
| `explanation` | str | IA (futuro) | inferido |

## ScoreComponent
| Campo | Tipo | Origem | Natureza |
|---|---|---|---|
| `name` | str | sistema | — |
| `weight` | float | config | — |
| `value` | float | calculado | calculado |
| `raw_input` | Any | coleta | real / manual |
| `notes` | str | sistema | — |

## AIAnalysis
| Campo | Tipo | Origem | Natureza |
|---|---|---|---|
| `summary` | str | IA | inferido |
| `strengths` | tuple[str] | IA | inferido |
| `risks` | tuple[str] | IA | inferido |
| `recommendation` | str | IA | inferido |
| `confidence` | float | IA | inferido |
| `generated_at` | float | sistema | real |

## Comparison
| Campo | Tipo | Origem | Natureza |
|---|---|---|---|
| `offers` | tuple[UUID,...] | usuário | manual |
| `fields` | tuple[str] | sistema | — |
| `rankings` | dict | calculado | calculado |
| `best_overall` | UUID | calculado | calculado |
| `created_at` | float | sistema | real |

## MonitoringJob
| Campo | Tipo | Origem | Natureza |
|---|---|---|---|
| `job_id` | UUID | sistema | — |
| `source_type` | str | config | — |
| `filters` | dict | config | — |
| `interval_hours` | int | config | — |
| `last_run` | float \| None | sistema | real |
| `next_run` | float | sistema | calculado |
| `enabled` | bool | sistema | — |

## BusinessMetric (histórico)
| Campo | Tipo | Origem | Natureza | Histórico |
|---|---|---|---|---|
| `offer_id` | UUID | sistema | — | sim |
| `date` | str | sistema | real | sim |
| `clicks` | int | real | real | sim |
| `sales` | int | real | real | sim |
| `commission_brl` | float | real | real | sim |
| `cost_brl` | float | real | real | sim |
| `roi_percent` | float | calculado | calculado | sim |
| `source` | str | sistema | — | sim |
| `confidence` | float | calculada | estimada | sim |

---

# 7. Fontes de dados

| Fonte | Dado desejado | Situação conhecida | Autenticação | Custo | Limites | Armazenamento | Risco | Fallback manual |
|---|---|---|---|---|---|---|---|---|
| Google Ads API | CPC, concorrência, volume de busca por palavra-chave ou URL (KeywordPlanIdeaService) | API oficial disponível, mas requer developer token, OAuth e customer ID | OAuth 2.0 + developer token + Google Ads customer ID | REQUER PESQUISA OFICIAL — não declarar como gratuito sem confirmação | REQUER PESQUISA OFICIAL — quotas e regras precisam verificação | Sim, com timestamp | Médio — bloqueio de conta se mal usado | Cadastro manual de CPC, palavras-chave e concorrência |
| Google Trends | Tendência, volume relativo, crescimento | API oficial anunciada em 2025 em alpha/acesso limitado; pytrends é não oficial | Nenhuma para pytrends; API oficial requer acesso alpha | Gratuito para pytrends (sem garantia); REQUER PESQUISA OFICIAL para acesso comercial | REQUER PESQUISA OFICIAL | Sim, com data e source_label | Médio — pytrends não oficial, pode falhar ou ser bloqueado | Coleta manual de screenshot ou dados públicos |
| Meta Ad Library | Anúncios ativos, criativos, advertiser count | Interface pública e API oficial disponíveis | REQUER PESQUISA OFICIAL — não declarar que API não exige autenticação sem confirmação | Gratuito para dados públicos | REQUER PESQUISA OFICIAL — rate limits e termos de redistribuição | REQUER PESQUISA OFICIAL — termos de uso para armazenamento e redistribuição comercial | Médio — dado público, mas coleta em massa, armazenamento indefinido e redistribuição podem violar termos | Navegação manual no site da Ad Library |
| TikTok Creative Center | Anúncios, criativos criativos, trends | Interface pública disponível; Research API tem critérios institucionais — não tratar como fonte comercial | REQUER PESQUISA OFICIAL | REQUER PESQUISA OFICIAL | REQUER PESQUISA OFICIAL | REQUER PESQUISA OFICIAL | Alto — Research API não é base comercial; Creative Center é público mas sem API garantida | Coleta manual |
| Google Ads Transparency Center | Anúncios, anunciantes | Site público, sem API oficial | Nenhuma | Gratuito | REQUER PESQUISA OFICIAL | Sim (manual, com data) | Baixo — dado público, mas armazenamento e redistribuição REQUEREM PESQUISA OFICIAL | Navegação manual no site |
| ClickBank | Produtos, comissão, gravidade, EPC | API oficial disponível (Hoplink, Marketplace) | API key | Gratuito para afiliados | REQUER PESQUISA OFICIAL | Sim | Baixo | Marketplace público no site |
| Digistore24 | Produtos, comissão | API oficial disponível | API key | Gratuito para afiliados | REQUER PESQUISA OFICIAL | Sim | Baixo | Marketplace + página pública |
| Hotmart | Produtos, comissão, eventos de venda | Webhook já implementado e ativo; API oficial disponível | Client ID + Secret | Gratuito | REQUER PESQUISA OFICIAL | Sim (já armazenamos) | Já integrado e testado | Marketplace público |
| Braip | Produtos, comissão | API oficial disponível (token salvo localmente) | API key | Gratuito | Ainda não testado pela fábrica | Sim | Baixo | Marketplace público |
| Mercado Livre | Preço, seller, estoque, categoria | API oficial (adapter read-only já implementado) | OAuth | Gratuito para leitura | Já implementado no adapter | Sim (com timestamp) | Read-only já bloqueia escrita | Site público |
| Amazon | Preço, BSR, reviews, variações | API Product Advertising | Associados ID + assinatura | REQUER PESQUISA OFICIAL | REQUER PESQUISA OFICIAL | Sim | Baixo com API oficial | Site público |
| Similarweb | Tráfego estimado, bounce rate, países, palavras-chave, duração da visita | API oficial paga | API key | Pago — REQUER PESQUISA OFICIAL de licenciamento comercial | REQUER PESQUISA OFICIAL | Sim, com data | Médio — estimativa, não dado real; uso comercial pode exigir licença específica | Extensão navegador (gratuita limitada) |
| Semrush | CPC, palavras-chave, concorrência, tráfego | API oficial paga | API key | Caro (~$200/mês) — REQUER PESQUISA OFICIAL de licenciamento comercial | REQUER PESQUISA OFICIAL | Sim | Alto — custo elevado; uso comercial pode exigir licença específica | Manual / análise gratuita limitada |

---

# 8. Sistema inicial de pontuação

## Fórmula determinística versão 1.0 (0-100)

### Componentes e pesos

| Componente | Peso | Fonte | Descrição |
|---|---|---|---|
| `trend_growth` | 20 | Google Trends + histórico | Direção + velocidade do crescimento |
| `volume_absolute` | 10 | Google Trends / Keyword Planner | Volume absoluto de busca |
| `commission` | 18 | Programa de afiliados / plataforma | % de comissão + valor absoluto potencial |
| `trend_persistence` | 8 | Histórico de tendência (3+ meses) | Tendência sustentada vs. pico momentâneo |
| `ad_presence` | 12 | Meta Ad Library + Google Ads | Quantidade de anunciantes e anúncios ativos |
| `offer_quality` | 12 | Marketplace trust + reviews + rating + price band | Qualidade percebida da oferta |
| `affiliate_availability` | 8 | Programa aberto, cookie longo, link disponível | Facilidade de afiliação |
| `evidence_freshness` | 5 | Data da coleta | Penalidade progressiva por obsolescência |
| `evidence_confidence` | 5 | Média ponderada das confianças | Fontes oficiais pesam mais |
| `saturation_risk` | 0 a -8 | Nicho, concorrência, densidade de afiliados | Penalidade por saturação |
| `policy_risk` | 0 a -10 | Análise de compliance/vertical | Penalidade por nicho restrito (saúde, finanças) |

### Penalidades

| Condição | Penalidade |
|---|---|
| Nicho saturado (muitos afiliados mesmas ofertas) | -3 a -8 |
| Nicho de alto risco (saúde, finanças, suplementos) | -5 a -15 |
| Evidência ausente por componente | -3 por componente |
| Dados desatualizados (>30 dias) | -2 |
| Dados desatualizados (>90 dias) | -5 |
| Sem link de afiliado disponível | -5 |

### Dados ausentes

Se um componente não tem dado, usa:
- média do dataset atual (se houver histórico);
- ou valor conservador padrão:
  - `trend_growth`: 6/20
  - `volume_absolute`: 3/10
  - `commission`: 9/18 (50% do peso)
  - `ad_presence`: 0/12
- O ScoreComponent deve marcar `data_available: false` e incluir nota explicativa.

### Baixa confiança

Se a confiança de uma evidência for < 0.5, o componente entra com 50% do peso máximo. O score final carrega `overall_confidence: low / medium / high`.

### Classificação final

| Faixa | Rótulo | Significado |
|---|---|---|
| 80-100 | strong_test | Oferta com sinais fortes; priorizar produção |
| 60-79 | promising | Sinais positivos; revisar evidências ausentes |
| 40-59 | needs_review | Dados insuficientes ou mistos |
| 20-39 | weak | Poucos sinais positivos |
| 0-19 | skip | Riscos altos ou dados muito fracos |

### Exemplo fictício

**Produto:** Fone Bluetooth XYZ na Amazon (R$ 189,90)

| Componente | Valor | Peso máximo | Score | Fonte | Confiança |
|---|---|---|---|---|---|
| `trend_growth` | crescimento forte 6m | 20 | 16 | Google Trends | alta |
| `volume_absolute` | busca alta | 10 | 7 | Trends | alta |
| `commission` | 6% + R$11,39 | 18 | 14 | Amazon Assoc. | alta |
| `trend_persistence` | 3+ meses subindo | 8 | 6 | Trends | média |
| `ad_presence` | 2 anunciantes Meta | 12 | 6 | Ad Library | média |
| `offer_quality` | trust 0.92, 4.5★, <2% refund | 12 | 9 | Amazon/ML | alta |
| `affiliate_availability` | link direto, cookie 24h | 8 | 8 | manual | alta |
| `evidence_freshness` | <7 dias | 5 | 5 | sistema | — |
| `evidence_confidence` | fontes oficiais+ | 5 | 4 | calculada | — |
| `saturation_risk` | concorrência média | 0 a -8 | -3 | inferido | média |
| `policy_risk` | eletrônicos | 0 a -10 | 0 | inferido | alta |

**Score total:** 16+7+14+6+6+9+8+5+4-3-0 = **72/100 → "promising"**

**Explicação da IA (futura):**
> "O fone XYZ mostra tendência de crescimento consistente e boa comissão. A presença de anúncios é moderada (2 concorrentes). O risco é baixo por ser eletrônico. Recomenda-se teste com criativo comparativo destacando preço vs. concorrentes."

---

# 9. Fases de desenvolvimento

| Fase | Objetivo | Responsável | Dependências | Risco | Critério de conclusão |
|---|---|---|---|---|---|
| 1 | Documentação da proposta | DeepSeek | Nenhuma | Nenhum | Documento aceito por Leandro |
| 2 | Protótipo isolado com dados MOCK | DeepSeek | Fase 1 | Nenhum | demo.py roda sem core/ com 15+ assertions |
| 3 | Modelos e score no core | Codex | Fase 2 | Baixo (aditivo) | compileall + demo 20+ assertions |
| 4 | Comparador | Codex | Fase 3 | Baixo | Comparação de 3 ofertas funcional |
| 5 | Coleta simulada de fontes | DeepSeek / Codex | Fase 3 | Baixo | Coleta mock → score pipeline |
| 6 | Revisão do Codex + regressão | Codex | Fases 3-5 | Médio (mudança em core/) | 114/114 demos, compileall |
| 7 | Fontes reais (Trends, Ad Library) | Codex | Fase 5 + pesquisa oficial de API | Médio-alto (API/custo) | MOCK + REAL smoke (opt-in) |
| 8 | Dashboard (Radar, Detalhe, Comparador) | Codex | Fases 6-7 | Médio (UI) | Telas funcionais com dados MOCK |
| 9 | Monitoramento + Alertas | Codex | Fase 7 | Médio | Job periódico + notificação |
| 10 | Métricas de ROI + aprendizado | Codex + Leandro | Fase 7 + vendas reais | Alto (financeiro) | ROI real alimentando score |
| 11 | SaaS + planos pagos | Codex + Leandro | Fases 8-10 | Alto (produto/comercial) | Plano gratuito + pago operacional |

---

# 10. Percentuais corretos

| Camada | Estimativa | Significado |
|---|---|---|
| Infraestrutura reutilizável (core, approval, qualidade, persistência, dashboard, workers, bridges, observabilidade, provider control) | 45-55% | Base sólida, mas precisa de adaptações |
| Motor específico de Offer Intelligence (models, scoring, comparator, pipeline) | 10-15% | Ainda não implementado; documentado e prototipável |
| Fontes externas reais (Google Trends, Meta Ad Library, Google Ads, etc.) | 5-10% | Depende de pesquisa oficial de API; algumas podem ser inviáveis |
| Interface SaaS (dashboard, radar, comparador, IA explanation, assinatura, landing page) | 0-5% | Nada implementado; completamente por construir |
| Produto comercial completo (plano gratuito + pago, landing page, checkout, billing, onboarding) | 0% | Futuro distante |

**Estas são estimativas de planejamento, não métricas de teste.**

---

# 11. Riscos

| Risco | Categoria | Probabilidade | Impacto | Mitigação |
|---|---|---|---|---|
| Google Trends API alpha não se tornar comercial | API | Alta | Alto | Fallback para pytrends (não oficial, pode falhar); ou coleta manual |
| Google Ads API muito cara | Financeiro | Média | Alto | Pesquisa oficial antes de implementar; começar com MOCK |
| Meta Ad Library API mudar termos | Legal/API | Média | Médio | Armazenar com timestamp; preparar fallback manual |
| TikTok Creative Center sem API comercial | API | Alta | Médio | Fonter apenas manual; não depender como fonte crítica |
| Similarweb/Semrush precisarem de licença paga | Financeiro | Alta | Médio | Não incluir no MVP; fontes gratuitas primeiro |
| Dados estimados serem confundidos com reais | Produto | Média | Alto | Sempre marcar source_type e confidence; UI clara |
| Dependência de fornecedor único (ex: só Google Trends) | Técnico | Baixa | Médio | Múltiplas fontes desde o início |
| Duplicidade de ofertas (mesmo produto em plataformas diferentes) | Dados | Alta | Baixo | OfferIdentity + hash de URL; merge manual |
| Classificação incorreta de nicho | Dados | Média | Baixo | Score usa dados, não dependência de nicho |
| LLM inventar conclusões na explicação | IA | Média | Médio | Score é determinístico; IA só explica; revisão humana |
| Promessas financeiras na interface | Legal/Produto | Média | Alto | Bloqueado por design: score diz "strong_test" não "ganhe dinheiro" |
| Saturação de oferta não detectada | Dados | Média | Médio | Score inclui penalidade; usuário decide |
| Política de anúncios mudar (Meta, Google) | Legal | Média | Alto | Monitorar termos; fallback manual |
| Vazamento de URL ou dados de oferta | Privacidade | Baixa | Médio | Dados públicos; sem PII; sem credenciais |
| Custo de infraestrutura (servidor, banco, workers) | Financeiro | Baixa | Baixo | MVP roda local; SaaS exigirá avaliação |

---

# 12. Decisões pendentes do proprietário

## Decisões obrigatórias agora
- Offer Intelligence deve ser domínio separado (`core/offer_intelligence/`) + departamento fino, ou apenas departamento?
- A primeira fonte real deve ser Google Trends (gratuito/público, mas pytrends não oficial) ou Meta Ad Library (API pública, mas termos pendentes)?
- O protótipo MOCK deve usar nomes de produtos reais (ex: fone XYZ) ou genéricos (Produto A, B, C)?

## Decisões que podem esperar
- Nome final do produto (OfferScope? OfferRadar? OfferFlow? OfferSense?)
- Precificação do plano pago
- Landing page pública
- Marca e identidade visual

## Decisões financeiras
- Orçamento disponível para APIs pagas (Google Ads, Similarweb, Semrush)?
- Disposição para pagar por fontes de dados terceiras?
- Investimento inicial em infraestrutura de SaaS?

## Decisões de produto
- Até onde vai o "Ads Spy"? Apenas Meta Ad Library pública ou inclui estimativas de gasto?
- Análise por IA: Kokoro (TTS, não LLM) não serve. Usar LLM local (qual?) ou API paga (OpenAI, Claude)?
- Monitoramento diário: manual (trigger do usuário) ou automático (job agendado)?

## Decisões legais/compliance
- Podemos armazenar dados da Meta Ad Library por quanto tempo?
- Podemos redistribuir dados de anúncios públicos comercialmente?
- Precisamos de termos de uso específicos para a ferramenta Offer Intelligence?

## Decisões sobre APIs
- Google Ads API: solicitar developer token agora ou esperar?
- Google Trends: tentar acesso ao alpha oficial ou usar pytrends como experimento isolado?
- TikTok: há alguma API comercial para Creative Center no Brasil?

## Decisões sobre marca
- Offer Intelligence é o nome provisório ou pode ser o definitivo?
- A marca deve ser separada da AI Content Factory ou sub-marca?

## Decisões sobre dashboard
- Offer Intelligence terá dashboard separado ou abas dentro do factory_dashboard existente?
- O radar de ofertas deve ser visualização local (HTML estático) ou no dashboard hospedado (D1/Next.js)?

## Decisões sobre IA
- Qual LLM será usado para a explicação? (requer integração futura com LLM Gateway / OmniRoute?)
- A explicação será gerada online (cada consulta) ou em batch (pré-calculada na coleta)?

---

# 13. Segurança do repositório

- O repositório local (`main`) possui **14 arquivos modificados** e **28 arquivos não rastreados** (conforme git status em 16/07/2026).
- Existem mudanças do Codex ainda não commitadas (último commit `69dffe0` — "fix(telegram): expire stale affiliate offers").
- O DeepSeek **não tocou e não tocará** em: `core/`, `apps/`, `demo_*.py`, `scripts/`, `AGENTS.md`, `.openai/`, providers, adapters, secrets, outputs.
- **Nenhuma alteração de produção deve ocorrer antes de checkpoint (git status, git diff, git stash se necessário) e revisão do Codex.**
- O DeepSeek deve ser explicitamente autorizado antes de qualquer alteração em arquivos não-listados como permitidos no protocolo.

---

# 14. Status

**Status:** PROPOSTA - NAO IMPLEMENTADA

**Origem estratégica:** GPT da Web, trabalhando em conversa com Leandro Vieira

**Executor documental desta fase:** DeepSeek, exclusivamente dentro do workspace seguro

**Revisor e integrador esperado:** Codex, responsável por validar arquitetura, contratos, testes, regressão e integração oficial

**Arquivos criados nesta missão:**
- `docs/external_llm_inbox/deepseek/ideas/2026-07-16_offer_intelligence.md` (este)
- `docs/external_llm_inbox/deepseek/ideas/2026-07-16_offer_intelligence_CODEX_HANDOFF.md`
- Atualizados: `INDEX.md`, `HANDOFF_CHECKLIST.md`
