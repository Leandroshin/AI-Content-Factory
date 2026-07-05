# Prompt for External Idea LLMs Without Repository Access

Use this prompt when asking an external LLM for ideas about AI Content Factory
and the model cannot inspect the GitHub repository or local files.

Copy everything from the section below into the external LLM chat.

---

# Context for External LLM

You are helping brainstorm future ideas for a project called **AI Content
Factory**.

You cannot inspect the repository directly, so use only the context below. If
you are uncertain, mark it as an assumption. Do not claim that you read files.

## What the Project Is

AI Content Factory is a modular platform that behaves like a company made of AI
employees. Each employee belongs to a department and works through deterministic
pipelines. The goal is to produce, approve, publish, and analyze content with
real external tools only when explicitly configured and budget-limited.

The project is not trying to reinvent mature tools. It should use adapters for
real providers and libraries instead of building everything from scratch.

## Current Architecture

The core inheritance pattern is:

```text
SpecialistEmployee
  -> ProductionEmployee
      -> VideoEditorEmployee
      -> AudioEngineerEmployee
      -> ImageDesignerEmployee
      -> ScriptWriterEmployee
      -> AffiliateDealsEmployee
      -> future employees
```

The base department layer is:

```text
core/departments/base/
  employee.py   -> ProductionEmployee
  pipeline.py   -> StageResult, ProductionPipeline
  models.py     -> ProductionMetrics
```

New departments should follow this shape:

```text
core/departments/<department_name>/
  models.py
  pipeline.py
  employee.py
  __init__.py
```

If needed, they may also require:

```text
core/observability.py additions
demo_<department_name>.py
```

Existing major systems:

- `ProductionEmployee`: shared base for department employees.
- `ProductionPipeline`: deterministic stage machine.
- `StageResult`: output of each pipeline stage.
- `QualityRuntime`: rule-based quality validation.
- `ObservabilityProjector`: event-based snapshots and metrics.
- `ProviderControlCenter`: provider configuration panel state.
- `ProviderBudgetGuard`: blocks REAL provider calls without approval and limits.
- `TelegramAdapter`: real Telegram Bot API adapter with manual approval gate.
- `AffiliateDealsEmployee`: scores offers, prepares copy, compliance, creative,
  audience plan, and Telegram-ready publishing plan.
- `ContentProductionWorkflow`: Brief -> Script -> Audio -> Image -> Video ->
  Quality -> Observability.

Current real/simulated adapters include:

- ElevenLabs for text-to-speech.
- FFmpeg for local render.
- Telegram Bot API for controlled publishing.
- GitHub, YouTube, Playwright, and other provider contracts.

Current important rules:

- Do not propose spam automation.
- Do not propose bypassing platform policies.
- Do not propose automated buying, trading, gambling, or financial execution.
- Do not expose or request API keys.
- Real provider calls must be opt-in, budget-limited, and owner-approved.
- WhatsApp should remain manual or highly controlled unless official APIs and
  compliance are clearly defined.
- Prefer deterministic MVPs first, then optional AI/provider upgrades.

## Current Product Direction

The current near-term direction is:

1. Turn Affiliate Deals into a real controlled publishing workflow.
2. Add a human approval queue before content is published.
3. Build a dashboard / 2.5D operational interface to see employees, tasks,
   approvals, costs, generated assets, and publishing status.
4. Add smarter content employees such as hook specialists, quality analysts,
   repurposing workers, publishing planners, and analytics/reporting workers.

## What I Want From You

Generate useful ideas for this factory.

You may propose:

- New employees.
- New departments.
- New workflows.
- New tool adapters/providers.
- Approval or quality gates.
- Observability/analytics extensions.
- UI/2.5D dashboard concepts.
- Monetization or content-funnel ideas.

For each idea, use this format:

```markdown
# Idea Name

## Summary
Explain the idea in 3 to 6 lines.

## Type
Choose one:
- Employee
- Department
- Gateway / Infrastructure
- Workflow
- Adapter / Provider
- UI / Dashboard
- Analytics / Observability

## Why It Matters
What problem does it solve? What impact could it have?

## Fit With Current Architecture
Use the actual project concepts:
- ProductionEmployee
- ProductionPipeline
- StageResult
- QualityRuntime
- ProviderControlCenter
- ProviderBudgetGuard
- TelegramAdapter
- AffiliateDealsEmployee
- ContentProductionWorkflow
- ObservabilityProjector

## Suggested Files
Suggest files only. Do not write code.
Prefer:
- core/departments/<name>/models.py
- core/departments/<name>/pipeline.py
- core/departments/<name>/employee.py
- core/departments/<name>/__init__.py
- demo_<name>.py

## Pipeline Stages
List deterministic stages in order.

## Inputs
List the data needed.

## Outputs
List the data produced.

## Quality Rules
List deterministic validations.

## Risks and Compliance
What can go wrong? How should the project prevent it?

## MVP
What is the smallest useful version?

## Future Evolution
How can it grow later?

## Priority
Choose:
- Now
- Soon
- Later

## Confidence
Choose:
- High
- Medium
- Low

## Assumptions
List anything you assumed because you cannot read the repo.
```

## Extra Instructions

- Do not generate code.
- Do not ask to modify GitHub.
- Do not invent that you inspected files.
- Do not suggest changing existing contracts.
- Do not suggest a new generic runtime unless absolutely necessary.
- Prefer small, testable, deterministic MVPs.
- If an idea uses an external API, mention official docs that should be checked
  later by Codex.
- If an idea could create spam, financial risk, legal risk, or platform-policy
  risk, design the safety gate first.

Start by giving the **top 5 ideas**, ranked by impact and implementation
sequence. Then expand the best 3 ideas using the full format above.
