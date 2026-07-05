"""GitHub REST API provider contract."""

from __future__ import annotations

from core.tools.http.models import RateLimitConfig
from core.tools.providers.base import Provider


class GitHubProvider(Provider):
    """Provider contract for GitHub REST API."""

    @property
    def provider_id(self) -> str:
        return "github"

    @property
    def display_name(self) -> str:
        return "GitHub"

    @property
    def base_url(self) -> str:
        return "https://api.github.com"

    @property
    def auth_type(self) -> str:
        return "token"

    @property
    def supported_versions(self) -> tuple[str, ...]:
        return ("2022-11-28",)

    @property
    def default_version(self) -> str:
        return "2022-11-28"

    @property
    def rate_limits(self) -> RateLimitConfig:
        return RateLimitConfig(
            max_requests=5000,
            window_seconds=3600.0,
            max_concurrent=50,
        )
