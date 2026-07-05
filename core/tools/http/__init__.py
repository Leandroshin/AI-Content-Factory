"""HTTP infrastructure for real tool execution.

Provides typed HTTP models, retry/timeout policies, rate limiting,
error types, event types, and reusable client implementations.

No adapter depends on this layer directly — it is injected when
an adapter switches to REAL execution mode.
"""

from __future__ import annotations

from .client import HttpClient, MockHttpClient
from .errors import (
    AuthExpiredError,
    HttpError,
    NetworkUnavailableError,
    QuotaExceededError,
    RateLimitError,
    RetryExhaustedError,
    TimeoutError,
)
from .events import (
    HttpAuthenticationFailed,
    HttpQuotaExceeded,
    HttpRateLimited,
    HttpRequestCompleted,
    HttpRequestFailed,
    HttpRequestStarted,
    HttpRetry,
)
from .models import (
    HttpMethod,
    HttpRequest,
    HttpResponse,
    RateLimitConfig,
    RetryPolicy,
    TimeoutPolicy,
)
from .rate_limiter import RateLimiter
from .real_client import RealHttpClient

__all__ = [
    "AuthExpiredError",
    "HttpAuthenticationFailed",
    "HttpClient",
    "HttpError",
    "HttpMethod",
    "HttpQuotaExceeded",
    "HttpRateLimited",
    "HttpRequest",
    "HttpRequestCompleted",
    "HttpRequestFailed",
    "HttpRequestStarted",
    "HttpResponse",
    "HttpRetry",
    "MockHttpClient",
    "NetworkUnavailableError",
    "QuotaExceededError",
    "RateLimitConfig",
    "RateLimitError",
    "RateLimiter",
    "RealHttpClient",
    "RetryExhaustedError",
    "RetryPolicy",
    "TimeoutError",
    "TimeoutPolicy",
]
