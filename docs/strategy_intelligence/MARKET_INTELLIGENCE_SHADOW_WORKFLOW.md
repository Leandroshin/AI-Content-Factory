# Market Intelligence Shadow Workflow

## Purpose

Mission 1 introduces the smallest safe bridge between `DailyLearningRadar` and future Market Intelligence. It accepts one owner-provided source, records immutable evidence, audits one claim, proposes a zero-cost experiment, and creates a hash-bound human approval request.

It does **not** call providers, publish content, alter production behavior, or write to `OrganizationalMemoryRuntime`.

## Flow

```text
Owner source
  -> transcript evidence + visual evidence
  -> source artifact with SHA-256
  -> claim
  -> cautious audit
  -> zero-cost experiment proposal
  -> pending KnowledgeCardDraft
  -> hash-bound HITL request
```

Approval covers only the exact offline experiment payload. It does not make the knowledge draft true and does not authorize promotion to company memory.

## Contracts

The package `core/intelligence/` provides frozen, slotted contracts:

- `EvidenceRef`
- `SourceArtifact`
- `ClaimRecord`
- `ClaimAudit`
- `ExperimentSpec`
- `KnowledgeCardDraft`
- `BoundApprovalRef`
- `MarketIntelligenceShadowResult`

Collections in these contracts use tuples. Canonical JSON normalizes dataclasses, enums, dates, UUIDs, paths, bytes, mappings, and sequences before hashing.

## Evidence rule

A transcript and screenshot from the same video prove what the creator presented, not that the creator's revenue or performance claim is independently true. The shadow workflow therefore returns `partial` and explicitly asks for:

1. independent corroboration;
2. a measured baseline-versus-variant result;
3. reconciled commission, refund, geography, and acquisition-cost data.

`ClaimAudit` rejects a `supported` verdict with no independent evidence.

## Approval integrity

`request_bound_approval()` stores the canonical payload SHA-256 in approval metadata. `verify_bound_approval()` recomputes three hashes before release:

1. the binding hash returned when review was requested;
2. the payload still stored in `ApprovalRuntime`;
3. the payload about to execute.

Any difference raises `ApprovalBindingError`. This prevents an approved draft from being changed silently after owner review.

## Demonstration

Run:

```powershell
python demo_market_intelligence_shadow_workflow.py
```

The demonstration uses the owner-provided FlowSpy transcript (`_Tnjul-5E8s`) and visual evidence when those research files are present. It has deterministic embedded evidence manifests for clean-clone regression. It proves that provider cost, publication attempts, and organizational memory remain zero.

## Promotion remains out of scope

A later mission may add an explicit promotion workflow, but only after an experiment is measured, independently audited, and separately approved. Mission 1 intentionally has no method that writes a `KnowledgeCardDraft` into organizational memory.
