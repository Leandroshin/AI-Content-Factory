"""Foundation demo for the AI Execution Runtime — no Runtime dependencies.

Uses only plain dataclasses as snapshots and a fake LLM callable.
Validates the full pipeline: prepare_context → execute_llm →
validate_output → build_result.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any
from uuid import UUID, uuid4

from core.execution import ExecutionContext, ExecutionResult, ExecutionRuntime, ExecutionTrace
from core.llm.models import LLMRequest, LLMResponse


# ------------------------------------------------------------------
# Plain snapshot-like objects (no Runtime involved)
# ------------------------------------------------------------------


@dataclass
class TaskSnapshot:
    task_id: UUID
    name: str
    prompt_template: str = ""
    metadata: object = None


@dataclass
class EmployeeSnapshot:
    employee_id: UUID
    name: str
    role: str = "generic"


# ------------------------------------------------------------------
# Fake LLM callables
# ------------------------------------------------------------------


def _fake_llm_success(request: LLMRequest) -> LLMResponse:
    """Returns a successful fixed response."""
    return LLMResponse(
        request_id=request.request_id,
        provider="fake",
        model=request.model,
        content="This is the generated content for the task.",
        input_tokens=20,
        output_tokens=10,
        total_tokens=30,
        finish_reason="stop",
    )


def _fake_llm_error(request: LLMRequest) -> LLMResponse:
    """Returns a response with error finish reason."""
    return LLMResponse(
        request_id=request.request_id,
        provider="fake",
        model=request.model,
        content="The model refused to generate this content.",
        input_tokens=5,
        output_tokens=1,
        total_tokens=6,
        finish_reason="error",
    )


def _fake_llm_empty(request: LLMRequest) -> LLMResponse:
    """Returns a response with empty content."""
    return LLMResponse(
        request_id=request.request_id,
        provider="fake",
        model=request.model,
        content="   ",
        input_tokens=10,
        output_tokens=0,
        total_tokens=10,
        finish_reason="stop",
    )


def _fake_llm_raises(request: LLMRequest) -> LLMResponse:
    """Simulates a provider crash."""
    raise RuntimeError("Provider connection timeout")


def _make_request(prompt: str = "Write a summary.") -> LLMRequest:
    return LLMRequest.create(
        prompt=prompt,
        model="gpt-4o",
        temperature=0.7,
    )


# ------------------------------------------------------------------
# Scenario 1: Successful execution
# ------------------------------------------------------------------


def scenario_successful_execution() -> None:
    """Full pipeline with a valid LLM response."""
    task = TaskSnapshot(task_id=uuid4(), name="Generate Report")
    employee = EmployeeSnapshot(employee_id=uuid4(), name="Alice")
    request = _make_request()

    result = ExecutionRuntime.execute(task, employee, request, _fake_llm_success)

    assert isinstance(result, ExecutionResult)
    assert result.success is True
    assert result.output == "This is the generated content for the task."
    assert result.error_message == ""
    assert result.duration_seconds >= 0
    print(f"[PASS] successful_execution           | success={result.success} "
          f"output='{result.output[:30]}...' duration={result.duration_seconds}s")


# ------------------------------------------------------------------
# Scenario 2: Provider error (exception)
# ------------------------------------------------------------------


def scenario_provider_error() -> None:
    """LLM callable raises an exception."""
    task = TaskSnapshot(task_id=uuid4(), name="Risk Analysis")
    employee = EmployeeSnapshot(employee_id=uuid4(), name="Bob")
    request = _make_request()

    result = ExecutionRuntime.execute(task, employee, request, _fake_llm_raises)

    assert result.success is False
    assert "exception" in result.error_message.lower()
    assert result.output == ""
    print(f"[PASS] provider_error                 | success={result.success} "
          f"error='{result.error_message}'")


# ------------------------------------------------------------------
# Scenario 3: Empty output
# ------------------------------------------------------------------


def scenario_empty_output() -> None:
    """LLM returns whitespace-only content."""
    task = TaskSnapshot(task_id=uuid4(), name="Format Email")
    employee = EmployeeSnapshot(employee_id=uuid4(), name="Charlie")
    request = _make_request()

    result = ExecutionRuntime.execute(task, employee, request, _fake_llm_empty)

    assert result.success is False
    assert "empty" in result.error_message.lower()
    assert result.output == ""
    print(f"[PASS] empty_output                   | success={result.success} "
          f"error='{result.error_message}'")


# ------------------------------------------------------------------
# Scenario 4: Invalid output (error finish reason)
# ------------------------------------------------------------------


def scenario_invalid_output() -> None:
    """LLM finishes with error reason."""
    task = TaskSnapshot(task_id=uuid4(), name="Complex Query")
    employee = EmployeeSnapshot(employee_id=uuid4(), name="Diana")
    request = _make_request()

    result = ExecutionRuntime.execute(task, employee, request, _fake_llm_error)

    assert result.success is False
    assert "finish_reason" in result.error_message.lower() or "error" in result.error_message.lower()
    assert result.output == ""
    print(f"[PASS] invalid_output                 | success={result.success} "
          f"finish_reason=error")


# ------------------------------------------------------------------
# Scenario 5: Duration calculated correctly
# ------------------------------------------------------------------


def scenario_duration_calculated() -> None:
    """duration_seconds reflects actual wall-clock time."""
    import time

    task = TaskSnapshot(task_id=uuid4(), name="Slow Task")
    employee = EmployeeSnapshot(employee_id=uuid4(), name="Eve")

    def _slow_llm(request: LLMRequest) -> LLMResponse:
        time.sleep(0.05)
        return _fake_llm_success(request)

    request = _make_request()
    result = ExecutionRuntime.execute(task, employee, request, _slow_llm)

    assert result.duration_seconds >= 0.05
    assert result.finished_at > result.started_at
    print(f"[PASS] duration_calculated            | duration={result.duration_seconds}s "
          f"(expected >= 0.05)")


# ------------------------------------------------------------------
# Scenario 6: Trace populated correctly
# ------------------------------------------------------------------


def scenario_trace_populated() -> None:
    """ExecutionTrace contains all stages, provider, and model."""
    task = TaskSnapshot(task_id=uuid4(), name="Trace Test")
    employee = EmployeeSnapshot(employee_id=uuid4(), name="Frank")
    request = _make_request()

    result = ExecutionRuntime.execute(task, employee, request, _fake_llm_success)

    trace = result.trace
    assert isinstance(trace, ExecutionTrace)
    assert trace.stages == ["prepare_context", "execute_llm", "validate_output", "build_result"]
    assert trace.provider_used == "fake"
    assert trace.model_used == "gpt-4o"
    assert "start" in trace.timestamps
    assert "llm_response" in trace.timestamps
    print(f"[PASS] trace_populated                | stages={trace.stages} "
          f"provider={trace.provider_used} model={trace.model_used}")


# ------------------------------------------------------------------
# Scenario 7: Deterministic — same inputs produce same outputs
# ------------------------------------------------------------------


def scenario_deterministic() -> None:
    """Given the same inputs, outputs are deterministic."""
    task = TaskSnapshot(task_id=uuid4(), name="Fixed Task")
    employee = EmployeeSnapshot(employee_id=uuid4(), name="Grace")
    request = _make_request("Always the same prompt")

    r1 = ExecutionRuntime.execute(task, employee, request, _fake_llm_success)
    r2 = ExecutionRuntime.execute(task, employee, request, _fake_llm_success)

    assert r1.output == r2.output
    assert r1.success == r2.success
    assert r1.trace.provider_used == r2.trace.provider_used
    assert r1.trace.model_used == r2.trace.model_used
    print(f"[PASS] deterministic                  | output='{r1.output}' (identical)")


# ------------------------------------------------------------------
# Scenario 8: Multiple independent executions
# ------------------------------------------------------------------


def scenario_multiple_executions() -> None:
    """Each execution produces a unique execution_id and independent result."""
    task = TaskSnapshot(task_id=uuid4(), name="Batch Task")
    employee = EmployeeSnapshot(employee_id=uuid4(), name="Heidi")

    results = [
        ExecutionRuntime.execute(task, employee, _make_request(f"Job {i}"), _fake_llm_success)
        for i in range(5)
    ]

    assert len(results) == 5
    ids = [r.execution_id for r in results]
    assert len(set(ids)) == 5  # all unique

    for i, r in enumerate(results):
        assert r.success is True
        assert r.output == "This is the generated content for the task."

    print(f"[PASS] multiple_executions            | count={len(results)} "
          f"unique_ids={len(set(ids))}")


# ------------------------------------------------------------------
# Scenario 9: prepare_context returns correct ExecutionContext
# ------------------------------------------------------------------


def scenario_prepare_context() -> None:
    """prepare_context builds an ExecutionContext with correct fields."""
    task = TaskSnapshot(task_id=uuid4(), name="Context Test")
    employee = EmployeeSnapshot(employee_id=uuid4(), name="Ivan")
    request = _make_request()

    ctx = ExecutionRuntime.prepare_context(task, employee, request, {"env": "test"})

    assert isinstance(ctx, ExecutionContext)
    assert isinstance(ctx.execution_id, UUID)
    assert ctx.task_snapshot.name == "Context Test"
    assert ctx.employee_snapshot.name == "Ivan"
    assert ctx.llm_request.prompt == "Write a summary."
    assert ctx.metadata["env"] == "test"
    print(f"[PASS] prepare_context                | execution_id={ctx.execution_id} "
          f"task={ctx.task_snapshot.name} employee={ctx.employee_snapshot.name}")


# ------------------------------------------------------------------
# Main
# ------------------------------------------------------------------


def main() -> None:
    print("=" * 62)
    print("AI Execution Runtime Foundation Demo")
    print("=" * 62)
    print()

    scenario_successful_execution()
    scenario_provider_error()
    scenario_empty_output()
    scenario_invalid_output()
    scenario_duration_calculated()
    scenario_trace_populated()
    scenario_deterministic()
    scenario_multiple_executions()
    scenario_prepare_context()

    print()
    print("=" * 62)
    print("All Execution Runtime scenarios passed.")
    print("=" * 62)


if __name__ == "__main__":
    main()
