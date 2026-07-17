# FASE 1 — ProductHunterEmployee (TrendScanner MOCK)

Status: PROPOSTA - NAO IMPLEMENTADA
Data: 2026-07-15
Video: `_Tnjul-5E8s` (Como Escolher Produtos Explodindo) + `HNgMXUNsEi8` (Ex-Uber R$4M)

---

## O QUE ESTE DOCUMENTO FAZ

Especificacao completa do ProductHunterEmployee para o Codex implementar.
Cada etapa referencia o minuto exato do video, para que o Codex possa assistir e conferir.

---

## 1. OBJETIVO DO EMPLOYEE

Varrer diariamente as plataformas de afiliado internacional (ClickBank, BuyGoods, MaxWeb), cruzar com Google Trends, e entregar um relatorio rankeado dos produtos que estao em alta — tudo em MOCK (dados deterministicos) para o MVP.

Nao faz scraping real. Nao chama API paga. Usa dados de exemplo.

---

## 2. REFERENCIA DOS VIDEOS

### Video A — Como escolher produtos (`_Tnjul-5E8s`)

| Timestamp | Conteudo | Como implementamos |
|---|---|---|
| 00:40 | Comissoes baixas (R$70-90) sao dificeis de lucrar | `CommissionFilter`: descarta produtos com comissao < $50 |
| 01:40 | Tipos de produto: digital, nutraceutico, ecommerce, game, marketplace | `ProductType` enum no modelo |
| 03:19 | **Relacao trafego x tempo** — o grafico do Trends e a coisa mais importante | `TrendCheck.curve` = rising/stable/falling |
| 04:18 | Produto TheBrainSong: curva caida = NÃO vender | `recommendation = "cold"` se falling |
| 05:48 | Produto Matsato (faca): curva estavel = aceitavel | `recommendation = "warm"` se stable |
| 06:11 | Flow Spy: ferramenta que agrega dados de SimilarWeb + Semrush | Fase futura paga, nao implementar agora |
| 06:28 | "Rising" = produtos que comecaram a crescer nos ultimos 30 dias | `trends_percent_30d` positivo |
| 07:23 | Heavy Share: comissao variavel (ClickBank) vs fixa (MaxWeb) | `commission_type` no modelo |
| 09:40 | Grafico de 3-6 meses para ver curva real, nao so 7 dias | `trends_period` = "3m", "6m" |
| 10:30 | Ignatra vs Menes Rescui: volume de trafego faz diferenca | Score pondera volume + crescimento |
| 12:20 | Cuidado com trafego do Brasil (provavelmente afiliados, nao compradores) | Se traffic_brazil_pct > 30% → penalidade |
| 13:30 | Gravidade do ClickBank: quanto mais alta, mais vende | `gravity_score` no check |
| 14:50 | Produtos com checkout direto vs so pagina de vendas | `checkout_type` no modelo |
| 16:30 | Cash on Delivery (COD): entrega por call center, comissao baixa | Ignorar no MVP |

### Video B — Ex-Uber R$4M (HNgMXUNsEi8)

| Timestamp | Conteudo | Como implementamos |
|---|---|---|
| 06:53 | ClickBank como plataforma principal | `Platform.CLICKBANK` |
| 07:35 | BuyGoods como alternativa | `Platform.BUYGOODS` |
| 08:02 | Margem de lucro: 20-30% de ROI | Calculo de `estimated_roi` no score |
| 09:42 | Google Trends como filtro principal | `TrendChecker` usa Trends |
| 11:00 | Foco em US, Canada, Australia, UK | `target_countries` default |
| 13:30 | Nao confiar no mapa de localizacao do Trends (poluido por afiliados) | Ignorar mapa, focar no grafico de linha |
| 14:00 | Produto com curva consistente em 7 dias mesmo sendo antigo = bom sinal | `trends_7d_stable` flag |
| 17:24 | CPA = 50% da comissao | `cpa_target` calculado |

### Video C — Claude +R$100k (WmhRp1aAuwk)

| Timestamp | Conteudo | Implementacao |
|---|---|---|
| 03:40 | Skills do Claude = prompts reutilizaveis para gerar campanhas | Usado na Fase 2 (landing page) e Fase 3 (ads) |
| 05:10 | Viral monitor: script Python que varre YouTube todo dia | Inspiracao para ProductHunter rodar diariamente |
| 06:50 | VPS Hostinger R$40/mes rodando 24h | Infra futura |

---

## 3. MODELOS (frozen+slots)

```python
@dataclass(frozen=True, slots=True)
class Platform:
    """Plataformas de afiliado suportadas"""
    CLICKBANK = "clickbank"
    BUYGOODS = "buygoods"
    MAXWEB = "maxweb"
    GURUMEDIA = "gurumedia"

@dataclass(frozen=True, slots=True)
class ProductType:
    DIGITAL = "digital"          # cursos, mentorias, SaaS
    NUTRACEUTICAL = "nutraceutical"  # remedios, cha, suplementos
    ECOMMERCE = "ecommerce"      # facas, fones, travesseiros
    GAME = "game"                # (nao recomendado — video 00:02:50)

@dataclass(frozen=True, slots=True)
class CommissionType:
    PERCENTAGE = "percentage"    # % do preco — ClickBank
    FIXED = "fixed"              # valor fixo — MaxWeb (video 00:07:23)
    HEAVY_SHARE = "heavy_share"  # variavel por pote/unidade

@dataclass(frozen=True, slots=True)
class TrendCurve:
    RISING = "rising"    # subindo — video 00:06:28
    STABLE = "stable"    # estavel — video 00:05:48
    FALLING = "falling"  # caindo — video 00:04:18

@dataclass(frozen=True, slots=True)
class CheckoutType:
    DIRECT = "direct"      # link vai direto pro checkout (bom)
    SALES_PAGE = "sales_page"  # link vai pra pagina de vendas (precisa de mais um clique)

@dataclass(frozen=True, slots=True)
class ProductOpportunity:
    """Um produto encontrado na varredura"""
    id: str                          # uuid
    product_name: str                # nome exato (ex: "ProstaVive")
    platform: str                    # Platform enum
    product_type: str                # ProductType enum
    commission_type: str             # CommissionType enum
    commission_usd: float            # comissao em dolar (ex: 175.60)
    product_price_usd: float         # preco do produto (ex: 49.95)
    gravity_score: float             # ClickBank gravity (ex: 175.43)
    affiliate_link: str              # link de afiliado completo
    checkout_type: str               # CheckoutType
    commission_pct: float            # % de comissao (ex: 0.75 = 75%)

@dataclass(frozen=True, slots=True)
class TrendCheck:
    """Resultado da checagem no Google Trends"""
    product_name: str
    curve: str                       # TrendCurve
    percent_change_30d: float        # -100 a +infinito
    percent_change_7d: float         # tendencia recente
    volume_30d_avg: float            # volume medio de busca (ex: 36100)
    period_months: int               # 3 ou 6
    traffic_brazil_pct: float        # % de trafego vindo do Brasil

@dataclass(frozen=True, slots=True)
class PlatformScan:
    """Resultado da varredura em uma plataforma"""
    platform: str
    products_scanned: int
    products_found: tuple[ProductOpportunity, ...]  # so os que passaram filtro

@dataclass(frozen=True, slots=True)
class ScoredOpportunity:
    """Oportunidade com score calculado + recomendacao"""
    product: ProductOpportunity
    trend: TrendCheck | None
    score_total: float               # 0-100
    score_commission: float          # 0-25
    score_trend: float               # 0-25
    score_volume: float              # 0-20
    score_gravity: float             # 0-15
    score_confidence: float          # 0-15
    risk_penalty: float              # -35 a 0
    recommendation: str              # "hot", "warm", "cold"
    estimated_daily_roi_pct: float   # ROI estimado (%)
    target_cpa_usd: float            # 50% da comissao — video 00:17:24

@dataclass(frozen=True, slots=True)
class HunterReport:
    """Relatorio final do dia"""
    date: str                        # "2026-07-15"
    total_scanned: int
    hot_opportunities: tuple[ScoredOpportunity, ...]
    warm_opportunities: tuple[ScoredOpportunity, ...]
    cold_opportunities: tuple[ScoredOpportunity, ...]
    summary: str                     # texto curto tipo "5 produtos em alta hoje"

@dataclass(frozen=True, slots=True)
class HunterTask:
    """Task recebida pelo ProductHunterEmployee"""
    scan_platforms: tuple[str, ...]  # quais platforms varrer
    min_commission_usd: float        # comissao minima (default 50)
    max_results: int                 # max de resultados (default 10)
    target_countries: tuple[str, ...] # (default: US, CA, AU, GB)

@dataclass(frozen=True, slots=True)
class HunterMetrics:
    """Metricas de producao do hunter"""
    products_scanned: int
    products_hot: int
    products_warm: int
    products_cold: int
    top_score: float
    platforms_covered: int
```

---

## 4. DADOS MOCK (produtos dos videos)

O ProductHunterEmployee, em modo MOCK, retorna estes dados. Todos os produtos sao reais e foram mencionados nos videos.

```python
# Fonte: Video A (_Tnjul-5E8s) + Video B (HNgMXUNsEi8)

MOCK_PRODUCTS = {
    "prostavive": ProductOpportunity(
        id="prod-001",
        product_name="ProstaVive",
        platform=Platform.CLICKBANK,
        product_type=ProductType.NUTRACEUTICAL,
        commission_type=CommissionType.PERCENTAGE,
        commission_usd=175.60,
        product_price_usd=69.00,
        gravity_score=175.43,
        affiliate_link="https://hop.clickbank.net/?affiliate=...&vendor=prostavive",
        checkout_type=CheckoutType.DIRECT,
        commission_pct=0.75,
    ),
    "ignatra": ProductOpportunity(
        id="prod-002",
        product_name="Ignatra",
        platform=Platform.CLICKBANK,
        product_type=ProductType.NUTRACEUTICAL,
        commission_type=CommissionType.PERCENTAGE,
        commission_usd=180.00,
        product_price_usd=67.00,
        gravity_score=142.18,
        affiliate_link="https://hop.clickbank.net/?affiliate=...&vendor=ignatra",
        checkout_type=CheckoutType.SALES_PAGE,
        commission_pct=0.75,
    ),
    "prodentin": ProductOpportunity(
        id="prod-003",
        product_name="Prodentin",
        platform=Platform.CLICKBANK,
        product_type=ProductType.NUTRACEUTICAL,
        commission_type=CommissionType.PERCENTAGE,
        commission_usd=140.00,
        product_price_usd=55.00,
        gravity_score=188.45,
        affiliate_link="https://hop.clickbank.net/?affiliate=...&vendor=prodentin",
        checkout_type=CheckoutType.DIRECT,
        commission_pct=0.75,
    ),
    "matsato": ProductOpportunity(
        id="prod-004",
        product_name="Matsato",
        platform=Platform.BUYGOODS,
        product_type=ProductType.ECOMMERCE,
        commission_type=CommissionType.FIXED,
        commission_usd=70.00,
        product_price_usd=89.00,
        gravity_score=45.20,
        affiliate_link="https://www.buygoods.com/...",
        checkout_type=CheckoutType.DIRECT,
        commission_pct=0.79,
    ),
    "brainsong": ProductOpportunity(
        id="prod-005",
        product_name="The BrainSong",
        platform=Platform.CLICKBANK,
        product_type=ProductType.DIGITAL,
        commission_type=CommissionType.PERCENTAGE,
        commission_usd=200.00,
        product_price_usd=47.00,
        gravity_score=220.10,
        affiliate_link="https://hop.clickbank.net/?affiliate=...&vendor=brainsong",
        checkout_type=CheckoutType.DIRECT,
        commission_pct=0.75,
    ),
    "menes_rescui": ProductOpportunity(
        id="prod-006",
        product_name="Menes Rescui",
        platform=Platform.MAXWEB,
        product_type=ProductType.NUTRACEUTICAL,
        commission_type=CommissionType.FIXED,
        commission_usd=166.00,
        product_price_usd=77.00,
        gravity_score=18.30,
        affiliate_link="https://www.maxweb.com/...",
        checkout_type=CheckoutType.SALES_PAGE,
        commission_pct=0.50,
    ),
}

MOCK_TRENDS = {
    "prostavive": TrendCheck(
        product_name="ProstaVive",
        curve=TrendCurve.RISING,
        percent_change_30d=25.0,
        percent_change_7d=8.0,
        volume_30d_avg=36100,
        period_months=3,
        traffic_brazil_pct=12.0,
    ),
    "ignatra": TrendCheck(
        product_name="Ignatra",
        curve=TrendCurve.RISING,
        percent_change_30d=17.0,
        percent_change_7d=5.0,
        volume_30d_avg=28400,
        period_months=3,
        traffic_brazil_pct=18.0,
    ),
    "prodentin": TrendCheck(
        product_name="Prodentin",
        curve=TrendCurve.RISING,
        percent_change_30d=8.0,
        percent_change_7d=2.0,
        volume_30d_avg=52300,
        period_months=3,
        traffic_brazil_pct=25.0,
    ),
    "matsato": TrendCheck(
        product_name="Matsato",
        curve=TrendCurve.STABLE,
        percent_change_30d=-2.0,
        percent_change_7d=-1.0,
        volume_30d_avg=8900,
        period_months=3,
        traffic_brazil_pct=8.0,
    ),
    "brainsong": TrendCheck(
        product_name="The BrainSong",
        curve=TrendCurve.FALLING,
        percent_change_30d=-30.0,
        percent_change_7d=-12.0,
        volume_30d_avg=45200,
        period_months=3,
        traffic_brazil_pct=35.0,
    ),
    "menes_rescui": TrendCheck(
        product_name="Menes Rescui",
        curve=TrendCurve.RISING,
        percent_change_30d=5.0,
        percent_change_7d=1.0,
        volume_30d_avg=3100,
        period_months=3,
        traffic_brazil_pct=40.0,
    ),
}
```

---

## 5. PIPELINE (6 stages)

```python
class ProductHunterPipeline(ProductionPipeline):
    """Pipeline de varredura de produtos em alta na gringa"""

    stages = (
        "CREATED",                    # 0 — estado inicial
        "SCANNING_PLATFORMS",         # 1 — varre ClickBank, BuyGoods, MaxWeb
        "CHECKING_TRENDS",            # 2 — consulta Google Trends para cada produto
        "SCORING_OPPORTUNITIES",      # 3 — calcula score composto
        "RANKING_AND_FILTERING",      # 4 — ordena, separa hot/warm/cold
        "DELIVERING_REPORT",          # 5 — gera HunterReport
        "COMPLETED",                  # 6 — fim
    )

    def __init__(self, task: HunterTask):
        self.task = task
        self.products: dict[str, ProductOpportunity] = {}
        self.trends: dict[str, TrendCheck] = {}
        self.scored: list[ScoredOpportunity] = []
        self.report: HunterReport | None = None
```

### Stage 1 — SCANNING_PLATFORMS

```python
def _handle_scanning_platforms(self) -> StageResult:
    """
    Varre as plataformas configuradas atras de produtos.
    Video A 00:01:40 — tipos de produto que valem a pena.
    Video A 00:06:53 — ClickBank como plataforma principal.

    MOCK: retorna dados pre-definidos de MOCK_PRODUCTS.
    REAL (futuro): chama API da ClickBank/BuyGoods.

    O QUE FAZER:
    1. Para cada plataforma em task.scan_platforms:
    2.   Busca produtos (MOCK: filtra MOCK_PRODUCTS por platform)
    3. Para cada produto encontrado:
    4.   Se commission_usd < task.min_commission_usd → descarta
    5.   Se product_type == ProductType.GAME → descarta
    6.   Adiciona a self.products

    RETORNA: StageResult(success, data={"platforms_scanned": [...], "count": N})
    """
```

### Stage 2 — CHECKING_TRENDS

```python
def _handle_checking_trends(self) -> StageResult:
    """
    Para cada produto encontrado, consulta o Google Trends.
    Video A 00:03:19 — relacao trafego x tempo e a coisa mais importante.
    Video A 00:04:18 — TheBrainSong em queda: nao vender.
    Video A 00:09:40 — olhar 3 a 6 meses, nao so 7 dias.
    Video A 00:12:20 — cuidado com trafego do Brasil.

    MOCK: retorna dados de MOCK_TRENDS.
    REAL (futuro): Google Trends API ou scraping.

    O QUE FAZER:
    1. Para cada produto em self.products:
    2.   Busca trends (MOCK: MOCK_TRENDS[product_name])
    3.   Se curve == FALLING AND percent_change_30d < -20:
    4.     Marcar como "evitar" — produto em queda (Video A 00:04:18)
    5.   Se traffic_brazil_pct > 30:
    6.     Marcar como "trafego suspeito" (Video A 00:12:20)
    7.   Adiciona a self.trends

    RETORNA: StageResult(success, data={"trends_checked": N})
    """
```

### Stage 3 — SCORING_OPPORTUNITIES

```python
def _score_single(self, product: ProductOpportunity, trend: TrendCheck | None) -> ScoredOpportunity:
    """
    Calcula score composto do produto.
    Video A 00:01:40 — comissao minima deve ser USD 100-500.
    Video A 00:10:30 — volume de trafego + crescimento.
    Video A 00:13:30 — gravidade alta = produto vende bem.
    Video B 00:08:02 — margem de lucro 20-30%.

    COMPONENTES DO SCORE (total 0-100):

    1. COMMISSION (0-25):
       - commission_usd >= 200 → 25
       - commission_usd >= 150 → 20
       - commission_usd >= 100 → 15
       - commission_usd >= 50  → 10
       - commission_usd <  50  → 0 (nem chega aqui — filtro)

    2. TREND (0-25):
       - curve == RISING AND percent_change_30d >= 15 → 25
       - curve == RISING                            → 20
       - curve == STABLE                            → 12
       - curve == FALLING                           → 0

    3. VOLUME (0-20):
       - volume_30d_avg >= 50000 → 20
       - volume_30d_avg >= 20000 → 15
       - volume_30d_avg >= 5000  → 10
       - volume_30d_avg <  5000  → 5

    4. GRAVITY (0-15):
       - gravity_score >= 150 → 15
       - gravity_score >= 80  → 10
       - gravity_score >= 30  → 6
       - gravity_score <  30  → 3

    5. CONFIDENCE (0-15):
       - checkout_type == DIRECT → 10
       - commission_type == FIXED → 5
       - gravity_score >= 50 → +5

    RISK PENALTY (-35 a 0):
       - curve == FALLING → -15
       - traffic_brazil_pct > 30 → -10
       - product_type == ECOMMERCE → -5 (comissao fixa baixa — Video A 00:16:30)
       - gravity_score < 20 → -5 (poucas vendas)

    RECOMENDACAO:
       - score >= 70 → "hot"
       - score >= 50 → "warm"
       - score <  50 → "cold"
    
    ESTIMATED DAILY ROI:
       - Se CPA (50% da comissao) for menor que a comissao:
         roi = (commission - cpa) / cpa * 100
       - Ex: comissao 175.60, CPA 87.80 → ROI = 100%

    TARGET CPA:
       = commission_usd * 0.50 (Video B 00:17:24)
    """
```

### Stage 4 — RANKING_AND_FILTERING

```python
def _handle_ranking_and_filtering(self) -> StageResult:
    """
    Ordena produtos por score, separa em categorias.
    Video A 00:11:00 — foco em produtos com volume + crescimento.

    O QUE FAZER:
    1. Ordena self.scored por score_total (decrescente)
    2. Separa em tres listas: hot, warm, cold
    3. Se len(hot) == 0 AND len(warm) == 0:
         Reportar "nenhum produto em alta hoje" (pode acontecer)
    4. Limita a task.max_results

    RETORNA: StageResult(success, data={
        "hot_count": N, "warm_count": N, "cold_count": N
    })
    """
```

### Stage 5 — DELIVERING_REPORT

```python
def _handle_delivering_report(self) -> StageResult:
    """
    Gera o HunterReport final.

    O QUE FAZER:
    1. Cria HunterReport com:
       - date: hoje
       - total_scanned: len(self.scored)
       - hot_opportunities: tuple dos hot
       - warm_opportunities: tuple dos warm
       - cold_opportunities: tuple dos cold
       - summary: "Top 3: {nome1} ({score1}), {nome2} ({score2}), {nome3} ({score3})"

    RETORNA: StageResult(success, data={"report": hunter_report})
    """
```

---

## 6. EMPLOYEE

```python
class ProductHunterEmployee(ProductionEmployee):
    """
    Vare diariamente as plataformas de afiliado por produtos em alta.

    Department keyword: "product_hunter", "trend_scanner", "affiliate_scan"
    """

    _DEPARTMENT_KEYWORD = "product_hunter"

    # --- hooks que SOBRESCREVEM os da base ---

    def _check_reject(self, task: ReceivedTask) -> str | None:
        """Rejeita se nao for task de varredura"""
        dept = task.department.lower()
        keywords = ("product_hunter", "trend_scanner", "affiliate_scan", "daily_scan")
        if not any(k in dept for k in keywords):
            return f"Department '{task.department}' not supported"

    def _build_pipeline(self, task: ReceivedTask) -> ProductionPipeline:
        """Cria pipeline de 6 stages"""
        hunter_task = self._coerce_hunter_task(task.context)
        return ProductHunterPipeline(hunter_task)

    def _build_output_from_stages(self, output: dict, parts: list) -> None:
        """Extrai relatorio do DELIVERING_REPORT stage"""
        for p in parts:
            if "report" in p.get("data", {}):
                output["report"] = p["data"]["report"]
                break

    def _build_metrics(self, completed: int, failed: int, output: dict, duration: float) -> ProductionMetrics:
        """Metricas do hunter"""
        report = output.get("report")
        if report:
            return HunterMetrics(
                products_scanned=report.total_scanned,
                products_hot=len(report.hot_opportunities),
                products_warm=len(report.warm_opportunities),
                products_cold=len(report.cold_opportunities),
                top_score=report.hot_opportunities[0].score_total if report.hot_opportunities else 0.0,
                platforms_covered=3,  # MOCK: ClickBank, BuyGoods, MaxWeb
            )
        return HunterMetrics(0, 0, 0, 0, 0.0, 0)

    def _build_summary(self, success: bool, parts: list) -> str:
        """Sumario do dia"""
        if not success:
            return "Product scan failed"
        report = None
        for p in parts:
            if "report" in p.get("data", {}):
                report = p["data"]["report"]
                break
        if not report:
            return "No report generated"
        return report.summary

    def analyze_capability_needs(self) -> tuple:
        """Capabilities necessarias"""
        from core.company.capability_registry import Capability
        return (Capability.WEB_SEARCH, Capability.BROWSER_AUTOMATION)

    def state(self) -> dict:
        """Estado atual do hunter"""
        base = super().state()
        base["hunter_capabilities"] = list(self.analyze_capability_needs())
        base["last_scan_date"] = ""  # preenchido apos scan
        return base

    # --- coerce helper ---

    @staticmethod
    def _coerce_hunter_task(ctx: dict) -> HunterTask:
        """Converte dict do ReceivedTask.context em HunterTask"""
        return HunterTask(
            scan_platforms=tuple(ctx.get("scan_platforms", 
                ["clickbank", "buygoods", "maxweb"])),
            min_commission_usd=float(ctx.get("min_commission_usd", 50.0)),
            max_results=int(ctx.get("max_results", 10)),
            target_countries=tuple(ctx.get("target_countries", 
                ["US", "CA", "AU", "GB"])),
        )
```

---

## 7. OBSERVABILITY

### Eventos (aditivo, em `core/events/domain_events.py`):

```python
@dataclass(frozen=True, slots=True)
class HunterScanStarted(Event):
    execution_id: str
    platforms: tuple[str, ...]
    timestamp: float

@dataclass(frozen=True, slots=True)
class HunterScanCompleted(Event):
    execution_id: str
    total_products: int
    hot_count: int
    warm_count: int
    cold_count: int
    timestamp: float
```

### Snapshot (aditivo, em `core/observability.py`):

```python
@dataclass(frozen=True, slots=True)
class ProductHunterSnapshot:
    """Snapshot do scanner de produtos"""
    date: str
    total_scanned: int
    hot_count: int
    warm_count: int
    cold_count: int
    top_score: float
    top_product: str  # nome do melhor produto
```

---

## 8. QUALITY RULES

Regras que o QualityRuntime deve aplicar no output do hunter:

```python
# Em core/company/quality.py (aditivo)

HUNTER_QUALITY_RULES = [
    QualityRule(
        name="hunter_has_report",
        category="completeness",
        description="Hunter deve gerar um relatorio",
        check=lambda ctx: "report" in ctx.get("output", {}),
    ),
    QualityRule(
        name="hunter_at_least_one_hot",
        category="quality",
        description="Deve haver ao menos 1 produto 'hot' no relatorio",
        check=lambda ctx: len(ctx.get("report", {}).get("hot_opportunities", [])) > 0,
    ),
    QualityRule(
        name="hunter_no_duplicates",
        category="consistency",
        description="Nenhum produto duplicado entre plataformas",
        check=lambda ctx: _check_no_duplicates(ctx.get("report", {})),
    ),
    QualityRule(
        name="hunter_trends_checked",
        category="process",
        description="Todos os produtos devem ter trend check",
        check=lambda ctx: _check_all_trended(ctx.get("report", {})),
    ),
]
```

---

## 9. DEMO OUTLINE

```python
# demo_product_hunter_employee.py
# Status sugerido: demo padrao da regressao

def test_hunter_mock():
    """
    Valida:
    1. ProductHunterEmployee aceita task com department="product_hunter"
    2. Pipeline executa 6 stages ate COMPLETED
    3. HunterReport contem produtos dos videos
    4. ProstaVive e Ignatra sao "hot" (curva subindo, comissao alta)
    5. TheBrainSong e "cold" (curva caindo — Video A 00:04:18)
    6. Menes Rescui e "cold" (trafego Brasil 40% — Video A 00:12:20)
    7. ScoredOpportunity.target_cpa == commission * 0.5 (Video B 00:17:24)
    8. HunterMetrics preenchidos corretamente
    9. Nenhuma chamada externa (modo MOCK padrao)
    """
```

---

## 10. O QUE O CODEX PRECISA FAZER

| Arquivo | Acao |
|---|---|
| `core/departments/product_hunter/__init__.py` | Criar — exports |
| `core/departments/product_hunter/models.py` | Criar — todos os frozen+slots acima |
| `core/departments/product_hunter/pipeline.py` | Criar — ProductHunterPipeline com 6 stages |
| `core/departments/product_hunter/employee.py` | Criar — ProductHunterEmployee |
| `core/events/domain_events.py` | Adicionar HunterScanStarted, HunterScanCompleted |
| `core/observability.py` | Adicionar ProductHunterSnapshot |
| `core/company/quality.py` | Adicionar HUNTER_QUALITY_RULES (opcional) |
| `demo_product_hunter_employee.py` | Criar — demo com assertions |

### Nao fazer:
- Nao implementar ClickBank API real
- Nao implementar Google Trends API real
- Nao conectar com Flow Spy
- Nao modificar classes existentes (tudo aditivo)

### Dependencias:
- `SpecialistEmployee` (ja existe)
- `ProductionEmployee` (ja existe)
- `ProductionPipeline` (ja existe)
- `QualityRuntime` (ja existe)
- `ObservabilityProjector` (ja existe)

Nenhuma nova dependencia externa. Nenhuma modificacao em arquivos existentes.
