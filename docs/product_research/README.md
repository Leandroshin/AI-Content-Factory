# Product Research Operating Model

This folder documents how product discovery should feed the AI Content Factory.

## Principle

Do not start by scraping everything. Start with a controlled research funnel:

1. Collect candidate products from manual research, videos, marketplaces,
   Telegram/WhatsApp references, browser extensions, or official APIs.
2. Convert each candidate into the internal `ProductCandidate` shape.
3. Let `ProductResearchEmployee` score and shortlist.
4. Send shortlisted products to `AffiliateDealsEmployee`.
5. Keep publishing behind the HITL approval gateway.

## Raw Input Folders

Use local raw folders for noisy material:

```text
research_inputs/raw_transcripts/
research_inputs/manual_candidates/
```

Recommended filenames:

```text
research_inputs/raw_transcripts/2026-07-05_tiktok-shop-strategy_channel-title.txt
research_inputs/manual_candidates/2026-07-05_10-product-links.md
```

Raw transcripts are intentionally ignored by Git. Codex can read them locally,
extract strategy, and write clean summaries/specs into `docs/`.

## Product Candidate Fields

Minimum useful candidate:

```text
product_name:
marketplace:
source_url:
category:
niche:
current_price:
old_price:
commission_percent:
image_url:
affiliate_url:
notes:
```

Useful signals:

```text
demand_signals:
  - name: deal_group_repeats
    value: 8
    weight: 1.1
creative_signals:
  - name: demo_potential
    value: 9
    weight: 1.0
competition_level: low|medium|high
saturation_level: low|medium|high
risk_flags:
```

## Sources

Preferred source order:

1. Official APIs or platform dashboards.
2. Manual export/copy from legitimate account pages.
3. Browser extensions used only as operator assistance.
4. Public videos/transcripts as strategy input.

Current references to evaluate:

- Mercado Livre Developers: `https://developers.mercadolivre.com.br/pt_br/api-docs-pt-br`
- Hotmart Developers: `https://developers.hotmart.com/docs/pt-BR/`
- TikTok Shop Affiliate: `https://business.tiktokshop.com/us/affiliate`
- Amazon Product Advertising / Creators API transition:
  `https://webservices.amazon.com/paapi5/documentation/register-for-pa-api.html`

Kwai should stay manual/assisted until a stable official product/affiliate API is
confirmed.

## What Shin Should Do On The Internet

1. Create/confirm affiliate accounts for each platform before trying automation.
2. Save your affiliate/tracking IDs, but do not paste secrets into raw docs.
3. For each interesting video, save the transcript in `research_inputs/raw_transcripts/`.
4. For each product idea, save the URL plus why it looks interesting in
   `research_inputs/manual_candidates/`.
5. Add notes about tools mentioned by the creator, especially extensions,
   dashboards, spreadsheets, coupon sites, and product research tools.
6. Ask Codex to process the folder after a batch is ready.
