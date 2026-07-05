"""Foundation demo for LLMRequestBuilder.

Validates the bridge between PromptRenderResult and LLMRequest,
including validation, metadata propagation, and deterministic behavior.
"""

from __future__ import annotations

from uuid import UUID

from core.llm import LLMRequest, PromptBuilder, PromptRenderResult, PromptTemplate
from core.llm.request_builder import InvalidPromptError, LLMRequestBuilder


# ------------------------------------------------------------------
# Scenario 1: Valid PromptRenderResult generates LLMRequest
# ------------------------------------------------------------------


def scenario_valid_render_generates_request() -> None:
    """A successful render produces a valid LLMRequest with the rendered prompt."""
    template = PromptTemplate.create(
        name="greeting",
        template="Hello, {name}!",
        required_placeholders=["name"],
    )
    render_result = PromptBuilder.render(template, {"name": "Alice"})
    assert render_result.success

    request = LLMRequestBuilder.build(render_result=render_result, model="gpt-4o")

    assert isinstance(request, LLMRequest)
    assert request.prompt == "Hello, Alice!"
    assert request.model == "gpt-4o"
    assert isinstance(request.request_id, UUID)
    print(f"[PASS] valid_render_generates_request  | prompt='{request.prompt}' model={request.model}")


# ------------------------------------------------------------------
# Scenario 2: Invalid PromptRenderResult raises error
# ------------------------------------------------------------------


def scenario_invalid_render_raises_error() -> None:
    """A failed render raises InvalidPromptError with a descriptive message."""
    template = PromptTemplate.create(
        name="incomplete",
        template="{a} + {b}",
        required_placeholders=["a", "b"],
    )
    render_result = PromptBuilder.render(template, {"a": "1"})
    assert not render_result.success

    try:
        LLMRequestBuilder.build(render_result=render_result)
        assert False, "Expected InvalidPromptError was not raised."
    except InvalidPromptError as exc:
        assert "incomplete" in str(exc)
        assert "b" in str(exc)
        print(f"[PASS] invalid_render_raises_error    | error='{exc}'")


# ------------------------------------------------------------------
# Scenario 3: Model propagated correctly
# ------------------------------------------------------------------


def scenario_model_propagated() -> None:
    """The model parameter is passed through to LLMRequest."""
    render_result = _make_valid_render("test", "content")

    request = LLMRequestBuilder.build(
        render_result=render_result,
        model="gpt-4o-mini",
    )

    assert request.model == "gpt-4o-mini"
    print(f"[PASS] model_propagated               | model={request.model}")


# ------------------------------------------------------------------
# Scenario 4: Temperature propagated correctly
# ------------------------------------------------------------------


def scenario_temperature_propagated() -> None:
    """The temperature parameter is passed through to LLMRequest."""
    render_result = _make_valid_render("test", "content")

    request = LLMRequestBuilder.build(
        render_result=render_result,
        temperature=0.2,
    )

    assert request.temperature == 0.2
    print(f"[PASS] temperature_propagated         | temperature={request.temperature}")


# ------------------------------------------------------------------
# Scenario 5: Max_tokens propagated correctly
# ------------------------------------------------------------------


def scenario_max_tokens_propagated() -> None:
    """The max_tokens parameter is passed through to LLMRequest."""
    render_result = _make_valid_render("test", "content")

    request = LLMRequestBuilder.build(
        render_result=render_result,
        max_tokens=512,
    )

    assert request.max_tokens == 512
    print(f"[PASS] max_tokens_propagated          | max_tokens={request.max_tokens}")


# ------------------------------------------------------------------
# Scenario 6: System prompt propagated correctly
# ------------------------------------------------------------------


def scenario_system_prompt_propagated() -> None:
    """The system_prompt parameter is passed through to LLMRequest."""
    render_result = _make_valid_render("test", "content")

    request = LLMRequestBuilder.build(
        render_result=render_result,
        system_prompt="You are a helpful assistant.",
    )

    assert request.system_prompt == "You are a helpful assistant."
    print(f"[PASS] system_prompt_propagated       | system_prompt='{request.system_prompt}'")


# ------------------------------------------------------------------
# Scenario 7: Metadata propagated correctly
# ------------------------------------------------------------------


def scenario_metadata_propagated() -> None:
    """Custom metadata is forwarded to the LLMRequest."""
    render_result = _make_valid_render("test", "content")

    request = LLMRequestBuilder.build(
        render_result=render_result,
        metadata={"source": "demo", "version": "1.0"},
    )

    assert request.metadata["source"] == "demo"
    assert request.metadata["version"] == "1.0"
    print(f"[PASS] metadata_propagated            | metadata={request.metadata}")


# ------------------------------------------------------------------
# Scenario 8: Template name automatically added to metadata
# ------------------------------------------------------------------


def scenario_template_name_in_metadata() -> None:
    """The template name is automatically set in metadata if not provided."""
    render_result = _make_valid_render("my_template", "Hello")
    request = LLMRequestBuilder.build(render_result=render_result)

    assert request.metadata["template_name"] == "my_template"
    print(f"[PASS] template_name_in_metadata      | template_name={request.metadata['template_name']}")


# ------------------------------------------------------------------
# Scenario 9: Request ID is auto-generated
# ------------------------------------------------------------------


def scenario_request_id_auto_generated() -> None:
    """Each call produces a unique request_id."""
    render_result = _make_valid_render("test", "content")

    r1 = LLMRequestBuilder.build(render_result)
    r2 = LLMRequestBuilder.build(render_result)

    assert isinstance(r1.request_id, UUID)
    assert isinstance(r2.request_id, UUID)
    assert r1.request_id != r2.request_id
    print(f"[PASS] request_id_auto_generated      | id1={r1.request_id} id2={r2.request_id} (different)")


# ------------------------------------------------------------------
# Scenario 10: Full pipeline — template → render → request
# ------------------------------------------------------------------


def scenario_full_pipeline() -> None:
    """End-to-end: PromptTemplate → PromptBuilder → LLMRequestBuilder → LLMRequest."""
    template = PromptTemplate.create(
        name="full_pipeline",
        template="Translate to {language}: {text}",
        required_placeholders=["language", "text"],
        description="Translation prompt",
    )
    render_result = PromptBuilder.render(template, {"language": "French", "text": "Hello"})
    assert render_result.success

    request = LLMRequestBuilder.build(
        render_result=render_result,
        model="gpt-4o",
        temperature=0.3,
        max_tokens=256,
        system_prompt="You are a translator.",
        metadata={"task": "translation"},
    )

    assert request.prompt == "Translate to French: Hello"
    assert request.model == "gpt-4o"
    assert request.temperature == 0.3
    assert request.max_tokens == 256
    assert request.system_prompt == "You are a translator."
    assert request.metadata["task"] == "translation"
    assert request.metadata["template_name"] == "full_pipeline"
    print(f"[PASS] full_pipeline                  | prompt='{request.prompt}' "
          f"model={request.model} temp={request.temperature}")


# ------------------------------------------------------------------
# Scenario 11: Deterministic behavior (same input → same prompt)
# ------------------------------------------------------------------


def scenario_deterministic() -> None:
    """Same render result and config always produces the same prompt."""
    render_result = _make_valid_render("det", "Fixed content")

    r1 = LLMRequestBuilder.build(render_result, model="gpt-4o")
    r2 = LLMRequestBuilder.build(render_result, model="gpt-4o")

    # prompt, model, temperature, max_tokens all match
    assert r1.prompt == r2.prompt
    assert r1.model == r2.model
    assert r1.temperature == r2.temperature
    assert r1.max_tokens == r2.max_tokens
    print(f"[PASS] deterministic                  | prompt='{r1.prompt}' (identical)")


# ------------------------------------------------------------------
# Helper
# ------------------------------------------------------------------


def _make_valid_render(name: str, content: str) -> PromptRenderResult:
    """Build a simple valid PromptRenderResult for testing."""
    return PromptRenderResult(
        rendered=content,
        template_name=name,
        variables_used={},
        variables_missing=[],
        success=True,
    )


# ------------------------------------------------------------------
# Main
# ------------------------------------------------------------------


def main() -> None:
    print("=" * 62)
    print("LLMRequestBuilder Demo")
    print("=" * 62)
    print()

    scenario_valid_render_generates_request()
    scenario_invalid_render_raises_error()
    scenario_model_propagated()
    scenario_temperature_propagated()
    scenario_max_tokens_propagated()
    scenario_system_prompt_propagated()
    scenario_metadata_propagated()
    scenario_template_name_in_metadata()
    scenario_request_id_auto_generated()
    scenario_full_pipeline()
    scenario_deterministic()

    print()
    print("=" * 62)
    print("All LLMRequestBuilder scenarios passed.")
    print("=" * 62)


if __name__ == "__main__":
    main()
