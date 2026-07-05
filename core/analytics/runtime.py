"""Performance Analytics Runtime — stateless metric aggregation.

Analyses snapshots and results produced by other runtimes and
generates consolidated performance metrics.

All classes are frozen dataclasses.
All methods are @staticmethod.
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from statistics import mean
from typing import TYPE_CHECKING
from uuid import UUID

from core.execution.runtime import ExecutionResult as AIExecutionResult
from core.llm.cost_tracker import LLMUsage
from core.skills.runtime import SkillRuntimeSnapshot
from core.workflows.runtime import WorkflowRuntimeSnapshot

if TYPE_CHECKING:
    from core.company.runtime import CompanyExecutionResult


# ------------------------------------------------------------------
# Data models
# ------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class PerformanceMetric:
    """A single named metric with value, unit, and optional labels."""

    name: str
    value: float
    unit: str = ""
    labels: dict[str, str] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class PerformanceSnapshot:
    """Collection of metrics at a point in time."""

    metrics: dict[str, PerformanceMetric] = field(default_factory=dict)
    timestamp: float = 0.0


@dataclass(frozen=True, slots=True)
class PerformanceTrace:
    """Metadata about an analysis operation."""

    sources_analyzed: list[str] = field(default_factory=list)
    duration_ms: float = 0.0
    metrics_count: int = 0


@dataclass(frozen=True, slots=True)
class PerformanceResult:
    """Output of a single analysis operation."""

    success: bool
    snapshot: PerformanceSnapshot | None = None
    trace: PerformanceTrace | None = None
    error_message: str = ""


# ------------------------------------------------------------------
# Helpers
# ------------------------------------------------------------------


def _safe_mean(values: list[float]) -> float:
    if not values:
        return 0.0
    return mean(values)


def _safe_div(numerator: float, denominator: float) -> float:
    if denominator == 0:
        return 0.0
    return numerator / denominator * 100.0


def _now() -> float:
    return time.time()


# ------------------------------------------------------------------
# PerformanceRuntime
# ------------------------------------------------------------------


class PerformanceRuntime:
    """Stateless performance analytics runtime.

    All methods are @staticmethod. Receives data; returns
    PerformanceResult with consolidated metrics.
    """

    # --------------------------------------------------------------
    # Core analysis helpers
    # --------------------------------------------------------------

    @staticmethod
    def _make_metric(name: str, value: float, unit: str = "", **labels: str) -> PerformanceMetric:
        return PerformanceMetric(name=name, value=value, unit=unit, labels=labels or {})

    @staticmethod
    def _snapshot_from_dict(metrics: dict[str, PerformanceMetric]) -> PerformanceSnapshot:
        return PerformanceSnapshot(metrics=metrics, timestamp=_now())

    @staticmethod
    def _result(snapshot: PerformanceSnapshot, sources: list[str], duration: float) -> PerformanceResult:
        return PerformanceResult(
            success=True,
            snapshot=snapshot,
            trace=PerformanceTrace(
                sources_analyzed=sources,
                duration_ms=duration * 1000.0,
                metrics_count=len(snapshot.metrics),
            ),
        )

    @staticmethod
    def _error(msg: str) -> PerformanceResult:
        return PerformanceResult(success=False, error_message=msg)

    # --------------------------------------------------------------
    # analyze_company
    # --------------------------------------------------------------

    @staticmethod
    def analyze_company(
        company_results: list[CompanyExecutionResult] | None = None,
        workflow_snapshots: list[WorkflowRuntimeSnapshot] | None = None,
        skills: list[SkillRuntimeSnapshot] | None = None,
    ) -> PerformanceResult:
        """Aggregate company-wide performance metrics."""
        start = _now()
        cr = company_results or []
        ws = workflow_snapshots or []
        sk = skills or []

        total = len(cr)
        success_count = sum(1 for r in cr if r.success)
        durations = [r.duration for r in cr if r.duration > 0]
        avg_time = _safe_mean(durations)

        completed_wfs = sum(1 for w in ws if w.state.value == "completed")

        memory_records = 0
        knowledge_entries = 0
        approved_decisions = 0
        rejected_decisions = 0
        for r in cr:
            if r.learning_pipeline_result is not None:
                lp = r.learning_pipeline_result
                if hasattr(lp, "trace") and lp.trace is not None:
                    memory_records += getattr(lp.trace, "memory_records_count", 0)
                    knowledge_entries += getattr(lp.trace, "knowledge_records_count", 0)
            dr = r.decision_result
            if dr is not None:
                if dr.approved:
                    approved_decisions += 1
                else:
                    rejected_decisions += 1

        metrics: dict[str, PerformanceMetric] = {
            "total_execucoes": PerformanceRuntime._make_metric("total_execucoes", float(total), "count"),
            "execucoes_com_sucesso": PerformanceRuntime._make_metric("execucoes_com_sucesso", float(success_count), "count"),
            "taxa_de_sucesso": PerformanceRuntime._make_metric("taxa_de_sucesso", _safe_div(float(success_count), float(total)), "%"),
            "tempo_medio": PerformanceRuntime._make_metric("tempo_medio", avg_time, "s"),
            "skills_geradas": PerformanceRuntime._make_metric("skills_geradas", float(len(sk)), "count"),
            "knowledge_gerado": PerformanceRuntime._make_metric("knowledge_gerado", float(knowledge_entries), "count"),
            "memory_records": PerformanceRuntime._make_metric("memory_records", float(memory_records), "count"),
            "workflows_finalizados": PerformanceRuntime._make_metric("workflows_finalizados", float(completed_wfs), "count"),
            "decisoes_aprovadas": PerformanceRuntime._make_metric("decisoes_aprovadas", float(approved_decisions), "count"),
            "decisoes_rejeitadas": PerformanceRuntime._make_metric("decisoes_rejeitadas", float(rejected_decisions), "count"),
        }

        return PerformanceRuntime._result(
            PerformanceRuntime._snapshot_from_dict(metrics),
            ["CompanyExecutionResult", "WorkflowRuntimeSnapshot", "SkillRuntimeSnapshot"],
            _now() - start,
        )

    # --------------------------------------------------------------
    # analyze_employee
    # --------------------------------------------------------------

    @staticmethod
    def analyze_employee(
        employee_id: UUID,
        results: list[CompanyExecutionResult] | None = None,
    ) -> PerformanceResult:
        """Compute performance metrics for a specific employee."""
        start = _now()
        if employee_id is None:
            return PerformanceRuntime._error("employee_id is required")
        rs = results or []

        total = len(rs)
        success_count = sum(1 for r in rs if r.success)
        durations = [r.duration for r in rs if r.duration > 0]
        avg_time = _safe_mean(durations)

        metrics: dict[str, PerformanceMetric] = {
            "total_tarefas": PerformanceRuntime._make_metric("total_tarefas", float(total), "count", employee_id=str(employee_id)),
            "tarefas_com_sucesso": PerformanceRuntime._make_metric("tarefas_com_sucesso", float(success_count), "count", employee_id=str(employee_id)),
            "eficiencia": PerformanceRuntime._make_metric("eficiencia", _safe_div(float(success_count), float(total)), "%", employee_id=str(employee_id)),
            "tempo_medio": PerformanceRuntime._make_metric("tempo_medio", avg_time, "s", employee_id=str(employee_id)),
        }

        return PerformanceRuntime._result(
            PerformanceRuntime._snapshot_from_dict(metrics),
            [f"CompanyExecutionResult(employee={employee_id})"],
            _now() - start,
        )

    # --------------------------------------------------------------
    # analyze_department
    # --------------------------------------------------------------

    @staticmethod
    def analyze_department(
        department_id: UUID,
        results: list[CompanyExecutionResult] | None = None,
    ) -> PerformanceResult:
        """Compute performance metrics for a specific department."""
        start = _now()
        if department_id is None:
            return PerformanceRuntime._error("department_id is required")
        rs = results or []

        total = len(rs)
        success_count = sum(1 for r in rs if r.success)
        durations = [r.duration for r in rs if r.duration > 0]
        avg_time = _safe_mean(durations)

        metrics: dict[str, PerformanceMetric] = {
            "tarefas_por_departamento": PerformanceRuntime._make_metric("tarefas_por_departamento", float(total), "count", department_id=str(department_id)),
            "tarefas_com_sucesso": PerformanceRuntime._make_metric("tarefas_com_sucesso", float(success_count), "count", department_id=str(department_id)),
            "eficiencia": PerformanceRuntime._make_metric("eficiencia", _safe_div(float(success_count), float(total)), "%", department_id=str(department_id)),
            "tempo_medio": PerformanceRuntime._make_metric("tempo_medio", avg_time, "s", department_id=str(department_id)),
        }

        return PerformanceRuntime._result(
            PerformanceRuntime._snapshot_from_dict(metrics),
            [f"CompanyExecutionResult(department={department_id})"],
            _now() - start,
        )

    # --------------------------------------------------------------
    # analyze_workflow
    # --------------------------------------------------------------

    @staticmethod
    def analyze_workflow(
        snapshots: list[WorkflowRuntimeSnapshot] | None = None,
    ) -> PerformanceResult:
        """Aggregate workflow-level metrics."""
        start = _now()
        snaps = snapshots or []

        total = len(snaps)
        completed = sum(1 for s in snaps if s.state.value == "completed")
        progress_values = [s.progress for s in snaps]
        avg_progress = _safe_mean(progress_values)
        total_tasks = sum(len(s.task_ids) for s in snaps)

        metrics: dict[str, PerformanceMetric] = {
            "workflows_registrados": PerformanceRuntime._make_metric("workflows_registrados", float(total), "count"),
            "workflows_finalizados": PerformanceRuntime._make_metric("workflows_finalizados", float(completed), "count"),
            "taxa_conclusao": PerformanceRuntime._make_metric("taxa_conclusao", _safe_div(float(completed), float(total)), "%"),
            "progresso_medio": PerformanceRuntime._make_metric("progresso_medio", avg_progress, "%"),
            "total_tarefas": PerformanceRuntime._make_metric("total_tarefas", float(total_tasks), "count"),
        }

        return PerformanceRuntime._result(
            PerformanceRuntime._snapshot_from_dict(metrics),
            ["WorkflowRuntimeSnapshot"],
            _now() - start,
        )

    # --------------------------------------------------------------
    # analyze_execution
    # --------------------------------------------------------------

    @staticmethod
    def analyze_execution(
        executions: list[AIExecutionResult] | None = None,
        usages: list[LLMUsage] | None = None,
    ) -> PerformanceResult:
        """Aggregate AI execution and cost metrics."""
        start = _now()
        exs = executions or []
        uss = usages or []

        total_ex = len(exs)
        success_ex = sum(1 for e in exs if e.success)
        durations = [e.duration_seconds for e in exs if e.duration_seconds > 0]
        avg_time = _safe_mean(durations)

        # Cost
        total_cost = sum(u.estimated_cost for u in uss)
        total_tokens = sum(u.total_tokens for u in uss)
        avg_latency = _safe_mean([u.latency_ms for u in uss if u.latency_ms > 0])

        # Per-provider
        provider_costs: dict[str, float] = {}
        provider_counts: dict[str, int] = {}
        for u in uss:
            provider_costs[u.provider] = provider_costs.get(u.provider, 0.0) + u.estimated_cost
            provider_counts[u.provider] = provider_counts.get(u.provider, 0) + 1

        # Per-model
        model_costs: dict[str, float] = {}
        model_counts: dict[str, int] = {}
        for u in uss:
            key = f"{u.provider}/{u.model}"
            model_costs[key] = model_costs.get(key, 0.0) + u.estimated_cost
            model_counts[key] = model_counts.get(key, 0) + 1

        metrics: dict[str, PerformanceMetric] = {
            "total_execucoes": PerformanceRuntime._make_metric("total_execucoes", float(total_ex), "count"),
            "execucoes_com_sucesso": PerformanceRuntime._make_metric("execucoes_com_sucesso", float(success_ex), "count"),
            "taxa_de_sucesso": PerformanceRuntime._make_metric("taxa_de_sucesso", _safe_div(float(success_ex), float(total_ex)), "%"),
            "tempo_medio": PerformanceRuntime._make_metric("tempo_medio", avg_time, "s"),
            "custo_total": PerformanceRuntime._make_metric("custo_total", total_cost, "USD"),
            "total_tokens": PerformanceRuntime._make_metric("total_tokens", float(total_tokens), "count"),
            "latencia_media": PerformanceRuntime._make_metric("latencia_media", avg_latency, "ms"),
        }

        for provider, cost in provider_costs.items():
            metrics[f"custo_por_provider:{provider}"] = PerformanceRuntime._make_metric(
                f"custo_por_provider", cost, "USD", provider=provider,
            )

        for model_key, cost in model_costs.items():
            metrics[f"custo_por_modelo:{model_key}"] = PerformanceRuntime._make_metric(
                f"custo_por_modelo", cost, "USD", model=model_key,
            )

        return PerformanceRuntime._result(
            PerformanceRuntime._snapshot_from_dict(metrics),
            ["AIExecutionResult", "LLMUsage"],
            _now() - start,
        )

    # --------------------------------------------------------------
    # build_dashboard
    # --------------------------------------------------------------

    @staticmethod
    def build_dashboard(
        results: list[PerformanceResult] | None = None,
    ) -> PerformanceResult:
        """Merge multiple analysis results into a single dashboard snapshot."""
        start = _now()
        rs = results or []
        if not rs:
            return PerformanceRuntime._error("No results to build dashboard from")

        merged: dict[str, PerformanceMetric] = {}
        all_sources: list[str] = []
        for r in rs:
            if r.success and r.snapshot is not None:
                merged.update(r.snapshot.metrics)
            if r.trace is not None:
                all_sources.extend(r.trace.sources_analyzed)
            if not r.success:
                pass

        return PerformanceRuntime._result(
            PerformanceRuntime._snapshot_from_dict(merged),
            list(set(all_sources)),
            _now() - start,
        )

    # --------------------------------------------------------------
    # merge_metrics
    # --------------------------------------------------------------

    @staticmethod
    def merge_metrics(
        snapshots: list[PerformanceSnapshot] | None = None,
    ) -> PerformanceSnapshot:
        """Merge multiple snapshots into one. Later values overwrite earlier ones."""
        merged: dict[str, PerformanceMetric] = {}
        for s in snapshots or []:
            merged.update(s.metrics)
        return PerformanceSnapshot(metrics=merged, timestamp=_now())
