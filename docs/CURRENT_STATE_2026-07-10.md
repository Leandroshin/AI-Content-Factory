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
- HyperFrames editorial composition with beat-map, caption, provenance and
  long-form-to-Shorts quality gates.
- Strategy Intelligence, Product Research and Creative Review departments.
- Affiliate Deals department with scoring, copy, compliance and publishing
  plan.
- Capability-based tool discovery and MOCK/REAL execution.
- HTTP, secrets, providers, retries, rate limits and masked observability.
- Persistence, organizational memory, quality and session continuity.
- Budget and explicit owner-approval controls for paid providers.
- HyperFrames deterministic composition, FFmpeg encoding/fallback and
  controlled ElevenLabs integration.
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

- 100 demo files are present.
- Standardized run on 2026-07-12: 100/100 demos, 0 failures.
- 44 demos explicitly printed 1540 assertions; 56 passed without a numeric
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

- Product URL Intake now accepts owner-provided HTTPS URLs from allowlisted
  marketplaces and extracts JSON-LD/Open Graph into `ProductCandidate`.
- Source, timestamp, content hash, price evidence, seller, image and warnings
  are preserved; blocked pages retain an explicit manual fallback.
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

- A new restricted ElevenLabs key is stored locally outside Git and voice
  lookup succeeds. TTS is currently blocked by a failed/incomplete invoice;
  settle billing before treating it as an optional premium voice.
- Kokoro is the working zero-cost local TTS baseline. Its adapter keeps the
  model and optional dependencies in an isolated subprocess and generated the
  six Brazilian Portuguese narration assets used by the second cut.
- Select one real image provider based on cost, quality and licensing.
- HyperFrames is the proven deterministic editorial/motion layer; its REAL
  adapter passed lint, strict visual check and physical MP4 rendering.
- FFmpeg remains the local encoder and fallback.
- AI video generation is a separate optional provider and is added only after
  image, voice and local editing are measured.

### Fase Nova Games editorial proof

- Meccha Chameleon 2.6.0 official Steam evidence was converted into a physical
  40.90-second 1080x1920 HyperFrames second cut.
- Eight official gameplay excerpts, six editorial scenes, five transitions,
  camera motion, source labels, captions and CTA passed lint, strict checks,
  43/43 contrast checks and contact-sheet review.
- Kokoro `pm_alex` is the current local pt-BR narrator. Publication remains
  blocked only until owner review; ElevenLabs is no longer a prerequisite.

### Publication and analytics

- Meta Ads read-only provider and adapter are implemented for permissions,
  account inventory, campaigns and insights. Token redaction, fixed fields,
  bounded dates/pages and pre-HTTP write blocking are verified.
- The first REAL Meta inventory is pending only because no `ads_read` token is
  currently stored; the three-request opt-in smoke is ready.
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
