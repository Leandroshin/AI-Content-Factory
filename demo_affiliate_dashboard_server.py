"""Demonstration: local backend for the affiliate approval dashboard.

The demo starts the server on a temporary port, drives the HTTP endpoints, and
proves approval/rejection/publication state is persisted without real Telegram
traffic.
"""

from __future__ import annotations

import json
import shutil
from pathlib import Path
from threading import Thread
from urllib.error import HTTPError
from urllib.request import Request, urlopen

from core.content_factory.affiliate_dashboard_server import (
    AffiliateDashboardStore,
    create_affiliate_dashboard_server,
    demo_dashboard_state,
)


_ASSERTION_COUNTER = 0


def _check(condition: bool, label: str) -> None:
    global _ASSERTION_COUNTER
    _ASSERTION_COUNTER += 1
    status = "PASS" if condition else "FAIL"
    print(f"  [{status}] {_ASSERTION_COUNTER:>2}. {label}")
    if not condition:
        raise AssertionError(label)


def _get_json(base_url: str, path: str) -> dict:
    with urlopen(f"{base_url}{path}", timeout=5) as response:
        return json.loads(response.read().decode("utf-8"))


def _get_text(base_url: str, path: str) -> str:
    with urlopen(f"{base_url}{path}", timeout=5) as response:
        return response.read().decode("utf-8")


def _post_json(base_url: str, path: str, body: dict | None = None) -> dict:
    payload = json.dumps(body or {}).encode("utf-8")
    request = Request(
        f"{base_url}{path}",
        data=payload,
        method="POST",
        headers={"Content-Type": "application/json"},
    )
    with urlopen(request, timeout=5) as response:
        return json.loads(response.read().decode("utf-8"))


def _post_json_error(base_url: str, path: str, body: dict | None = None) -> dict:
    try:
        return _post_json(base_url, path, body)
    except HTTPError as exc:
        return json.loads(exc.read().decode("utf-8"))


def main() -> None:
    print("=" * 70)
    print("Affiliate Dashboard Server - Local Backend")
    print("=" * 70)

    temp_dir = Path("temp/affiliate_dashboard_server")
    if temp_dir.exists():
        shutil.rmtree(temp_dir)
    store_path = temp_dir / "queue.json"
    store = AffiliateDashboardStore(store_path)
    seeded = store.seed(demo_dashboard_state())
    _check(store_path.exists(), "Server queue is persisted on seed")
    _check(seeded["mode"] == "server", "Seeded state runs in server mode")
    _check(seeded["summary"]["pending"] == 2, "Seeded state starts with two pending offers")

    server = create_affiliate_dashboard_server(store, host="127.0.0.1", port=0)
    host, port = server.server_address
    base_url = f"http://{host}:{port}"
    thread = Thread(target=server.serve_forever, daemon=True)
    thread.start()

    try:
        print("\n" + "-" * 70)
        print("Step 1: Read server state and HTML")
        print("-" * 70)
        state_payload = _get_json(base_url, "/api/state")
        _check(state_payload["ok"] is True, "GET /api/state succeeds")
        state = state_payload["state"]
        _check(state["mode"] == "server", "API state is server-backed")
        _check(state["summary"]["total"] == 2, "API state returns two offers")
        first_id = state["offers"][0]["id"]
        second_id = state["offers"][1]["id"]

        html = _get_text(base_url, "/")
        _check("Affiliate Approval Dashboard" in html, "GET / renders dashboard HTML")
        _check("serverAction" in html, "HTML includes server-backed actions")
        _check("/api/offers/" in html, "HTML calls offer action endpoints")
        _check("window.print" not in html, "HTML has no print/A4 workflow")

        print("\n" + "-" * 70)
        print("Step 2: Enforce approval gate before publishing")
        print("-" * 70)
        blocked = _post_json_error(base_url, f"/api/offers/{first_id}/publish")
        _check(blocked["ok"] is False, "Publish before approval is rejected")
        _check("Aprove" in blocked["error"], "Publish rejection explains approval requirement")

        print("\n" + "-" * 70)
        print("Step 3: Approve and publish one offer")
        print("-" * 70)
        approved = _post_json(base_url, f"/api/offers/{first_id}/approve", {"decided_by": "Shin"})
        _check(approved["ok"] is True, "Approve endpoint succeeds")
        _check(approved["offer"]["approval_status"] == "approved", "Offer becomes approved")
        _check(approved["summary"]["approved"] == 1, "Summary counts approved offer")

        published = _post_json(base_url, f"/api/offers/{first_id}/publish")
        _check(published["ok"] is True, "Publish endpoint succeeds after approval")
        _check(published["offer"]["telegram_status"] == "sent_mock", "Telegram publish stays in mock-safe mode")
        _check(published["offer"]["telegram_message_id"] == 1001, "Mock Telegram message id is recorded")
        _check(published["summary"]["published"] == 1, "Summary counts published offer")

        print("\n" + "-" * 70)
        print("Step 4: Reject another offer and confirm persistence")
        print("-" * 70)
        rejected = _post_json(base_url, f"/api/offers/{second_id}/reject", {"reason": "Imagem precisa melhorar."})
        _check(rejected["ok"] is True, "Reject endpoint succeeds")
        _check(rejected["offer"]["status"] == "blocked", "Rejected offer becomes blocked")
        _check(rejected["summary"]["blocked"] == 1, "Summary counts blocked offer")

        saved = json.loads(store_path.read_text(encoding="utf-8"))
        _check(saved["summary"]["published"] == 1, "Published state persisted to disk")
        _check(saved["summary"]["blocked"] == 1, "Rejected state persisted to disk")
        _check(saved["offers"][0]["telegram_status"] == "sent_mock", "Persisted first offer has Telegram status")
        _check(saved["offers"][1]["status"] == "blocked", "Persisted second offer is blocked")
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=5)

    print(f"\n{'=' * 70}")
    print(f"All {_ASSERTION_COUNTER} assertions passed.")
    print(f"{'=' * 70}")


if __name__ == "__main__":
    main()
