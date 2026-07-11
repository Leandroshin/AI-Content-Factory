# Hotmart Integration Plan

Updated on 2026-07-10.

## What the screen is asking for

The Hotmart Webhook screen expects a public HTTPS endpoint owned by this
project. It is a destination to which Hotmart sends transaction events. It is
not a Codex URL and it is not the full Hotmart API.

Do not activate a configuration until the endpoint is deployed, validates
authentication and responds successfully to Hotmart's test.

Planned shape:

https://api.<future-domain>/webhooks/hotmart/v2

The final URL does not exist yet.

## Two different connectors

### Hotmart API client

Purpose:

- read resources allowed by the account credentials;
- obtain product and sales data where the API scope permits;
- normalize data for Product Research and business analytics.

Authentication and scopes must use Hotmart Developers credentials. The
documented product-list endpoint is for a creator's products, so access to an
affiliate marketplace or third-party product catalog must be verified
separately and must not be assumed.

### Hotmart webhook receiver

Purpose:

- receive purchase and subscription state changes;
- update commission and conversion metrics;
- trigger controlled follow-up workflows.

Initial events:

- PURCHASE_APPROVED;
- PURCHASE_CANCELED;
- PURCHASE_REFUNDED;
- PURCHASE_CHARGEBACK;
- PURCHASE_DELAYED when a recovery workflow exists.

## Security contract

1. Accept POST only over HTTPS.
2. Validate X-HOTMART-HOTTOK before processing.
3. Read the expected hottok from a secret provider or host environment.
4. Use the Hotmart event ID as an idempotency key.
5. Store the event before launching downstream work.
6. Return a successful response quickly and process asynchronously.
7. Redact buyer and payment personal data from logs.
8. Keep a dead-letter queue for invalid or repeatedly failing events.
9. Record source, received time, event version and payload hash.
10. Never place hottok, client credentials or payloads with personal data in
    Git.

Hotmart can retry failed deliveries and may disable a configuration whose URL
keeps returning errors. Reliability is part of the security boundary.

## Role of n8n

n8n is optional, not the brain of the factory.

Good uses:

- rapidly prototype a connector;
- route a low-risk notification;
- bridge a service that has a maintained n8n node;
- run a visual schedule while the native connector does not exist.

Do not place in n8n:

- core scoring rules;
- canonical business state;
- approval policy;
- provider budgets;
- compliance decisions;
- secrets duplicated across many workflows.

Preferred boundary:

Hotmart -> native verified webhook -> event store/queue -> factory workflow

Optional boundary for a prototype:

Hotmart -> protected n8n webhook -> signed request to native factory endpoint

## What 24/7 autonomy means

Employees do not stay alive because a chat window is open. Production autonomy
needs:

- always-on HTTPS ingress;
- persistent database;
- durable event queue;
- scheduler for periodic research;
- workers with retries, timeouts and rate limits;
- official API credentials;
- budget guard and usage logs;
- HITL queue for publishing, spending and risky actions;
- health checks, alerts and dead-letter recovery.

The existing employees and pipelines are domain workers. Hosting, queue and
scheduling are the missing operational shell around them.

## Implementation order

1. Choose hosting and database for the affiliate dashboard.
2. Implement and test the receiver locally with fake payloads.
3. Deploy the endpoint with a placeholder-disabled state.
4. Store HOTTOK as a host secret.
5. Enable validation and idempotency.
6. Use Hotmart's test-send action.
7. Register only the minimum events.
8. Connect approved events to conversion and commission metrics.
9. Add alerts and a replay screen before calling the integration production
   ready.

## Official references

- https://help.hotmart.com/pt-BR/article/360001491352
- https://developers.hotmart.com/docs/pt-BR/2.0.0/webhook/purchase-webhook/
- https://developers.hotmart.com/docs/pt-BR/tutorials/use-webhook-for-subscriptions/
- https://developers.hotmart.com/docs/en/v1/product/product-list/
