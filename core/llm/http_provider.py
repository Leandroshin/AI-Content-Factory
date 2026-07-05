"""Reusable HTTP transport layer for LLM providers.

HTTPProviderAdapter is the abstract bridge between LLMRequest
and any REST-based LLM provider. Subclasses implement only
provider-specific serialisation and parsing.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any
from uuid import UUID

from .models import LLMRequest, LLMResponse
from .providers import ProviderAdapter


class HTTPClient(ABC):
    """Injectable HTTP client contract.

    Default implementation uses urllib.request (stdlib).
    Replace with a fake for tests or a more robust client later.
    """

    @abstractmethod
    def post(self, url: str, headers: dict[str, str], json_data: dict[str, Any]) -> dict[str, Any]:
        """Perform an HTTP POST and return the parsed JSON response."""


class DefaultHTTPClient(HTTPClient):
    """Default HTTP client backed by urllib.request."""

    def post(self, url: str, headers: dict[str, str], json_data: dict[str, Any]) -> dict[str, Any]:
        import json
        import urllib.request

        body = json.dumps(json_data).encode("utf-8")
        req = urllib.request.Request(url, data=body, headers=headers, method="POST")

        with urllib.request.urlopen(req) as resp:
            return json.loads(resp.read().decode("utf-8"))


class HTTPProviderAdapter(ProviderAdapter, ABC):
    """Abstract base for REST-based LLM providers.

    Subclasses implement four methods:
      - build_payload()   → provider-specific request JSON
      - build_headers()   → provider-specific HTTP headers
      - parse_response()  → provider-specific JSON → LLMResponse
      - endpoint()        → provider-specific URL

    The HTTP client is injectable for testing (see DefaultHTTPClient).
    """

    def __init__(self, api_key: str, http_client: HTTPClient | None = None) -> None:
        if not api_key or not api_key.strip():
            raise ValueError(
                f"{type(self).__name__}: a valid API key is required. "
                "Provide one via the constructor."
            )
        self._api_key = api_key
        self._http_client = http_client or DefaultHTTPClient()

    def generate(self, request: LLMRequest) -> LLMResponse:
        """Execute the full HTTP request pipeline."""
        payload = self.build_payload(request)
        headers = self.build_headers()
        url = self.endpoint()

        json_response = self._http_client.post(url, headers, payload)

        return self.parse_response(request.request_id, json_response)

    @abstractmethod
    def build_payload(self, request: LLMRequest) -> dict[str, Any]:
        """Translate an LLMRequest into the provider-specific JSON body."""

    @abstractmethod
    def build_headers(self) -> dict[str, str]:
        """Return HTTP headers for the provider API call."""

    @abstractmethod
    def parse_response(self, request_id: UUID, json_data: dict[str, Any]) -> LLMResponse:
        """Parse the provider JSON response into a standard LLMResponse."""

    @abstractmethod
    def endpoint(self) -> str:
        """Return the provider API endpoint URL."""
