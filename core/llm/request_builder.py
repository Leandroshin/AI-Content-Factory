"""Bridge between PromptBuilder and LLMGateway.

LLMRequestBuilder transforms a PromptRenderResult into an
LLMRequest by adding model configuration (model, temperature,
max_tokens). This keeps PromptBuilder completely ignorant of
LLM-specific concerns.
"""

from __future__ import annotations

from typing import Any

from .models import LLMRequest
from .prompts import PromptRenderResult


class InvalidPromptError(ValueError):
    """Raised when attempting to build an LLMRequest from a failed PromptRenderResult."""


class LLMRequestBuilder:
    """Stateless builder that converts PromptRenderResult into LLMRequest.

    Pipeline:
      1. Receive PromptRenderResult + model config
      2. Validate PromptRenderResult.success
      3. Construct LLMRequest via LLMRequest.create()
      4. Return LLMRequest
    """

    @staticmethod
    def build(
        render_result: PromptRenderResult,
        model: str = "gpt-4o",
        temperature: float = 0.7,
        max_tokens: int = 2048,
        system_prompt: str = "",
        metadata: dict[str, Any] | None = None,
    ) -> LLMRequest:
        """Build an LLMRequest from a rendered prompt.

        Args:
            render_result: The output of PromptBuilder.render().
            model: LLM model identifier.
            temperature: Sampling temperature (0.0–2.0).
            max_tokens: Maximum tokens in the response.
            system_prompt: Optional system-level instruction.
            metadata: Optional extra metadata forwarded to the request.

        Returns:
            An LLMRequest ready for the gateway.

        Raises:
            InvalidPromptError: If render_result.success is False.
        """
        if not render_result.success:
            missing = ", ".join(render_result.variables_missing)
            raise InvalidPromptError(
                f"Cannot build request from failed render of template "
                f"'{render_result.template_name}'. "
                f"Missing placeholders: {missing}."
            )

        merged_metadata: dict[str, Any] = dict(metadata) if metadata else {}
        merged_metadata.setdefault("template_name", render_result.template_name)

        return LLMRequest.create(
            prompt=render_result.rendered,
            system_prompt=system_prompt,
            model=model,
            temperature=temperature,
            max_tokens=max_tokens,
            metadata=merged_metadata,
        )
