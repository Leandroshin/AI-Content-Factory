# FASE 5 — Notificacao Telegram Diaria

## 1. Objective

Every morning at 9 AM (configurable), the factory sends a Telegram message to Shin with:
- Top 3 product opportunities of the day (from ProductHunter report)
- Each with: product_name, commission, trend curve, score, recommendation
- Action link to the dashboard for approval
- Summary: "X hot, Y warm, Z cold today"

**Why:** Shin should not need to open the dashboard every morning. The notification replaces the need to check the computer — just look at Telegram and decide.

### Video References
- **Video B 00:25:00-00:26:00**: Morning routine (wake up, coffee, check campaigns). The Telegram digest replaces opening the laptop.
- **Video C 00:05:10-00:08:00**: Viral monitor sends YouTube alerts to Telegram automatically. Same pattern: system → Telegram push.
- **Video B 00:28:00**: Flow Track app — Shin wants to see spend vs profit in the morning. Our Telegram digest can deliver that.

---

## 2. Models (frozen+slots)

### `DailyDigestConfig` — `core/content_factory/gringa_daily_digest.py`

```python
@dataclass(frozen=True, slots=True)
class DailyDigestConfig:
    chat_id: str                    # Telegram chat ID (shin's)
    send_time: str = "09:00"        # HH:MM format
    timezone: str = "America/Sao_Paulo"
    max_products: int = 3           # Top N products to include
    include_summary: bool = True    # Include hot/warm/cold summary line
    include_dashboard_link: bool = True  # Include action link to dashboard
    locale: str = "pt-BR"           # Message language
```

### `DigestMessage` — the formatted payload ready to send

```python
@dataclass(frozen=True, slots=True)
class DigestMessage:
    text: str                       # Full formatted message (Telegram-safe, < 4096 chars)
    photo_url: str | None = None    # Optional product photo/thumbnail
```

### `DailyDigestResult` — outcome of sending

```python
@dataclass(frozen=True, slots=True)
class DailyDigestResult:
    sent_at: str                    # ISO timestamp
    message_id: int | None          # Telegram message_id on success
    products_included: int
    success: bool
    error: str | None = None
```

---

## 3. Message Format (compact, Telegram-style)

### Template with 3 hot products

```
🔥 AFILIADO GRINGA — TOP 3 OPORTUNIDADES
📅 15/07/2026

1. ProstaVive (ClickBank)
💰 $175.60 comissao | 📈 Subindo +25%
⭐ Score: 89 — RECOMENDADO
🔗 Ver no dashboard: https://central-ai-content-factory.leandro-az-v.chatgpt.site/?approve=prod_123

2. Ignatra (ClickBank)
💰 $180.00 comissao | 📈 Subindo +17%
⭐ Score: 85 — RECOMENDADO
🔗 Ver no dashboard: https://central-ai-content-factory.leandro-az-v.chatgpt.site/?approve=prod_456

3. Prodentin (ClickBank)
💰 $140.00 comissao | 📈 Subindo +8%
⭐ Score: 72 — ATENCAO
🔗 Ver no dashboard: https://central-ai-content-factory.leandro-az-v.chatgpt.site/?approve=prod_789

📊 Hoje: 3 🔥 hot | 2 ⚡ warm | 1 ❄️ cold
```

### Fallback — empty/no hot products

```
❌ AFILIADO GRINGA — TOP 3 OPORTUNIDADES
📅 15/07/2026

Nenhum produto em alta hoje. O mercado esta frio.

📊 Hoje: 0 🔥 hot | 0 ⚡ warm | 0 ❄️ cold
```

### Single hot product variation

```
🔥 AFILIADO GRINGA — 1 OPORTUNIDADE QUENTE
📅 15/07/2026

1. ProstaVive (ClickBank)
💰 $175.60 comissao | 📈 Subindo +25%
⭐ Score: 89 — RECOMENDADO
🔗 Ver no dashboard: https://central-ai-content-factory.leandro-az-v.chatgpt.site/?approve=prod_123

📊 Hoje: 1 🔥 hot | 3 ⚡ warm | 2 ❄️ cold
```

### Design rules (from `formatter.py` patterns):
- Bold header with emoji: `🔥 AFILIADO GRINGA`
- Each product: number + name + source in parentheses
- Commission + trend on same line with emoji separators
- Score line with colord status (RECOMENDADO / ATENCAO)
- Action link per product (dashboard URL with product ID)
- Summary line always at bottom
- Total length must be under 4096 characters (Telegram limit)
- No markdown bold/italic — use plain text + emoji only

---

## 4. Integration Pattern

### `DailyDigestService` — core logic

```
Input:  DailyDigestConfig + HunterReport data (from persistence)
Flow:
  1. Load latest HunterReport from PersistenceRuntime
  2. Sort products by score descending
  3. Classify each product: score >= 80 = hot, >= 60 = warm, < 60 = cold
  4. Build DigestMessage text using formatter-like helpers
  5. Call TelegramAdapter.send_message(chat_id, digest_text)
  6. Build DailyDigestResult from Telegram response
  7. Log result to persistence (optional, for observability)
Output: DailyDigestResult
```

### HunterReport data contract (expected shape):

```python
@dataclass(frozen=True, slots=True)
class HunterProduct:
    product_id: str
    product_name: str
    source: str                     # e.g. "ClickBank", "Digistore24"
    commission: float               # e.g. 175.60
    currency: str = "USD"
    trend_direction: str            # "up", "down", "stable"
    trend_percentage: float         # e.g. 25.0
    score: float                    # 0-100
    status: str = "hot"             # "hot", "warm", "cold"

@dataclass(frozen=True, slots=True)
class HunterReport:
    date: str                       # ISO date
    products: list[HunterProduct]
    summary: dict | None = None     # e.g. {"hot": 3, "warm": 2, "cold": 1}
```

---

## 5. Scheduling

| Env | Method | Notes |
|---|---|---|
| MOCK / demo | Manual trigger via `DailyDigestWorker.run()` | Called from demo script or dashboard button |
| REAL (future) | Cron job (Linux VPS) | `0 9 * * * cd /path && python -c "from core.content_factory.gringa_daily_digest import DailyDigestWorker; DailyDigestWorker().run()"` |
| REAL (future) | GitHub Action | Scheduled workflow with SSH or direct call |
| REAL (future) | Windows Task Scheduler | If running on local machine |

The worker itself is scheduling-agnostic. It just needs the data to be available.

---

## 6. Adapter/Script — `DailyDigestWorker`

```python
class DailyDigestWorker:
    """
    Standalone class that can be called from:
    - Demo script
    - Dashboard "Enviar Digest Agora" button
    - Automated scheduler (cron/GitHub Action)
    """

    def __init__(
        self,
        config: DailyDigestConfig,
        telegram_adapter: TelegramAdapter,
        persistence: PersistenceRuntime | None = None,
    ):
        ...

    def run(self) -> DailyDigestResult:
        """Execute full digest cycle: load → format → send → log."""
        ...

    def build_message(self, report: HunterReport) -> DigestMessage:
        """Format HunterReport into DigestMessage (no side effects, testable)."""
        ...

    def classify(self, score: float) -> str:
        """Return 'hot', 'warm', or 'cold'."""
        ...
```

### Behavior matrix:

| Scenario | Message | Telegram action |
|---|---|---|
| Report has 3+ hot products | Top 3, full summary | `send_message` |
| Report has 1 hot product | "1 oportunidade quente" header, show it | `send_message` |
| Report has 0 hot products | "Nenhum produto em alta" fallback | `send_message` |
| No report found | Error message, log warning | `send_message` with error text |
| Telegram fails (401, timeout) | Log error, write to file | No Telegram call |
| Message > 4096 chars | Truncate products, retry | `send_message` with truncated version |

---

## 7. Message Variations

### No hot products
```
❌ AFILIADO GRINGA — TOP 3 OPORTUNIDADES
📅 15/07/2026

Nenhum produto em alta hoje. O mercado esta frio.

📊 Hoje: 0 🔥 hot | 0 ⚡ warm | 0 ❄️ cold
```

### Single hot product
```
🔥 AFILIADO GRINGA — 1 OPORTUNIDADE QUENTE
📅 15/07/2026

1. ProstaVive (ClickBank)
💰 $175.60 comissao | 📈 Subindo +25%
⭐ Score: 89 — RECOMENDADO
🔗 Ver no dashboard: [link]

📊 Hoje: 1 🔥 hot | 3 ⚡ warm | 2 ❄️ cold
```

### Telegram adapter failure
- Log: `DailyDigestWorker: Telegram send_message failed: 401 Unauthorized`
- Write digest text to `output/daily_digest/{date}_fallback.txt`
- Return `DailyDigestResult(success=False, error="401 Unauthorized")`

### No HunterReport available (first run, no data yet)
- Log: `DailyDigestWorker: No HunterReport found for today. Skipping digest.`
- Return `DailyDigestResult(success=False, error="No data")`

---

## 8. Demo Outline

File: `demo_gringa_daily_digest.py`

### Assertions (24 expected):

```python
def test_daily_digest():
    # Setup
    config = DailyDigestConfig(chat_id="@shin")
    adapter = MockTelegramAdapter()
    worker = DailyDigestWorker(config, adapter)

    # Seed 2 hot products
    report = HunterReport(
        date="2026-07-15",
        products=[
            HunterProduct(product_id="p1", product_name="ProstaVive", source="ClickBank",
                          commission=175.60, currency="USD", trend_direction="up",
                          trend_percentage=25.0, score=89, status="hot"),
            HunterProduct(product_id="p2", product_name="Ignatra", source="ClickBank",
                          commission=180.00, currency="USD", trend_direction="up",
                          trend_percentage=17.0, score=85, status="hot"),
        ],
        summary={"hot": 2, "warm": 0, "cold": 0}
    )

    # Build message
    msg = worker.build_message(report)

    assert "AFILIADO GRINGA" in msg.text                   # Header
    assert "ProstaVive" in msg.text                         # Product 1 name
    assert "Ignatra" in msg.text                            # Product 2 name
    assert "$175.60" in msg.text                            # Commission formatted
    assert "$180.00" in msg.text                            # Commission formatted
    assert "RECOMENDADO" in msg.text                        # Score label
    assert "Ver no dashboard" in msg.text                   # Action link
    assert "2 🔥 hot" in msg.text                           # Summary
    assert len(msg.text) < 4096                             # Telegram limit

    # Send
    result = worker.run()

    assert result.success is True
    assert result.products_included == 2
    assert result.message_id is not None

    # Empty report
    empty = HunterReport(date="2026-07-15", products=[], summary={"hot": 0, "warm": 0, "cold": 0})
    msg_empty = worker.build_message(empty)
    assert "Nenhum produto em alta" in msg_empty.text
```

### What the demo validates:
1. Message header is present
2. Product names appear
3. Commission values are formatted with currency
4. Score labels are present
5. Dashboard link is included
6. Summary line shows counts
7. Message is under Telegram's 4096 character limit
8. TelegramAdapter.send_message was called
9. Result contains message_id on success
10. Empty report generates fallback message

---

## 9. O que o Codex precisa fazer

### File to create: `core/content_factory/gringa_daily_digest.py`

| Component | Lines (estimated) | Responsibility |
|---|---|---|
| `DailyDigestConfig` | ~12 | frozen+slots config |
| `DigestMessage` | ~6 | frozen+slots payload |
| `DailyDigestResult` | ~8 | frozen+slots outcome |
| `HunterProduct` | ~15 | frozen+slots product data |
| `HunterReport` | ~8 | frozen+slots report container |
| `DailyDigestService.build_message()` | ~40 | Format logic (header, products, summary, fallback) |
| `DailyDigestService.classify()` | ~5 | score → hot/warm/cold |
| `DailyDigestService.send_digest()` | ~15 | Call TelegramAdapter, build result |
| `DailyDigestWorker.run()` | ~20 | Load report, build, send, log |

Total: ~130 lines, no new adapter (reuses `TelegramAdapter`)

### What does NOT change:
- `core/tools/adapters/telegram_adapter.py` — untouched, just called
- `core/departments/affiliate_deals/formatter.py` — used as reference for format, not modified
- `core/content_factory/affiliate_dashboard_server.py` — not modified
- No new providers, no new adapters

### File to create: `demo_gringa_daily_digest.py`

- ~80 lines, 24 assertions
- Uses `MockTelegramAdapter` (no real Telegram calls)
- Seeded HunterReport with 2 hot products
- Validates format, length, content, and fallback

---

## 10. Architecture Diagram

```
┌──────────────────────────────────────────────────┐
│              DailyDigestWorker.run()              │
│                                                    │
│  1. Load HunterReport                             │
│     ├─ from PersistenceRuntime (JSON)             │
│     └─ or from in-memory (demo)                   │
│                                                    │
│  2. build_message(report) → DigestMessage         │
│     ├─ Header: 🔥 AFILIADO GRINGA + date         │
│     ├─ For each product: name, commission, trend  │
│     │  score, status, dashboard link              │
│     └─ Summary: X hot, Y warm, Z cold             │
│                                                    │
│  3. send_digest(digest) → DailyDigestResult       │
│     └─ TelegramAdapter.send_message(chat_id, text)│
│                                                    │
│  4. Log result                                     │
│     ├─ Success → observability event              │
│     └─ Failure → fallback file + log              │
└──────────────────────────────────────────────────┘
```

---

## 11. Video Reference Details

| Video | Timestamp | Context | Our implementation |
|---|---|---|---|
| B | 00:25:00-00:26:00 | Acordar, cafe, olhar campanhas no computador | A notificacao no Telegram substitui abrir o PC |
| C | 00:05:10-00:08:00 | Viral monitor envia alertas do YouTube pro Telegram | Mesmo padrao: sistema empurra informacao pro Telegram |
| B | 00:28:00 | Flow Track: ver gasto vs lucro de manha | Podemos expandir o digest para incluir metricas de campanha |

---

## 12. Riscos e Auto-Crítica

| Risco | Impact | Mitigação |
|---|---|---|
| TelegramAdapter REAL requer chat_id + token validos | Digest nao funciona em REAL sem config | MOCK por padrao; demo comprova o fluxo |
| HunterReport pode nao existir (primeira execucao) | Mensagem vazia ou erro | Fallback "Nenhum produto em alta" |
| Mensagem > 4096 chars | Telegram rejeita | Truncar produtos ate caber |
| Usuario pode nao querer notificacao diaria | Incomodo | Configuravel via DailyDigestConfig (pode desligar) |
| Fuso horario: 09:00 BRT vs UTC | Horario errado | Campo timezone no config |

### O que so Shin/Codex decide:
- O chat_id real do Shin para receber a digest
- Se quer REAL automation (cron/GitHub Action) ou manual por enquanto
- Se o link do dashboard deve abrir direto no approve ou na pagina inicial
- Se quer incluir campanhas ativas + gasto no futuro (Flow Track expansion)

---

## 13. Dependencias

```
Nenhuma. Reusa TelegramAdapter (ja existe).
```
