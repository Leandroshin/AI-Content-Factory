# Department Spec: <DepartmentName>

## Goal

What this department does for the AI Company.

## Why This Department Should Exist

Explain why this should be a department instead of just a helper function or
tool adapter.

## Suggested Files

```text
core/departments/<name>/
  models.py
  pipeline.py
  employee.py
  __init__.py
```

Optional only when clearly needed:

```text
formatter.py
scoring.py
compliance.py
```

## Models

List proposed frozen+slots models and their important fields.

## Pipeline Stages

List deterministic stages from `created` to `completed` or `failed`.

## Employee

Describe the concrete employee and hooks.

## Capabilities

Use existing capabilities first. Explain missing capabilities separately.

## Quality And Compliance

What rules must be checked.

## Observability

What snapshots and metrics should be added.

## Demo Plan

List positive, negative, and edge-case scenarios.

## MVP Boundaries

What must not be implemented in the first version.

## Future Adapters

Which external APIs/tools could be integrated later.

## Sources

Links for external claims, APIs, and policies.
