"""Google Gemini Developer API provider contract."""

from __future__ import annotations

from core.tools.http.models import RateLimitConfig
from core.tools.providers.base import Provider


class GeminiProvider(Provider):
    """Provider metadata for Gemini Interactions and model inventory APIs."""

    @property
    def provider_id(self) -> str:
        return "gemini"

    @property
    def display_name(self) -> str:
        return "Google Gemini Developer API"

    @property
    def base_url(self) -> str:
        return "https://generativelanguage.googleapis.com"

    @property
    def supported_versions(self) -> tuple[str, ...]:
        return ("v1beta",)

    @property
    def default_version(self) -> str:
        return "v1beta"

    @property
    def rate_limits(self) -> RateLimitConfig:
        return RateLimitConfig(max_requests=10, window_seconds=60.0, max_concurrent=1)
