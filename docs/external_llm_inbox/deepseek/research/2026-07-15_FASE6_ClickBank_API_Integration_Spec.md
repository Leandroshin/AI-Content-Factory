# FASE 6 — ClickBank API Integration

Status: PROPOSTA - NAO IMPLEMENTADA
Data: 2026-07-15
Fase: 6 de 7 (primeira integracao REAL)
Videos: `_Tnjul-5E8s` (Como Escolher Produtos) + `HNgMXUNsEi8` (Ex-Uber R$4M)

---

## O QUE ESTE DOCUMENTO FAZ

Especificacao completa do ClickBankProvider + ClickBankAdapter para o Codex implementar.
Esta e a primeira fase que conecta a API REAL da ClickBank ao inves de usar dados MOCK.
O ProductHunterEmployee (Fase 1) continuara usando MOCK por padrao, mas podera receber
o ClickBankAdapter para buscar produtos reais quando configurado em modo REAL.

---

## 1. OBJETIVO

Criar `ClickBankProvider` (provider pattern) + `ClickBankAdapter` (tool adapter)
que substituem os dados MOCK do `ProductHunterPipeline` por dados reais da API ClickBank.

A pipeline da Fase 1 NAO e alterada. O adapter e um componente separado que:
- Em MOCK mode: retorna exatamente os mesmos `MOCK_PRODUCTS` da Fase 1
- Em REAL mode: chama a API ClickBank, mapeia resposta para `ProductOpportunity`,
  gera hoplinks com o affiliate ID real de Shin, e aplica BudgetGuard

O ProductHunterEmployee podera opcionalmente receber o adapter via configuracao.
Se nao receber, continua funcionando em MOCK puro (compatibilidade reversa).

---

## 2. REFERENCIA DOS VIDEOS

### Video A — Como escolher produtos (`_Tnjul-5E8s`)

| Timestamp | Conteudo | Relevancia para Fase 6 |
|---|---|---|
| 03:00 | ClickBank e a plataforma principal, cadastro gratis | Base para criacao do provider — ClickBank e o primeiro alvo REAL |
| 07:23 | Heavy Share (comissao variavel) vs Fixed (MaxWeb) | Mapear `commissionType` da API corretamente |
| 09:00 | Navegacao no marketplace da ClickBank | Entender como a API de marketplace funciona: categoria, gravidade, preco |
| 13:30 | Gravity score mostra popularidade | Mapear `gravity` do response para `gravity_score` no modelo |
| 14:50 | Produtos com checkout direto vs so pagina de vendas | Mapear `checkoutUrl` para `CheckoutType` |

### Video B — Ex-Uber R$4M (HNgMXUNsEi8)

| Timestamp | Conteudo | Relevancia para Fase 6 |
|---|---|---|
| 06:53-07:35 | ClickBank + BuyGoods como plataformas | ClickBank e o primeiro provider REAL; BuyGoods sera Fase 7 |

---

## 3. PROVIDER — `core/tools/providers/clickbank.py`

### Estrutura

```python
@dataclass(frozen=True, slots=True)
class ClickBankProduct:
    """Produto bruto retornado pela API ClickBank marketplace"""
    id: str                        # ex: "PROSTAVIVE"
    name: str                      # ex: "ProstaVive"
    commission: float              # comissao em USD (ja calculada ou % do preco)
    commission_type: str           # "percentage", "fixed", "heavy_share"
    price: float                   # preco do produto
    gravity: float                 # gravity score
    category: str                  # ex: "Health & Fitness"
    type: str                      # "digital", "physical"
    vendor: str                    # nome do vendor (proprietario do produto)
    checkout_url: str | None       # URL de checkout direto (se existir)
    sales_page_url: str | None     # URL da pagina de vendas
    is_recurring: bool             # se tem pagamento recorrente
    rebill_amount: float | None    # valor da recarga recorrente
    future_commissions: bool       # se paga comissao em futuras recargas

@dataclass(frozen=True, slots=True)
class ClickBankSearchResponse:
    """Resposta paginada da API de search/marketplace"""
    total_results: int
    products: tuple[ClickBankProduct, ...]
    page: int
    next_page: int | None
```

A API ClickBank retorna uma lista de categorias e subcategorias no marketplace.
O provider deve normalizar isso no modelo `ClickBankProduct`.

### Classe `ClickBankProvider`

```python
class ClickBankProvider:
    """
    Provider para a API ClickBank (REST 1.3).
    
    Documentacao oficial:
    https://support.clickbank.com/hc/en-us/articles/220346807-ClickBank-API-Overview
    
    Base URL: https://api.clickbank.com/rest/1.3/
    Autenticacao: Header "Authorization: dev-key {API_KEY}"
    """

    BASE_URL = "https://api.clickbank.com/rest/1.3/"
    DEFAULT_TIMEOUT = 15  # segundos

    def __init__(
        self,
        api_key: str,                    # da SecretProvider
        affiliate_id: str,               # da SecretProvider (nickname)
        requests_per_minute: int = 10,   # rate limit conservativo
    ):
        self._api_key = api_key
        self._affiliate_id = affiliate_id
        self._http_client: RealHttpClient = RealHttpClient()
        self._rate_limiter = RateLimiter(
            tokens=requests_per_minute,
            refill_period=60,  # tokens por minuto
        )

    def set_budget_guard(self, guard: ProviderBudgetGuard) -> None:
        """Injeta BudgetGuard para controle de gastos (aditivo)"""

    def search_products(
        self,
        query: str | None = None,
        category: str | None = None,
        subcategory: str | None = None,
        min_gravity: float | None = None,
        min_commission: float | None = None,
        max_results: int = 20,
        page: int = 1,
    ) -> ClickBankSearchResponse:
        """
        GET /rest/1.3/marketplace
        
        Parametros da API:
        - query: termo de busca
        - category: filtro por categoria
        - subcategory: filtro por subcategoria
        - siteID: filtro por vendor especifico (nao usado)
        - page: numero da pagina
        
        A API ClickBank retorna resultados paginados com no maximo 20 items
        por pagina. O provider deve:
        1. Adquirir token do rate limiter
        2. Fazer GET com header de autenticacao
        3. Parsear resposta XML/JSON (ClickBank usa ambos)
        4. Aplicar filtros locais (min_gravity, min_commission)
        5. Retornar ClickBankSearchResponse
        
        Resposta esperada (XML):
        ```xml
        <ClickBankMarketplace>
            <Results>
                <Result>
                    <id>PROSTAVIVE</id>
                    <name>ProstaVive</name>
                    <commission>$175.60</commission>
                    <commissionType>percentage</commissionType>
                    <price>$69.00</price>
                    <gravity>175.43</gravity>
                    <category>Health & Fitness</category>
                    <type>digital</type>
                    <vendor>prostavive</vendor>
                    <checkoutUrl>https://prostavive.com/checkout/...</checkoutUrl>
                    <salesPageUrl>https://prostavive.com/</salesPageUrl>
                </Result>
            </Results>
            <TotalResults>150</TotalResults>
        </ClickBankMarketplace>
        ```
        """

    def get_product_details(self, product_id: str) -> ClickBankProduct | None:
        """
        GET /rest/1.3/marketplace/{product_id}
        
        Detalhes de um produto especifico.
        Pode retornar campos adicionais como:
        - recurring: se tem pagamento recorrente
        - rebill: valor da recarga
        - futureCommission: se paga comissao futura
        
        Se o produto nao for encontrado, retorna None.
        """

    def get_hoplink(self, vendor: str) -> str:
        """
        Gera hoplink de afiliado no formato:
        https://hop.clickbank.net/?affiliate={affiliate_id}&vendor={vendor}
        
        NOTA: a API ClickBank NAO tem um endpoint para gerar hoplinks.
        O formato e padrao e deve ser construido localmente.
        """

    def get_categories(self) -> list[dict]:
        """
        GET /rest/1.3/marketplace/categories
        
        Retorna a arvore de categorias disponiveis no marketplace.
        Usado para filtro e navegacao.
        """

    def _get_headers(self) -> dict:
        """Headers padrao: Authorization + Accept + Content-Type"""

    def _parse_product(self, raw: dict) -> ClickBankProduct:
        """Converte resposta bruta (dict) em ClickBankProduct"""

    def _parse_commission(self, commission_str: str) -> float:
        """
        Converte string de comissao para float.
        A API pode retornar "$175.60", "75%", ou null.
        Se for percentual, calcula o valor nominal.
        """

    def _calculate_commission_value(
        self, commission_raw: str, price: float, commission_type: str
    ) -> float:
        """
        Calcula o valor nominal da comissao em USD.
        
        Se commission_type == "percentage":
            Ex: price=$69.00, comissao raw="75%" → $51.75
        Se commission_type == "fixed":
            Ex: commission_raw="$175.60" → $175.60
        Se commission_type == "heavy_share":
            Ex: variavel por pote → usar o valor medio informado
        """
```

### Error Handling

```python
# Erros mapeados da API ClickBank:

# 401 Unauthorized — API key invalida ou expirada
#   → Log warning, retornar ClickBankSearchResponse vazio
#   → Provider continua funcionando (fallback silencioso)

# 403 Forbidden — IP bloqueado ou acesso negado
#   → Log error, retornar ClickBankSearchResponse vazio
#   → Provider entra em modo de espera (backoff de 60s)

# 429 Too Many Requests — Rate limit excedido
#   → Usar RateLimiter.acquire() com retry automatico
#   → Se esgotar retries, log e retorno vazio

# 5xx Server Error — ClickBank fora do ar
#   → Log warning, retornar ClickBankSearchResponse vazio
#   → Nao falhar a pipeline

# Timeout (> DEFAULT_TIMEOUT)
#   → RealHttpClient ja trata com HttpTimeoutError
#   → Log, retornar vazio
```

---

## 4. ADAPTER — `core/tools/adapters/clickbank_adapter.py`

### Estrutura

```python
class ClickBankAdapter(AbstractToolAdapter):
    """
    Adapter para buscar produtos reais na ClickBank via API.
    
    MOCK mode:
        Retorna os mesmos dados de Fase 1 MOCK_PRODUCTS (deterministico).
        Nao chama HTTP, nao precisa de API key.
    
    REAL mode:
        1. Chama ClickBankProvider.search_products()
        2. Mapeia resposta para ProductOpportunity (modelo da Fase 1)
        3. Para cada produto, tenta Google Trends check (MOCK nesta fase)
        4. Retorna lista de ProductOpportunity com hoplinks gerados
        5. Aplica BudgetGuard pre-flight
    """

    ADAPTER_NAME = "clickbank_api"
    ADAPTER_VERSION = "1.0.0"

    # Mesmos produtos da Fase 1
    MOCK_PRODUCTS = {
        "prostavive": ProductOpportunity(...),
        "ignatra": ProductOpportunity(...),
        "prodentin": ProductOpportunity(...),
        # ... (copiar exatamente os mesmos da Fase 1)
    }

    MOCK_TRENDS = {
        "prostavive": TrendCheck(...),
        # ... (copiar exatamente os mesmos da Fase 1)
    }

    def __init__(self):
        super().__init__()
        self._provider: ClickBankProvider | None = None
        self._budget_guard: ProviderBudgetGuard | None = None
        self._secret_provider: SecretProvider | None = None

    def set_secret_provider(self, sp: SecretProvider) -> None:
        """Injeta SecretProvider para obter API key + affiliate ID"""

    def set_budget_guard(self, guard: ProviderBudgetGuard) -> None:
        """Injeta BudgetGuard para controle de gastos"""

    def _build_provider(self) -> ClickBankProvider | None:
        """
        Cria ClickBankProvider se tiver SecretProvider.
        Le CLICKBANK_API_KEY e CLICKBANK_AFFILIATE_ID.
        Se nao tiver keys, retorna None (modo MOCK).
        """

    def search_trending_products(
        self,
        min_commission: float = 50.0,
        max_results: int = 10,
        category: str | None = None,
    ) -> list[ProductOpportunity]:
        """
        Busca produtos em alta na ClickBank.
        
        MOCK mode:
            Retorna lista de ProductOpportunity de MOCK_PRODUCTS
            filtrada por min_commission e limitada a max_results.
            Mesmo comportamento da Fase 1.
        
        REAL mode:
            1. Pre-flight: BudgetGuard.check("clickbank_search")
            2. ClickBankProvider.search_products(
                 min_commission=min_commission,
                 max_results=max_results,
                 category=category,
               )
            3. Para cada ClickBankProduct:
               a. Mapeia campos para ProductOpportunity
               b. Gera hoplink via ClickBankProvider.get_hoplink()
               c. Busca trend (MOCK: MOCK_TRENDS por nome do produto)
               d. Calcula commission_usd corretamente
            4. Ordena por gravity score (decrescente)
            5. Retorna lista limitada a max_results
        
        Se a API falhar (qualquer erro):
            → Log warning "ClickBank API error, falling back to MOCK"
            → Retorna dados MOCK filtrados (graceful degradation)
        """

    def get_affiliate_hoplink(self, vendor: str) -> str:
        """
        Gera hoplink para um vendor especifico.
        
        MOCK: retorna "https://hop.clickbank.net/?affiliate=MOCK&vendor={vendor}"
        REAL: ClickBankProvider.get_hoplink(vendor)
        """

    def execute(self, input_data: dict) -> AdapterExecutionResult:
        """
        Metodo padrao do AbstractToolAdapter.
        
        input_data esperado:
        {
            "action": "search_trending_products" | "get_affiliate_hoplink",
            "min_commission": 50.0,
            "max_results": 10,
            "category": None,
            "vendor": "prostavive",  # para get_affiliate_hoplink
        }
        
        Retorna AdapterExecutionResult com:
        - success: True
        - data: list[ProductOpportunity] ou str (hoplink)
        - execution_mode: "MOCK" | "REAL"
        """
```

### API Response Mapping (detalhado)

```
ClickBank API (XML/JSON)          ProductOpportunity (Fase 1)
─────────────────────────────     ──────────────────────────────────
result.name                      → product_name
result.commission (string)       → commission_usd (calculado, ver abaixo)
result.price (string)            → product_price_usd
result.gravity (float)           → gravity_score
result.type (string)             → product_type (mapear: "digital" → DIGITAL)
result.commissionType (string)   → commission_type ("percentage" → PERCENTAGE)
result.vendor (string)           → usado para hoplink
result.checkoutUrl (presenca)    → checkout_type (DIRECT se existe, SALES_PAGE se null)
result.category (string)         → categoria (usado para filtro, nao no modelo atual)

Calculo da comissao:
──────────────────
Cenario 1: commissionType = "percentage" e commission = "75%"
    commission_usd = price * 0.75
    Ex: $69.00 * 0.75 = $51.75

Cenario 2: commissionType = "fixed" e commission = "$175.60"
    commission_usd = 175.60

Cenario 3: commissionType = "heavy_share"
    commission_usd = parse commission string (ex: "$20-$40/pot" → usar 30.0 medio)

commission_pct:
    Se commissionType = "percentage": usar o valor do percentual (ex: 0.75)
    Se commissionType = "fixed": calcular price / commission_usd (ex: 69/175.60 = ~0.39)
    Se commissionType = "heavy_share": 0 (indeterminado)

affiliate_link:
    = hoplink gerado via get_hoplink(vendor)

checkout_type:
    Se checkoutUrl != null → DIRECT
    Se checkoutUrl == null AND salesPageUrl != null → SALES_PAGE
    Se ambos null → SALES_PAGE (fallback)

id:
    = "clickbank_{vendor}" (ex: "clickbank_prostavive")
    Ou uuid se preferir — mas manter consistente
```

---

## 5. AFFILIATE HOPLINK GENERATION

```python
# Formato padrao ClickBank:
# https://hop.clickbank.net/?affiliate={affiliate_id}&vendor={vendor}

# O affiliate_id e o "nickname" da conta ClickBank de Shin.
# Deve vir do SecretProvider, chave: CLICKBANK_AFFILIATE_ID

# Exemplo com MOCK:
#   https://hop.clickbank.net/?affiliate=MOCK&vendor=prostavive

# Exemplo com REAL:
#   https://hop.clickbank.net/?affiliate=shin_afiliado&vendor=prostavive

# NOTA: ClickBank NAO tem endpoint de API para gerar hoplinks.
# O formato e documentado no FAQ do afiliado ClickBank.
# Devemos construir a URL manualmente — SEMPRE.
```

---

## 6. BUDGET GUARD INTEGRATION

```python
# Em core/tools/provider_control.py (aditivo)

CLICKBANK_BUDGET_RULES = ProviderBudget(
    provider_name="clickbank",
    limits={
        "max_requests_per_day": 100,        # 100 chamadas de API por dia
        "max_products_scanned_per_day": 500,  # 500 produtos analisados
        "min_approval_required": False,       # ClickBank e gratuito, sem custo por chamada
    },
)

# O BudgetGuard e opcional — se nao for injetado, o adapter funciona sem cheque.
# Se injetado, faz pre-flight check em cada search_products():
#   1. Verifica se max_requests_per_day nao foi excedido
#   2. Verifica se max_products_scanned_per_day nao foi excedido
#   3. Se exceder: log warning, fallback para MOCK
```

---

## 7. ERROR HANDLING — Matriz de Decisao

| Erro | Acao | Log Level | Fallback |
|---|---|---|---|
| API key ausente | Provider retorna None, adapter entra em MOCK | warning | Dados MOCK completos |
| 401 Unauthorized | Log + continua em MOCK pelo resto do dia | warning | Dados MOCK do dia |
| 403 Forbidden | Log + espera 60s + tenta 1x | error | Dados MOCK do dia |
| 429 Rate Limit | RateLimiter faz retry com exponential backoff | info | Se exaurir retries → MOCK |
| 5xx Server Error | Log + retorna vazio (nao falha pipeline) | warning | Lista vazia (sem MOCK) |
| Timeout (>15s) | Log + retorna vazio | warning | Lista vazia (sem MOCK) |
| Network error | Log + fallback para MOCK | warning | Dados MOCK |
| XML parse error | Log + fallback para MOCK | error | Dados MOCK |
| Produto sem vendor | Ignora (pula, nao falha) | debug | N/A |
| Produto sem price | Usa 0.0, continua | debug | N/A |

Principio: **NUNCA quebrar a pipeline**. A pipeline de produtos nunca deve falhar
por causa da API ClickBank. Sempre degradar graciosamente.

---

## 8. GOOGLE TRENDS INTEGRATION (Ainda MOCK nesta fase)

```python
# A Fase 6 NAO implementa Google Trends REAL.
# Para cada produto retornado pela ClickBank API em REAL mode:
#
# 1. Procura em MOCK_TRENDS (key: nome do produto em lowercase, sem espacos)
# 2. Se encontrar: associa o TrendCheck ao ProductOpportunity
# 3. Se nao encontrar: cria TrendCheck com curve=STABLE e volume=0
#    (nem toda API retorna tendencia — isso e aceitavel)
#
# Exemplo:
#   product_name="ProstaVive" → key="prostavive" → MOCK_TRENDS["prostavive"] existe
#   product_name="NewProductXYZ" → key="newproductxyz" → nao existe → TrendCheck neutro
#
# REAL Google Trends API requer adapter separado (fora do escopo da Fase 6).
# Possiveis fontes futuras:
#   - pytrends (biblioteca Python nao-oficial)
#   - SerpAPI Google Trends (paga)
#   - Scraping manual do Google Trends (arriscado)
```

---

## 9. CONFIGURACAO

### Secrets (`secrets/clickbank.env` — IGNORADO pelo .gitignore)

```env
# ClickBank API credentials
# Criado pelo Codex como placeholder.
# Shin preenche com dados reais da conta dele.
CLICKBANK_API_KEY=your_clickbank_api_key_here
CLICKBANK_AFFILIATE_ID=your_clickbank_nickname_here
```

### Configuracoes default (no provider)

```python
# Valores default usados quando nao configurado explicitamente
CLICKBANK_DEFAULTS = {
    "api_base": "https://api.clickbank.com/rest/1.3/",
    "requests_per_minute": 10,
    "timeout_seconds": 15,
    "max_results_default": 20,
    "max_results_per_page": 20,  # limite da API
    "min_commission_default": 50.0,
}
```

### .gitignore (verificar se ja cobre `secrets/`)

```gitignore
# Deve existir no .gitignore:
secrets/
# Se nao existir, adicionar (mas AGENTS.md diz que secrets/ ja esta ignorado)
```

---

## 10. DEMO OUTLINE

```python
# demo_clickbank_adapter.py
# Status sugerido: demo padrao da regressao (REAL mode opt-in)

def test_clickbank_mock():
    """
    Valida ClickBankAdapter em MOCK mode (default):
    1. Cria ClickBankAdapter sem SecretProvider
    2. search_trending_products(min_commission=50)
    3. Assert retorna lista de ProductOpportunity
    4. Assert len >= 5 (tem 6 produtos MOCK)
    5. Assert cada item tem campos preenchidos:
       - product_name nao vazio
       - commission_usd > 0
       - product_price_usd > 0
       - gravity_score >= 0
       - affiliate_link contem "hop.clickbank.net"
       - checkout_type in ("direct", "sales_page")
       - commission_type in ("percentage", "fixed", "heavy_share")
    6. Assert comissao mapeada corretamente:
       - ProstaVive commission_usd == 175.60
       - Matsato commission_type == "fixed" (BuyGoods)
    7. Assert hoplink gerado com affiliate="MOCK"
    8. Assert max_results respeitado
    """

def test_clickbank_mock_filter():
    """
    Valida filtro MOCK:
    1. search_trending_products(min_commission=150)
    2. Assert retorna apenas produtos com comissao >= 150
    3. ProstaVive (175.60) incluso
    4. Prodentin (140.00) excluido
    """

def test_clickbank_affiliate_hoplink():
    """
    Valida geracao de hoplink:
    1. get_affiliate_hoplink("prostavive")
    2. Assert retorna "https://hop.clickbank.net/?affiliate=MOCK&vendor=prostavive"
    3. Formato exato esperado
    """

def test_clickbank_empty_results():
    """
    Valida API falha silenciosamente:
    1. Mock RealHttpClient para retornar erro 500
    2. search_trending_products()
    3. Assert retorna lista vazia (nao exception)
    """

def test_clickbank_real_opt_in():
    """
    Valida REAL mode (DRY-RUN por padrao):
    1. Cria ClickBankAdapter com SecretProvider (se disponivel)
    2. Se CLICKBANK_API_KEY nao existir → skip
    3. search_trending_products(max_results=5)
    4. Assert retorna ProductOpportunity com dados reais
    5. Assert affiliate_link contem affiliate_id real (nao "MOCK")
    6. Assert gravity_score > 0 (API retorna dados reais)
    
    DRY-RUN: 
    - Sempre pula se CLICKBANK_API_KEY nao estiver definida
    - Se definida, faz exatamente 1 chamada a API
    - Nao excede limite de budget
    """
```

### Regressao

| Teste | Regressao | REAL mode |
|---|---|---|
| `test_clickbank_mock` | Sim | Nao |
| `test_clickbank_mock_filter` | Sim | Nao |
| `test_clickbank_affiliate_hoplink` | Sim | Nao |
| `test_clickbank_empty_results` | Sim | Nao |
| `test_clickbank_real_opt_in` | Sim (skip sem key) | Sim (se key existe) |

---

## 11. O QUE O CODEX PRECISA FAZER

| Arquivo | Acao | Observacao |
|---|---|---|
| `core/tools/providers/clickbank.py` | **Criar** — ClickBankProvider, ClickBankProduct, ClickBankSearchResponse | Seguir pattern de `core/tools/providers/google.py`, `github.py` |
| `core/tools/adapters/clickbank_adapter.py` | **Criar** — ClickBankAdapter | Herdar AbstractToolAdapter; MOCK/REAL; graceful degradation |
| `core/tools/providers/__init__.py` | **Adicionar** export do ClickBankProvider | Aditivo, nao quebrar exports existentes |
| `core/tools/adapters/__init__.py` | **Adicionar** export do ClickBankAdapter | Aditivo |
| `secrets/clickbank.env` | **Criar** — placeholder | IGNORADO pelo git, Shin preenche |
| `demo_clickbank_adapter.py` | **Criar** — demo com assertions | 5 testes, regressao completa |
| `.gitignore` | **Verificar** se `secrets/` ja esta ignorado | Se nao estiver, adicionar |
| `scripts/run_all_demos.py` | **Nao modificar** | O script ja descobre demos por glob — so adicionar o arquivo |

### Nao fazer

- Nao modificar `ProductHunterPipeline` ou `ProductHunterEmployee` da Fase 1
- Nao modificar classes existentes em `core/tools/providers/` ou `core/tools/adapters/`
- Nao implementar Google Trends API real (fica para fase futura)
- Nao implementar BuyGoods API (Fase 7)
- Nao criar endpoints de API HTTP (so adapter + provider)
- Nao instalar dependencias externas (tudo urllib-based, como o projeto exige)
- Nao adicionar custo financeiro sem BudgetGuard

### Dependencias

- `AbstractToolAdapter` (ja existe em `core/tools/base.py`)
- `RealHttpClient` (ja existe em `core/tools/http/real_client.py`)
- `SecretProvider` (ja existe em `core/tools/secrets/`)
- `ProviderBudgetGuard` (ja existe em `core/tools/provider_control.py`)
- `RateLimiter` (ja existe em `core/tools/http/rate_limiter.py`)
- `ProductOpportunity`, `TrendCheck` da Fase 1 (ja existem em `core/departments/product_hunter/models.py`)
- `AdapterExecutionResult` (ja existe)

Nenhuma nova dependencia externa. Nenhuma modificacao em arquivos existentes (exceto adicoes aditivas em `__init__.py`).

---

## 12. CHECKLIST DE QUALIDADE

Antes de dar como pronto, o Codex deve verificar:

- [ ] `compileall` passa sem erros em `core/`
- [ ] `demo_clickbank_adapter.py` roda em regressao (modo MOCK) sem nenhuma chamada externa
- [ ] `demo_clickbank_adapter.py` nao aparece em `demo_*.py` que exige opt-in REAL na regressao
- [ ] ClickBankAdapter herda de `AbstractToolAdapter` (nao de outra classe)
- [ ] ClickBankProvider usa `RealHttpClient` (nao `requests`/`httpx`)
- [ ] `set_secret_provider()` e `set_budget_guard()` sao metodos aditivos (opcionais)
- [ ] MOCK mode nunca chama HTTP
- [ ] REAL mode sempre passa por BudgetGuard pre-flight
- [ ] Erro da API nunca quebra a pipeline (sempre fallback gracioso)
- [ ] Hoplink gerado localmente (nunca via API)
- [ ] `secrets/clickbank.env` no `.gitignore`
- [ ] `regressao completa` — 0 falhas, mesmo numero de demos + 1

---

## 13. POS-IMPLEMENTACAO

### Teste REAL (Shin, apos Codex)

1. Criar conta ClickBank em `https://www.clickbank.com/` (Video A 00:03:00 — cadastro gratis)
2. Gerar API key em `Account Settings > API Access`
3. Preencher `secrets/clickbank.env` com:
   ```
   CLICKBANK_API_KEY=<key>
   CLICKBANK_AFFILIATE_ID=<nickname>
   ```
4. Executar `python demo_clickbank_adapter.py` com variavel de ambiente `CLICKBANK_REAL=1`
5. Verificar se retorna produtos REAIS do marketplace
6. Verificar se hoplinks tem o affiliate ID real
7. Verificar se BudgetGuard conta as chamadas corretamente
8. Reportar resultado para atualizar este documento

### Proximo passo (Fase 7)

A Fase 7 implementara o BuyGoodsAdapter seguindo o mesmo pattern,
e o ProductHunterEmployee podera alternar entre MOCK / ClickBank REAL / BuyGoods REAL
via injecao de dependencia.
