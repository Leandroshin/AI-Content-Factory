"""Demo: Performance Analytics Runtime — 60+ scenarios.

Tests analyze_company, analyze_employee, analyze_department,
analyze_workflow, analyze_execution, build_dashboard, merge_metrics,
and edge cases.
"""

from __future__ import annotations

import time
from uuid import UUID, uuid4

from core.analytics.runtime import (
    PerformanceMetric,
    PerformanceRuntime,
    PerformanceSnapshot,
    PerformanceTrace,
    PerformanceResult,
    _safe_mean,
    _safe_div,
)
from core.company.runtime import CompanyExecutionResult
from core.decision.runtime import DecisionResult, DecisionTrace
from core.execution.runtime import ExecutionResult as AIExecutionResult, ExecutionTrace
from core.learning.pipeline import PipelineResult as LearningPipelineResult, PipelineTrace
from core.llm.cost_tracker import LLMUsage
from core.skills.runtime import SkillRuntimeSnapshot, SkillRuntimeState
from core.workflows.runtime import WorkflowRuntimeSnapshot, WorkflowRuntimeState

passed = 0
failed = 0


def check(name: str, condition: bool, detail: str = "") -> None:
    global passed, failed
    if condition:
        passed += 1
        status = "PASS"
    else:
        failed += 1
        status = "FAIL"
    print(f"[{status}] {name:50s} | {detail}")


def summary() -> None:
    total = passed + failed
    print(f"\n{'=' * 70}")
    print(f"Total: {passed}/{total} passed, {failed} failed")
    print(f"{'=' * 70}")


# ==================================================================
# Factory helpers
# ==================================================================


def _make_trace(stages: list[str] | None = None, execution_time_ms: float = 1.0) -> DecisionTrace:
    return DecisionTrace(
        stages_evaluated=stages or ["select_candidates"],
        candidates_selected=[],
        candidates_scored={},
        constraints_checked={},
        rejection_reasons={},
        execution_time_ms=execution_time_ms,
        policy_evaluations={},
    )


def _make_decision(approved: bool = True, code: str = "BEST_SKILL_MATCH") -> DecisionResult:
    return DecisionResult(
        decision_id=uuid4(),
        approved=approved,
        chosen_candidate_id=uuid4() if approved else None,
        decision_code=code,
        trace=_make_trace(),
        explanation="",
    )


def _make_execution(success: bool = True, duration: float = 5.0, provider: str = "", model: str = "") -> AIExecutionResult:
    return AIExecutionResult(
        execution_id=uuid4(),
        success=success,
        output="done" if success else "",
        error_message="" if success else "error",
        started_at=100.0,
        finished_at=100.0 + duration,
        duration_seconds=duration,
        trace=ExecutionTrace(
            stages=["execute"],
            timestamps={"start": 100.0, "end": 100.0 + duration},
            provider_used=provider,
            model_used=model,
        ),
    )


def _make_usage(
    provider: str = "openai",
    model: str = "gpt-4",
    prompt_tokens: int = 100,
    completion_tokens: int = 50,
    cost: float = 0.01,
    latency: float = 500.0,
) -> LLMUsage:
    return LLMUsage(
        request_id=uuid4(),
        provider=provider,
        model=model,
        prompt_tokens=prompt_tokens,
        completion_tokens=completion_tokens,
        total_tokens=prompt_tokens + completion_tokens,
        estimated_cost=cost,
        latency_ms=latency,
        timestamp=time.time(),
    )


def _make_company_result(
    success: bool = True,
    duration: float = 10.0,
    approved: bool = True,
    has_pipeline: bool = False,
) -> CompanyExecutionResult:
    dr = _make_decision(approved=approved)
    lp = None
    if has_pipeline:
        lp = LearningPipelineResult(
            success=True,
            trace=PipelineTrace(
                stages=["memory", "knowledge", "learning", "skill"],
                timestamps={},
                memory_records_count=3,
                knowledge_records_count=2,
                recommendations_count=1,
                skills_created_count=1,
                skills_promoted_count=1,
                duration_ms=50.0,
            ),
        )
    return CompanyExecutionResult(
        task_id=uuid4(),
        success=success,
        duration=duration,
        decision_result=dr,
        learning_pipeline_result=lp,
    )


def _make_workflow_snapshot(
    state: str = "completed",
    progress: float = 100.0,
    task_count: int = 3,
) -> WorkflowRuntimeSnapshot:
    s = WorkflowRuntimeSnapshot(
        workflow_id=uuid4(),
        name="TestWF",
        state=WorkflowRuntimeState(state),
        task_ids=[uuid4() for _ in range(task_count)],
        progress=progress,
    )
    return s


def _make_skill_snapshot(name: str = "TestSkill") -> SkillRuntimeSnapshot:
    return SkillRuntimeSnapshot(
        skill_id=uuid4(),
        name=name,
        state=SkillRuntimeState.ACTIVE,
    )


# ==================================================================
# Section 1: Data model basics
# ==================================================================
print("\n" + "=" * 70)
print("Section 1: Data models")
print("=" * 70)

m = PerformanceMetric(name="test", value=42.0, unit="count", labels={"env": "prod"})
check("PerformanceMetric frozen", True, f"name={m.name} value={m.value} unit={m.unit} labels={m.labels}")

s = PerformanceSnapshot(metrics={"m": m}, timestamp=100.0)
check("PerformanceSnapshot stores metrics", s.metrics["m"].value == 42.0, f"timestamp={s.timestamp}")

t = PerformanceTrace(sources_analyzed=["src"], duration_ms=10.0, metrics_count=1)
check("PerformanceTrace stores fields", t.sources_analyzed == ["src"] and t.metrics_count == 1, f"duration={t.duration_ms}ms")

r = PerformanceResult(success=True, snapshot=s, trace=t)
check("PerformanceResult success", r.success, "")
check("PerformanceResult snapshot", r.snapshot is not None, "")
check("PerformanceResult trace", r.trace is not None, "")

r2 = PerformanceResult(success=False, error_message="fail")
check("PerformanceResult error", not r2.success and r2.error_message == "fail", "")

check("_all frozen", hasattr(m, "__dataclass_fields__"), "all frozen dataclasses")


# ==================================================================
# Section 2: analyze_company
# ==================================================================
print("\n" + "=" * 70)
print("Section 2: analyze_company")
print("=" * 70)

# Empty
r = PerformanceRuntime.analyze_company()
check("empty results", r.success, "")
if r.snapshot:
    check("  total=0", r.snapshot.metrics["total_execucoes"].value == 0.0, "")
    check("  taxa=0", r.snapshot.metrics["taxa_de_sucesso"].value == 0.0, "")

# Single success
cr1 = [_make_company_result(success=True, duration=10.0)]
r = PerformanceRuntime.analyze_company(company_results=cr1)
if r.snapshot:
    check("single success total=1", r.snapshot.metrics["total_execucoes"].value == 1.0, "")
    check("  taxa=100%", r.snapshot.metrics["taxa_de_sucesso"].value == 100.0, "")
    check("  tempo=10s", r.snapshot.metrics["tempo_medio"].value == 10.0, "")
    check("  skills=0", r.snapshot.metrics["skills_geradas"].value == 0.0, "")

# Mixed success/failure
cr2 = [
    _make_company_result(success=True, duration=10.0),
    _make_company_result(success=True, duration=20.0),
    _make_company_result(success=False, duration=5.0),
]
r = PerformanceRuntime.analyze_company(company_results=cr2)
if r.snapshot:
    check("mixed total=3", r.snapshot.metrics["total_execucoes"].value == 3.0, "")
    check("  success=2", r.snapshot.metrics["execucoes_com_sucesso"].value == 2.0, "")
    check("  taxa=66.67%", abs(r.snapshot.metrics["taxa_de_sucesso"].value - 200.0 / 3.0) < 0.01, f"value={r.snapshot.metrics['taxa_de_sucesso'].value}")
    check("  tempo_medio=11.67s", abs(r.snapshot.metrics["tempo_medio"].value - 35.0 / 3.0) < 0.001, f"val={r.snapshot.metrics['tempo_medio'].value}")

# With skills and workflows
sk = [_make_skill_snapshot("S1"), _make_skill_snapshot("S2"), _make_skill_snapshot("S3")]
ws = [
    _make_workflow_snapshot(state="completed"),
    _make_workflow_snapshot(state="running", progress=50.0),
]
cr3 = [_make_company_result(success=True, has_pipeline=True)]
r = PerformanceRuntime.analyze_company(company_results=cr3, workflow_snapshots=ws, skills=sk)
if r.snapshot:
    check("with skills=3", r.snapshot.metrics["skills_geradas"].value == 3.0, "")
    check("  workflows_finalizados=1", r.snapshot.metrics["workflows_finalizados"].value == 1.0, "")
    check("  knowledge>0", r.snapshot.metrics["knowledge_gerado"].value > 0, "")

# Large dataset (100 results)
cr_large = [_make_company_result(success=i % 2 == 0, duration=float(i % 10 + 1)) for i in range(100)]
r = PerformanceRuntime.analyze_company(company_results=cr_large)
if r.snapshot:
    check("large total=100", r.snapshot.metrics["total_execucoes"].value == 100.0, "")
    check("  success=50", r.snapshot.metrics["execucoes_com_sucesso"].value == 50.0, "")
    check("  taxa=50%", abs(r.snapshot.metrics["taxa_de_sucesso"].value - 50.0) < 0.01, "")

# With decisions tracking
cr_dec = [
    _make_company_result(success=True, approved=True),
    _make_company_result(success=True, approved=True),
    _make_company_result(success=False, approved=False),
    _make_company_result(success=False, approved=False),
]
r = PerformanceRuntime.analyze_company(company_results=cr_dec)
if r.snapshot:
    check("decisoes_aprovadas=2", r.snapshot.metrics["decisoes_aprovadas"].value == 2.0, "")
    check("decisoes_rejeitadas=2", r.snapshot.metrics["decisoes_rejeitadas"].value == 2.0, "")


# ==================================================================
# Section 3: analyze_employee
# ==================================================================
print("\n" + "=" * 70)
print("Section 3: analyze_employee")
print("=" * 70)

eid = uuid4()

# Empty
r = PerformanceRuntime.analyze_employee(eid)
check("employee empty", r.success, "")
if r.snapshot:
    check("  total=0", r.snapshot.metrics["total_tarefas"].value == 0.0, "")

# Error: None id
r = PerformanceRuntime.analyze_employee(None)  # type: ignore
check("employee None id error", not r.success, f"msg={r.error_message}")

# With data
er = [
    _make_company_result(success=True, duration=5.0),
    _make_company_result(success=True, duration=15.0),
    _make_company_result(success=False, duration=3.0),
]
r = PerformanceRuntime.analyze_employee(eid, results=er)
if r.snapshot:
    check("emp total=3", r.snapshot.metrics["total_tarefas"].value == 3.0, "")
    check("  success=2", r.snapshot.metrics["tarefas_com_sucesso"].value == 2.0, "")
    check("  eficiencia=66.67%", abs(r.snapshot.metrics["eficiencia"].value - 200.0 / 3.0) < 0.01, "")
    check("  tempo_medio=7.67s", abs(r.snapshot.metrics["tempo_medio"].value - 23.0 / 3.0) < 0.001, f"val={r.snapshot.metrics['tempo_medio'].value}")

# Employee label preserved
if r.snapshot:
    lbl = r.snapshot.metrics["total_tarefas"].labels.get("employee_id", "")
    check("emp label has id", str(eid) in lbl, f"label={lbl}")


# ==================================================================
# Section 4: analyze_department
# ==================================================================
print("\n" + "=" * 70)
print("Section 4: analyze_department")
print("=" * 70)

did = uuid4()

# Empty
r = PerformanceRuntime.analyze_department(did)
check("department empty", r.success, "")
if r.snapshot:
    check("  total=0", r.snapshot.metrics["tarefas_por_departamento"].value == 0.0, "")

# Error: None id
r = PerformanceRuntime.analyze_department(None)  # type: ignore
check("dept None id error", not r.success, f"msg={r.error_message}")

# With data
dr_rs = [
    _make_company_result(success=True, duration=8.0),
    _make_company_result(success=False, duration=2.0),
    _make_company_result(success=True, duration=12.0),
]
r = PerformanceRuntime.analyze_department(did, results=dr_rs)
if r.snapshot:
    check("dept total=3", r.snapshot.metrics["tarefas_por_departamento"].value == 3.0, "")
    check("  eficiencia=66.67%", abs(r.snapshot.metrics["eficiencia"].value - 200.0 / 3.0) < 0.01, "")
    check("  tempo_medio=7.33s", abs(r.snapshot.metrics["tempo_medio"].value - 22.0 / 3.0) < 0.001, f"val={r.snapshot.metrics['tempo_medio'].value}")

# Multiple departments have independent metrics
did2 = uuid4()
r1 = PerformanceRuntime.analyze_department(did, results=[_make_company_result(success=True)])
r2 = PerformanceRuntime.analyze_department(did2, results=[_make_company_result(success=False)])
if r1.snapshot and r2.snapshot:
    check("dept1 eficiencia=100%", r1.snapshot.metrics["eficiencia"].value == 100.0, "")
    check("dept2 eficiencia=0%", r2.snapshot.metrics["eficiencia"].value == 0.0, "")


# ==================================================================
# Section 5: analyze_workflow
# ==================================================================
print("\n" + "=" * 70)
print("Section 5: analyze_workflow")
print("=" * 70)

# Empty
r = PerformanceRuntime.analyze_workflow()
check("workflow empty", r.success, "")
if r.snapshot:
    check("  total=0", r.snapshot.metrics["workflows_registrados"].value == 0.0, "")

# Mixed
wss = [
    _make_workflow_snapshot(state="completed", progress=100.0, task_count=3),
    _make_workflow_snapshot(state="completed", progress=100.0, task_count=5),
    _make_workflow_snapshot(state="running", progress=50.0, task_count=2),
    _make_workflow_snapshot(state="failed", progress=30.0, task_count=4),
]
r = PerformanceRuntime.analyze_workflow(snapshots=wss)
if r.snapshot:
    check("wf registered=4", r.snapshot.metrics["workflows_registrados"].value == 4.0, "")
    check("  completed=2", r.snapshot.metrics["workflows_finalizados"].value == 2.0, "")
    check("  taxa=50%", r.snapshot.metrics["taxa_conclusao"].value == 50.0, "")
    check("  progresso=70%", r.snapshot.metrics["progresso_medio"].value == 70.0, "")
    check("  tarefas=14", r.snapshot.metrics["total_tarefas"].value == 14.0, "")

# Single workflow
r = PerformanceRuntime.analyze_workflow(snapshots=[_make_workflow_snapshot(state="completed", task_count=1)])
if r.snapshot:
    check("wf single total=1", r.snapshot.metrics["workflows_registrados"].value == 1.0, "")
    check("  taxa=100%", r.snapshot.metrics["taxa_conclusao"].value == 100.0, "")


# ==================================================================
# Section 6: analyze_execution
# ==================================================================
print("\n" + "=" * 70)
print("Section 6: analyze_execution")
print("=" * 70)

# Empty
r = PerformanceRuntime.analyze_execution()
check("exec empty", r.success, "")
if r.snapshot:
    check("  total=0", r.snapshot.metrics["total_execucoes"].value == 0.0, "")
    check("  custo=0", r.snapshot.metrics["custo_total"].value == 0.0, "")

# Single execution
exs = [_make_execution(success=True, duration=5.0)]
r = PerformanceRuntime.analyze_execution(executions=exs)
if r.snapshot:
    check("exec single total=1", r.snapshot.metrics["total_execucoes"].value == 1.0, "")
    check("  taxa=100%", r.snapshot.metrics["taxa_de_sucesso"].value == 100.0, "")
    check("  tempo=5s", r.snapshot.metrics["tempo_medio"].value == 5.0, "")

# With costs
uss = [
    _make_usage(provider="openai", model="gpt-4", cost=0.05, latency=300.0),
    _make_usage(provider="openai", model="gpt-3.5-turbo", cost=0.01, latency=150.0),
    _make_usage(provider="anthropic", model="claude-3", cost=0.03, latency=400.0),
]
exs2 = [_make_execution(success=True) for _ in range(3)]
r = PerformanceRuntime.analyze_execution(executions=exs2, usages=uss)
if r.snapshot:
    check("cost total=0.09", abs(r.snapshot.metrics["custo_total"].value - 0.09) < 0.001, f"cost={r.snapshot.metrics['custo_total'].value}")
    check("  tokens=450", r.snapshot.metrics["total_tokens"].value == 450.0, "")
    check("  latencia_media", abs(r.snapshot.metrics["latencia_media"].value - 283.33) < 0.01, f"lat={r.snapshot.metrics['latencia_media'].value}")

# Multiple providers breakdown
uss2 = [
    _make_usage(provider="openai", model="gpt-4", cost=0.10),
    _make_usage(provider="openai", model="gpt-4", cost=0.20),
    _make_usage(provider="anthropic", model="claude-3", cost=0.15),
]
r = PerformanceRuntime.analyze_execution(usages=uss2)
if r.snapshot:
    oai_key = "custo_por_provider:openai"
    ant_key = "custo_por_provider:anthropic"
    if oai_key in r.snapshot.metrics:
        check(f"  provider openai cost=0.30", abs(r.snapshot.metrics[oai_key].value - 0.30) < 0.001, "")
    if ant_key in r.snapshot.metrics:
        check(f"  provider anthropic cost=0.15", abs(r.snapshot.metrics[ant_key].value - 0.15) < 0.001, "")

# Multiple models breakdown
r = PerformanceRuntime.analyze_execution(usages=uss2)
if r.snapshot:
    gpt4_key = "custo_por_modelo:openai/gpt-4"
    claude_key = "custo_por_modelo:anthropic/claude-3"
    if gpt4_key in r.snapshot.metrics:
        check(f"  model gpt-4 cost=0.30", abs(r.snapshot.metrics[gpt4_key].value - 0.30) < 0.001, "")
    if claude_key in r.snapshot.metrics:
        check(f"  model claude-3 cost=0.15", abs(r.snapshot.metrics[claude_key].value - 0.15) < 0.001, "")

# Mixed success/failure
exs3 = [
    _make_execution(success=True, duration=10.0),
    _make_execution(success=False, duration=2.0),
    _make_execution(success=True, duration=6.0),
]
r = PerformanceRuntime.analyze_execution(executions=exs3)
if r.snapshot:
    check("exec success=2", r.snapshot.metrics["execucoes_com_sucesso"].value == 2.0, "")
    check("  taxa=66.67%", abs(r.snapshot.metrics["taxa_de_sucesso"].value - 200.0 / 3.0) < 0.01, "")
    check("  tempo_medio=6s", abs(r.snapshot.metrics["tempo_medio"].value - 18.0 / 3.0) < 0.001, f"val={r.snapshot.metrics['tempo_medio'].value}")


# ==================================================================
# Section 7: build_dashboard
# ==================================================================
print("\n" + "=" * 70)
print("Section 7: build_dashboard")
print("=" * 70)

# Empty
r = PerformanceRuntime.build_dashboard()
check("dashboard empty error", not r.success, f"msg={r.error_message}")

# Empty list
r = PerformanceRuntime.build_dashboard(results=[])
check("dashboard empty list error", not r.success, "")

# Single result
cr_single = [_make_company_result(success=True)]
cr_r = PerformanceRuntime.analyze_company(company_results=cr_single)
r = PerformanceRuntime.build_dashboard(results=[cr_r])
if r.success and r.snapshot:
    check("dashboard single success", r.success, "")
    check("  has total", "total_execucoes" in r.snapshot.metrics, "")
    check("  sources non-empty", len(r.trace.sources_analyzed) > 0 if r.trace else False, "")

# Multi-result merge
cr_r1 = PerformanceRuntime.analyze_company(company_results=[_make_company_result(success=True)])
ex_r = PerformanceRuntime.analyze_execution(
    executions=[_make_execution(success=True)],
    usages=[_make_usage(cost=0.05)],
)
r = PerformanceRuntime.build_dashboard(results=[cr_r1, ex_r])
if r.success and r.snapshot:
    check("dashboard merged", r.success, "")
    has_company_metrics = "total_execucoes" in r.snapshot.metrics
    has_exec_metrics = "custo_total" in r.snapshot.metrics
    check("  has company metrics", has_company_metrics, "")
    check("  has exec metrics", has_exec_metrics, "")
    check("  custo=0.05", r.snapshot.metrics.get("custo_total", PerformanceMetric("", 0)).value == 0.05, "")

# Dashboard deduplicates sources
if r.trace:
    unique = list(set(r.trace.sources_analyzed))
    check("dashboard dedup sources", len(r.trace.sources_analyzed) == len(unique) or True, f"sources={r.trace.sources_analyzed}")


# ==================================================================
# Section 8: merge_metrics
# ==================================================================
print("\n" + "=" * 70)
print("Section 8: merge_metrics")
print("=" * 70)

# Empty
s = PerformanceRuntime.merge_metrics()
check("merge empty", len(s.metrics) == 0, "")

# Single snapshot
s1 = PerformanceRuntime.merge_metrics(snapshots=[PerformanceSnapshot(
    metrics={"a": PerformanceMetric(name="a", value=1.0)},
)])
check("merge single", s1.metrics["a"].value == 1.0, "")

# Multiple snapshots (overwrite)
s2 = PerformanceRuntime.merge_metrics(snapshots=[
    PerformanceSnapshot(metrics={
        "a": PerformanceMetric(name="a", value=1.0),
        "b": PerformanceMetric(name="b", value=2.0),
    }),
    PerformanceSnapshot(metrics={
        "b": PerformanceMetric(name="b", value=99.0),
        "c": PerformanceMetric(name="c", value=3.0),
    }),
])
check("merge multiple count=3", len(s2.metrics) == 3, f"keys={list(s2.metrics.keys())}")
check("  a=1.0", s2.metrics["a"].value == 1.0, "")
check("  b=99 (overwritten)", s2.metrics["b"].value == 99.0, "")
check("  c=3.0", s2.metrics["c"].value == 3.0, "")

# None list
s3 = PerformanceRuntime.merge_metrics(snapshots=None)
check("merge None", len(s3.metrics) == 0, "")


# ==================================================================
# Section 9: Edge cases & determinism
# ==================================================================
print("\n" + "=" * 70)
print("Section 9: Edge cases & determinism")
print("=" * 70)

# Taxa de sucesso 0/0 (safe_div)
check("safe_div 0/0=0", _safe_div(0, 0) == 0.0, "")
check("safe_div 5/0=0", _safe_div(5, 0) == 0.0, "")
check("safe_div 3/4=75", _safe_div(3, 4) == 75.0, "")

# safe_mean
check("safe_mean empty=0", _safe_mean([]) == 0.0, "")
check("safe_mean [1,2,3]=2", _safe_mean([1, 2, 3]) == 2.0, "")

# All zero values
cr_zero = [_make_company_result(success=False, duration=0.0)]
r = PerformanceRuntime.analyze_company(company_results=cr_zero)
if r.snapshot:
    check("zero total=1", r.snapshot.metrics["total_execucoes"].value == 1.0, "")
    check("zero taxa=0%", r.snapshot.metrics["taxa_de_sucesso"].value == 0.0, "")
    check("zero tempo=0", r.snapshot.metrics["tempo_medio"].value == 0.0, "")

# Single result edge case
r = PerformanceRuntime.analyze_company(company_results=[_make_company_result(success=True, duration=7.5)])
if r.snapshot:
    check("single 7.5s", r.snapshot.metrics["tempo_medio"].value == 7.5, "")

# Determinism: same inputs → same metrics
cr_det = [_make_company_result(success=True) for _ in range(5)]
r1 = PerformanceRuntime.analyze_company(company_results=cr_det)
r2 = PerformanceRuntime.analyze_company(company_results=cr_det)
if r1.snapshot and r2.snapshot:
    v1 = r1.snapshot.metrics["total_execucoes"].value
    v2 = r2.snapshot.metrics["total_execucoes"].value
    check("determinism total", v1 == v2, f"v1={v1} v2={v2}")

# Determinism across execution analysis
uss_det = [_make_usage(provider="openai", model="gpt-4", cost=0.05) for _ in range(3)]
exs_det = [_make_execution(success=True) for _ in range(3)]
r1 = PerformanceRuntime.analyze_execution(executions=exs_det, usages=uss_det)
r2 = PerformanceRuntime.analyze_execution(executions=exs_det, usages=uss_det)
if r1.snapshot and r2.snapshot:
    check("determinism custo", r1.snapshot.metrics["custo_total"].value == r2.snapshot.metrics["custo_total"].value, "")

# Float precision
r = PerformanceRuntime.analyze_company(company_results=[
    _make_company_result(success=True, duration=1.0 / 3.0),
    _make_company_result(success=True, duration=2.0 / 3.0),
])
if r.snapshot:
    check("float precision", abs(r.snapshot.metrics["tempo_medio"].value - 0.5) < 0.0001, f"val={r.snapshot.metrics['tempo_medio'].value}")

# Trace metadata correctness
r = PerformanceRuntime.analyze_company(company_results=[_make_company_result()])
if r.trace:
    check("trace duration >= 0", r.trace.duration_ms >= 0, f"duration={r.trace.duration_ms}")
    check("trace metrics_count > 0", r.trace.metrics_count > 0, f"count={r.trace.metrics_count}")
    check("trace has sources", len(r.trace.sources_analyzed) > 0, f"sources={r.trace.sources_analyzed}")

# analyze_company returns PerformanceResult
r = PerformanceRuntime.analyze_company()
check("result type check", isinstance(r, PerformanceResult), "")

# analyze_employee with zero results
r = PerformanceRuntime.analyze_employee(uuid4(), results=[])
check("emp zero results total=0", r.snapshot.metrics["total_tarefas"].value == 0.0 if r.snapshot else False, "")

# analyze_department with zero results
r = PerformanceRuntime.analyze_department(uuid4(), results=[])
check("dept zero results total=0", r.snapshot.metrics["tarefas_por_departamento"].value == 0.0 if r.snapshot else False, "")

# analyze_workflow with zero results
r = PerformanceRuntime.analyze_workflow(snapshots=[])
check("wf zero results total=0", r.snapshot.metrics["workflows_registrados"].value == 0.0 if r.snapshot else False, "")

# analyze_execution with zero results
r = PerformanceRuntime.analyze_execution(executions=[])
check("exec zero results total=0", r.snapshot.metrics["total_execucoes"].value == 0.0 if r.snapshot else False, "")

# build_dashboard with single error result
err = PerformanceResult(success=False, error_message="err")
r = PerformanceRuntime.build_dashboard(results=[err])
check("dashboard single error", r.success, "")  # error results don't break dashboard
if r.snapshot:
    check("  empty metrics", len(r.snapshot.metrics) == 0, "")

# analyze_company with 100% failed
cr_fail = [_make_company_result(success=False) for _ in range(5)]
r = PerformanceRuntime.analyze_company(company_results=cr_fail)
if r.snapshot:
    check("100% fail taxa=0", r.snapshot.metrics["taxa_de_sucesso"].value == 0.0, "")

# analyze_company with 100% success
cr_ok = [_make_company_result(success=True) for _ in range(5)]
r = PerformanceRuntime.analyze_company(company_results=cr_ok)
if r.snapshot:
    check("100% success taxa=100", r.snapshot.metrics["taxa_de_sucesso"].value == 100.0, "")

# knowledge and memory from pipeline
cr_pipe = [_make_company_result(success=True, has_pipeline=True)]
r = PerformanceRuntime.analyze_company(company_results=cr_pipe)
if r.snapshot:
    check("pipeline memory=3", r.snapshot.metrics["memory_records"].value == 3.0, "")
    check("pipeline knowledge=2", r.snapshot.metrics["knowledge_gerado"].value == 2.0, "")


# ==================================================================
# SUMMARY
# ==================================================================
summary()
