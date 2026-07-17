# Archify as Visual Documentation Layer

## Decision

Archify is a strong candidate for an internal visual documentation and review
layer. It must not become an execution engine, an automatic source of truth, or
a replacement for the existing dashboard and department contracts.

Current status: `candidate_for_zero_cost_experiment`.

## Evidence

- Owner source: `https://www.youtube.com/watch?v=0NelhyQwP-w`
- Transcript: owner-provided, 25,911 characters
- Official project: `https://github.com/tt-a1i/archify`
- License observed in the official repository: MIT

The transcript proves what the video presents. It does not independently prove
commercial claims, performance claims, or claims made in the sponsored Appmax
segment.

## Useful patterns extracted

1. Describe the system before drawing it.
2. Convert the description into a typed intermediate representation.
3. Validate required nodes, links, labels, and layout constraints.
4. Render a self-contained visual artifact.
5. Review readability and iterate instead of accepting the first diagram.
6. Use different diagram types for different questions:
   - architecture for ownership and boundaries;
   - workflow for operational stages;
   - sequence for interactions between employees and tools;
   - data flow for evidence and state movement;
   - lifecycle for statuses and approval gates.
7. Export a portable artifact only after validation.

## What should not be learned automatically

- Sponsored product recommendations from the video.
- Revenue, conversion, speed, or quality claims without independent evidence.
- The assumption that a diagram proves the implementation is correct.
- The assumption that all project internals belong in one large diagram.
- Any instruction that bypasses owner approval, evidence, tests, or rollback.

## Proposed use inside the factory

Archify can support the future `Modo Entender` with focused visual maps. Each
map should answer one concrete owner question and link back to real evidence.

Initial map set:

1. Learning source lifecycle:
   `Source -> Transcript -> Evidence -> Audit -> Experiment -> Knowledge`.
2. Product campaign lifecycle:
   `URL -> Research -> Creative Review -> Affiliate Link -> HITL -> Telegram`.
3. Content production lifecycle:
   `Brief -> Script -> Audio -> Image -> Video -> Quality -> Review`.
4. Publication sequence:
   owner approval, queue worker, Telegram adapter, receipt, audit record.

The dashboard remains the operational surface. Visual maps explain what an
action will trigger, what it will not trigger, and what output is expected.

## Zero-cost experiment

1. Install or run Archify only in an isolated, reversible workspace.
2. Generate the Learning Source Lifecycle from official contracts, not from
   guesses or transcript prose.
3. Validate every node and transition against repository files.
4. Compare owner comprehension before and after the visual map.
5. Reject the experiment if labels are misleading, the map becomes too dense,
   or maintenance cost is higher than its explanatory value.

Success criteria:

- Leandro can identify the current stage and next action without assistance.
- Every displayed stage has an official source file or API contract.
- No diagram authorizes execution, spending, publication, or memory promotion.
- The artifact can be regenerated after architecture changes.

## Promotion rule

This candidate may become an approved internal skill only after the zero-cost
experiment passes, the generated map is audited, and the owner approves the
exact workflow. Installation alone is not approval.
