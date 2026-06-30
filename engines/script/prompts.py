"""Script engine prompt templates for AI Content Factory."""

from __future__ import annotations

from enum import StrEnum


class PromptTemplate(StrEnum):
    """Supported script prompt template placeholders."""

    TOPIC_TO_OUTLINE = "topic_to_outline"
    OUTLINE_TO_SCRIPT = "outline_to_script"
    DRAFT_REFINEMENT = "draft_refinement"
