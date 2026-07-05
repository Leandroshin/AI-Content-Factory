# Engineering Blueprint — Company Runtime

## Purpose

This document is the engineering blueprint for the `Company Runtime` layer of
the AI Company.

It converts the conceptual runtime architecture into a future implementation
plan. It is not code, it does not alter contracts, and it does not introduce
runtime behavior.

---

## 1. Future Responsibilities of the Company Runtime

The future implementation will likely own:

- company-wide runtime state;
- lifecycle coordination of the company session;
- task registration tracking;
- queue visibility and pressure tracking;
- blockage awareness;
- progress aggregation;
- runtime projections for observability;
- state projection for the 2.5D interface;
- conceptual reporting to the Orchestrator;
- synchronization of transient company state.

The runtime should remain the top-level coordinator of live company state, not
the executor of business work.

---

## 2. Classes Likely to Exist

The future codebase will likely need a small but explicit set of classes.

### Core runtime classes

- `CompanyRuntime`
- `CompanyRuntimeState`
- `CompanyRuntimeLifecycle`
- `CompanyRuntimeSnapshot`
- `CompanyRuntimeRegistry`
- `CompanyRuntimeManager`
- `CompanyRuntimeController`
- `CompanyRuntimeMonitor`
- `CompanyRuntimeReporter`
- `CompanyRuntimeCache`

### Coordination helpers

- `TaskRuntimeTracker`
- `WorkflowRuntimeTracker`
- `DepartmentRuntimeTracker`
- `EmployeeRuntimeTracker`
- `QueueRuntimeTracker`
- `BlockageDetector`
- `ProgressTracker`
- `RuntimeStateAggregator`
- `RuntimeProjectionBuilder`

### Projection classes

- `RuntimeObservabilityProjection`
- `RuntimeInterface2p5DProjection`

The names are intentionally descriptive so implementation later can remain easy
to navigate.

---

## 3. Probable Interfaces and Collaboration Points

The future implementation will likely rely on interfaces or abstract service
boundaries for:

- Orchestrator communication;
- Department state reporting;
- Employee state reporting;
- Task registration;
- Workflow stage visibility;
- Result intake;
- Knowledge update signaling;
- Event emission signaling;
- Policy constraint awareness;
- Observability projections.

```text
CompanyRuntime
  ├── OrchestratorGateway
  ├── DepartmentStateReader
  ├── EmployeeStateReader
  ├── TaskStateReader
  ├── WorkflowStateReader
  ├── ResultStateReader
  ├── KnowledgeStateReader
  ├── EventPublisherView
  └── ProjectionBuilder
```

These are implementation collaboration points, not new public contracts.

---

## 4. Adapters and Bridges

To preserve low coupling, the future runtime should likely use adapters and
bridges instead of direct subsystem coupling.

### Likely adapters

- `OrchestratorRuntimeAdapter`
- `DepartmentRuntimeAdapter`
- `EmployeeRuntimeAdapter`
- `TaskRuntimeAdapter`
- `WorkflowRuntimeAdapter`
- `ResultRuntimeAdapter`
- `KnowledgeRuntimeAdapter`
- `EventsRuntimeAdapter`
- `PoliciesRuntimeAdapter`

### Likely bridges

- `RuntimeObservabilityBridge`
- `RuntimeInterfaceBridge`
- `RuntimeStateBridge`

Adapters should translate external subsystem state into runtime-friendly
representations.

Bridges should connect runtime snapshots to projections without introducing
behavioral coupling.

---

## 5. State Model

The runtime will need a clear separation between mutable and immutable data.

### Likely immutable data

- runtime identity;
- startup configuration snapshot;
- company topology reference;
- static environment metadata.

### Likely mutable transient state

- active company state;
- active task set;
- queue pressure;
- department health summary;
- employee availability summary;
- blockage signals;
- progress signals;
- recovery state;
- maintenance state;
- observability snapshot.

### Likely persisted state in the future

- runtime session history;
- lifecycle audit trail;
- blockage history;
- progress history;
- state transition history;
- summary checkpoints.

---

## 6. Runtime Cache Expectations

The future runtime may benefit from a transient cache for:

- latest company state;
- latest queue pressure;
- latest observability snapshot;
- latest projections for the 2.5D interface;
- recent blockage signals;
- recent progress deltas;
- current lifecycle state.

The cache should be treated as a read optimization and not as the source of
truth.

```text
State Source → Runtime Cache → Projections
```

---

## 7. Future Queue Concept

Queues are not implemented now, but the future runtime may need queue-aware
tracking for:

- waiting tasks;
- active tasks;
- blocked tasks;
- escalated tasks;
- completed tasks.

The runtime should track queue pressure conceptually through snapshots rather
than manage queue mechanics directly.

---

## 8. Runtime Lifecycle

The runtime lifecycle will likely include:

- `Booting`
- `Idle`
- `Running`
- `Paused`
- `Maintenance`
- `Degraded`
- `Recovering`
- `Stopping`
- `ShuttingDown`
- `Error`

```text
Booting → Idle → Running → Paused → Running → Stopping → ShuttingDown
                   ↘ Maintenance ↗
                   ↘ Degraded → Recovering ↗
                   ↘ Error ↗
```

Lifecycle management should remain explicit and centralized.

---

## 9. How the Runtime Will Converse with Other Subsystems

### Employees

The runtime will likely:

- read availability snapshots;
- observe task participation;
- expose employee state to observability;
- track blockages and progress.

### Departments

The runtime will likely:

- read local workload;
- read domain boundaries;
- receive routing or progress signals;
- aggregate departmental health.

### Tasks

The runtime will likely:

- register task lifecycle state;
- track routing and progress;
- observe blockage and completion state.

### Workflows

The runtime will likely:

- track current stage;
- track stage transitions;
- surface workflow progress;
- surface blocked or paused paths.

### Results

The runtime will likely:

- register outcome state;
- propagate completion signals;
- trigger observability refreshes.

### Knowledge

The runtime will likely:

- observe learning updates;
- refresh company learning state;
- expose knowledge growth signals.

### Events

The runtime will likely:

- consume event signals as state change markers;
- publish runtime-visible events for observability.

### Policies

The runtime will likely:

- read constraint signals;
- mark blocked paths;
- avoid violating policy-defined boundaries.

### Observability

The runtime will likely:

- build readable snapshots;
- push projection updates;
- expose health and progress summaries.

---

## 10. Responsibilities That Do Not Belong to the Runtime

The future runtime implementation must not own:

- engine execution;
- provider selection;
- prompt rendering;
- business rule evaluation;
- direct employee behavior;
- direct department execution;
- analytics computation;
- persistence logic;
- event bus mechanics;
- queue mechanics;
- policy engine logic.

These remain separate concerns.

---

## 11. Expected Projection Outputs

The runtime will likely produce projections for:

- observability;
- 2.5D interface;
- orchestrator summaries;
- company health summaries;
- blockage overviews;
- progress overviews.

Projection objects should be read-only views derived from runtime state.

---

## 12. Responsibilities by Future Component

### `CompanyRuntime`

- orchestrates runtime state.

### `CompanyRuntimeState`

- holds mutable runtime session state.

### `CompanyRuntimeRegistry`

- stores runtime-scoped references and snapshots.

### `CompanyRuntimeManager`

- coordinates lifecycle transitions.

### `CompanyRuntimeController`

- exposes entry points for future orchestration calls.

### `CompanyRuntimeMonitor`

- observes health, progress, and blockages.

### `CompanyRuntimeReporter`

- prepares runtime summaries for external layers.

### `CompanyRuntimeCache`

- stores transient state for efficient reads.

### `RuntimeProjectionBuilder`

- converts runtime state into projections.

---

## 13. Simplification Expectations

When implementation begins, the following simplifications should be preferred:

- keep runtime state centralized;
- keep projections separate from the source of truth;
- avoid direct coupling to engines and providers;
- avoid duplicated trackers when a shared aggregator is sufficient;
- keep queue behavior conceptual unless a real implementation demands it;
- keep adapters narrow and purpose-specific.

---

## 14. Implementation Risks

The main implementation risks are:

- turning the runtime into a hidden execution engine;
- coupling runtime directly to business logic;
- duplicating state across too many trackers;
- mixing transient projections with persistent records;
- making the runtime aware of engine/provider internals;
- creating too many manager classes too early.

---

## 15. Final Blueprint Statement

This blueprint is the implementation-oriented companion to
`COMPANY_RUNTIME_ARCHITECTURE.md`. It preserves the contract-first foundation
and prepares the runtime layer for future engineering without forcing
behavioral decisions now.
