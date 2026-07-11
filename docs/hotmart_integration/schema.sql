CREATE TABLE IF NOT EXISTS hotmart_webhook_events (
    event_id text PRIMARY KEY,
    event_name text NOT NULL,
    version text NOT NULL,
    creation_date bigint NOT NULL,
    received_at timestamptz NOT NULL,
    payload_sha256 char(64) NOT NULL,
    product_id text NOT NULL DEFAULT '',
    product_ucode text NOT NULL DEFAULT '',
    product_name text NOT NULL DEFAULT '',
    purchase_status text NOT NULL DEFAULT '',
    purchase_value numeric(18, 2) NOT NULL DEFAULT 0,
    purchase_currency varchar(3) NOT NULL DEFAULT '',
    payment_type text NOT NULL DEFAULT '',
    offer_code text NOT NULL DEFAULT '',
    transaction_sha256 varchar(64) NOT NULL DEFAULT '',
    commissions jsonb NOT NULL DEFAULT '[]'::jsonb,
    state text NOT NULL CHECK (
        state IN ('pending', 'processed', 'failed', 'dead_letter', 'ignored')
    ),
    attempts integer NOT NULL DEFAULT 0 CHECK (attempts >= 0),
    last_error text NOT NULL DEFAULT '',
    processed_at timestamptz,
    updated_at timestamptz NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS hotmart_webhook_events_state_received_idx
    ON hotmart_webhook_events (state, received_at);

CREATE INDEX IF NOT EXISTS hotmart_webhook_events_transaction_idx
    ON hotmart_webhook_events (transaction_sha256)
    WHERE transaction_sha256 <> repeat('0', 64) AND transaction_sha256 <> '';
