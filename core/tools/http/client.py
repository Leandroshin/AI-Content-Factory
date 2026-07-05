"""HTTP client abstraction with mock implementation.

The base class defines the contract. MockHttpClient returns
predictable responses for testing. RealHttpClient (future)
will wrap requests/httpx.

No real HTTP calls are made by this module.
"""

from __future__ import annotations

import time
from abc import ABC, abstractmethod
from typing import Any

from core.tools.http.errors import (
    AuthExpiredError,
    NetworkUnavailableError,
    QuotaExceededError,
    RateLimitError,
    RetryExhaustedError,
    TimeoutError,
)
from core.tools.http.models import (
    HttpMethod,
    HttpRequest,
    HttpResponse,
    RateLimitConfig,
    RetryPolicy,
    TimeoutPolicy,
)


class HttpClient(ABC):
    """Abstract HTTP client contract.

    Subclasses implement the actual transport layer. All HTTP
    errors are raised as typed exceptions defined in errors.py.
    """

    def __init__(
        self,
        retry_policy: RetryPolicy | None = None,
        timeout_policy: TimeoutPolicy | None = None,
        rate_limit: RateLimitConfig | None = None,
    ) -> None:
        self._retry_policy = retry_policy or RetryPolicy()
        self._timeout_policy = timeout_policy or TimeoutPolicy()
        self._rate_limit = rate_limit

    @abstractmethod
    def send(self, request: HttpRequest) -> HttpResponse:
        """Send a single HTTP request and return the response."""
        ...

    def request(
        self,
        method: HttpMethod,
        url: str,
        headers: dict[str, str] | None = None,
        params: dict[str, str] | None = None,
        body: Any = None,
        timeout: float | None = None,
    ) -> HttpResponse:
        """Convenience: build and send an HttpRequest."""
        return self.send(HttpRequest(
            method=method,
            url=url,
            headers=headers or {},
            params=params or {},
            body=body,
            timeout=timeout or self._timeout_policy.total,
        ))

    def get(self, url: str, **kwargs: Any) -> HttpResponse:
        """Convenience: send a GET request."""
        return self.request(HttpMethod.GET, url, **kwargs)

    def post(self, url: str, **kwargs: Any) -> HttpResponse:
        """Convenience: send a POST request."""
        return self.request(HttpMethod.POST, url, **kwargs)

    def put(self, url: str, **kwargs: Any) -> HttpResponse:
        """Convenience: send a PUT request."""
        return self.request(HttpMethod.PUT, url, **kwargs)

    def patch(self, url: str, **kwargs: Any) -> HttpResponse:
        """Convenience: send a PATCH request."""
        return self.request(HttpMethod.PATCH, url, **kwargs)

    def delete(self, url: str, **kwargs: Any) -> HttpResponse:
        """Convenience: send a DELETE request."""
        return self.request(HttpMethod.DELETE, url, **kwargs)


class MockHttpClient(HttpClient):
    """Mock HTTP client that returns configurable responses.

    No real network calls are made. Useful for testing and
    as the default client in MOCK execution mode.
    """

    def __init__(
        self,
        default_response: HttpResponse | None = None,
        error_map: dict[str, Exception] | None = None,
        **kwargs: Any,
    ) -> None:
        super().__init__(**kwargs)
        self._default_response = default_response or HttpResponse(
            status_code=200,
            headers={"content-type": "application/json"},
            body={"status": "ok", "mock": True},
        )
        self._error_map: dict[str, Exception] = dict(error_map or {})
        self._sent_requests: list[HttpRequest] = []

    def send(self, request: HttpRequest) -> HttpResponse:
        self._sent_requests.append(request)

        for pattern, exc in self._error_map.items():
            if pattern in request.url:
                raise exc

        start = time.time()
        elapsed = (time.time() - start) * 1000.0
        return HttpResponse(
            status_code=self._default_response.status_code,
            headers=dict(self._default_response.headers),
            body=self._default_response.body,
            elapsed_ms=round(elapsed, 2),
        )

    @property
    def sent_requests(self) -> list[HttpRequest]:
        """Return all requests sent through this client."""
        return list(self._sent_requests)

    def last_request(self) -> HttpRequest | None:
        """Return the most recent request, or None."""
        return self._sent_requests[-1] if self._sent_requests else None

    def reset(self) -> None:
        """Clear all recorded requests."""
        self._sent_requests.clear()
