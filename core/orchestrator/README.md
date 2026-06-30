# Core Orchestrator

## Responsibility

This package defines the architectural foundation for the AI Content Factory
orchestrator.

## Scope of this module

- Define orchestration contracts and core execution models
- Keep orchestration fully decoupled from engines
- Provide a stable public surface for future coordination logic

## What this module does NOT do

- Does not execute engines
- Does not create a functional pipeline
- Does not call AI
- Does not create workflows
- Does not create automation
- Does not maintain global state

## Public interface

- `OrchestratorContext`
- `ExecutionPlan`
- `ExecutionStep`
- `ExecutionResult`
- `ExecutionStatus`
- `BaseOrchestrator`
- `OrchestratorContract`

## Future evolution

The orchestrator may later coordinate declarative steps without direct coupling
to concrete engines or external providers.
