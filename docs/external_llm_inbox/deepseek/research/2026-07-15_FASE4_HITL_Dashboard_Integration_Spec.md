# FASE 4 — Integracao HITL + Dashboard

## 1. Objective

Nova aba **"Afiliado Gringa"** no Factory Dashboard que centraliza o pipeline completo de produtos do mercado gringo (Amazon US, Digistore24, ClickBank, Braip):

- Produtos do dia vindos do ProductHunter
- Landing pages geradas (preview HTML)
- Campanhas prontas para exportar (JSON)
- Aprovacao HITL para cada etapa
- Status de cada produto visivel em um unico lugar

Inspiracao direta:
- Video B 00:25:00-00:29:00: rotina diaria de analise ANTES de criar — dashboard e o "lugar unico"
- Video B 00:28:00: Flow Track app — gasto vs lucro de manha, inspiracao para o dashboard responsivo
- Video B 00:29:30: pausar keyword que vendia por engano — precisa de historico de acoes
- Video A 00:13:30: gravidade e comissao visiveis para decisao rapida
- Video A 00:15:30: decidir entre produtos com dados comparaveis

---

## 2. Workflow States

Cada oportunidade passa por estes estados, em ordem linear:

```
DISCOVERED ──> LANDING_READY ──> CAMPAIGN_READY ──> APPROVED ──> LIVE ──> PAUSED
                                      │                  │
                                      │  (reject)        │  (reject)
                                      v                  v
                                   REJECTED           REJECTED
                                      │
                                      v
                                   CLOSED
```

| State | Meaning | Trigger |
|---|---|---|
| `DISCOVERED` | Produto encontrado pelo ProductHunter | Scan automatico ou manual |
| `LANDING_READY` | Landing page HTML gerada | "Generate Landing Page" |
| `CAMPAIGN_READY` | JSON de campanha pronto para exportar | "Build Campaign" |
| `APPROVED` | Shin aprovou campanha via HITL | Approve no dashboard |
| `LIVE` | Campanha no ar (Google Ads ou MOCK) | Export + confirmacao |
| `PAUSED` | Campanha pausada manualmente | Botao "Pause" |
| `REJECTED` | Shin rejeitou com motivo | Reject + motivo |
| `CLOSED` | Produto arquivado, nao reaparece | Botao "Close" |

Transicoes possiveis:
- De `LANDING_READY` pode voltar para `DISCOVERED` se regenerar landing
- De `CAMPAIGN_READY` pode voltar para `LANDING_READY` se alterar oferta
- De `REJECTED` pode reabrir para `DISCOVERED` (Shin muda de ideia)
- `LIVE` e `PAUSED` sao terminais ate decisao manual

---

## 3. Dashboard Section — "Afiliado Gringa"

### 3.1 Summary Bar

Quatro cards no topo, atualizados em cada GET /api/gringa/products:

| Metric | Label | Example |
|---|---|---|
| Total oportunidades hoje | `opportunities_today` | 12 |
| Quentes (score >= 7) | `hot_count` | 4 |
| Landing pages prontas | `landing_ready_count` | 2 |
| Campanhas pendentes de aprovacao | `pending_approval_count` | 3 |

### 3.2 Product Table

Colunas:

| Column | Content |
|---|---|
| Produto | `product_name` (linkavel) |
| Plataforma | Badge: Amazon / Digistore24 / ClickBank / Braip |
| Comissao | `commission` + `commission_type` (ex: "$45.60", "40%") |
| Score | Numero 1-10 com cor (verde >=7, amarelo 4-6, vermelho <=3) |
| Tendencia | Icone + texto: `↑ 12%` / `→ 0%` / `↓ -5%` |
| Status | Badge colorido com o estado atual |
| Acoes | Botoes contextuais (Gerate, Build, Approve, Reject) |

Ordenacao padrao: score descending. Filtros: por plataforma, status, score range.

### 3.3 Detail Panel

Ao clicar em uma linha, abrir painel lateral (ou modal em mobile) com abas:

**Aba 1 — Produto**
- Nome, preco, comissao, gravidade, URL do marketplace
- Score detalhado (sub-scores: demanda, concorrencia, margem, confianca)
- Trend chart text: "Rising 12% in last 7 days" / "Stable" / "Falling 5%"
- Fonte da descoberta (ProductHunter, manual, etc.)
- Timestamp da primeira deteccao

**Aba 2 — Landing Page**
- Preview HTML embutido (iframe com srcdoc) ou link file:///
- Botao "Generate Landing Page" (se DISCOVERED) → muda para LANDING_READY
- Botao "Regenerate" (se LANDING_READY) → regenera e mantem estado
- Status: "Not generated" / "Generated at 2026-07-15 10:30"
- Caminho do arquivo: `landing_path`

**Aba 3 — Campaign**
- JSON formatado com syntax highlight
- Download button (download .json)
- Botao "Build Campaign" (se LANDING_READY) → muda para CAMPAIGN_READY
- Botao "Mark Ready" (apos download manual)
- Status: "Not built" / "Built at 2026-07-15 11:00"

**Aba 4 — Approval**
- Historico de aprovacoes/rejeicoes (timestamp + quem)
- Botoes: "Approve Campaign" / "Reject Campaign"
- Campo de texto para rejection reason
- Se aprovado: mostra "Approved by Shin at 2026-07-15 11:30"
- Se rejeitado: mostra motivo em vermelho

**Aba 5 — History**
- Log de todas as acoes (scan, generate, build, approve, reject, pause, close)
- Timestamp, acao, detalhe

### 3.4 Action Buttons (fora da tabela)

| Button | Action | API |
|---|---|---|
| "Scan Now" | Trigger ProductHunter scan | `POST /api/gringa/scan` |
| "Generate All Hot" | Gera landing page para todos score >= 7 em DISCOVERED | `POST /api/gringa/generate-all-hot` |
| "Build All Ready" | Gera campaign JSON para todos LANDING_READY | `POST /api/gringa/build-all-ready` |
| "Approve All Pending" | Aprova todos CAMPAIGN_READY | `POST /api/gringa/approve-all-pending` |

Cada botao multi-item exige confirmacao modal: "Isso vai afetar N produtos. Continuar?"

---

## 4. Models

### 4.1 GringaProductStatus (enum)

```python
@unique
class GringaProductStatus(str, Enum):
    DISCOVERED = "discovered"
    LANDING_READY = "landing_ready"
    CAMPAIGN_READY = "campaign_ready"
    APPROVED = "approved"
    LIVE = "live"
    PAUSED = "paused"
    REJECTED = "rejected"
    CLOSED = "closed"
```

### 4.2 GringaProductRecord (frozen+slots)

```python
@dataclass(frozen=True, slots=True)
class GringaProductRecord:
    product_id: str                          # hash unico (ex: "prostavive_20260715")
    product_name: str
    platform: str                            # "amazon" | "digistore24" | "clickbank" | "braip"
    product_url: str
    price: float
    currency: str                            # "USD" | "BRL"
    commission: float
    commission_type: str                     # "fixed" | "percentage"
    gravity: float                           # gravidade ClickBank / popularidade
    score: int                               # 1-10
    trend_direction: str                     # "rising" | "stable" | "falling"
    trend_percent: float                     # -100 a +100
    status: GringaProductStatus
    landing_path: str | None                 # caminho para HTML da landing page
    campaign_path: str | None                # caminho para JSON da campanha
    approved_by: str | None                  # "shin" | None
    approved_at: str | None                  # ISO timestamp
    rejected_reason: str | None
    rejected_at: str | None
    discovered_at: str                       # ISO timestamp
    updated_at: str                          # ISO timestamp
    history: tuple[ActionLog, ...]           # frozen tuple de logs
```

### 4.3 ActionLog (frozen+slots)

```python
@dataclass(frozen=True, slots=True)
class ActionLog:
    timestamp: str
    action: str       # "scan" | "generate_landing" | "build_campaign" | "approve" | "reject" | "pause" | "close"
    detail: str
    by: str           # "system" | "shin"
```

### 4.4 GringaDashboardState (frozen+slots)

```python
@dataclass(frozen=True, slots=True)
class GringaDashboardState:
    products: tuple[GringaProductRecord, ...]
    last_scan_date: str | None               # ISO timestamp
    last_scan_result: str | None             # "success" | "error" | None

    @property
    def opportunities_today(self) -> int:
        return len(self.products)

    @property
    def hot_count(self) -> int:
        return sum(1 for p in self.products if p.score >= 7 and p.status in (
            GringaProductStatus.DISCOVERED,
            GringaProductStatus.LANDING_READY,
            GringaProductStatus.CAMPAIGN_READY,
        ))

    @property
    def landing_ready_count(self) -> int:
        return sum(1 for p in self.products if p.status == GringaProductStatus.LANDING_READY)

    @property
    def pending_approval_count(self) -> int:
        return sum(1 for p in self.products if p.status == GringaProductStatus.CAMPAIGN_READY)
```

---

## 5. Integration with HITLApprovalGateway

### 5.1 New Approval Type

Adicionar ao `core/company/hitl_gateway.py` (aditivo, sem quebrar existente):

```python
@dataclass(frozen=True, slots=True)
class GringaCampaignApprovalRequest:
    """Novo tipo de aprovacao para campanhas gringas."""
    product_id: str
    product_name: str
    platform: str
    landing_page_url: str
    campaign_budget: float
    estimated_roi: float
    score: int
    tags: tuple[str, ...] = ()
```

Adicionar ao HITLApprovalGateway:

```python
def submit_gringa_campaign(
    self,
    request: GringaCampaignApprovalRequest,
) -> HITLApprovalTicket:
    """Submete campanha gringa para aprovacao HITL."""
    return self._create_ticket(
        item_id=request.product_id,
        item_type="gringa_campaign",
        summary=f"{request.product_name} ({request.platform}) — ROI estimado {request.estimated_roi:.0%}",
        details={
            "product_name": request.product_name,
            "platform": request.platform,
            "landing_page_url": request.landing_page_url,
            "budget": request.campaign_budget,
            "estimated_roi": request.estimated_roi,
            "score": request.score,
        },
        tags=request.tags,
    )
```

### 5.2 Approval Callback

Quando ticket e aprovado:

```python
def _on_approve(self, ticket: HITLApprovalTicket) -> None:
    if ticket.item_type == "gringa_campaign":
        self._gringa_dashboard.set_product_status(
            product_id=ticket.item_id,
            new_status=GringaProductStatus.APPROVED,
            approved_by="shin",
        )
```

### 5.3 Rejection Callback

Quando ticket e rejeitado:

```python
def _on_reject(self, ticket: HITLApprovalTicket) -> None:
    if ticket.item_type == "gringa_campaign":
        reason = ticket.details.get("rejection_reason", "No reason provided")
        self._gringa_dashboard.set_product_status(
            product_id=ticket.item_id,
            new_status=GringaProductStatus.REJECTED,
            rejected_reason=reason,
        )
```

### 5.4 Wiring

`GringaApprovalDashboard` aceita injecao de `HITLApprovalGateway` via setter:

```python
def set_hitl_gateway(self, gateway: HITLApprovalGateway) -> None:
    self._hitl_gateway = gateway
```

Quando Shin clica "Approve" no dashboard, o fluxo e:

1. Dashboard chama `POST /api/gringa/products/{id}/approve`
2. Backend cria `GringaCampaignApprovalRequest`
3. Submete via `gateway.submit_gringa_campaign()`
4. Gateway cria `HITLApprovalTicket` com status `pending`
5. Se gateway esta em modo auto-approve (MOCK), aprova imediatamente
6. Callback `_on_approve` muda status para `APPROVED`
7. Dashboard recarrega e mostra badge verde

---

## 6. Persistence

### 6.1 Directory Structure

```
.ai_company/gringa_affiliate/
    products/
        prostavive_20260715.json
        matsato_20260715.json
        ...
    state.json                  # GringaDashboardState serializado
    history_log.jsonl           # Append-only log de todas as acoes
```

### 6.2 File Format (product record)

```json
{
    "product_id": "prostavive_20260715",
    "product_name": "ProstaVive",
    "platform": "digistore24",
    "product_url": "https://www.digistore24.com/...",
    "price": 49.00,
    "currency": "USD",
    "commission": 34.30,
    "commission_type": "fixed",
    "gravity": 12.5,
    "score": 8,
    "trend_direction": "rising",
    "trend_percent": 12.0,
    "status": "discovered",
    "landing_path": null,
    "campaign_path": null,
    "approved_by": null,
    "approved_at": null,
    "rejected_reason": null,
    "rejected_at": null,
    "discovered_at": "2026-07-15T06:00:00Z",
    "updated_at": "2026-07-15T06:00:00Z",
    "history": [
        {
            "timestamp": "2026-07-15T06:00:00Z",
            "action": "scan",
            "detail": "Discovered via ProductHunter scan",
            "by": "system"
        }
    ]
}
```

### 6.3 Store Pattern

Seguir o padrao de `AffiliateDashboardStore` mas simplificado:

```python
class GringaProductStore:
    def __init__(self, base_path: str = ".ai_company/gringa_affiliate/"):
        self._base_path = base_path
        self._products_dir = os.path.join(base_path, "products")
        os.makedirs(self._products_dir, exist_ok=True)

    def save_product(self, record: GringaProductRecord) -> None:
        path = os.path.join(self._products_dir, f"{record.product_id}.json")
        with open(path, "w", encoding="utf-8") as f:
            json.dump(asdict(record), f, indent=2, ensure_ascii=False)

    def load_product(self, product_id: str) -> GringaProductRecord | None:
        path = os.path.join(self._products_dir, f"{product_id}.json")
        if not os.path.exists(path):
            return None
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return GringaProductRecord(**data)

    def load_all_products(self) -> list[GringaProductRecord]:
        products = []
        for fname in os.listdir(self._products_dir):
            if fname.endswith(".json"):
                with open(os.path.join(self._products_dir, fname), "r", encoding="utf-8") as f:
                    data = json.load(f)
                products.append(GringaProductRecord(**data))
        return sorted(products, key=lambda p: p.score, reverse=True)

    def append_history(self, product_id: str, log: ActionLog) -> None:
        path = os.path.join(self._products_dir, f"{product_id}.json")
        if os.path.exists(path):
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
            data["history"].append(asdict(log))
            data["updated_at"] = log.timestamp
            with open(path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
```

---

## 7. Page Structure (HTML pseudo-code)

### 7.1 Layout (single page application dentro da tab)

```
+------------------------------------------------------------------+
| [Summary Bar]                                                     |
| +----------+ +----------+ +----------+ +----------+               |
| |Total: 12 | |Hot: 4    | |Landing: 2| |Pending: 3|              |
| +----------+ +----------+ +----------+ +----------+               |
+------------------------------------------------------------------+
| [Action Buttons Bar]                                              |
| [Scan Now] [Generate All Hot] [Build All Ready] [Approve All Pnd]|
+------------------------------------------------------------------+
| [Filters]                                                         |
| Plataforma: [All v]  Score: [1-10]  Status: [All v]              |
+------------------------------------------------------------------+
| [Product Table]                                                   |
| Produto      | Plataf | Comissao | Score | Tend | Status  | Acoes |
|--------------|--------|----------|-------|------|---------|-------|
| ProstaVive   | D24    | $34.30   | 8     | ↑12% | 📄 Ready| [Ap]  |
| Matsato      | CB     | $19.80   | 6     | →0%  | 🔍 Disc | [Gn]  |
| ...                                                               |
+------------------------------------------------------------------+
| [Detail Panel - slides in from right]                             |
| +------------------------------------------------------------+   |
| | Product: ProstaVive                                        |   |
| | [Aba: Product] [Landing] [Campaign] [Approval] [History]   |   |
| |                                                            |   |
| | (conteudo da aba ativa)                                    |   |
| |                                                            |   |
| | [Close]                                                    |   |
| +------------------------------------------------------------+   |
+------------------------------------------------------------------+
```

### 7.2 Dark Theme

Reutilizar o tema Operacional (dark) do Factory Dashboard V2:

```css
:root {
    --bg-primary: #0a0e17;
    --bg-secondary: #111827;
    --bg-card: #1a2234;
    --text-primary: #e2e8f0;
    --text-secondary: #94a3b8;
    --accent-green: #22c55e;
    --accent-yellow: #eab308;
    --accent-red: #ef4444;
    --accent-blue: #3b82f6;
    --border: #1e293b;
}
```

### 7.3 Approval Modal

```html
<div id="approval-modal" class="modal hidden">
    <div class="modal-backdrop"></div>
    <div class="modal-content">
        <h2>Approve Campaign</h2>
        <p>Product: <strong>{product_name}</strong></p>
        <p>Platform: {platform}</p>
        <p>Score: {score}/10</p>
        <p>Commission: ${commission}</p>
        <p>Estimated ROI: {estimated_roi}%</p>
        <div class="modal-actions">
            <button class="btn btn-danger" onclick="rejectCampaign('{id}')">
                Reject
            </button>
            <button class="btn btn-success" onclick="approveCampaign('{id}')">
                Approve
            </button>
        </div>
        <div id="reject-reason-field" class="hidden">
            <label>Reason for rejection:</label>
            <textarea id="reject-reason" rows="3"></textarea>
            <button class="btn btn-danger" onclick="confirmReject('{id}')">
                Confirm Rejection
            </button>
        </div>
    </div>
</div>
```

### 7.4 Routing

A aba "Afiliado Gringa" segue o mesmo padrao das abas existentes no Factory Dashboard:

```javascript
// Dentro do switch de abas existente
if (tab === 'gringa') {
    loadGringaDashboard();
}

function loadGringaDashboard() {
    fetch('/api/gringa/products')
        .then(r => r.json())
        .then(state => {
            renderSummaryBar(state);
            renderTable(state.products);
            renderActions(state);
        });
}
```

---

## 8. API Endpoints

### 8.1 GET /api/gringa/products

**Response**:

```json
{
    "products": [ /* GringaProductRecord[] serializado */ ],
    "summary": {
        "opportunities_today": 12,
        "hot_count": 4,
        "landing_ready_count": 2,
        "pending_approval_count": 3
    },
    "last_scan_date": "2026-07-15T06:00:00Z",
    "last_scan_result": "success"
}
```

### 8.2 POST /api/gringa/scan

Trigger ProductHunter scan. Em MOCK, adiciona 1-2 produtos pre-definidos.

**Request**: `{}`

**Response**:

```json
{
    "success": true,
    "new_products": 2,
    "message": "Scan completed. 2 new opportunities found."
}
```

### 8.3 POST /api/gringa/products/{id}/approve

**Request**:

```json
{
    "approved_by": "shin"
}
```

**Response**:

```json
{
    "success": true,
    "product_id": "prostavive_20260715",
    "new_status": "approved",
    "ticket_id": "tkt_gringa_001"
}
```

### 8.4 POST /api/gringa/products/{id}/reject

**Request**:

```json
{
    "reason": "Commission too low for ad spend"
}
```

**Response**:

```json
{
    "success": true,
    "product_id": "prostavive_20260715",
    "new_status": "rejected",
    "rejected_reason": "Commission too low for ad spend"
}
```

### 8.5 GET /api/gringa/products/{id}/landing-page

**Response**: HTML content (Content-Type: text/html). Em MOCK, retorna HTML placeholder.

### 8.6 POST /api/gringa/generate-all-hot

Gera landing pages para todos DISCOVERED com score >= 7.

**Response**:

```json
{
    "success": true,
    "generated": ["prostavive_20260715"],
    "failed": [],
    "skipped": ["matsato_20260715"]  // score < 7
}
```

### 8.7 POST /api/gringa/build-all-ready

Build campaign JSON para todos LANDING_READY.

**Response**: similar ao anterior.

### 8.8 POST /api/gringa/approve-all-pending

Aprova todos CAMPAIGN_READY via HITL gateway.

**Response**:

```json
{
    "success": true,
    "approved": ["prostavive_20260715"],
    "rejected": [],
    "tickets": ["tkt_gringa_001"]
}
```

---

## 9. Server Integration

### 9.1 HTTPHandler Pattern

Reutilizar `SimpleHTTPRequestHandler` do `affiliate_dashboard_server.py`:

```python
class GringaDashboardHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/api/gringa/products":
            self._handle_get_products()
        elif match := re.match(r"/api/gringa/products/([^/]+)/landing-page", self.path):
            self._handle_get_landing_page(match.group(1))
        else:
            self.send_response(404)
            self.end_headers()

    def do_POST(self):
        if self.path == "/api/gringa/scan":
            self._handle_scan()
        elif match := re.match(r"/api/gringa/products/([^/]+)/approve", self.path):
            self._handle_approve(match.group(1))
        elif match := re.match(r"/api/gringa/products/([^/]+)/reject", self.path):
            self._handle_reject(match.group(1))
        elif self.path == "/api/gringa/generate-all-hot":
            self._handle_generate_all_hot()
        elif self.path == "/api/gringa/build-all-ready":
            self._handle_build_all_ready()
        elif self.path == "/api/gringa/approve-all-pending":
            self._handle_approve_all_pending()
        else:
            self.send_response(404)
            self.end_headers()
```

### 9.2 CORS and MOCK mode

Mesmo padrao: headers CORS, `ExecutionMode.MOCK` como default, `execution_mode.set()` para REAL.

---

## 10. Demo Outline

### 10.1 File: `demo_gringa_dashboard_integration.py`

```python
"""
Demo FASE 4 — Integracao HITL + Dashboard Afiliado Gringa.

Valida:
- Criacao de GringaDashboardState com produtos seed
- Status counts corretos no summary
- Aprovacao HITL via gateway
- Rejeicao com motivo
- Persistencia em .ai_company/gringa_affiliate/
- HTML render sem erros
- Nenhuma chamada REAL (modo MOCK)

Assertions esperadas: ~35
"""
```

### 10.2 Seed Data

```python
seed_products = (
    GringaProductRecord(
        product_id="prostavive_20260715",
        product_name="ProstaVive",
        platform="digistore24",
        product_url="https://www.digistore24.com/...",
        price=49.00,
        currency="USD",
        commission=34.30,
        commission_type="fixed",
        gravity=12.5,
        score=8,
        trend_direction="rising",
        trend_percent=12.0,
        status=GringaProductStatus.DISCOVERED,
        landing_path=None,
        campaign_path=None,
        approved_by=None,
        approved_at=None,
        rejected_reason=None,
        rejected_at=None,
        discovered_at="2026-07-15T06:00:00Z",
        updated_at="2026-07-15T06:00:00Z",
        history=(ActionLog("2026-07-15T06:00:00Z", "scan", "Discovered via ProductHunter", "system"),),
    ),
    GringaProductRecord(
        product_id="matsato_20260715",
        product_name="Matsato",
        platform="clickbank",
        product_url="https://www.clickbank.com/...",
        price=37.00,
        currency="USD",
        commission=19.80,
        commission_type="fixed",
        gravity=3.2,
        score=6,
        trend_direction="stable",
        trend_percent=0.0,
        status=GringaProductStatus.DISCOVERED,
        landing_path=None,
        campaign_path=None,
        approved_by=None,
        approved_at=None,
        rejected_reason=None,
        rejected_at=None,
        discovered_at="2026-07-15T06:30:00Z",
        updated_at="2026-07-15T06:30:00Z",
        history=(ActionLog("2026-07-15T06:30:00Z", "scan", "Discovered via ProductHunter", "system"),),
    ),
)
```

### 10.3 Assertions

```python
def test_dashboard_seeding():
    state = GringaDashboardState(products=seed_products, last_scan_date="2026-07-15T06:30:00Z")
    assert state.opportunities_today == 2
    assert state.hot_count == 1  # ProstaVive score=8 >= 7
    assert state.landing_ready_count == 0
    assert state.pending_approval_count == 0
    assert state.last_scan_date == "2026-07-15T06:30:00Z"

def test_generate_landing():
    store = GringaProductStore()
    state = GringaDashboardState(products=seed_products, last_scan_date="2026-07-15T06:30:00Z")
    # Gera landing para ProstaVive
    updated = state.set_product_status("prostavive_20260715", GringaProductStatus.LANDING_READY)
    assert updated.hot_count == 1  # ainda hot
    assert updated.landing_ready_count == 1
    # Verifica landing_path foi preenchido (MOCK)
    record = updated.get_product("prostavive_20260715")
    assert record.status == GringaProductStatus.LANDING_READY
    assert record.landing_path is not None

def test_hitl_approval():
    store = GringaProductStore()
    gateway = HITLApprovalGateway()
    dashboard = GringaApprovalDashboard(store=store, hitl_gateway=gateway)
    # Avanca ProstaVive para CAMPAIGN_READY
    state = dashboard.state.set_product_status("prostavive_20260715", GringaProductStatus.CAMPAIGN_READY)
    assert state.pending_approval_count == 1
    # Aprova via HITL
    result = dashboard.approve_product("prostavive_20260715", approved_by="shin")
    assert result["new_status"] == "approved"
    record = store.load_product("prostavive_20260715")
    assert record.status == GringaProductStatus.APPROVED
    assert record.approved_by == "shin"

def test_rejection():
    store = GringaProductStore()
    gateway = HITLApprovalGateway()
    dashboard = GringaApprovalDashboard(store=store, hitl_gateway=gateway)
    # Rejeita Matsato
    result = dashboard.reject_product("matsato_20260715", reason="Commission too low for ad spend")
    assert result["new_status"] == "rejected"
    record = store.load_product("matsato_20260715")
    assert record.status == GringaProductStatus.REJECTED
    assert record.rejected_reason == "Commission too low for ad spend"

def test_html_render():
    store = GringaProductStore()
    dashboard = GringaApprovalDashboard(store=store)
    html = dashboard.render_html()
    assert "<!DOCTYPE html>" in html
    assert "Afiliado Gringa" in html
    assert "ProstaVive" in html
    assert "Matsato" in html
    assert "summary-bar" in html
    assert "product-table" in html
    assert html.count("approve") >= 1  # botoes

def test_mock_no_real_calls():
    store = GringaProductStore()
    dashboard = GringaApprovalDashboard(store=store)
    state = dashboard.state
    # Todas as operacoes sao locais, sem HTTP
    updated = state.set_product_status("prostavive_20260715", GringaProductStatus.LANDING_READY)
    assert updated is not None  # nao levanta excecao
    # Nenhuma chamada a provider externo

def test_persistence():
    import tempfile, os
    with tempfile.TemporaryDirectory() as tmpdir:
        store = GringaProductStore(base_path=tmpdir)
        store.save_product(seed_products[0])
        loaded = store.load_product("prostavive_20260715")
        assert loaded is not None
        assert loaded.product_name == "ProstaVive"
        assert loaded.score == 8
        all_prods = store.load_all_products()
        assert len(all_prods) == 1
```

### 10.4 Expected Results

```
GringaDashboardState: 35 assertions, 0 failed
```

---

## 11. What the Codex Needs to Build

### 11.1 Files to Create

| File | Purpose |
|---|---|
| `core/departments/product_hunter/models.py` | GringaProductStatus, GringaProductRecord, ActionLog, GringaDashboardState (frozen+slots) |
| `core/content_factory/gringa_dashboard.py` | GringaApprovalDashboard (renderer HTML + state management + store integration + HITL wiring) |
| `demo_gringa_dashboard_integration.py` | ~35 assertions cobrindo seeding, generate, approve, reject, render, MOCK, persistencia |

### 11.2 Files to Modify (aditivo)

| File | Change |
|---|---|
| `core/company/hitl_gateway.py` | Adicionar `GringaCampaignApprovalRequest` e metodo `submit_gringa_campaign()`. Adicionar callbacks `_on_approve`/`_on_reject` para `gringa_campaign`. Nao quebrar tipos existentes. |
| `core/departments/product_hunter/__init__.py` | Exportar novos modelos |
| `core/content_factory/__init__.py` | Exportar `GringaApprovalDashboard` |

### 11.3 Not in Scope (Phase 4)

- ProductHunter real scan — usa MOCK com dados seed
- Geracao real de landing page — usa template HTML placeholder
- Geracao real de campanha — usa JSON template placeholder
- Integracao com Google Ads — apenas JSON para download
- REAL ExecutionMode — apenas MOCK por enquanto
- Edicao do Factory Dashboard V2 hospedado (Sites) — fase posterior

### 11.4 Integration Test Strategy

1. `demo_gringa_dashboard_integration.py` roda em modo MOCK (default)
2. Nao requer API keys, providers, ou rede
3. Testa estado, transicoes, persistencia, HTML, HITL gateway
4. Pode ser adicionado a `scripts/run_all_demos.py` sem configuracao extra

---

## 12. Video References (documentacao interna)

| Timestamp | Conteudo | Relacao com FASE 4 |
|---|---|---|
| Video B 00:25:00 | Rotina: analisar campanhas PRIMEIRO | Dashboard e o "lugar unico" para analise matinal |
| Video B 00:27:00 | Documentario: organizacao e essencial | Aba unifica descoberta, landing, campanha, aprovacao |
| Video B 00:28:00 | Flow Track app: gasto vs lucro | Dashboard responsivo, summary bar com metricas |
| Video B 00:29:30 | Erro: pausar keyword que vendia | Historico de acoes no detail panel previne erro similar |
| Video A 00:13:30 | Gravidade e comissao visiveis | Colunas na tabela e score detalhado no painel |
| Video A 00:15:30 | Decisao entre produtos com dados | Tabela ordenavel por score, filtros, comparacao |

---

## 13. Risks and Self-Critique

### 13.1 What I (LLM) might have missed

| Risk | Mitigation |
|---|---|
| GringaProductRecord com muitos campos opcionais pode ficar verboso | Todos os campos sao obrigatorios no construtor (frozen+slots); None para opcionais e explicito |
| HITL gateway callback pode duplicar logica se nao for aditivo | Callback verifica `item_type` antes de agir; nao interfere com `gringa_campaign` ou tipos futuros |
| Persistencia JSON pode ficar lenta com muitos produtos | Produtos sao individuais; load_all faz O(N) IO, aceitavel para < 100 produtos |
| HTML preview embutido no dashboard pode ser pesado | Usar iframe com srcdoc; para MVP, link file:/// e suficiente |
| MOCK mode pode esconder erros de serializacao | Demo testa save/load/update cycle completo |

### 13.2 What only Shin/Codex decides

- Nome exato da aba no dashboard (sugerido: "Afiliado Gringa")
- Se o approval modal deve ter campos extras (budget, targeting, etc.)
- Se a landing page preview deve ser iframe ou link externo
- Ordem de prioridade: implementar primeiro o backend ou o frontend
- Se deve integrar com o dashboard hospedado (Sites) agora ou depois

---

## 14. Caminho Critico

```
1. Models (product_hunter/models.py) — 30 min
   ├── GringaProductStatus (enum)
   ├── ActionLog (frozen+slots)
   ├── GringaProductRecord (frozen+slots)
   └── GringaDashboardState (frozen+slots + properties)

2. HITL integration (hitl_gateway.py aditivo) — 30 min
   ├── GringaCampaignApprovalRequest
   ├── submit_gringa_campaign()
   └── callbacks _on_approve / _on_reject

3. Store + Dashboard (gringa_dashboard.py) — 1h
   ├── GringaProductStore (CRUD JSON)
   ├── GringaApprovalDashboard (state management)
   ├── render_html() (full page HTML)
   └── HTTP handlers (8 endpoints)

4. Demo (demo_gringa_dashboard_integration.py) — 30 min
   ├── Seed 2 products
   ├── Test seeding counts (4 assertions)
   ├── Test generate landing (4 assertions)
   ├── Test HITL approval (5 assertions)
   ├── Test rejection (4 assertions)
   ├── Test HTML render (6 assertions)
   ├── Test MOCK no real calls (2 assertions)
   └── Test persistence (6 assertions)

5. compileall + regressao — 10 min

Total estimado: ~2h 40min
```

---

## 15. Checklist para Codex

- [ ] `core/departments/product_hunter/models.py` criado com todos os modelos frozen+slots
- [ ] `core/departments/product_hunter/__init__.py` exporta os novos modelos
- [ ] `core/company/hitl_gateway.py` modificado aditivamente (GringaCampaignApprovalRequest + submit + callbacks)
- [ ] `core/content_factory/gringa_dashboard.py` criado com store + dashboard + renderer + HTTP handlers
- [ ] `core/content_factory/__init__.py` exporta GringaApprovalDashboard
- [ ] `demo_gringa_dashboard_integration.py` criado com ~35 assertions
- [ ] compileall passa sem erros
- [ ] Regressao completa passa (114/114 demos existentes + novo demo)

---

## 16. Prova de Conceito (pre-implementacao)

Antes de implementar, validar este contrato minimo em um prototipo no terminal:

```python
# Prototipo conceitual - apenas para validar contratos
from dataclasses import dataclass

@dataclass(frozen=True, slots=True)
class GringaProductRecord:
    product_id: str
    product_name: str
    score: int
    status: str = "discovered"

state = (
    GringaProductRecord("p1", "ProstaVive", 8),
    GringaProductRecord("p2", "Matsato", 6),
)
hot = [p for p in state if p.score >= 7]
assert len(hot) == 1
assert hot[0].product_name == "ProstaVive"
print("Contrato de dados validado:", len(state), "produtos,", len(hot), "hot")
```

Este prototipo e apenas para confirmar que frozen+slots funciona e o modelo de dados e viavel.
