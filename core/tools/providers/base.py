"""Abstract base class for all SDK providers.

A Provider defines the contract (base URL, auth type, rate limits,
endpoints) for an external service. It does NOT make real API calls.
Adapters reference providers when operating in REAL mode.
"""

from __future__ import annotations

from abc import ABC, abstractmethod

from core.tools.http.models import RateLimitConfig


class Provider(ABC):
    """Contract for an external service provider.

    Subclasses define the metadata needed to interact with
    a specific API (Google, GitHub, OpenAI, etc.).
    """

    @property
    @abstractmethod
    def provider_id(self) -> str:
        """Unique identifier (e.g. 'google', 'github')."""
        ...

    @property
    @abstractmethod
    def display_name(self) -> str:
        """Human-readable name (e.g. 'Google Cloud Platform')."""
        ...

    @property
    @abstractmethod
    def base_url(self) -> str:
        """Base URL for all API calls (e.g. 'https://www.googleapis.com')."""
        ...

    @property
    def auth_type(self) -> str:
        """Authentication method: 'api_key', 'oauth', 'token', or 'none'."""
        return "api_key"

    @property
    def rate_limits(self) -> RateLimitConfig:
        """Default rate limiting configuration."""
        return RateLimitConfig()

    @property
    def supported_versions(self) -> tuple[str, ...]:
        """Supported API versions."""
        return ("v1",)

    @property
    def default_version(self) -> str:
        """Default API version."""
        return "v1"
