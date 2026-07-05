# Employee Spec: <EmployeeName>

## Purpose

What this employee is responsible for.

## Department

Which department owns this employee.

## Inheritance

Expected chain:

```text
SpecialistEmployee -> ProductionEmployee -> <ConcreteEmployee>
```

## Inputs

What task context fields or models it receives.

## Outputs

What artifacts, plans, metrics, or decisions it returns.

## Pipeline Hooks

Which `ProductionEmployee` hooks need domain-specific behavior:

- `_check_reject`
- `_build_pipeline`
- `_estimate_duration`
- `_build_output_from_stages`
- `_build_metrics`
- `_build_summary`
- `_run_quality_check`
- `analyze_capability_needs`
- `state`

## Capabilities

List capability names, not concrete tools.

## Quality Rules

What must be validated before output is accepted.

## Observability

What should appear in snapshots or metrics.

## Demo Requirements

What scenarios a `demo_*.py` file must prove.

## Risks

What this employee must not do.
