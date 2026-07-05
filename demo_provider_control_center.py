"""Provider control-center demo.

Proves the settings-panel backend for API keys, MOCK/REAL mode, budgets,
approval, and adapter wiring without using external services.
"""

from __future__ import annotations

from uuid import uuid4

from core.tools import (
    ElevenLabsAdapter,
    ElevenLabsProvider,
    ExecutionMode,
    HttpResponse,
    MockHttpClient,
    MockSecretProvider,
    ProviderControlCenter,
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


def main() -> None:
    print("=" * 70)
    print("Provider Control Center - Settings Panel Backend")
    print("=" * 70)

    secrets = MockSecretProvider()
    center = ProviderControlCenter(secret_provider=secrets)

    print("\n" + "-" * 70)
    print("Step 1: Register ElevenLabs in safe MOCK mode")
    print("-" * 70)
    center.register_elevenlabs(unit_cost_usd=0.0001, max_cost_usd=0.02, max_units=120, max_requests=2)
    snap = center.snapshot("elevenlabs")
    _check(snap.provider == "elevenlabs", "ElevenLabs profile registered")
    _check(snap.execution_mode == "mock", "Default mode is MOCK")
    _check(snap.status == "safe_mock", "MOCK provider status is safe")
    _check(not snap.can_execute_real, "MOCK profile cannot execute REAL")
    _check(snap.missing_secret_keys == ("api_key",), "API key is missing")
    _check(snap.max_units == 120 and snap.max_requests == 2, "Budget limits visible")

    print("\n" + "-" * 70)
    print("Step 2: Secret configuration is UI-safe")
    print("-" * 70)
    center.set_secret("elevenlabs", "api_key", "sk_mock_1234567890")
    snap = center.snapshot("elevenlabs")
    _check(snap.configured_secret_keys == ("api_key",), "API key marked configured")
    _check(snap.missing_secret_keys == (), "No missing secret keys")
    dashboard = center.dashboard_state()
    dashboard_text = str(dashboard)
    _check("sk_mock_1234567890" not in dashboard_text, "Dashboard state does not expose raw secret")
    _check("sk...90" in dashboard_text, "Dashboard state can expose masked secret hint indirectly")

    print("\n" + "-" * 70)
    print("Step 3: REAL mode still requires owner approval")
    print("-" * 70)
    center.set_execution_mode("elevenlabs", ExecutionMode.REAL)
    snap = center.snapshot("elevenlabs")
    _check(snap.execution_mode == "real", "Provider mode switched to REAL")
    _check(snap.status == "awaiting_owner_approval", "REAL mode awaits owner approval")
    _check(not snap.can_execute_real, "Cannot execute REAL before approval")

    print("\n" + "-" * 70)
    print("Step 4: Approval requires an explicit budget")
    print("-" * 70)
    no_limit_center = ProviderControlCenter(secret_provider=MockSecretProvider())
    no_limit_center.register_elevenlabs(unit_cost_usd=0.0001)
    blocked_approval = False
    try:
        no_limit_center.approve_provider("elevenlabs", True)
    except ValueError:
        blocked_approval = True
    _check(blocked_approval, "Owner approval without budget limits is rejected")

    approved = center.approve_provider("elevenlabs", True)
    _check(approved.budget is not None and approved.budget.owner_approved, "Owner approval recorded")
    snap = center.snapshot("elevenlabs")
    _check(snap.status == "real_ready", "Provider is REAL-ready")
    _check(snap.can_execute_real, "Provider can execute REAL after key + budget + approval")

    print("\n" + "-" * 70)
    print("Step 5: Adapter receives settings and budget guard")
    print("-" * 70)
    http = MockHttpClient(
        default_response=HttpResponse(
            status_code=200,
            headers={"content-type": "audio/mpeg"},
            body=b"mock-real-audio",
        )
    )
    adapter = _adapter(center, http)
    result = adapter.execute(_request("a" * 100))
    _check(result.success, "Configured adapter executes approved REAL request")
    _check(len(http.sent_requests) == 1, "Approved REAL request sends HTTP")
    _check(result.output["provider_control"]["allowed"], "Adapter output includes budget approval")

    snap = center.snapshot("elevenlabs")
    _check(snap.usage_summary is not None, "Usage summary attached to snapshot")
    assert snap.usage_summary is not None
    _check(snap.usage_summary.requests == 1, "Usage summary counts one request")
    _check(snap.usage_summary.billable_units == 100, "Usage summary counts billable units")
    _check(snap.usage_summary.estimated_cost_usd == 0.01, "Usage summary estimates cost")

    print("\n" + "-" * 70)
    print("Step 6: Dashboard state reflects usage and budget block")
    print("-" * 70)
    blocked = adapter.execute(_request("b" * 30))
    _check(not blocked.success, "Second request blocked by remaining unit budget")
    _check(len(http.sent_requests) == 1, "Blocked request sends no HTTP")

    dashboard = center.dashboard_state()
    providers = dashboard["providers"]
    _check(len(providers) == 1, "Dashboard exposes one provider card")
    card = providers[0]
    _check(card["provider"] == "elevenlabs", "Dashboard provider key correct")
    _check(card["status"] == "real_ready", "Dashboard status remains real_ready")
    _check(card["usage_summary"]["requests"] == 1, "Dashboard usage requests visible")
    _check(card["usage_summary"]["estimated_cost_usd"] == 0.01, "Dashboard usage cost visible")
    _check(dashboard["ready_real_providers"] == ("elevenlabs",), "Dashboard lists REAL-ready provider")

    print(f"\n{'=' * 70}")
    print(f"All {_ASSERTION_COUNTER} assertions passed.")
    print(f"{'=' * 70}")


if __name__ == "__main__":
    main()
