# Company Runtime Architecture — AI Company

## Purpose

This document defines the conceptual `Company Runtime` layer of the AI Company.

The Company Runtime is the organizational layer responsible for coordinating the
company while work is in progress. It is not a scheduler, not an engine, not a
provider, and not a behavior implementation.

It exists to describe how the company is observed, maintained, and kept in a
coherent running state during execution.

---

## 1. Role of the Company Runtime

The Company Runtime is the layer that conceptually manages the live state of the
AI Company.

It answers questions such as:

- Is the company running?
- Is the company idle?
- Is the company paused?
- Are there blocked areas?
- Is the organization in maintenance?
- Is there an error state affecting the company?

```text
Company Runtime
   ├── company state
   ├── operational visibility
   ├── progress tracking
   ├── blockage awareness
   └── organizational coordination
```

The Runtime is the conceptual heartbeat of the company.

---

## 2. Responsibilities Exclusive to the Runtime

The Company Runtime conceptually owns:

- global company state management;
- lifecycle interpretation of the running company;
- state aggregation across subsystems;
- progress visibility across tasks and workflows;
- blockage awareness at company level;
- runtime health representation;
- coordination signals for observability;
- runtime-to-orchestrator conceptual reporting.

These responsibilities are organizational, not operational.

---

## 3. What Does Not Belong to the Runtime

The Company Runtime does **not** own:

- task execution logic;
- workflow execution logic;
- engine behavior;
- provider integration;
- business rules implementation;
- policy evaluation internals;
- persistence;
- analytics computation;
- message bus behavior;
- queue implementation;
- worker orchestration details.

The Runtime may reflect these concerns conceptually, but it must not implement
them.

---

## 4. Global Company States

The company may conceptually be in the following global states:

- `Idle`
- `Running`
- `Paused`
- `Stopping`
- `Maintenance`
- `Error`
- `Degraded`
- `Recovering`
- `Booting`
- `ShuttingDown`

```text
Booting → Idle → Running → Paused → Running → Stopping → ShuttingDown
                    ↘ Maintenance ↗
                    ↘ Error ↘ Recovering ↗
```

These states describe the company as a whole, not any single subsystem.

---

## 5. How the Runtime Tracks Departments

The Runtime conceptually tracks Departments by observing:

- active workload;
- local progress;
- blocked state;
- policy pressure;
- ownership boundaries;
- relative health.

```text
Runtime
  └── Department State Snapshot
        ├── workload
        ├── progress
        ├── blockage
        ├── policy impact
        └── health
```

The Runtime does not operate Departments. It only keeps their state visible at
the company level.

---

## 6. How the Runtime Tracks Employees

The Runtime conceptually tracks Employees by observing:

- availability;
- active participation;
- local blockages;
- skill relevance;
- workload fit;
- collaboration context.

```text
Runtime
  └── Employee State Snapshot
        ├── availability
        ├── participation
        ├── blockage
        ├── skills
        └── collaboration
```

Employees remain independent conceptual contributors. The Runtime does not own
their behavior.

---

## 7. How the Runtime Tracks Tasks

The Runtime tracks Tasks conceptually by following:

- task creation;
- task prioritization;
- task assignment boundary;
- task progress;
- task blockage;
- task completion visibility.

```text
Task Lifecycle
  ├── Created
  ├── Prioritized
  ├── Routed
  ├── In Progress
  ├── Blocked
  └── Completed
```

The Runtime surfaces the lifecycle state but does not execute the task.

---

## 8. How the Runtime Tracks Workflows

The Runtime tracks Workflows by keeping visibility on:

- active stage;
- current department;
- current employee involvement;
- next conceptual step;
- progression status;
- workflow blockage.

```text
Workflow
  ├── Stage 1
  ├── Stage 2
  ├── Stage 3
  └── Result
```

The Runtime treats workflows as running paths of meaning, not as executable
pipelines.

---

## 9. How the Runtime Tracks Queues

The Runtime conceptually tracks queues as:

- waiting items;
- active items;
- blocked items;
- escalated items;
- completed items.

```text
[Waiting] → [Active] → [Blocked] → [Escalated] → [Completed]
```

The Runtime may expose queue state, but it does not implement queue mechanics.

---

## 10. How the Runtime Detects Blockages

The Runtime conceptually detects blockages by observing:

- policy constraints;
- unavailable employees;
- overloaded departments;
- stalled workflows;
- missing skills;
- unresolved dependencies;
- state transitions that stop progressing.

```text
Signal Stagnation → Runtime Blockage Awareness
```

Blockage detection is an architectural awareness concept, not a computational
implementation.

---

## 11. How the Runtime Registers Progress

Progress is registered as a conceptual delta in company state.

The Runtime may track:

- task advancement;
- workflow advancement;
- departmental progress;
- employee contribution progress;
- result completion signals;
- knowledge accumulation signals.

```text
Before State → Progress Signal → After State
```

Progress is the change in state, not a direct action.

---

## 12. How the Runtime Supplies Observability

The Runtime is a major source of truth for Observability.

It provides:

- company state;
- department snapshots;
- employee snapshots;
- task progress;
- workflow progress;
- queue pressure;
- blockage signals;
- health signals.

```text
Company Runtime → Observability Layer → 2.5D Interface
```

Observability reads the Runtime. It does not drive it.

---

## 13. How the Runtime Talks to the CEO / Orchestrator

The Runtime conceptually reports to the CEO layer, represented by the future
Orchestrator.

The Runtime may inform the CEO about:

- global state changes;
- major blockages;
- maintenance mode;
- company health;
- progress summaries;
- priority pressure;
- recovery status.

```text
Company Runtime ↔ CEO / Orchestrator
```

The Runtime informs. The Orchestrator decides at the strategic level.

---

## 14. How the Runtime Avoids Coupling with Engines and Providers

The Runtime must remain detached from:

- engine implementations;
- provider implementations;
- provider selection details;
- model invocation logic;
- prompt rendering logic;
- execution mechanics.

It may observe the effect of those layers conceptually, but it must never own
their execution path.

```text
Runtime ──X──> Engines
Runtime ──X──> Providers
```

The Runtime is organizational; Engines and Providers are implementation layers.

---

## 15. Runtime Lifecycle

```text
Booting → Idle → Running → Paused → Running → Stopping → ShuttingDown
                     ↘ Maintenance ↗
                     ↘ Error → Recovering ↗
```

### Lifecycle meanings

- `Booting`: company is initializing conceptually.
- `Idle`: company is available but not actively processing.
- `Running`: company is actively coordinating work.
- `Paused`: company is intentionally halted.
- `Maintenance`: company is in controlled maintenance mode.
- `Error`: company has encountered a global problem.
- `Recovering`: company is returning to a healthy state.
- `Stopping`: company is preparing to stop.
- `ShuttingDown`: company is terminating the runtime session.

---

## 16. Conceptual Example

```text
1. A Task appears.
2. The Runtime marks the company as Running.
3. A Department receives the Task.
4. An Employee is chosen conceptually.
5. A Workflow begins.
6. Progress is registered.
7. A blockage is detected.
8. Observability receives the state.
9. The Orchestrator is informed.
10. The company reaches a Result.
```

This example is conceptual only.

---

## 17. Architectural Boundaries

The Company Runtime must never become:

- a scheduler;
- a worker system;
- an event bus;
- an analytics engine;
- a persistence layer;
- a provider manager;
- an engine runner;
- a policy evaluator.

It must remain a conceptual control layer for the running company state.

---

## 18. Future Evolution

This architecture may later support concrete runtime coordination, but only if
future missions explicitly authorize implementation.

Until then, the Company Runtime remains a conceptual layer that helps the AI
Company stay coherent while work is in progress.
