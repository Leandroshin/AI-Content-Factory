"""Rate limiter with exponential backoff and jitter.

Respects provider-defined rate limits and retry policies.
Thread-safe via a standard lock. Deterministic when called
sequentially.
"""

from __future__ import annotations

import random
import time
from threading import Lock
from typing import Any

from core.tools.http.errors import RateLimitError, RetryExhaustedError
from core.tools.http.models import RateLimitConfig, RetryPolicy


class RateLimiter:
    """Token-bucket rate limiter with configurable window.

    Usage::

        limiter = RateLimiter(RateLimitConfig(max_requests=60, window_seconds=60))
        with limiter:
            response = client.send(request)
    """

    def __init__(
        self,
        config: RateLimitConfig | None = None,
        retry_policy: RetryPolicy | None = None,
    ) -> None:
        self._config = config or RateLimitConfig()
        self._retry_policy = retry_policy or RetryPolicy()
        self._slots: list[float] = []
        self._lock = Lock()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def acquire(self) -> float:
        """Block until a rate-limit slot is available.

        Returns the wait time in seconds (0 if immediate).
        """
        if self._config.max_requests <= 0:
            return 0.0

        with self._lock:
            now = time.time()
            window_start = now - self._config.window_seconds

            # Prune expired slots
            self._slots = [t for t in self._slots if t > window_start]

            if len(self._slots) < self._config.max_requests:
                self._slots.append(now)
                return 0.0

            # Next available slot is the oldest in the window
            wait = self._slots[0] + self._config.window_seconds - now
            if wait > 0:
                time.sleep(wait)
            self._slots.append(time.time())
            self._slots.pop(0)
            return max(wait, 0.0)

    def release(self) -> None:
        """Manually release a slot (for error paths)."""
        pass  # Tokens expire naturally via window pruning

    @property
    def available(self) -> int:
        """Number of requests still available in the current window."""
        with self._lock:
            now = time.time()
            window_start = now - self._config.window_seconds
            self._slots = [t for t in self._slots if t > window_start]
            return max(0, self._config.max_requests - len(self._slots))

    @property
    def remaining(self) -> int:
        return self.available

    # ------------------------------------------------------------------
    # Context manager
    # ------------------------------------------------------------------

    def __enter__(self) -> RateLimiter:
        self.acquire()
        return self

    def __exit__(self, *args: Any) -> None:
        self.release()

    # ------------------------------------------------------------------
    # Retry helper
    # ------------------------------------------------------------------

    def retry_delay(self, attempt: int, status_code: int = 0) -> float:
        """Calculate exponential backoff delay for a given attempt.

        Uses: base_delay * backoff_factor^attempt + jitter
        """
        if attempt <= 0:
            return 0.0

        delay = self._retry_policy.base_delay * (
            self._retry_policy.backoff_factor ** (attempt - 1)
        )
        delay = min(delay, self._retry_policy.max_delay)

        if self._retry_policy.jitter:
            delay *= 0.5 + random.random() * 0.5  # 50-100% of calculated

        return round(delay, 3)

    def should_retry(self, attempt: int, status_code: int) -> bool:
        """Check if a retry should be attempted."""
        if attempt >= self._retry_policy.max_retries:
            return False
        return status_code in self._retry_policy.retryable_statuses

    def with_retry(
        self,
        fn: Any,
        *,
        on_error: Any = None,
    ) -> Any:
        """Execute a callable with automatic retry and backoff.

        Args:
            fn: Callable that returns (status_code, result) or raises
            on_error: Callable(status_code, attempt, delay) for side effects

        Returns:
            Result from fn if successful

        Raises:
            RetryExhaustedError after all retries exhausted
        """
        last_status = 0
        last_error = ""

        for attempt in range(1, self._retry_policy.max_retries + 1):
            try:
                self.acquire()
                result = fn()
                last_status = 200
                return result
            except RateLimitError as e:
                delay = e.retry_after or self.retry_delay(attempt, 429)
                last_status = 429
                last_error = str(e)
                if on_error:
                    on_error(429, attempt, delay)
                if attempt < self._retry_policy.max_retries:
                    time.sleep(delay)
            except Exception as e:
                last_status = 0
                last_error = str(e)
                if not self.should_retry(attempt, 0):
                    raise
                delay = self.retry_delay(attempt, 0)
                if on_error:
                    on_error(0, attempt, delay)
                time.sleep(delay)

        raise RetryExhaustedError(
            url="",
            attempts=self._retry_policy.max_retries,
            last_status=last_status,
            last_error=last_error,
        )
