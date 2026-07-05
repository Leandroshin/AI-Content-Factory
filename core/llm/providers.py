"""Provider abstraction layer for the LLM Gateway."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from .models import LLMRequest, LLMResponse


class ProviderAdapter(ABC):
    """Abstract contract for an LLM provider adapter.

    Each concrete provider (OpenAI, Gemini, Anthropic, etc.)
    implements generate() to translate LLMRequest into a
    provider-specific API call and return an LLMResponse.
    """

    @abstractmethod
    def generate(self, request: LLMRequest) -> LLMResponse:
        """Send a generation request to the LLM provider.

        Args:
            request: Immutable request with prompt, system_prompt,
                     model, temperature, max_tokens.

        Returns:
            An LLMResponse with the generated content and token usage.
        """


class ProviderRegistry:
    """Registry for managing LLM provider adapters by name.

    Responsible only for registration, removal, and lookup.
    No business logic, no caching, no validation beyond existence.
    """

    def __init__(self) -> None:
        self._adapters: dict[str, ProviderAdapter] = {}

    def register(self, name: str, adapter: ProviderAdapter) -> None:
        """Register a provider adapter under the given name.

        Args:
            name: Unique provider name (e.g. "openai", "gemini").
            adapter: The provider adapter instance.

        Raises:
            ValueError: If a provider with the same name is already registered.
        """
        if name in self._adapters:
            raise ValueError(f"Provider '{name}' is already registered.")
        self._adapters[name] = adapter

    def unregister(self, name: str) -> None:
        """Remove a previously registered provider adapter.

        Args:
            name: The provider name to remove.

        Raises:
            KeyError: If no provider with the given name is registered.
        """
        if name not in self._adapters:
            raise KeyError(f"Provider '{name}' is not registered.")
        del self._adapters[name]

    def get(self, name: str) -> ProviderAdapter:
        """Look up a provider adapter by name.

        Args:
            name: The provider name to look up.

        Returns:
            The registered ProviderAdapter instance.

        Raises:
            KeyError: If no provider with the given name is registered.
        """
        if name not in self._adapters:
            raise KeyError(f"Provider '{name}' is not registered.")
        return self._adapters[name]

    def list(self) -> dict[str, Any]:
        """Return a read-only view of all registered provider names.

        Returns:
            A dict mapping provider name to its adapter repr.
        """
        return {name: repr(adapter) for name, adapter in self._adapters.items()}
