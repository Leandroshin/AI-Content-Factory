# Execution Flow Architecture — AI Company

## Purpose

This document defines the first conceptual execution flow of the AI Company.

It describes how a single Task can traverse the organization from creation to
organizational knowledge update.

This document is strictly architectural. It does **not** implement behavior,
classes, contracts, APIs, or runtime logic.

---

## 1. Flow Overview

The official conceptual execution flow is:

```text
Task Creation
   ↓
Company Runtime Registration
   ↓
CEO / Orchestrator Evaluation
   ↓
Department Routing
   ↓
Employee Selection
   ↓
Execution Context Preparation
   ↓
Prompt Construction
   ↓
Engine Call
   ↓
Result Production
   ↓
Events Publication
   ↓
Knowledge Update
   ↓
Employee Skills Update
   ↓
Runtime State Update
   ↓
Observability Update
   ↓
2.5D Interface Update
```

This is the first end-to-end conceptual flow that connects the company layers.

---

## 2. Step-by-Step Flow

### 2.1 Task Creation

A Task is created when a need, signal, or opportunity enters the company.

Responsibilities:

- `Organization`: provides the global structure for the need.
- `Department`: may originate or request the Task.
- `Employee`: may signal a need, but does not own the creation flow.
- `Company Runtime`: becomes aware of the new Task state.

Deterministic: yes.
IA allowed: no.

### 2.2 Registration by the Company Runtime

The Company Runtime conceptually registers that the Task now exists in the
company state.

Responsibilities:

- track that the Task is present;
- expose the task as part of the current company state;
- make the Task visible to observability and orchestrator layers.

Deterministic: yes.
IA allowed: no.

### 2.3 Evaluation by the Orchestrator

The CEO / Orchestrator conceptually evaluates the Task at strategic level.

Responsibilities:

- decide if the Task should proceed;
- determine strategic priority;
- approve or defer routing;
- enforce company-wide direction.

Deterministic: primarily yes, with future room for IA-assisted suggestions only.

### 2.4 Routing to the Appropriate Department

The Task is conceptually routed to the Department that owns the domain.

Responsibilities:

- `Department`: claims conceptual ownership.
- `Organization`: preserves structural boundaries.
- `Orchestrator`: resolves cross-department conflicts.

Deterministic: yes.
IA allowed: no.

### 2.5 Conceptual Employee Selection

The Department selects the most suitable Employee conceptually.

Responsibilities:

- `Department`: evaluates fit inside its domain.
- `Skills`: influence suitability.
- `Policies`: constrain validity.
- `Runtime`: ensures availability is visible.

Deterministic: primarily yes, with future room for IA-assisted ranking.

### 2.6 Execution Context Preparation

The conceptual execution context is prepared before any work begins.

Responsibilities:

- gather task context;
- gather department context;
- gather employee context;
- gather policy context;
- gather runtime context.

Deterministic: yes.
IA allowed: no.

### 2.7 Prompt Construction

A Prompt is conceptually constructed to guide the future engine interaction.

Responsibilities:

- `Prompt` subsystem: shape the request.
- `Employee`: may contribute contextual information.
- `Department`: may add domain framing.
- `Policies`: may constrain the prompt scope.

Deterministic: yes for structure, with future room for IA-assisted prompt
refinement.

### 2.8 Conceptual Engine Call

The Engine is called conceptually as the execution capability of the company.

Responsibilities:

- receive the prepared prompt;
- produce the conceptual output;
- respect contracts and policies;
- avoid leaking internal execution details.

Deterministic: no, future implementations may use IA here depending on engine
type.

### 2.9 Result Production

The Engine output is transformed conceptually into a Result.

Responsibilities:

- `Result`: records the official outcome;
- `Runtime`: registers outcome visibility;
- `Orchestrator`: observes strategic implications.

Deterministic: yes in transformation shape; actual content may later come from
IA depending on the engine.

### 2.10 Events Publication

Relevant state changes produce Events conceptually.

Responsibilities:

- signal task completion;
- signal workflow transition;
- signal knowledge-impacting outcomes;
- signal blockage or recovery.

Deterministic: yes.
IA allowed: no.

### 2.11 Knowledge Update

The Result updates organizational Knowledge.

Responsibilities:

- `Knowledge`: absorb the conceptual learning;
- `Runtime`: expose that the company has learned something;
- `Orchestrator`: observe the impact on future routing.

Deterministic: yes.
IA allowed: no.

### 2.12 Employee Skills Update

The Employee’s skills are conceptually refined by the newly gained knowledge.

Responsibilities:

- `Employee`: internal capability profile evolves;
- `Department`: validates future fit;
- `Knowledge`: acts as the input source.

Deterministic: primarily yes, with future room for assisted recommendations.

### 2.13 Runtime State Update

The Company Runtime updates the company-wide live state.

Responsibilities:

- reflect progress;
- reflect completion;
- reflect blockage or recovery;
- expose new state to observability.

Deterministic: yes.
IA allowed: no.

### 2.14 Observability Update

Observability receives the new state from the Runtime and Events.

Responsibilities:

- summarize state;
- reveal progress;
- highlight blockages;
- present organizational signals.

Deterministic: yes.
IA allowed: no.

### 2.15 2.5D Interface Update

The 2.5D interface receives the updated observability state.

Responsibilities:

- visualize the company state;
- show progress and blockages;
- display the conceptual flow result;
- remain purely representational.

Deterministic: yes in rendering state; future visualization enhancements may use
IA for explanation layers, but never for execution.

---

## 3. Responsibilities by Subsystem

### Organization

- provides the global structure;
- defines ownership and boundaries.

### Company Runtime

- tracks live company state;
- aggregates visibility.

### Orchestrator

- makes strategic evaluation;
- resolves high-level direction.

### Department

- routes work inside its boundary;
- selects suitable contributors.

### Employee

- participates in the workflow conceptually;
- receives contextual assignment.

### Skills

- influence suitability and growth.

### Policies

- constrain valid paths.

### Prompt

- shapes execution intent.

### Engine

- produces the conceptual output.

### Result

- records official outcome.

### Events

- signal state changes.

### Knowledge

- stores organizational learning.

### Observability

- interprets company state.

### 2.5D Interface

- displays the company state.

---

## 4. Pause, Interruption, and Resume Points

The flow may be conceptually interrupted at the following points:

- after Task creation;
- during orchestrator evaluation;
- during department routing;
- during employee selection;
- during prompt construction;
- during engine call;
- during result production;
- during knowledge update;
- during runtime update;
- during observability refresh.

Possible conceptual pause points:

- policy constraint triggered;
- employee unavailable;
- department overloaded;
- runtime maintenance;
- orchestrator defers decision.

Possible conceptual resume points:

- after policy clearance;
- after employee availability returns;
- after maintenance ends;
- after strategic approval;
- after blockage is resolved.

---

## 5. Deterministic vs IA-Enabled Areas

### Must remain deterministic

- task registration;
- runtime state tracking;
- routing boundaries;
- policy enforcement;
- event emission rules;
- observability summary generation;
- interface update signaling.

### May use IA in future

- employee ranking suggestions;
- prompt refinement;
- workflow optimization suggestions;
- knowledge pattern interpretation;
- skill growth suggestions;
- result summarization assistance.

The rule is:

> Anything involving safety, boundaries, ownership, and governance should remain
> deterministic.

---

## 6. ASCII Complete Flow

```text
Need
  ↓
Task Created
  ↓
Company Runtime Registers Task
  ↓
CEO / Orchestrator Evaluates
  ↓
Department Receives
  ↓
Employee Selected
  ↓
Context Prepared
  ↓
Prompt Built
  ↓
Engine Called
  ↓
Result Produced
  ↓
Events Published
  ↓
Knowledge Updated
  ↓
Employee Skills Updated
  ↓
Runtime State Updated
  ↓
Observability Refreshed
  ↓
2.5D Interface Updated
```

---

## 7. Future Notes

This document defines the first integrated flow of the company. It is intended
to support future implementation missions without forcing any implementation
prematurely.
