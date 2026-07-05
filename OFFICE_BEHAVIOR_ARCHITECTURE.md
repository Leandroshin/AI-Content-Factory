# Office Behavior Architecture — AI Company

## Purpose

This document defines the behavioral architecture of the 2.5D office as a
visual projection of the real state of the AI Company.

The office does not invent behavior. It only renders visible manifestations of
the organizational state derived from Runtime, Events, Message System, and
Observability.

## Core Principle

The 2.5D interface never decides what happens in the company.

It can only:
- observe state;
- render state;
- animate state transitions;
- display messages derived from real events;
- show movement and presence derived from domain signals.

If a behavior is not traceable to company state, it must not appear in the
office.

## Relationship with Other Layers

### Runtime

The Company Runtime is the source of organizational state.

It determines:
- who is active;
- who is idle;
- who is in a task;
- who is in training;
- who is paused;
- who is collaborating;
- who is in a meeting.

### Events

Events describe meaningful changes in the company.

The office may animate only what can be inferred from emitted events.

### Message System

Messages are the visible communication layer of the company.

The office may display:
- speech balloons;
- alerts;
- assignments;
- acknowledgements;
- completion notices;
- collaboration prompts.

### Observability

Observability provides the visual projection layer.

It exposes:
- active roles;
- current posture;
- current location;
- current status;
- task participation;
- movement eligibility;
- visibility constraints.

### Interface 2.5D

The interface consumes company state and translates it into visual presence.

It must remain passive and deterministic in relation to domain state.

## Visual States

### Directors

Directors may appear as:
- at their desk;
- in a meeting room;
- walking between areas;
- observing a mural;
- reviewing knowledge boards;
- in collaboration mode;
- temporarily paused;
- in idle observation.

Directors should visually emphasize coordination, review, and delegation.

### Departments

Departments are represented as zones or visual clusters.

They may appear as:
- active;
- waiting;
- blocked;
- under review;
- in planning;
- in collaboration;
- in maintenance.

### Employees

Employees may appear as:
- at workstation;
- moving to another area;
- in training;
- collaborating;
- in a meeting;
- studying;
- organizing knowledge;
- resting;
- paused;
- idle.

## State Transitions

State transitions must always originate from company signals.

Examples:
- Task assigned -> move to workstation;
- Meeting requested -> move to meeting area;
- Training requested -> move to training area;
- Collaboration started -> move to collaboration space;
- Task completed -> return to desk or idle posture;
- No task available -> remain idle or study.

The interface may animate transitions, but never choose them.

## Movement Criteria

Character movement may occur only when one of the following is true:
- a task has been assigned;
- a meeting has been scheduled;
- collaboration has been requested;
- training has started;
- a message requires presence in another area;
- the company state indicates relocation.

Movement must never be triggered by decorative logic.

## Idle Criteria

A character should remain Idle when:
- no task is assigned;
- no meeting is pending;
- no collaboration is required;
- no training is active;
- no relocation signal exists;
- the runtime indicates availability without action.

Idle is a valid company state, not an error.

## When a Character Talks

A character should speak only when:
- a message is emitted to that character;
- a task assignment is received;
- a result is delivered;
- a meeting begins;
- a policy or warning must be acknowledged;
- a collaboration request is active.

Speech must always be traceable to a message or event.

## When a Character Only Observes

A character should observe when:
- the company is in review mode;
- the character is awaiting a task;
- the character is monitoring a department;
- the character is in an idle learning phase;
- the current role is managerial or supervisory.

Observation is a visual posture, not a decision engine.

## When a Character Participates in Meetings

Meetings are visualized when:
- the runtime marks a meeting state;
- a director or employee receives a meeting message;
- a task requires alignment across roles;
- a decision requires collaboration.

The office may show gathering, seated presence, or active discussion.

## When a Character Returns to Workstation

A character should return to the workstation when:
- a meeting ends;
- training ends;
- collaboration ends;
- the task context returns to execution;
- the runtime indicates normal operation.

Returning to the workstation is a visual reflection of state recovery.

## Automatic Activities During No-Task Periods

When no Tasks are available, characters may visually engage in:
- study;
- training;
- knowledge organization;
- maintenance;
- social interaction;
- observation;
- planning.

These activities are only allowed if they correspond to a valid company state.

## Behavioral Differences by Role

### CEO

The CEO behaves as the highest coordination presence:
- observes broadly;
- delegates;
- attends strategic meetings;
- emits direction;
- rarely performs routine movement.

### Directors

Directors coordinate domains:
- move between strategic areas;
- review departments;
- attend operational meetings;
- inspect progress;
- supervise transitions.

### Employees

Employees execute operational presence:
- move to tasks;
- join training;
- collaborate;
- study;
- rest;
- return to desk;
- remain idle when appropriate.

## Office Growth Behavior

As the company grows, the office may:
- add more work zones;
- add more meeting spaces;
- add knowledge walls;
- add collaboration areas;
- represent departments more explicitly;
- increase visual density while preserving clarity.

Growth must not change the meaning of state; it only changes the richness of
representation.

## Derivation of Animations and Dialogues

Animations and speech balloons must be derived from:
- Events;
- Messages;
- Runtime state;
- Observability data.

They must never be produced by independent interface logic.

Examples:
- Task assigned -> walk to desk + assignment bubble;
- Result completed -> celebration bubble + return movement;
- Block detected -> warning bubble + stop animation;
- Training started -> move to training area + study posture.

## Example Flow — Task Lifecycle in the Office

```text
TASK CREATED
    |
    v
RUNTIME REGISTERS TASK
    |
    v
ORCHESTRATOR ASSIGNS DEPARTMENT
    |
    v
EMPLOYEE RECEIVES MESSAGE
    |
    v
EMPLOYEE MOVES TO DESK
    |
    v
WORKFLOW STARTS
    |
    v
ENGINEERING / EXECUTION SIGNALS OCCUR
    |
    v
EVENTS AND MESSAGES EMIT
    |
    v
RESULT COMPLETED
    |
    v
EMPLOYEE RETURNS TO IDLE OR STUDY
    |
    v
OFFICE UPDATES VISUAL STATE
```

## Example Flow — Collaboration

```text
TASK REQUIRES HELP
    |
    v
MESSAGE SYSTEM SENDS COLLABORATION REQUEST
    |
    v
SECOND EMPLOYEE MOVES TO COLLABORATION AREA
    |
    v
DIRECTOR OBSERVES FROM DEPARTMENT ZONE
    |
    v
EVENT RECORDED
    |
    v
BALLOONS AND ANIMATIONS RENDERED
```

## Architectural Rules

- The interface must not invent movement.
- The interface must not invent dialogue.
- The interface must not infer hidden task logic.
- The interface must not assign roles.
- The interface must not decide priority.
- The interface must not evaluate policies.
- The interface must not trigger work.

## Risks

- Overlapping responsibilities between visual cues and domain events.
- Visual exaggeration could be mistaken for actual execution.
- Idle behavior could become ambiguous without clear runtime signals.
- Growth could create crowded scenes if visual density is not controlled.

## Future Opportunities

- Add richer visual projections for nested team structures.
- Add more precise state-to-animation mapping rules.
- Add theme layers for different company products.
- Add non-intrusive visual summaries for managers and observers.

## Final Rule

The office is a projection of the company, not a simulator of independent
behavior.