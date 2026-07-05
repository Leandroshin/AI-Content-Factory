"""ElevenLabs API adapter — mock + real execution modes."""

from __future__ import annotations

import math
import wave
from pathlib import Path
from struct import pack
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
from core.tools.http.errors import HttpError
from core.tools.provider_control import ProviderBudgetDecision, ProviderBudgetGuard


class ElevenLabsAdapter(AbstractToolAdapter):
    """Adapter for ElevenLabs text-to-speech API.

    MOCK mode returns deterministic fake data (default).
    REAL mode calls the actual ElevenLabs API via HttpClient + Provider.
    """

    def __init__(self) -> None:
        super().__init__()
        self._budget_guard: ProviderBudgetGuard | None = None

    @property
    def adapter_id(self) -> str:
        return "elevenlabs_tts"

    def set_budget_guard(self, budget_guard: ProviderBudgetGuard | None) -> None:
        """Inject a REAL-mode provider budget guard."""
        self._budget_guard = budget_guard

    @property
    def tool_name(self) -> str:
        return "ElevenLabs"

    def supported_capabilities(self) -> frozenset[Capability]:
        return frozenset({
            Capability.SPEECH_GENERATION,
            Capability.VOICE_CLONE,
        })

    def required_config_keys(self) -> tuple[str, ...]:
        return ("api_key",)

    def required_credential_keys(self) -> tuple[str, ...]:
        return ("api_key",)

    def credential_requirements(self) -> tuple[CredentialRequirement, ...]:
        return (CredentialRequirement(
            key="api_key",
            label="ElevenLabs API Key",
            description="API Key from ElevenLabs profile settings",
        ),)

    def validate_configuration(self, config: dict[str, Any]) -> bool:
        api_key = config.get("api_key", "")
        return bool(api_key) and len(api_key) >= 8

    def validate_credentials(self) -> bool:
        return True

    def check_availability(self) -> bool:
        return True

    def owner_guidance(self) -> OwnerGuidance:
        return OwnerGuidance(
            steps=(
                "1. Acesse ElevenLabs (https://elevenlabs.io) e faça login",
                "2. Vá para Profile > API Key",
                "3. Copie sua API Key (ou crie uma nova)",
                "4. Cole a API Key no sistema",
            ),
            docs_url="https://docs.elevenlabs.io/api-reference/authentication",
            notes="A API Key gratuita tem limite de caracteres por mês. Considere um plano pago para uso intensivo.",
        )

    # ------------------------------------------------------------------
    # Execution
    # ------------------------------------------------------------------

    def execute(self, request: ToolRequest) -> AdapterExecutionResult:
        if self._execution_mode == ExecutionMode.REAL:
            return self._execute_real(request)
        return self._execute_mock(request)

    def _execute_mock(self, request: ToolRequest) -> AdapterExecutionResult:
        action = request.params.get("action", "synthesize")
        text = request.params.get("text", "Hello world")
        voice = request.params.get("voice", "default")

        if action == "synthesize":
            voice_id = request.params.get("voice_id", f"voice_{voice.lower().replace(' ', '_')}")
            model_id = request.params.get("model_id", "mock_tts_model")
            audio_format = str(request.params.get("output_format", "mp3")).lstrip(".")
            duration_seconds = float(request.params.get(
                "duration_seconds",
                round(len(text) * 0.08, 2),
            ))
            file_info = self._maybe_write_mock_audio(request, audio_format, duration_seconds)
            output = {
                "text": text,
                "voice": voice,
                "voice_id": voice_id,
                "model_id": model_id,
                "duration_seconds": round(duration_seconds, 2),
                "audio_format": file_info.get("audio_format", audio_format),
                "characters": len(text),
            }
            output.update(file_info)
            return AdapterExecutionResult(
                success=True,
                summary=f"Speech synthesised: '{text[:50]}...' ({voice})",
                output=output,
            )
        if action == "clone_voice":
            return AdapterExecutionResult(
                success=True,
                summary=f"Voice clone created: {voice}",
                output={
                    "voice_id": f"voice_{voice.lower().replace(' ', '_')}",
                    "name": voice,
                    "status": "ready",
                },
            )
        return AdapterExecutionResult(
            success=True,
            summary=f"ElevenLabs voice info: {voice}",
            output={
                "voice_id": voice,
                "name": voice,
                "category": "premade",
            },
        )

    def _execute_real(self, request: ToolRequest) -> AdapterExecutionResult:
        action = request.params.get("action", "synthesize")
        text = request.params.get("text", "Hello world")
        voice = request.params.get("voice", "default")

        client = self._http_client
        provider = self._provider
        if client is None or provider is None:
            return AdapterExecutionResult(
                success=False,
                summary="",
                error="ElevenLabs REAL mode requires HttpClient and Provider",
            )

        api_key = self._resolve_credential("api_key")
        if not api_key:
            return AdapterExecutionResult(
                success=False,
                summary="",
                error="ElevenLabs REAL mode requires 'api_key' credential",
            )

        base = provider.base_url.rstrip("/")
        headers = {
            "xi-api-key": api_key,
            "Content-Type": "application/json",
        }

        if action == "synthesize":
            voice_id = request.params.get("voice_id", "21m00Tcm4TlvDq8ikWAM")
            model_id = request.params.get("model_id", "eleven_monolingual_v1")
            output_format = str(request.params.get("output_format", "mp3")).lstrip(".")
            voice_settings = request.params.get(
                "voice_settings",
                {"stability": 0.5, "similarity_boost": 0.75},
            )
            if not isinstance(voice_settings, dict):
                voice_settings = {"stability": 0.5, "similarity_boost": 0.75}
            url = f"{base}/v1/text-to-speech/{voice_id}"
            body = {
                "text": text,
                "model_id": model_id,
                "voice_settings": voice_settings,
            }

            budget_decision = self._budget_check("synthesize", len(text), "characters")
            if budget_decision is not None and not budget_decision.allowed:
                return AdapterExecutionResult(
                    success=False,
                    summary="ElevenLabs REAL call blocked by provider budget guard.",
                    output={
                        "_real": True,
                        "_blocked_by_budget": True,
                        "provider_control": budget_decision.to_dict(),
                    },
                    error=budget_decision.reason,
                )

            try:
                resp = client.post(url, headers=headers, body=body)
            except HttpError as exc:
                self._budget_record(
                    operation="synthesize",
                    units=len(text),
                    unit_name="characters",
                    success=False,
                    metadata={
                        "voice_id": str(voice_id),
                        "model_id": str(model_id),
                        "output_format": output_format,
                        "http_error": type(exc).__name__,
                    },
                )
                output = {
                    "_real": True,
                    "_http_error": type(exc).__name__,
                }
                if budget_decision is not None:
                    output["provider_control"] = budget_decision.to_dict()
                return AdapterExecutionResult(
                    success=False,
                    summary="ElevenLabs REAL synthesis failed before audio response.",
                    output=output,
                    error=str(exc) or type(exc).__name__,
                )
            file_info = (
                self._maybe_write_real_audio(request, resp.body, output_format)
                if resp.status_code == 200 else {}
            )
            duration_seconds = float(request.params.get(
                "duration_seconds",
                round(len(text) * 0.08, 2),
            ))
            output = {
                "text": text,
                "voice": voice,
                "voice_id": voice_id,
                "model_id": model_id,
                "duration_seconds": round(duration_seconds, 2),
                "audio_format": output_format,
                "characters": len(text),
                "_real": True,
                "_audio_in_response": resp.status_code == 200,
            }
            if budget_decision is not None:
                output["provider_control"] = budget_decision.to_dict()
            output.update(file_info)
            self._budget_record(
                operation="synthesize",
                units=len(text),
                unit_name="characters",
                success=resp.status_code == 200,
                metadata={
                    "voice_id": str(voice_id),
                    "model_id": str(model_id),
                    "output_format": output_format,
                },
            )
            return AdapterExecutionResult(
                success=resp.status_code == 200,
                summary=f"Speech synthesised: {len(text)} chars ({voice})" if resp.status_code == 200
                        else f"Synthesis failed: HTTP {resp.status_code}",
                output=output,
                error="" if resp.status_code == 200 else f"HTTP {resp.status_code}",
            )

        if action == "clone_voice":
            url = f"{base}/v1/voices/add"
            name = request.params.get("name", voice)
            files = request.params.get("files", [])
            body = {"name": name, "files": files}
            try:
                resp = client.post(url, headers=headers, body=body)
            except HttpError as exc:
                return AdapterExecutionResult(
                    success=False,
                    summary="ElevenLabs REAL voice clone failed before response.",
                    output={
                        "_real": True,
                        "_http_error": type(exc).__name__,
                    },
                    error=str(exc) or type(exc).__name__,
                )
            resp_body = resp.body if isinstance(resp.body, dict) else {}
            return AdapterExecutionResult(
                success=resp.status_code in (200, 201),
                summary=f"Voice clone: {resp_body.get('voice_id', 'unknown')}" if resp.status_code in (200, 201)
                        else f"Clone failed: HTTP {resp.status_code}",
                output={
                    "voice_id": resp_body.get("voice_id", ""),
                    "name": name,
                    "status": "ready" if resp.status_code in (200, 201) else "failed",
                    "_real": True,
                },
                error="" if resp.status_code in (200, 201) else f"HTTP {resp.status_code}",
            )

        url = f"{base}/v1/voices"
        try:
            resp = client.get(url, headers=headers)
        except HttpError as exc:
            return AdapterExecutionResult(
                success=False,
                summary="ElevenLabs REAL voice lookup failed before response.",
                output={
                    "_real": True,
                    "_http_error": type(exc).__name__,
                },
                error=str(exc) or type(exc).__name__,
            )
        resp_body = resp.body if isinstance(resp.body, dict) else {}
        voices = resp_body.get("voices", [])
        return AdapterExecutionResult(
            success=resp.status_code == 200,
            summary=f"ElevenLabs: {len(voices)} voices available" if resp.status_code == 200
                    else f"Voices failed: HTTP {resp.status_code}",
            output={
                "voice_id": voice,
                "voices": [v.get("name", "") for v in (voices or [])],
                "category": "premade",
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

    def _output_dir(self, request: ToolRequest) -> Path | None:
        raw = request.params.get("output_dir") or self._config.get("output_dir")
        if not raw:
            return None
        return Path(str(raw))

    def _should_write_file(self, request: ToolRequest) -> bool:
        return bool(request.params.get("write_file")) or self._output_dir(request) is not None

    def _safe_task_stem(self, request: ToolRequest) -> str:
        raw = str(request.params.get("task_id", request.tool_id))
        safe = "".join(ch if ch.isalnum() or ch in ("-", "_") else "_" for ch in raw)
        return safe or "speech"

    def _maybe_write_mock_audio(
        self,
        request: ToolRequest,
        audio_format: str,
        duration_seconds: float,
    ) -> dict[str, Any]:
        if not self._should_write_file(request):
            return {}

        output_dir = self._output_dir(request) or Path("output/audio")
        output_dir.mkdir(parents=True, exist_ok=True)
        fmt = audio_format.lower()
        if fmt != "wav":
            fmt = "wav"
        output_path = output_dir / f"{self._safe_task_stem(request)}.{fmt}"
        self._write_mock_wav(output_path, max(0.25, duration_seconds))
        return {
            "audio_format": "wav",
            "file_path": str(output_path.resolve()),
            "file_size_bytes": output_path.stat().st_size,
            "physical_asset": True,
            "mode": "mock_file",
        }

    def _maybe_write_real_audio(
        self,
        request: ToolRequest,
        body: Any,
        output_format: str,
    ) -> dict[str, Any]:
        if not self._should_write_file(request):
            return {}
        raw = self._body_to_bytes(body)
        if not raw:
            return {}

        output_dir = self._output_dir(request) or Path("output/audio")
        output_dir.mkdir(parents=True, exist_ok=True)
        output_path = output_dir / f"{self._safe_task_stem(request)}.{output_format.lower()}"
        output_path.write_bytes(raw)
        return {
            "file_path": str(output_path.resolve()),
            "file_size_bytes": output_path.stat().st_size,
            "physical_asset": True,
            "mode": "real_file",
        }

    def _body_to_bytes(self, body: Any) -> bytes:
        if isinstance(body, bytes):
            return body
        if isinstance(body, bytearray):
            return bytes(body)
        if isinstance(body, str):
            return body.encode("utf-8")
        return b""

    def _write_mock_wav(self, output_path: Path, duration_seconds: float) -> None:
        sample_rate = 16000
        total_frames = max(1, int(sample_rate * duration_seconds))
        amplitude = 1800
        frequency = 220.0
        with wave.open(str(output_path), "wb") as wav:
            wav.setnchannels(1)
            wav.setsampwidth(2)
            wav.setframerate(sample_rate)
            frames = bytearray()
            for idx in range(total_frames):
                envelope = 0.35 + 0.65 * math.sin((idx / sample_rate) * math.pi)
                sample = int(amplitude * envelope * math.sin(2 * math.pi * frequency * idx / sample_rate))
                frames.extend(pack("<h", sample))
            wav.writeframes(bytes(frames))

    def _budget_check(
        self,
        operation: str,
        units: int,
        unit_name: str,
    ) -> ProviderBudgetDecision | None:
        if self._budget_guard is None:
            return None
        return self._budget_guard.check(
            provider="elevenlabs",
            operation=operation,
            units=units,
            unit_name=unit_name,
        )

    def _budget_record(
        self,
        *,
        operation: str,
        units: int,
        unit_name: str,
        success: bool,
        metadata: dict[str, Any] | None = None,
    ) -> None:
        if self._budget_guard is None:
            return
        self._budget_guard.record_usage(
            provider="elevenlabs",
            operation=operation,
            mode=self._execution_mode.value,
            units=units,
            unit_name=unit_name,
            success=success,
            billable=success,
            metadata=metadata,
        )
