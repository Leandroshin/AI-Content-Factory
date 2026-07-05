"""Google Cloud / YouTube Data API provider contract."""

from __future__ import annotations

from core.tools.http.models import RateLimitConfig
from core.tools.providers.base import Provider


class GoogleProvider(Provider):
    """Provider contract for Google Cloud Platform APIs.

    Covers YouTube Data API, Google Drive, Gemini, and other
    GCP services.
    """

    @property
    def provider_id(self) -> str:
        return "google"

    @property
    def display_name(self) -> str:
        return "Google Cloud Platform"

    @property
    def base_url(self) -> str:
        return "https://www.googleapis.com"

    @property
    def auth_type(self) -> str:
        return "api_key"

    @property
    def supported_versions(self) -> tuple[str, ...]:
        return ("v3",)

    @property
    def default_version(self) -> str:
        return "v3"

    @property
    def rate_limits(self) -> RateLimitConfig:
        return RateLimitConfig(
            max_requests=60,
            window_seconds=60.0,
            max_concurrent=10,
        )
