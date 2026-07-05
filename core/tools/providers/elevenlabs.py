"""ElevenLabs API provider contract."""

from __future__ import annotations

from core.tools.http.models import RateLimitConfig
from core.tools.providers.base import Provider


class ElevenLabsProvider(Provider):
    """Provider contract for ElevenLabs Text-to-Speech API."""

    @property
    def provider_id(self) -> str:
        return "elevenlabs"

    @property
    def display_name(self) -> str:
        return "ElevenLabs"

    @property
    def base_url(self) -> str:
        return "https://api.elevenlabs.io"

    @property
    def auth_type(self) -> str:
        return "api_key"

    @property
    def rate_limits(self) -> RateLimitConfig:
        return RateLimitConfig(
            max_requests=30,
            window_seconds=60.0,
            max_concurrent=3,
        )
