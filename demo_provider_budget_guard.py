"""Provider budget guard demo.

Proves controlled REAL provider usage without calling paid APIs:
- owner approval is required;
- approved usage records billable character estimates;
- unit/cost/request budgets block before HTTP is sent.
"""

from __future__ import annotations

from uuid import uuid4

from core.tools import (
    ElevenLabsAdapter,
    ElevenLabsProvider,
    ExecutionMode,
    HttpResponse,
    MockHttpClient,
    ProviderBudget,
    ProviderBudgetGuard,
    ProviderPricing,
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


def _adapter(guard: ProviderBudgetGuard) -> tuple[ElevenLabsAdapter, MockHttpClient]:
    http = MockHttpClient(
        default_response=HttpResponse(
            status_code=200,
            headers={"content-type": "audio/mpeg"},
            body=b"mock-real-audio-bytes",
        )
    )
    adapter = ElevenLabsAdapter()
    adapter.configure({"api_key": "mock_api_key"})
    adapter.authenticate()
    adapter.mark_ready()
    adapter.set_execution_mode(ExecutionMode.REAL)
    adapter.set_provider(ElevenLabsProvider())
    adapter.set_http_client(http)
    adapter.set_budget_guard(guard)
    return adapter, http


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
    print("=" * 66)
    print("Provider Budget Guard - Controlled REAL Provider Usage")
    print("=" * 66)

    print("\n" + "-" * 66)
    print("Scenario 1: Owner approval required")
    print("-" * 66)
    guard = ProviderBudgetGuard(
        budgets=(ProviderBudget(provider="elevenlabs", owner_approved=False, max_units=1000),),
        pricing=(ProviderPricing(provider="elevenlabs", operation="synthesize", unit_name="characters", unit_cost_usd=0.0001),),
    )
    adapter, http = _adapter(guard)
    blocked = adapter.execute(_request("blocked because owner approval is missing"))
    _check(not blocked.success, "REAL call blocked without owner approval")
    _check(blocked.output["_blocked_by_budget"], "Blocked result marks budget block")
    _check(blocked.output["provider_control"]["owner_approved"] is False, "Decision records missing approval")
    _check(len(http.sent_requests) == 0, "No HTTP request sent when approval is missing")
    _check(len(guard.records()) == 0, "Blocked call does not create billable usage")

    print("\n" + "-" * 66)
    print("Scenario 2: Approved usage within budget")
    print("-" * 66)
    approved_guard = ProviderBudgetGuard(
        budgets=(ProviderBudget(provider="elevenlabs", owner_approved=True, max_units=120, max_cost_usd=0.02, max_requests=2),),
        pricing=(ProviderPricing(provider="elevenlabs", operation="synthesize", unit_name="characters", unit_cost_usd=0.0001),),
    )
    approved_adapter, approved_http = _adapter(approved_guard)
    text = "a" * 100
    ok = approved_adapter.execute(_request(text))
    _check(ok.success, "Approved REAL-mode call succeeds through MockHttpClient")
    _check(len(approved_http.sent_requests) == 1, "One HTTP request sent after approval")
    _check(ok.output["provider_control"]["allowed"], "Provider control decision allowed execution")
    _check(ok.output["characters"] == 100, "Character count preserved in adapter output")
    _check(approved_guard.request_count("elevenlabs") == 1, "Guard records one provider attempt")
    _check(approved_guard.used_units("elevenlabs") == 100, "Guard records billable characters")
    _check(approved_guard.spent_usd("elevenlabs") == 0.01, "Guard records estimated cost")
    summary = approved_guard.summary("elevenlabs")
    _check(summary.requests == 1 and summary.successes == 1, "Summary counts successful request")
    _check(summary.billable_units == 100, "Summary exposes billable units")
    _check(summary.estimated_cost_usd == 0.01, "Summary exposes estimated cost")

    print("\n" + "-" * 66)
    print("Scenario 3: Unit budget blocks before HTTP")
    print("-" * 66)
    unit_block = approved_adapter.execute(_request("b" * 30))
    _check(not unit_block.success, "Second call blocked by remaining unit budget")
    _check("unit budget" in unit_block.error.lower(), "Unit budget reason returned")
    _check(len(approved_http.sent_requests) == 1, "Blocked unit budget sends no extra HTTP")
    _check(approved_guard.request_count("elevenlabs") == 1, "Blocked unit call is not counted as provider request")

    print("\n" + "-" * 66)
    print("Scenario 4: Cost and request budgets block")
    print("-" * 66)
    cost_guard = ProviderBudgetGuard(
        budgets=(ProviderBudget(provider="elevenlabs", owner_approved=True, max_cost_usd=0.004, max_requests=5),),
        pricing=(ProviderPricing(provider="elevenlabs", operation="synthesize", unit_name="characters", unit_cost_usd=0.0001),),
    )
    cost_adapter, cost_http = _adapter(cost_guard)
    cost_block = cost_adapter.execute(_request("c" * 50))
    _check(not cost_block.success, "Call blocked by max cost before HTTP")
    _check("cost budget" in cost_block.error.lower(), "Cost budget reason returned")
    _check(len(cost_http.sent_requests) == 0, "Cost block sends no HTTP")

    request_guard = ProviderBudgetGuard(
        budgets=(ProviderBudget(provider="elevenlabs", owner_approved=True, max_units=1000, max_requests=1),),
        pricing=(ProviderPricing(provider="elevenlabs", operation="synthesize", unit_name="characters", unit_cost_usd=0.0001),),
    )
    request_adapter, request_http = _adapter(request_guard)
    first = request_adapter.execute(_request("first request"))
    second = request_adapter.execute(_request("second request"))
    _check(first.success, "First request within max_requests succeeds")
    _check(not second.success, "Second request blocked by request budget")
    _check(len(request_http.sent_requests) == 1, "Request budget block sends no second HTTP")
    _check(request_guard.summary("elevenlabs").requests == 1, "Summary keeps one attempted provider request")

    print(f"\n{'=' * 66}")
    print(f"All {_ASSERTION_COUNTER} assertions passed.")
    print(f"{'=' * 66}")


if __name__ == "__main__":
    main()
