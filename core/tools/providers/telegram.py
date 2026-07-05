"""Telegram Bot API provider contract."""

from __future__ import annotations

from core.tools.http.models import RateLimitConfig
from core.tools.providers.base import Provider


class TelegramProvider(Provider):
    """Provider contract for Telegram Bot API."""

    @property
    def provider_id(self) -> str:
        return "telegram"

    @property
    def display_name(self) -> str:
        return "Telegram Bot API"

    @property
    def base_url(self) -> str:
        return "https://api.telegram.org"

    @property
    def auth_type(self) -> str:
        return "bot_token"

    @property
    def supported_versions(self) -> tuple[str, ...]:
        return ("bot_api",)

    @property
    def default_version(self) -> str:
        return "bot_api"

    @property
    def rate_limits(self) -> RateLimitConfig:
        return RateLimitConfig(
            max_requests=20,
            window_seconds=1.0,
            max_concurrent=5,
        )
