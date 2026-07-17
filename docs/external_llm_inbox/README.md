# External LLM Inbox

This folder is a safe handoff area for ideas produced by external LLMs that can
read the GitHub repository but cannot run the local project.

External LLMs may add Markdown specs here. They must not modify `core/`,
`demo_*.py`, provider code, secrets, dependency files, or generated outputs.
Codex will later review these specs, decide what belongs in the architecture,
and implement the accepted parts with tests.

## Allowed Contributions

- New department ideas.
- New employee/persona specs.
- New tool adapter proposals.
- Workflow or funnel ideas.
- Monetization experiments.
- Compliance notes and risk analysis.
- UI/2.5D interaction concepts.

## Required Rules

- Write specs only. Do not implement production code here.
- Do not include API keys, tokens, passwords, cookies, phone numbers, or private
  account data.
- Mark assumptions clearly.
- Separate facts from guesses.
- Include source links when discussing external APIs, platform policies, or
  affiliate/advertising rules.
- Keep every idea compatible with the existing architecture:
  `SpecialistEmployee -> ProductionEmployee -> department employee`.
- New departments should be proposed as `models.py`, `pipeline.py`,
  `employee.py`, `__init__.py`, observability, and demo requirements.
- No spam automation, policy bypass, account creation automation, scraping abuse,
  or automated buying/trading.

## Where To Put Files

Use this structure:

```text
docs/external_llm_inbox/
  synthesis/
    YYYY-MM-DD_topic_synthesis.md
  claude/
    YYYY-MM-DD_short-topic.md
  qwen/
    YYYY-MM-DD_short-topic.md
```

Examples:

```text
docs/external_llm_inbox/qwen/2026-07-05_affiliate_growth_extensions.md
docs/external_llm_inbox/claude/2026-07-05_infoproducts_client_services.md
docs/external_llm_inbox/qwen/2026-07-05_market_research_department.md
docs/external_llm_inbox/synthesis/2026-07-05_external_llm_synthesis.md
```

Start from one of the templates in this folder:

- `IDEA_TEMPLATE.md`
- `EMPLOYEE_SPEC_TEMPLATE.md`
- `DEPARTMENT_SPEC_TEMPLATE.md`
- `PROMPT_FOR_EXTERNAL_IDEA_LLMS.md` for LLMs that cannot access GitHub
- `GPT_WEB_START_HERE.md` for GPT Web with GitHub access
- `CURRENT_HANDOFF.md` for the compact official state
- `DECISION_LEDGER.md` and `STATUS_TAXONOMY.md` before proposing changes

Codex will treat files in this inbox as proposals, not accepted source of truth.

## Local LLMs with workspace access

OpenCode, DeepSeek and other local models use a stricter corridor:

- read `LOCAL_LLM_WORK_PROTOCOL.md` before doing any work;
- start from `PROMPT_FOR_OPENCODE_DEEPSEEK.md`;
- write only under `docs/external_llm_inbox/deepseek/` or in the isolated
  prototype location allowed by that protocol;
- never treat a local-model proposal as implemented until Codex has reviewed,
  tested and explicitly accepted it.
- finish each session with `deepseek/SESSION_HANDOFF_TEMPLATE.md` and the
  root `HANDOFF_VALIDATION_CHECKLIST.md`.
