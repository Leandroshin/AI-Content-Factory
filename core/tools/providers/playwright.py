"""Playwright browser automation provider contract."""

from __future__ import annotations

from core.tools.http.models import RateLimitConfig
from core.tools.providers.base import Provider


class PlaywrightProvider(Provider):
    """Provider contract for Playwright browser automation.

    Playwright runs locally and does not use HTTP APIs, so
    rate limits and auth are not applicable.
    """

    @property
    def provider_id(self) -> str:
        return "playwright"

    @property
    def display_name(self) -> str:
        return "Playwright"

    @property
    def base_url(self) -> str:
        return ""

    @property
    def auth_type(self) -> str:
        return "none"

    @property
    def rate_limits(self) -> RateLimitConfig:
        return RateLimitConfig(
            max_requests=0,
            window_seconds=0.0,
            max_concurrent=1,
        )
