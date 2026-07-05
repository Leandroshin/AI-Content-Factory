"""Runtime implementation for the LLM Gateway foundation.

Minimal stateless gateway that receives an LLMRequest,
looks up the appropriate ProviderAdapter, delegates
generate(), and returns the LLMResponse.

No business logic, no PromptBuilder, no Conversation,
no Memory, no CostTracker, no Retry.
"""

from __future__ import annotations

from .models import LLMRequest, LLMResponse
from .providers import ProviderAdapter, ProviderRegistry


class LLMGateway:
    """Stateless gateway that routes LLM requests to the appropriate provider.

    Pipeline:
      1. Receive LLMRequest
      2. Locate ProviderAdapter via ProviderRegistry
      3. Execute adapter.generate()
      4. Return LLMResponse
    """

    def __init__(self, registry: ProviderRegistry) -> None:
        self._registry = registry

    def execute(self, request: LLMRequest, provider_name: str | None = None) -> LLMResponse:
        """Route an LLMRequest to the specified provider and return the response.

        Args:
            request: The immutable LLM generation request.
            provider_name: Target provider name. If None, uses the
                           provider hint from request metadata or "openai".

        Returns:
            An LLMResponse with the generated content.

        Raises:
            KeyError: If the requested provider is not registered.
        """
        provider = provider_name or request.metadata.get("provider", "openai")
        adapter = self._registry.get(provider)
        return adapter.generate(request)
