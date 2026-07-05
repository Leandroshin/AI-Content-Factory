# AI Content Factory

AI Content Factory is a modular platform for building, automating, publishing, and analyzing AI-assisted content. The project is designed to stay **niche-agnostic**: niche-specific details live in configuration, while the platform architecture remains stable.

## Architecture Overview

The repository follows a layered architecture centered on a shared `core/` foundation and isolated `engines/` for domain-specific capabilities.

- `core/config` — architectural foundation for configuration contracts
- `core/container` — dependency container contracts
- `core/departments` — department representation contracts
- `core/events` — domain event contracts
- `core/knowledge` — shared knowledge contracts
- `core/logging` — logging architecture contracts
- `core/models` — shared data models
- `core/orchestrator` — orchestration contracts
- `core/pipeline` — pipeline contracts
- `core/prompts` — prompt-management contracts
- `engines/base` — shared engine contracts
- `engines/script` — script engine foundation

## Repository Organization

- `core/` — central infrastructure and cross-cutting contracts
- `engines/` — domain modules and concrete engine foundations
- `config/` — global configuration files
- `projects/` — project or niche-specific configuration
- `docs/` — documentation and architectural records
- `tests/` — test suite structure
- `assets/` — static resources
- `output/` — generated artifacts
- `temp/` — temporary processing files

## Current Stage

The project now has a concrete production layer:

- Base department layer with `ProductionEmployee` and `ProductionPipeline`
- Video, Audio, Image, Script, and Affiliate Deals departments
- Content workflow: Brief -> Script -> Audio -> Image -> Video -> Quality -> Observability
- Provider control, budget guard, masked API settings, Telegram publishing, and interactive provider-panel preview
- Deterministic demos for regression and architecture proof

See `AGENTS.md` for the latest architectural state and next steps.

## External LLM Inbox

External LLMs that can read GitHub but cannot run the local project should not
modify production code directly. They should write Markdown proposals in:

```text
docs/external_llm_inbox/qwen/
```

Use the templates in `docs/external_llm_inbox/`. Codex will later review,
validate, and implement accepted proposals with tests.

## Architectural Principles

- Clean separation of responsibilities
- Low coupling and high cohesion
- Contract-first design
- Niche as configuration, not code
- Engines remain isolated from one another
- Infrastructure remains replaceable and testable

## Notes

Generated artifacts in `output/` and local secrets are intentionally ignored by
Git. Real external-provider calls must remain opt-in and budget-limited.
