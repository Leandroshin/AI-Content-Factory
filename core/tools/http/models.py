"""HTTP data models for real tool execution."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any


class HttpMethod(StrEnum):
    """Standard HTTP methods supported by the HTTP client."""
    GET = "GET"
    POST = "POST"
    PUT = "PUT"
    PATCH = "PATCH"
    DELETE = "DELETE"


@dataclass(frozen=True, slots=True)
class HttpRequest:
    """Typed HTTP request ready to be sent."""
    method: HttpMethod
    url: str
    headers: dict[str, str] = field(default_factory=dict)
    params: dict[str, str] = field(default_factory=dict)
    body: Any = None
    timeout: float = 30.0


@dataclass(frozen=True, slots=True)
class HttpResponse:
    """Typed HTTP response after execution."""
    status_code: int
    headers: dict[str, str] = field(default_factory=dict)
    body: Any = None
    elapsed_ms: float = 0.0


@dataclass(frozen=True, slots=True)
class RetryPolicy:
    """Configuration for retry behaviour."""
    max_retries: int = 3
    base_delay: float = 1.0
    max_delay: float = 60.0
    backoff_factor: float = 2.0
    retryable_statuses: tuple[int, ...] = (429, 500, 502, 503, 504)
    jitter: bool = True


@dataclass(frozen=True, slots=True)
class TimeoutPolicy:
    """Granular timeout configuration."""
    connect: float = 10.0
    read: float = 30.0
    write: float = 30.0
    total: float = 60.0


@dataclass(frozen=True, slots=True)
class RateLimitConfig:
    """Rate limiting configuration for a provider/endpoint."""
    max_requests: int = 10
    window_seconds: float = 1.0
    max_concurrent: int = 5
