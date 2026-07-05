"""Telegram handoff for human approval requests."""

from __future__ import annotations

from uuid import UUID, uuid4

from core.approval.models import ApprovalRequest, ApprovalStatus
from core.approval.runtime import ApprovalRuntime
from core.tools.adapters.models import AdapterExecutionResult, ToolRequest
from core.tools.adapters.telegram_adapter import TelegramAdapter


_MAX_TELEGRAM_TEXT = 4096
_APPROVAL_PREVIEW_LIMIT = 2800


class TelegramApprovalGateway:
    """Sends approval prompts and publishes payloads after approval."""

    def __init__(
        self,
        approval_runtime: ApprovalRuntime,
        telegram_adapter: TelegramAdapter,
        *,
        owner_chat_id: str,
    ) -> None:
        if not owner_chat_id.strip():
            raise ValueError("owner_chat_id is required.")
        self._approval_runtime = approval_runtime
        self._telegram_adapter = telegram_adapter
        self._owner_chat_id = owner_chat_id

    @property
    def owner_chat_id(self) -> str:
        return self._owner_chat_id

    def send_approval_request(self, request: ApprovalRequest) -> AdapterExecutionResult:
        """Notify the owner that an approval item is waiting.

        approved=True here authorizes the control notification itself. It does
        not approve the underlying publication payload.
        """
        return self._telegram_adapter.execute(ToolRequest(
            tool_id=uuid4(),
            capability="social_media",
            params={
                "action": "send_message",
                "chat_id": self._owner_chat_id,
                "text": self.format_approval_message(request),
                "approved": True,
                "disable_web_page_preview": True,
                "protect_content": True,
            },
            metadata={
                "purpose": "approval_request",
                "approval_id": str(request.approval_id),
            },
        ))

    def publish_if_approved(
        self,
        approval_id: UUID,
        *,
        chat_id: str | None = None,
        text_key: str = "telegram_text",
    ) -> AdapterExecutionResult:
        request = self._approval_runtime.require(approval_id)
        if request.status != ApprovalStatus.APPROVED:
            return AdapterExecutionResult(
                success=False,
                summary=f"Publication blocked: approval is {request.status.value}.",
                output={
                    "approval_id": str(approval_id),
                    "approval_status": request.status.value,
                    "channel": "telegram",
                    "_blocked_by_approval_runtime": True,
                },
                error="Publication requires an approved ApprovalRequest.",
            )

        payload = self._approval_runtime.release_payload(approval_id)
        text = str(payload.get(text_key) or payload.get("text") or request.preview_text)
        destination = str(chat_id or payload.get("chat_id") or self._owner_chat_id)
        return self._telegram_adapter.execute(ToolRequest(
            tool_id=uuid4(),
            capability="social_media",
            params={
                "action": "send_message",
                "chat_id": destination,
                "text": text,
                "approved": True,
                "disable_web_page_preview": True,
            },
            metadata={
                "purpose": "approved_publication",
                "approval_id": str(approval_id),
            },
        ))

    @staticmethod
    def format_approval_message(request: ApprovalRequest) -> str:
        preview = _trim(request.preview_text, _APPROVAL_PREVIEW_LIMIT)
        message = (
            "AI Content Factory approval request\n"
            f"ID: {request.approval_id}\n"
            f"Title: {request.title}\n"
            f"Source: {request.source}\n"
            f"Requester: {request.requester}\n"
            f"Risk: {request.risk_level}\n\n"
            "Preview:\n"
            f"{preview}\n\n"
            f"Approve: approve {request.approval_id}\n"
            f"Reject: reject {request.approval_id} <reason>"
        )
        return _trim(message, _MAX_TELEGRAM_TEXT)


def _trim(value: str, limit: int) -> str:
    if len(value) <= limit:
        return value
    suffix = "\n...[trimmed for Telegram]"
    return value[: max(0, limit - len(suffix))].rstrip() + suffix
