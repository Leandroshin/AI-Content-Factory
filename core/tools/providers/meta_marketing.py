"""Meta Marketing API provider contract."""

from __future__ import annotations

from core.tools.http.models import RateLimitConfig
from core.tools.providers.base import Provider


class MetaMarketingProvider(Provider):
    """Provider metadata for configurable Meta Graph API versions."""

    @property
    def provider_id(self) -> str:
        return "meta_marketing"

    @property
    def display_name(self) -> str:
        return "Meta Marketing API"

    @property
    def base_url(self) -> str:
        return "https://graph.facebook.com"

    @property
    def auth_type(self) -> str:
        return "oauth_bearer"

    @property
    def supported_versions(self) -> tuple[str, ...]:
        return ("configurable",)

    @property
    def default_version(self) -> str:
        return "configurable"

    @property
    def rate_limits(self) -> RateLimitConfig:
        return RateLimitConfig(
            max_requests=4,
            window_seconds=1.0,
            max_concurrent=2,
        )
