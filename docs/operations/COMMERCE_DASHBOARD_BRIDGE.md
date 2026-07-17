# Commerce Dashboard Bridge

## Purpose

`CommerceDashboardBridge` connects controlled product collection and the affiliate commerce workflow to the private operational dashboard.

It is a one-way review bridge. A dashboard decision does not approve the internal HITL request and does not publish to Telegram, Meta, Shopee, TikTok, or any other channel.

## Product gate

A product enters the visual queue only when all conditions are true:

- the URL intake status is `ready`;
- name, verified price, image, and public HTTPS source are present;
- an affiliate target is already present;
- synchronization was explicitly enabled and the dashboard token was supplied.

Products requiring manual completion, blocked URLs, missing images, and missing affiliate links remain outside the dashboard intake and are counted as blocked in the bridge result.

## Workflow gate

An affiliate campaign preview enters the queue only when:

- the workflow succeeded;
- the publication package is `pending_approval` or `ready`;
- its ApprovalRuntime request is still `pending`;
- no publication has succeeded;
- the selected product retains a public HTTPS source.

The dashboard card explicitly says that publication requires the separate factory HITL approval.

## Endpoint

The hosted dashboard accepts bounded requests at:

`POST /api/intake/commerce`

Authentication uses `Authorization: Bearer ...`. The token is never accepted in the URL, included in results, or committed to Git. The bridge is disabled by default.

## Verification

Run:

```powershell
python demo_commerce_dashboard_bridge.py
```

The demo proves product eligibility, affiliate-link blocking, pending-HITL delivery, prevention of requeue after approval, and zero publication calls.
