"""Foundation demo for the LLM Gateway — no external dependencies.

Uses a FakeProviderAdapter that returns a fixed response.
No OpenAI, no Gemini, no Anthropic, no HTTP, no async.
"""

from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID

from core.llm import LLMGateway, LLMRequest, LLMResponse, ProviderAdapter, ProviderRegistry


# ------------------------------------------------------------------
# Fake provider for demo purposes
# ------------------------------------------------------------------


@dataclass
class FakeProviderAdapter(ProviderAdapter):
    """Returns a fixed response regardless of input."""

    name: str = "fake"
    fixed_content: str = "This is a fake LLM response for testing."
    fake_input_tokens: int = 10
    fake_output_tokens: int = 20

    def generate(self, request: LLMRequest) -> LLMResponse:
        return LLMResponse(
            request_id=request.request_id,
            provider=self.name,
            model=request.model,
            content=self.fixed_content,
            input_tokens=self.fake_input_tokens,
            output_tokens=self.fake_output_tokens,
            total_tokens=self.fake_input_tokens + self.fake_output_tokens,
            finish_reason="stop",
            metadata={"demo": True, "fake": True},
        )


# ------------------------------------------------------------------
# Scenario 1: Register a provider and verify it's listed
# ------------------------------------------------------------------


def scenario_register_and_list() -> None:
    """Register a fake provider and confirm it appears in the registry."""
    registry = ProviderRegistry()
    adapter = FakeProviderAdapter(name="test_fake")
    registry.register("test_fake", adapter)

    providers = registry.list()
    assert "test_fake" in providers
    print(f"[PASS] register_and_list              | registered=test_fake providers={list(providers.keys())}")


# ------------------------------------------------------------------
# Scenario 2: Look up a provider by name
# ------------------------------------------------------------------


def scenario_get_provider() -> None:
    """Look up a registered provider and confirm it is the correct instance."""
    registry = ProviderRegistry()
    adapter = FakeProviderAdapter(name="lookup_test")
    registry.register("lookup_test", adapter)

    found = registry.get("lookup_test")
    assert found is adapter
    assert isinstance(found, FakeProviderAdapter)
    print(f"[PASS] get_provider                   | found={type(found).__name__} name={found.name}")


# ------------------------------------------------------------------
# Scenario 3: Execute via gateway and check response
# ------------------------------------------------------------------


def scenario_gateway_execution() -> None:
    """Execute a full gateway pipeline with a fake provider."""
    registry = ProviderRegistry()
    registry.register("demo", FakeProviderAdapter(name="demo"))

    gateway = LLMGateway(registry)
    request = LLMRequest.create(
        prompt="What is the capital of France?",
        system_prompt="Answer concisely.",
        temperature=0.5,
    )

    response = gateway.execute(request, provider_name="demo")

    assert isinstance(response, LLMResponse)
    assert response.request_id == request.request_id
    assert response.provider == "demo"
    assert response.model == request.model
    assert response.content == "This is a fake LLM response for testing."
    assert response.finish_reason == "stop"
    assert response.total_tokens == 30  # 10 input + 20 output
    assert response.metadata["demo"] is True
    print(f"[PASS] gateway_execution              | provider={response.provider} "
          f"content={response.content[:40]}... tokens={response.total_tokens}")


# ------------------------------------------------------------------
# Scenario 4: Response correctly maps request_id
# ------------------------------------------------------------------


def scenario_response_maps_request_id() -> None:
    """Verify the response's request_id matches the request."""
    registry = ProviderRegistry()
    registry.register("echo", FakeProviderAdapter(name="echo"))

    gateway = LLMGateway(registry)
    request = LLMRequest.create(prompt="Hello")
    response = gateway.execute(request, provider_name="echo")

    assert response.request_id == request.request_id
    assert isinstance(response.request_id, UUID)
    print(f"[PASS] response_maps_request_id       | request={request.request_id} response={response.request_id}")


# ------------------------------------------------------------------
# Scenario 5: Non-existent provider raises KeyError
# ------------------------------------------------------------------


def scenario_missing_provider_raises_error() -> None:
    """Requesting an unregistered provider raises KeyError."""
    registry = ProviderRegistry()
    gateway = LLMGateway(registry)
    request = LLMRequest.create(prompt="Test")

    try:
        gateway.execute(request, provider_name="nonexistent")
        assert False, "Expected KeyError was not raised."
    except KeyError as exc:
        assert "nonexistent" in str(exc)
        print(f"[PASS] missing_provider_raises_error  | error='{exc}'")


# ------------------------------------------------------------------
# Scenario 6: Registering duplicate raises ValueError
# ------------------------------------------------------------------


def scenario_duplicate_registration_raises_error() -> None:
    """Registering the same provider name twice raises ValueError."""
    registry = ProviderRegistry()
    registry.register("dup", FakeProviderAdapter(name="dup1"))

    try:
        registry.register("dup", FakeProviderAdapter(name="dup2"))
        assert False, "Expected ValueError was not raised."
    except ValueError as exc:
        assert "dup" in str(exc)
        print(f"[PASS] duplicate_registration_error   | error='{exc}'")


# ------------------------------------------------------------------
# Scenario 7: Unregister a provider
# ------------------------------------------------------------------


def scenario_unregister_provider() -> None:
    """Unregister removes the provider; subsequent get raises KeyError."""
    registry = ProviderRegistry()
    registry.register("temp", FakeProviderAdapter(name="temp"))
    assert "temp" in registry.list()

    registry.unregister("temp")
    assert "temp" not in registry.list()

    try:
        registry.get("temp")
        assert False, "Expected KeyError after unregister."
    except KeyError:
        print(f"[PASS] unregister_provider           | providers={list(registry.list().keys())} (empty)")


# ------------------------------------------------------------------
# Scenario 8: Gateway uses default provider from metadata
# ------------------------------------------------------------------


def scenario_default_provider_from_metadata() -> None:
    """When provider_name is None, gateway falls back to request.metadata."""
    registry = ProviderRegistry()
    registry.register("my_default", FakeProviderAdapter(name="my_default"))

    gateway = LLMGateway(registry)
    request = LLMRequest.create(prompt="Hi", metadata={"provider": "my_default"})

    response = gateway.execute(request)
    assert response.provider == "my_default"
    print(f"[PASS] default_provider_from_metadata  | provider={response.provider} "
          f"(from request.metadata)")


# ------------------------------------------------------------------
# Main
# ------------------------------------------------------------------


def main() -> None:
    print("=" * 62)
    print("LLM Gateway Foundation Demo")
    print("=" * 62)
    print()

    scenario_register_and_list()
    scenario_get_provider()
    scenario_gateway_execution()
    scenario_response_maps_request_id()
    scenario_missing_provider_raises_error()
    scenario_duplicate_registration_raises_error()
    scenario_unregister_provider()
    scenario_default_provider_from_metadata()

    print()
    print("=" * 62)
    print("All LLM Gateway scenarios passed.")
    print("=" * 62)


if __name__ == "__main__":
    main()
