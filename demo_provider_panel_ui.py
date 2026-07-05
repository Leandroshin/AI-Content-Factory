"""Provider settings panel demo.

Generates a local HTML preview from ProviderControlCenter.dashboard_state()
without external API calls or raw secret exposure.
"""

from __future__ import annotations

from pathlib import Path
from uuid import uuid4

from core.tools import (
    ElevenLabsAdapter,
    ElevenLabsProvider,
    ExecutionMode,
    HttpResponse,
    MockHttpClient,
    MockSecretProvider,
    ProviderBudget,
    ProviderControlCenter,
    ProviderControlProfile,
    ProviderPanelRenderer,
    ProviderPricing,
    ProviderSecretSlot,
    ToolRequest,
)


_ASSERTION_COUNTER: int = 0


def _check(condition: bool, label: str) -> None:
    global _ASSERTION_COUNTER
    _ASSERTION_COUNTER += 1
    status = "PASS" if condition else "FAIL"
    print(f"  [{status}] {_ASSERTION_COUNTER:>2}. {label}")
    if not condition:
        raise AssertionError(label)


def _adapter(center: ProviderControlCenter, http: MockHttpClient) -> ElevenLabsAdapter:
    adapter = ElevenLabsAdapter()
    adapter.configure({"api_key": "configured_via_secret_provider"})
    adapter.authenticate()
    adapter.mark_ready()
    adapter.set_provider(ElevenLabsProvider())
    adapter.set_http_client(http)
    center.apply_to_elevenlabs(adapter)
    return adapter


def _request(text: str) -> ToolRequest:
    return ToolRequest(
        tool_id=uuid4(),
        capability="speech_generation",
        params={
            "action": "synthesize",
            "text": text,
            "voice_id": "voice_narrator_pt_br",
            "model_id": "mock_multilingual_v2",
            "output_format": "mp3",
        },
    )


def _register_visual_profiles(center: ProviderControlCenter) -> None:
    image_profile = ProviderControlProfile(
        provider="image_generation",
        display_name="Image Generator",
        category="image",
        execution_mode=ExecutionMode.MOCK,
        budget=ProviderBudget(
            provider="image_generation",
            owner_approved=False,
            max_cost_usd=3.0,
            max_units=200,
            max_requests=50,
            notes="Future image provider budget for covers and visual assets.",
        ),
        pricing=(ProviderPricing(
            provider="image_generation",
            operation="generate_image",
            unit_name="images",
            unit_cost_usd=0.04,
            pricing_note="Planning estimate until the final image provider is chosen.",
        ),),
        secret_slots=(ProviderSecretSlot(
            key="image_api_key",
            label="Image Provider API Key",
            required=True,
        ),),
        metadata={"capabilities": ("image_generation", "thumbnail_design")},
    )
    center.register_profile(image_profile)
    center.mark_secret_configured("image_generation", "image_api_key", "img...ok")

    video_profile = ProviderControlProfile(
        provider="video_generation",
        display_name="Video Generator",
        category="video",
        execution_mode=ExecutionMode.REAL,
        budget=ProviderBudget(
            provider="video_generation",
            owner_approved=False,
            max_cost_usd=5.0,
            max_units=10,
            max_requests=5,
            notes="Future text-to-video provider budget; approval still required.",
        ),
        pricing=(ProviderPricing(
            provider="video_generation",
            operation="text_to_video",
            unit_name="clips",
            unit_cost_usd=0.5,
            pricing_note="Planning estimate until the final video provider is chosen.",
        ),),
        secret_slots=(ProviderSecretSlot(
            key="video_api_key",
            label="Video Provider API Key",
            required=True,
        ),),
        metadata={"capabilities": ("text_to_video", "video_generation")},
    )
    center.register_profile(video_profile)


def main() -> None:
    print("=" * 70)
    print("Provider Panel UI - Interactive Preview")
    print("=" * 70)

    secrets = MockSecretProvider()
    center = ProviderControlCenter(secret_provider=secrets)

    print("\n" + "-" * 70)
    print("Step 1: Build provider control state")
    print("-" * 70)
    center.register_elevenlabs(
        unit_cost_usd=0.0001,
        max_cost_usd=0.05,
        max_units=1000,
        max_requests=5,
        execution_mode=ExecutionMode.MOCK,
    )
    center.set_secret("elevenlabs", "api_key", "sk_mock_1234567890")
    center.set_execution_mode("elevenlabs", ExecutionMode.REAL)
    center.approve_provider("elevenlabs", True)
    _register_visual_profiles(center)

    dashboard = center.dashboard_state()
    _check(dashboard["total_providers"] == 3, "Dashboard exposes three provider profiles")
    _check(dashboard["ready_real_providers"] == ("elevenlabs",), "Only ElevenLabs is REAL-ready")

    providers = {p["provider"]: p for p in dashboard["providers"]}
    _check(providers["elevenlabs"]["status"] == "real_ready", "ElevenLabs is ready for REAL mode")
    _check(providers["image_generation"]["status"] == "safe_mock", "Image provider stays safe in MOCK")
    _check(
        providers["video_generation"]["status"] == "missing_credentials",
        "Video provider is blocked before key and approval",
    )

    print("\n" + "-" * 70)
    print("Step 2: Simulate approved REAL usage through the adapter")
    print("-" * 70)
    http = MockHttpClient(
        default_response=HttpResponse(
            status_code=200,
            headers={"content-type": "audio/mpeg"},
            body=b"mock-real-audio",
        )
    )
    adapter = _adapter(center, http)
    result = adapter.execute(_request("Narracao curta para validar custos do painel."))
    _check(result.success, "Approved REAL request succeeds through MockHttpClient")
    _check(len(http.sent_requests) == 1, "Mock HTTP received one request")
    _check(result.output["provider_control"]["allowed"], "Provider budget allowed execution")

    dashboard = center.dashboard_state()
    providers = {p["provider"]: p for p in dashboard["providers"]}
    eleven_usage = providers["elevenlabs"]["usage_summary"]
    _check(eleven_usage["requests"] == 1, "Dashboard usage counts one ElevenLabs request")
    _check(eleven_usage["billable_units"] > 0, "Dashboard usage includes billable units")
    _check(eleven_usage["estimated_cost_usd"] > 0, "Dashboard usage includes estimated cost")

    print("\n" + "-" * 70)
    print("Step 3: Render local HTML panel")
    print("-" * 70)
    html = ProviderPanelRenderer.render_html(dashboard)
    output_dir = Path("output/provider_control_panel")
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / "index.html"
    output_path.write_text(html, encoding="utf-8")

    _check("<title>AI Content Factory - APIs e Custos</title>" in html, "HTML has expected title")
    _check("ElevenLabs" in html, "HTML renders ElevenLabs card")
    _check("Image Generator" in html, "HTML renders image provider card")
    _check("Video Generator" in html, "HTML renders video provider card")
    _check("Nenhuma API real roda sem aprovacao" in html, "HTML shows REAL execution safety warning")
    _check("MOCK" in html and "REAL" in html, "HTML shows execution mode toggle labels")
    _check("Snapshot usado pela UI" in html, "HTML exposes UI snapshot section")
    _check("window.__providerDashboard" in html, "HTML embeds safe dashboard state for browser interactions")
    _check('id="provider-search"' in html, "HTML includes provider search control")
    _check('id="filter-blocked"' in html, "HTML includes blocked-provider filter")
    _check("data-provider-row" in html, "HTML rows are selectable provider controls")
    _check('id="provider-detail"' in html, "HTML includes selected-provider detail panel")
    _check("function renderProviderDetail" in html, "HTML includes interactive detail renderer")
    _check("Simular uso local" in html, "HTML includes local usage simulation control")
    _check('data-tab="auditoria"' in html, "HTML includes interactive audit tab")
    _check("sk_mock_1234567890" not in html, "HTML does not expose raw secret")
    _check("sk...90" in html, "HTML exposes only masked secret hint")
    _check(output_path.exists(), "HTML preview file was written")
    _check(output_path.stat().st_size > 10000, "HTML preview has substantial UI content")

    print(f"\nPreview written to: {output_path.resolve()}")
    print(f"\n{'=' * 70}")
    print(f"All {_ASSERTION_COUNTER} assertions passed.")
    print(f"{'=' * 70}")


if __name__ == "__main__":
    main()
