"""Local backend for the affiliate approval dashboard.

The server is intentionally small and domain-specific. It persists the offer
queue locally, exposes approval actions for the dashboard, and keeps Telegram
publication in MOCK mode unless a future controlled workflow opts into REAL.
"""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any
from urllib.parse import unquote, urlparse
from uuid import uuid4

from core.content_factory.affiliate_dashboard import AffiliateApprovalDashboardRenderer
from core.tools import TelegramAdapter, ToolRequest


DEFAULT_DASHBOARD_STORE = Path(".ai_company/affiliate_dashboard/queue.json")
DEFAULT_TELEGRAM_CHAT_ID = "@achadosbaratosBrasil"
_TEST_TELEGRAM_TOKEN = "test_telegram_token_dashboard_server"
_PUBLISHED_TELEGRAM_STATUSES = {"sent", "sent_mock"}


class AffiliateDashboardStore:
    """Persist and mutate the affiliate dashboard queue."""

    def __init__(
        self,
        path: str | Path = DEFAULT_DASHBOARD_STORE,
        *,
        default_chat_id: str = DEFAULT_TELEGRAM_CHAT_ID,
        telegram_token: str = _TEST_TELEGRAM_TOKEN,
    ) -> None:
        self.path = Path(path)
        self.default_chat_id = default_chat_id
        self.telegram_token = telegram_token

    def load(self) -> dict[str, Any]:
        """Load the current dashboard state from disk."""
        if not self.path.exists():
            return self._normalize_state(self._empty_state())
        data = json.loads(self.path.read_text(encoding="utf-8"))
        return self._normalize_state(data)

    def save(self, state: dict[str, Any]) -> dict[str, Any]:
        """Persist a normalized dashboard state."""
        normalized = self._normalize_state(state)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(json.dumps(normalized, ensure_ascii=False, indent=2), encoding="utf-8")
        return normalized

    def seed(self, state: dict[str, Any]) -> dict[str, Any]:
        """Replace the queue with a supplied dashboard state."""
        return self.save(state)

    def state(self) -> dict[str, Any]:
        """Return the current normalized state."""
        return self.load()

    def create_manual_offer(self, payload: dict[str, Any]) -> dict[str, Any]:
        """Create a pending offer from manual owner input."""
        title = str(payload.get("product_name") or payload.get("title") or "").strip()
        if not title:
            raise ValueError("Informe o nome do produto.")
        affiliate_url = str(payload.get("affiliate_url") or "").strip()
        if not affiliate_url:
            raise ValueError("Informe o link afiliado antes de criar a oferta.")

        state = self.load()
        offer = self._manual_offer(payload, title=title, affiliate_url=affiliate_url)
        state.setdefault("offers", []).insert(0, offer)
        saved = self.save(state)
        return saved["offers"][0]

    def approve(self, offer_id: str, *, decided_by: str = "owner", reason: str = "") -> dict[str, Any]:
        """Mark an offer as approved for publication."""
        state = self.load()
        offer = self._find_offer(state, offer_id)
        if offer.get("status") == "published":
            return self.save(state)["offers"][self._offer_index(state, offer_id)]
        offer["approval_status"] = "approved"
        offer["status"] = "approved"
        offer["approved_by"] = decided_by
        offer["decision_reason"] = reason
        offer["updated_at"] = _now()
        saved = self.save(state)
        return saved["offers"][self._offer_index(saved, offer_id)]

    def reject(self, offer_id: str, *, reason: str = "") -> dict[str, Any]:
        """Block an offer from publication."""
        state = self.load()
        offer = self._find_offer(state, offer_id)
        if offer.get("status") == "published":
            return self.save(state)["offers"][self._offer_index(state, offer_id)]
        offer["approval_status"] = "rejected"
        offer["status"] = "blocked"
        offer["decision_reason"] = reason
        offer["updated_at"] = _now()
        saved = self.save(state)
        return saved["offers"][self._offer_index(saved, offer_id)]

    def publish(self, offer_id: str, *, chat_id: str | None = None) -> dict[str, Any]:
        """Publish an approved offer through the Telegram adapter in MOCK mode."""
        state = self.load()
        offer = self._find_offer(state, offer_id)
        if offer.get("approval_status") != "approved":
            raise ValueError("Aprove a oferta antes de publicar.")
        if offer.get("telegram_status") in _PUBLISHED_TELEGRAM_STATUSES:
            return self.save(state)["offers"][self._offer_index(state, offer_id)]

        message = str(offer.get("message_body", "")).strip()
        if not message:
            raise ValueError("A oferta nao tem mensagem Telegram para publicar.")

        target_chat_id = chat_id or str(offer.get("telegram_chat_id") or self.default_chat_id)
        adapter = TelegramAdapter()
        adapter.configure({"bot_token": self.telegram_token})
        adapter.authenticate()
        adapter.mark_ready()
        result = adapter.execute(
            ToolRequest(
                tool_id=uuid4(),
                capability="social_media",
                params={
                    "action": "send_message",
                    "chat_id": target_chat_id,
                    "text": message,
                    "approved": True,
                    "disable_web_page_preview": True,
                },
                metadata={
                    "source": "affiliate_dashboard_server",
                    "offer_id": offer_id,
                },
            )
        )
        offer["telegram_status"] = str(result.output.get("status", "failed"))
        offer["telegram_message_id"] = int(result.output.get("message_id", 0) or 0)
        offer["telegram_chat_id"] = target_chat_id
        offer["publishing_status"] = "published" if result.success else "failed"
        offer["status"] = "published" if result.success else "approved"
        offer["telegram_error"] = result.error
        offer["updated_at"] = _now()
        saved = self.save(state)
        return saved["offers"][self._offer_index(saved, offer_id)]

    def _empty_state(self) -> dict[str, Any]:
        return {
            "title": "Affiliate Approval Dashboard",
            "generated_at": _now(),
            "mode": "server",
            "summary": {"total": 0, "pending": 0, "approved": 0, "published": 0, "blocked": 0},
            "offers": [],
        }

    def _manual_offer(self, payload: dict[str, Any], *, title: str, affiliate_url: str) -> dict[str, Any]:
        marketplace = str(payload.get("marketplace") or "manual").strip() or "manual"
        product_url = str(payload.get("product_url") or "").strip()
        image_url = str(payload.get("image_url") or "").strip()
        coupon = str(payload.get("coupon_code") or "").strip()
        notes = str(payload.get("notes") or "").strip()
        current_price = _float_or_zero(payload.get("current_price"))
        old_price = _float_or_zero(payload.get("old_price"))
        discount = _discount_percent(old_price, current_price)
        deal_score = min(95.0, 55.0 + (discount * 0.9) + (12.0 if coupon else 0.0) + (8.0 if image_url else 0.0))
        message = self._manual_message(
            title=title,
            current_price=current_price,
            old_price=old_price,
            coupon=coupon,
            affiliate_url=affiliate_url,
        )
        return {
            "id": str(uuid4()),
            "title": title,
            "marketplace": marketplace,
            "category": str(payload.get("category") or "manual").strip() or "manual",
            "product_url": product_url,
            "affiliate_url": affiliate_url,
            "image_url": image_url,
            "product_research_score": round(deal_score, 1),
            "creative_action": "manual_review",
            "creative_score": 70.0 if image_url else 45.0,
            "deal_score": round(deal_score, 1),
            "recommendation": "manual_review",
            "approval_status": "pending",
            "telegram_status": "",
            "publishing_status": "pending_approval",
            "status": "pending",
            "message_body": message,
            "notes": notes,
            "created_at": _now(),
            "steps": (
                {"department": "Manual Intake", "success": True, "summary": "Owner entered product offer."},
                {"department": "Product Research", "success": True, "summary": "Basic price and affiliate data captured."},
                {"department": "Creative Review", "success": bool(image_url), "summary": "Image provided." if image_url else "Image missing; review before publishing."},
                {"department": "Affiliate Deals", "success": True, "summary": "Draft Telegram message generated."},
            ),
        }

    def _manual_message(
        self,
        *,
        title: str,
        current_price: float,
        old_price: float,
        coupon: str,
        affiliate_url: str,
    ) -> str:
        lines = [title, ""]
        if current_price > 0 and old_price > current_price:
            lines.append(f"DE R${old_price:.2f} | POR R${current_price:.2f}")
        elif current_price > 0:
            lines.append(f"POR R${current_price:.2f}")
        if coupon:
            lines.append(f"Cupom: {coupon}")
        lines.extend(["", f"Link: {affiliate_url}", "", "Alguns links podem ser afiliados."])
        return "\n".join(lines)

    def _normalize_state(self, state: dict[str, Any]) -> dict[str, Any]:
        normalized = dict(state)
        offers = [dict(offer) for offer in normalized.get("offers", []) if isinstance(offer, dict)]
        for offer in offers:
            offer.setdefault("id", str(uuid4()))
            offer.setdefault("title", "Oferta sem titulo")
            offer.setdefault("approval_status", "pending")
            offer.setdefault("telegram_status", "")
            offer.setdefault("publishing_status", "")
            offer["status"] = self._queue_status(offer)
        normalized["title"] = str(normalized.get("title") or "Affiliate Approval Dashboard")
        normalized["generated_at"] = str(normalized.get("generated_at") or _now())
        normalized["mode"] = "server"
        normalized["offers"] = offers
        normalized["summary"] = self._summary(offers)
        return normalized

    def _queue_status(self, offer: dict[str, Any]) -> str:
        if offer.get("telegram_status") in _PUBLISHED_TELEGRAM_STATUSES:
            return "published"
        if offer.get("status") == "blocked" or offer.get("approval_status") in {"rejected", "declined"}:
            return "blocked"
        if offer.get("approval_status") == "approved":
            return "approved"
        return "pending"

    def _summary(self, offers: list[dict[str, Any]]) -> dict[str, int]:
        return {
            "total": len(offers),
            "pending": sum(1 for offer in offers if offer.get("approval_status") == "pending"),
            "approved": sum(1 for offer in offers if offer.get("approval_status") == "approved"),
            "published": sum(1 for offer in offers if offer.get("telegram_status") in _PUBLISHED_TELEGRAM_STATUSES),
            "blocked": sum(1 for offer in offers if offer.get("status") == "blocked"),
        }

    def _find_offer(self, state: dict[str, Any], offer_id: str) -> dict[str, Any]:
        for offer in state.get("offers", []):
            if str(offer.get("id", "")) == offer_id:
                return offer
        raise KeyError(f"Offer not found: {offer_id}")

    def _offer_index(self, state: dict[str, Any], offer_id: str) -> int:
        for index, offer in enumerate(state.get("offers", [])):
            if str(offer.get("id", "")) == offer_id:
                return index
        raise KeyError(f"Offer not found: {offer_id}")


def create_affiliate_dashboard_server(
    store: AffiliateDashboardStore,
    *,
    host: str = "127.0.0.1",
    port: int = 8787,
) -> ThreadingHTTPServer:
    """Create a local HTTP server for the affiliate approval dashboard."""

    class Handler(BaseHTTPRequestHandler):
        def do_GET(self) -> None:  # noqa: N802 - BaseHTTPRequestHandler API
            parsed = urlparse(self.path)
            if parsed.path == "/":
                html = AffiliateApprovalDashboardRenderer.render_html(store.state())
                self._send_text(html, "text/html; charset=utf-8")
                return
            if parsed.path == "/api/state":
                self._send_json({"ok": True, "state": store.state()})
                return
            self._send_json({"ok": False, "error": "Not found"}, HTTPStatus.NOT_FOUND)

        def do_POST(self) -> None:  # noqa: N802 - BaseHTTPRequestHandler API
            parsed = urlparse(self.path)
            parts = [unquote(part) for part in parsed.path.strip("/").split("/") if part]
            if len(parts) == 2 and parts[0] == "api" and parts[1] == "offers":
                self._handle_create_offer()
                return
            if len(parts) == 4 and parts[0] == "api" and parts[1] == "offers":
                self._handle_offer_action(parts[2], parts[3])
                return
            self._send_json({"ok": False, "error": "Not found"}, HTTPStatus.NOT_FOUND)

        def log_message(self, _format: str, *args: object) -> None:
            return

        def _handle_create_offer(self) -> None:
            try:
                offer = store.create_manual_offer(self._read_json())
            except ValueError as exc:
                self._send_json({"ok": False, "error": str(exc)}, HTTPStatus.BAD_REQUEST)
                return
            self._send_json({
                "ok": True,
                "offer": offer,
                "summary": store.state()["summary"],
                "message": "Oferta manual criada na fila.",
            }, HTTPStatus.CREATED)

        def _handle_offer_action(self, offer_id: str, action: str) -> None:
            try:
                body = self._read_json()
                if action == "approve":
                    offer = store.approve(
                        offer_id,
                        decided_by=str(body.get("decided_by") or "owner"),
                        reason=str(body.get("reason") or ""),
                    )
                    message = "Oferta aprovada no servidor local."
                elif action == "reject":
                    offer = store.reject(offer_id, reason=str(body.get("reason") or ""))
                    message = "Oferta rejeitada no servidor local."
                elif action == "publish":
                    offer = store.publish(offer_id, chat_id=body.get("chat_id"))
                    message = "Publicacao enviada pelo TelegramAdapter em modo seguro."
                else:
                    self._send_json({"ok": False, "error": "Unknown action"}, HTTPStatus.NOT_FOUND)
                    return
            except (KeyError, ValueError) as exc:
                self._send_json({"ok": False, "error": str(exc)}, HTTPStatus.BAD_REQUEST)
                return
            self._send_json({"ok": True, "offer": offer, "summary": store.state()["summary"], "message": message})

        def _read_json(self) -> dict[str, Any]:
            length = int(self.headers.get("Content-Length", "0") or "0")
            if length <= 0:
                return {}
            raw = self.rfile.read(length)
            if not raw:
                return {}
            data = json.loads(raw.decode("utf-8"))
            return data if isinstance(data, dict) else {}

        def _send_text(self, text: str, content_type: str, status: HTTPStatus = HTTPStatus.OK) -> None:
            payload = text.encode("utf-8")
            self.send_response(int(status))
            self.send_header("Content-Type", content_type)
            self.send_header("Content-Length", str(len(payload)))
            self.end_headers()
            self.wfile.write(payload)

        def _send_json(self, body: dict[str, Any], status: HTTPStatus = HTTPStatus.OK) -> None:
            payload = json.dumps(body, ensure_ascii=False).encode("utf-8")
            self.send_response(int(status))
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(payload)))
            self.end_headers()
            self.wfile.write(payload)

    return ThreadingHTTPServer((host, port), Handler)


def demo_dashboard_state() -> dict[str, Any]:
    """Return a small server-mode queue for local manual testing."""
    return {
        "title": "Affiliate Approval Dashboard",
        "generated_at": _now(),
        "mode": "server",
        "offers": [
            {
                "id": "demo-dualsense",
                "title": "PlayStation DualSense Controle sem fio - Gray Camouflage",
                "marketplace": "Amazon",
                "category": "games",
                "product_research_score": 88.5,
                "creative_action": "use_as_is",
                "creative_score": 92.0,
                "deal_score": 91.0,
                "recommendation": "post_now",
                "approval_status": "pending",
                "telegram_status": "",
                "publishing_status": "pending_approval",
                "status": "pending",
                "message_body": (
                    "BONITUDO HEIN?!\n\n"
                    "PlayStation DualSense Controle sem fio - Gray Camouflage\n\n"
                    "DE R$499,90 | POR R$327,22 no Pix\n"
                    "Cupom: TUDOPRIME\n\n"
                    "Link: https://amzn.example/seu-link-afiliado\n\n"
                    "Alguns links podem ser afiliados."
                ),
                "steps": (
                    {"department": "Strategy Intelligence", "success": True, "summary": "Patterns extracted."},
                    {"department": "Product Research", "success": True, "summary": "Strong offer shortlisted."},
                    {"department": "Creative Review", "success": True, "summary": "Creative can be used as is."},
                    {"department": "Affiliate Deals", "success": True, "summary": "Telegram copy prepared."},
                ),
            },
            {
                "id": "demo-monitor",
                "title": "Monitor gamer 24 polegadas 144Hz",
                "marketplace": "Amazon",
                "category": "pc_gamer",
                "product_research_score": 74.0,
                "creative_action": "needs_improvement",
                "creative_score": 58.0,
                "deal_score": 70.0,
                "recommendation": "review_first",
                "approval_status": "pending",
                "telegram_status": "",
                "publishing_status": "pending_approval",
                "status": "pending",
                "message_body": "Monitor gamer 24 polegadas 144Hz\n\nLink: https://amzn.example/monitor-afiliado",
                "steps": (
                    {"department": "Strategy Intelligence", "success": True, "summary": "Audience fit found."},
                    {"department": "Product Research", "success": True, "summary": "Offer may work."},
                    {"department": "Creative Review", "success": True, "summary": "Image should be improved."},
                    {"department": "Affiliate Deals", "success": True, "summary": "Copy prepared but not ideal."},
                ),
            },
        ],
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the local affiliate approval dashboard server.")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8787)
    parser.add_argument("--store", default=str(DEFAULT_DASHBOARD_STORE))
    parser.add_argument("--seed-demo", action="store_true", help="Seed demo offers before starting the server.")
    args = parser.parse_args()

    store = AffiliateDashboardStore(args.store)
    if args.seed_demo or not store.path.exists():
        store.seed(demo_dashboard_state())
    server = create_affiliate_dashboard_server(store, host=args.host, port=args.port)
    print(f"Affiliate dashboard server: http://{args.host}:{server.server_address[1]}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _float_or_zero(value: Any) -> float:
    try:
        return float(str(value).replace(",", "."))
    except (TypeError, ValueError):
        return 0.0


def _discount_percent(old_price: float, current_price: float) -> float:
    if old_price <= 0 or current_price <= 0 or current_price >= old_price:
        return 0.0
    return ((old_price - current_price) / old_price) * 100.0


if __name__ == "__main__":
    main()
