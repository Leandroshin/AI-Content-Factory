# Proposta: Pipeline Completo de Afiliado Internacional (ClickBank + Google Ads)

Status: PROPOSTA - NAO IMPLEMENTADA
Data: 2026-07-15
Fontes: 3 transcricoes de YouTube (tactiq) sobre afiliado na gringa

---

## CAMADA 1 — Proposta Inicial

### One-Sentence Idea
Automatizar todo o funil de afiliado internacional: funcionarios da fabrica varrem diariamente ClickBank/BuyGoods/MaxWeb em busca de produtos em alta (curva Google Trends subindo), apresentam oportunidades ranqueadas para aprovacao humana e, uma vez aprovado, geram landing page persuasiva + campanha de Google Ads — tudo dentro da arquitetura ja existente, sem chamada paga no MVP.

### Why It Fits
- Ja temos 6/8 pecas do quebra-cabeca (veja Arvore de Dependencia)
- AffiliateDealsEmployee ja faz score, compliance e copy
- ProductResearchEmployee ja faz shortlist de candidatos
- ProductUrlIntake ja extrai dados de URLs
- HITL Gateway ja existe para aprovacao
- O que falta e a ponta "pesquisa ativa + landing page + ads" — que e justamente o core do video

### User Value
- Shin nao precisa mais passar horas garimpando ClickBank
- O retorno e um ranking diario pronto: "esses 5 produtos estao subindo, comissao X, trends Y, recomendacao Z"
- Ao escolher um, a fabrica gera landing page + estrutura de campanha em minutos (MOCK) e, com aprovacao e budget, publica ads de verdade (REAL)

### MVP Scope (Zero Gasto)
1. **TrendScanner** — rotina diaria MOCK que simula varredura de ClickBank + Google Trends
2. **ProductBrief** — output estruturado com nome, comissao, curva, link de afiliado, gravidade
3. **LandingPageAdapter** — gera HTML estatico (como Flow Pages faz) com copy persuasiva
4. **GoogleAdsCampaignBuilder** — monta estrutura de campanha (palavra, CPA, local, rede) em formato exportavel
5. **Integracao com HITL** — Shin aprova antes de qualquer acao

### Later Integrations (Nivel Pago)
1. **ClickBank API real** — pegar produtos, comissoes, gravidade ao vivo
2. **Google Trends API real** — curva de pesquisa ao vivo
3. **Flow Spy / Semrush API** — dados profundos de trafego
4. **Google Ads API real** — publicar campanha de verdade (requer cartao + aprovacao)
5. **Landing page hosted** — publicar em subdominio proprio com dominio .com

---

## CAMADA 2 — Arvore de Dependencia

```
N0 - CONCEITO
    Shin quer: funcionarios pesquisam produtos → landing page → ads → venda
    Existe? NAO como pipeline integrado. Existem pecas soltas.

N1 - PRODUTO EM ALTA (TrendScanner)
    ├── O que faz: varre ClickBank/BuyGoods/MaxWeb em busca de produtos subindo
    ├── Dados que precisa:
    │     Nome do produto, comissao, preco, link de afiliado, gravidade (ClickBank)
    │     Google Trends (curva 30-90 dias: subindo, estavel, caindo)
    │     Tipo (digital, nutraceutico, ecommerce)
    │     Paises de entrega (US, CA, AU, UK — os que vendem)
    ├── [OK] ProductResearchEmployee ja existe — mas ele recebe candidatos,
    │     nao pesquisa ativamente. Precisa de um "ProductHunterEmployee" novo
    │     ou estender ProductResearchEmployee com metodo de varredura.
    ├── [$] ClickBank API: gratuita para afiliados cadastrados
    │     https://support.clickbank.com/hc/en-us/articles/220346807-ClickBank-API-Overview
    ├── [$] Google Trends: gratuita (pode ser via feed RSS ou selenium)
    ├── [?] DECISAO: Shin quer dados MOCK (dados de exemplo) ou REAL?
    │     MVP: MOCK — dados deterministicos baseados nos produtos dos videos
    │     (ProstaVive, Prodentin, BrainSong, Matsato, Ignatra, Menes Rescui)
    └── [risco] ClickBank pode bloquear scraping automatizado → usar API oficial

N2 - SELECAO HUMANA
    ├── O que faz: Shin (ou Codex) escolhe 1-3 produtos da lista para produzir
    ├── [OK] HITL Approval Gateway ja existe → pode reusar
    ├── [OK] AffiliateDealsEmployee ja faz score por produto
    ├── Formato: lista diaria no dashboard ou no Telegram
    └── [?] DECISAO: notificar por Telegram? Ja temos TelegramAdapter

N3 - LANDING PAGE (o "entre" o ads e o produto)
    ├── O que faz: gera HTML de pagina intermediaria que:
    │     - Simula pagina legitima (aceite de cookies, design limpo)
    │     - Tem copy persuasiva (dor, solucao, beneficios, CTA)
    │     - Contem link de afiliado que leva ao checkout do produto
    │     - Passa no criterio do Google Ads (nao e link direto de afiliado)
    ├── [OK] ScriptDepartment ja gera copy, hook, CTA
    ├── [OK] AffiliateDealsFormatter ja gera copy estilo Telegram
    ├── [OK] ImageDepartment ja gera assets visuais (PNG para capa)
    ├── [NOVO] LandingPageBuilder — adapter que:
    │     MOCK: gera HTML estatico em output/landing_pages/<produto>/index.html
    │     REAL: hospeda em VPS/dominio proprio (futuro)
    ├── Template: pagina "fundo de funil" — focada no nome do produto
    │     (ex: "ProstaVive" → pesquisa quem busca "ProstaVive")
    ├── Elementos obrigatorios:
    │     - Headline com o nome do produto
    │     - Subheadline com o problema que ele resolve
    │     - Bullet points de beneficios
    │     - CTA claro ("Compre Agora", "Acesse o Site Oficial")
    │     - Popup de cookies (para marcar cookie de afiliado)
    │     - Disclosure de afiliado (ja temos em compliance.py)
    │     - Responsivo (mobile-first)
    │     - Meta tags basicas (title, description, robots)
    └── [risco] Google Ads exige que a pagina tenha conteudo real,
          nao so um redirect. O template precisa ser legitimo.

N4 - CAMPANHA GOOGLE ADS
    ├── O que faz: gera estrutura de campanha que Shin pode copiar para o Google Ads
    ├── Configuracoes (dos videos):
    │     Rede: so pesquisa (desligar display)
    │     Local: Estados Unidos (presenca), Canada, Australia, Reino Unido
    │     Idioma: todos os idiomas
    │     Palavra-chave: correspondencia de FRASE (aspas)
    │     "prosta vive" — nao ampla, nao exata
    │     Lance: CPA desejado = ~50% da comissao
    │     Orcamento: diario pequeno (ex: $20/dia)
    │     Anuncio: titulos + descricoes gerados pela landing page copy
    ├── [NOVO] GoogleAdsCampaignGenerator — adapter que:
    │     MOCK: gera JSON/CSV com estrutura completa para importar
    │     REAL: futuramente usa Google Ads API
    ├── Metricas para Shin acompanhar:
    │     Gasto diario, clicks, conversoes, CPA, receita, ROI
    └── [$$$] Google Ads REAL requer cartao de credito + orcamento
          MVP: gera arquivo .csv pronto para importar na conta Google

N5 - ANALISE E CORTE
    ├── O que faz: monitora performance e para campanha que nao vende
    ├── Regra dos videos: se gastou 70-80% da comissao e nao vendeu, corta
    ├── [NOVO] CampaignAnalytics — compara gasto vs conversoes
    ├── [OK] QualityRuntime pode ser adaptado para regras de campanha
    └── [?] DECISAO: corte automatico ou so alerta?

N6 - PERSISTENCIA E MEMORIA
    ├── [OK] PersistenceRuntime (ExecutionRecord, CompanySnapshot)
    ├── [OK] OrganizationalMemoryRuntime (versao de cada campanha)
    └── Dados a persistir: produtos escolhidos, landing pages geradas,
          campanhas rodando, gasto diario, comissoes

N7 - DASHBOARD
    ├── [OK] Factory Dashboard V2 ja existe
    ├── [OK] Provider Panel UI existente
    ├── [NOVO] Nova aba/area no dashboard: "Afiliado Gringa"
    │     - Produtos do dia (TrendScanner output)
    │     - Landing pages geradas
    │     - Status das campanhas
    │     - Gasto vs receita
    └── [OK] TelegramAdapter pode notificar diariamente

N8 - PAGO / REAL (so depois do MVP)
    ├── ClickBank API real → dados reais de produtos
    ├── Google Trends API real → graficos reais
    ├── Google Ads API real → publicar campanha de verdade
    │     Custo: variavel ($20-$100/dia para testar 1 produto)
    ├── Dominio + VPS → hospedar landing pages
    │     Custo: ~R$40/mes Hostinger VPS (como o video falou)
    └── Flow Spy / Semrush → dados profundos de concorrencia
          Custo: ~$30-50/mes

AUTO-CRITICA (o que eu nao pensei):
    ? A landing page precisa de um dominio proprio (nao pode ser subdominio
      gratuito). Google Ads nao aceita links de afiliado direto nem sites
      gratuitos. Shin precisa de pelo menos 1 dominio .com ou .net.
    ? O cookie de afiliado tem prazo de validade. ClickBank: 60 dias.
      Se a pessoa clica e compra 2 meses depois, ainda comissiona.
      Mas se trocar de navegador, perde.
    ? Google Ads pode rejeitar a landing page se achar que e "bridge page"
      (pagina intermediaria sem valor). O template precisa ter conteudo
      suficiente — nao pode ser so um botao de "compre aqui".
    ? CPA de 50% da comissao e uma REGRA dos videos, mas na pratica o
      Google pode gastar mais se a campanha nao tiver historico.
      Precisa de CPAn tambem (custo por acao — nao conversao).
    ? Palavra-chave em frase ainda pode mostrar para termos relacionados.
      Precisa de palavras negativas para evitar "gratis", "review",
      "Amazon", "Walmart" — senao o Google gasta com busca de quem
      nao quer comprar.
    ? Vendedores brasileiros acessando ClickBank como afiliados poluem
      o Google Trends. O video 3 mencionou isso — trafego do Brasil
      muitas vezes e de afiliados pesquisando, nao de compradores.
      Nosso TrendScanner precisa filtrar isso.
    ? A fabrica hoje nao tem acesso a dados reais de conversao.
      Sem Pixel do Google Ads ou checkout proprio, nao sabemos se
      a venda realmente aconteceu. O ROI seria estimado.
    ? O que acontece se 2 afiliados brasileiros usam a MESMA landing page
      template para o MESMO produto? Google pode entender como spam.
    ? Shin precisa de uma conta Google Ads configurada com metodo de
      pagamento internacional (USD). Nem todo cartao brasileiro passa.
      Alternativa: conta Google Ads Brasil (anuncia em BRL) mas o
      publico-alvo e americano — o CPC pode ser diferente.
    ? FTC disclosure: afiliados nos EUA sao obrigados por lei a declarar
      que ganham comissao. Nossa compliance ja faz isso, mas o Google
      Ads pode exigir que o disclosure esteja visivel sem precisar
      rolar a pagina.
```

---

## CAMADA 3 — Riscos e Auto-Critica

### O que eu (DeepSeek) posso ter deixado passar:

1. **Ciclo de aprendizado do Google Ads.** Toda campanha nova passa por "learning phase" — o Google testa e gasta sem necessariamente converter. Shin pode perder $50-$100 nos primeiros dias antes de qualquer venda. Isso e normal, mas precisa estar claro.

2. **Pixel de conversao.** O video nao menciona explicitamente como o Google sabe que uma venda aconteceu. Na pratica, o afiliado ou usa o Pixel do proprio produto (quando o vendor fornece) ou confia no relatorio do ClickBank (que tem delay de horas/dias). Nossa pipeline MOCK nao tem como simular isso com precisao.

3. **Problema de multiple accounts.** ClickBank paga comissao para o ULTIMO afiliado que indicou. Se Shin cria campanha e outro afiliado brasileiro tambem anuncia o mesmo produto, quem levou o cliente? O ClickBank atribui ao ultimo cookie. Isso pode gerar "briga de afiliado" onde Shin paga pelo clique e outro afiliado leva a venda.

4. **Horario de lances.** O video 1 mostrou que produtos americanos convertem melhor em horario comercial dos EUA (9AM-5PM EST, que e 10PM-6AM BRT). Shin precisaria ajustar schedule de campanha — algo que nao existe hoje na fabrica.

5. **Produtos sazonais.** O TrendScanner precisa entender sazonalidade. Produto de emagrecimento sobe em janeiro (resolucao de ano novo) e cai em marco. Nosso scanner pode mostrar como "alta" algo que e simplesmente sazonal — e Shin compra na alta e vende na queda.

6. **Fraude de clique.** Concorrentes podem clicar nos anuncios de Shin para gastar o orcamento dele. O Google Ads tem protecao automatica, mas nao e 100%.

### O que so Shin/Codex pode decidir:

| Decisao | Impacto |
|---|---|
| Shin quer MOCK total (nunca gastar) ou REAL com budget controlado? | Define se o GoogleAdsAdapter sera so gerador de CSV ou se tera API real |
| Shin ja tem conta Google Ads? Cartao internacional? | Sem isso, REAL e impossivel |
| Shin quer dominio proprio (.com) para landing pages? | Hostinger VPS como o video sugeriu (~R$40/mes) |
| Quem opera as campanhas: Shin ou a fabrica pode ajustar lances? | Seguranca vs automatizacao |
| Shin quer notificacao diaria no Telegram com as oportunidades? | Fazer ou nao o push |
| Produtos do Brasil (Hotmart/Kiwify) entram ou so gringa? | Escopo aumenta |

---

## CAMADA 4 — Caminho Critico

### Ordem de construcao

```
FASE 1 — TRENDSCANNER MOCK (2-3 dias de implementacao)
    Importancia: ALTA — desbloqueia todo o resto
    Entrega: todo dia uma lista de 5-10 produtos "ficticios mas realistas"
    com nome, comissao, link, curva de trends, gravidade
    Nao precisa de API externa, so dados deterministicos

FASE 2 — LANDING PAGE BUILDER (2-3 dias)
    Importancia: ALTA — sem landing page, Google Ads nao aceita
    Entrega: HTML responsivo com template "fundo de funil"
    Consome copy do ScriptDepartment + assets do ImageDepartment
    Salva em output/landing_pages/<produto>/

FASE 3 — GOOGLE ADS CAMPAIGN GENERATOR (1-2 dias)
    Importancia: MEDIA — so faz sentido depois da landing page
    Entrega: JSON/CSV exportavel com estrutura de campanha
    Shin copia manualmente para o Google Ads (MOCK)
    Nao ha gasto real

FASE 4 — INTEGRACAO COM HITL + DASHBOARD (2 dias)
    Importancia: MEDIA — Shin precisa de um lugar para ver e aprovar
    Entrega: nova aba no dashboard com produtos do dia + acao

FASE 5 — NOTIFICACAO TELEGRAM (1 dia)
    Importancia: BAIXA — conveniencia, nao essencial
    Entrega: todo dia as 9AM, o robô envia top 3 oportunidades

FASE 6 — PRODUTOS REAIS (ClickBank API) (2-3 dias)
    Importancia: MEDIA — transforma MOCK em dados reais
    Requer: conta ClickBank + API key
    Risco: documentacao da API ClickBank pode estar desatualizada

FASE 7 — GOOGLE ADS REAL (so quando Shin decidir gastar)
    Importancia: depende de Shin
    Requer: cartao internacional + conta Google Ads + dominios
    Risco FINANCEIRO: $20-$100/dia por produto testado
```

### Mapa de dependencias entre fases:
```
FASE 1 ──> FASE 2 ──> FASE 3 ──> FASE 4
  │                                          
  └──> FASE 5 (pode ser paralela)           
                                            
FASE 6 ──> FASE 7 (so com dinheiro real)
```

### Recomendacao sincera:
Faca Fase 1 + 2 primeiro. So isso ja da para Shin entender o fluxo completo, ver as landing pages no navegador e decidir se quer prosseguir para gasto real. Fase 3 e 4 sao consequencia natural.

---

## DETALHAMENTO TECNICO: Componentes a Construir

### 1. ProductHunterEmployee (`core/departments/product_hunter/`)

**Herda:** `ProductionEmployee` (→ `SpecialistEmployee`)

**Responsabilidade:** Varrer plataformas de afiliado e Google Trends para encontrar produtos em alta.

**Pipeline (6 stages):**
```
CREATED → SCANNING_PLATFORMS → CHECKING_TRENDS → SCORING_OPPORTUNITIES →
RANKING_AND_FILTERING → DELIVERING_REPORT → COMPLETED
```

**Stage handlers:**
1. `SCANNING_PLATFORMS` — itera sobre ClickBank, BuyGoods, MaxWeb (MOCK: dados pre-definidos; REAL: API)
2. `CHECKING_TRENDS` — para cada produto, consulta Google Trends (MOCK: curva simulada; REAL: Trends API)
3. `SCORING_OPPORTUNITIES` — score por: comissao (0-25), crescimento trends (0-25), volume de busca (0-20), gravidade (0-15), risco de saturacao (-35)
4. `RANKING_AND_FILTERING` — ordena por score, remove produtos em queda ou com volume irrelevante
5. `DELIVERING_REPORT` — gera relatorio estruturado com top 5-10 oportunidades

**Output:** `HunterReport` — lista de `ProductOpportunity` com nome, comissao, link afiliado, curva trends, score, recomendacao ("hot", "warm", "cold")

**Dados MOCK (baseados nos videos):**

| Produto | Plataforma | Comissao | Trends 30d | Gravidade | Score | Recomendacao |
|---|---|---|---|---|---|---|
| ProstaVive | ClickBank | $175.60 | Subindo (+25%) | 175.43 | 89 | hot |
| Ignatra | ClickBank | $180.00 | Subindo (+17%) | 142.18 | 85 | hot |
| Prodentin | ClickBank | $140.00 | Subindo (+8%) | 188.45 | 72 | warm |
| Matsato (faca) | BuyGoods | $70.00 | Estavel (-2%) | 45.20 | 55 | warm |
| BrainSong | ClickBank | $200.00 | Caindo (-30%) | 220.10 | 40 | cold |
| Menes Rescui | MaxWeb | $166.00 | Crescendo baixo (+5%) | 18.30 | 38 | cold |

### 2. LandingPageBuilderAdapter (`core/tools/adapters/landing_page_adapter.py`)

**Extends:** `AbstractToolAdapter`

**Responsabilidade:** Gerar HTML de landing page persuasiva para produto afiliado.

**Metodo principal:**
```python
def build_landing_page(
    product_name: str,
    affiliate_link: str,
    commission: float,
    product_type: str,  # "digital", "nutraceutical", "ecommerce"
    benefits: list[str],
    target_countries: list[str],
    output_dir: str | None = None,
) -> LandingPageResult:
```

**MOCK:** Gera HTML completo em `output/landing_pages/<product_name_slug>/index.html`
**REAL:** (futuro) Publica em VPS via FTP/SSH

**Template de landing page (estilo "fundo de funil"):**
```html
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{product_name} — Official Website</title>
    <meta name="description" content="{meta_description}">
    <!-- Cookie consent popup -->
</head>
<body>
    <!-- Cookie popup: "This site uses cookies. Accept?" -->
    <!-- Na verdade, ao clicar em "Accept", dispara o cookie de afiliado -->
    
    <!-- Hero section -->
    <h1>{product_name} — {headline_dor}</h1>
    <p>{subheadline}</p>
    
    <!-- Benefits section -->
    <ul>
        {benefits_html}
    </ul>
    
    <!-- CTA -->
    <a href="{affiliate_link}" rel="sponsored">
        Visit Official Website
    </a>
    
    <!-- Disclosure -->
    <p class="disclosure">
        We may earn a commission if you purchase through our links.
    </p>
    
    <!-- Footer -->
    <p>&copy; 2026 {site_name}. All rights reserved.</p>
</body>
</html>
```

### 3. GoogleAdsCampaignAdapter (`core/tools/adapters/google_ads_adapter.py`)

**Extends:** `AbstractToolAdapter`

**Responsabilidade:** Gerar estrutura exportavel de campanha Google Ads.

**Configuracoes (dos videos):**
```python
CAMPAIGN_CONFIG = {
    "campaign_type": "search",
    "network": "search_only",  # desligar display
    "locations": ["US", "CA", "AU", "GB"],  # presencia
    "languages": ["all"],
    "keyword_match": "phrase",  # "prosta vive" (com aspas)
    "bidding": "target_cpa",
    "cpa_target_percent": 0.50,  # 50% da comissao
    "budget_daily": 20.00,  # USD
    "ad_format": {
        "headlines": ["{product_name} Official", "Try {product_name} Today"],
        "descriptions": ["{benefit_1}", "{benefit_2}"],
    }
}
```

**MOCK output:** Gera arquivo `output/campaigns/<produto>/google_ads_campaign.json` com estrutura completa que Shin pode copiar para o Google Ads.

### 4. Integracao com o Workflow Existente

```python
# Novo workflow: AffiliateGringaWorkflow
# Extende ou substitui o AffiliateCommerceWorkflow para foco internacional

class AffiliateGringaWorkflow:
    def __init__(self):
        self.hunter = ProductHunterEmployee(company_runtime)
        self.landing_builder = LandingPageBuilderAdapter()
        self.ads_builder = GoogleAdsCampaignAdapter()
        self.deals = AffiliateDealsEmployee(company_runtime)
        self.approval = HITLApprovalGateway(...)
    
    def run_daily_scan(self) -> HunterReport:
        """Roda todo dia automaticamente"""
        return self.hunter.execute_task(...)
    
    def run_product_pipeline(self, opportunity_id: str):
        """Quando Shin escolhe um produto"""
        # 1. Landing page
        lp = self.landing_builder.build_landing_page(...)
        
        # 2. Copy + compliance (reusa AffiliateDealsEmployee)
        deal = self.deals.execute_task(...)
        
        # 3. Campaign structure
        campaign = self.ads_builder.build_campaign(...)
        
        # 4. HITL approval
        approval = self.approval.create_request(...)
        
        return GringaCampaignPackage(...)
```

### 5. Employee Propostos

| Employee | Arquivo | Herda | Pipeline |
|---|---|---|---|
| `ProductHunterEmployee` | `core/departments/product_hunter/` | `ProductionEmployee` | 6 stages |
| (reuso) `ScriptWriterEmployee` | ja existe | — | para copy da landing page |
| (reuso) `AffiliateDealsEmployee` | ja existe | — | compliance + disclosure |
| (reuso) `ImageDesignerEmployee` | ja existe | — | imagem de hero/banner |

### 6. Capabilities Necessarias

| Capability | Employee | Ja existe? |
|---|---|---|
| `web_search` | ProductHunter | Sim |
| `browser_automation` | ProductHunter (para Trends) | Sim |
| `text_generation` | LandingPage (via Script) | Sim |
| `image_editing` | LandingPage (via Image) | Sim |
| `document_generation` | GoogleAdsCampaign | Sim |
| `social_media` | (futuro) | Sim |
| `storage` | LandingPage (salvar HTML) | Sim |

### 7. Persistencia e Estado

O que salvar a cada execucao:
```python
@dataclass(frozen=True, slots=True)
class ProductOpportunity:
    id: str  # uuid
    product_name: str
    platform: str  # "clickbank", "buygoods", "maxweb"
    commission_usd: float
    product_price_usd: float
    affiliate_link: str
    trends_curve: str  # "rising", "stable", "falling"
    trends_percent_30d: float
    gravity_score: float
    total_score: float
    recommendation: str  # "hot", "warm", "cold"

@dataclass(frozen=True, slots=True)
class HunterReport:
    date: str
    products: tuple[ProductOpportunity, ...]
    total_scanned: int
    hot_count: int
    warm_count: int
    cold_count: int

@dataclass(frozen=True, slots=True)
class LandingPageResult:
    product_name: str
    html_path: str  # caminho do arquivo HTML gerado
    preview_url: str  # "file:///..." para abrir no navegador
    styles_inline: bool
    
@dataclass(frozen=True, slots=True)
class CampaignPackage:
    product_name: str
    landing_page: LandingPageResult
    campaign_json: dict
    approval_status: str  # "pending", "approved", "rejected"
```

---

## REFERENCIA CRUZADA: O Que Cada Video Ensina

### Video 1 — Ex-Uber R$4M (HNgMXUNsEi8)
| Ensinamento | Como a Fabrica Implementa |
|---|---|
| ClickBank + BuyGoods como plataformas | ProductHunterEmployee.scan_platforms() |
| Google Trends para escolher produto | ProductHunterEmployee.check_trends() |
| Comissao media de 50% do preco | Scoring commission_weight = 0.50 |
| Fundo de funil (anunciar nome do produto) | LandingPageBuilder template "fundo de funil" |
| Flow Pages para landing page | LandingPageBuilderAdapter gera HTML |
| CPA = 50% da comissao | GoogleAdsCampaignAdapter.cpa_target_percent |
| Rede de pesquisa + frase match | Configuracoes de campanha |
| Estados Unidos + Canada + Australia + UK | target_countries fixo |
| Nao usar Imax, nao usar palavra ampla | Regras no config |
| Organizacao diaria: analisar primeiro | Relatorio diario antes de criar novo produto |
| Corte rapido: 70-80% da comissao sem venda | CampaignAnalytics com regra QualityRuntime |

### Video 2 — Claude +R$100k/mes (WmhRp1aAuwk)
| Ensinamento | Como a Fabrica Implementa |
|---|---|
| Skills do Claude = prompts reutilizaveis | Skills.js — ja temos no AGENTS.md como conceito |
| Claude Code = agente autonomo VPS | Pode usar nosso ContentFactoryWorkflow |
| Sistema viral monitor (YouTube → Telegram) | Ja temos GamingDashboardBridge como template |
| Geracao de pagina com IA (contexto + copy) | LandingPageBuilder + ScriptWriterEmployee |
| Projetos do Claude = memoria de contexto | OrganizationalMemoryRuntime ja existe |
| Artefatos = edicao ao vivo | Nosso HTML e estatico, mas Shin pode editar |
| Analise de CSV de campanhas | CampaignAnalytics le relatorios exportados |

### Video 3 — Escolher Produtos (Tnjul-5E8s)
| Ensinamento | Como a Fabrica Implementa |
|---|---|
| Comissao minima USD 100-500 | Filtro no scoring: commission < 100 → cold |
| Curva trafego x tempo | trends_curve + trends_percent_30d |
| Nao pegar produto em queda | Se trends_curve == "falling" → cold |
| Flow Spy (SimilarWeb + Semrush) | Integracao futura paga |
| Gravidade do ClickBank | gravity_score no ProductOpportunity |
| Trafego do Brasil = afiliados, nao compradores | Filtrar: se traffic_brazil_pct > 30% → cold |
| Comissao fixa vs variavel (Heavy Share) | AffiliatePlatformProfile.platform_type |

---

## CHECKLIST PARA IMPLEMENTACAO

### Se Shin aprovar esta proposta, o Codex deve:

- [ ] Criar `core/departments/product_hunter/` com models, pipeline, employee
- [ ] Criar `core/tools/adapters/landing_page_adapter.py` (MOCK HTML generator)
- [ ] Criar `core/tools/adapters/google_ads_adapter.py` (MOCK campaign builder)
- [ ] Adicionar snapshots em `core/observability.py` (HunterReport, CampaignSnapshot)
- [ ] Adicionar eventos em `core/events/domain_events.py` (se necessario)
- [ ] Criar `core/content_factory/affiliate_gringa_workflow.py`
- [ ] Criar demo `demo_affiliate_gringa_pipeline.py` com assertions
- [ ] Rodar compileall + regressao completa
- [ ] Atualizar AGENTS.md com o novo departamento

### O que NÃO deve ser feito no MVP:
- Nao chamar ClickBank API real (usar dados MOCK)
- Nao chamar Google Trends API real (usar curva simulada)
- Nao publicar landing page em dominio real (salvar em output/)
- Nao gastar dinheiro em Google Ads (gerar arquivo exportavel)
- Nao conectar com Flow Spy / Semrush

---

## ARQUIVOS QUE O CODEX DEVE REVISAR

1. `docs/external_llm_inbox/deepseek/ideas/2026-07-15_affiliate_marketing_pipeline_gringa.md` (este arquivo)
2. (futuro) `core/departments/product_hunter/` — se implementado
3. (futuro) `core/tools/adapters/landing_page_adapter.py` — se implementado
4. (futuro) `core/tools/adapters/google_ads_adapter.py` — se implementado
