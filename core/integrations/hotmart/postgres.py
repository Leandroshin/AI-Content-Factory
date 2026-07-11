"""Neon/Postgres persistence for verified Hotmart webhook events."""

from __future__ import annotations

import json
from datetime import datetime
from decimal import Decimal
from typing import Any

from core.integrations.hotmart.webhook import (
    HotmartWebhookEvent,
    HotmartWebhookState,
)

try:
    import psycopg
    from psycopg.rows import dict_row
    from psycopg.types.json import Jsonb
except ImportError:  # pragma: no cover - exercised only without deployment dependency
    psycopg = None
    dict_row = None
    Jsonb = None


class HotmartPostgresStore:
    """Durable hosted store using an injected PostgreSQL connection string."""

    def __init__(self, connection_string: str, *, max_attempts: int = 5) -> None:
        if not connection_string.strip():
            raise ValueError("A PostgreSQL connection string is required")
        if max_attempts < 1:
            raise ValueError("max_attempts must be at least 1")
        if psycopg is None:
            raise RuntimeError("Install psycopg[binary] to use HotmartPostgresStore")
        self._connection_string = connection_string.strip()
        self.max_attempts = max_attempts

    def register(
        self,
        event: HotmartWebhookEvent,
        *,
        initial_state: HotmartWebhookState = HotmartWebhookState.PENDING,
    ) -> tuple[dict[str, Any], bool]:
        """Insert once using the Hotmart event id as the primary key."""
        record = event.as_record(initial_state)
        with self._connect() as connection:
            inserted = connection.execute(
                """
                INSERT INTO hotmart_webhook_events (
                    event_id, event_name, version, creation_date, received_at,
                    payload_sha256, product_id, product_ucode, product_name,
                    purchase_status, purchase_value, purchase_currency,
                    payment_type, offer_code, transaction_sha256, commissions,
                    state, attempts, last_error
                ) VALUES (
                    %(event_id)s, %(event_name)s, %(version)s, %(creation_date)s,
                    %(received_at)s, %(payload_sha256)s, %(product_id)s,
                    %(product_ucode)s, %(product_name)s, %(purchase_status)s,
                    %(purchase_value)s, %(purchase_currency)s, %(payment_type)s,
                    %(offer_code)s, %(transaction_sha256)s, %(commissions)s,
                    %(state)s, 0, ''
                )
                ON CONFLICT (event_id) DO NOTHING
                RETURNING *
                """,
                {
                    "event_id": event.event_id,
                    "event_name": event.event_name,
                    "version": event.version,
                    "creation_date": event.creation_date,
                    "received_at": event.received_at,
                    "payload_sha256": event.payload_sha256,
                    "product_id": event.product_id,
                    "product_ucode": event.product_ucode,
                    "product_name": event.product_name,
                    "purchase_status": event.purchase_status,
                    "purchase_value": event.purchase_value,
                    "purchase_currency": event.purchase_currency,
                    "payment_type": event.payment_type,
                    "offer_code": event.offer_code,
                    "transaction_sha256": event.transaction_sha256,
                    "commissions": Jsonb([item.as_dict() for item in event.commissions]),
                    "state": initial_state.value,
                },
            ).fetchone()
            if inserted is not None:
                return _record(inserted), False
            existing = connection.execute(
                "SELECT * FROM hotmart_webhook_events WHERE event_id = %s",
                (record["event_id"],),
            ).fetchone()
            if existing is None:
                raise RuntimeError("Hotmart idempotency lookup failed")
            return _record(existing), True

    def pending(self, *, limit: int = 100) -> tuple[dict[str, Any], ...]:
        if limit < 1:
            return ()
        with self._connect() as connection:
            rows = connection.execute(
                """
                SELECT * FROM hotmart_webhook_events
                WHERE state = 'pending'
                ORDER BY received_at ASC
                LIMIT %s
                """,
                (limit,),
            ).fetchall()
        return tuple(_record(row) for row in rows)

    def mark_processed(self, event_id: str) -> dict[str, Any]:
        with self._connect() as connection:
            row = connection.execute(
                """
                UPDATE hotmart_webhook_events
                SET state = 'processed', processed_at = now(), last_error = '', updated_at = now()
                WHERE event_id = %s
                RETURNING *
                """,
                (event_id,),
            ).fetchone()
        return self._required(row, event_id)

    def mark_failed(self, event_id: str, error: str) -> dict[str, Any]:
        with self._connect() as connection:
            current = connection.execute(
                "SELECT attempts FROM hotmart_webhook_events WHERE event_id = %s FOR UPDATE",
                (event_id,),
            ).fetchone()
            if current is None:
                raise KeyError(f"Hotmart event not found: {event_id}")
            attempts = int(current["attempts"]) + 1
            next_state = (
                HotmartWebhookState.DEAD_LETTER.value
                if attempts >= self.max_attempts
                else HotmartWebhookState.FAILED.value
            )
            row = connection.execute(
                """
                UPDATE hotmart_webhook_events
                SET state = %s, attempts = %s, last_error = %s, updated_at = now()
                WHERE event_id = %s
                RETURNING *
                """,
                (next_state, attempts, _safe_error(error), event_id),
            ).fetchone()
        return self._required(row, event_id)

    def requeue(self, event_id: str) -> dict[str, Any]:
        with self._connect() as connection:
            row = connection.execute(
                """
                UPDATE hotmart_webhook_events
                SET state = 'pending', updated_at = now()
                WHERE event_id = %s AND state <> 'processed'
                RETURNING *
                """,
                (event_id,),
            ).fetchone()
        if row is None:
            with self._connect() as connection:
                exists = connection.execute(
                    "SELECT state FROM hotmart_webhook_events WHERE event_id = %s",
                    (event_id,),
                ).fetchone()
            if exists is None:
                raise KeyError(f"Hotmart event not found: {event_id}")
            raise ValueError("Processed events cannot be requeued")
        return _record(row)

    def summary(self) -> dict[str, int]:
        with self._connect() as connection:
            rows = connection.execute(
                "SELECT state, count(*) AS total FROM hotmart_webhook_events GROUP BY state"
            ).fetchall()
        result = {"total": 0}
        for state in HotmartWebhookState:
            result[state.value] = 0
        for row in rows:
            count = int(row["total"])
            result[str(row["state"])] = count
            result["total"] += count
        return result

    def _connect(self) -> Any:
        return psycopg.connect(self._connection_string, row_factory=dict_row)

    def _required(self, row: Any, event_id: str) -> dict[str, Any]:
        if row is None:
            raise KeyError(f"Hotmart event not found: {event_id}")
        return _record(row)


def _record(row: dict[str, Any]) -> dict[str, Any]:
    commissions = row.get("commissions")
    if isinstance(commissions, str):
        commissions = json.loads(commissions)
    processed_at = row.get("processed_at")
    return {
        "event_id": str(row.get("event_id") or ""),
        "event_name": str(row.get("event_name") or ""),
        "version": str(row.get("version") or ""),
        "creation_date": int(row.get("creation_date") or 0),
        "received_at": _timestamp(row.get("received_at")),
        "payload_sha256": str(row.get("payload_sha256") or ""),
        "product": {
            "id": str(row.get("product_id") or ""),
            "ucode": str(row.get("product_ucode") or ""),
            "name": str(row.get("product_name") or ""),
        },
        "purchase": {
            "status": str(row.get("purchase_status") or ""),
            "value": _float(row.get("purchase_value")),
            "currency": str(row.get("purchase_currency") or ""),
            "payment_type": str(row.get("payment_type") or ""),
            "offer_code": str(row.get("offer_code") or ""),
            "transaction_sha256": str(row.get("transaction_sha256") or ""),
        },
        "commissions": commissions if isinstance(commissions, list) else [],
        "state": str(row.get("state") or ""),
        "attempts": int(row.get("attempts") or 0),
        "last_error": str(row.get("last_error") or ""),
        "processed_at": _timestamp(processed_at) if processed_at else "",
    }


def _timestamp(value: Any) -> str:
    if isinstance(value, datetime):
        return value.isoformat()
    return str(value or "")


def _float(value: Any) -> float:
    if isinstance(value, Decimal):
        return float(value)
    try:
        return float(value)
    except (TypeError, ValueError):
        return 0.0


def _safe_error(value: str) -> str:
    return " ".join(str(value).split())[:500]
