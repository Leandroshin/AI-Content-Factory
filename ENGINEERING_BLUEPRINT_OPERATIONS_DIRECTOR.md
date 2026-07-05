# Engineering Blueprint — Operations Director

## Purpose

This document is the engineering blueprint for the future `Operations Director`
layer of the AI Company.

The Operations Director is responsible for operational coordination across the
company. It does not execute tasks, it does not replace the runtime, and it does
not alter contracts or models.

The blueprint is technical and implementation-oriented. It does not introduce
behavior, code, or public API changes.

---

## 1. Mission of the Operations Director

The Operations Director is the operational coordination layer that transforms
strategic direction into manageable operational flow.

It will likely answer questions such as:

- How should a task enter operational flow?
- Which employee should receive the work?
- Which department should own the routing?
- When should a task be redistributed?
- When should a task be escalated back to the CEO / Orchestrator?
- How should queues be organized and monitored?

```text
Strategic Decision → Operations Coordination → Operational Flow
```

The Operations Director coordinates work. It does not own company strategy.

---

## 2. Exclusive Responsibilities

The future implementation will likely own:

- operational task intake;
- workload coordination;
- assignment coordination;
- queue organization;
- capacity analysis;
- availability matching;
- redistribution decisions at operational level;
- blockage handling;
- retry coordination;
- idle management;
- collaboration coordination;
- operational dashboard projection;
- operational state aggregation;
- escalation preparation for the Orchestrator.

The Operations Director is the operational conductor, not the strategic owner.

---

## 3. What Does NOT Belong to the Operations Director

The future Operations Director must not own:

- company strategy;
- AI model strategy;
- platform integration strategy;
- knowledge lifecycle strategy;
- direct task execution;
- engine execution details;
- provider authentication;
- runtime lifecycle ownership;
- observability implementation;
- persistence implementation;
- policy engine implementation.

### Explicit boundaries

- The CEO / Orchestrator makes strategic decisions.
- The Company Runtime tracks company state.
- The AI Director decides AI usage strategy.
- The Platform Director manages external integrations.
- The Knowledge Director manages knowledge lifecycle strategy.

---

## 4. Probable Engineering Structures

The future implementation may include:

- `OperationsDirector`
- `OperationsDirectorState`
- `OperationsManager`
- `TaskDispatcher`
- `WorkloadAnalyzer`
- `AssignmentEngine`
- `QueueCoordinator`
- `CapacityMonitor`
- `AvailabilityManager`
- `EscalationManager`
- `BlockDetection`
- `RetryCoordinator`
- `IdleManager`
- `CollaborationCoordinator`
- `OperationsDashboardBuilder`
- `OperationsAdapterLayer`
- `OperationsProjection`
- `OperationsReporter`

These are implementation candidates, not public API commitments.

---

## 5. Immutability Expectations

The following information should likely be treated as immutable or effectively
immutable once established:

- operational policy templates;
- queue structure definitions;
- assignment rule definitions;
- capacity thresholds;
- escalation thresholds;
- redistribution rule definitions;
- dashboard projection schema.

Mutable information will likely include:

- current queue state;
- current workload pressure;
- current availability state;
- current assignment state;
- current blockage state;
- current retry state;
- current idle state;
- current operational snapshot.

---

## 6. How a Task Enters Operations

A Task enters operations after it has a strategic reason to be processed.

The future flow will likely be:

1. strategic need appears;
2. Orchestrator approves direction;
3. Operations Director receives the task;
4. operational intake registers it;
5. queue placement is determined;
6. assignment and routing begin.

```text
Task Creation → Strategic Approval → Operations Intake → Queue Placement
```

The Operations Director does not create the task. It coordinates its operational
entry.

---

## 7. How Employees Are Chosen

Employee selection will likely be based on:

- availability;
- workload fit;
- skill fit;
- department fit;
- collaboration context;
- policy constraints;
- current blockage state;
- retry context.

```text
Task → Candidate Pool → Availability/Skill/Workload Analysis → Employee Choice
```

The Operations Director should coordinate selection, not replace strategic
ownership or employee identity.

---

## 8. How Departments Receive Work

Departments receive work as part of operational routing.

The future implementation will likely:

- respect department ownership;
- honor routing constraints;
- provide local context to departments;
- monitor departmental saturation;
- support department-level redistributions.

```text
Task → Department Routing → Department Ownership
```

Departments are the domain boundary for operational work; the Operations
Director coordinates access to that boundary.

---

## 9. Queue Organization

The future system will likely organize queues by:

- priority;
- department;
- employee availability;
- workflow stage;
- blockage status;
- escalation level;
- retry eligibility.

```text
[Waiting] → [Ready] → [Assigned] → [Blocked] → [Escalated] → [Done]
```

Queues are operational coordination structures, not execution engines.

---

## 10. Blockage Handling

The Operations Director will likely detect and handle blockages by observing:

- unavailable employees;
- overloaded departments;
- stalled workflows;
- policy conflicts;
- missing skills;
- external integration delays;
- retry exhaustion.

```text
Signal Stagnation → Block Detection → Operational Response
```

Responses may include redistribution, pause, retry, or escalation.

---

## 11. Redistribution

When a Task cannot continue as originally planned, the Operations Director may
redistribute it conceptually.

Possible redistribution triggers:

- employee unavailable;
- department saturated;
- workflow stalled;
- policy restriction;
- capacity imbalance;
- escalation request.

```text
Task → Redistribute → New Employee / New Department / Escalation
```

Redistribution must be controlled and traceable.

---

## 12. When a Task Returns to the CEO / Orchestrator

A Task should be returned to the Orchestrator when:

- the operational path is blocked beyond operational authority;
- strategic trade-off is required;
- policy interpretation exceeds operational scope;
- cross-department conflict cannot be resolved locally;
- retry limits are exhausted;
- company-wide reprioritization is needed.

```text
Operations Director → Escalation → Orchestrator
```

---

## 13. Runtime Updates

The Operations Director will likely update the Runtime with:

- queue state;
- workload state;
- assignment state;
- blockage state;
- retry state;
- progress signals;
- idle signals;
- escalation signals.

The Runtime remains the state holder; Operations Director is the coordinator.

---

## 14. Observability Updates

Observability will likely receive:

- operational queue health;
- overload signals;
- assignment summaries;
- blockage indicators;
- redistribution indicators;
- retry pressure;
- escalation summaries.

```text
Operations Director → Runtime Snapshot → Observability → Dashboard
```

The dashboard is a projection of operations, not the operator itself.

---

## 15. Relationship with Other Layers

### CEO / Orchestrator

Receives escalations and strategic exceptions.

### Company Runtime

Receives operational state updates and progress summaries.

### AI Director

May be consulted only for AI capability availability in future phases, but does
not own operations strategy.

### Platform Director

May provide integration-dependent availability signals, but does not own
operations.

### Knowledge Director

May provide historical learning signals for better future routing, but does not
manage the operational flow.

### Departments

Receive work, localize context, and report progress.

### Employees

Receive tasks, participate in work, and contribute local signals.

### Tasks

Enter the operational flow and carry work intent.

### Workflows

Define the route and stage progression.

### Results

Return as operational outcomes and may trigger escalation, learning, or
closure.

### Policies

Constrain the operational path.

### Events

Signal task movement, blockage, progress, and completion.

### Observability

Consumes operational snapshots and exposes them for visualization.

---

## 16. Deterministic vs IA-Enabled Decisions

### Deterministic

- queue placement rules;
- capacity thresholds;
- availability checks;
- assignment eligibility;
- retry limits;
- escalation thresholds;
- blockage classification rules.

### Potentially IA-assisted in the future

- workload balancing suggestions;
- redistribution recommendations;
- collaboration pattern analysis;
- bottleneck prediction;
- operational summarization;
- fallback suggestion generation.

The rule is:

> Safety, eligibility, and escalation boundaries should remain deterministic.

---

## 17. ASCII Operational Flow

```text
Task
  ↓
Operations Director
  ↓
Queue / Workload Analysis
  ↓
Employee Selection
  ↓
Department Routing
  ↓
Workflow Progress
  ↓
Result
  ↓
Runtime Update
  ↓
Observability Update
```

```text
Operations Director
  ├── Task Dispatcher
  ├── Workload Analyzer
  ├── Assignment Engine
  ├── Queue Coordinator
  ├── Capacity Monitor
  ├── Availability Manager
  ├── Escalation Manager
  ├── Block Detection
  ├── Retry Coordinator
  ├── Idle Manager
  ├── Collaboration Coordinator
  ├── Operations Dashboard Builder
  └── Operations Adapter Layer
```

---

## 18. What Does Not Belong to the Operations Director

The future Operations Director must not become:

- the CEO / Orchestrator;
- the Company Runtime;
- the AI Director;
- the Platform Director;
- the Knowledge Director;
- a task executor;
- a workflow engine;
- an observability engine;
- a persistence layer;
- a policy engine;
- a direct engine caller.

---

## 19. Simplification Expectations

Future implementation should aim for:

- a single operational intake point;
- small, purpose-specific coordinators;
- narrow adapters and bridges;
- explicit escalation boundaries;
- simple queue semantics;
- projections instead of duplicated state;
- deterministic operational gates.

---

## 20. Final Blueprint Statement

This blueprint defines how the AI Company will later coordinate operational
flow while preserving the contract-first architecture. It is a future
implementation guide only.
