# Engineering Blueprint — Policy Engine

## Purpose

This document is the engineering blueprint for the `Policy Engine` of the AI Company. It defines the architecture of the declarative policy evaluation layer responsible for answering whether an action is permitted, which rule was violated, and which policy approved or blocked a given operation.

This blueprint translates the conceptual ideas of the [Decision Architecture](file:///c:/Users/Shin/Documents/Novo_projeto_Ai_Content_Factory/DECISION_ARCHITECTURE.md) into concrete component responsibilities without introducing runtime code, modifying existing contracts, or mutating active state.

The Policy Engine does **not** make decisions. It answers policy questions. The distinction is fundamental: decisions belong to the Decision Engine and the Orchestrator; policy answers belong to the Policy Engine.

---

## 1. Scope and Boundaries

To avoid role confusion and architectural leakage, the Policy Engine must enforce a strict boundary between what it evaluates and what it never touches.

### In Scope (What Belongs to the Policy Engine)

- **Constraint Validation**: Determining whether a proposed action violates an active constraint (e.g., workload cap, segregation of duties, deadline enforcement).
- **Rule Evaluation**: Executing Boolean logic against a set of declarative rules and returning which rules passed and which failed.
- **Organizational Policy Enforcement**: Interpreting company-wide, division-level, and department-level policies as evaluable conditions.
- **Compliance Checking**: Verifying that an action adheres to mandatory regulatory or governance policies.
- **Authorization**: Answering whether a given actor (employee, department, system) is authorized to perform a specific action.
- **Safety Rule Verification**: Checking hard-block safety policies that must never be overridden (e.g., no self-assignment, no concurrent execution of conflicting tasks).
- **Runtime Policy Queries**: Evaluating runtime-scoped policies (e.g., max tasks per department, maintenance mode restrictions).
- **AI Policy Evaluation (Future)**: Evaluating guardrails and boundaries for AI-generated recommendations without letting AI override safety rules.

### Out of Scope (What Does NOT Belong to the Policy Engine)

- **Decision Making**: The Policy Engine does not choose candidates, rank employees, route tasks, or resolve priorities. It returns policy verdicts; the Decision Engine consumes them.
- **State Mutation**: The Policy Engine *never* updates the state of runtimes (e.g., it does not mark a task as `BLOCKED` or set an employee to `OFFLINE`).
- **Execution of Work**: The Policy Engine does not perform tasks, generate content, or run workflows.
- **Persistence & Storage**: It does not store policies, logs, or evaluation history. Persistence is delegated to the Knowledge/Result layers.
- **Policy Authoring**: The Policy Engine evaluates policies; it does not create, edit, or deploy them.
- **State Tracking**: It does not hold state. It operates as a stateless evaluation layer.

---

## 2. Separation of Concerns

Policy evaluation is split into three distinct layers to prevent strategic governance from collapsing into operational rule-checking:

```text
┌─────────────────────────────────────────────────────────────┐
│                 Strategic Policy Layer                      │
│  (Owned by Orchestrator / Company-wide Governance)           │
│  Defines: global policies, organizational boundaries,        │
│           safety invariants, compliance mandates             │
└───────────────────────────┬─────────────────────────────────┘
                            │ Constrains & Guides
                            ▼
┌─────────────────────────────────────────────────────────────┐
│                Operational Policy Layer                     │
│  (Evaluated by Policy Engine / Decision Engine)              │
│  Evaluates: active policies, constraints, rules,             │
│             authorization checks, runtime policies            │
└───────────────────────────┬─────────────────────────────────┘
                            │ Returns Verdict
                            ▼
┌─────────────────────────────────────────────────────────────┐
│                    Execution Layer                          │
│  (Performed by Employees / Workflows / Skill Runtimes)      │
│  Consumes: policy verdicts as pass/fail gates               │
└─────────────────────────────────────────────────────────────┘
```

### Strategic Policy (Global Governance)
- **Responsibility**: Owned by the `Orchestrator` and the Policy Repository interface.
- **Decisions**: Defining global policies, establishing company-wide safety rules, setting compliance requirements, and managing organizational boundaries.

### Operational Policy (Local Evaluation)
- **Responsibility**: Evaluated by the `Policy Engine` on behalf of the `Decision Engine` and `Orchestrator`.
- **Decisions**: Validating constraints, evaluating rules, checking authorization, and returning structured verdicts with explanation.

### Execution (Operational Output)
- **Responsibility**: Performed by `Employees` and `Workflows` within the boundaries set by the runtimes.
- **Decisions**: Applying policies as pass/fail gates before executing state transitions.

---

## 3. Relationships and Interactions

The Policy Engine acts as a stateless utility invoked by the Decision Engine during the constraint evaluation phase. It does not actively listen to the `EventBus` or trigger actions; instead, it is queried during decision pipelines:

```text
 Decision Request
        │
        ▼
 Decision Engine
        │
        ├─► 1. Queries Policy Engine (with Action, Actor, Policies)
        │
        ├─◄ 2. Receives PolicyResult (Approved / Violated / Error)
        │
        ▼
 Decision Result (incorporates policy verdict)
        │
        ▼
 Orchestrator / Runtime
        │
        ▼
 Executes State Change (if approved)
```

- **Decision Engine**: Primary consumer of the Policy Engine. During `evaluate_constraints`, the Decision Engine delegates policy-specific checks to the Policy Engine.
- **Orchestrator**: Queries the Policy Engine directly for strategic policy validation (e.g., "is this cross-department action allowed?").
- **Departments**: May query the Policy Engine for local policy evaluation before proposing candidates to the Decision Engine.
- **Employees**: Their actions and state transitions are validated against active policies.
- **Tasks**: Task metadata and type determine which policies are relevant.
- **Policies**: Configured rules stored externally (YAML, JSON, database) and loaded into `PolicyContext` at evaluation time.

---

## 4. Component Breakdown

The Policy Engine is organized as a set of logical, stateless sub-components:

```text
                      Policy Query
                          │
                          ▼
             ┌────────────┴────────────┐
             │     PolicyContext        │
             │   (Immutable Input)      │
             └────────────┬────────────┘
                          │
          ┌───────────────┼───────────────┐
          ▼               ▼               ▼
   ┌──────────────┐ ┌──────────────┐ ┌──────────────┐
   │RuleEvaluator │ │Constraint    │ │Authorization │
   │ (Boolean     │ │Validator     │ │Checker       │
   │  Logic)      │ │ (Hard Blocks)│ │ (Permissions)│
   └──────┬───────┘ └──────┬───────┘ └──────┬───────┘
          │                │                │
          └────────────────┼────────────────┘
                           │
                           ▼
             ┌─────────────┴─────────────┐
             │       PolicyTrace         │
             │   (Structured Log)        │
             └─────────────┬─────────────┘
                           │
                           ▼
             ┌─────────────┴─────────────┐
             │       PolicyResult        │
             │   (Final Verdict)         │
             └─────────────┬─────────────┘
                           │
                           ▼
                     Policy Answer
```

### 4.1 PolicyContext
- **Purpose**: Immutable input containing the action being evaluated, the actor attempting the action, the active policies, and relevant runtime snapshots.
- **Execution**: Purely in-memory, compiled from snapshots and policy definitions. Never mutated after construction.
- **Structure** (conceptual):
  - `action`: The proposed operation (e.g., `assign_task`, `transfer_employee`, `approve_result`).
  - `actor`: The entity attempting the action (employee, department, system).
  - `target`: The entity the action targets (task, result, workflow).
  - `active_policies`: List of policy definitions relevant to this query.
  - `snapshots`: Read-only runtime snapshots required for evaluation.

### 4.2 PolicyResult
- **Purpose**: Immutable output containing the evaluation verdict and structured explanation.
- **Execution**: Produced by the Policy Engine after all sub-components have run. Never mutated after creation.
- **Structure** (conceptual):
  - `policy_id`: Identifier of the policy that produced this result.
  - `approved`: Boolean verdict (pass/fail).
  - `violation_code`: Machine-readable code identifying the violation (e.g., `SEGREGATION_OF_DUTIES`, `WORKLOAD_EXCEEDED`).
  - `violation_detail`: Human-readable explanation of what was violated.
  - `trace`: The `PolicyTrace` object containing full evaluation history.

### 4.3 PolicyTrace
- **Purpose**: Structured execution trace listing every rule evaluated, every constraint checked, and the ordering of evaluation.
- **Execution**: Built incrementally as each sub-component runs. Immutable after the evaluation completes.
- **Structure** (conceptual):
  - `rules_evaluated`: List of rule identifiers and their Boolean results.
  - `constraints_checked`: List of constraint identifiers and pass/fail status.
  - `authorization_checks`: List of permission checks and outcomes.
  - `rejection_reasons`: Mapping of rule/constraint identifiers to human-readable failure explanations.
  - `execution_order`: Ordered list of evaluation stages.
  - `execution_time_ms`: Wall-clock time for the full evaluation.

### 4.4 ConstraintValidator
- **Purpose**: Evaluates hard-block constraints against the proposed action and actor. If any constraint fails, the action is rejected immediately.
- **Execution**: Runs first in the pipeline. Constraints are ordered by severity (safety first, compliance second, operational third). Each constraint is a pure function that receives `PolicyContext` and returns a pass/fail verdict with an explanation.
- **Examples of constraints**:
  - Segregation of Duties: "The same employee must not approve and execute the same task."
  - Workload Cap: "Department must not exceed N concurrent tasks."
  - Deadline Enforcement: "Task must not be assigned after its deadline."
  - Maintenance Mode: "No task assignment allowed during company maintenance."

### 4.5 RuleEvaluator
- **Purpose**: Executes declarative Boolean rules against the `PolicyContext`. Rules are expressed as simple predicates (e.g., `actor.role == target.required_role`).
- **Execution**: Runs after constraint validation. Rules are evaluated in priority order. Each rule returns a pass/fail verdict. The `RuleEvaluator` aggregates results and produces a summary of which rules passed and which failed.
- **Rule structure** (conceptual):
  - `rule_id`: Unique identifier.
  - `condition`: Boolean expression referencing fields in `PolicyContext`.
  - `priority`: Evaluation order.
  - `on_fail`: Action on failure (block / warn / log).
  - `explanation`: Human-readable description of what the rule checks.

### 4.6 AuthorizationChecker
- **Purpose**: Verifies that the actor has the required permissions to perform the action on the target.
- **Execution**: Runs after rule evaluation. Checks role-based or capability-based permissions against the actor's profile.
- **Examples**:
  - "Only employees with role `strategist` may approve results."
  - "Only employees with capability `coordinate` may route tasks."
  - "Departments of type `operations` may not assign tasks to departments of type `research`."

### 4.7 PolicyRepository (Interface — Conceptual Only)
- **Purpose**: Defines the interface for loading policy definitions from external sources. This component is not implemented in the first version; it exists as a seam for future integration.
- **Methods** (conceptual):
  - `load_policy(policy_id) -> PolicyDefinition`
  - `load_policies_by_scope(scope) -> list[PolicyDefinition]`
  - `load_active_policies() -> list[PolicyDefinition]`
- **Implementation Notes**: The interface is designed so that any backend (YAML files, JSON files, database, web API) can be plugged in without modifying the Policy Engine core.

### 4.8 PolicyEngine
- **Purpose**: Orchestrates the full policy evaluation pipeline. It is the single entry point for all policy queries.
- **Execution**:
  1. Receives a `PolicyContext`.
  2. Delegates to `ConstraintValidator` — if any hard constraint fails, returns immediately with `approved=False`.
  3. Delegates to `RuleEvaluator` — evaluates all relevant rules.
  4. Delegates to `AuthorizationChecker` — verifies actor permissions.
  5. Assembles `PolicyTrace` from all sub-component results.
  6. Returns `PolicyResult`.

---

## 5. Architectural Flow

The Policy Engine never initiates action. It is always invoked:

```text
                  ┌──────────────────────┐
                  │  External Trigger     │
                  │  (Task, Event, Timer) │
                  └──────────┬───────────┘
                             ▼
                  ┌──────────────────────┐
                  │    Decision Engine    │
                  │  choose_best_         │
                  │  candidate()          │
                  └──────────┬───────────┘
                             │ evaluate_constraints()
                             ▼
                  ┌──────────────────────┐
                  │    Policy Engine      │◄──── Policy Definitions
                  │  evaluate()          │       (YAML / JSON / DB)
                  └──────────┬───────────┘
                             │
                  ┌──────────┴───────────┐
                  ▼                      ▼
         ┌────────────────┐   ┌────────────────────┐
         │ approved=True  │   │ approved=False      │
         │ (passes to     │   │ (returns violation  │
         │  match_skills) │   │  code + explanation)│
         └────────────────┘   └────────────────────┘
```

### Why the Policy Engine Never Executes Actions

The Policy Engine is intentionally stateless and return-only. This design ensures:

1. **Auditability**: Every policy check produces a `PolicyTrace` that can be inspected without side effects.
2. **Testability**: The engine can be tested with any combination of context and policies without booting runtimes.
3. **Decoupling**: Policy logic is isolated from execution logic. Policies can change without affecting runtime code.
4. **Safety**: Hard-block constraints are evaluated before any action is taken, preventing unauthorized state changes.
5. **Composability**: The Decision Engine can query multiple policies in sequence without worrying about state contamination.

---

## 6. Explainability

Every policy evaluation must produce a structured explanation suitable for both machine consumption and human debugging.

### Machine-Readable Output

```text
PolicyResult:
  approved: false
  violation_code: WORKLOAD_EXCEEDED
  violation_detail: "Department 'Engineering' has 12 active tasks; maximum is 10."
  trace:
    constraints_checked:
      - constraint: max_workload
        passed: false
        detail: "12 active tasks exceeds limit of 10"
    rules_evaluated:
      - rule: department_must_have_capacity
        passed: false
    authorization_checks:
      - check: orchestrator_can_assign
        passed: true
    execution_order: [constraints, rules, authorization]
    execution_time_ms: 0.45
```

### Human-Readable Output

Every `PolicyResult` must include a `violation_detail` field written in natural language that explains:
- What action was attempted.
- Which policy was violated.
- What the policy expected.
- What the actual state was.

### Explanation Requirements

- **Every rejection** must include the specific rule or constraint identifier that caused the rejection.
- **Every approval** must list which policies were checked and confirmed as passing.
- **Multiple violations** must list all failures, not just the first one.
- **Trace ordering** must reflect the actual evaluation sequence.

---

## 7. Future: Policy Sources

The Policy Engine core must remain agnostic to how policies are defined and loaded. The `PolicyRepository` interface provides the seam for multiple backends:

### YAML Policies
```yaml
policies:
  - id: max_workload
    scope: department
    type: constraint
    condition: "department.active_tasks < 10"
    on_fail: block
    explanation: "Department must not exceed 10 concurrent tasks"
```

### JSON Policies
```json
{
  "policies": [
    {
      "id": "segregation_of_duties",
      "scope": "global",
      "type": "constraint",
      "condition": "actor.employee_id != target.creator_id",
      "on_fail": "block",
      "explanation": "Creator must not also be the approver"
    }
  ]
}
```

### Database Policies
Policies stored in a relational or document database, loaded by the `PolicyRepository` implementation at query time. Supports dynamic updates without code changes.

### Web Interface Policies
A future administrative UI may allow non-technical users to:
- View active policies.
- Enable or disable policies.
- Adjust policy parameters (e.g., workload limits).
- Preview the impact of a policy change.

### AI-Generated Policy Recommendations (Future)
The `Recommendation Layer` (described in the Decision Engine blueprint) may suggest policy adjustments:
- "Department X has been exceeding its workload limit consistently — consider increasing the limit or adding capacity."
- "Role Y has never triggered a policy violation — consider removing the restriction."

These recommendations **must never** auto-enable policies. They require human or Orchestrator approval before taking effect.

```text
AI Recommendation
       │
       ▼
 Orchestrator Review
       │
       ▼
 Policy Repository Update
       │
       ▼
 Policy Engine (unchanged core)
```

The Policy Engine core does not change regardless of the source. The `PolicyRepository` abstraction absorbs all backend variation.

---

## 8. Architectural Risks

### 8.1 Policy Proliferation
- **Risk**: As the company grows, the number of policies may grow unbounded, leading to evaluation slowdowns.
- **Mitigation**: Policies must be scoped (global / division / department / runtime). The `PolicyContext` should only load policies relevant to the current action. Evaluation must be ordered by priority with early exit on hard-block failures.

### 8.2 Conflicting Policies
- **Risk**: Two active policies may produce contradictory requirements (e.g., "max 5 tasks per employee" vs. "all high-priority tasks must be assigned immediately").
- **Mitigation**: The first version avoids conflict resolution — hard-block constraints always win. A future version may introduce policy priority and override semantics.

### 8.3 Runtime Coupling via Snapshots
- **Risk**: The `PolicyContext` may accidentally leak runtime objects instead of immutable snapshots, breaking determinism.
- **Mitigation**: Same rule as the Decision Engine — only snapshots, never runtime references. Use frozen dataclasses.

### 8.4 Performance at Scale
- **Risk**: Evaluating dozens of policies per decision may become a bottleneck.
- **Mitigation**: Policies are pure functions with no I/O. Evaluation is CPU-bound and fast (microseconds per policy). If needed, policies can be indexed by action type for O(1) lookup.

### 8.5 Policy Bypass
- **Risk**: A runtime path may skip the Policy Engine and perform actions without validation.
- **Mitigation**: All state transitions must go through the Decision Engine pipeline, which always calls the Policy Engine during `evaluate_constraints`. No runtime should expose public mutation methods that bypass this pipeline.

---

## 9. Benefits of Separation

### 9.1 Decoupling of Policy Logic from Decision Logic

The Decision Engine answers "who should do this task?" The Policy Engine answers "is this action allowed?" These are fundamentally different questions. Mixing them would create a single, untestable block of conditional logic.

### 9.2 Auditable Policy Layer

Every policy evaluation produces a `PolicyTrace` that can be:
- Logged for compliance.
- Displayed in the 2.5D office interface.
- Replayed for debugging.
- Used as training data for future AI policy recommendations.

### 9.3 Pluggable Policy Sources

Because the Policy Engine depends only on the `PolicyRepository` interface, policies can be loaded from any source without modifying the evaluation logic.

### 9.4 Independent Testability

The `ConstraintValidator`, `RuleEvaluator`, and `AuthorizationChecker` can be unit-tested in isolation with mock `PolicyContext` objects. No runtimes, no events, no database.

### 9.5 Safety Isolation

Hard-block safety constraints live in their own component (`ConstraintValidator`) and are evaluated first. This ensures safety rules cannot be accidentally bypassed by changes to scoring or ranking logic.

### 9.6 Evolutionary Path to AI

When the `Recommendation Layer` is added, it will suggest candidate actions, but the Policy Engine will still validate them before approval. This satisfies the **Safety First** principle: non-deterministic recommendations never override deterministic constraints.

---

## 10. Relationship with Existing Architecture Documents

### ARCHITECTURE.md

This blueprint adds the `Policy Engine` as a new architectural component under the "Blueprints de Engenharia" section, specifically within the "Core Runtime and Coordination" category. It lives alongside the `Decision Engine` and `Orchestrator` blueprints. The `ARCHITECTURE.md` index should be updated to include this document when the Policy Engine reaches implementation phase.

### ENGINEERING_BLUEPRINT_DECISION_ENGINE.md

The Decision Engine blueprint defines `ConstraintValidator` as one of its sub-components (section 4.6). In this blueprint, `ConstraintValidator` is promoted to a first-class citizen within the Policy Engine. The Decision Engine's `evaluate_constraints` step becomes a delegation point: instead of evaluating constraints inline, it queries the Policy Engine.

This means:
- The Decision Engine retains `evaluate_constraints` as a pipeline step.
- The implementation of `evaluate_constraints` delegates to the Policy Engine.
- The Decision Engine never needs to know how policies are defined or loaded.

### MESSAGE_SYSTEM_ARCHITECTURE.md

The Message System may carry policy-related signals:
- Policy violation notifications.
- Policy change announcements.
- Compliance alerts.
- Authorization failure messages.

Messages never carry evaluation logic. They represent the outcome of a policy evaluation for visibility and coordination purposes.

### OBSERVABILITY_ARCHITECTURE.md

Observability provides visibility into:
- Which policies are currently active.
- How many times each policy has been triggered.
- Which actions are most frequently blocked.
- Policy evaluation latency.
- Compliance status per department.

The Policy Engine does not push data to observability. Instead, the `PolicyTrace` produced by each evaluation can be consumed by a projector that updates observability snapshots.

### COMPANY_RUNTIME_ARCHITECTURE.md

The Company Runtime maintains operational state that the Policy Engine queries via snapshots:
- Company lifecycle state (is the company in maintenance mode?).
- Department load (how many active tasks?).
- Employee availability (who is idle vs. busy?).
- Workflow progress (is a critical path blocked?).

The Policy Engine evaluates policies against this state but never modifies it.

### Decision Architecture (DECISION_ARCHITECTURE.md)

The Decision Architecture document describes the conceptual model of decision-making. The Policy Engine fits within the **Constraint & Policy Evaluation** layer of that model. It is the mechanism that answers the question "is this action valid according to company rules?" before a decision is finalized.

---

## 11. Validation

### Architectural Decisions

| Decision | Rationale |
|----------|-----------|
| Policy Engine is a separate component from Decision Engine | Answers different questions (policy vs. selection); separate lifecycles and testability |
| ConstraintValidator runs before RuleEvaluator | Safety first: hard blocks must never be bypassed by rule evaluation |
| PolicyRepository is interface-only in v1 | Defines the seam without committing to a backend; prevents premature I/O coupling |
| All policy data is stateless and read-only | Enables idempotent evaluation and parallel testing |
| PolicyTrace is always produced | Guarantees explainability for every policy evaluation, whether pass or fail |

### Technical Justification

The separation of policy evaluation from decision logic follows the **Single Responsibility Principle**. The Decision Engine already handles candidate selection, skill matching, and priority resolution. Adding policy evaluation directly would create a class with multiple reasons to change: changes to selection logic and changes to policy rules would both require modifying the same class.

By isolating policy evaluation in its own engine, each component has exactly one reason to change:
- **Decision Engine** changes when selection, matching, or priority logic changes.
- **Policy Engine** changes when policy rules, constraints, or authorization logic changes.

### Risks

1. **Over-engineering**: The Policy Engine may never need all the described components. The blueprint should be treated as a guide, not a mandatory structure. Start with `ConstraintValidator` and `RuleEvaluator`; add `AuthorizationChecker` and `PolicyRepository` when needed.
2. **Performance overhead**: An additional delegation step (Decision Engine → Policy Engine) adds function call overhead. This is acceptable (microseconds per call) but should be measured.
3. **Policy drift**: If policies are defined in multiple sources (YAML, JSON, DB), inconsistencies may arise. A future policy validation tool should verify that all sources produce equivalent evaluations for the same inputs.

### Future Opportunities

1. **Policy simulation**: Test a proposed policy against historical `PolicyContext` snapshots before deploying it.
2. **Policy impact analysis**: "If we enable this policy, which current workflows would be blocked?"
3. **AI-assisted policy authoring**: An LLM could draft policy rules in natural language, which are then compiled to the Policy Engine's rule format.
4. **Policy versioning**: Each policy evaluation records which version of the policy was used, enabling rollback analysis.

### Impact on Existing Architecture

| Area | Impact |
|------|--------|
| `core/decision/runtime.py` | `evaluate_constraints` remains a pipeline step; internally delegates to Policy Engine |
| `core/policies/` | Existing placeholder models (`Policy`, `PolicyCondition`, `PolicyConstraint`) may be replaced or extended by Policy Engine components |
| `core/orchestrator/runtime.py` | May use Policy Engine for strategic policy validation |
| `EventBus` | Unchanged. Policy traces may be emitted as events by the caller, not by the Policy Engine |
| `ObservabilityProjector` | May add a `PolicyProjector` to consume policy traces and update observability snapshots |
| `core/decision/runtime.py` pipeline | The `evaluate_constraints` step remains as-is, but delegates policy work to the Policy Engine |

---

## 12. Architectural Principles

- **Immutability of Inputs**: The Policy Engine must treat all incoming contexts and policies as read-only.
- **Idempotency**: Given the exact same policy context, the evaluation result must be identical.
- **Explainability**: Every policy result must include a trace listing which constraints passed, which failed, and the explanation for each.
- **Safety First**: Hard-block constraints (ConstraintValidator) must always be evaluated before soft rules (RuleEvaluator). Non-deterministic recommendations must never override deterministic constraint checks.
- **Backend Agnosticism**: The Policy Engine core must not depend on any specific policy storage format or location.

---

## 13. Final Blueprint Statement

This blueprint defines the future implementation shape of the Policy Engine layer while preserving the contract-first architecture of the AI Company. The Policy Engine is not a replacement for the Decision Engine — it is a complementary layer that answers policy questions so that the Decision Engine can make informed, safe, and auditable decisions.
