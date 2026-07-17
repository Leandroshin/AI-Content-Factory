"""Gemini Omni Flash video adapter with mandatory REAL budget control."""

from __future__ import annotations

import base64
from pathlib import Path
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


class GeminiOmniVideoAdapter(AbstractToolAdapter):
    """Generate or edit short videos with Gemini Omni Flash.

    MOCK is the default. REAL generation is blocked unless a ProviderBudgetGuard
    exists, owner approval is true, and the seconds/request/cost limits allow it.
    """

    MODEL_ID = "gemini-omni-flash-preview"

    def __init__(self) -> None:
        super().__init__()
        self._budget_guard: ProviderBudgetGuard | None = None

    @property
    def adapter_id(self) -> str:
        return "gemini_omni_video"

    @property
    def tool_name(self) -> str:
        return "Gemini Omni Flash Video"

    def supported_capabilities(self) -> frozenset[Capability]:
        return frozenset({Capability.VIDEO_GENERATION, Capability.VIDEO_EDITING})

    def required_config_keys(self) -> tuple[str, ...]:
        return ("api_key",)

    def required_credential_keys(self) -> tuple[str, ...]:
        return ("api_key",)

    def credential_requirements(self) -> tuple[CredentialRequirement, ...]:
        return (CredentialRequirement(
            key="api_key",
            label="Gemini API Key",
            description="Google AI Studio key stored outside Git.",
        ),)

    def validate_configuration(self, config: dict[str, Any]) -> bool:
        return len(str(config.get("api_key", ""))) >= 20

    def validate_credentials(self) -> bool:
        return True

    def check_availability(self) -> bool:
        return True

    def owner_guidance(self) -> OwnerGuidance:
        return OwnerGuidance(
            steps=(
                "1. Create a key in Google AI Studio.",
                "2. Store it in secrets/gemini.env as GEMINI_API_KEY.",
                "3. Configure billing for Gemini Developer API if REAL generation is required.",
                "4. Approve an explicit seconds, requests, and USD budget before switching to REAL.",
            ),
            docs_url="https://ai.google.dev/gemini-api/docs/omni",
            notes="Gemini Omni Flash has no API free tier. Official effective video price is approximately USD 0.10 per output second at 720p.",
        )

    def set_budget_guard(self, budget_guard: ProviderBudgetGuard | None) -> None:
        self._budget_guard = budget_guard

    def execute(self, request: ToolRequest) -> AdapterExecutionResult:
        if self._execution_mode == ExecutionMode.REAL:
            return self._execute_real(request)
        return self._execute_mock(request)

    def _execute_mock(self, request: ToolRequest) -> AdapterExecutionResult:
        duration = self._duration(request)
        task = str(request.params.get("task", "text_to_video"))
        return AdapterExecutionResult(
            success=True,
            summary=f"Gemini Omni Flash MOCK planned {duration}s {task}",
            output={
                "model_id": self.MODEL_ID,
                "duration_seconds": duration,
                "task": task,
                "resolution": "720p",
                "fps": 24,
                "estimated_cost_usd": round(duration * 0.10, 2),
                "physical_asset": False,
                "_real": False,
            },
        )

    def _execute_real(self, request: ToolRequest) -> AdapterExecutionResult:
        client = self._http_client
        provider = self._provider
        if client is None or provider is None:
            return self._failure("Gemini REAL mode requires HttpClient and Provider")
        api_key = self._resolve_credential()
        if not api_key:
            return self._failure("Gemini REAL mode requires 'api_key' credential")
        duration = self._duration(request)
        decision = self._budget_check(duration)
        if decision is None or not decision.allowed:
            reason = decision.reason if decision is not None else "Provider budget guard is mandatory for Gemini REAL generation."
            return AdapterExecutionResult(
                success=False,
                summary="Gemini REAL generation blocked before HTTP.",
                output={
                    "_real": True,
                    "_blocked_by_budget": True,
                    "provider_control": decision.to_dict() if decision is not None else {},
                },
                error=reason,
            )

        task = str(request.params.get("task", "text_to_video"))
        input_items: list[dict[str, str]] = [{"type": "text", "text": str(request.params.get("prompt", ""))}]
        image_data = request.params.get("image_base64")
        if image_data:
            input_items.insert(0, {
                "type": "image",
                "data": str(image_data),
                "mime_type": str(request.params.get("image_mime_type", "image/png")),
            })
        aspect_ratio = str(request.params.get("aspect_ratio", "9:16"))
        if aspect_ratio not in {"9:16", "16:9"}:
            aspect_ratio = "9:16"
        body = {
            "model": str(request.params.get("model_id", self.MODEL_ID)),
            "input": input_items,
            "generation_config": {"video_config": {"task": task}},
            "response_format": {"type": "video", "aspect_ratio": aspect_ratio},
        }
        try:
            response = client.post(
                f"{provider.base_url.rstrip('/')}/v1beta/interactions",
                headers={"x-goog-api-key": api_key, "Content-Type": "application/json"},
                body=body,
            )
        except HttpError as exc:
            self._record(duration, False, False, {"http_error": type(exc).__name__})
            return self._failure(str(exc) or type(exc).__name__, real=True, decision=decision)

        payload = response.body if isinstance(response.body, dict) else {}
        video_data = self._video_data(payload)
        success = response.status_code in (200, 201) and bool(video_data)
        file_info = self._write_video(request, video_data) if success else {}
        self._record(duration, success, success, {"model_id": body["model"], "task": task})
        output = {
            "_real": True,
            "model_id": body["model"],
            "duration_seconds": duration,
            "task": task,
            "aspect_ratio": aspect_ratio,
            "resolution": "720p",
            "fps": 24,
            "provider_control": decision.to_dict(),
            **file_info,
        }
        return AdapterExecutionResult(
            success=success,
            summary=f"Gemini Omni Flash generated {duration}s video" if success else "Gemini Omni Flash returned no video",
            output=output,
            error="" if success else f"HTTP {response.status_code} or missing output video",
        )

    def _duration(self, request: ToolRequest) -> int:
        value = int(request.params.get("duration_seconds", 8))
        return min(10, max(3, value))

    def _resolve_credential(self) -> str:
        if self._secret_provider is not None:
            from core.tools.secrets.models import SecretKey
            for secret_key in (
                SecretKey(key="api_key", tool_id=self.adapter_id),
                SecretKey(key="api_key", provider="gemini_omni_flash"),
            ):
                secret = self._secret_provider.get(secret_key)
                if secret is not None:
                    return secret.value
        return str(self._config.get("api_key", ""))

    def _budget_check(self, duration: int) -> ProviderBudgetDecision | None:
        if self._budget_guard is None:
            return None
        return self._budget_guard.check(
            provider="gemini_omni_flash",
            operation="generate_video",
            units=duration,
            unit_name="seconds",
        )

    def _record(self, duration: int, success: bool, billable: bool, metadata: dict[str, Any]) -> None:
        if self._budget_guard is not None:
            self._budget_guard.record_usage(
                provider="gemini_omni_flash",
                operation="generate_video",
                mode=self._execution_mode.value,
                units=duration,
                unit_name="seconds",
                success=success,
                billable=billable,
                metadata=metadata,
            )

    @staticmethod
    def _video_data(payload: dict[str, Any]) -> str:
        steps = payload.get("steps")
        if isinstance(steps, list):
            for step in steps:
                if not isinstance(step, dict) or step.get("type") != "model_output":
                    continue
                content = step.get("content")
                if not isinstance(content, list):
                    continue
                for item in content:
                    if (
                        isinstance(item, dict)
                        and item.get("type") == "video"
                        and isinstance(item.get("data"), str)
                    ):
                        return item["data"]
        # Kept for SDK-shaped test doubles and backward compatibility.
        output_video = payload.get("output_video")
        if isinstance(output_video, dict) and isinstance(output_video.get("data"), str):
            return output_video["data"]
        return ""

    def _write_video(self, request: ToolRequest, data: str) -> dict[str, Any]:
        output_dir = Path(str(request.params.get("output_dir", "output/gemini_omni")))
        output_dir.mkdir(parents=True, exist_ok=True)
        raw_stem = str(request.params.get("task_id", request.tool_id))
        stem = "".join(ch if ch.isalnum() or ch in "-_" else "_" for ch in raw_stem) or "video"
        output_path = output_dir / f"{stem}.mp4"
        output_path.write_bytes(base64.b64decode(data, validate=True))
        return {
            "file_path": str(output_path.resolve()),
            "file_size_bytes": output_path.stat().st_size,
            "physical_asset": True,
        }

    @staticmethod
    def _failure(message: str, *, real: bool = False, decision: ProviderBudgetDecision | None = None) -> AdapterExecutionResult:
        output: dict[str, Any] = {"_real": real}
        if decision is not None:
            output["provider_control"] = decision.to_dict()
        return AdapterExecutionResult(success=False, summary="", output=output, error=message)
