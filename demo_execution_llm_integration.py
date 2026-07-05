"""Integration demo: ExecutionRuntime + LLMGateway + PromptBuilder.

End-to-end pipeline:

  PromptTemplate
  → PromptBuilder.render()
  → LLMRequestBuilder.build()
  → ExecutionRuntime.execute_with_gateway()
  → LLMGateway.execute()
  → FakeProviderAdapter
  → LLMResponse
  → ExecutionResult

All tests use FakeProviderAdapter — no real HTTP, no API key.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any
from uuid import UUID, uuid4

from core.execution import ExecutionResult, ExecutionRuntime
from core.llm import (
    LLMGateway,
    LLMRequest,
    LLMResponse,
    PromptBuilder,
    PromptTemplate,
    ProviderAdapter,
    ProviderRegistry,
)
from core.llm.request_builder import InvalidPromptError, LLMRequestBuilder


# ------------------------------------------------------------------
# Fake provider
# ------------------------------------------------------------------


class FakeProviderAdapter(ProviderAdapter):
    """Returns a fixed response for every request."""

    def __init__(
        self,
        content: str = "Generated content for the task.",
        finish_reason: str = "stop",
        provider_name: str = "fake",
    ) -> None:
        self._content = content
        self._finish_reason = finish_reason
        self._provider_name = provider_name

    def generate(self, request: LLMRequest) -> LLMResponse:
        return LLMResponse(
            request_id=request.request_id,
            provider=self._provider_name,
            model=request.model,
            content=self._content,
            input_tokens=10,
            output_tokens=5,
            total_tokens=15,
            finish_reason=self._finish_reason,
        )


# ------------------------------------------------------------------
# Plain snapshot-like objects
# ------------------------------------------------------------------


@dataclass
class TaskSnapshot:
    task_id: UUID
    name: str
    metadata: object = None


@dataclass
class EmployeeSnapshot:
    employee_id: UUID
    name: str
    role: str = "generic"


# ------------------------------------------------------------------
# Scenario 1: Full pipeline — template render → request → execution
# ------------------------------------------------------------------


def scenario_full_pipeline() -> None:
    """Complete flow from PromptTemplate to ExecutionResult."""
    registry = ProviderRegistry()
    registry.register("fake", FakeProviderAdapter())
    gateway = LLMGateway(registry)

    template = PromptTemplate.create(
        name="summarize",
        template="Summarize this text: {text}",
        required_placeholders=["text"],
    )
    render = PromptBuilder.render(template, {"text": "Long article content here."})
    assert render.success

    request = LLMRequestBuilder.build(
        render_result=render,
        model="gpt-4o",
        temperature=0.3,
    )
    task = TaskSnapshot(task_id=uuid4(), name="Summarization")
    employee = EmployeeSnapshot(employee_id=uuid4(), name="Alice")

    result = ExecutionRuntime.execute_with_gateway(task, employee, request, gateway, provider_name="fake")

    assert isinstance(result, ExecutionResult)
    assert result.success is True
    assert result.output == "Generated content for the task."
    assert result.trace.provider_used == "fake"
    assert result.trace.model_used == "gpt-4o"
    print(f"[PASS] full_pipeline                  | success={result.success} "
          f"output='{result.output[:30]}...' provider={result.trace.provider_used}")


# ------------------------------------------------------------------
# Scenario 2: PromptTemplate rendered correctly through the pipeline
# ------------------------------------------------------------------


def scenario_prompt_rendered_correctly() -> None:
    """The rendered prompt is what reaches the adapter."""
    captured: list[str] = []

    class CapturingProvider(ProviderAdapter):
        def generate(self, request: LLMRequest) -> LLMResponse:
            captured.append(request.prompt)
            return LLMResponse(
                request_id=request.request_id,
                provider="capture",
                model=request.model,
                content="OK",
                total_tokens=2,
            )

    registry = ProviderRegistry()
    registry.register("cap", CapturingProvider())
    gateway = LLMGateway(registry)

    template = PromptTemplate.create(
        name="translate",
        template="Translate to {lang}: {text}",
        required_placeholders=["lang", "text"],
    )
    render = PromptBuilder.render(template, {"lang": "French", "text": "Hello"})
    request = LLMRequestBuilder.build(render)
    task = TaskSnapshot(task_id=uuid4(), name="Translate")
    employee = EmployeeSnapshot(employee_id=uuid4(), name="Bob")

    ExecutionRuntime.execute_with_gateway(task, employee, request, gateway, provider_name="cap")

    assert captured[0] == "Translate to French: Hello"
    print(f"[PASS] prompt_rendered_correctly       | prompt='{captured[0]}'")


# ------------------------------------------------------------------
# Scenario 3: RequestBuilder generates valid LLMRequest with correct fields
# ------------------------------------------------------------------


def scenario_request_builder_fields() -> None:
    """LLMRequestBuilder produces a request with all expected fields."""
    render = PromptBuilder.render(
        PromptTemplate.create(name="test", template="Say {msg}", required_placeholders=["msg"]),
        {"msg": "Hello"},
    )
    request = LLMRequestBuilder.build(
        render_result=render,
        model="gpt-4o-mini",
        temperature=0.5,
        max_tokens=512,
        system_prompt="Be concise.",
        metadata={"source": "demo"},
    )

    assert request.prompt == "Say Hello"
    assert request.model == "gpt-4o-mini"
    assert request.temperature == 0.5
    assert request.max_tokens == 512
    assert request.system_prompt == "Be concise."
    assert request.metadata["source"] == "demo"
    assert request.metadata["template_name"] == "test"
    print(f"[PASS] request_builder_fields          | prompt='{request.prompt}' "
          f"model={request.model} temp={request.temperature}")


# ------------------------------------------------------------------
# Scenario 4: Gateway locates the correct provider
# ------------------------------------------------------------------


def scenario_gateway_locates_provider() -> None:
    """Gateway dispatches to the correct adapter by name."""
    registry = ProviderRegistry()
    registry.register("alpha", FakeProviderAdapter(content="From Alpha", provider_name="alpha"))
    registry.register("beta", FakeProviderAdapter(content="From Beta", provider_name="beta"))
    gateway = LLMGateway(registry)

    task = TaskSnapshot(task_id=uuid4(), name="Multi")
    employee = EmployeeSnapshot(employee_id=uuid4(), name="Charlie")
    request = LLMRequest.create(prompt="Test")

    r1 = ExecutionRuntime.execute_with_gateway(task, employee, request, gateway, provider_name="alpha")
    r2 = ExecutionRuntime.execute_with_gateway(task, employee, request, gateway, provider_name="beta")

    assert r1.output == "From Alpha"
    assert r2.output == "From Beta"
    print(f"[PASS] gateway_locates_provider       | alpha='{r1.output}' "
          f"beta='{r2.output}'")


# ------------------------------------------------------------------
# Scenario 5: Provider returns response and ExecutionRuntime captures it
# ------------------------------------------------------------------


def scenario_provider_returns_response() -> None:
    """LLMResponse from provider is correctly wrapped in ExecutionResult."""
    registry = ProviderRegistry()
    registry.register("fake", FakeProviderAdapter(content="Specific response"))
    gateway = LLMGateway(registry)

    task = TaskSnapshot(task_id=uuid4(), name="Response Test")
    employee = EmployeeSnapshot(employee_id=uuid4(), name="Diana")
    request = LLMRequest.create(prompt="Generate")

    result = ExecutionRuntime.execute_with_gateway(task, employee, request, gateway, provider_name="fake")

    assert result.output == "Specific response"
    assert result.trace.provider_used == "fake"
    assert result.trace.model_used == "gpt-4o"
    print(f"[PASS] provider_returns_response       | output='{result.output}' "
          f"provider={result.trace.provider_used}")


# ------------------------------------------------------------------
# Scenario 6: ExecutionRuntime produces valid ExecutionResult
# ------------------------------------------------------------------


def scenario_execution_result_structure() -> None:
    """ExecutionResult has all expected fields populated."""
    registry = ProviderRegistry()
    registry.register("fake", FakeProviderAdapter())
    gateway = LLMGateway(registry)

    task = TaskSnapshot(task_id=uuid4(), name="Structure")
    employee = EmployeeSnapshot(employee_id=uuid4(), name="Eve")
    request = LLMRequest.create(prompt="Structure test", model="gpt-4o-mini")

    result = ExecutionRuntime.execute_with_gateway(task, employee, request, gateway, provider_name="fake")

    assert isinstance(result.execution_id, UUID)
    assert result.success is True
    assert isinstance(result.output, str)
    assert result.error_message == ""
    assert result.started_at > 0
    assert result.finished_at >= result.started_at
    assert result.duration_seconds >= 0
    assert len(result.trace.stages) == 4
    print(f"[PASS] execution_result_structure      | id={result.execution_id} "
          f"duration={result.duration_seconds}s stages={result.trace.stages}")


# ------------------------------------------------------------------
# Scenario 7: Non-existent provider raises KeyError via execute_with_gateway
# ------------------------------------------------------------------


def scenario_nonexistent_provider() -> None:
    """Requesting an unregistered provider produces a failed ExecutionResult."""
    registry = ProviderRegistry()
    gateway = LLMGateway(registry)

    task = TaskSnapshot(task_id=uuid4(), name="Ghost")
    employee = EmployeeSnapshot(employee_id=uuid4(), name="Frank")
    request = LLMRequest.create(prompt="Hi")

    result = ExecutionRuntime.execute_with_gateway(task, employee, request, gateway, provider_name="ghost")

    assert result.success is False
    assert "exception" in result.error_message.lower()
    print(f"[PASS] nonexistent_provider            | success={result.success} "
          f"error='{result.error_message}'")


# ------------------------------------------------------------------
# Scenario 8: Invalid prompt (failed PromptRenderResult) raises error
# ------------------------------------------------------------------


def scenario_invalid_prompt() -> None:
    """Building a request from a failed render raises InvalidPromptError."""
    template = PromptTemplate.create(
        name="failing",
        template="{a} + {b}",
        required_placeholders=["a", "b"],
    )
    render = PromptBuilder.render(template, {"a": "1"})
    assert not render.success

    try:
        LLMRequestBuilder.build(render)
        assert False, "Expected InvalidPromptError was not raised."
    except InvalidPromptError:
        pass
    print(f"[PASS] invalid_prompt                  | InvalidPromptError raised for missing placeholder")


# ------------------------------------------------------------------
# Scenario 9: Empty response from provider produces failed ExecutionResult
# ------------------------------------------------------------------


def scenario_empty_response() -> None:
    """Provider returning empty content results in failed execution."""
    registry = ProviderRegistry()
    registry.register("empty", FakeProviderAdapter(content="   ", finish_reason="stop", provider_name="empty"))
    gateway = LLMGateway(registry)

    task = TaskSnapshot(task_id=uuid4(), name="Empty Test")
    employee = EmployeeSnapshot(employee_id=uuid4(), name="Grace")
    request = LLMRequest.create(prompt="Say nothing")

    result = ExecutionRuntime.execute_with_gateway(task, employee, request, gateway, provider_name="empty")

    assert result.success is False
    assert result.output == ""
    assert "empty" in result.error_message.lower()
    print(f"[PASS] empty_response                  | success={result.success} "
          f"error='{result.error_message}'")


# ------------------------------------------------------------------
# Scenario 10: Determinism — same inputs produce same result
# ------------------------------------------------------------------


def scenario_determinism() -> None:
    """Identical pipeline inputs produce identical ExecutionResult contents."""
    registry = ProviderRegistry()
    registry.register("det", FakeProviderAdapter(content="Deterministic", provider_name="det"))
    gateway = LLMGateway(registry)

    template = PromptTemplate.create(
        name="det_test",
        template="Repeat: {word}",
        required_placeholders=["word"],
    )
    render = PromptBuilder.render(template, {"word": "hello"})
    request = LLMRequestBuilder.build(render, model="gpt-4o")

    task = TaskSnapshot(task_id=uuid4(), name="Det")
    employee = EmployeeSnapshot(employee_id=uuid4(), name="Heidi")

    r1 = ExecutionRuntime.execute_with_gateway(task, employee, request, gateway, provider_name="det")
    r2 = ExecutionRuntime.execute_with_gateway(task, employee, request, gateway, provider_name="det")

    assert r1.output == r2.output
    assert r1.success == r2.success
    assert r1.trace.provider_used == r2.trace.provider_used
    print(f"[PASS] determinism                    | output='{r1.output}' (identical)")


# ------------------------------------------------------------------
# Scenario 11: Full end-to-end with all components connected
# ------------------------------------------------------------------


def scenario_end_to_end() -> None:
    """Every component in the chain is exercised end-to-end."""
    registry = ProviderRegistry()
    registry.register("e2e", FakeProviderAdapter(content="E2E response", provider_name="e2e"))
    gateway = LLMGateway(registry)

    template = PromptTemplate.create(
        name="e2e",
        template="Answer: {question}",
        required_placeholders=["question"],
        description="E2E test template",
    )
    render = PromptBuilder.render(template, {"question": "What is AI?"})
    assert render.success
    assert render.template_name == "e2e"

    request = LLMRequestBuilder.build(
        render_result=render,
        model="gpt-4o",
        temperature=0.7,
        max_tokens=256,
        system_prompt="Answer concisely.",
        metadata={"env": "test"},
    )
    assert request.system_prompt == "Answer concisely."

    task = TaskSnapshot(task_id=uuid4(), name="E2E Task")
    employee = EmployeeSnapshot(employee_id=uuid4(), name="Ivan")

    result = ExecutionRuntime.execute_with_gateway(
        task, employee, request, gateway,
        provider_name="e2e",
        metadata={"execution_env": "integration_test"},
    )

    assert result.success is True
    assert result.output == "E2E response"
    assert result.trace.stages == ["prepare_context", "execute_llm", "validate_output", "build_result"]
    assert result.trace.provider_used == "e2e"
    assert result.trace.model_used == "gpt-4o"
    print(f"[PASS] end_to_end                     | success={result.success} "
          f"output='{result.output}' provider={result.trace.provider_used}")


# ------------------------------------------------------------------
# Main
# ------------------------------------------------------------------


def main() -> None:
    print("=" * 62)
    print("ExecutionRuntime + LLM Gateway Integration Demo")
    print("=" * 62)
    print()

    scenario_full_pipeline()
    scenario_prompt_rendered_correctly()
    scenario_request_builder_fields()
    scenario_gateway_locates_provider()
    scenario_provider_returns_response()
    scenario_execution_result_structure()
    scenario_nonexistent_provider()
    scenario_invalid_prompt()
    scenario_empty_response()
    scenario_determinism()
    scenario_end_to_end()

    print()
    print("=" * 62)
    print("All integration scenarios passed.")
    print("=" * 62)


if __name__ == "__main__":
    main()
