"""Regression demo for provider quotes that never execute providers."""

from core.tools.provider_quote import MediaProviderQuotePlanner


def main() -> None:
    planner = MediaProviderQuotePlanner()
    local, hybrid = planner.quote(script="palavra " * 104)

    assert local.plan_id == "local_free"
    assert local.estimated_duration_seconds == 40
    assert local.estimated_cost_usd == 0.0
    assert local.complete_price is True
    assert local.executable_now is True
    assert len(local.items) == 3
    assert all(item.available for item in local.items)
    assert {item.department for item in local.items} == {"audio", "image", "video"}
    assert local.items[0].provider == "kokoro_local"
    assert local.items[1].provider == "owned_source_assets"
    assert local.items[2].provider == "hyperframes_ffmpeg"
    assert "aprovação separada" in local.warning

    assert hybrid.plan_id == "hybrid_quality"
    assert hybrid.estimated_duration_seconds == 40
    assert hybrid.estimated_cost_usd == 4.0
    assert hybrid.complete_price is False
    assert hybrid.executable_now is False
    assert len(hybrid.items) == 3
    assert all(not item.available for item in hybrid.items)
    assert hybrid.items[0].pricing_status == "billing_blocked_quote_pending"
    assert hybrid.items[1].pricing_status == "provider_not_selected"
    assert hybrid.items[2].pricing_status == "official_estimate"
    assert hybrid.items[2].metadata["estimated_requests"] == 4
    assert hybrid.items[2].metadata["max_clip_seconds"] == 10
    assert hybrid.items[2].metadata["pricing_source"].startswith("https://ai.google.dev/")
    assert "Estimativa parcial" in hybrid.warning

    payload = hybrid.to_dict()
    assert payload["plan_id"] == "hybrid_quality"
    assert payload["items"][2]["estimated_cost_usd"] == 4.0
    assert payload["items"][2]["metadata"]["estimated_requests"] == 4

    short = planner.quote(script="curto", target_duration_seconds=8)[1]
    assert short.estimated_duration_seconds == 8
    assert short.estimated_cost_usd == 0.8
    assert short.items[2].metadata["estimated_requests"] == 1

    capped = planner.quote(script="x " * 1000)[1]
    assert capped.estimated_duration_seconds == 60
    assert capped.estimated_cost_usd == 6.0
    assert capped.items[2].metadata["estimated_requests"] == 6

    print("All 35 assertions passed.")


if __name__ == "__main__":
    main()
