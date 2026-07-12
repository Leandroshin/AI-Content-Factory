"""Tool Adapters — pluggable integration layer for external tools.

Each adapter implements only its specific tool logic.
No adapter knows about Company, CEO, DepartmentManager,
or SpecialistEmployee.
"""

from __future__ import annotations

from .base import AbstractToolAdapter
from .elevenlabs_adapter import ElevenLabsAdapter
from .ffmpeg_adapter import FFmpegRenderAdapter
from .github_adapter import GitHubAdapter
from .hyperframes_adapter import HyperFramesRenderAdapter
from .kokoro_adapter import KokoroTTSAdapter
from .meta_ads_adapter import MetaAdsAnalyticsAdapter
from .models import (
    AdapterConfigStatus,
    AdapterExecutionResult,
    AdapterStatus,
    CredentialRequirement,
    ExecutionMode,
    OwnerGuidance,
    ToolRequest,
    ToolResponse,
)
from .playwright_adapter import PlaywrightAdapter
from .telegram_adapter import TelegramAdapter
from .youtube_adapter import YouTubeAdapter

__all__ = [
    "AbstractToolAdapter",
    "AdapterConfigStatus",
    "AdapterExecutionResult",
    "AdapterStatus",
    "CredentialRequirement",
    "ElevenLabsAdapter",
    "ExecutionMode",
    "FFmpegRenderAdapter",
    "GitHubAdapter",
    "HyperFramesRenderAdapter",
    "KokoroTTSAdapter",
    "MetaAdsAnalyticsAdapter",
    "OwnerGuidance",
    "PlaywrightAdapter",
    "TelegramAdapter",
    "ToolRequest",
    "ToolResponse",
    "YouTubeAdapter",
]
