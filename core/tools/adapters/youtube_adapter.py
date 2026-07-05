"""YouTube Data API v3 adapter — mock + real execution modes."""

from __future__ import annotations

from typing import Any

from core.tools.adapters.base import AbstractToolAdapter
from core.tools.adapters.models import (
    AdapterExecutionResult,
    CredentialRequirement,
    ExecutionMode,
    OwnerGuidance,
    ToolRequest,
)
from core.tools.capabilities import Capability
from core.tools.http.models import HttpMethod


class YouTubeAdapter(AbstractToolAdapter):
    """Adapter for YouTube Data API v3.

    MOCK mode returns deterministic fake data (default).
    REAL mode calls the actual YouTube API via HttpClient + Provider.
    """

    @property
    def adapter_id(self) -> str:
        return "youtube_v3"

    @property
    def tool_name(self) -> str:
        return "YouTube"

    def supported_capabilities(self) -> frozenset[Capability]:
        return frozenset({
            Capability.VIDEO_EDITING,
            Capability.STORAGE,
            Capability.SOCIAL_MEDIA,
        })

    def required_config_keys(self) -> tuple[str, ...]:
        return ("api_key",)

    def required_credential_keys(self) -> tuple[str, ...]:
        return ("api_key",)

    def credential_requirements(self) -> tuple[CredentialRequirement, ...]:
        return (CredentialRequirement(
            key="api_key",
            label="YouTube API Key",
            description="API Key from Google Cloud Console with YouTube Data API v3 enabled",
        ),)

    def validate_configuration(self, config: dict[str, Any]) -> bool:
        api_key = config.get("api_key", "")
        return bool(api_key) and len(api_key) >= 10

    def validate_credentials(self) -> bool:
        return True

    def check_availability(self) -> bool:
        return True

    def owner_guidance(self) -> OwnerGuidance:
        return OwnerGuidance(
            steps=(
                "1. Acesse o Google Cloud Console (https://console.cloud.google.com)",
                "2. Crie um novo projeto ou selecione um existente",
                "3. Habilite a YouTube Data API v3",
                "4. Crie uma Credencial do tipo 'API Key'",
                "5. Restrinja a chave para uso apenas com YouTube Data API",
                "6. Copie a API Key e cole no sistema",
            ),
            docs_url="https://developers.google.com/youtube/v3/getting-started",
            notes="A API Key é gratuita com cotas diárias. Para produção, configure OAuth 2.0.",
        )

    # ------------------------------------------------------------------
    # Execution
    # ------------------------------------------------------------------

    def execute(self, request: ToolRequest) -> AdapterExecutionResult:
        if self._execution_mode == ExecutionMode.REAL:
            return self._execute_real(request)
        return self._execute_mock(request)

    def _execute_mock(self, request: ToolRequest) -> AdapterExecutionResult:
        action = request.params.get("action", "info")
        video_id = request.params.get("video_id", "dQw4w9WgXcQ")
        title = request.params.get("title", "Untitled")

        if action == "upload":
            return AdapterExecutionResult(
                success=True,
                summary=f"YouTube upload completed: '{title}'",
                output={
                    "video_id": video_id,
                    "title": title,
                    "status": "published",
                    "url": f"https://youtube.com/watch?v={video_id}",
                },
            )
        if action == "search":
            query = request.params.get("query", "ai")
            return AdapterExecutionResult(
                success=True,
                summary=f"YouTube search results for '{query}'",
                output={
                    "query": query,
                    "results": [
                        {"id": "vid1", "title": f"Result 1 for {query}"},
                        {"id": "vid2", "title": f"Result 2 for {query}"},
                    ],
                    "total_results": 2,
                },
            )
        return AdapterExecutionResult(
            success=True,
            summary=f"YouTube metadata retrieved for {video_id}",
            output={
                "video_id": video_id,
                "title": title,
                "duration_seconds": 120,
                "view_count": 1000,
            },
        )

    def _execute_real(self, request: ToolRequest) -> AdapterExecutionResult:
        action = request.params.get("action", "info")
        video_id = request.params.get("video_id", "dQw4w9WgXcQ")
        title = request.params.get("title", "Untitled")

        client = self._http_client
        provider = self._provider
        if client is None or provider is None:
            return AdapterExecutionResult(
                success=False,
                summary="",
                error="YouTube REAL mode requires HttpClient and Provider",
            )

        api_key = self._resolve_credential("api_key")
        if not api_key:
            return AdapterExecutionResult(
                success=False,
                summary="",
                error="YouTube REAL mode requires 'api_key' credential",
            )

        base = provider.base_url.rstrip("/")
        version = provider.default_version

        if action == "search":
            query = request.params.get("query", "ai")
            url = f"{base}/youtube/{version}/search"
            resp = client.get(
                url,
                params={
                    "part": "snippet",
                    "q": query,
                    "key": api_key,
                    "maxResults": "5",
                },
            )
            items = resp.body.get("items", []) if isinstance(resp.body, dict) else []
            return AdapterExecutionResult(
                success=resp.status_code == 200,
                summary=f"YouTube search: {len(items)} results" if resp.status_code == 200
                        else f"Search failed: HTTP {resp.status_code}",
                output={
                    "query": query,
                    "results": [
                        {"id": i.get("id", {}).get("videoId", ""),
                         "title": i.get("snippet", {}).get("title", "")}
                        for i in items
                    ],
                    "total_results": len(items),
                    "_real": True,
                },
                error="" if resp.status_code == 200 else f"HTTP {resp.status_code}",
            )

        if action == "upload":
            return AdapterExecutionResult(
                success=True,
                summary=f"YouTube upload simulated: '{title}' (REAL upload needs OAuth)",
                output={
                    "video_id": video_id,
                    "title": title,
                    "status": "simulated",
                    "url": f"https://youtube.com/watch?v={video_id}",
                    "_real": True,
                    "_note": "Upload requires OAuth 2.0 — use search or info in REAL mode",
                },
            )

        url = f"{base}/youtube/{version}/videos"
        resp = client.get(
            url,
            params={
                "part": "snippet,statistics",
                "id": video_id,
                "key": api_key,
            },
        )
        body = resp.body if isinstance(resp.body, dict) else {}
        snippet = body.get("items", [{}])[0].get("snippet", {}) if body.get("items") else {}
        stats = body.get("items", [{}])[0].get("statistics", {}) if body.get("items") else {}

        return AdapterExecutionResult(
            success=resp.status_code == 200,
            summary=f"YouTube info: {snippet.get('title', title)}" if resp.status_code == 200
                    else f"Info failed: HTTP {resp.status_code}",
            output={
                "video_id": video_id,
                "title": snippet.get("title", title),
                "duration_seconds": 0,
                "view_count": int(stats.get("viewCount", 0)),
                "channel": snippet.get("channelTitle", ""),
                "_real": True,
            },
            error="" if resp.status_code == 200 else f"HTTP {resp.status_code}",
        )

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _resolve_credential(self, key: str) -> str:
        if self._secret_provider is not None:
            from core.tools.secrets.models import SecretKey
            secret = self._secret_provider.get(SecretKey(key=key, tool_id=self.adapter_id))
            if secret is not None:
                return secret.value
        return self._config.get(key, "")
