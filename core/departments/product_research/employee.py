"""ProductResearchEmployee specialized in product discovery and shortlisting."""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Any
from uuid import UUID

from core.company.department_manager import DepartmentManager
from core.company.quality import QualityRuntime
from core.company.specialist_employee import (
    EmployeeSkill,
    EmployeeStatus,
    ReceivedTask,
    TaskAccepted,
    TaskDecision,
)
from core.departments.base.employee import ProductionEmployee
from core.departments.base.pipeline import ProductionPipeline
from core.departments.product_research.models import (
    MarketplaceSignal,
    ProductCandidate,
    ProductResearchBrief,
    ProductResearchMetrics,
)
from core.departments.product_research.pipeline import PipelineStage, ProductResearchPipeline
from core.events.bus import EventBus
from core.runtime import CompanyRuntime as CoreCompanyRuntime
from core.tools.capabilities import Capability
from core.tools.registry import ToolRegistry
from core.tools.runtime import ToolRuntime


@dataclass(frozen=True, slots=True)
class ProductResearchCapability:
    """Domain-specific product research capability metadata."""

    name: str
    proficiency: float = 0.5
    enabled: bool = True


class ProductResearchEmployee(ProductionEmployee):
    """Specialist employee for product research before affiliate production."""

    _DEPARTMENT_KEYWORD = "product_research"

    def __init__(
        self,
        company_runtime: CoreCompanyRuntime,
        employee_id: UUID,
        skills: tuple[EmployeeSkill, ...] = (),
        *,
        event_bus: EventBus | None = None,
        department_manager: DepartmentManager | None = None,
        tool_runtime: ToolRuntime | None = None,
        tool_registry: ToolRegistry | None = None,
        quality_runtime: QualityRuntime | None = None,
    ) -> None:
        super().__init__(
            company_runtime=company_runtime,
            employee_id=employee_id,
            skills=skills,
            event_bus=event_bus,
            department_manager=department_manager,
            tool_runtime=tool_runtime,
            tool_registry=tool_registry,
            quality_runtime=quality_runtime,
        )
        self._product_research_capabilities: dict[str, ProductResearchCapability] = {
            "candidate_intake": ProductResearchCapability("candidate_intake", 0.9),
            "market_signal_review": ProductResearchCapability("market_signal_review", 0.84),
            "winner_scoring": ProductResearchCapability("winner_scoring", 0.86),
            "creative_feasibility": ProductResearchCapability("creative_feasibility", 0.8),
            "affiliate_handoff": ProductResearchCapability("affiliate_handoff", 0.82),
            "risk_triage": ProductResearchCapability("risk_triage", 0.78),
        }
        self._current_product_research_brief: ProductResearchBrief | None = None

    @property
    def product_research_capabilities(self) -> dict[str, ProductResearchCapability]:
        return dict(self._product_research_capabilities)

    def receive_task(self, task: ReceivedTask) -> TaskDecision:
        if not _is_product_research_department(task.department):
            return super().receive_task(task)
        if self._workload >= self._max_workload:
            return super().receive_task(task)

        self._tasks[task.task_id] = task
        self._current_task_id = task.task_id
        self._workload += 1
        self._status = EmployeeStatus.ANALYZING

        self._current_product_research_brief = _coerce_brief(task)
        self._pipeline = ProductResearchPipeline(self._current_product_research_brief)

        self._publish(TaskAccepted(
            employee_id=self._employee_id,
            task_id=task.task_id,
            title=task.title,
            difficulty=0.45,
            estimated_time_minutes=self._estimate_duration(task.context),
            timestamp=time.time(),
        ))
        return TaskDecision.ACCEPTED

    def _check_reject(self, task: ReceivedTask) -> str | None:
        if not _is_product_research_department(task.department):
            return f"Department '{task.department}' is not product_research"
        if self._workload >= self._max_workload:
            return "Workload limit reached (max 3)"
        return None

    def _build_pipeline(self, task: ReceivedTask) -> ProductionPipeline:
        return ProductResearchPipeline(self._current_product_research_brief)

    def _estimate_duration(self, ctx: dict[str, Any]) -> int:
        candidates = _as_iterable(ctx.get("candidates", ()))
        return max(4, 3 + len(candidates))

    def _get_production_type(self) -> str:
        return "product_research"

    def _build_output_from_stages(
        self, final_output: dict[str, Any], summary_parts: list[str],
    ) -> None:
        for slog in self._pipeline.stages_log:
            if slog.stage == PipelineStage.DELIVERING.value:
                final_output.update(slog.output)
                summary_parts.append(slog.summary)
            elif slog.stage in (
                PipelineStage.COLLECTING_CANDIDATES.value,
                PipelineStage.SCORING_CANDIDATES.value,
                PipelineStage.SHORTLISTING.value,
                PipelineStage.HANDOFF_PLANNING.value,
            ):
                final_output.update(slog.output)

    def _build_metrics(
        self,
        stages_completed: int,
        stages_failed: int,
        final_output: dict[str, Any],
        duration: float,
    ) -> ProductResearchMetrics:
        shortlisted = final_output.get("shortlisted", [])
        top = shortlisted[0] if shortlisted else {}
        return ProductResearchMetrics(
            total_stages=stages_completed + stages_failed,
            completed_stages=stages_completed,
            failed_stages=stages_failed,
            candidates_analyzed=final_output.get("total_candidates", final_output.get("candidates_analyzed", 0)),
            shortlisted_count=len(shortlisted),
            rejected_count=final_output.get("rejected_count", 0),
            average_score=final_output.get("average_score", 0.0),
            top_score=top.get("score_total", 0.0) if isinstance(top, dict) else 0.0,
            top_marketplace=top.get("marketplace", "") if isinstance(top, dict) else "",
            top_niche=top.get("niche", "") if isinstance(top, dict) else "",
            quality_passed=final_output.get("quality_passed", True),
            quality_corrections=tuple(final_output.get("quality_issues", [])),
            duration_minutes=round(duration, 2),
        )

    def _build_summary(self, success: bool, summary_parts: list[str]) -> str:
        if summary_parts:
            return " | ".join(summary_parts)
        return "Product research completed" if success else "Product research failed"

    def analyze_capability_needs(self) -> tuple[Capability, ...]:
        return (
            Capability.WEB_SEARCH,
            Capability.BROWSER_AUTOMATION,
            Capability.TEXT_GENERATION,
            Capability.IMAGE_EDITING,
            Capability.STORAGE,
        )

    def state(self) -> dict[str, Any]:
        base = super().state()
        base["product_research_capabilities"] = {
            k: {"name": v.name, "proficiency": v.proficiency, "enabled": v.enabled}
            for k, v in self._product_research_capabilities.items()
        }
        brief = self._current_product_research_brief
        base["current_product_research_brief"] = (
            {
                "title": brief.title,
                "target_market": brief.target_market,
                "candidates": len(brief.candidates),
                "shortlist_size": brief.shortlist_size,
            }
            if brief is not None else None
        )
        metrics = base["production_metrics"]
        metrics["candidates_analyzed"] = getattr(self._production_metrics, "candidates_analyzed", 0)
        metrics["shortlisted_count"] = getattr(self._production_metrics, "shortlisted_count", 0)
        metrics["top_score"] = getattr(self._production_metrics, "top_score", 0.0)
        metrics["top_marketplace"] = getattr(self._production_metrics, "top_marketplace", "")
        metrics["top_niche"] = getattr(self._production_metrics, "top_niche", "")
        return base


def _is_product_research_department(department: str) -> bool:
    lowered = department.lower()
    markers = ("product_research", "product research", "research", "discovery", "produto", "mercado")
    return any(marker in lowered for marker in markers)


def _coerce_brief(task: ReceivedTask) -> ProductResearchBrief:
    ctx = task.context
    return ProductResearchBrief(
        task_id=task.task_id,
        title=task.title,
        objective=ctx.get("objective", "Find winning product candidates for affiliate content."),
        target_market=ctx.get("target_market", "BR"),
        niches=tuple(ctx.get("niches", ())),
        source_platforms=tuple(ctx.get("source_platforms", ())),
        candidates=_coerce_candidates(ctx.get("candidates", ())),
        shortlist_size=int(ctx.get("shortlist_size", 5) or 5),
        require_affiliate_url=bool(ctx.get("require_affiliate_url", False)),
        metadata=dict(ctx.get("metadata", {})),
    )


def _coerce_candidates(raw: Any) -> tuple[ProductCandidate, ...]:
    items = _as_iterable(raw)
    return tuple(
        item if isinstance(item, ProductCandidate) else _coerce_candidate(item)
        for item in items
        if isinstance(item, (ProductCandidate, dict))
    )


def _coerce_candidate(data: dict[str, Any]) -> ProductCandidate:
    return ProductCandidate(
        product_name=data.get("product_name", data.get("name", "")),
        marketplace=data.get("marketplace", data.get("source", "")),
        category=data.get("category", ""),
        niche=data.get("niche", ""),
        source_url=data.get("source_url", data.get("url", "")),
        affiliate_url=data.get("affiliate_url", ""),
        image_url=data.get("image_url", ""),
        current_price=float(data.get("current_price", data.get("price", 0.0)) or 0.0),
        old_price=_optional_float(data.get("old_price")),
        commission_percent=float(data.get("commission_percent", 0.0) or 0.0),
        marketplace_trust=float(data.get("marketplace_trust", _trust_for(data.get("marketplace", ""))) or 0.65),
        demand_signals=_coerce_signals(data.get("demand_signals", ())),
        creative_signals=_coerce_signals(data.get("creative_signals", ())),
        competition_level=data.get("competition_level", "medium"),
        saturation_level=data.get("saturation_level", "medium"),
        risk_flags=tuple(data.get("risk_flags", ())),
        notes=tuple(data.get("notes", ())),
        metadata=dict(data.get("metadata", {})),
    )


def _coerce_signals(raw: Any) -> tuple[MarketplaceSignal, ...]:
    return tuple(
        item if isinstance(item, MarketplaceSignal) else MarketplaceSignal(
            name=item.get("name", ""),
            value=float(item.get("value", 0.0) or 0.0),
            weight=float(item.get("weight", 1.0) or 1.0),
            source=item.get("source", ""),
            note=item.get("note", ""),
            metadata=dict(item.get("metadata", {})),
        )
        for item in _as_iterable(raw)
        if isinstance(item, (MarketplaceSignal, dict))
    )


def _trust_for(marketplace: str) -> float:
    return {
        "amazon": 0.92,
        "mercado_livre": 0.86,
        "mercado livre": 0.86,
        "hotmart": 0.78,
        "kiwify": 0.74,
        "tiktok_shop": 0.72,
        "kwai": 0.62,
    }.get(str(marketplace).lower(), 0.65)


def _optional_float(value: Any) -> float | None:
    if value is None or value == "":
        return None
    return float(value)


def _as_iterable(raw: Any) -> tuple[Any, ...]:
    if raw is None:
        return ()
    if isinstance(raw, tuple):
        return raw
    if isinstance(raw, list):
        return tuple(raw)
    return (raw,)
