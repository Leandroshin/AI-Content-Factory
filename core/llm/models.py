"""Immutable request/response models for the LLM Gateway."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any
from uuid import UUID, uuid4


@dataclass(frozen=True, slots=True)
class LLMRequest:
    """Immutable input for an LLM generation call."""

    request_id: UUID
    prompt: str
    system_prompt: str = ""
    model: str = "gpt-4o"
    temperature: float = 0.7
    max_tokens: int = 2048
    metadata: dict[str, Any] = field(default_factory=dict)

    @staticmethod
    def create(
        prompt: str,
        system_prompt: str = "",
        model: str = "gpt-4o",
        temperature: float = 0.7,
        max_tokens: int = 2048,
        metadata: dict[str, Any] | None = None,
    ) -> LLMRequest:
        """Convenience factory that auto-generates a request_id."""
        return LLMRequest(
            request_id=uuid4(),
            prompt=prompt,
            system_prompt=system_prompt,
            model=model,
            temperature=temperature,
            max_tokens=max_tokens,
            metadata=metadata if metadata is not None else {},
        )


@dataclass(frozen=True, slots=True)
class LLMResponse:
    """Immutable output from an LLM generation call."""

    request_id: UUID
    provider: str
    model: str
    content: str
    input_tokens: int = 0
    output_tokens: int = 0
    total_tokens: int = 0
    finish_reason: str = "stop"
    metadata: dict[str, Any] = field(default_factory=dict)
