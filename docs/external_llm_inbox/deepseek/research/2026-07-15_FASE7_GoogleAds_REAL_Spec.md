# FASE 7 — Google Ads REAL (OPT-IN)

## ⚠️ WARNING — THIS PHASE REQUIRES REAL MONEY

Google Ads REAL campaigns cost money. Every click, every impression, every day you have a budget running. This is NOT a simulation. You can lose the entire budget in hours if misconfigured.

**If you are reading this spec and have NOT validated the full pipeline in MOCK for 2+ weeks, close this file and go back to Fase 3.**

Fase 7 is the FINAL phase for a reason. Fases 1-5 cost zero dollars. Fase 6 uses free APIs (ClickBank/Digistore24). Fase 7 connects your credit card to Google and spends real money on real clicks.

---

## Prerequisites Checklist (do not proceed without all items)

- [ ] Tested with MOCK campaigns for 2+ weeks (Fase 3 export workflow)
- [ ] Google Ads account created with payment method configured
- [ ] Google Ads API access granted (developer token approved by Google)
- [ ] Real domain owned (not `file:///` or free subdomain)
- [ ] Landing page hosting active (VPS or static hosting with custom domain)
- [ ] At least $200 budget allocated for initial testing
- [ ] CPA formula defined: target CPA ≤ 50% of commission per sale
- [ ] Daily analysis routine established (30 min/day minimum)
- [ ] FTC disclosure present on all landing pages
- [ ] Owner ready to monitor and kill campaigns daily

---

## Activation Rule

Fase 7 is ONLY activated when **Shin explicitly sets ALL of the following**:

```
execution_mode = REAL
owner_approved = True
budget_allocated > 0  (minimum $200)
daily_budget <= max_daily ($20 default)
landing_page_domain = "real-domain.com"  (not "localhost" or "file://")
```

Until all conditions are true, the adapter MUST refuse ALL REAL operations and fall back to MOCK (same as Fase 3 output).

---

## 1. Objective

Create `GoogleAdsRealAdapter` that:

1. Creates REAL campaigns via Google Ads API
2. Monitors campaign performance daily (automated)
3. Auto-pauses campaigns that spend > 70% of commission without a conversion
4. Reports performance metrics back to the dashboard (Telegram + Provider Panel)
5. ALL write operations require explicit budget approval before any HTTP call

### What stays MOCK

- Campaign structure generation (keywords, ads, extensions)
- Landing page HTML/CSS templates
- Budget calculations and estimates
- Performance projections

### What becomes REAL (only after approval)

- Campaign creation on Google Ads servers
- Budget spending
- Click/conversion tracking
- Campaign pausing/updating

---

## 2. Architecture Decision — Why This Is the LAST Phase

| Phase | Cost | API Keys Required | Risk |
|-------|------|-------------------|------|
| 1-5   | $0   | No                | None |
| 6     | $0   | Yes (free)        | Low  |
| 7     | $$$  | Yes (Google)      | **High** |

**Decision: Fase 7 is optional and isolated from all previous phases.**

- Fase 3 works 100% independently (export campaign files, manual upload)
- Fase 7 only adds REAL execution on top of the same data structures
- If Shin never activates Fase 7, the project is still complete and functional
- The ONLY reason to build Fase 7 is automation: having the Codex monitor and adjust campaigns without manual Google Ads UI

---

## 3. Required Infrastructure Before REAL

### Google Ads Account
- Standard Google Ads account (not MCC initially)
- Billing configured (credit card on file)
- At least one campaign created manually to "warm up" the account
- Conversion tracking set up (Google Ads tag on landing page)

### Google Ads API Access
- Google Cloud Project created
- OAuth 2.0 consent screen configured (External, testing scope)
- OAuth 2.0 credentials downloaded (client_id, client_secret)
- Developer token: apply via Google Ads API center (can take 2-4 weeks for approval)
- For testing: use test account (`--google-ads-test`) — no cost, but limited functionality

### Domain & Hosting
- Real domain with HTTPS (e.g., `suplementosbrasil.com.br`)
- Cannot use `file:///` or `localhost` — Google requires real URLs for ads
- Options (from Video C 00:06:50):
  - Hostinger VPS: ~R$40/month
  - Cloudflare Pages: free tier with custom domain
  - GitHub Pages: free with custom domain
- SCP/SSH access for uploading landing pages

### Budget
- Minimum $200 for initial testing (as referenced in Video B 00:22:50, R$3k invested example)
- If $200 is not available, DO NOT activate REAL mode
- Recommended: start with $20/day budget, run for 10 days minimum

---

## 4. Google Ads API Setup

### OAuth 2.0 Flow

```
1. Create Google Cloud Project
2. Enable Google Ads API
3. Configure OAuth consent screen (External, add test users)
4. Create OAuth 2.0 credentials (Desktop application type)
5. Download client_id and client_secret
6. Run OAuth flow to get refresh_token (manual step, one-time)
7. Store refresh_token in SecretProvider (never in code)
```

### Developer Token

- Apply at `https://ads.google.com/apis/credentials`
- Standard access: requires Google review and account history
- Test account: basic access for development (no real spend)
- API limit: 10,000 operations per day per developer token

### Account Structure

```
MCC (Manager Account) — optional, for multiple accounts
  └── Client Account (standard Google Ads account)
        ├── Campaign 1 (e.g., "ProstaVive BR Search")
        │     ├── Ad Group 1 ("prostatite remedio")
        │     │     ├── Keyword (phrase): "remedio para prostatite"
        │     │     ├── Responsive Search Ad (headline 1, headline 2, description)
        │     │     └── Sitelink Extension
        │     ├── Ad Group 2 ("saude masculina")
        │     └── ...
        ├── Campaign 2
        └── ...
```

---

## 5. Provider — `core/tools/providers/google_ads.py`

### `GoogleAdsProvider`

```python
@dataclass(frozen=True, slots=True)
class GoogleAdsConfig:
    client_id: str          # from OAuth credentials
    client_secret: str      # from OAuth credentials
    developer_token: str    # from Google Ads API center
    refresh_token: str      # from OAuth flow
    login_customer_id: str  # MCC ID (optional)
    account_id: str         # target account ID (without dashes)
    test_account: bool = True  # default: use test account

class GoogleAdsProvider:
    """
    Wraps the Google Ads API client.
    READ-ONLY methods are always available.
    WRITE methods require explicit approval + budget.
    """

    # --- READ-ONLY (safe, no cost) ---

    def list_campaigns(self) -> list[dict]: ...
    def get_campaign_performance(self, campaign_id: str, date_range: str) -> CampaignMetrics: ...
    def get_keyword_performance(self, campaign_id: str) -> list[KeywordMetrics]: ...
    def get_account_summary(self) -> AccountSummary: ...
    def list_available_budgets(self) -> list[BudgetInfo]: ...

    # --- WRITE (requires approval, costs money) ---

    def create_campaign(
        self,
        campaign_structure: CampaignStructure,
        budget: BudgetConfig,
        *,
        owner_approval_token: str,
    ) -> CampaignResult: ...

    def update_campaign(
        self,
        campaign_id: str,
        updates: CampaignUpdates,
        *,
        owner_approval_token: str,
    ) -> CampaignResult: ...

    def pause_campaign(
        self,
        campaign_id: str,
        *,
        owner_approval_token: str,
    ) -> CampaignResult: ...

    def resume_campaign(
        self,
        campaign_id: str,
        *,
        owner_approval_token: str,
    ) -> CampaignResult: ...
```

### CampaignMetrics (frozen+slots)

```python
@dataclass(frozen=True, slots=True)
class CampaignMetrics:
    campaign_id: str
    campaign_name: str
    status: str
    impressions: int
    clicks: int
    cost_micros: int          # cost in micros (divide by 1,000,000 for real currency)
    conversions: int
    conversion_value_micros: int
    ctr: float                # click-through rate
    avg_cpc_micros: int
    cost_per_conversion_micros: int
    conversion_rate: float
    date_range: str
    cached_at: float          # timestamp
```

### BudgetGuard Integration

The provider uses the existing `ProviderBudgetGuard` from `core/tools/provider_control.py`:

```python
provider = GoogleAdsProvider(config, budget_guard=budget_guard)
budget_guard.set_max_daily_spend(20_000_000)   # $20 in micros
budget_guard.set_max_campaign_spend(200_000_000)  # $200 in micros
budget_guard.set_require_owner_approval(True)
budget_guard.set_owner_approval_token(None)  # must be set by Shin
```

---

## 6. Adapter — `core/tools/adapters/google_ads_real_adapter.py`

### Design

Extends the MOCK `GoogleAdsCampaignAdapter` from Fase 3. Does NOT replace it.

```
GoogleAdsCampaignAdapter (Fase 3, MOCK only)
  └── GoogleAdsRealAdapter (Fase 7, extends with REAL mode)
```

### RealAdapter.execute() Flow

```
adapter.execute(context) → AdapterExecutionResult

MOCK mode (default):
  1. validate context
  2. generate campaign structure (keywords, ads, budgets)
  3. write export files (CSV, Google Ads Editor format)
  4. return success + file paths

REAL mode (opt-in only):
  1. validate context
  2. CHECK: execution_mode == REAL? → fail if MOCK
  3. CHECK: owner_approved == True? → fail "Owner approval required"
  4. CHECK: budget_allocated > 0? → fail "No budget allocated"
  5. CHECK: daily_budget <= max_daily? → fail "Daily budget exceeds max"
  6. CHECK: landing_page domain is real? → fail "file:/// not allowed in REAL"
  7. Validate campaign structure
  8. Create campaign via GoogleAdsProvider.create_campaign()
  9. Return campaign_id + google_ads_url
```

### Dry Run Mode

```python
# To test without spending:
adapter.execute(context, dry_run=True)
# Returns: AdapterExecutionResult(
#     success=True,
#     data={"campaign_id": "MOCK_CAMPAIGN_001", "dry_run": True},
#     output_dir="output/campaigns/dry_run/",
# )
# Dry run passes all checks but never calls Google Ads API.
```

---

## 7. Campaign Monitor — `core/content_factory/gringa_campaign_monitor.py`

### `CampaignMonitor` Class

```python
class CampaignMonitor:
    """
    Daily monitor for active Google Ads campaigns.
    Uses GoogleAdsProvider (READ-ONLY) to check performance.
    Can auto-pause campaigns based on rules.
    """

    def __init__(self, provider: GoogleAdsProvider, budget_guard: ProviderBudgetGuard): ...

    def check_campaign(self, campaign_id: str, commission_per_sale: float) -> CampaignHealth: ...

    def monitor_all_active(self, commissions: dict[str, float]) -> list[CampaignAlert]: ...

    def pause_campaign(self, campaign_id: str) -> CampaignAction: ...

    def daily_report(self) -> str: ...  # returns formatted Telegram message
```

### CampaignHealth (frozen+slots)

```python
@dataclass(frozen=True, slots=True)
class CampaignHealth:
    campaign_id: str
    campaign_name: str
    status: str
    spend_today: float
    spend_total: float
    conversions: int
    conversion_value: float
    cpa: float
    target_cpa: float
    commission_per_sale: float
    spend_vs_commission_pct: float
    days_since_last_conversion: int
    risk_level: str  # "green" | "yellow" | "red"
    recommendation: str  # "keep" | "alert" | "pause"
```

### Auto-Pause Rules (from Video B)

| Rule | Trigger | Action | Source |
|------|---------|--------|--------|
| 1 | Spent > 70% of commission with 0 conversions | Pause campaign | Video B 00:29:30 |
| 2 | CPA > 80% of commission for 3 consecutive days | Alert owner + recommend pause | Video B 00:17:24 |
| 3 | 0 conversions in 7 days | Pause + notify | Video B 00:25:00 |
| 4 | CTR < 0.5% after 1000 impressions | Alert (review keywords) | Video B 00:20:31 |
| 5 | Daily budget exhausted before 12:00 | Alert (reduce bids or budget) | Standard practice |
| 6 | Account-level overage > 110% of max_daily | Pause ALL campaigns | Safety |

**Important: Rule 1 must NOT pause a keyword that is selling (ref Video B 00:29:30 error).**
- Rule 1 pauses the CAMPAIGN, not individual keywords
- If ANY conversion exists within the campaign, do NOT apply pause rules
- Only apply pause to campaigns with ZERO conversions

### Performance Alerts (Telegram output)

The monitor produces formatted messages for the Telegram integration (Fase 5):

```
📊 *Daily Campaign Report - 2026-07-15*

🟢 ProstaVive: $12.40 gasto, 1 venda ($49.90), CPA $12.40 ✅
🟡 TestosteroneMax: $18.50 gasto, 0 vendas, CPA $18.50 — 3 dias sem venda
🔴 SleepWell: PAUSADA — gastou $55 sem vender (78% da comissao)

Resumo: 3 campanhas, 1 venda, $49.90 receita, $30.90 gasto

⚠️ ATENCAO: TestosteroneMax precisa de revisao se nao vender ate sabado
```

---

## 8. Budget Gates (using existing ProviderBudgetGuard from Fase 5)

The existing `ProviderBudgetGuard` from `core/tools/provider_control.py` is extended with Google Ads-specific limits:

```python
guard = ProviderBudgetGuard()

# Global limits
guard.set_max_daily_spend(20.00)       # $20/day total across all campaigns
guard.set_max_total_spend(200.00)      # $200 total before requiring top-up

# Per-campaign limits
guard.set_max_daily_per_campaign(10.00)   # $10/day per campaign
guard.set_max_campaign_total(50.00)       # $50 total per campaign

# Approval gates
guard.set_require_owner_approval(True)
guard.set_owner_approval_token(None)      # Filled by Shin in dashboard

# Safety
guard.set_stop_on_overage(True)           # Pause campaign if over budget
guard.set_stop_all_on_account_overage(True)  # Pause ALL if account over 110%

# Required for REAL execution
guard.set_require_real_domain(True)
guard.set_require_https(True)
guard.set_require_ftc_disclosure(True)
```

### Budget Verification Flow (pre-API call)

```python
def _verify_can_spend(campaign_id: str, budget: float, context: dict) -> bool:
    checks = [
        ("execution_mode", context.get("execution_mode") == "REAL"),
        ("owner_approved", context.get("owner_approval_token") is not None),
        ("budget > 0", budget > 0),
        ("daily_limit", budget <= guard.max_daily_per_campaign()),
        ("total_limit", guard.total_spent + budget <= guard.max_total_spend()),
        ("real_domain", context.get("domain", "").startswith("https://")),
        ("disclosure", context.get("has_disclosure", False)),
    ]
    for name, passed in checks:
        if not passed:
            return False
    return True
```

---

## 9. Landing Page Hosting

### Current State (Fase 2)
`LandingPageBuilderAdapter` generates HTML files to `output/landing_pages/`. These are `file:///` URLs — not usable for REAL Google Ads.

### REAL Mode Requirements
- Landing pages must be hosted on a real domain with HTTPS
- Google Ads requires final URL to be a reachable HTTPS page
- Cannot use file:/// URLs, localhost, or IP addresses

### Hosting Options (from Video C 00:06:50)

| Option | Cost | Effort | Recommended For |
|--------|------|--------|-----------------|
| Hostinger VPS | ~R$40/mo | Medium | Multiple campaigns, full control |
| Cloudflare Pages | Free tier | Low | Static landing pages (no backend) |
| GitHub Pages + custom domain | Free | Low | Simple affiliate pages |

### LandingPageBuilderAdapter REAL Mode

```python
def execute(self, context, *, execution_mode="MOCK"):
    steps = super().execute(context)  # Generate HTML (same as MOCK)

    if execution_mode == "REAL" and context.get("host_config"):
        host_config = context["host_config"]
        # SCP/SSH upload to VPS
        # or Cloudflare Pages API deploy
        # or GitHub Pages push
        return self.upload_to_host(host_config, steps.output_dir)

    return steps  # MOCK: same as Fase 2
```

---

## 10. Demo Outline — `demo_gringa_campaign_monitor.py`

This demo MUST be DRY RUN ONLY — no API calls, no real money.

```python
def test_gringa_campaign_monitor():
    # Setup
    adapter = GoogleAdsRealAdapter()
    provider = MockGoogleAdsProvider()  # deterministic data
    monitor = CampaignMonitor(provider, budget_guard)
    budget_guard.set_max_daily_spend(20.00)

    # Test 1: REAL mode requires approval
    result = adapter.execute(
        {"campaign": campaign_structure},
        execution_mode="REAL"
    )
    assert result.success == False  # denied: no approval
    assert "owner approval" in result.error.lower()

    # Test 2: Budget guard blocks without budget
    budget_guard.set_max_total_spend(0)
    result = adapter.execute(
        {"campaign": campaign_structure, "owner_approval_token": "x"},
        execution_mode="REAL"
    )
    assert result.success == False
    assert "budget" in result.error.lower()

    # Test 3: Dry run with valid config returns MOCK data
    budget_guard.set_max_total_spend(200.00)
    result = adapter.execute(
        {"campaign": campaign_structure, "owner_approval_token": "abc"},
        execution_mode="REAL",
        dry_run=True,
    )
    assert result.success == True
    assert result.data["dry_run"] == True

    # Test 4: Auto-pause logic via monitor
    health = monitor.check_campaign("camp_001", commission_per_sale=50.00)
    # Mock provider returns: $140 spent, 0 conversions, $50 commission
    assert health.risk_level == "red"
    assert health.recommendation == "pause"

    # Test 5: Campaign with conversion is NOT paused
    health = monitor.check_campaign("camp_002", commission_per_sale=50.00)
    # Mock provider returns: $320 spent, 2 conversions, $360 value
    assert health.risk_level == "green"
    assert health.recommendation == "keep"

    print("✅ All 5 dry-run assertions passed — no API calls made")
```

---

## 11. Safety Checklist (code-enforced)

Every REAL operation MUST pass all checks before executing:

```
[ ] 1. execution_mode == "REAL"
[ ] 2. owner_approved == True (token validated)
[ ] 3. budget_allocated > 0 ($200 minimum)
[ ] 4. daily_budget <= max_daily ($20 default)
[ ] 5. total_budget <= max_total ($200 default)
[ ] 6. landing_page hosted on real domain (HTTPS required)
[ ] 7. FTC disclosure present in landing page
[ ] 8. target_cpa <= 50% of commission
[ ] 9. developer_token is not "TEST_TOKEN" (REAL token only)
[ ] 10. test_account == False (no real spend on test accounts)
```

If ANY check fails → operation is BLOCKED with specific error message.

---

## 12. O que o Codex precisa fazer

| File | What | Priority |
|------|------|----------|
| `core/tools/providers/google_ads.py` | GoogleAdsProvider (MOCK only for now, with contracts for REAL) | HIGH |
| `core/tools/adapters/google_ads_real_adapter.py` | Extends Fase 3 GoogleAdsCampaignAdapter with REAL mode + safety gates | HIGH |
| `core/content_factory/gringa_campaign_monitor.py` | CampaignMonitor with auto-pause rules, CampaignHealth, daily report | HIGH |
| `core/tools/provider_control.py` | Extend ProviderBudgetGuard with Google Ads-specific limits (max_daily_per_campaign, require_real_domain, require_ftc_disclosure, stop_all_on_account_overage) | MEDIUM |
| `core/tools/providers/google_ads.py` | MockGoogleAdsProvider (deterministic data for demos) | HIGH |
| `demo_gringa_campaign_monitor.py` | 5 dry-run assertions, NO real API calls | HIGH |
| `docs/external_llm_inbox/deepseek/research/2026-07-15_FASE7_GoogleAds_REAL_Spec.md` | This spec | DONE |

### What Codex does NOT do

- Does NOT modify existing Fase 3 adapter (extends, does not replace)
- Does NOT create real Google Ads account, generate OAuth tokens, or apply for developer token
- Does NOT spend any money
- Does NOT modify existing demos
- Does NOT create landing page hosting infrastructure

---

## 13. Video References

| Video | Timestamp | Lesson | Application in Fase 7 |
|-------|-----------|--------|----------------------|
| B | 00:17:24 | CPA = 50% da comissao | `target_cpa = commission * 0.5` — golden rule enforced in budget gates |
| B | 00:18:00 | Desligar display, so pesquisa | Campaign structure must use `SEARCH` network, not `DISPLAY` or `PERFORMANCE_MAX` |
| B | 00:19:30 | Nao usar Performance Max | `advertising_channel_type` must be `SEARCH` — REJECT any PMax config |
| B | 00:20:31 | Keyword em frase, nunca ampla | `keyword_match_type` must be `PHRASE` — reject `BROAD` in validation |
| B | 00:22:50 | $3k investido, $5.3k retorno | Reference case: target 76% ROI. Used as benchmark for monitor alerts. |
| B | 00:25:00-00:30:00 | Rotina de analise diaria | Daily report generation + Telegram alerts replace manual UI checking |
| B | 00:29:30 | Erro: pausou keyword que vendia | Rule 1 pauses campaign, not keyword. Check conversion before action. |
| A | 00:15:30 | Decisao baseada em dados | Monitor recommendations are advisory — final pause decision is owner's |
| C | 00:06:50 | VPS Hostinger R$40/mes | Landing page hosting (SCP/SSH upload) |

---

## 14. Risk Register

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| Campaign spends budget with 0 sales | High | High | Auto-pause at 70% of commission |
| Developer token rejected by Google | Medium | High | Apply early, use test account meanwhile |
| Landing page domain not ready | Medium | High | Hostinger VPS quickest path |
| FTC violation on landing page | Low | Very High | Disclosure required by safety check |
| Mistakenly pausing a winning campaign | Low | Medium | Pause campaign, not keyword; check for conversions |
| Budget exceeded due to delayed API | Low | Medium | `stop_on_overage` + `stop_all_on_account_overage` |
| Click fraud (competitor draining budget) | Low | High | Monitor CTR and conversion rate spikes |

---

## 15. Final Recommendation

**Do NOT implement Fase 7 yet.**

Complete priority order:
1. Validate that Fase 3 affiliate campaigns work when manually uploaded to Google Ads
2. Run MOCK campaigns through the full pipeline for 2+ weeks
3. Get a real domain and landing page hosting active
4. Apply for Google Ads developer token
5. Set up Google Ads account with payment method
6. Have at least $200 budget available
7. **Then** implement Fase 7

The MVP is Fase 3 (exportable files). Fase 7 is automation of what Shin can already do manually. Only automate after proving the manual process works and produces profit.

---

*Refer to `docs/external_llm_inbox/deepseek/ideas/2026-07-13_MASTER_PROJECT_TREES.md` for dependency tree positioning.*
