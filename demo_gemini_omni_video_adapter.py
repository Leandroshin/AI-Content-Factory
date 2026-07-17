"""Demonstrate Gemini Omni Flash MOCK/REAL budget safety."""

from __future__ import annotations

import base64
from pathlib import Path
from tempfile import TemporaryDirectory
from uuid import uuid4

from core.tools.adapters import ExecutionMode, GeminiOmniVideoAdapter, ToolRequest
from core.tools.http import HttpResponse, MockHttpClient
from core.tools.provider_control import ProviderBudget, ProviderBudgetGuard, ProviderPricing
from core.tools.provider_settings import ProviderControlCenter
from core.tools.providers import GeminiProvider
from core.tools.secrets import MockSecretProvider


COUNT = 0


def check(condition: bool, label: str) -> None:
    global COUNT
    COUNT += 1
    if not condition:
        raise AssertionError(label)


def request(output_dir: str = "") -> ToolRequest:
    return ToolRequest(
        tool_id=uuid4(),
        capability="video_generation",
        params={
            "prompt": "Original product rotates on a clean table.",
            "duration_seconds": 8,
            "task": "text_to_video",
            "task_id": "omni-safe-smoke",
            "output_dir": output_dir,
        },
    )


def main() -> None:
    secrets = MockSecretProvider()
    center = ProviderControlCenter(secret_provider=secrets)
    profile = center.register_gemini_omni()
    check(profile.execution_mode == ExecutionMode.MOCK, "Provider defaults to MOCK")
    check(profile.metadata["free_tier"] is False, "Paid-only status is explicit")
    center.set_secret("gemini_omni_flash", "api_key", "test_key_long_enough_for_adapter")
    snapshot = center.snapshot("gemini_omni_flash")
    check(snapshot.configured_secret_keys == ("api_key",), "Control center masks configured key")
    check(not snapshot.can_execute_real, "REAL remains blocked without approval and budget")

    adapter = GeminiOmniVideoAdapter()
    mock = adapter.execute(request())
    check(mock.success, "MOCK succeeds")
    check(mock.output["estimated_cost_usd"] == 0.8, "MOCK exposes estimate")
    check(not mock.output["_real"], "MOCK is explicit")

    adapter.set_provider(GeminiProvider())
    client = MockHttpClient(default_response=HttpResponse(
        status_code=200,
        body={"steps": [{
            "type": "model_output",
            "content": [{
                "type": "video",
                "mime_type": "video/mp4",
                "data": base64.b64encode(b"fake-mp4").decode("ascii"),
            }],
        }]},
    ))
    adapter.set_http_client(client)
    center.apply_to_gemini_omni(adapter)
    adapter.set_execution_mode(ExecutionMode.REAL)
    blocked = adapter.execute(request())
    check(not blocked.success, "REAL blocks without budget guard")
    check(blocked.output["_blocked_by_budget"], "Block is auditable")
    check(len(client.sent_requests) == 0, "No HTTP before approval")

    guard = ProviderBudgetGuard(
        budgets=(ProviderBudget(
            provider="gemini_omni_flash",
            owner_approved=True,
            max_cost_usd=0.80,
            max_units=8,
            max_requests=1,
        ),),
        pricing=(ProviderPricing(
            provider="gemini_omni_flash",
            operation="generate_video",
            unit_name="seconds",
            unit_cost_usd=0.10,
            pricing_note="Official effective 720p preview price on 2026-07-13.",
        ),),
    )
    adapter.set_budget_guard(guard)
    with TemporaryDirectory() as temp_dir:
        result = adapter.execute(request(temp_dir))
        check(result.success, "Approved REAL contract succeeds with mock HTTP")
        check(result.output["provider_control"]["estimated_cost_usd"] == 0.8, "Cost is preflighted")
        check(Path(result.output["file_path"]).read_bytes() == b"fake-mp4", "Physical MP4 response is written")
    check(len(client.sent_requests) == 1, "Exactly one approved HTTP request")
    check("x-goog-api-key" in client.last_request().headers, "API key uses header")
    check("key=" not in client.last_request().url, "API key is absent from URL")
    check(client.last_request().body["response_format"]["aspect_ratio"] == "9:16", "TikTok output defaults to 9:16")
    check(guard.summary("gemini_omni_flash").estimated_cost_usd == 0.8, "Usage summary records estimate")
    print(f"All {COUNT} assertions passed.")


if __name__ == "__main__":
    main()
