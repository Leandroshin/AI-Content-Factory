# Meta Ads Analytics - Read-Only Operation

## Purpose

Give the factory controlled visibility into Meta ad accounts, campaigns and
performance without allowing campaign creation, edits, budget changes,
publication or deletion.

## Implemented reads

- `get_permissions`
- `list_ad_accounts`
- `get_ad_account`
- `list_campaigns`
- `get_insights`

Every operation uses `GET` and a fixed field allowlist. Unknown actions and
write-like commands are blocked before HTTP.

## Required permission

- `ads_read`: required for ad account and performance reporting.
- `business_management`: optional, only when business asset inventory needs it.
- `ads_management`: intentionally not requested by this integration.

Use the Graph API version shown in the Meta app dashboard. The version is a
required configuration value so the project does not silently depend on a
moving `latest` alias.

## Local secret file

Create this ignored file only on the local machine:

```text
secrets/meta_ads.env
```

Contents:

```dotenv
META_ACCESS_TOKEN=your_read_only_token
META_GRAPH_API_VERSION=vXX.X
META_AD_ACCOUNT_ID=2069488655023
```

Do not commit or paste the token into documentation. The `secrets/` directory
is ignored by Git.

## REAL smoke

The default demo is dry and performs no API call:

```powershell
python demo_meta_ads_real_smoke.py
```

After the local secret file is ready:

```powershell
$env:AI_COMPANY_RUN_REAL_META_ADS='1'
python demo_meta_ads_real_smoke.py
```

The smoke performs at most three reads:

1. permissions;
2. selected ad account inventory;
3. campaign inventory.

The redacted result is written to:

```text
output/meta_ads_real_smoke/report.json
```

## Safety controls

- Bearer token travels in the authorization header, not the URL.
- Raw paging URLs are removed because Meta may include credentials in them.
- Only cursors and `has_next` are retained.
- Request pages are capped at 100 records.
- Insights accept fixed levels and bounded date ranges up to 366 days.
- Monetary fields remain in the native API representation.
- Provider Control Center requires token, request cap and owner approval.
- The adapter contains no POST, PATCH, PUT or DELETE operation.
- No payment method, ad spend or campaign mutation is reachable.

## Current status

The provider, adapter, control panel profile, MOCK proof and opt-in REAL smoke
are implemented. The first real inventory remains pending because the previous
token is no longer available in the clipboard or local secret storage.
