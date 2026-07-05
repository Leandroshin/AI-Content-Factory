"""HTTP event types for real tool execution observability.

All events are published by the RealHttpClient or RateLimiter
during REAL execution mode. They feed into HttpSnapshot via
the ObservabilityProjector.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any
from uuid import UUID


@dataclass(frozen=True, slots=True)
class HttpRequestStarted:
    request_id: UUID
    method: str
    url: str
    timestamp: float = 0.0
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class HttpRequestCompleted:
    request_id: UUID
    status_code: int
    elapsed_ms: float
    timestamp: float = 0.0
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class HttpRequestFailed:
    request_id: UUID
    error_type: str
    error_message: str
    timestamp: float = 0.0
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class HttpRetry:
    request_id: UUID
    attempt: int
    status_code: int
    delay: float
    timestamp: float = 0.0
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class HttpRateLimited:
    request_id: UUID
    retry_after: float
    limit: int = 0
    remaining: int = 0
    timestamp: float = 0.0
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class HttpAuthenticationFailed:
    request_id: UUID
    reason: str
    timestamp: float = 0.0
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class HttpQuotaExceeded:
    request_id: UUID
    quota_type: str
    limit: int = 0
    timestamp: float = 0.0
    metadata: dict[str, Any] = field(default_factory=dict)
