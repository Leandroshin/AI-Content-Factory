"""Provider-agnostic cost and usage tracking for LLM calls.

LLMCostTracker is a stateless utility that receives usage data
and produces aggregated metrics. It has no knowledge of any
specific provider's pricing — each provider adapter is
responsible for estimating its own costs.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any
from uuid import UUID, uuid4
import time


# ------------------------------------------------------------------
# LLMUsage
# ------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class LLMUsage:
    """Immutable usage record for a single LLM request.

    Attributes:
        request_id: Unique identifier for the request.
        provider: Provider name (e.g. "openai", "gemini").
        model: Model identifier (e.g. "gpt-4o", "gemini-2.0-flash").
        prompt_tokens: Number of input/prompt tokens consumed.
        completion_tokens: Number of output/completion tokens generated.
        total_tokens: Total tokens (prompt + completion).
        estimated_cost: Estimated cost in USD (set by the provider adapter).
        latency_ms: Request latency in milliseconds.
        timestamp: Unix timestamp of when the request completed.
    """

    request_id: UUID
    provider: str
    model: str
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0
    estimated_cost: float = 0.0
    latency_ms: float = 0.0
    timestamp: float = 0.0

    @staticmethod
    def from_response(
        provider: str,
        model: str,
        prompt_tokens: int,
        completion_tokens: int,
        estimated_cost: float = 0.0,
        latency_ms: float = 0.0,
        request_id: UUID | None = None,
    ) -> LLMUsage:
        """Factory that auto-generates request_id and timestamp."""
        return LLMUsage(
            request_id=request_id or uuid4(),
            provider=provider,
            model=model,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            total_tokens=prompt_tokens + completion_tokens,
            estimated_cost=estimated_cost,
            latency_ms=latency_ms,
            timestamp=time.time(),
        )


# ------------------------------------------------------------------
# LLMCostSummary
# ------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class LLMCostSummary:
    """Immutable aggregated summary of multiple LLM usage records.

    Attributes:
        total_requests: Number of requests included.
        total_prompt_tokens: Sum of all prompt tokens.
        total_completion_tokens: Sum of all completion tokens.
        total_tokens: Sum of all tokens.
        total_estimated_cost: Sum of all estimated costs in USD.
        average_latency_ms: Mean latency across all requests.
        usage_per_provider: Dict mapping provider name to
                            (requests, tokens, cost).
        usage_per_model: Dict mapping model name to
                         (requests, tokens, cost).
    """

    total_requests: int = 0
    total_prompt_tokens: int = 0
    total_completion_tokens: int = 0
    total_tokens: int = 0
    total_estimated_cost: float = 0.0
    average_latency_ms: float = 0.0
    usage_per_provider: dict[str, tuple[int, int, float]] = field(default_factory=dict)
    usage_per_model: dict[str, tuple[int, int, float]] = field(default_factory=dict)


# ------------------------------------------------------------------
# LLMCostTracker
# ------------------------------------------------------------------


class LLMCostTracker:
    """Stateless utility for aggregating LLM usage data.

    All methods are deterministic — given the same input, they
    always produce the same output.
    """

    @staticmethod
    def summarize(usages: list[LLMUsage]) -> LLMCostSummary:
        """Aggregate a list of usage records into a single summary.

        Args:
            usages: List of LLMUsage records.

        Returns:
            An LLMCostSummary with totals and breakdowns.
        """
        if not usages:
            return LLMCostSummary()

        total_req = len(usages)
        total_prompt = sum(u.prompt_tokens for u in usages)
        total_completion = sum(u.completion_tokens for u in usages)
        total_tok = sum(u.total_tokens for u in usages)
        total_cost = sum(u.estimated_cost for u in usages)
        avg_latency = sum(u.latency_ms for u in usages) / total_req

        per_provider: dict[str, list[int | float]] = {}
        per_model: dict[str, list[int | float]] = {}

        for u in usages:
            if u.provider not in per_provider:
                per_provider[u.provider] = [0, 0, 0.0]
            per_provider[u.provider][0] += 1
            per_provider[u.provider][1] += u.total_tokens
            per_provider[u.provider][2] += u.estimated_cost

            if u.model not in per_model:
                per_model[u.model] = [0, 0, 0.0]
            per_model[u.model][0] += 1
            per_model[u.model][1] += u.total_tokens
            per_model[u.model][2] += u.estimated_cost

        return LLMCostSummary(
            total_requests=total_req,
            total_prompt_tokens=total_prompt,
            total_completion_tokens=total_completion,
            total_tokens=total_tok,
            total_estimated_cost=round(total_cost, 6),
            average_latency_ms=round(avg_latency, 2),
            usage_per_provider={
                p: (v[0], v[1], round(v[2], 6))
                for p, v in sorted(per_provider.items())
            },
            usage_per_model={
                m: (v[0], v[1], round(v[2], 6))
                for m, v in sorted(per_model.items())
            },
        )

    @staticmethod
    def cost_per_provider(usages: list[LLMUsage]) -> dict[str, float]:
        """Return total estimated cost grouped by provider.

        Args:
            usages: List of LLMUsage records.

        Returns:
            Dict mapping provider name to total estimated cost.
        """
        result: dict[str, float] = {}
        for u in usages:
            result[u.provider] = round(result.get(u.provider, 0.0) + u.estimated_cost, 6)
        return dict(sorted(result.items()))

    @staticmethod
    def cost_per_model(usages: list[LLMUsage]) -> dict[str, float]:
        """Return total estimated cost grouped by model.

        Args:
            usages: List of LLMUsage records.

        Returns:
            Dict mapping model name to total estimated cost.
        """
        result: dict[str, float] = {}
        for u in usages:
            result[u.model] = round(result.get(u.model, 0.0) + u.estimated_cost, 6)
        return dict(sorted(result.items()))

    @staticmethod
    def token_statistics(usages: list[LLMUsage]) -> dict[str, int]:
        """Return aggregated token counts.

        Args:
            usages: List of LLMUsage records.

        Returns:
            Dict with keys: total_prompt, total_completion, total.
        """
        return {
            "total_prompt": sum(u.prompt_tokens for u in usages),
            "total_completion": sum(u.completion_tokens for u in usages),
            "total": sum(u.total_tokens for u in usages),
        }

    @staticmethod
    def average_latency(usages: list[LLMUsage]) -> float:
        """Return the mean latency across all records.

        Args:
            usages: List of LLMUsage records.

        Returns:
            Average latency in milliseconds.
        """
        if not usages:
            return 0.0
        return round(sum(u.latency_ms for u in usages) / len(usages), 2)
