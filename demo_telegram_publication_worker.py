"""Demonstrate the approved dashboard-to-Telegram publication bridge."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

from core.content_factory.telegram_publication_worker import TelegramPublicationWorker
from core.tools import (
    ExecutionMode,
    MockSecretProvider,
    ProviderControlCenter,
    TelegramAdapter,
    TelegramProvider,
)
from core.tools.http import HttpClient, HttpMethod, HttpRequest, HttpResponse


_ASSERTIONS = 0
_ENDPOINT = "https://central-ai-content-factory.leandro-az-v.chatgpt.site/api/intake/telegram-publications"
_CHAT_ID = "@achadosbaratosBrasil"
_TEXT = "🔥 Produto de teste\n\n💰 Por R$ 69,90\n\n🔗 Mercado Livre: https://meli.la/teste\n\nPreço e estoque podem mudar.\n\n#publi"
_IMAGE = "https://http2.mlstatic.com/product-test.jpg"


def _check(condition: bool, label: str) -> None:
    global _ASSERTIONS
    _ASSERTIONS += 1
    print(f"  [{'PASS' if condition else 'FAIL'}] {_ASSERTIONS:>2}. {label}")
    if not condition:
        raise AssertionError(label)


class RoutingHttpClient(HttpClient):
    """Return deterministic queue, Telegram and callback responses."""

    def __init__(self, *, chat_id: str = _CHAT_ID) -> None:
        super().__init__()
        self.requests: list[HttpRequest] = []
        self.chat_id = chat_id

    def send(self, request: HttpRequest) -> HttpResponse:
        self.requests.append(request)
        if request.url == _ENDPOINT and request.method == HttpMethod.GET:
            return HttpResponse(status_code=200, body={"items": [{
                "id": "telegram-request-1",
                "productId": "product-1",
                "chatId": self.chat_id,
                "messageText": _TEXT,
                "affiliateUrl": "https://meli.la/teste",
                "imageUrl": _IMAGE,
                "linkPreviewEnabled": True,
                "ownerApproved": True,
                "approvedAt": datetime.now(timezone.utc).isoformat(),
                "authorizationKind": "manual",
                "policyId": "",
                "policyVersion": 0,
                "leaseToken": "lease-token-telegram-worker",
                "leaseExpiresAt": (datetime.now(timezone.utc) + timedelta(minutes=5)).isoformat(),
            }]})
        if request.url == _ENDPOINT and request.method == HttpMethod.POST:
            return HttpResponse(status_code=202, body={"accepted": True})
        if "api.telegram.org" in request.url and request.url.endswith("/sendPhoto"):
            return HttpResponse(status_code=200, body={
                "ok": True,
                "result": {"message_id": 778, "chat": {"id": self.chat_id}},
            })
        if "api.telegram.org" in request.url and request.url.endswith("/sendMessage"):
            return HttpResponse(status_code=200, body={
                "ok": True,
                "result": {"message_id": 779, "chat": {"id": self.chat_id}},
            })
        return HttpResponse(status_code=404, body={"ok": False})


def _adapter(client: HttpClient) -> TelegramAdapter:
    secrets = MockSecretProvider()
    center = ProviderControlCenter(secret_provider=secrets)
    center.register_telegram(max_messages=1, max_requests=2)
    center.set_secret("telegram", "bot_token", "test_bot_token_telegram_worker")
    center.set_execution_mode("telegram", ExecutionMode.REAL)
    center.approve_provider("telegram", True)

    adapter = TelegramAdapter()
    adapter.configure({"bot_token": "configured_via_secret_provider"})
    adapter.set_provider(TelegramProvider())
    adapter.set_http_client(client)
    center.apply_to_telegram(adapter)
    adapter.authenticate()
    adapter.mark_ready()
    return adapter


def main() -> None:
    print("=" * 72)
    print("Telegram Publication Worker - Owner Approval and Single Send")
    print("=" * 72)

    client = RoutingHttpClient()
    worker = TelegramPublicationWorker(client, _ENDPOINT)
    disabled = worker.run_once(_adapter(client), token="queue-token", enabled=False)
    _check(disabled.skipped_reason == "worker_disabled", "Worker is opt-in")
    _check(len(client.requests) == 0, "Disabled worker performs no HTTP request")

    result = worker.run_once(
        _adapter(client),
        token="queue-token",
        enabled=True,
        site_access_token="private-site-token",
    )
    _check(result.received == 1, "One approved publication is claimed")
    _check(result.sent == 1 and result.failed == 0, "Approved publication is sent once")
    _check(result.message_ids == (778,), "Telegram message_id is preserved")
    _check(len(client.requests) == 3, "Flow performs claim, send and callback")
    _check(client.requests[0].method == HttpMethod.GET, "First request claims the queue item")
    send_request = client.requests[1]
    _check(send_request.url.endswith("/sendPhoto"), "Second request uses Telegram sendPhoto")
    _check(send_request.body["chat_id"] == _CHAT_ID, "Only the allowlisted channel is targeted")
    _check(send_request.body["caption"] == _TEXT, "Exact owner-reviewed caption is preserved")
    _check(send_request.body["photo"] == _IMAGE, "Reviewed product image is preserved")
    _check("#publi" in send_request.body["caption"], "Compact affiliate disclosure is present")
    callback = client.requests[2]
    _check(callback.body["status"] == "sent", "Dashboard receives sent status")
    _check(callback.body["leaseToken"] == "lease-token-telegram-worker", "Callback returns the atomic lease token")
    _check(callback.body["messageId"] == 778, "Dashboard receives the Telegram message_id")
    _check(callback.headers["Authorization"] == "Bearer queue-token", "Queue callback is authenticated")
    _check("OAI-Sites-Authorization" in callback.headers, "Private Sites authorization is included")

    blocked_client = RoutingHttpClient(chat_id="@canal_nao_autorizado")
    blocked = TelegramPublicationWorker(blocked_client, _ENDPOINT).run_once(
        _adapter(blocked_client),
        token="queue-token",
        enabled=True,
    )
    _check(blocked.received == 1 and blocked.failed == 1, "Unknown destination is rejected")
    _check(len(blocked_client.requests) == 2, "Rejected destination never reaches Telegram")
    _check(all("api.telegram.org" not in request.url for request in blocked_client.requests), "Destination block happens before Telegram HTTP")
    _check(blocked_client.requests[-1].body["error"] == "telegram_destination_not_allowlisted", "Failure reason returns to the dashboard")

    stale_client = RoutingHttpClient()
    original_send = stale_client.send

    def stale_send(request: HttpRequest) -> HttpResponse:
        response = original_send(request)
        if request.url == _ENDPOINT and request.method == HttpMethod.GET and isinstance(response.body, dict):
            response.body["items"][0]["approvedAt"] = (
                datetime.now(timezone.utc) - timedelta(hours=3)
            ).isoformat()
        return response

    stale_client.send = stale_send  # type: ignore[method-assign]
    stale = TelegramPublicationWorker(stale_client, _ENDPOINT).run_once(
        _adapter(stale_client), token="queue-token", enabled=True,
    )
    _check(stale.received == 1 and stale.failed == 1, "Expired offer is rejected before Telegram")
    _check(all("api.telegram.org" not in request.url for request in stale_client.requests), "Expired price never reaches Telegram")
    _check(stale_client.requests[-1].body["error"] == "telegram_offer_expired", "Expiration reason returns to the dashboard")

    pending_client = RoutingHttpClient()
    original_pending_send = pending_client.send

    def pending_send(request: HttpRequest) -> HttpResponse:
        response = original_pending_send(request)
        if request.url == _ENDPOINT and request.method == HttpMethod.GET and isinstance(response.body, dict):
            response.body["items"][0]["ownerApproved"] = False
        return response

    pending_client.send = pending_send  # type: ignore[method-assign]
    pending = TelegramPublicationWorker(pending_client, _ENDPOINT).run_once(
        _adapter(pending_client), token="queue-token", enabled=True,
    )
    _check(pending.received == 1 and pending.failed == 1, "Missing human approval is rejected")
    _check(all("api.telegram.org" not in request.url for request in pending_client.requests), "Pending candidate never reaches Telegram")
    _check(pending_client.requests[-1].body["error"] == "owner_approval_missing", "Approval failure is auditable")

    editorial_client = RoutingHttpClient()
    original_editorial_send = editorial_client.send

    def editorial_send(request: HttpRequest) -> HttpResponse:
        response = original_editorial_send(request)
        if request.url == _ENDPOINT and request.method == HttpMethod.GET and isinstance(response.body, dict):
            item = response.body["items"][0]
            item["messageText"] = "Bem-vindo ao canal Achados Baratos Brasil. Acompanhe as próximas seleções."
            item["affiliateUrl"] = ""
            item["imageUrl"] = ""
        return response

    editorial_client.send = editorial_send  # type: ignore[method-assign]
    editorial = TelegramPublicationWorker(editorial_client, _ENDPOINT).run_once(
        _adapter(editorial_client), token="queue-token", enabled=True,
    )
    _check(editorial.sent == 1, "Approved non-affiliate editorial message does not require #publi")

    print(f"\nTelegram publication worker demo passed: {_ASSERTIONS}/{_ASSERTIONS} assertions")


if __name__ == "__main__":
    main()
