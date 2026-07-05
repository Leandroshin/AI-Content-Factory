"""Prompt template system for the LLM Gateway.

Provides PromptTemplate, PromptRenderResult, PromptBuilder,
and TemplateRegistry — all provider-agnostic.

The builder only assembles prompts; it has no knowledge of
any LLM provider, SDK, HTTP, or async.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any
from uuid import uuid4


# ------------------------------------------------------------------
# PromptTemplate
# ------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class PromptTemplate:
    """Immutable template definition with named placeholders.

    Placeholders use the {variable_name} syntax, compatible with
    Python's str.format().

    Attributes:
        template_id: Unique identifier for the template.
        name: Human-readable name used as registry key.
        template: The template string with {placeholders}.
        required_placeholders: Placeholders that must be provided.
        description: Optional description of the template's purpose.
    """

    template_id: str
    name: str
    template: str
    required_placeholders: list[str] = field(default_factory=list)
    description: str = ""

    @staticmethod
    def create(
        name: str,
        template: str,
        required_placeholders: list[str] | None = None,
        description: str = "",
    ) -> PromptTemplate:
        """Factory that auto-generates a template_id."""
        return PromptTemplate(
            template_id=str(uuid4()),
            name=name,
            template=template,
            required_placeholders=list(required_placeholders) if required_placeholders else [],
            description=description,
        )


# ------------------------------------------------------------------
# PromptRenderResult
# ------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class PromptRenderResult:
    """Immutable result of a prompt rendering operation.

    Attributes:
        rendered: The final rendered prompt string.
        template_name: Name of the template used.
        variables_used: Dict of variable name to value that were substituted.
        variables_missing: List of required placeholder names that were
                           not provided (empty = complete render).
        success: True if all required placeholders were provided.
    """

    rendered: str
    template_name: str
    variables_used: dict[str, str] = field(default_factory=dict)
    variables_missing: list[str] = field(default_factory=list)
    success: bool = True


# ------------------------------------------------------------------
# PromptBuilder
# ------------------------------------------------------------------


class PromptBuilder:
    """Stateless builder that renders PromptTemplates with variables.

    Validates that all required placeholders are provided,
    then renders using str.format().
    """

    @staticmethod
    def render(template: PromptTemplate, variables: dict[str, str]) -> PromptRenderResult:
        """Render a template with the given variables.

        Args:
            template: The PromptTemplate to render.
            variables: Dict mapping placeholder name to value.

        Returns:
            A PromptRenderResult with the rendered text and validation info.
        """
        missing = [
            ph for ph in template.required_placeholders
            if ph not in variables or variables[ph] is None
        ]

        if missing:
            return PromptRenderResult(
                rendered=template.template,
                template_name=template.name,
                variables_used=dict(variables),
                variables_missing=list(missing),
                success=False,
            )

        try:
            rendered = template.template.format(**variables)
        except KeyError as exc:
            missing_key = exc.args[0]
            return PromptRenderResult(
                rendered=template.template,
                template_name=template.name,
                variables_used=dict(variables),
                variables_missing=[missing_key],
                success=False,
            )

        return PromptRenderResult(
            rendered=rendered,
            template_name=template.name,
            variables_used=dict(variables),
            variables_missing=[],
            success=True,
        )


# ------------------------------------------------------------------
# TemplateRegistry
# ------------------------------------------------------------------


class TemplateRegistry:
    """Registry for managing PromptTemplates by name.

    Responsible only for CRUD operations on templates.
    No rendering logic, no persistence.
    """

    def __init__(self) -> None:
        self._templates: dict[str, PromptTemplate] = {}

    def register(self, template: PromptTemplate) -> None:
        """Register a template by its name.

        Args:
            template: The PromptTemplate to register.

        Raises:
            ValueError: If a template with the same name already exists.
        """
        if template.name in self._templates:
            raise ValueError(f"Template '{template.name}' is already registered.")
        self._templates[template.name] = template

    def unregister(self, name: str) -> None:
        """Remove a previously registered template.

        Args:
            name: The template name to remove.

        Raises:
            KeyError: If no template with the given name exists.
        """
        if name not in self._templates:
            raise KeyError(f"Template '{name}' is not registered.")
        del self._templates[name]

    def get(self, name: str) -> PromptTemplate:
        """Look up a template by name.

        Args:
            name: The template name.

        Returns:
            The registered PromptTemplate.

        Raises:
            KeyError: If no template with the given name exists.
        """
        if name not in self._templates:
            raise KeyError(f"Template '{name}' is not registered.")
        return self._templates[name]

    def exists(self, name: str) -> bool:
        """Check if a template is registered.

        Args:
            name: The template name.

        Returns:
            True if the template exists, False otherwise.
        """
        return name in self._templates

    def list_templates(self) -> dict[str, str]:
        """Return a read-only view of registered template names and descriptions.

        Returns:
            Dict mapping template name to description.
        """
        return {name: tpl.description for name, tpl in self._templates.items()}
