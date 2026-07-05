"""Foundation demo for LLMCostTracker.

Validates aggregation, breakdown by provider/model, token statistics,
latency, and deterministic behaviour — all with no external deps.
"""

from __future__ import annotations

from uuid import uuid4

from core.llm.cost_tracker import LLMCostTracker, LLMUsage


def _make_usage(
    provider: str,
    model: str,
    prompt: int,
    completion: int,
    cost: float,
    latency: float = 100.0,
) -> LLMUsage:
    return LLMUsage.from_response(
        request_id=uuid4(),
        provider=provider,
        model=model,
        prompt_tokens=prompt,
        completion_tokens=completion,
        estimated_cost=cost,
        latency_ms=latency,
    )


# ------------------------------------------------------------------
# Scenario 1: Single usage record summary
# ------------------------------------------------------------------


def scenario_single_usage() -> None:
    """Summarize a single usage record."""
    usage = _make_usage("openai", "gpt-4o", 100, 50, 0.015, 200.0)
    summary = LLMCostTracker.summarize([usage])

    assert summary.total_requests == 1
    assert summary.total_prompt_tokens == 100
    assert summary.total_completion_tokens == 50
    assert summary.total_tokens == 150
    assert summary.total_estimated_cost == 0.015
    assert summary.average_latency_ms == 200.0
    print(f"[PASS] single_usage                   | requests={summary.total_requests} "
          f"tokens={summary.total_tokens} cost=${summary.total_estimated_cost}")


# ------------------------------------------------------------------
# Scenario 2: Multiple providers
# ------------------------------------------------------------------


def scenario_multiple_providers() -> None:
    """Aggregate records from different providers."""
    usages = [
        _make_usage("openai", "gpt-4o", 100, 50, 0.015),
        _make_usage("gemini", "gemini-pro", 200, 100, 0.005),
        _make_usage("openai", "gpt-4o-mini", 50, 25, 0.002),
    ]
    summary = LLMCostTracker.summarize(usages)

    assert summary.total_requests == 3
    assert summary.total_tokens == 525
    assert "openai" in summary.usage_per_provider
    assert "gemini" in summary.usage_per_provider
    print(f"[PASS] multiple_providers             | providers={list(summary.usage_per_provider.keys())} "
          f"requests={summary.total_requests}")


# ------------------------------------------------------------------
# Scenario 3: Cost per provider
# ------------------------------------------------------------------


def scenario_cost_per_provider() -> None:
    """Cost breakdown by provider."""
    usages = [
        _make_usage("openai", "gpt-4o", 100, 50, 0.015),
        _make_usage("openai", "gpt-4o-mini", 50, 25, 0.002),
        _make_usage("gemini", "gemini-pro", 200, 100, 0.005),
    ]
    costs = LLMCostTracker.cost_per_provider(usages)

    assert costs["openai"] == 0.017
    assert costs["gemini"] == 0.005
    assert len(costs) == 2
    print(f"[PASS] cost_per_provider              | openai=${costs['openai']} "
          f"gemini=${costs['gemini']}")


# ------------------------------------------------------------------
# Scenario 4: Cost per model
# ------------------------------------------------------------------


def scenario_cost_per_model() -> None:
    """Cost breakdown by model."""
    usages = [
        _make_usage("openai", "gpt-4o", 100, 50, 0.015),
        _make_usage("openai", "gpt-4o-mini", 50, 25, 0.002),
        _make_usage("gemini", "gemini-pro", 200, 100, 0.005),
    ]
    costs = LLMCostTracker.cost_per_model(usages)

    assert costs["gpt-4o"] == 0.015
    assert costs["gpt-4o-mini"] == 0.002
    assert costs["gemini-pro"] == 0.005
    assert len(costs) == 3
    print(f"[PASS] cost_per_model                 | gpt-4o=${costs['gpt-4o']} "
          f"gpt-4o-mini=${costs['gpt-4o-mini']} gemini-pro=${costs['gemini-pro']}")


# ------------------------------------------------------------------
# Scenario 5: Token statistics
# ------------------------------------------------------------------


def scenario_token_statistics() -> None:
    """Aggregated token counts."""
    usages = [
        _make_usage("openai", "gpt-4o", 100, 50, 0.0),
        _make_usage("gemini", "gemini-pro", 200, 100, 0.0),
    ]
    stats = LLMCostTracker.token_statistics(usages)

    assert stats["total_prompt"] == 300
    assert stats["total_completion"] == 150
    assert stats["total"] == 450
    print(f"[PASS] token_statistics               | prompt={stats['total_prompt']} "
          f"completion={stats['total_completion']} total={stats['total']}")


# ------------------------------------------------------------------
# Scenario 6: Average latency
# ------------------------------------------------------------------


def scenario_average_latency() -> None:
    """Mean latency calculation."""
    usages = [
        _make_usage("openai", "gpt-4o", 10, 5, 0.0, latency=150.0),
        _make_usage("openai", "gpt-4o-mini", 10, 5, 0.0, latency=50.0),
    ]
    avg = LLMCostTracker.average_latency(usages)

    assert avg == 100.0
    print(f"[PASS] average_latency                | avg={avg}ms")


# ------------------------------------------------------------------
# Scenario 7: Empty list
# ------------------------------------------------------------------


def scenario_empty() -> None:
    """All methods handle empty input gracefully."""
    empty: list[LLMUsage] = []

    summary = LLMCostTracker.summarize(empty)
    assert summary.total_requests == 0
    assert summary.total_tokens == 0
    assert summary.total_estimated_cost == 0.0

    assert LLMCostTracker.cost_per_provider(empty) == {}
    assert LLMCostTracker.cost_per_model(empty) == {}
    assert LLMCostTracker.token_statistics(empty) == {"total_prompt": 0, "total_completion": 0, "total": 0}
    assert LLMCostTracker.average_latency(empty) == 0.0
    print(f"[PASS] empty                          | all methods handle empty gracefully")


# ------------------------------------------------------------------
# Scenario 8: Deterministic — same input → same output
# ------------------------------------------------------------------


def scenario_deterministic() -> None:
    """Same usage list always produces identical summaries."""
    usages = [
        _make_usage("openai", "gpt-4o", 50, 25, 0.0075),
        _make_usage("gemini", "gemini-pro", 100, 50, 0.0025),
    ]

    s1 = LLMCostTracker.summarize(usages)
    s2 = LLMCostTracker.summarize(usages)
    s3 = LLMCostTracker.summarize(usages)

    assert s1.total_estimated_cost == s2.total_estimated_cost == s3.total_estimated_cost
    assert s1.average_latency_ms == s2.average_latency_ms
    assert s1.usage_per_provider == s2.usage_per_provider
    print(f"[PASS] deterministic                  | cost=${s1.total_estimated_cost} "
          f"(3 identical summaries)")


# ------------------------------------------------------------------
# Scenario 9: Per-provider breakdown in summary
# ------------------------------------------------------------------


def scenario_summary_per_provider() -> None:
    """summary.usage_per_provider contains correct tuples."""
    usages = [
        _make_usage("openai", "gpt-4o", 100, 50, 0.015),
        _make_usage("openai", "gpt-4o-mini", 50, 25, 0.002),
        _make_usage("gemini", "gemini-pro", 200, 100, 0.005),
    ]
    summary = LLMCostTracker.summarize(usages)

    openai_data = summary.usage_per_provider["openai"]
    assert openai_data[0] == 2  # requests
    assert openai_data[1] == 225  # tokens (150 + 75)
    assert openai_data[2] == 0.017  # cost

    gemini_data = summary.usage_per_provider["gemini"]
    assert gemini_data[0] == 1
    assert gemini_data[1] == 300
    assert gemini_data[2] == 0.005
    print(f"[PASS] summary_per_provider           | openai={openai_data} "
          f"gemini={gemini_data}")


# ------------------------------------------------------------------
# Scenario 10: Large number of records
# ------------------------------------------------------------------


def scenario_large_batch() -> None:
    """Aggregation scales correctly with many records."""
    usages = [
        _make_usage("openai", "gpt-4o", 10, 5, 0.001, latency=50.0)
        for _ in range(100)
    ]
    summary = LLMCostTracker.summarize(usages)

    assert summary.total_requests == 100
    assert summary.total_prompt_tokens == 1000
    assert summary.total_completion_tokens == 500
    assert summary.total_tokens == 1500
    assert summary.total_estimated_cost == 0.1
    assert summary.average_latency_ms == 50.0
    print(f"[PASS] large_batch                    | requests={summary.total_requests} "
          f"tokens={summary.total_tokens} cost=${summary.total_estimated_cost}")


# ------------------------------------------------------------------
# Main
# ------------------------------------------------------------------


def main() -> None:
    print("=" * 62)
    print("LLM CostTracker Demo")
    print("=" * 62)
    print()

    scenario_single_usage()
    scenario_multiple_providers()
    scenario_cost_per_provider()
    scenario_cost_per_model()
    scenario_token_statistics()
    scenario_average_latency()
    scenario_empty()
    scenario_deterministic()
    scenario_summary_per_provider()
    scenario_large_batch()

    print()
    print("=" * 62)
    print("All CostTracker scenarios passed.")
    print("=" * 62)


if __name__ == "__main__":
    main()
