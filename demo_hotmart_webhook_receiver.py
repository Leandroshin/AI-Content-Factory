"""Demonstration: authenticated, private and idempotent Hotmart intake."""

from __future__ import annotations

import json
import shutil
from pathlib import Path
from threading import Thread
from urllib.error import HTTPError
from urllib.request import Request, urlopen

from core.content_factory.hotmart_webhook import (
    HOTMART_HOTTOK_HEADER,
    HotmartAuthenticationError,
    HotmartPayloadError,
    HotmartWebhookReceiver,
    HotmartWebhookState,
    HotmartWebhookStore,
)
from core.content_factory.hotmart_webhook_server import create_hotmart_webhook_server

_ASSERTION_COUNTER = 0
_TEST_HOTTOK = "hotmart_test_hottok_never_persist"


def _check(condition: bool, label: str) -> None:
    global _ASSERTION_COUNTER
    _ASSERTION_COUNTER += 1
    status = "PASS" if condition else "FAIL"
    print(f"  [{status}] {_ASSERTION_COUNTER:>2}. {label}")
    if not condition:
        raise AssertionError(label)


def _payload(event_id: str, event: str = "PURCHASE_APPROVED") -> dict:
    return {
        "id": event_id,
        "creation_date": 1783700000000,
        "event": event,
        "version": "2.0.0",
        "data": {
            "product": {
                "id": 213344,
                "ucode": "product-ucode-safe",
                "name": "Curso de Conteudo com IA",
                "support_email": "support-secret@example.com",
            },
            "buyer": {
                "email": "buyer-secret@example.com",
                "name": "Buyer Secret Name",
                "document": "12345678900",
                "address": {"street": "Private Street", "number": "99"},
            },
            "producer": {"name": "Producer Secret", "document": "00999888000177"},
            "commissions": [
                {"value": 42.5, "currency_value": "BRL", "source": "AFFILIATE"},
                {"value": 7.0, "currency_value": "BRL", "source": "PRODUCER"},
            ],
            "purchase": {
                "status": "APPROVED",
                "transaction": "HP-SECRET-TRANSACTION-123",
                "full_price": {"value": 149.9, "currency_value": "BRL"},
                "offer": {"code": "offer-public-code"},
                "payment": {
                    "type": "PIX",
                    "pix_code": "PIX-SECRET-CODE",
                    "billet_barcode": "BILLET-SECRET-CODE",
                },
            },
        },
    }


def _raw(payload: dict) -> bytes:
    return json.dumps(payload, ensure_ascii=False).encode("utf-8")


def _request(
    base_url: str,
    path: str,
    *,
    body: bytes | None = None,
    hottok: str | None = None,
) -> tuple[int, dict, dict[str, str]]:
    headers = {"Content-Type": "application/json"}
    if hottok is not None:
        headers[HOTMART_HOTTOK_HEADER] = hottok
    request = Request(
        f"{base_url}{path}",
        data=body,
        method="POST" if body is not None else "GET",
        headers=headers,
    )
    try:
        with urlopen(request, timeout=5) as response:
            return (
                response.status,
                json.loads(response.read().decode("utf-8")),
                dict(response.headers.items()),
            )
    except HTTPError as exc:
        return exc.code, json.loads(exc.read().decode("utf-8")), dict(exc.headers.items())


def main() -> None:
    print("=" * 72)
    print("Hotmart Webhook Receiver - Verified Intake")
    print("=" * 72)

    temp_dir = Path("temp/hotmart_webhook_receiver")
    if temp_dir.exists():
        shutil.rmtree(temp_dir)
    store_path = temp_dir / "events.json"
    store = HotmartWebhookStore(store_path, max_attempts=2)
    receiver = HotmartWebhookReceiver(_TEST_HOTTOK, store)

    print("\n" + "-" * 72)
    print("Step 1: Authenticate, redact and persist one event")
    print("-" * 72)
    payload = _payload("event-001")
    receipt = receiver.receive(_raw(payload), _TEST_HOTTOK)
    _check(receipt.event_id == "event-001", "Authenticated event returns its Hotmart event id")
    _check(receipt.state is HotmartWebhookState.PENDING, "Allowed purchase event enters pending state")
    _check(receipt.duplicate is False, "First delivery is not a duplicate")
    _check(store_path.exists(), "Redacted event store is written atomically")

    persisted_text = store_path.read_text(encoding="utf-8")
    persisted = json.loads(persisted_text)
    record = persisted["events"]["event-001"]
    _check(record["product"]["name"] == "Curso de Conteudo com IA", "Product identity is preserved")
    _check(record["purchase"]["value"] == 149.9, "Business purchase value is preserved")
    _check(record["commissions"][0]["source"] == "AFFILIATE", "Commission metrics are preserved")
    _check(len(record["purchase"]["transaction_sha256"]) == 64, "Transaction is stored only as SHA-256")
    _check("buyer-secret@example.com" not in persisted_text, "Buyer email is not persisted")
    _check("Buyer Secret Name" not in persisted_text, "Buyer name is not persisted")
    _check("12345678900" not in persisted_text, "Buyer document is not persisted")
    _check("Private Street" not in persisted_text, "Buyer address is not persisted")
    _check("PIX-SECRET-CODE" not in persisted_text, "PIX code is not persisted")
    _check("BILLET-SECRET-CODE" not in persisted_text, "Billet barcode is not persisted")
    _check("HP-SECRET-TRANSACTION-123" not in persisted_text, "Raw transaction id is not persisted")
    _check(_TEST_HOTTOK not in persisted_text, "HOTTOK is not persisted")

    print("\n" + "-" * 72)
    print("Step 2: Enforce idempotency and authentication")
    print("-" * 72)
    duplicate = receiver.receive(_raw(payload), _TEST_HOTTOK)
    _check(duplicate.duplicate is True, "Repeated Hotmart id is recognized as duplicate")
    _check(store.summary()["total"] == 1, "Duplicate delivery does not create another record")

    try:
        receiver.receive(_raw(_payload("event-invalid-auth")), "wrong-token")
    except HotmartAuthenticationError:
        invalid_auth_blocked = True
    else:
        invalid_auth_blocked = False
    _check(invalid_auth_blocked, "Invalid HOTTOK is blocked before payload storage")
    _check(store.summary()["total"] == 1, "Invalid authentication leaves store unchanged")

    malformed = _payload("event-invalid-version")
    malformed["version"] = "1.0.0"
    try:
        receiver.receive(_raw(malformed), _TEST_HOTTOK)
    except HotmartPayloadError:
        invalid_version_blocked = True
    else:
        invalid_version_blocked = False
    _check(invalid_version_blocked, "Unsupported webhook version is rejected")

    print("\n" + "-" * 72)
    print("Step 3: Ignore unconfigured events and prove recovery lifecycle")
    print("-" * 72)
    ignored = receiver.receive(_raw(_payload("event-ignored", "PURCHASE_COMPLETE")), _TEST_HOTTOK)
    _check(ignored.state is HotmartWebhookState.IGNORED, "Unconfigured event is acknowledged but ignored")
    _check(store.summary()["ignored"] == 1, "Ignored event is visible in operational summary")
    _check(len(store.pending()) == 1, "Only approved configured event is pending")

    failed_once = store.mark_failed("event-001", "Temporary metrics worker failure")
    _check(failed_once["state"] == "failed", "First worker failure is retained for retry")
    _check(failed_once["attempts"] == 1, "Failure attempt is counted")
    dead_letter = store.mark_failed("event-001", "Second worker failure")
    _check(dead_letter["state"] == "dead_letter", "Retry limit moves event to dead-letter")
    _check(store.state()["dead_letter"] == ["event-001"], "Dead-letter index is persisted")
    requeued = store.requeue("event-001")
    _check(requeued["state"] == "pending", "Explicit owner action can requeue an event")
    processed = store.mark_processed("event-001")
    _check(processed["state"] == "processed", "Recovered event can be marked processed")
    _check(store.summary()["processed"] == 1, "Processed total is observable")

    print("\n" + "-" * 72)
    print("Step 4: Exercise real HTTP routes without external traffic")
    print("-" * 72)
    server = create_hotmart_webhook_server(receiver, host="127.0.0.1", port=0, max_body_bytes=1024)
    host, port = server.server_address
    base_url = f"http://{host}:{port}"
    thread = Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        health_status, health, health_headers = _request(base_url, "/health")
        _check(health_status == 200 and health["configured"] is True, "Health route confirms configured receiver")
        _check(health["queue"]["total"] == 2, "Health route exposes only aggregate queue counts")
        _check(health_headers.get("Cache-Control") == "no-store", "Health response disables caching")

        server_payload = _raw(_payload("event-http-001"))
        accepted_status, accepted, accepted_headers = _request(
            base_url,
            "/webhooks/hotmart/v2",
            body=server_payload,
            hottok=_TEST_HOTTOK,
        )
        _check(accepted_status == 202 and accepted["ok"] is True, "New HTTP delivery returns 202 Accepted")
        _check(accepted["state"] == "pending", "HTTP delivery is durably queued")
        _check(accepted_headers.get("X-Content-Type-Options") == "nosniff", "Webhook response adds security header")

        duplicate_status, duplicate_body, _ = _request(
            base_url,
            "/webhooks/hotmart/v2",
            body=server_payload,
            hottok=_TEST_HOTTOK,
        )
        _check(duplicate_status == 200 and duplicate_body["duplicate"] is True, "HTTP retry returns safe idempotent 200")

        auth_status, auth_body, _ = _request(
            base_url,
            "/webhooks/hotmart/v2",
            body=_raw(_payload("event-http-auth")),
            hottok="wrong-token",
        )
        _check(auth_status == 401 and auth_body["error"] == "Unauthorized", "HTTP invalid token gets generic 401")
        _check(_TEST_HOTTOK not in json.dumps(auth_body), "Authentication response never exposes expected token")

        malformed_status, malformed_body, _ = _request(
            base_url,
            "/webhooks/hotmart/v2",
            body=b"not-json",
            hottok=_TEST_HOTTOK,
        )
        _check(malformed_status == 400 and malformed_body["ok"] is False, "Malformed HTTP JSON gets 400")

        large_status, large_body, _ = _request(
            base_url,
            "/webhooks/hotmart/v2",
            body=b"x" * 2048,
            hottok=_TEST_HOTTOK,
        )
        _check(large_status == 413 and large_body["ok"] is False, "Oversized body is rejected before parsing")

        missing_status, missing_body, _ = _request(
            base_url,
            "/not-a-webhook",
            body=server_payload,
            hottok=_TEST_HOTTOK,
        )
        _check(missing_status == 404 and missing_body["ok"] is False, "Unknown HTTP route gets 404")
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=5)

    _check(store.summary()["total"] == 3, "Only authenticated, valid event ids reach the final store")
    print(f"\n{'=' * 72}")
    print(f"All {_ASSERTION_COUNTER} assertions passed.")
    print(f"{'=' * 72}")


if __name__ == "__main__":
    main()
