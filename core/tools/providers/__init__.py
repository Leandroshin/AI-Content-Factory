"""SDK Provider contracts.

Each provider defines its API surface (base URL, auth type,
rate limits, endpoints) without making real API calls.
Adapters use providers when in REAL execution mode.
"""

from __future__ import annotations

from .base import Provider
from .elevenlabs import ElevenLabsProvider
from .github_provider import GitHubProvider
from .google import GoogleProvider
from .openai import OpenAIProvider
from .playwright import PlaywrightProvider
from .telegram import TelegramProvider

__all__ = [
    "ElevenLabsProvider",
    "GitHubProvider",
    "GoogleProvider",
    "OpenAIProvider",
    "PlaywrightProvider",
    "Provider",
    "TelegramProvider",
]
