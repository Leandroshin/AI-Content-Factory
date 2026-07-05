"""Real HTTP client implementation using urllib.

Publishes typed events for every request so the ObservabilityProjector
can auto-project HttpSnapshot metrics.

No external dependencies — uses only Python standard library.
"""

from __future__ import annotations

import json
import time
import urllib.error
import urllib.request
from typing import Any
from uuid import uuid4

from core.events.bus import EventBus
from core.tools.http.client import HttpClient
from core.tools.http.errors import (
    AuthExpiredError,
    HttpError,
    NetworkUnavailableError,
    QuotaExceededError,
    RateLimitError,
    RetryExhaustedError,
    TimeoutError,
)
from core.tools.http.events import (
    HttpAuthenticationFailed,
    HttpQuotaExceeded,
    HttpRateLimited,
    HttpRequestCompleted,
    HttpRequestFailed,
    HttpRequestStarted,
    HttpRetry,
)
from core.tools.http.models import (
    HttpMethod,
    HttpRequest,
    HttpResponse,
    RateLimitConfig,
    RetryPolicy,
    TimeoutPolicy,
)
from core.tools.http.rate_limiter import RateLimiter


class RealHttpClient(HttpClient):
    """Production HTTP client backed by urllib.

    Publishes typed events for observability. Supports retry,
    rate limiting, timeout, and error handling via existing contracts.
    """

    def __init__(
        self,
        retry_policy: RetryPolicy | None = None,
        timeout_policy: TimeoutPolicy | None = None,
        rate_limit: RateLimitConfig | None = None,
        event_bus: EventBus | None = None,
    ) -> None:
        super().__init__(retry_policy, timeout_policy, rate_limit)
        self._event_bus = event_bus
        self._rate_limiter = RateLimiter(
            config=rate_limit,
            retry_policy=retry_policy,
        )
        self._total_requests = 0
        self._total_retries = 0
        self._total_failures = 0

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def send(self, request: HttpRequest) -> HttpResponse:
        """Send a single HTTP request with retry and rate limiting."""
        request_id = uuid4()
        self._publish_request_started(request_id, request)

        attempt = 0
        while True:
            attempt += 1
            try:
                return self._do_send(request, request_id, attempt)
            except RetryExhaustedError:
                raise
            except RateLimitError as e:
                delay = e.retry_after or 1.0
                self._publish_rate_limited(request_id, e)
                if attempt < self._retry_policy.max_retries:
                    self._total_retries += 1
                    self._publish_retry(request_id, attempt, 429, delay)
                    time.sleep(delay)
                    continue
                self._publish_failed(request_id, "RateLimitError", str(e))
                self._total_failures += 1
                raise
            except AuthExpiredError as e:
                self._publish_auth_failed(request_id, e)
                self._total_failures += 1
                raise
            except QuotaExceededError as e:
                self._publish_quota_exceeded(request_id, e)
                self._total_failures += 1
                raise
            except (TimeoutError, NetworkUnavailableError):
                self._total_failures += 1
                raise
            except HttpError as e:
                self._publish_failed(request_id, type(e).__name__, str(e))
                self._total_failures += 1
                if attempt < self._retry_policy.max_retries:
                    delay = self._rate_limiter.retry_delay(attempt, 0)
                    self._total_retries += 1
                    self._publish_retry(request_id, attempt, 0, delay)
                    time.sleep(delay)
                    continue
                raise

    # ------------------------------------------------------------------
    # Internals
    # ------------------------------------------------------------------

    def _do_send(
        self, request: HttpRequest, request_id: Any, attempt: int
    ) -> HttpResponse:
        self._rate_limiter.acquire()
        start = time.time()

        try:
            req = self._build_urllib_request(request)
            with urllib.request.urlopen(
                req,
                timeout=request.timeout or self._timeout_policy.total,
            ) as response:
                elapsed = (time.time() - start) * 1000.0
                body = self._parse_body(response)
                result = HttpResponse(
                    status_code=response.status,
                    headers=dict(response.headers),
                    body=body,
                    elapsed_ms=round(elapsed, 2),
                )
                self._publish_completed(request_id, result)
                self._total_requests += 1
                return result

        except urllib.error.HTTPError as e:
            elapsed = (time.time() - start) * 1000.0
            status = e.code
            body = self._try_decode(e.read())

            if status == 401:
                raise AuthExpiredError(url=request.url, reason=str(e))
            if status == 403:
                body_str = str(body).lower()
                if "quota" in body_str or "rate" in body_str:
                    raise QuotaExceededError(url=request.url, limit=0)
                raise AuthExpiredError(url=request.url, reason=str(e))
            if status == 429:
                retry_after = float(e.headers.get("Retry-After", 1))
                raise RateLimitError(
                    url=request.url,
                    retry_after=retry_after,
                )

            # Retryable server errors
            if status in self._retry_policy.retryable_statuses:
                if attempt >= self._retry_policy.max_retries:
                    raise RetryExhaustedError(
                        url=request.url,
                        attempts=attempt,
                        last_status=status,
                        last_error=str(e),
                    )
                delay = self._rate_limiter.retry_delay(attempt, status)
                self._total_retries += 1
                self._publish_retry(request_id, attempt, status, delay)
                time.sleep(delay)
                return self._do_send(request, request_id, attempt + 1)

            raise HttpError(f"HTTP {status}: {e}")

        except urllib.error.URLError as e:
            raise NetworkUnavailableError(
                url=request.url,
                reason=str(e.reason),
            )

    def _build_urllib_request(self, request: HttpRequest) -> urllib.request.Request:
        url = request.url
        if request.params:
            from urllib.parse import urlencode
            sep = "&" if "?" in url else "?"
            url = f"{url}{sep}{urlencode(request.params)}"

        data = None
        if request.body is not None:
            if isinstance(request.body, dict):
                data = json.dumps(request.body).encode("utf-8")
            elif isinstance(request.body, str):
                data = request.body.encode("utf-8")
            else:
                data = request.body

        req = urllib.request.Request(
            url,
            data=data,
            headers=dict(request.headers),
            method=request.method.value,
        )
        return req

    def _parse_body(self, response: urllib.request.AddInfoHandler) -> Any:
        raw = response.read()
        return self._try_decode(raw)

    def _try_decode(self, raw: bytes) -> Any:
        try:
            text = raw.decode("utf-8")
        except Exception:
            return raw
        try:
            return json.loads(text)
        except Exception:
            return text

    # ------------------------------------------------------------------
    # Event publishing
    # ------------------------------------------------------------------

    def _publish(self, event: Any) -> None:
        if self._event_bus is not None:
            self._event_bus.publish(event)

    def _publish_request_started(self, rid: Any, req: HttpRequest) -> None:
        self._publish(HttpRequestStarted(
            request_id=rid if isinstance(rid, uuid4.__class__) else uuid4(),
            method=req.method.value,
            url=req.url,
            timestamp=time.time(),
        ))

    def _publish_completed(self, rid: Any, resp: HttpResponse) -> None:
        self._publish(HttpRequestCompleted(
            request_id=rid if isinstance(rid, uuid4.__class__) else uuid4(),
            status_code=resp.status_code,
            elapsed_ms=resp.elapsed_ms,
            timestamp=time.time(),
        ))

    def _publish_failed(self, rid: Any, err_type: str, msg: str) -> None:
        self._publish(HttpRequestFailed(
            request_id=rid if isinstance(rid, uuid4.__class__) else uuid4(),
            error_type=err_type,
            error_message=msg,
            timestamp=time.time(),
        ))

    def _publish_retry(self, rid: Any, attempt: int, status: int, delay: float) -> None:
        self._publish(HttpRetry(
            request_id=rid if isinstance(rid, uuid4.__class__) else uuid4(),
            attempt=attempt,
            status_code=status,
            delay=delay,
            timestamp=time.time(),
        ))

    def _publish_rate_limited(self, rid: Any, err: RateLimitError) -> None:
        self._publish(HttpRateLimited(
            request_id=rid if isinstance(rid, uuid4.__class__) else uuid4(),
            retry_after=err.retry_after,
            limit=err.limit,
            remaining=err.remaining,
            timestamp=time.time(),
        ))

    def _publish_auth_failed(self, rid: Any, err: AuthExpiredError) -> None:
        self._publish(HttpAuthenticationFailed(
            request_id=rid if isinstance(rid, uuid4.__class__) else uuid4(),
            reason=err.reason,
            timestamp=time.time(),
        ))

    def _publish_quota_exceeded(self, rid: Any, err: QuotaExceededError) -> None:
        self._publish(HttpQuotaExceeded(
            request_id=rid if isinstance(rid, uuid4.__class__) else uuid4(),
            quota_type=err.quota_type,
            limit=err.limit,
            timestamp=time.time(),
        ))

    # ------------------------------------------------------------------
    # Metrics
    # ------------------------------------------------------------------

    @property
    def total_requests(self) -> int:
        return self._total_requests

    @property
    def total_retries(self) -> int:
        return self._total_retries

    @property
    def total_failures(self) -> int:
        return self._total_failures
