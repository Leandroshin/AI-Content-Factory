# Employee Lifecycle Architecture — AI Company

## Purpose

This document defines the conceptual lifecycle of an Employee inside the AI Company.

It is strictly architectural. It does **not** implement behavior, classes, contracts,
models, runtime logic, or subsystem changes.

The goal is to describe how an Employee is created, configured, trained, used, paused,
and eventually deactivated, while preserving organizational memory and avoiding identity
inheritance leakage.

---

## 1. How an Employee is Born

An Employee is born as a conceptual organizational entity.

The birth of an Employee typically begins when the company identifies a need for a
new contributor profile.

```text
Need for contributor
        ↓
   Employee concept
```

At this stage, the Employee is not yet operational. It exists as an organizational
intent.

---

## 2. How Identity is Assigned

Identity gives the Employee a stable conceptual reference.

Identity may include:

- unique identifier;
- display identity;
- structural name;
- organizational traceability.

```text
Employee concept → Identity assignment → Employee identity
```

Identity is not behavior. It is recognition and traceability.

---

## 3. How Department is Assigned

The Department defines the Employee’s organizational home.

The assignment is based on:

- role fit;
- domain fit;
- organizational need;
- future responsibility boundary.

```text
Employee → Department assignment
```

The Department gives context, ownership, and operational boundary.

---

## 4. How Skills are Assigned

Skills are attached as capability structures.

They may represent:

- current capabilities;
- expected capabilities;
- developmental capabilities;
- cross-functional capabilities.

```text
Employee → Skills
```

Skills do not define identity. They describe capacity.

---

## 5. How Prompt is Assigned

Prompt, in this conceptual lifecycle, means the guidance structure used to shape the
Employee’s future participation.

It may include:

- operational framing;
- contextual instruction;
- domain guidance;
- behavior constraints.

```text
Employee → Prompt context
```

Prompt is not execution. It is a conceptual preparation layer.

---

## 6. How Tools are Assigned

Tools are the conceptual set of capabilities the Employee may use in future phases.

They may include:

- reading tools;
- writing tools;
- analysis tools;
- coordination tools;
- domain utilities.

```text
Employee → Tool access context
```

Tools must remain controlled by architecture, not by ad hoc assignment.

---

## 7. How Policies are Assigned

Policies define what the Employee may or may not do.

They constrain:

- scope;
- authority;
- behavior boundaries;
- collaboration boundaries;
- approval paths.

```text
Employee → Policies
```

Policies are not instructions. They are boundaries.

---

## 8. How Training Begins

An Employee enters training when the company decides the identity is ready to be
prepared for participation.

Training may conceptually include:

- onboarding;
- contextual alignment;
- skill calibration;
- policy familiarization;
- department acclimation.

```text
Identity + Department + Skills + Policies → Training
```

Training does not mean execution. It means preparation.

---

## 9. How the Employee Becomes Idle

After initial preparation, the Employee may enter `Idle`.

`Idle` means:

- the Employee is active in the company structure;
- the Employee is available for tasks;
- the Employee is not currently processing a task.

```text
Training → Idle
```

Idle is a ready state, not inactivity in the organizational sense.

---

## 10. How Tasks are Received

Tasks are conceptually assigned to an Idle or available Employee through the
organizational flow.

```text
Task → Department → Employee
```

Task reception depends on:

- department ownership;
- skill fit;
- policy compatibility;
- availability;
- runtime state.

---

## 11. How the Employee Learns During Work

An Employee learns while participating in work conceptually.

Learning may happen through:

- repeated exposure;
- result feedback;
- policy interaction;
- workflow completion;
- knowledge reuse.

```text
Task Participation → Experience → Learning
```

This is conceptual learning, not runtime AI training.

---

## 12. How Knowledge is Updated

Employee knowledge is updated from work outcomes and organizational feedback.

```text
Result → Knowledge Update → Employee Growth
```

Knowledge may affect:

- decision quality;
- skill relevance;
- future routing;
- collaboration fit.

---

## 13. How Skills Evolve

Skills evolve as a consequence of learning and organizational feedback.

```text
Knowledge → Skill Evolution
```

Skill evolution is conceptual and must remain compatible with the company’s
organizational model.

---

## 14. How Role Changes in the Future

An Employee may later change role conceptually.

This may happen when:

- responsibilities shift;
- department boundaries change;
- skills mature;
- company structure evolves.

```text
Employee → Role Evolution
```

Role change is structural, not identity replacement.

---

## 15. How an Employee Enters Pause

An Employee may enter `Paused` when temporarily unavailable.

Reasons may include:

- maintenance;
- policy restriction;
- organizational decision;
- training reset;
- workload balancing.

```text
Idle / Active → Paused
```

Paused means the Employee remains part of the organization, but is not currently
available for conceptual assignment.

---

## 16. How an Employee is Deactivated

An Employee is deactivated when the company conceptually ends the active use of
that identity.

```text
Paused / Idle → Deactivated
```

Deactivation does not erase organizational memory. It ends active participation.

---

## 17. How a New Employee Inherits Organizational Knowledge

A new Employee may inherit organizational knowledge without inheriting identity.

This means:

- it can receive learned patterns;
- it can receive calibrated skills;
- it can receive contextual guidance;
- it can receive policy awareness.

It must **not** inherit:

- identity history;
- personal traceability;
- prior lifecycle state;
- individual ownership artifacts.

```text
Old Employee Knowledge → Organizational Knowledge → New Employee
```

The company learns across employees, but identity remains unique.

---

## 18. Employee State Model

Conceptual states may include:

- `Draft`
- `Training`
- `Idle`
- `Active`
- `Paused`
- `Suspended`
- `Deactivated`
- `Archived`

```text
Draft → Training → Idle → Active → Paused → Idle
                        ↘ Suspended ↘
                                ↓
                          Deactivated → Archived
```

These states are conceptual and may be refined in future implementation phases.

---

## 19. Runtime Responsibilities

The Runtime conceptually:

- tracks employee availability;
- tracks employee state;
- tracks active participation;
- exposes progress signals;
- detects blockages;
- informs observability;
- reports state changes to the CEO / Orchestrator.

```text
Runtime → Employee State Visibility
```

The Runtime does not own identity or behavior.

---

## 20. Department Responsibilities

The Department conceptually:

- owns the employee’s organizational home;
- determines local fit;
- contextualizes task participation;
- helps define growth boundaries;
- participates in training and routing decisions.

The Department does not own the Employee’s identity.

---

## 21. CEO / Orchestrator Responsibilities

The CEO / Orchestrator conceptually:

- approves global lifecycle policies;
- defines company-wide role direction;
- manages strategic reallocation;
- interprets cross-department movement;
- governs high-level deactivation boundaries.

The CEO does not manage daily details of employee execution.

---

## 22. ASCII Lifecycle Diagram

```text
Employee Birth
     ↓
Identity Assignment
     ↓
Department Assignment
     ↓
Skills / Prompt / Tools / Policies
     ↓
Training
     ↓
Idle
     ↓
Task Assignment
     ↓
Active Participation
     ↓
Learning + Knowledge Update
     ↓
Skill Evolution
     ↓
Pause / Role Change / Deactivation
```

```text
Draft → Training → Idle → Active → Idle → Paused → Deactivated → Archived
```

---

## 23. Architectural Boundaries

This lifecycle must never become:

- a runtime implementation;
- a task executor;
- an engine manager;
- a provider manager;
- a scheduler;
- a bus;
- a persistence model;
- a hidden state machine implementation.

It is a conceptual lifecycle reference only.

---

## 24. Future Evolution

Future missions may add implementation details, but only if they preserve:

- identity uniqueness;
- organizational knowledge inheritance;
- clean lifecycle boundaries;
- separation from execution mechanics.
