"""Foundation Strategy Runtime — deterministic recommendation engine.

Consumes snapshots and results from Analytics, Monitoring, Performance,
Company, and other runtimes to produce strategic recommendations.

100% stateless. All methods are @staticmethod. All models are frozen dataclasses.
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any
from uuid import UUID, uuid4

from core.analytics.runtime import PerformanceSnapshot
from core.knowledge.foundation import KnowledgeSnapshot
from core.learning.foundation import LearningSnapshot
from core.llm.cost_tracker import LLMCostSummary, LLMUsage
from core.monitoring.runtime import MonitoringSnapshot
from core.skills.foundation import SkillSnapshot
from core.skills.runtime import SkillRuntimeSnapshot
from core.workflows.runtime import WorkflowRuntimeSnapshot

if TYPE_CHECKING:
    from core.company.runtime import CompanyExecutionResult

# ------------------------------------------------------------------
# Category constants
# ------------------------------------------------------------------

CATEGORY_COST_REDUCTION = "Cost Reduction"
CATEGORY_PERFORMANCE_IMPROVEMENT = "Performance Improvement"
CATEGORY_WORKFLOW_OPTIMIZATION = "Workflow Optimization"
CATEGORY_EMPLOYEE_TRAINING = "Employee Training"
CATEGORY_SKILL_DEVELOPMENT = "Skill Development"
CATEGORY_KNOWLEDGE_EXPANSION = "Knowledge Expansion"
CATEGORY_DEPARTMENT_REORGANIZATION = "Department Reorganization"
CATEGORY_PROVIDER_RECOMMENDATION = "Provider Recommendation"
CATEGORY_MODEL_RECOMMENDATION = "Model Recommendation"
CATEGORY_MONITORING_ALERT = "Monitoring Alert"
CATEGORY_CAPACITY_PLANNING = "Capacity Planning"
CATEGORY_RISK_MITIGATION = "Risk Mitigation"

# ------------------------------------------------------------------
# Priority constants
# ------------------------------------------------------------------

PRIORITY_LOW = "LOW"
PRIORITY_MEDIUM = "MEDIUM"
PRIORITY_HIGH = "HIGH"
PRIORITY_CRITICAL = "CRITICAL"

_PRIORITY_ORDER = {PRIORITY_LOW: 0, PRIORITY_MEDIUM: 1, PRIORITY_HIGH: 2, PRIORITY_CRITICAL: 3}


# ------------------------------------------------------------------
# Data models
# ------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class StrategyRecommendation:
    """A single strategic recommendation generated from analysis."""

    recommendation_id: UUID
    category: str
    priority: str
    title: str
    description: str
    reason: str
    expected_benefit: str
    confidence: float
    metadata: dict[str, Any] = field(default_factory=dict)
    created_at: float = 0.0


@dataclass(frozen=True, slots=True)
class StrategySnapshot:
    """Collection of strategic recommendations at a point in time."""

    recommendations: tuple[StrategyRecommendation, ...] = field(default_factory=tuple)
    recommendations_by_category: dict[str, int] = field(default_factory=dict)
    recommendations_by_priority: dict[str, int] = field(default_factory=dict)
    created_at: float = 0.0
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class StrategyTrace:
    """Metadata about a strategy analysis operation."""

    stages: tuple[str, ...] = field(default_factory=tuple)
    timestamps: dict[str, float] = field(default_factory=dict)
    metrics: dict[str, float] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class StrategyResult:
    """Output of a single strategy analysis operation."""

    success: bool
    snapshot: StrategySnapshot | None = None
    trace: StrategyTrace | None = None
    error_message: str = ""


# ------------------------------------------------------------------
# Helpers
# ------------------------------------------------------------------


def _now() -> float:
    return time.time()


def _build_snapshot(
    recommendations: list[StrategyRecommendation],
    metadata: dict[str, Any] | None = None,
) -> StrategySnapshot:
    """Build a StrategySnapshot from a list of recommendations."""
    by_category: dict[str, int] = {}
    by_priority: dict[str, int] = {}
    for r in recommendations:
        by_category[r.category] = by_category.get(r.category, 0) + 1
        by_priority[r.priority] = by_priority.get(r.priority, 0) + 1
    return StrategySnapshot(
        recommendations=tuple(recommendations),
        recommendations_by_category=dict(sorted(by_category.items())),
        recommendations_by_priority=dict(sorted(by_priority.items(), key=lambda x: _PRIORITY_ORDER.get(x[0], 0))),
        created_at=_now(),
        metadata=metadata or {},
    )


def _result(
    recommendations: list[StrategyRecommendation],
    stages: list[str],
    metrics: dict[str, float],
    metadata: dict[str, Any] | None = None,
) -> StrategyResult:
    """Build a successful StrategyResult."""
    now = _now()
    snapshot = _build_snapshot(recommendations, metadata)
    trace = StrategyTrace(
        stages=tuple(stages),
        timestamps={"created_at": now},
        metrics=metrics,
    )
    return StrategyResult(success=True, snapshot=snapshot, trace=trace)


def _error_result(msg: str) -> StrategyResult:
    return StrategyResult(success=False, error_message=msg)


def _rec(
    category: str,
    priority: str,
    title: str,
    description: str,
    reason: str,
    expected_benefit: str,
    confidence: float,
    **metadata: Any,
) -> StrategyRecommendation:
    """Helper to create a single recommendation."""
    return StrategyRecommendation(
        recommendation_id=uuid4(),
        category=category,
        priority=priority,
        title=title,
        description=description,
        reason=reason,
        expected_benefit=expected_benefit,
        confidence=max(0.0, min(1.0, confidence)),
        metadata=metadata or {},
        created_at=_now(),
    )


# ------------------------------------------------------------------
# FoundationStrategyRuntime
# ------------------------------------------------------------------


class FoundationStrategyRuntime:
    """Stateless strategy recommendation engine.

    Consumes snapshots and results from the entire platform and
    produces deterministic, actionable recommendations.
    """

    # --------------------------------------------------------------
    # Core
    # --------------------------------------------------------------

    @staticmethod
    def create_snapshot() -> StrategySnapshot:
        """Create an empty strategy snapshot."""
        return StrategySnapshot(created_at=_now())

    @staticmethod
    def build_trace(
        stages: list[str] | None = None,
        metrics: dict[str, float] | None = None,
    ) -> StrategyTrace:
        """Create a StrategyTrace from raw data."""
        now = _now()
        return StrategyTrace(
            stages=tuple(stages or []),
            timestamps={"created_at": now},
            metrics=metrics or {},
        )

    @staticmethod
    def build_result(
        snapshot: StrategySnapshot,
        stages: list[str] | None = None,
        metrics: dict[str, float] | None = None,
    ) -> StrategyResult:
        """Wrap a snapshot in a StrategyResult."""
        now = _now()
        return StrategyResult(
            success=True,
            snapshot=snapshot,
            trace=StrategyTrace(
                stages=tuple(stages or []),
                timestamps={"created_at": now},
                metrics=metrics or {},
            ),
        )

    # --------------------------------------------------------------
    # Analysis: monitoring
    # --------------------------------------------------------------

    @staticmethod
    def analyze_monitoring(
        snapshot: MonitoringSnapshot,
    ) -> StrategyResult:
        """Analyze a MonitoringSnapshot and produce recommendations."""
        recs: list[StrategyRecommendation] = []
        stages = ["analyze_monitoring"]
        metrics: dict[str, float] = {
            "total_events": float(snapshot.total_events),
            "health_score": snapshot.health_score,
            "error_rate": snapshot.error_rate,
            "success_rate": snapshot.success_rate,
        }

        if snapshot.total_events == 0:
            recs.append(_rec(
                CATEGORY_MONITORING_ALERT, PRIORITY_MEDIUM,
                "No events observed",
                "The monitoring system has not recorded any events.",
                "Zero events indicate the platform may not be producing or publishing events.",
                "Enables detection of silent failures or misconfigured publishers.",
                0.6,
            ))

        if snapshot.health_score < 50:
            recs.append(_rec(
                CATEGORY_MONITORING_ALERT, PRIORITY_HIGH,
                f"Low health score: {snapshot.health_score:.1f}",
                f"The platform health score is {snapshot.health_score:.1f}, below the 50 threshold.",
                f"Health score of {snapshot.health_score:.1f} indicates significant operational issues.",
                "Improving health score reduces risk of platform instability.",
                0.85,
            ))

        if snapshot.error_rate > 20:
            recs.append(_rec(
                CATEGORY_MONITORING_ALERT, PRIORITY_HIGH,
                f"High error rate: {snapshot.error_rate:.1f}%",
                f"Error rate is {snapshot.error_rate:.1f}%, exceeding the 20% threshold.",
                f"{snapshot.total_errors} errors out of {snapshot.total_events} total events.",
                "Reducing error rate improves platform reliability and user trust.",
                0.8,
            ))

        if snapshot.error_rate > 50:
            recs.append(_rec(
                CATEGORY_RISK_MITIGATION, PRIORITY_CRITICAL,
                f"Critical error rate: {snapshot.error_rate:.1f}%",
                f"Error rate exceeds 50%, indicating severe platform issues.",
                "More than half of all events are errors, requiring immediate investigation.",
                "Immediate remediation prevents cascading failures.",
                0.95,
            ))

        if snapshot.total_events > 0 and snapshot.event_rate < 0.001:
            recs.append(_rec(
                CATEGORY_CAPACITY_PLANNING, PRIORITY_LOW,
                "Low event throughput",
                f"Event rate is {snapshot.event_rate:.6f} events/s, suggesting low platform activity.",
                "Very low event throughput may indicate insufficient workload.",
                "Investigating can identify opportunities to increase platform utilization.",
                0.3,
            ))

        if snapshot.uptime > 0 and snapshot.success_rate < 50:
            recs.append(_rec(
                CATEGORY_PERFORMANCE_IMPROVEMENT, PRIORITY_HIGH,
                "Success rate below 50%",
                f"Platform success rate is {snapshot.success_rate:.1f}%.",
                "Low success rate affects all downstream operations.",
                "Improving success rate increases overall platform efficiency.",
                0.75,
            ))

        return _result(recs, stages, metrics)

    # --------------------------------------------------------------
    # Analysis: performance
    # --------------------------------------------------------------

    @staticmethod
    def analyze_performance(
        snapshot: PerformanceSnapshot,
    ) -> StrategyResult:
        """Analyze a PerformanceSnapshot and produce recommendations."""
        recs: list[StrategyRecommendation] = []
        stages = ["analyze_performance"]
        metrics: dict[str, float] = {}
        m = snapshot.metrics

        success_rate = m.get("taxa_de_sucesso")
        if success_rate is not None:
            metrics["success_rate"] = success_rate.value
            if success_rate.value < 80:
                recs.append(_rec(
                    CATEGORY_PERFORMANCE_IMPROVEMENT, PRIORITY_HIGH,
                    f"Low success rate: {success_rate.value:.1f}%",
                    f"Performance success rate is {success_rate.value:.1f}%, below the 80% target.",
                    "Sub-80% success rate indicates systemic performance issues.",
                    "Improving to 80%+ increases throughput and reduces waste.",
                    0.75,
                ))

        tempo = m.get("tempo_medio")
        if tempo is not None and tempo.value > 30:
            recs.append(_rec(
                CATEGORY_PERFORMANCE_IMPROVEMENT, PRIORITY_MEDIUM,
                f"High average time: {tempo.value:.1f}s",
                f"Average execution time is {tempo.value:.1f}s, indicating slow operations.",
                "Slow execution times reduce platform throughput.",
                "Optimizing execution time improves overall efficiency.",
                0.5,
            ))

        total_ex = m.get("total_execucoes")
        if total_ex is not None and total_ex.value == 0:
            recs.append(_rec(
                CATEGORY_CAPACITY_PLANNING, PRIORITY_LOW,
                "No executions recorded",
                "Performance metrics show zero executions.",
                "No execution activity may indicate idle platform or integration issues.",
                "Diagnosing causes can improve platform utilization.",
                0.4,
            ))

        workflows_finalizados = m.get("workflows_finalizados")
        total_wf = m.get("workflows_registrados")
        if workflows_finalizados is not None and total_wf is not None and total_wf.value > 0:
            completion_rate = workflows_finalizados.value / total_wf.value * 100
            metrics["workflow_completion_rate"] = completion_rate
            if completion_rate < 50:
                recs.append(_rec(
                    CATEGORY_WORKFLOW_OPTIMIZATION, PRIORITY_HIGH,
                    f"Low workflow completion: {completion_rate:.1f}%",
                    f"Only {completion_rate:.1f}% of registered workflows have been completed.",
                    "Low completion rate suggests blocked or abandoned workflows.",
                    "Unblocking workflows increases value delivery.",
                    0.7,
                ))

        total_cost = m.get("custo_total")
        if total_cost is not None and total_cost.value > 10:
            recs.append(_rec(
                CATEGORY_COST_REDUCTION, PRIORITY_MEDIUM,
                f"High total cost: ${total_cost.value:.2f}",
                f"Total operational cost is ${total_cost.value:.2f}.",
                "Elevated costs may impact platform sustainability.",
                "Cost optimization improves operational efficiency.",
                0.45,
            ))

        return _result(recs, stages, metrics)

    # --------------------------------------------------------------
    # Analysis: costs
    # --------------------------------------------------------------

    @staticmethod
    def analyze_costs(
        cost_summary: LLMCostSummary | None = None,
        usages: list[LLMUsage] | None = None,
    ) -> StrategyResult:
        """Analyze LLM costs and produce recommendations."""
        recs: list[StrategyRecommendation] = []
        stages = ["analyze_costs"]
        metrics: dict[str, float] = {}

        if cost_summary is not None:
            metrics["total_cost"] = cost_summary.total_estimated_cost
            metrics["total_tokens"] = float(cost_summary.total_tokens)
            metrics["total_requests"] = float(cost_summary.total_requests)
            metrics["avg_latency"] = cost_summary.average_latency_ms

            if cost_summary.total_estimated_cost > 10:
                recs.append(_rec(
                    CATEGORY_COST_REDUCTION, PRIORITY_HIGH,
                    f"High LLM cost: ${cost_summary.total_estimated_cost:.2f}",
                    f"Total LLM estimated cost is ${cost_summary.total_estimated_cost:.2f}.",
                    f"{cost_summary.total_requests} requests consumed {cost_summary.total_tokens} tokens.",
                    "Reducing token usage or switching providers can lower costs.",
                    0.7,
                ))

            if cost_summary.average_latency_ms > 2000:
                recs.append(_rec(
                    CATEGORY_PERFORMANCE_IMPROVEMENT, PRIORITY_MEDIUM,
                    f"High average latency: {cost_summary.average_latency_ms:.0f}ms",
                    f"Average LLM latency is {cost_summary.average_latency_ms:.0f}ms, exceeding 2000ms.",
                    "High latency slows down all AI operations.",
                    "Switching to faster providers or models can improve response times.",
                    0.55,
                ))

            if cost_summary.total_tokens > 1_000_000:
                recs.append(_rec(
                    CATEGORY_CAPACITY_PLANNING, PRIORITY_MEDIUM,
                    f"High token consumption: {cost_summary.total_tokens:,}",
                    f"Total token consumption is {cost_summary.total_tokens:,}, exceeding 1M.",
                    "High token usage may impact costs and rate limits.",
                    "Implementing token optimization strategies can reduce costs.",
                    0.5,
                ))

            if len(cost_summary.usage_per_provider) > 2:
                top_provider = max(cost_summary.usage_per_provider.items(), key=lambda x: x[1][2])
                recs.append(_rec(
                    CATEGORY_PROVIDER_RECOMMENDATION, PRIORITY_MEDIUM,
                    f"Provider cost analysis: {top_provider[0]}",
                    f"Provider {top_provider[0]} accounts for the highest cost.",
                    "Concentrating usage on cost-effective providers can reduce expenses.",
                    "Negotiating volume pricing or switching providers may lower costs.",
                    0.4,
                ))

        if usages:
            model_costs: dict[str, float] = {}
            for u in usages:
                key = f"{u.provider}/{u.model}"
                model_costs[key] = model_costs.get(key, 0.0) + u.estimated_cost

            if model_costs:
                most_expensive = max(model_costs.items(), key=lambda x: x[1])
                if most_expensive[1] > 5:
                    recs.append(_rec(
                        CATEGORY_MODEL_RECOMMENDATION, PRIORITY_MEDIUM,
                        f"Expensive model: {most_expensive[0]} (${most_expensive[1]:.2f})",
                        f"Model {most_expensive[0]} costs ${most_expensive[1]:.2f} total.",
                        "High-cost models may not provide proportional value.",
                        "Evaluating cheaper alternatives or tiered model usage can optimize costs.",
                        0.45,
                    ))

                if len(model_costs) > 3:
                    recs.append(_rec(
                        CATEGORY_MODEL_RECOMMENDATION, PRIORITY_LOW,
                        f"Many models in use: {len(model_costs)}",
                        f"Using {len(model_costs)} different models across providers.",
                        "Fragmented model usage increases complexity and reduces negotiation power.",
                        "Standardising on fewer models can simplify management and reduce costs.",
                        0.35,
                    ))

        if not recs and cost_summary is not None:
            recs.append(_rec(
                CATEGORY_COST_REDUCTION, PRIORITY_LOW,
                "Costs within acceptable range",
                f"Total LLM cost is ${cost_summary.total_estimated_cost:.2f}, within normal parameters.",
                "No cost anomalies detected.",
                "Continue monitoring to maintain cost efficiency.",
                0.5,
            ))

        return _result(recs, stages, metrics)

    # --------------------------------------------------------------
    # Analysis: skills
    # --------------------------------------------------------------

    @staticmethod
    def analyze_skills(
        skill_snapshot: SkillSnapshot | None = None,
        skill_runtime_snapshots: list[SkillRuntimeSnapshot] | None = None,
    ) -> StrategyResult:
        """Analyze skills and produce recommendations."""
        recs: list[StrategyRecommendation] = []
        stages = ["analyze_skills"]
        metrics: dict[str, float] = {}

        if skill_snapshot is not None:
            total_skills = len(skill_snapshot.skills)
            metrics["total_skills_foundation"] = float(total_skills)
            if total_skills == 0:
                recs.append(_rec(
                    CATEGORY_SKILL_DEVELOPMENT, PRIORITY_HIGH,
                    "No skills in foundation",
                    "The skill foundation contains zero skills.",
                    "Without skills, the platform cannot improve autonomously.",
                    "Creating initial skills enables continuous improvement cycles.",
                    0.8,
                ))
            elif total_skills < 5:
                recs.append(_rec(
                    CATEGORY_SKILL_DEVELOPMENT, PRIORITY_MEDIUM,
                    f"Low skill count: {total_skills}",
                    f"Only {total_skills} skills exist in the foundation.",
                    "A small skill set limits the platform's adaptability.",
                    "Expanding skills improves coverage and capability.",
                    0.55,
                ))

            avg_level = sum(r.level for r in skill_snapshot.skills) / max(total_skills, 1)
            metrics["avg_skill_level"] = float(avg_level)
            if avg_level < 2 and total_skills > 0:
                recs.append(_rec(
                    CATEGORY_EMPLOYEE_TRAINING, PRIORITY_MEDIUM,
                    f"Low average skill level: {avg_level:.1f}",
                    f"Average skill level is {avg_level:.1f} (below intermediate).",
                    "Low skill levels indicate limited experience and capability.",
                    "Training programs can accelerate skill development.",
                    0.5,
                ))

        if skill_runtime_snapshots:
            total_runtime = len(skill_runtime_snapshots)
            metrics["total_skills_runtime"] = float(total_runtime)

            active_count = sum(1 for s in skill_runtime_snapshots if s.state.value == "active")
            if active_count == 0 and total_runtime > 0:
                recs.append(_rec(
                    CATEGORY_SKILL_DEVELOPMENT, PRIORITY_HIGH,
                    "No active skills in runtime",
                    f"All {total_runtime} runtime skills are inactive.",
                    "Inactive skills provide no value to the platform.",
                    "Investigating and activating skills improves platform capabilities.",
                    0.7,
                ))

        if not recs:
            recs.append(_rec(
                CATEGORY_SKILL_DEVELOPMENT, PRIORITY_LOW,
                "Skills are adequately provisioned",
                "Current skill inventory meets operational needs.",
                "No skill-related issues detected.",
                "Continue monitoring to identify future skill gaps.",
                0.4,
            ))

        return _result(recs, stages, metrics)

    # --------------------------------------------------------------
    # Analysis: learning
    # --------------------------------------------------------------

    @staticmethod
    def analyze_learning(
        learning_snapshot: LearningSnapshot | None = None,
        knowledge_snapshot: KnowledgeSnapshot | None = None,
    ) -> StrategyResult:
        """Analyze learning and knowledge and produce recommendations."""
        recs: list[StrategyRecommendation] = []
        stages = ["analyze_learning"]
        metrics: dict[str, float] = {}

        if knowledge_snapshot is not None:
            total_knowledge = len(knowledge_snapshot.records)
            metrics["total_knowledge_records"] = float(total_knowledge)
            if total_knowledge == 0:
                recs.append(_rec(
                    CATEGORY_KNOWLEDGE_EXPANSION, PRIORITY_HIGH,
                    "No knowledge records",
                    "The knowledge base is empty.",
                    "Without knowledge, the platform cannot learn from past experiences.",
                    "Populating the knowledge base improves decision quality.",
                    0.85,
                ))
            elif total_knowledge < 10:
                recs.append(_rec(
                    CATEGORY_KNOWLEDGE_EXPANSION, PRIORITY_MEDIUM,
                    f"Small knowledge base: {total_knowledge} records",
                    f"Only {total_knowledge} knowledge records exist.",
                    "A small knowledge base limits the platform's learning capacity.",
                    "Expanding knowledge improves recommendation quality.",
                    0.5,
                ))

            avg_confidence = sum(r.confidence for r in knowledge_snapshot.records) / max(total_knowledge, 1)
            metrics["avg_knowledge_confidence"] = float(avg_confidence)
            if avg_confidence < 0.5 and total_knowledge > 0:
                recs.append(_rec(
                    CATEGORY_KNOWLEDGE_EXPANSION, PRIORITY_MEDIUM,
                    f"Low knowledge confidence: {avg_confidence:.2f}",
                    f"Average knowledge confidence is {avg_confidence:.2f}.",
                    "Low confidence records may lead to unreliable recommendations.",
                    "Improving data quality increases trust in the knowledge base.",
                    0.45,
                ))

        if learning_snapshot is not None:
            total_recommendations = len(learning_snapshot.recommendations)
            metrics["total_learning_recommendations"] = float(total_recommendations)
            if total_recommendations > 20:
                recs.append(_rec(
                    CATEGORY_EMPLOYEE_TRAINING, PRIORITY_MEDIUM,
                    f"Many learning recommendations: {total_recommendations}",
                    f"There are {total_recommendations} pending learning recommendations.",
                    "A large backlog of recommendations indicates untapped learning potential.",
                    "Processing recommendations accelerates team growth.",
                    0.5,
                ))

        if not recs and knowledge_snapshot is not None:
            recs.append(_rec(
                CATEGORY_KNOWLEDGE_EXPANSION, PRIORITY_LOW,
                "Knowledge base adequately populated",
                f"Current knowledge base has {len(knowledge_snapshot.records)} records.",
                "Knowledge levels are satisfactory.",
                "Continue regular knowledge acquisition.",
                0.3,
            ))

        return _result(recs, stages, metrics)

    # --------------------------------------------------------------
    # Analysis: workflow
    # --------------------------------------------------------------

    @staticmethod
    def analyze_workflow(
        workflow_snapshots: list[WorkflowRuntimeSnapshot] | None = None,
    ) -> StrategyResult:
        """Analyze workflow snapshots and produce recommendations."""
        recs: list[StrategyRecommendation] = []
        stages = ["analyze_workflow"]
        snaps = workflow_snapshots or []
        metrics: dict[str, float] = {
            "total_workflows": float(len(snaps)),
        }

        if not snaps:
            recs.append(_rec(
                CATEGORY_WORKFLOW_OPTIMIZATION, PRIORITY_LOW,
                "No workflows registered",
                "There are no workflows registered in the system.",
                "Absence of workflows may indicate low platform activity.",
                "Creating workflows automates business processes.",
                0.3,
            ))
            return _result(recs, stages, metrics)

        completed = sum(1 for s in snaps if s.state.value == "completed")
        failed = sum(1 for s in snaps if s.state.value == "failed")
        running = sum(1 for s in snaps if s.state.value in ("running", "waiting"))
        metrics["completed_workflows"] = float(completed)
        metrics["failed_workflows"] = float(failed)
        metrics["running_workflows"] = float(running)

        if failed > 0:
            recs.append(_rec(
                CATEGORY_WORKFLOW_OPTIMIZATION, PRIORITY_HIGH,
                f"Failed workflows: {failed}",
                f"{failed} workflow(s) have failed out of {len(snaps)} total.",
                "Failed workflows represent incomplete business processes.",
                "Debugging and fixing failures improves completion rate.",
                0.7 + (0.1 * min(failed, 3)),
            ))

        if running > 3:
            recs.append(_rec(
                CATEGORY_WORKFLOW_OPTIMIZATION, PRIORITY_MEDIUM,
                f"Many running workflows: {running}",
                f"{running} workflows are currently running or waiting.",
                "Multiple concurrent workflows may indicate resource contention.",
                "Optimizing workflow scheduling improves throughput.",
                0.5,
            ))

        if completed == 0 and len(snaps) > 0:
            recs.append(_rec(
                CATEGORY_WORKFLOW_OPTIMIZATION, PRIORITY_CRITICAL,
                "No completed workflows",
                f"None of the {len(snaps)} registered workflows have been completed.",
                "Zero completions indicate blocked or stuck processes.",
                "Unblocking workflows is critical for platform value delivery.",
                0.9,
            ))

        stuck = sum(1 for s in snaps if s.progress > 50 and s.state.value not in ("completed", "failed", "cancelled"))
        if stuck > 0:
            recs.append(_rec(
                CATEGORY_WORKFLOW_OPTIMIZATION, PRIORITY_HIGH,
                f"Stuck workflows: {stuck}",
                f"{stuck} workflow(s) have >50% progress but are not completed.",
                "Partially completed workflows may be stuck or abandoned.",
                "Resolving stuck workflows recovers invested effort.",
                0.65,
            ))

        return _result(recs, stages, metrics)

    # --------------------------------------------------------------
    # Analysis: company
    # --------------------------------------------------------------

    @staticmethod
    def analyze_company(
        company_results: list[CompanyExecutionResult] | None = None,
    ) -> StrategyResult:
        """Analyze company execution results and produce recommendations."""
        recs: list[StrategyRecommendation] = []
        stages = ["analyze_company"]
        cr = company_results or []
        metrics: dict[str, float] = {
            "total_company_tasks": float(len(cr)),
        }

        if not cr:
            recs.append(_rec(
                CATEGORY_CAPACITY_PLANNING, PRIORITY_LOW,
                "No company tasks executed",
                "No company execution results have been recorded.",
                "Absence of execution data limits strategic insights.",
                "Initiating tasks enables data-driven strategy.",
                0.3,
            ))
            return _result(recs, stages, metrics)

        success_count = sum(1 for r in cr if r.success)
        fail_count = len(cr) - success_count
        metrics["successful_tasks"] = float(success_count)
        metrics["failed_tasks"] = float(fail_count)

        success_rate = success_count / len(cr) * 100
        metrics["company_success_rate"] = success_rate

        if success_rate < 60:
            recs.append(_rec(
                CATEGORY_RISK_MITIGATION, PRIORITY_CRITICAL,
                f"Company task success rate: {success_rate:.1f}%",
                f"Company task success rate is {success_rate:.1f}%, well below the 60% threshold.",
                f"{fail_count} out of {len(cr)} tasks failed.",
                "Immediate investigation into failures is required to maintain operations.",
                0.9,
            ))
        elif success_rate < 80:
            recs.append(_rec(
                CATEGORY_PERFORMANCE_IMPROVEMENT, PRIORITY_HIGH,
                f"Company task success rate: {success_rate:.1f}%",
                f"Company task success rate is {success_rate:.1f}%, below the 80% target.",
                f"{fail_count} tasks failed out of {len(cr)}.",
                "Improving success rate increases overall platform effectiveness.",
                0.7,
            ))

        durations = [r.duration for r in cr if r.duration > 0]
        if durations:
            avg_duration = sum(durations) / len(durations)
            metrics["avg_task_duration"] = avg_duration
            if avg_duration > 60:
                recs.append(_rec(
                    CATEGORY_PERFORMANCE_IMPROVEMENT, PRIORITY_MEDIUM,
                    f"High average task duration: {avg_duration:.1f}s",
                    f"Company tasks average {avg_duration:.1f}s, exceeding 60s.",
                    "Long-running tasks reduce platform throughput.",
                    "Optimizing task execution accelerates delivery.",
                    0.5,
                ))

        return _result(recs, stages, metrics)

    # --------------------------------------------------------------
    # Analysis: department
    # --------------------------------------------------------------

    @staticmethod
    def analyze_department(
        department_id: UUID | None = None,
        company_results: list[CompanyExecutionResult] | None = None,
        monitoring_snapshot: MonitoringSnapshot | None = None,
    ) -> StrategyResult:
        """Analyze department-level data and produce recommendations."""
        recs: list[StrategyRecommendation] = []
        stages = ["analyze_department"]
        metrics: dict[str, float] = {}

        if department_id is not None:
            metrics["department_id"] = float(abs(hash(str(department_id))) % 100000)

        if company_results:
            total = len(company_results)
            success_count = sum(1 for r in company_results if r.success)
            rate = success_count / total * 100 if total > 0 else 0
            metrics["department_task_count"] = float(total)
            metrics["department_success_rate"] = rate

            if rate < 50:
                recs.append(_rec(
                    CATEGORY_DEPARTMENT_REORGANIZATION, PRIORITY_HIGH,
                    "Low department success rate",
                    f"Department task success rate is {rate:.1f}%.",
                    "Persistent low success suggests structural or process issues.",
                    "Reorganizing workflows or reassigning tasks may improve outcomes.",
                    0.6,
                ))
            elif rate < 75:
                recs.append(_rec(
                    CATEGORY_PERFORMANCE_IMPROVEMENT, PRIORITY_MEDIUM,
                    f"Department success rate: {rate:.1f}%",
                    f"Department success rate is {rate:.1f}%, below the 75% target.",
                    "Moderate success rate indicates room for improvement.",
                    "Process optimization can increase department effectiveness.",
                    0.45,
                ))

        if monitoring_snapshot is not None and monitoring_snapshot.total_events > 0:
            if monitoring_snapshot.health_score < 50 and department_id is not None:
                recs.append(_rec(
                    CATEGORY_DEPARTMENT_REORGANIZATION, PRIORITY_MEDIUM,
                    f"Department monitoring health: {monitoring_snapshot.health_score:.1f}",
                    f"Monitoring health for department is {monitoring_snapshot.health_score:.1f}.",
                    "Low health score indicates potential department-level issues.",
                    "Reviewing department operations can improve stability.",
                    0.5,
                ))

        if not recs:
            recs.append(_rec(
                CATEGORY_PERFORMANCE_IMPROVEMENT, PRIORITY_LOW,
                "Department performing adequately",
                "No critical issues detected for this department.",
                "Department metrics are within normal ranges.",
                "Continue regular monitoring.",
                0.3,
            ))

        return _result(recs, stages, metrics)

    # --------------------------------------------------------------
    # Analysis: employee
    # --------------------------------------------------------------

    @staticmethod
    def analyze_employee(
        employee_id: UUID | None = None,
        company_results: list[CompanyExecutionResult] | None = None,
    ) -> StrategyResult:
        """Analyze employee-level data and produce recommendations."""
        recs: list[StrategyRecommendation] = []
        stages = ["analyze_employee"]
        metrics: dict[str, float] = {}

        if employee_id is None:
            return _error_result("employee_id is required")

        metrics["employee_id_hash"] = float(abs(hash(str(employee_id))) % 100000)
        cr = company_results or []
        metrics["employee_tasks"] = float(len(cr))

        if not cr:
            recs.append(_rec(
                CATEGORY_CAPACITY_PLANNING, PRIORITY_LOW,
                "Employee has no tasks",
                f"Employee {employee_id} has no completed tasks.",
                "No task data available for performance assessment.",
                "Assigning tasks enables performance evaluation and growth.",
                0.3,
            ))
            return _result(recs, stages, metrics)

        success_count = sum(1 for r in cr if r.success)
        rate = success_count / len(cr) * 100
        metrics["employee_success_rate"] = rate

        if rate < 40:
            recs.append(_rec(
                CATEGORY_RISK_MITIGATION, PRIORITY_HIGH,
                f"Employee success rate: {rate:.1f}%",
                f"Employee {employee_id} has a success rate of only {rate:.1f}%.",
                f"Only {success_count} of {len(cr)} tasks completed successfully.",
                "Immediate mentoring or process adjustments may be needed.",
                0.75,
            ))
        elif rate < 70:
            recs.append(_rec(
                CATEGORY_EMPLOYEE_TRAINING, PRIORITY_MEDIUM,
                f"Employee training recommended: {rate:.1f}%",
                f"Employee {employee_id} success rate is {rate:.1f}%.",
                "Below-70% success rate suggests additional training may be beneficial.",
                "Targeted training can improve employee performance.",
                0.5,
            ))

        durations = [r.duration for r in cr if r.duration > 0]
        if durations:
            avg_dur = sum(durations) / len(durations)
            metrics["employee_avg_duration"] = avg_dur
            if avg_dur > 120:
                recs.append(_rec(
                    CATEGORY_PERFORMANCE_IMPROVEMENT, PRIORITY_LOW,
                    f"Employee execution time: {avg_dur:.1f}s avg",
                    f"Employee {employee_id} averages {avg_dur:.1f}s per task.",
                    "High execution time may indicate challenging tasks or inefficiencies.",
                    "Analyzing task patterns can identify optimization opportunities.",
                    0.35,
                ))

        return _result(recs, stages, metrics)

    # --------------------------------------------------------------
    # Master recommendation
    # --------------------------------------------------------------

    @staticmethod
    def recommend(
        monitoring_snapshot: MonitoringSnapshot | None = None,
        performance_snapshot: PerformanceSnapshot | None = None,
        cost_summary: LLMCostSummary | None = None,
        usages: list[LLMUsage] | None = None,
        skill_snapshot: SkillSnapshot | None = None,
        skill_runtime_snapshots: list[SkillRuntimeSnapshot] | None = None,
        learning_snapshot: LearningSnapshot | None = None,
        knowledge_snapshot: KnowledgeSnapshot | None = None,
        workflow_snapshots: list[WorkflowRuntimeSnapshot] | None = None,
        company_results: list[CompanyExecutionResult] | None = None,
    ) -> StrategyResult:
        """Master analysis: run all analyzers and merge recommendations."""
        stages = ["recommend"]
        all_recs: list[StrategyRecommendation] = []
        merged_metrics: dict[str, float] = {}

        if monitoring_snapshot is not None:
            r = FoundationStrategyRuntime.analyze_monitoring(monitoring_snapshot)
            if r.success and r.snapshot:
                all_recs.extend(r.snapshot.recommendations)
                if r.trace:
                    merged_metrics.update(r.trace.metrics)
                stages.append("monitoring")

        if performance_snapshot is not None:
            r = FoundationStrategyRuntime.analyze_performance(performance_snapshot)
            if r.success and r.snapshot:
                all_recs.extend(r.snapshot.recommendations)
                if r.trace:
                    merged_metrics.update(r.trace.metrics)
                stages.append("performance")

        if cost_summary is not None or usages:
            r = FoundationStrategyRuntime.analyze_costs(cost_summary, usages)
            if r.success and r.snapshot:
                all_recs.extend(r.snapshot.recommendations)
                if r.trace:
                    merged_metrics.update(r.trace.metrics)
                stages.append("costs")

        if skill_snapshot is not None or skill_runtime_snapshots:
            r = FoundationStrategyRuntime.analyze_skills(skill_snapshot, skill_runtime_snapshots)
            if r.success and r.snapshot:
                all_recs.extend(r.snapshot.recommendations)
                if r.trace:
                    merged_metrics.update(r.trace.metrics)
                stages.append("skills")

        if learning_snapshot is not None or knowledge_snapshot is not None:
            r = FoundationStrategyRuntime.analyze_learning(learning_snapshot, knowledge_snapshot)
            if r.success and r.snapshot:
                all_recs.extend(r.snapshot.recommendations)
                if r.trace:
                    merged_metrics.update(r.trace.metrics)
                stages.append("learning")

        if workflow_snapshots is not None:
            r = FoundationStrategyRuntime.analyze_workflow(workflow_snapshots)
            if r.success and r.snapshot:
                all_recs.extend(r.snapshot.recommendations)
                if r.trace:
                    merged_metrics.update(r.trace.metrics)
                stages.append("workflow")

        if company_results is not None:
            r = FoundationStrategyRuntime.analyze_company(company_results)
            if r.success and r.snapshot:
                all_recs.extend(r.snapshot.recommendations)
                if r.trace:
                    merged_metrics.update(r.trace.metrics)
                stages.append("company")

        now = _now()
        snapshot = _build_snapshot(all_recs, {"source": "recommend"})
        trace = StrategyTrace(
            stages=tuple(stages),
            timestamps={"created_at": now},
            metrics=merged_metrics,
        )
        return StrategyResult(success=True, snapshot=snapshot, trace=trace)

    # --------------------------------------------------------------
    # Prioritize
    # --------------------------------------------------------------

    @staticmethod
    def prioritize(
        recommendations: list[StrategyRecommendation] | tuple[StrategyRecommendation, ...],
    ) -> list[StrategyRecommendation]:
        """Sort recommendations by priority (CRITICAL first) then confidence."""
        def sort_key(r: StrategyRecommendation) -> tuple[int, float]:
            return -_PRIORITY_ORDER.get(r.priority, 0), -r.confidence
        return sorted(recommendations, key=sort_key)

    # --------------------------------------------------------------
    # Merge
    # --------------------------------------------------------------

    @staticmethod
    def merge_recommendations(
        snapshots: list[StrategySnapshot],
    ) -> StrategySnapshot:
        """Merge multiple StrategySnapshots into one."""
        all_recs: list[StrategyRecommendation] = []
        merged_metadata: dict[str, Any] = {}
        seen_ids: set[UUID] = set()
        for s in snapshots:
            for r in s.recommendations:
                if r.recommendation_id not in seen_ids:
                    all_recs.append(r)
                    seen_ids.add(r.recommendation_id)
            merged_metadata.update(s.metadata)
        return _build_snapshot(all_recs, merged_metadata)

    # --------------------------------------------------------------
    # Filter
    # --------------------------------------------------------------

    @staticmethod
    def filter_recommendations(
        recommendations: list[StrategyRecommendation] | tuple[StrategyRecommendation, ...],
        category: str | None = None,
        priority: str | None = None,
        min_confidence: float = 0.0,
    ) -> list[StrategyRecommendation]:
        """Filter recommendations by category, priority, and minimum confidence."""
        result = list(recommendations)
        if category is not None:
            result = [r for r in result if r.category == category]
        if priority is not None:
            result = [r for r in result if r.priority == priority]
        if min_confidence > 0:
            result = [r for r in result if r.confidence >= min_confidence]
        return result

    # --------------------------------------------------------------
    # Group
    # --------------------------------------------------------------

    @staticmethod
    def group_by_category(
        recommendations: list[StrategyRecommendation] | tuple[StrategyRecommendation, ...],
    ) -> dict[str, list[StrategyRecommendation]]:
        """Group recommendations by category."""
        groups: dict[str, list[StrategyRecommendation]] = {}
        for r in recommendations:
            groups.setdefault(r.category, []).append(r)
        return dict(sorted(groups.items()))

    @staticmethod
    def group_by_priority(
        recommendations: list[StrategyRecommendation] | tuple[StrategyRecommendation, ...],
    ) -> dict[str, list[StrategyRecommendation]]:
        """Group recommendations by priority."""
        groups: dict[str, list[StrategyRecommendation]] = {}
        for r in recommendations:
            groups.setdefault(r.priority, []).append(r)
        return dict(sorted(groups.items(), key=lambda x: _PRIORITY_ORDER.get(x[0], 0)))
