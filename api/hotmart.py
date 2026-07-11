"""Vercel Python Function for verified Hotmart webhook intake."""

from __future__ import annotations

import json
import os
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler
from typing import Any

from core.integrations.hotmart.postgres import HotmartPostgresStore
from core.integrations.hotmart.webhook import (
    HOTMART_HOTTOK_HEADER,
    HotmartAuthenticationError,
    HotmartPayloadError,
    HotmartWebhookConfigurationError,
    HotmartWebhookReceiver,
)

MAX_BODY_BYTES = 1_048_576
HOTTOK_ENV = "AI_COMPANY_HOTMART_HOTTOK"
DATABASE_URL_ENV = "AI_COMPANY_DATABASE_URL"


def _receiver() -> HotmartWebhookReceiver:
    hottok = os.environ.get(HOTTOK_ENV, "").strip()
    database_url = os.environ.get(DATABASE_URL_ENV, "").strip()
    if not hottok or not database_url:
        raise HotmartWebhookConfigurationError("Hosted Hotmart receiver is not configured")
    return HotmartWebhookReceiver(hottok, HotmartPostgresStore(database_url))


class handler(BaseHTTPRequestHandler):  # noqa: N801 - Vercel entrypoint contract
    """Vercel-compatible request handler."""

    def do_GET(self) -> None:
        hottok_present = bool(os.environ.get(HOTTOK_ENV, "").strip())
        database_url_present = bool(os.environ.get(DATABASE_URL_ENV, "").strip())
        if not hottok_present or not database_url_present:
            self._send_json(
                {
                    "ok": False,
                    "service": "hotmart-webhook",
                    "configured": False,
                    "configuration": {
                        "hottok_present": hottok_present,
                        "database_url_present": database_url_present,
                    },
                },
                HTTPStatus.SERVICE_UNAVAILABLE,
            )
            return
        try:
            receiver = _receiver()
            summary = receiver.store.summary()
        except HotmartWebhookConfigurationError:
            self._send_json(
                {
                    "ok": False,
                    "service": "hotmart-webhook",
                    "configured": False,
                },
                HTTPStatus.SERVICE_UNAVAILABLE,
            )
            return
        except Exception as exc:
            self._send_json(
                {
                    "ok": False,
                    "service": "hotmart-webhook",
                    "configured": True,
                    "database": "unavailable",
                    "error_type": type(exc).__name__,
                },
                HTTPStatus.SERVICE_UNAVAILABLE,
            )
            return
        self._send_json(
            {
                "ok": True,
                "service": "hotmart-webhook",
                "configured": True,
                "database": "available",
                "queue": summary,
            },
            HTTPStatus.OK,
        )

    def do_POST(self) -> None:
        content_length = self._content_length()
        if content_length is None:
            self._send_json({"ok": False, "error": "Invalid Content-Length"}, HTTPStatus.BAD_REQUEST)
            return
        if content_length > MAX_BODY_BYTES:
            self._send_json(
                {"ok": False, "error": "Webhook body is too large"},
                HTTPStatus.REQUEST_ENTITY_TOO_LARGE,
            )
            return

        raw_body = self.rfile.read(content_length)
        try:
            receipt = _receiver().receive(raw_body, self.headers.get(HOTMART_HOTTOK_HEADER))
        except HotmartAuthenticationError:
            self._send_json({"ok": False, "error": "Unauthorized"}, HTTPStatus.UNAUTHORIZED)
            return
        except HotmartPayloadError as exc:
            self._send_json({"ok": False, "error": str(exc)}, HTTPStatus.BAD_REQUEST)
            return
        except HotmartWebhookConfigurationError:
            self._send_json({"ok": False, "error": "Receiver is not configured"}, HTTPStatus.SERVICE_UNAVAILABLE)
            return
        except Exception:
            self._send_json({"ok": False, "error": "Temporary intake failure"}, HTTPStatus.SERVICE_UNAVAILABLE)
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
