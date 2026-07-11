"""Small HTTP server for the verified Hotmart webhook receiver."""

from __future__ import annotations

import argparse
import json
import os
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

from core.integrations.hotmart.webhook import (
    DEFAULT_HOTMART_WEBHOOK_STORE,
    HOTMART_HOTTOK_HEADER,
    HotmartAuthenticationError,
    HotmartPayloadError,
    HotmartWebhookConfigurationError,
    HotmartWebhookReceiver,
    HotmartWebhookStore,
)

DEFAULT_HOTMART_WEBHOOK_PATH = "/webhooks/hotmart/v2"
DEFAULT_MAX_BODY_BYTES = 1_048_576
HOTMART_HOTTOK_ENV = "AI_COMPANY_HOTMART_HOTTOK"


def create_hotmart_webhook_server(
    receiver: HotmartWebhookReceiver,
    *,
    host: str = "127.0.0.1",
    port: int = 8790,
    max_body_bytes: int = DEFAULT_MAX_BODY_BYTES,
) -> ThreadingHTTPServer:
    """Create a local HTTP server using a preconfigured receiver."""
    if max_body_bytes < 1:
        raise ValueError("max_body_bytes must be positive")

    class Handler(BaseHTTPRequestHandler):
        def do_GET(self) -> None:
            parsed = urlparse(self.path)
            if parsed.path == "/health":
                self._send_json(
                    {
                        "ok": receiver.configured,
                        "service": "hotmart-webhook",
                        "configured": receiver.configured,
                        "queue": receiver.store.summary(),
                    },
                    HTTPStatus.OK if receiver.configured else HTTPStatus.SERVICE_UNAVAILABLE,
                )
                return
            self._send_json({"ok": False, "error": "Not found"}, HTTPStatus.NOT_FOUND)

        def do_POST(self) -> None:
            parsed = urlparse(self.path)
            if parsed.path != DEFAULT_HOTMART_WEBHOOK_PATH:
                self._send_json({"ok": False, "error": "Not found"}, HTTPStatus.NOT_FOUND)
                return

            content_length = self._content_length()
            if content_length is None:
                self._send_json({"ok": False, "error": "Invalid Content-Length"}, HTTPStatus.BAD_REQUEST)
                return
            if content_length > max_body_bytes:
                self._send_json(
                    {"ok": False, "error": "Webhook body is too large"},
                    HTTPStatus.REQUEST_ENTITY_TOO_LARGE,
                )
                return

            raw_body = self.rfile.read(content_length)
            try:
                receipt = receiver.receive(raw_body, self.headers.get(HOTMART_HOTTOK_HEADER))
            except HotmartAuthenticationError:
                self._send_json({"ok": False, "error": "Unauthorized"}, HTTPStatus.UNAUTHORIZED)
                return
            except HotmartPayloadError as exc:
                self._send_json({"ok": False, "error": str(exc)}, HTTPStatus.BAD_REQUEST)
                return
            except HotmartWebhookConfigurationError:
                self._send_json({"ok": False, "error": "Receiver is not configured"}, HTTPStatus.SERVICE_UNAVAILABLE)
                return

            status = HTTPStatus.OK if receipt.duplicate else HTTPStatus.ACCEPTED
            self._send_json(receipt.as_dict(), status)

        def log_message(self, _format: str, *args: object) -> None:
            return

        def _content_length(self) -> int | None:
            try:
                value = int(self.headers.get("Content-Length", "0") or "0")
            except ValueError:
                return None
            return value if value >= 0 else None

        def _send_json(self, body: dict[str, Any], status: HTTPStatus) -> None:
            payload = json.dumps(body, ensure_ascii=False).encode("utf-8")
            self.send_response(int(status))
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(payload)))
            self.send_header("Cache-Control", "no-store")
            self.send_header("X-Content-Type-Options", "nosniff")
            self.end_headers()
            self.wfile.write(payload)

    return ThreadingHTTPServer((host, port), Handler)


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the verified Hotmart webhook receiver locally.")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8790)
    parser.add_argument("--store", default=str(DEFAULT_HOTMART_WEBHOOK_STORE))
    args = parser.parse_args()

    expected_hottok = os.environ.get(HOTMART_HOTTOK_ENV, "").strip()
    if not expected_hottok:
        raise SystemExit(f"Set {HOTMART_HOTTOK_ENV} before starting the receiver.")

    store = HotmartWebhookStore(Path(args.store))
    receiver = HotmartWebhookReceiver(expected_hottok, store)
    server = create_hotmart_webhook_server(receiver, host=args.host, port=args.port)
    print(f"Hotmart webhook receiver: http://{args.host}:{server.server_address[1]}{DEFAULT_HOTMART_WEBHOOK_PATH}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
