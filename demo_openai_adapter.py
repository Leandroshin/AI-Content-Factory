"""Foundation demo for the OpenAI adapter — no real API key required.

Uses a FakeHTTPClient to simulate the OpenAI Responses API.
Validates payload, headers, endpoint, parsing, and full integration
with LLMRequestBuilder → LLMGateway → OpenAIAdapter → LLMResponse.
"""

from __future__ import annotations

from typing import Any
from uuid import UUID

from core.llm import (
    LLMGateway,
    LLMRequest,
    LLMResponse,
    PromptBuilder,
    PromptTemplate,
    ProviderRegistry,
)
from core.llm.http_provider import HTTPClient
from core.llm.openai_adapter import OpenAIAdapter
from core.llm.request_builder import LLMRequestBuilder


# ------------------------------------------------------------------
# Fake HTTP client that captures requests and returns canned responses
# ------------------------------------------------------------------


class FakeHTTPClient(HTTPClient):
    """Simulates an HTTP POST to the OpenAI Responses API.

    Records the last URL, headers, and payload for test assertions,
    and returns a pre-configured fake JSON response.
    """

    def __init__(self) -> None:
        self.last_url: str = ""
        self.last_headers: dict[str, str] = {}
        self.last_payload: dict[str, Any] = {}
        self.calls: list[dict[str, Any]] = []

    def post(self, url: str, headers: dict[str, str], json_data: dict[str, Any]) -> dict[str, Any]:
        self.last_url = url
        self.last_headers = headers
        self.last_payload = json_data
        self.calls.append({"url": url, "headers": headers, "payload": json_data})

        return {
            "id": "resp_fake_test_123",
            "model": json_data.get("model", "gpt-4o"),
            "output": [
                {
                    "type": "message",
                    "role": "assistant",
                    "content": [
                        {
                            "type": "output_text",
                            "text": "This is a fake OpenAI response for testing.",
                        }
                    ],
                }
            ],
            "usage": {
                "input_tokens": 15,
                "output_tokens": 25,
                "total_tokens": 40,
            },
        }


# ------------------------------------------------------------------
# Scenario 1: Payload structure matches Responses API
# ------------------------------------------------------------------


def scenario_payload_structure() -> None:
    """Verify build_payload produces correct Responses API JSON."""
    fake = FakeHTTPClient()
    adapter = OpenAIAdapter(api_key="sk-test", http_client=fake)

    request = LLMRequest.create(
        prompt="What is the capital of France?",
        system_prompt="Answer concisely.",
        model="gpt-4o",
        temperature=0.5,
        max_tokens=100,
    )
    adapter.generate(request)

    payload = fake.last_payload
    assert payload["model"] == "gpt-4o"
    assert payload["temperature"] == 0.5
    assert payload["max_output_tokens"] == 100
    assert "input" in payload
    assert len(payload["input"]) == 2
    assert payload["input"][0]["role"] == "system"
    assert payload["input"][1]["role"] == "user"
    print(f"[PASS] payload_structure              | model={payload['model']} "
          f"messages={len(payload['input'])}")


# ------------------------------------------------------------------
# Scenario 2: Headers contain Bearer token
# ------------------------------------------------------------------


def scenario_headers() -> None:
    """Verify build_headers contains proper Authorization."""
    fake = FakeHTTPClient()
    adapter = OpenAIAdapter(api_key="sk-secret-key", http_client=fake)

    adapter.generate(LLMRequest.create(prompt="Hello"))
    headers = fake.last_headers

    assert headers["Authorization"] == "Bearer sk-secret-key"
    assert headers["Content-Type"] == "application/json"
    print(f"[PASS] headers                        | auth=Bearer sk-...")


# ------------------------------------------------------------------
# Scenario 3: Endpoint is correct
# ------------------------------------------------------------------


def scenario_endpoint() -> None:
    """Verify the default endpoint URL."""
    fake = FakeHTTPClient()
    adapter = OpenAIAdapter(api_key="sk-test", http_client=fake)

    adapter.generate(LLMRequest.create(prompt="Hi"))
    assert "responses" in fake.last_url
    assert fake.last_url == "https://api.openai.com/v1/responses"
    print(f"[PASS] endpoint                       | url={fake.last_url}")


# ------------------------------------------------------------------
# Scenario 4: Parse response correctly
# ------------------------------------------------------------------


def scenario_parse_response() -> None:
    """Verify parse_response extracts content and token counts."""
    fake = FakeHTTPClient()
    adapter = OpenAIAdapter(api_key="sk-test", http_client=fake)

    request = LLMRequest.create(prompt="Test")
    response = adapter.generate(request)

    assert isinstance(response, LLMResponse)
    assert response.provider == "openai"
    assert response.content == "This is a fake OpenAI response for testing."
    assert response.input_tokens == 15
    assert response.output_tokens == 25
    assert response.total_tokens == 40
    assert response.finish_reason == "stop"
    print(f"[PASS] parse_response                 | content='{response.content[:40]}...' "
          f"tokens={response.total_tokens}")


# ------------------------------------------------------------------
# Scenario 5: System prompt becomes first input message
# ------------------------------------------------------------------


def scenario_system_prompt_in_payload() -> None:
    """System prompt appears as the first input message with input_text type."""
    fake = FakeHTTPClient()
    adapter = OpenAIAdapter(api_key="sk-test", http_client=fake)

    adapter.generate(LLMRequest.create(
        prompt="Hello", system_prompt="Be polite.",
    ))

    msg0 = fake.last_payload["input"][0]
    assert msg0["role"] == "system"
    assert msg0["content"][0]["type"] == "input_text"
    assert msg0["content"][0]["text"] == "Be polite."
    print(f"[PASS] system_prompt_in_payload       | role={msg0['role']} text='{msg0['content'][0]['text']}'")


# ------------------------------------------------------------------
# Scenario 6: No system prompt — only user message
# ------------------------------------------------------------------


def scenario_no_system_prompt() -> None:
    """Without system prompt, only the user message is sent."""
    fake = FakeHTTPClient()
    adapter = OpenAIAdapter(api_key="sk-test", http_client=fake)

    adapter.generate(LLMRequest.create(prompt="Just this"))

    assert len(fake.last_payload["input"]) == 1
    assert fake.last_payload["input"][0]["role"] == "user"
    print(f"[PASS] no_system_prompt               | messages={len(fake.last_payload['input'])} (user only)")


# ------------------------------------------------------------------
# Scenario 7: API key validation
# ------------------------------------------------------------------


def scenario_api_key_validation() -> None:
    """Empty API key raises ValueError at construction."""
    try:
        OpenAIAdapter(api_key="")
        assert False, "Expected ValueError was not raised."
    except ValueError as exc:
        assert "API key" in str(exc)
        print(f"[PASS] api_key_validation             | error='{exc}'")


# ------------------------------------------------------------------
# Scenario 8: request_id propagated through the whole pipeline
# ------------------------------------------------------------------


def scenario_request_id_propagated() -> None:
    """The request_id survives the round-trip through the adapter."""
    fake = FakeHTTPClient()
    adapter = OpenAIAdapter(api_key="sk-test", http_client=fake)

    request = LLMRequest.create(prompt="Propagate me")
    response = adapter.generate(request)

    assert response.request_id == request.request_id
    print(f"[PASS] request_id_propagated          | id={response.request_id}")


# ------------------------------------------------------------------
# Scenario 9: Full pipeline — PromptBuilder → LLMRequestBuilder
#            → LLMGateway → OpenAIAdapter → LLMResponse
# ------------------------------------------------------------------


def scenario_full_pipeline() -> None:
    """End-to-end integration with template, builder, gateway, and adapter."""
    fake = FakeHTTPClient()
    adapter = OpenAIAdapter(api_key="sk-pipeline", http_client=fake)

    registry = ProviderRegistry()
    registry.register("openai", adapter)
    gateway = LLMGateway(registry)

    template = PromptTemplate.create(
        name="translate",
        template="Translate to {language}: {text}",
        required_placeholders=["language", "text"],
    )
    render = PromptBuilder.render(template, {"language": "French", "text": "Hello"})
    assert render.success

    request = LLMRequestBuilder.build(
        render_result=render,
        model="gpt-4o",
        temperature=0.3,
        max_tokens=256,
        system_prompt="You are a translator.",
    )

    response = gateway.execute(request)
    assert isinstance(response, LLMResponse)
    assert response.request_id == request.request_id
    assert response.provider == "openai"
    assert response.content == "This is a fake OpenAI response for testing."

    # Verify the adapter received the rendered prompt
    assert "Translate to French: Hello" in str(fake.last_payload)
    print(f"[PASS] full_pipeline                  | prompt='{request.prompt}' "
          f"response='{response.content[:30]}...' "
          f"provider={response.provider}")


# ------------------------------------------------------------------
# Scenario 10: Multiple calls produce independent payloads
# ------------------------------------------------------------------


def scenario_multiple_calls() -> None:
    """Each generate() call records independently."""
    fake = FakeHTTPClient()
    adapter = OpenAIAdapter(api_key="sk-test", http_client=fake)

    adapter.generate(LLMRequest.create(prompt="First"))
    adapter.generate(LLMRequest.create(prompt="Second"))

    assert len(fake.calls) == 2
    assert fake.calls[0]["payload"]["input"][-1]["content"][0]["text"] == "First"
    assert fake.calls[1]["payload"]["input"][-1]["content"][0]["text"] == "Second"
    print(f"[PASS] multiple_calls                 | calls={len(fake.calls)} "
          f"payloads independent")


# ------------------------------------------------------------------
# Scenario 11: Base URL can be overridden
# ------------------------------------------------------------------


def scenario_custom_base_url() -> None:
    """The base_url constructor parameter changes the endpoint."""
    fake = FakeHTTPClient()
    adapter = OpenAIAdapter(
        api_key="sk-test",
        http_client=fake,
        base_url="https://custom.openai.com/v1/responses",
    )

    adapter.generate(LLMRequest.create(prompt="Custom URL"))
    assert fake.last_url == "https://custom.openai.com/v1/responses"
    print(f"[PASS] custom_base_url                | url={fake.last_url}")


# ------------------------------------------------------------------
# Main
# ------------------------------------------------------------------


def main() -> None:
    print("=" * 62)
    print("OpenAI Adapter Demo (Fake HTTP)")
    print("=" * 62)
    print()

    scenario_payload_structure()
    scenario_headers()
    scenario_endpoint()
    scenario_parse_response()
    scenario_system_prompt_in_payload()
    scenario_no_system_prompt()
    scenario_api_key_validation()
    scenario_request_id_propagated()
    scenario_full_pipeline()
    scenario_multiple_calls()
    scenario_custom_base_url()

    print()
    print("=" * 62)
    print("All OpenAI adapter scenarios passed.")
    print("=" * 62)


if __name__ == "__main__":
    main()
