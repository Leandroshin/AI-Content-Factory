"""Foundation demo for the PromptBuilder and TemplateRegistry.

Validates template registration, rendering, placeholder validation,
error handling, and deterministic behavior.
"""

from __future__ import annotations

from core.llm import PromptBuilder, PromptTemplate, TemplateRegistry


# ------------------------------------------------------------------
# Scenario 1: Register templates in the registry
# ------------------------------------------------------------------


def scenario_register_templates() -> None:
    """Register multiple templates and verify they are stored."""
    registry = TemplateRegistry()

    t1 = PromptTemplate.create(
        name="greeting",
        template="Hello, {name}! Welcome to {project}.",
        required_placeholders=["name", "project"],
        description="A simple greeting template.",
    )
    t2 = PromptTemplate.create(
        name="code_review",
        template="Review the following {language} code:\n\n{code}",
        required_placeholders=["language", "code"],
        description="Template for code review prompts.",
    )

    registry.register(t1)
    registry.register(t2)

    assert registry.exists("greeting")
    assert registry.exists("code_review")
    assert not registry.exists("nonexistent")
    print(f"[PASS] register_templates             | registered={list(registry.list_templates().keys())}")


# ------------------------------------------------------------------
# Scenario 2: Render a template correctly
# ------------------------------------------------------------------


def scenario_render_correct() -> None:
    """Render a template with all required variables."""
    template = PromptTemplate.create(
        name="greeting",
        template="Hello, {name}! Welcome to {project}.",
        required_placeholders=["name", "project"],
    )

    result = PromptBuilder.render(template, {"name": "Alice", "project": "AI Factory"})

    assert result.success
    assert result.rendered == "Hello, Alice! Welcome to AI Factory."
    assert result.variables_missing == []
    assert result.template_name == "greeting"
    print(f"[PASS] render_correct                 | rendered='{result.rendered}'")


# ------------------------------------------------------------------
# Scenario 3: Required placeholder missing
# ------------------------------------------------------------------


def scenario_missing_placeholder() -> None:
    """Render fails when a required placeholder is missing."""
    template = PromptTemplate.create(
        name="greeting",
        template="Hello, {name}! Welcome to {project}.",
        required_placeholders=["name", "project"],
    )

    result = PromptBuilder.render(template, {"name": "Alice"})

    assert not result.success
    assert "project" in result.variables_missing
    assert result.rendered == template.template  # unmodified
    print(f"[PASS] missing_placeholder            | missing={result.variables_missing}")


# ------------------------------------------------------------------
# Scenario 4: Placeholder absent from variables dict (not in required)
# ------------------------------------------------------------------


def scenario_optional_placeholder_missing() -> None:
    """A placeholder not in required list but absent from variables raises KeyError."""
    template = PromptTemplate.create(
        name="optional_test",
        template="Hello {name}, your balance is {balance}.",
        required_placeholders=["name"],
    )

    result = PromptBuilder.render(template, {"name": "Bob"})

    assert not result.success
    assert "balance" in result.variables_missing
    print(f"[PASS] optional_placeholder_missing    | detected missing='{result.variables_missing}'")


# ------------------------------------------------------------------
# Scenario 5: Multiple templates render differently
# ------------------------------------------------------------------


def scenario_multiple_templates() -> None:
    """Render different templates with different variable sets."""
    code_template = PromptTemplate.create(
        name="code_review",
        template="Review {language} code by {author}:\n```\n{code}\n```",
        required_placeholders=["language", "author", "code"],
    )
    summary_template = PromptTemplate.create(
        name="summary",
        template="Summarize {topic} in {max_words} words.",
        required_placeholders=["topic", "max_words"],
    )

    code_result = PromptBuilder.render(
        code_template,
        {"language": "Python", "author": "Charlie", "code": "print('hello')"},
    )
    summary_result = PromptBuilder.render(
        summary_template,
        {"topic": "quantum computing", "max_words": "100"},
    )

    assert code_result.success
    assert summary_result.success
    assert "Python" in code_result.rendered
    assert "quantum computing" in summary_result.rendered
    assert code_result.template_name == "code_review"
    assert summary_result.template_name == "summary"
    print(f"[PASS] multiple_templates             | code='{code_result.rendered[:30]}...' "
          f"summary='{summary_result.rendered}'")


# ------------------------------------------------------------------
# Scenario 6: Template registry list_templates
# ------------------------------------------------------------------


def scenario_list_templates() -> None:
    """List registered templates with descriptions."""
    registry = TemplateRegistry()

    registry.register(PromptTemplate.create(
        name="a", template="A", description="First template",
    ))
    registry.register(PromptTemplate.create(
        name="b", template="B", description="Second template",
    ))

    listing = registry.list_templates()
    assert "a" in listing
    assert "b" in listing
    assert listing["a"] == "First template"
    assert listing["b"] == "Second template"
    assert len(listing) == 2
    print(f"[PASS] list_templates                 | count={len(listing)} "
          f"names={list(listing.keys())}")


# ------------------------------------------------------------------
# Scenario 7: Unregister a template
# ------------------------------------------------------------------


def scenario_unregister_template() -> None:
    """Unregister removes the template from the registry."""
    registry = TemplateRegistry()
    t = PromptTemplate.create(name="temp", template="Temporary")
    registry.register(t)
    assert registry.exists("temp")

    registry.unregister("temp")
    assert not registry.exists("temp")
    print(f"[PASS] unregister_template            | temp removed, "
          f"remaining={list(registry.list_templates().keys())}")


# ------------------------------------------------------------------
# Scenario 8: Get nonexistent template raises KeyError
# ------------------------------------------------------------------


def scenario_nonexistent_template() -> None:
    """Getting an unregistered template raises KeyError."""
    registry = TemplateRegistry()

    try:
        registry.get("ghost")
        assert False, "Expected KeyError was not raised."
    except KeyError as exc:
        assert "ghost" in str(exc)
        print(f"[PASS] nonexistent_template          | error='{exc}'")


# ------------------------------------------------------------------
# Scenario 9: Duplicate registration raises ValueError
# ------------------------------------------------------------------


def scenario_duplicate_registration() -> None:
    """Registering the same template name twice raises ValueError."""
    registry = TemplateRegistry()
    t = PromptTemplate.create(name="dup", template="Original")
    registry.register(t)

    t2 = PromptTemplate.create(name="dup", template="Duplicate")
    try:
        registry.register(t2)
        assert False, "Expected ValueError was not raised."
    except ValueError as exc:
        assert "dup" in str(exc)
        print(f"[PASS] duplicate_registration        | error='{exc}'")


# ------------------------------------------------------------------
# Scenario 10: Deterministic rendering (same input → same output)
# ------------------------------------------------------------------


def scenario_deterministic_render() -> None:
    """Same template + same variables always produces the same rendered output."""
    template = PromptTemplate.create(
        name="deterministic",
        template="Result: {a} + {b} = {result}",
    )

    vars_in = {"a": "2", "b": "3", "result": "5"}
    r1 = PromptBuilder.render(template, vars_in)
    r2 = PromptBuilder.render(template, vars_in)
    r3 = PromptBuilder.render(template, vars_in)

    assert r1.rendered == "Result: 2 + 3 = 5"
    assert r1.rendered == r2.rendered == r3.rendered
    print(f"[PASS] deterministic_render           | output='{r1.rendered}' "
          f"(3 identical renders)")


# ------------------------------------------------------------------
# Scenario 11: Unregister nonexistent raises KeyError
# ------------------------------------------------------------------


def scenario_unregister_nonexistent() -> None:
    """Unregistering a nonexistent template raises KeyError."""
    registry = TemplateRegistry()

    try:
        registry.unregister("phantom")
        assert False, "Expected KeyError was not raised."
    except KeyError as exc:
        assert "phantom" in str(exc)
        print(f"[PASS] unregister_nonexistent        | error='{exc}'")


# ------------------------------------------------------------------
# Main
# ------------------------------------------------------------------


def main() -> None:
    print("=" * 62)
    print("PromptBuilder + TemplateRegistry Demo")
    print("=" * 62)
    print()

    scenario_register_templates()
    scenario_render_correct()
    scenario_missing_placeholder()
    scenario_optional_placeholder_missing()
    scenario_multiple_templates()
    scenario_list_templates()
    scenario_unregister_template()
    scenario_nonexistent_template()
    scenario_duplicate_registration()
    scenario_deterministic_render()
    scenario_unregister_nonexistent()

    print()
    print("=" * 62)
    print("All PromptBuilder scenarios passed.")
    print("=" * 62)


if __name__ == "__main__":
    main()
