# Decision Architecture — AI Company

## Purpose

This document defines, at a conceptual level, how the AI Company makes
decisions.

It does **not** implement decision logic, classes, contracts, or runtime
behavior. It is a reference for future architectural work.

---

## 1. How a Task is Born

A Task begins as a need for work inside the AI Company.

Typical conceptual sources:

- a business request
- an organizational need
- a policy-triggered action
- a knowledge gap
- an opportunity identified by a Department

```text
Need / Signal / Opportunity
            ↓
         Task
```

The Task is the smallest unit of work that can be routed through the company.

---

## 2. How a Task Gets Priority

Priority is determined conceptually by:

- urgency
- strategic impact
- policy constraints
- organizational context
- available capacity
- business value

```text
Task → Priority Decision → Priority Level
```

Priority is not execution. It is only a decision about ordering and attention.

---

## 3. How a Department Receives a Task

A Department receives a Task when the Task belongs to its responsibility
domain.

Conceptual criteria:

- task type
- organizational ownership
- required capability
- current workload
- policy fit

```text
Task → Department Routing
```

Departments do not execute tasks themselves in this document. They own the
decision boundary that receives and routes work.

---

## 4. How an Employee is Chosen

An Employee is chosen conceptually based on:

- role fit
- skill fit
- availability
- policy compliance
- department membership
- task context

```text
Task + Department + Skills + Policies
                ↓
            Employee Choice
```

The choice is a decision, not an execution step.

---

## 5. How Skills Influence the Choice

Skills act as a capability filter and a confidence signal.

They can:

- increase eligibility
- improve ranking
- disqualify mismatches
- suggest alternative employees

```text
Employee Candidates
      ↓ filtered by
      Skills
      ↓
   Best Fit
```

Skills do not execute tasks. They only influence who should receive them.

---

## 6. How Policies Participate in the Decision

Policies constrain and shape the decision process.

They can:

- allow or block a route
- require specific qualifications
- enforce organizational boundaries
- determine escalation paths
- restrict certain task types

```text
Decision Path
   ↑
Policies constrain
```

Policies are decision guards, not execution engines.

---

## 7. How a Workflow is Started

A Workflow starts when the company decides that a Task should follow a
structured path.

The Workflow defines the conceptual sequence:

```text
Task → Workflow → Department → Employee → Result
```

The Workflow is the logical map of the decision path.

---

## 8. How Result is Produced

A Result is produced when the conceptual path reaches an outcome.

The Result represents:

- what happened
- what was decided
- what was produced
- whether it was successful

```text
Task / Workflow / Employee Decision
                ↓
             Result
```

Result is the official record of outcome, not persistence or analytics.

---

## 9. How Result Feeds Knowledge

Results become inputs for organizational knowledge.

Conceptually:

- successful results reinforce patterns
- failed results identify gaps
- partial results reveal uncertainty
- repeated results reveal trends

```text
Result → Knowledge
```

Knowledge is derived, not executed.

---

## 10. How Knowledge Improves Skills

Knowledge can refine skills by:

- identifying strong patterns
- exposing weak points
- suggesting refinements
- guiding future capability growth

```text
Knowledge → Skill Improvement
```

This is conceptual learning, not runtime adaptation.

---

## 11. How Skills Evolve Employees

Skills influence employees by shaping:

- their effective capability profile
- task suitability
- routing preference
- growth opportunities

```text
Skill Growth → Employee Capability Growth
```

Employees do not become Skills; Skills strengthen the employee’s conceptual
profile.

---

## 12. How the Company Learns Continuously

Continuous learning is a closed conceptual loop:

```text
Task → Workflow → Decision → Result → Knowledge → Skills → Employees → Task
```

This loop is the foundation for future organizational improvement.

---

## 13. Decisions That Always Belong to the CEO

The future `CEO` role is represented architecturally by the future
Orchestrator.

Decisions reserved to the CEO / Orchestrator layer:

- final prioritization policy
- cross-department arbitration
- strategic routing
- escalation resolution
- global decision boundaries
- company-wide policy interpretation

```text
Strategic / Global Decisions → CEO (Orchestrator)
```

---

## 14. Decisions That Belong to Departments

Departments own:

- local task acceptance
- internal routing
- functional interpretation of work
- domain-specific suitability checks
- department-level escalation

Departments are not allowed to override company-wide policy or strategic
orchestration.

---

## 15. Decisions That Belong to Employees

Employees own:

- local capability interpretation
- task-level response at the conceptual level
- skill-based suitability signaling
- context-aware participation

Employees do not own strategic decisions, policy interpretation at the company
level, or orchestration boundaries.

---

## 16. ASCII Flow of the Decision Model

```text
                     CEO / Orchestrator
                             │
                             ▼
                    Company-wide decision
                             │
        ┌────────────────────┼────────────────────┐
        ▼                    ▼                    ▼
   Department           Policy constraints      Knowledge
        │                    │                    │
        ▼                    ▼                    ▼
     Task routing        Allowed / blocked      Skill growth
        │
        ▼
     Employee choice
        │
        ▼
     Workflow start
        │
        ▼
        Result
```

```text
Need → Task → Priority → Department → Employee → Workflow → Result → Knowledge
                                   ↑                    │
                                   └──── Skills ────────┘
                                            ↑
                                         Policies
```

---

## 17. Decision Categories

### Organizational decisions

Decisions about:

- ownership
- routing
- priority boundaries
- policy enforcement
- escalation
- company structure

### Operational decisions

Decisions about:

- task acceptance
- employee selection
- workflow start
- result creation
- knowledge derivation

### Technical decisions

Decisions about:

- implementation strategy
- contract shape
- dependency boundaries
- module placement
- architectural consistency

---

## 18. Future IA vs Deterministic Decisions

### May use IA in the future

- priority refinement
- employee ranking suggestions
- skill matching suggestions
- knowledge pattern extraction
- workflow optimization suggestions

### Should remain deterministic

- policy enforcement
- company-wide escalation rules
- contract validation
- dependency boundary checks
- ownership assignment
- architectural classification

The rule is simple:

> If a decision affects governance, boundaries, or structural safety, it should
> remain deterministic.

---

## 19. Architectural Principles

- decisions must be explainable
- decisions must respect ownership boundaries
- decisions must not collapse into execution
- decisions must not introduce hidden coupling
- decisions must remain compatible with future products of the AI Company

---

## 20. Final Note

This document is the conceptual reference for decision-making inside the AI
Company. Future implementation missions may build on this model, but they must
not violate the boundaries defined here.
