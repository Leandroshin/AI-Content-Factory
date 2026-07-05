"""OpenAI API provider contract."""

from __future__ import annotations

from core.tools.http.models import RateLimitConfig
from core.tools.providers.base import Provider


class OpenAIProvider(Provider):
    """Provider contract for OpenAI API (GPT, Whisper, etc.)."""

    @property
    def provider_id(self) -> str:
        return "openai"

    @property
    def display_name(self) -> str:
        return "OpenAI"

    @property
    def base_url(self) -> str:
        return "https://api.openai.com"

    @property
    def auth_type(self) -> str:
        return "token"

    @property
    def rate_limits(self) -> RateLimitConfig:
        return RateLimitConfig(
            max_requests=500,
            window_seconds=60.0,
            max_concurrent=10,
        )
