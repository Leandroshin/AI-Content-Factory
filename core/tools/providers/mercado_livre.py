"""Mercado Livre API provider contract."""

from __future__ import annotations

from core.tools.http.models import RateLimitConfig
from core.tools.providers.base import Provider


class MercadoLivreProvider(Provider):
    """Metadata for the Brazilian Mercado Livre API."""

    @property
    def provider_id(self) -> str:
        return "mercado_livre"

    @property
    def display_name(self) -> str:
        return "Mercado Livre API"

    @property
    def base_url(self) -> str:
        return "https://api.mercadolibre.com"

    @property
    def auth_type(self) -> str:
        return "oauth_bearer"

    @property
    def supported_versions(self) -> tuple[str, ...]:
        return ("unversioned",)

    @property
    def default_version(self) -> str:
        return "unversioned"

    @property
    def rate_limits(self) -> RateLimitConfig:
        return RateLimitConfig(max_requests=4, window_seconds=1.0, max_concurrent=2)
