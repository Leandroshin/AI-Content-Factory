# Architecture Relationships — AI Company

## Purpose

This document defines the **architectural relationship model** for Phase 2 of
the AI Company foundation.

It does **not** define behavior, execution, orchestration, or operational
communication. It only defines **which subsystems may conceptually know each
other**, which dependencies are forbidden, and the official company flow.

---

## 1. Relationship Principles

- Relationships are **contractual**, not operational.
- A subsystem may know another subsystem only if the relationship is explicitly
  listed here.
- Knowledge of another subsystem must remain **one-way whenever possible**.
- Operational coupling is forbidden unless a future implementation mission
  explicitly authorizes it.
- The architecture must preserve low coupling and high cohesion.

---

## 2. Allowed Knowledge Graph

### Core organizational chain

```text
Organization
  ├── Departments
  ├── Employees
  ├── Skills
  ├── Policies
  ├── Workflows
  ├── Tasks
  ├── Results
  ├── Knowledge
  └── Events
```

### Official company flow

```text
Employee
  ↓ receives
Task
  ↓ follows
Workflow
  ↓ uses
Skills
  ↓ produces
Result
  ↓ informs
Knowledge
  ↓ triggers
Events
  ↓ constrained by
Policies
  ↓ assigned within
Department
  ↓ grouped by
Organization
```

This flow is conceptual and may be refined later, but it establishes the
official relationship direction for Phase 2.

---

## 3. Relationship Matrix

### Allowed relationships

- `Organization` may know:
  - `Departments`
  - `Employees`
  - `Skills`
  - `Policies`
  - `Workflows`
  - `Tasks`
  - `Results`
  - `Knowledge`
  - `Events`

- `Department` may know:
  - `Organization`
  - `Employees`
  - `Policies`

- `Employee` may know:
  - `Department`
  - `Skills`
  - `Tasks`
  - `Workflows`
  - `Results`
  - `Policies`

- `Skill` may know:
  - `Employees`
  - `Policies`

- `Policy` may know:
  - `Organization`
  - `Department`
  - `Employee`
  - `Workflow`
  - `Task`
  - `Result`

- `Task` may know:
  - `Workflow`
  - `Result`
  - `Policies`

- `Workflow` may know:
  - `Task`
  - `Department`
  - `Skill`
  - `Result`
  - `Policies`

- `Result` may know:
  - `Task`
  - `Workflow`
  - `Knowledge`
  - `Events`

- `Knowledge` may know:
  - `Result`
  - `Events`

- `Event` may know:
  - `Result`
  - `Knowledge`
  - `Policy`

### Relationship responsibilities

- `Organization` defines global structure and ownership.
- `Department` defines organizational grouping and reporting boundaries.
- `Employee` represents a human or structural contributor within the company.
- `Skill` represents a reusable capability that may be associated with an
  employee.
- `Policy` constrains how organizational behavior should be interpreted.
- `Task` represents a unit of work.
- `Workflow` represents the logical path a task can follow.
- `Result` represents the official output of an activity.
- `Knowledge` represents reusable organizational learning derived from results.
- `Event` represents a domain signal emitted from state transitions or outcomes.

---

## 4. Forbidden Dependencies

The following dependencies are forbidden in Phase 2:

- `Task` must not directly depend on `Employee` implementation details.
- `Engine` must not directly depend on `Engine`.
- `Skill` must not depend on `Task`.
- `Policy` must not depend on `Provider`.
- `Department` must not directly execute work.
- `Knowledge` must not become a persistence layer.
- `Event` must not become an event bus implementation.
- `Workflow` must not become a scheduler.
- `Result` must not become an analytics engine.
- `Organization` must not become an orchestration runtime.

---

## 5. ASCII Relationship Model

```text
                     Organization
                  /   |   |   |   \
                 /    |   |   |    \
                ▼     ▼   ▼   ▼     ▼
           Department Employee Skill Policy Workflow
                 \       |      |      |      /
                  \      ▼      ▼      ▼     /
                   \   Task → Result → Knowledge
                    \______________________/
                               |
                               ▼
                             Events
```

```text
Employee → Task → Workflow → Skills → Result → Knowledge → Events
                      ▲                    │
                      └──── Policies ──────┘
```

---

## 6. Rules to Prevent Incorrect Coupling

1. If a relationship is not listed here, it must be treated as forbidden.
2. A subsystem may read another subsystem’s contracts, but not its internal
   implementation.
3. Concepts must not be duplicated across multiple subsystems without a clear
   boundary.
4. Operational code must not be introduced under the guise of “relationship
   modeling”.
5. Relationships must remain directional and minimal.
6. Future implementation missions must preserve these boundaries unless this
   document is explicitly updated.

---

## 7. Phase 2 Implementation Order

The first relationships to be implemented in later missions should be:

1. `Organization` ↔ `Department`
2. `Organization` ↔ `Employee`
3. `Employee` ↔ `Skill`
4. `Employee` ↔ `Task`
5. `Task` ↔ `Workflow`
6. `Workflow` ↔ `Result`
7. `Result` ↔ `Knowledge`
8. `Result` ↔ `Events`
9. `Policy` ↔ the rest of the company relationships

This order preserves organizational structure before moving into execution and
learning relationships.

---

## 8. Future Considerations

- Relationship modeling may later be split into implementation-specific layers
  if the codebase grows substantially.
- A shared relationship contract layer may become useful only if repeated
  patterns appear in concrete implementations.
- The current model intentionally favors clarity over premature abstraction.
