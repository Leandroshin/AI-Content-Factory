# Engineering Blueprint — Decision Engine

## Purpose

This document is the engineering blueprint for the `Decision Engine` of the AI Company. It defines the architecture of the deterministic decision-making layer responsible for processing policies, routing tasks, and verifying constraints.

This blueprint translates the conceptual ideas of the [Decision Architecture](file:///c:/Users/Shin/Documents/Novo_projeto_Ai_Content_Factory/DECISION_ARCHITECTURE.md) into concrete component responsibilities without introducing runtime code, modifying existing contracts, or mutating active state.

---

## 1. Scope and Boundaries

To avoid premature abstraction and bloated dependencies, the Decision Engine must enforce a strict boundary between what is inside and what is outside its scope.

### In Scope (What Belong to the Decision Engine)
- **Deterministic Evaluation**: Checking if a specific routing or assignment conforms to organizational rules.
- **Priority Resolution**: Calculating queue ordering or critical paths based on immutable task attributes and policy formulas.
- **Constraint Validation**: Ensuring compliance with global policies (e.g., security boundaries, maximum workload, division of labor).
- **Candidate Ranking**: Sorting eligible employees for a task based on objective skill profiles, category match, and availability metrics.
- **Context Construction**: Building a read-only context representing the current company state required for a specific decision.

### Out of Scope (What does NOT Belong to the Decision Engine)
- **State Mutation**: The Decision Engine *never* updates the state of runtimes (e.g., it does not change an employee's state to `BUSY` or mark a task as `ASSIGNED`). It returns decisions; the runtimes execute state transitions.
- **Execution of Work**: The Decision Engine does not perform tasks, generate content, or run workflows.
- **Persistence & Storage**: It does not store rules, logs, or decision history. Any persistence is delegated to the Knowledge/Result layers.
- **State Tracking**: It does not hold state. It operates as a stateless evaluation layer.

---

## 2. Separation of Concerns

Decision-making is split into three distinct layers to prevent strategic governance from collapsing into operational execution:

```text
┌─────────────────────────────────────────────────────────┐
│              Strategic Decision Layer                   │
│  (Governed by Orchestrator / Company-wide Policies)      │
└───────────────────────────┬─────────────────────────────┘
                            │ Constrains & Guides
                            ▼
┌─────────────────────────────────────────────────────────┐
│              Operational Decision Layer                 │
│  (Evaluated by Decision Engine / Departments / Runtimes) │
└───────────────────────────┬─────────────────────────────┘
                            │ Asserts Suitability
                            ▼
┌─────────────────────────────────────────────────────────┐
│                    Execution Layer                      │
│  (Performed by Employees / Workflows / Skill Runtimes)  │
└─────────────────────────────────────────────────────────┘
```

### Strategic Decisions (Global Governance)
- **Responsibility**: Owned by the `Orchestrator` (the CEO role).
- **Decisions**: Defining global policies, establishing department boundaries, managing company lifecycle states, and resolving high-impact escalations.

### Operational Decisions (Local Routing & Filtering)
- **Responsibility**: Evaluated by the `Decision Engine` on behalf of `Departments` and `Orchestrator`.
- **Decisions**: Selecting the best employee for a task, routing tasks to departments, adjusting queue priority, and validating local constraint compliance.

### Execution (Operational Output)
- **Responsibility**: Performed by `Employees` and `Workflows` within the boundaries set by the runtimes.
- **Decisions**: Applying specific skills to solve a task, generating results, and producing knowledge assets.

---

## 3. Relationships and Interactions

The Decision Engine acts as a stateless utility invoked by the orchestrator and runtime managers. It does not actively listen to the `EventBus` or trigger actions; instead, it is queried during state transitions:

```text
 Runtime Transition (e.g., Task Assignment)
          │
          ▼
   Orchestrator / Runtime
          │
          ├─► 1. Queries Decision Engine (with Task, Employees, Policies)
          │
          ├─◄ 2. Receives Deterministic Decision (Approved / Rejected / Ranked)
          │
          ▼
 Executes State Change (if Approved)
```

- **Orchestrator**: Queries the Decision Engine to resolve priority conflicts and route contested tasks across departments.
- **Departments**: Query the Decision Engine to select eligible department employees for incoming tasks.
- **Employees**: Their capabilities and availability are passed to the Decision Engine as candidate profiles.
- **Skills**: Act as capability tags matched by the Decision Engine to rank candidates.
- **Tasks**: Represent the payload of work containing the requirement profile evaluated by the Decision Engine.
- **Policies**: Configured rules passed as input to the Decision Engine to validate paths.
- **Workflows**: Their current execution map and progress dictate the sequence of decisions requested from the engine.

---

## 4. Component Breakdown

The Decision Engine is organized as a set of logical, stateless sub-components:

```text
                        Decision Request
                               │
                               ▼
                  ┌────────────┴────────────┐
                  │ Decision Context Builder│
                  └────────────┬────────────┘
                               │
            ┌──────────────────┼──────────────────┐
            ▼                  ▼                  ▼
     ┌──────────────┐   ┌──────────────┐   ┌──────────────┐
     │Rule Evaluator│   │Skill Matcher │   │Constraint val│
     └──────┬───────┘   └──────┬───────┘   └──────┬───────┘
            │                  │                  │
            └──────────────────┼──────────────────┘
                               │
                               ▼
                  ┌────────────┴────────────┐
                  │    Priority Resolver    │
                  └────────────┬────────────┘
                               │
                               ▼
                  ┌────────────┴────────────┐
                  │    Candidate Selector   │
                  └────────────┬────────────┘
                               │
                               ▼
                  ┌────────────┴────────────┐
                  │  Recommendation Layer   │
                  │       (Future AI)       │
                  └────────────┬────────────┘
                               │
                               ▼
                        Decision Output
```

### 4.1 Decision Context Builder
- **Purpose**: Collects and structures the transient parameters required for a decision (e.g., current task metadata, candidate employee list, active policy rules).
- **Execution**: Purely in-memory, compiling runtime snapshots into a read-only context model.

### 4.2 Rule Evaluator
- **Purpose**: Executes simple Boolean logic and domain rules against the decision context.
- **Execution**: Evaluates if the condition matches the requirement (e.g., `Employee.role == Task.required_role`).

### 4.3 Priority Resolver
- **Purpose**: Resolves task importance and urgency sorting.
- **Execution**: Computes a deterministic priority score using active policy coefficients.

### 4.4 Candidate Selector
- **Purpose**: Filters the list of available employees down to those who are eligible and members of the target department.
- **Execution**: Filters out employees whose states are not `IDLE` or who are restricted by active policies.

### 4.5 Skill Matcher
- **Purpose**: Scores and ranks eligible candidates based on their registered skills against task requirements.
- **Execution**: Calculates match percentages by analyzing the intersection of task requirements and employee skill tags.

### 4.6 Constraint Validator
- **Purpose**: Ensures that the proposed decision does not violate organizational boundaries or safety policies (e.g. Segregation of Duties).
- **Execution**: Hard block checks. If any validator fails, the decision is rejected immediately.

### 4.7 Recommendation Layer (Future AI)
- **Purpose**: Plugs in future non-deterministic recommendation heuristics (e.g., LLM-based ranking, predictive workflow paths).
- **Execution**: Acts as an optional advice decorator. It *suggests* candidates or priorities, but its output is always passed through the deterministic **Constraint Validator** before being approved.

---

## 5. Architectural Principles

- **Immutability of Inputs**: The Decision Engine must treat all incoming contexts and policies as read-only.
- **Idempotency**: Given the exact same decision context, the output must be identical.
- **Explainability**: Every decision result must include a trace listing which rules passed, which failed, and the scores assigned by the Skill Matcher and Priority Resolver.
- **Safety First**: Non-deterministic (AI-driven) recommendations must never override deterministic constraints.
