# Current State - 2026-07-10

Operational status last verified on 2026-07-11.

This document is the current source of truth for the AI Content Factory. Older
roadmaps remain useful as architectural history, but their demo counts and
pending-work lists must not be read as the present state.

## Product objective

Build a daily operating system that can:

1. gather traceable market and strategy evidence;
2. shortlist products or content opportunities;
3. review assets and generate an affiliate package;
4. wait for the owner's approval;
5. publish through official APIs;
6. measure clicks, sales, commission, cost and ROI;
7. promote only measured lessons into organizational memory.

## Proven architecture

- Company, CEO, DepartmentManager, tasks, employees and observability.
- ProductionEmployee and ProductionPipeline as the department pattern.
- Script, Audio, Image and Video production departments.
- Strategy Intelligence, Product Research and Creative Review departments.
- Affiliate Deals department with scoring, copy, compliance and publishing
  plan.
- Capability-based tool discovery and MOCK/REAL execution.
- HTTP, secrets, providers, retries, rate limits and masked observability.
- Persistence, organizational memory, quality and session continuity.
- Budget and explicit owner-approval controls for paid providers.
- FFmpeg physical rendering and controlled ElevenLabs integration.
- Telegram adapter with a proven controlled real smoke test.

## Proven affiliate flow

The integrated flow is:

Strategy Intelligence -> Product Research -> Creative Review ->
Affiliate Deals -> HITL Approval -> Telegram

Concrete pieces:

- core/content_factory/affiliate_workflow.py coordinates the departments.
- core/company/approval.py provides the human approval gate.
- core/content_factory/affiliate_dashboard.py renders the operating view.
- core/content_factory/affiliate_dashboard_server.py persists the queue and
  exposes manual offer, approve, reject and publish endpoints.
- Publication stays in MOCK by default. REAL Telegram remains explicit,
  credentialed, approved and budget-limited.
- Manual intake is available so the owner can start with real affiliate links
  before marketplace APIs are ready.

## Official connector status

- **Hotmart webhook:** active for all products with only purchase approved,
  canceled, refunded and chargeback events. Hotmart's official history showed
  four `202 - Processado` deliveries. Neon persistence and PII exclusion were
  verified, then the official test rows were removed.
- **Shopee Affiliate:** the authenticated Open API portal currently redirects
  this account to the affiliate enrollment form. API work is blocked until the
  owner chooses PF/PJ, registers truthful brand social accounts and submits the
  program terms personally.
- **TikTok Shop:** the current business goal uses the Creator Affiliate route,
  which starts in the TikTok mobile app. Enrollment approval plus identity and
  tax verification are prerequisites. TikTok Partner/Affiliate API access is a
  separate approval track and must not be assumed.

## Verification baseline

- 95 demo files are present.
- Standardized run on 2026-07-11: 95/95 demos, 0 failures.
- 39 demos explicitly printed 1388 assertions; 56 passed without a numeric
  assertion summary.
- Core compilation was successful at that baseline.

Run python scripts/run_all_demos.py after code changes. Its local JSON report
records pass/fail, duration and only assertion totals actually printed by each
demo. The former 4390 figure used an undocumented counting method and is not a
current verification metric.

## Product maturity

| Layer | Estimate | Meaning |
|---|---:|---|
| Architectural foundation | 80% | Main contracts and control layers exist |
| Demonstrable production flows | 65% | Affiliate and content flows run with deterministic inputs |
| Daily tool for Shin | 35% | Local dashboard exists, but data entry and connectors are limited |
| Autonomous measured operation | 15% | Official data, publishing and revenue feedback are not complete |

These percentages are planning estimates, not test coverage.

## Real gaps

### Product and opportunity input

- Accept a marketplace/product URL and extract a normalized candidate.
- Preserve source, timestamp, price evidence, seller and image provenance.
- Prefer official APIs or owner-provided exports.
- Treat browser research as controlled evidence collection, never aggressive
  scraping.

### Affiliate platforms

- Store program/account readiness without storing login passwords.
- Support affiliate-link generation or validation per official platform.
- Capture commission rules and attribution windows.
- Keep manual fallback for platforms without an accessible API.
- Hotmart remains split into an API client and a verified webhook receiver.
  The receiver, Neon schema, Vercel URL and sensitive host variables are live.
  Health, hosted idempotency and Hotmart's official test all passed. See
  docs/hotmart_integration/PLAN.md.

### Media providers

- Replace or renew the expired ElevenLabs credential before another real
  smoke test.
- Select one real image provider based on cost, quality and licensing.
- Add video generation only after image, voice and local editing are measured.

### Publication and analytics

- Meta starts read-only: account/page/Instagram inventory and performance
  reports.
- Posting and ads must use official APIs and human approval.
- No browser script may imitate a person or warm an account automatically.
- No campaign creation, payment setup or spend without explicit owner action.
- Add click, sale, commission, cost and ROI events.

### Product delivery

- Host the dashboard with a persistent database and authentication.
- Build a compliant pre-sell/landing page.
- Add privacy policy, terms and affiliate disclosure.
- Create a short visual operating guide when a real daily workflow is ready.

## Meta status supplied by the owner

- Brand: Achados Baratos BR.
- Instagram: achadosbaratosbr2.
- Ad account: 2069488655023.
- Meta app: Agente Achados Baratos, ID 1027456609762193.
- The owner reports that the business restriction was removed after captcha,
  phone and identity verification.

Before integration, verify asset connections and create or confirm a Meta
System User with the minimum permissions. Never commit an access token. A
person-like account named for an agent is not a substitute for a System User.

## Knowledge from transcripts

Raw transcripts do not become employee instructions. The approved lifecycle is:

Raw source -> Evidence -> Knowledge Card -> Controlled Experiment ->
Measured Result -> Approved or Archived Knowledge

Each card needs provenance, date, confidence, applicable department, risks and
review date. Revenue promises and platform policies require independent
verification.

## Official next order

1. Finish master documentation, transcript inventory and Graphify refresh.
2. Add real product-URL intake with evidence and manual fallback.
3. Configure Meta read-only through official assets and token storage.
4. Complete Shopee and TikTok Shop owner onboarding, then prove only the API
   scopes actually granted to each account.
5. Host dashboard and compliant landing page.
6. Add conversion and ROI feedback.
7. Select the first real image provider.
8. Implement the 2.5D office as an operational visualization after the real
   dashboard is useful.

## Non-goals for the next phase

- Building generators from scratch when a maintained tool/provider fits.
- Autonomous ad spend.
- Automatic WhatsApp spam or simulated human activity.
- Loading the entire transcript archive into every employee prompt.
- Expanding departments without a real workflow or measurable outcome.
