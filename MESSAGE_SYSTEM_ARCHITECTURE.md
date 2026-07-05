# Message System Architecture — AI Company

## Purpose

This document defines the conceptual architecture of the internal message system
of the AI Company.

The message system exists to represent communication signals between layers of
the company without becoming execution logic. It is architectural and
documentary, not functional.

---

## 1. Purpose of the Message System

The message system provides a conceptual layer for:

- internal coordination;
- human-readable visibility;
- organizational signaling;
- alerts and reviews;
- progress and status communication;
- non-executing operational awareness.

```text
Subsystem State → Message → Visibility / Coordination
```

Messages do not perform actions. They represent meaning.

---

## 2. Internal Messages vs User Messages

### Internal messages

Internal messages are used between subsystems and internal coordination layers.
They may carry operational meaning, but they must not control company logic.

### User messages

User messages are visible to the user or reflected in the 2.5D interface.
They summarize company state, progress, warnings, approvals, and outcomes.

```text
Internal Message → Internal Coordination
User Message → Interface / Visibility
```

The same conceptual event may produce both an internal signal and a user-facing
message, but they must remain separate representations.

---

## 3. Message Types

The system should support a controlled set of message categories.

Examples:

- `Assignment`
- `Status`
- `Collaboration`
- `Alert`
- `Review`
- `Approval`
- `Knowledge`
- `Warning`
- `Error`
- `Completion`
- `Celebration`

These categories are semantic. They do not define runtime behavior.

---

## 4. Message Lifecycle

The lifecycle of a message may conceptually be:

```text
Created → Classified → Routed → Visible → Acknowledged → Archived
```

Possible intermediate states may include:

- `Draft`
- `Pending`
- `Ready`
- `Delivered`
- `Read`
- `Dismissed`
- `Expired`
- `Archived`

Messages remain informational throughout their lifecycle.

---

## 5. Priority

Messages may have priority to express relevance and urgency.

Possible conceptual levels:

- `Low`
- `Normal`
- `High`
- `Critical`

Priority affects display and routing order, not execution.

---

## 6. Recipients

Messages may be directed to:

- a single Employee;
- a Department;
- a Director layer;
- the Company Runtime;
- the Orchestrator;
- the AI Director;
- the Platform Director;
- the Knowledge Director;
- the Operations Director;
- the Observability layer;
- the 2.5D Interface;
- broadcast audiences.

Recipients determine visibility, not authority.

---

## 7. Broadcast vs Direct Message

### Direct message

A direct message targets a specific recipient or a narrow group.

### Broadcast message

A broadcast message is visible to a broader audience, usually with controlled
scope.

```text
Direct → specific recipient
Broadcast → scoped audience
```

Broadcasts should be used for company-wide status, critical alerts, and
organization signals.

---

## 8. Messages Between Directors

Messages between Directors represent strategic or coordinating communication.

Examples:

- Orchestrator ↔ Operations Director
- Orchestrator ↔ AI Director
- Orchestrator ↔ Platform Director
- Orchestrator ↔ Knowledge Director
- Runtime ↔ Observability

These messages should remain structured and not become hidden execution logic.

---

## 9. Messages Between Departments

Departments may exchange messages to coordinate ownership, progress, and
blocking conditions.

Examples:

- assignment handoff;
- dependency notice;
- collaboration request;
- escalation notice;
- completion notice.

Departments should communicate coordination signals, not internal implementation
details.

---

## 10. Messages Between Employees

Employees may exchange messages for collaboration, updates, and coordination.

Examples:

- task handoff;
- review request;
- assistance request;
- status update;
- knowledge sharing;
- celebration signal.

Employee messaging must not replace task ownership or authority boundaries.

---

## 11. Automatic Messages from Runtime

The Company Runtime may conceptually generate messages for:

- state changes;
- blockage events;
- maintenance mode;
- queue pressure;
- progress updates;
- recovery notifications;
- lifecycle transitions.

Runtime messages are state reflections, not decision makers.

---

## 12. Messages Derived from Events

Events may create one or more messages.

Example:

```text
Event → Message → Visibility
```

Events signal that something changed. Messages translate that signal into
communication suitable for humans and internal coordination layers.

---

## 13. Integration with Observability and the 2.5D Interface

Observability may consume messages to build summaries and visual state views.

The 2.5D interface may display:

- message cards;
- alerts;
- collaboration hints;
- status banners;
- progress indicators;
- celebration animations;
- warning indicators;
- approval confirmations.

```text
Message → Observability → 2.5D Interface
```

The visual layer may animate, highlight, or summarize messages, but it must not
control company logic.

---

## 14. What Should Be Visible to the User

User-visible messages may include:

- progress updates;
- completion notices;
- warnings;
- approvals;
- high-level collaboration signals;
- operational health summaries;
- selected knowledge notices;
- celebrations.

User-visible messages should be meaningful, concise, and non-leaking.

---

## 15. What Must Remain Internal

Internal-only messages may include:

- routing hints;
- policy evaluation details;
- intermediate coordination signals;
- fallback notices;
- internal block diagnostics;
- low-level state changes;
- implementation-specific metadata.

These should not be exposed directly to the user unless a future mission says so.

---

## 16. Animation in the 2.5D Environment

Messages may later drive animations such as:

- task arrival pulse;
- approval glow;
- warning shake;
- completion flourish;
- collaboration link highlight;
- knowledge update shimmer.

Animations are purely representational.

```text
Message → Visual Cue → 2.5D Animation
```

The animation must not alter routing, execution, or state authority.

---

## 17. Probable Engineering Structures

The future implementation may include:

- `Message`
- `MessageType`
- `MessagePriority`
- `MessageLifecycle`
- `MessageRecipient`
- `MessageRouter`
- `MessageBroker`
- `MessageDispatcher`
- `MessageRegistry`
- `MessageComposer`
- `MessageClassifier`
- `MessageVisibilityProjection`
- `MessageAnimationProjection`
- `MessageAdapterLayer`
- `MessagePolicyEngine`

These are implementation candidates, not public API commitments.

---

## 18. Deterministic vs IA-Enabled Decisions

### Deterministic

- message routing rules;
- recipient visibility rules;
- priority assignment rules;
- internal vs external visibility rules;
- broadcast scope rules;
- archive/expiry rules;
- message classification gates.

### Potentially IA-assisted in the future

- message summarization;
- collaboration signal interpretation;
- user-facing wording suggestions;
- severity suggestion;
- celebration copy generation;
- visibility recommendation assistance.

The rule is:

> Routing, visibility, and governance should remain deterministic.

---

## 19. What Must Not Happen

The message system must not become:

- a task engine;
- a workflow engine;
- an event bus implementation;
- a runtime coordinator;
- a policy engine;
- a persistence layer;
- a logging subsystem;
- a hidden command channel for execution.

---

## 20. Future Simplification Opportunities

Future implementation should aim for:

- a small message type taxonomy;
- one routing layer;
- separated internal and user-facing projections;
- lightweight animation projections;
- deterministic visibility rules;
- narrow adapters to observability and interface layers.

---

## 21. Final Statement

This document defines the conceptual architecture of the AI Company message
system. It is intentionally technical, non-functional, and contract-first.
