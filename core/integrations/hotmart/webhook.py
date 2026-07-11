"""Verified Hotmart webhook intake for affiliate business metrics.

The receiver deliberately stores only a redacted operational projection of
each event. Buyer, producer, address, document and payment payloads never enter
the local event store or application logs.
"""

from __future__ import annotations

import hashlib
import hmac
import json
from collections.abc import Iterable
from dataclasses import dataclass
from datetime import UTC, datetime
from enum import StrEnum
from pathlib import Path
from threading import RLock
from typing import Any, Protocol

DEFAULT_HOTMART_WEBHOOK_STORE = Path(".ai_company/hotmart/webhook_events.json")
HOTMART_HOTTOK_HEADER = "X-HOTMART-HOTTOK"
HOTMART_WEBHOOK_VERSION = "2.0.0"
DEFAULT_HOTMART_EVENTS = frozenset(
    {
        "PURCHASE_APPROVED",
        "PURCHASE_CANCELED",
        "PURCHASE_REFUNDED",
        "PURCHASE_CHARGEBACK",
        "PURCHASE_DELAYED",
    }
)


class HotmartWebhookState(StrEnum):
    """Lifecycle state of a safely stored Hotmart event."""

    PENDING = "pending"
    PROCESSED = "processed"
    FAILED = "failed"
    DEAD_LETTER = "dead_letter"
    IGNORED = "ignored"


@dataclass(frozen=True, slots=True)
class HotmartCommission:
    """Non-personal commission amount extracted from a Hotmart event."""

    source: str
    value: float
    currency: str

    def as_dict(self) -> dict[str, Any]:
        return {
            "source": self.source,
            "value": self.value,
            "currency": self.currency,
        }


@dataclass(frozen=True, slots=True)
class HotmartWebhookEvent:
    """Privacy-safe projection of one authenticated webhook event."""

    event_id: str
    event_name: str
    version: str
    creation_date: int
    received_at: str
    payload_sha256: str
    product_id: str
    product_ucode: str
    product_name: str
    purchase_status: str
    purchase_value: float
    purchase_currency: str
    payment_type: str
    offer_code: str
    transaction_sha256: str
    commissions: tuple[HotmartCommission, ...]

    def as_record(self, state: HotmartWebhookState) -> dict[str, Any]:
        return {
            "event_id": self.event_id,
            "event_name": self.event_name,
            "version": self.version,
            "creation_date": self.creation_date,
            "received_at": self.received_at,
            "payload_sha256": self.payload_sha256,
            "product": {
                "id": self.product_id,
                "ucode": self.product_ucode,
                "name": self.product_name,
            },
            "purchase": {
                "status": self.purchase_status,
                "value": self.purchase_value,
                "currency": self.purchase_currency,
                "payment_type": self.payment_type,
                "offer_code": self.offer_code,
                "transaction_sha256": self.transaction_sha256,
            },
            "commissions": [commission.as_dict() for commission in self.commissions],
            "state": state.value,
            "attempts": 0,
            "last_error": "",
            "processed_at": "",
        }


@dataclass(frozen=True, slots=True)
class HotmartWebhookReceipt:
    """Small response returned after verified, durable intake."""

    event_id: str
    event_name: str
    state: HotmartWebhookState
    duplicate: bool

    def as_dict(self) -> dict[str, Any]:
        return {
            "ok": True,
            "event_id": self.event_id,
            "event": self.event_name,
            "state": self.state.value,
            "duplicate": self.duplicate,
        }


class HotmartWebhookError(ValueError):
    """Base error for requests that must not enter the event store."""


class HotmartAuthenticationError(HotmartWebhookError):
    """Raised when the HOTTOK header is missing or invalid."""


class HotmartPayloadError(HotmartWebhookError):
    """Raised when a request is not a valid Hotmart 2.0.0 event."""


class HotmartWebhookConfigurationError(RuntimeError):
    """Raised when the receiver has no server-side HOTTOK configured."""


class HotmartWebhookStoreContract(Protocol):
    """Minimal domain contract shared by local and hosted event stores."""

    def register(
        self,
        event: HotmartWebhookEvent,
        *,
        initial_state: HotmartWebhookState = HotmartWebhookState.PENDING,
    ) -> tuple[dict[str, Any], bool]: ...

    def summary(self) -> dict[str, int]: ...


class HotmartWebhookStore:
    """Atomic JSON event store with idempotency and dead-letter tracking."""

    def __init__(
        self,
        path: str | Path = DEFAULT_HOTMART_WEBHOOK_STORE,
        *,
        max_attempts: int = 5,
    ) -> None:
        if max_attempts < 1:
            raise ValueError("max_attempts must be at least 1")
        self.path = Path(path)
        self.max_attempts = max_attempts
        self._lock = RLock()

    def state(self) -> dict[str, Any]:
        with self._lock:
            return self._load()

    def register(
        self,
        event: HotmartWebhookEvent,
        *,
        initial_state: HotmartWebhookState = HotmartWebhookState.PENDING,
    ) -> tuple[dict[str, Any], bool]:
        """Store an event once and return ``(record, duplicate)``."""
        with self._lock:
            state = self._load()
            events = state["events"]
            existing = events.get(event.event_id)
            if isinstance(existing, dict):
                return dict(existing), True

            record = event.as_record(initial_state)
            events[event.event_id] = record
            state["order"].append(event.event_id)
            state["updated_at"] = _now()
            self._save(state)
            return dict(record), False

    def pending(self, *, limit: int = 100) -> tuple[dict[str, Any], ...]:
        """Return pending records in arrival order without raw payload data."""
        if limit < 1:
            return ()
        with self._lock:
            state = self._load()
            records = []
            for event_id in state["order"]:
                record = state["events"].get(event_id)
                if isinstance(record, dict) and record.get("state") == HotmartWebhookState.PENDING.value:
                    records.append(dict(record))
                if len(records) >= limit:
                    break
            return tuple(records)

    def mark_processed(self, event_id: str) -> dict[str, Any]:
        """Mark one queued event as processed by a downstream workflow."""
        with self._lock:
            state = self._load()
            record = self._record(state, event_id)
            record["state"] = HotmartWebhookState.PROCESSED.value
            record["processed_at"] = _now()
            record["last_error"] = ""
            state["updated_at"] = _now()
            self._save(state)
            return dict(record)

    def mark_failed(self, event_id: str, error: str) -> dict[str, Any]:
        """Record a processing failure and dead-letter after the retry limit."""
        with self._lock:
            state = self._load()
            record = self._record(state, event_id)
            attempts = int(record.get("attempts", 0)) + 1
            record["attempts"] = attempts
            record["last_error"] = _safe_error(error)
            if attempts >= self.max_attempts:
                record["state"] = HotmartWebhookState.DEAD_LETTER.value
                if event_id not in state["dead_letter"]:
                    state["dead_letter"].append(event_id)
            else:
                record["state"] = HotmartWebhookState.FAILED.value
            state["updated_at"] = _now()
            self._save(state)
            return dict(record)

    def requeue(self, event_id: str) -> dict[str, Any]:
        """Move a failed event back to pending for an explicit retry."""
        with self._lock:
            state = self._load()
            record = self._record(state, event_id)
            if record.get("state") == HotmartWebhookState.PROCESSED.value:
                raise ValueError("Processed events cannot be requeued")
            record["state"] = HotmartWebhookState.PENDING.value
            if event_id in state["dead_letter"]:
                state["dead_letter"].remove(event_id)
            state["updated_at"] = _now()
            self._save(state)
            return dict(record)

    def summary(self) -> dict[str, int]:
        """Return event counts by operational state."""
        with self._lock:
            state = self._load()
            records = tuple(state["events"].values())
            result = {"total": len(records)}
            for item in HotmartWebhookState:
                result[item.value] = sum(1 for record in records if record.get("state") == item.value)
            return result

    def _load(self) -> dict[str, Any]:
        if not self.path.exists():
            return self._empty_state()
        data = json.loads(self.path.read_text(encoding="utf-8"))
        if not isinstance(data, dict):
            raise ValueError("Hotmart event store must contain a JSON object")
        data.setdefault("schema_version", 1)
        data.setdefault("created_at", _now())
        data.setdefault("updated_at", data["created_at"])
        data.setdefault("events", {})
        data.setdefault("order", [])
        data.setdefault("dead_letter", [])
        if not isinstance(data["events"], dict):
            raise ValueError("Hotmart event store events must be an object")
        return data

    def _save(self, state: dict[str, Any]) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        temporary = self.path.with_suffix(f"{self.path.suffix}.tmp")
        temporary.write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8")
        temporary.replace(self.path)

    def _record(self, state: dict[str, Any], event_id: str) -> dict[str, Any]:
        record = state["events"].get(event_id)
        if not isinstance(record, dict):
            raise KeyError(f"Hotmart event not found: {event_id}")
        return record

    def _empty_state(self) -> dict[str, Any]:
        created_at = _now()
        return {
            "schema_version": 1,
            "created_at": created_at,
            "updated_at": created_at,
            "events": {},
            "order": [],
            "dead_letter": [],
        }


class HotmartWebhookReceiver:
    """Authenticate, validate, redact and durably queue Hotmart events."""

    def __init__(
        self,
        expected_hottok: str,
        store: HotmartWebhookStoreContract,
        *,
        allowed_events: Iterable[str] = DEFAULT_HOTMART_EVENTS,
    ) -> None:
        self._expected_hottok = expected_hottok.strip()
        self.store = store
        self.allowed_events = frozenset(str(event).strip().upper() for event in allowed_events if str(event).strip())

    @property
    def configured(self) -> bool:
        return bool(self._expected_hottok)

    def receive(self, raw_body: bytes, provided_hottok: str | None) -> HotmartWebhookReceipt:
        """Accept one request after constant-time HOTTOK verification."""
        self._authenticate(provided_hottok)
        payload = _decode_payload(raw_body)
        event = _project_event(payload, raw_body)
        initial_state = (
            HotmartWebhookState.PENDING
            if event.event_name in self.allowed_events
            else HotmartWebhookState.IGNORED
        )
        record, duplicate = self.store.register(event, initial_state=initial_state)
        return HotmartWebhookReceipt(
            event_id=event.event_id,
            event_name=event.event_name,
            state=HotmartWebhookState(str(record["state"])),
            duplicate=duplicate,
        )

    def _authenticate(self, provided_hottok: str | None) -> None:
        if not self.configured:
            raise HotmartWebhookConfigurationError("Hotmart HOTTOK is not configured on the server")
        supplied = (provided_hottok or "").strip()
        if not supplied or not hmac.compare_digest(self._expected_hottok, supplied):
            raise HotmartAuthenticationError("Invalid Hotmart authentication header")


def _decode_payload(raw_body: bytes) -> dict[str, Any]:
    if not raw_body:
        raise HotmartPayloadError("Empty webhook body")
    try:
        payload = json.loads(raw_body.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise HotmartPayloadError("Webhook body must be valid UTF-8 JSON") from exc
    if not isinstance(payload, dict):
        raise HotmartPayloadError("Webhook payload must be a JSON object")
    return payload


def _project_event(payload: dict[str, Any], raw_body: bytes) -> HotmartWebhookEvent:
    event_id = _required_text(payload, "id")
    event_name = _required_text(payload, "event").upper()
    version = _required_text(payload, "version")
    if version != HOTMART_WEBHOOK_VERSION:
        raise HotmartPayloadError(f"Unsupported Hotmart webhook version: {version}")
    creation_date = payload.get("creation_date")
    if isinstance(creation_date, bool) or not isinstance(creation_date, int):
        raise HotmartPayloadError("creation_date must be an integer timestamp in milliseconds")
    data = payload.get("data")
    if not isinstance(data, dict):
        raise HotmartPayloadError("data must be a JSON object")

    product = _mapping(data.get("product"))
    purchase = _mapping(data.get("purchase"))
    price = _mapping(purchase.get("full_price")) or _mapping(purchase.get("price"))
    payment = _mapping(purchase.get("payment"))
    offer = _mapping(purchase.get("offer"))
    transaction = str(purchase.get("transaction") or "").strip()

    return HotmartWebhookEvent(
        event_id=event_id,
        event_name=event_name,
        version=version,
        creation_date=creation_date,
        received_at=_now(),
        payload_sha256=hashlib.sha256(raw_body).hexdigest(),
        product_id=str(product.get("id") or ""),
        product_ucode=str(product.get("ucode") or ""),
        product_name=str(product.get("name") or "").strip(),
        purchase_status=str(purchase.get("status") or "").strip().upper(),
        purchase_value=_number(price.get("value")),
        purchase_currency=str(price.get("currency_value") or "").strip().upper(),
        payment_type=str(payment.get("type") or "").strip().upper(),
        offer_code=str(offer.get("code") or "").strip(),
        transaction_sha256=hashlib.sha256(transaction.encode("utf-8")).hexdigest() if transaction else "",
        commissions=_commissions(data.get("commissions")),
    )


def _commissions(value: Any) -> tuple[HotmartCommission, ...]:
    if not isinstance(value, list):
        return ()
    result = []
    for item in value:
        if not isinstance(item, dict):
            continue
        result.append(
            HotmartCommission(
                source=str(item.get("source") or "UNKNOWN").strip().upper(),
                value=_number(item.get("value")),
                currency=str(item.get("currency_value") or "").strip().upper(),
            )
        )
    return tuple(result)


def _required_text(payload: dict[str, Any], key: str) -> str:
    value = str(payload.get(key) or "").strip()
    if not value:
        raise HotmartPayloadError(f"Missing required field: {key}")
    return value


def _mapping(value: Any) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def _number(value: Any) -> float:
    if isinstance(value, bool):
        return 0.0
    try:
        return float(value)
    except (TypeError, ValueError):
        return 0.0


def _safe_error(value: str) -> str:
    compact = " ".join(str(value).split())
    return compact[:500]


def _now() -> str:
    return datetime.now(UTC).isoformat()
