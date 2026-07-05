"""HTTP error types for real tool execution.

All error types are frozen dataclasses with slots for
predictable structure and low overhead.
"""

from __future__ import annotations

from dataclasses import dataclass


class HttpError(Exception):
    """Base exception for all HTTP-related errors."""


@dataclass
class TimeoutError(HttpError):
    """Request timed out."""
    url: str = ""
    timeout_seconds: float = 0.0


@dataclass
class RetryExhaustedError(HttpError):
    """All retry attempts were exhausted."""
    url: str = ""
    attempts: int = 0
    last_status: int = 0
    last_error: str = ""


@dataclass
class RateLimitError(HttpError):
    """Rate limit exceeded."""
    url: str = ""
    retry_after: float = 0.0
    limit: int = 0
    remaining: int = 0


@dataclass
class AuthExpiredError(HttpError):
    """Authentication has expired."""
    url: str = ""
    reason: str = ""


@dataclass
class QuotaExceededError(HttpError):
    """API quota exceeded."""
    url: str = ""
    quota_type: str = ""
    limit: int = 0


@dataclass
class NetworkUnavailableError(HttpError):
    """Network is unreachable."""
    url: str = ""
    reason: str = ""
