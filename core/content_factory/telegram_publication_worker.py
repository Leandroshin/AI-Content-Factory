"""Publish owner-approved dashboard messages through the Telegram adapter."""

from __future__ import annotations

from dataclasses import dataclass, field
import ipaddress
from typing import Any
from urllib.parse import urlparse
from uuid import uuid4

from core.tools.adapters.models import ToolRequest
from core.tools.adapters.telegram_adapter import TelegramAdapter
from core.tools.http.client import HttpClient
from core.tools.http.errors import HttpError


@dataclass(frozen=True, slots=True)
class TelegramPublicationWorkItem:
    request_id: str
    product_id: str
    chat_id: str
    message_text: str
    image_url: str = ""
    link_preview_enabled: bool = True
    owner_approved: bool = False


@dataclass(frozen=True, slots=True)
class TelegramPublicationWorkResult:
    skipped_reason: str = ""
    received: int = 0
    sent: int = 0
    failed: int = 0
    request_ids: tuple[str, ...] = field(default_factory=tuple)
    message_ids: tuple[int, ...] = field(default_factory=tuple)


class TelegramPublicationWorker:
    """Consume one explicitly approved publication and report its outcome."""

    def __init__(
        self,
        client: HttpClient,
        endpoint: str,
        *,
        allowed_chat_ids: tuple[str, ...] = ("@achadosbaratosBrasil",),
    ) -> None:
        endpoint = endpoint.strip()
        if not endpoint.startswith("https://") or not endpoint.endswith(
            "/api/intake/telegram-publications"
        ):
            raise ValueError("Telegram worker endpoint must be the public HTTPS intake route.")
        normalized = tuple(item.strip() for item in allowed_chat_ids if item.strip())
        if not normalized:
            raise ValueError("At least one Telegram destination must be allowlisted.")
        self._client = client
        self._endpoint = endpoint
        self._allowed_chat_ids = frozenset(normalized)

    def run_once(
        self,
        adapter: TelegramAdapter,
        *,
        token: str,
        enabled: bool = False,
        site_access_token: str = "",
    ) -> TelegramPublicationWorkResult:
        if not enabled:
            return TelegramPublicationWorkResult(skipped_reason="worker_disabled")
        if not token.strip():
            return TelegramPublicationWorkResult(skipped_reason="missing_token")
        try:
            response = self._client.get(
                self._endpoint,
                headers=self._headers(token, site_access_token=site_access_token),
            )
        except HttpError:
            return TelegramPublicationWorkResult(skipped_reason="queue_unavailable")
        if response.status_code != 200 or not isinstance(response.body, dict):
            return TelegramPublicationWorkResult(skipped_reason="invalid_queue_response")

        values = response.body.get("items", ())
        item = self._coerce_item(values[0] if isinstance(values, list) and values else None)
        if item is None:
            return TelegramPublicationWorkResult(skipped_reason="queue_empty")

        validation_error = self._validation_error(item)
        if validation_error:
            self._report(
                item.request_id,
                status="failed",
                message_id=None,
                error=validation_error,
                token=token,
                site_access_token=site_access_token,
            )
            return TelegramPublicationWorkResult(
                received=1,
                failed=1,
                request_ids=(item.request_id,),
            )

        use_photo = bool(item.image_url)
        params: dict[str, Any] = {
            "action": "send_photo" if use_photo else "send_message",
            "chat_id": item.chat_id,
            "approved": item.owner_approved,
        }
        if use_photo:
            params.update({"photo": item.image_url, "caption": item.message_text})
        else:
            params.update({
                "text": item.message_text,
                "disable_web_page_preview": not item.link_preview_enabled,
            })
        result = adapter.execute(ToolRequest(
            tool_id=uuid4(),
            capability="social_media",
            params=params,
        ))
        message_id = self._message_id(result.output.get("message_id")) if result.success else None
        status = "sent" if result.success and message_id is not None else "failed"
        error = "" if status == "sent" else (result.error or result.summary or "telegram_send_failed")
        reported = self._report(
            item.request_id,
            status=status,
            message_id=message_id,
            error=error,
            token=token,
            site_access_token=site_access_token,
        )
        if not reported:
            return TelegramPublicationWorkResult(
                skipped_reason="result_callback_failed",
                received=1,
                sent=1 if status == "sent" else 0,
                failed=1 if status == "failed" else 0,
                request_ids=(item.request_id,),
                message_ids=(message_id,) if message_id is not None else (),
            )
        return TelegramPublicationWorkResult(
            received=1,
            sent=1 if status == "sent" else 0,
            failed=1 if status == "failed" else 0,
            request_ids=(item.request_id,),
            message_ids=(message_id,) if message_id is not None else (),
        )

    def _validation_error(self, item: TelegramPublicationWorkItem) -> str:
        if not item.owner_approved:
            return "owner_approval_missing"
        if item.chat_id not in self._allowed_chat_ids:
            return "telegram_destination_not_allowlisted"
        max_length = 1024 if item.image_url else 4096
        if not item.message_text or len(item.message_text) > max_length:
            return "telegram_message_invalid"
        if item.image_url and not self._valid_public_image_url(item.image_url):
            return "telegram_image_invalid"
        if "#publi" not in item.message_text.lower():
            return "affiliate_disclosure_missing"
        return ""

    def _report(
        self,
        request_id: str,
        *,
        status: str,
        message_id: int | None,
        error: str,
        token: str,
        site_access_token: str,
    ) -> bool:
        try:
            response = self._client.post(
                self._endpoint,
                headers=self._headers(
                    token,
                    site_access_token=site_access_token,
                    include_content_type=True,
                ),
                body={
                    "requestId": request_id,
                    "status": status,
                    "messageId": message_id,
                    "error": error[:500],
                },
            )
        except HttpError:
            return False
        return response.status_code == 202

    @staticmethod
    def _headers(
        token: str,
        *,
        site_access_token: str,
        include_content_type: bool = False,
    ) -> dict[str, str]:
        headers = {"Authorization": f"Bearer {token.strip()}"}
        if site_access_token.strip():
            headers["OAI-Sites-Authorization"] = f"Bearer {site_access_token.strip()}"
        if include_content_type:
            headers["Content-Type"] = "application/json"
        return headers

    @staticmethod
    def _coerce_item(value: Any) -> TelegramPublicationWorkItem | None:
        if not isinstance(value, dict):
            return None
        request_id = str(value.get("id", "")).strip()
        product_id = str(value.get("productId", "")).strip()
        chat_id = str(value.get("chatId", "")).strip()
        message_text = str(value.get("messageText", "")).strip()
        image_url = str(value.get("imageUrl", "")).strip()
        if not request_id or not product_id or not chat_id or not message_text:
            return None
        return TelegramPublicationWorkItem(
            request_id=request_id,
            product_id=product_id,
            chat_id=chat_id,
            message_text=message_text,
            image_url=image_url,
            link_preview_enabled=bool(value.get("linkPreviewEnabled", True)),
            owner_approved=bool(value.get("ownerApproved", False)),
        )

    @staticmethod
    def _message_id(value: Any) -> int | None:
        if isinstance(value, bool):
            return None
        if isinstance(value, int) and value > 0:
            return value
        return None

    @staticmethod
    def _valid_public_image_url(value: str) -> bool:
        if not value.startswith("https://") or len(value) > 2048:
            return False
        parsed = urlparse(value)
        if parsed.scheme != "https" or not parsed.hostname or parsed.username or parsed.password:
            return False
        host = parsed.hostname.lower()
        if host == "localhost" or host.endswith(".localhost"):
            return False
        try:
            address = ipaddress.ip_address(host)
        except ValueError:
            return True
        return not (
            address.is_private
            or address.is_loopback
            or address.is_link_local
            or address.is_multicast
            or address.is_reserved
            or address.is_unspecified
        )
