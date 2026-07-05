"""OpenAI adapter — Responses API (latest).

Implements the provider-specific serialisation and parsing
for OpenAI's Responses endpoint. No streaming, no function
calling, no tools — text only.
"""

from __future__ import annotations

from typing import Any
from uuid import UUID

from .http_provider import HTTPClient, HTTPProviderAdapter
from .models import LLMRequest, LLMResponse


class OpenAIAdapter(HTTPProviderAdapter):
    """OpenAI Responses API adapter.

    Translates LLMRequest → OpenAI Responses JSON → LLMResponse.

    Usage:
        adapter = OpenAIAdapter(api_key="example-openai-key")
        adapter = OpenAIAdapter(api_key="example-openai-key", http_client=FakeClient())
    """

    PROVIDER_NAME = "openai"

    def __init__(
        self,
        api_key: str,
        http_client: HTTPClient | None = None,
        base_url: str = "https://api.openai.com/v1/responses",
    ) -> None:
        super().__init__(api_key, http_client)
        self._base_url = base_url.rstrip("/")

    # ------------------------------------------------------------------
    # HTTPProviderAdapter contract
    # ------------------------------------------------------------------

    def endpoint(self) -> str:
        return self._base_url

    def build_headers(self) -> dict[str, str]:
        return {
            "Authorization": f"Bearer {self._api_key}",
            "Content-Type": "application/json",
        }

    def build_payload(self, request: LLMRequest) -> dict[str, Any]:
        """Convert LLMRequest to OpenAI Responses API JSON body."""
        input_messages: list[dict[str, Any]] = []

        if request.system_prompt:
            input_messages.append({
                "role": "system",
                "content": [{"type": "input_text", "text": request.system_prompt}],
            })

        input_messages.append({
            "role": "user",
            "content": [{"type": "input_text", "text": request.prompt}],
        })

        payload: dict[str, Any] = {
            "model": request.model,
            "input": input_messages,
        }

        # Only include non-default values to keep payload clean
        if request.temperature != 0.7:
            payload["temperature"] = request.temperature
        if request.max_tokens != 2048:
            payload["max_output_tokens"] = request.max_tokens

        return payload

    def parse_response(self, request_id: UUID, json_data: dict[str, Any]) -> LLMResponse:
        """Parse OpenAI Responses API JSON into LLMResponse."""
        content = ""
        output_list = json_data.get("output", [])
        for item in output_list:
            if isinstance(item, dict) and item.get("type") == "message":
                content_parts = item.get("content", [])
                for part in content_parts:
                    if isinstance(part, dict) and part.get("type") == "output_text":
                        content += part.get("text", "")

        usage = json_data.get("usage", {})
        input_tokens = usage.get("input_tokens", 0) if isinstance(usage, dict) else 0
        output_tokens = usage.get("output_tokens", 0) if isinstance(usage, dict) else 0
        total_tokens = usage.get("total_tokens", 0) if isinstance(usage, dict) else 0

        finish_reason = "stop"

        # Extract model from response, fall back to request default
        model = json_data.get("model", "gpt-4o")

        return LLMResponse(
            request_id=request_id,
            provider=self.PROVIDER_NAME,
            model=model,
            content=content,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            total_tokens=total_tokens,
            finish_reason=finish_reason,
            metadata={"raw_response_id": json_data.get("id", "")},
        )
