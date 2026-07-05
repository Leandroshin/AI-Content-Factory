# Claude Proposal - Infoproducts and Client Services

Date received: 2026-07-05
Source: pasted Claude response from Shin
Status: reviewed by Codex

## Context Correction

Claude noted that `TelegramAdapter` did not exist when it inspected the repo.
That was true for its snapshot, but the current repository already includes:

- `core/tools/adapters/telegram_adapter.py`
- `core/tools/providers/telegram.py`
- `demo_telegram_publishing_adapter.py`
- `core/approval/` with `TelegramApprovalGateway`

So the idea should be interpreted against the current state after the Telegram
and HITL commits.

## Top Ideas

1. Extend Affiliate Deals to digital infoproducts such as Hotmart/Kiwify.
2. UGC / Ad-Creative-as-a-Service for local businesses.
3. White-label content factory service via freelance marketplaces.
4. Localization and dubbing as a B2B service.
5. Content digest/newsletter for niche research.

## Codex Decision

Accepted next implementation: extend `AffiliateDealsEmployee` for manually
curated digital infoproduct offers, with conservative compliance rules.

Deferred:

- UGC/client services, because it is more product/packaging than core runtime.
- White-label/freelance channel, because it can reuse the later client services
  workflow.
- Localization/dubbing, because it should come after provider/cost controls are
  more visible.
- Newsletter/digest, because it belongs naturally with a future Research
  Department.

## Safety Rule

Do not automate marketplace scraping or policy-sensitive campaign launch. The
first version must accept manually supplied offers, require manual source
review metadata, block risky regulated-vertical copy, and keep human approval
required before publication.
