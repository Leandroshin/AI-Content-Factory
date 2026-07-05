"""Deterministic product research pipeline."""

from __future__ import annotations

from enum import StrEnum

from core.departments.base.pipeline import ProductionPipeline, StageResult
from core.departments.product_research.models import (
    ProductCandidate,
    ProductResearchBrief,
    ProductResearchFinding,
    ProductResearchReport,
)


class PipelineStage(StrEnum):
    """Stages of the product research pipeline."""

    CREATED = "created"
    ANALYZING_BRIEF = "analyzing_brief"
    COLLECTING_CANDIDATES = "collecting_candidates"
    ENRICHING_SIGNALS = "enriching_signals"
    SCORING_CANDIDATES = "scoring_candidates"
    SHORTLISTING = "shortlisting"
    HANDOFF_PLANNING = "handoff_planning"
    DELIVERING = "delivering"
    COMPLETED = "completed"
    FAILED = "failed"


class ProductResearchPipeline(ProductionPipeline):
    """Rule-based state machine for product discovery and shortlisting."""

    def __init__(self, brief: ProductResearchBrief) -> None:
        super().__init__()
        self._brief = brief
        self._stage: str = PipelineStage.CREATED.value
        self._candidates: tuple[ProductCandidate, ...] = ()
        self._findings: tuple[ProductResearchFinding, ...] = ()
        self._shortlisted: tuple[ProductResearchFinding, ...] = ()
        self._next_actions: tuple[str, ...] = ()
        self._report: ProductResearchReport | None = None

    @property
    def stage(self) -> str:
        return self._stage

    @property
    def progress(self) -> float:
        stages = list(PipelineStage)
        try:
            idx = stages.index(PipelineStage(self._stage))
            return round((idx / (len(stages) - 1)) * 100.0, 1)
        except (ValueError, KeyError):
            return 0.0

    def advance(self) -> StageResult:
        handlers = {
            PipelineStage.CREATED: self._stage_created,
            PipelineStage.ANALYZING_BRIEF: self._stage_analyzing_brief,
            PipelineStage.COLLECTING_CANDIDATES: self._stage_collecting_candidates,
            PipelineStage.ENRICHING_SIGNALS: self._stage_enriching_signals,
            PipelineStage.SCORING_CANDIDATES: self._stage_scoring_candidates,
            PipelineStage.SHORTLISTING: self._stage_shortlisting,
            PipelineStage.HANDOFF_PLANNING: self._stage_handoff_planning,
            PipelineStage.DELIVERING: self._stage_delivering,
        }

        try:
            current = PipelineStage(self._stage)
        except (ValueError, KeyError):
            result = StageResult(stage=self._stage, success=False, error=f"Unknown stage: {self._stage}")
            self._stages_log.append(result)
            self._stage = PipelineStage.FAILED.value
            return result

        handler = handlers.get(current)
        if handler is None:
            result = StageResult(stage=self._stage, success=False, error=f"No handler for: {self._stage}")
            self._stages_log.append(result)
            self._stage = PipelineStage.FAILED.value
            return result

        result = handler()
        self._stages_log.append(result)
        if result.next_stage:
            self._stage = result.next_stage
        elif result.success:
            self._stage = self._next_stage(current).value
        else:
            self._stage = PipelineStage.FAILED.value
        return result

    def reset(self) -> None:
        super().reset()
        self._stage = PipelineStage.CREATED.value
        self._candidates = ()
        self._findings = ()
        self._shortlisted = ()
        self._next_actions = ()
        self._report = None

    def _stage_created(self) -> StageResult:
        return StageResult(
            stage=PipelineStage.CREATED.value,
            success=True,
            summary=f"Product research task '{self._brief.title}' created",
            output={
                "task_id": str(self._brief.task_id),
                "target_market": self._brief.target_market,
                "shortlist_size": self._brief.shortlist_size,
            },
            next_stage=PipelineStage.ANALYZING_BRIEF.value,
        )

    def _stage_analyzing_brief(self) -> StageResult:
        if self._brief.shortlist_size <= 0:
            return StageResult(
                stage=PipelineStage.ANALYZING_BRIEF.value,
                success=False,
                error="shortlist_size must be greater than zero.",
            )
        if not self._brief.objective:
            return StageResult(
                stage=PipelineStage.ANALYZING_BRIEF.value,
                success=False,
                error="Research objective is required.",
            )
        return StageResult(
            stage=PipelineStage.ANALYZING_BRIEF.value,
            success=True,
            summary=f"Brief analyzed for {self._brief.target_market}",
            output={
                "objective": self._brief.objective,
                "niches": list(self._brief.niches),
                "source_platforms": list(self._brief.source_platforms),
            },
            next_stage=PipelineStage.COLLECTING_CANDIDATES.value,
        )

    def _stage_collecting_candidates(self) -> StageResult:
        candidates = tuple(c for c in self._brief.candidates if c.product_name and c.source_url)
        if not candidates:
            return StageResult(
                stage=PipelineStage.COLLECTING_CANDIDATES.value,
                success=False,
                error="At least one candidate with product_name and source_url is required.",
            )
        self._candidates = candidates
        return StageResult(
            stage=PipelineStage.COLLECTING_CANDIDATES.value,
            success=True,
            summary=f"Collected {len(candidates)} candidate(s)",
            output={
                "candidates_collected": len(candidates),
                "marketplaces": list(dict.fromkeys(c.marketplace for c in candidates)),
                "niches": list(dict.fromkeys(c.niche for c in candidates if c.niche)),
            },
            next_stage=PipelineStage.ENRICHING_SIGNALS.value,
        )

    def _stage_enriching_signals(self) -> StageResult:
        missing_affiliate = sum(1 for c in self._candidates if not c.has_affiliate_target)
        with_images = sum(1 for c in self._candidates if c.image_url)
        with_demand = sum(1 for c in self._candidates if c.demand_signals)
        return StageResult(
            stage=PipelineStage.ENRICHING_SIGNALS.value,
            success=True,
            summary=f"Signals enriched: {with_demand} candidate(s) with demand evidence",
            output={
                "with_demand_signals": with_demand,
                "with_images": with_images,
                "missing_affiliate_urls": missing_affiliate,
                "requires_affiliate_url": self._brief.require_affiliate_url,
            },
            next_stage=PipelineStage.SCORING_CANDIDATES.value,
        )

    def _stage_scoring_candidates(self) -> StageResult:
        self._findings = tuple(_score_candidate(c, self._brief.require_affiliate_url) for c in self._candidates)
        avg = round(sum(f.score_total for f in self._findings) / len(self._findings), 2)
        return StageResult(
            stage=PipelineStage.SCORING_CANDIDATES.value,
            success=True,
            summary=f"Scored {len(self._findings)} candidate(s)",
            output={
                "candidates_analyzed": len(self._findings),
                "average_score": avg,
                "top_score": max(f.score_total for f in self._findings),
            },
            next_stage=PipelineStage.SHORTLISTING.value,
        )

    def _stage_shortlisting(self) -> StageResult:
        viable = [f for f in self._findings if f.recommendation != "skip"]
        viable.sort(key=lambda f: f.score_total, reverse=True)
        self._shortlisted = tuple(viable[: self._brief.shortlist_size])
        rejected = sum(1 for f in self._findings if f.recommendation == "skip")
        return StageResult(
            stage=PipelineStage.SHORTLISTING.value,
            success=True,
            summary=f"Shortlisted {len(self._shortlisted)} candidate(s)",
            output={
                "shortlisted_count": len(self._shortlisted),
                "rejected_count": rejected,
                "shortlisted": [f.to_public_dict() for f in self._shortlisted],
            },
            next_stage=PipelineStage.HANDOFF_PLANNING.value,
        )

    def _stage_handoff_planning(self) -> StageResult:
        actions = []
        if self._shortlisted:
            actions.append("Send shortlisted products to AffiliateDealsEmployee for offer scoring and copy.")
            actions.append("Check affiliate URL/tracking ID for every shortlisted product before publishing.")
            actions.append("Review image quality before creative production.")
        if any(not f.candidate.has_affiliate_target for f in self._shortlisted):
            actions.append("Owner must create affiliate links for shortlisted products missing affiliate_url.")
        if any(f.candidate.risk_flags for f in self._shortlisted):
            actions.append("Run compliance review before creative generation for flagged products.")
        self._next_actions = tuple(actions)
        return StageResult(
            stage=PipelineStage.HANDOFF_PLANNING.value,
            success=True,
            summary=f"Handoff planned with {len(actions)} action(s)",
            output={
                "next_actions": list(self._next_actions),
                "handoff_target": "affiliate_deals",
            },
            next_stage=PipelineStage.DELIVERING.value,
        )

    def _stage_delivering(self) -> StageResult:
        rejected = sum(1 for f in self._findings if f.recommendation == "skip")
        needs_review = sum(1 for f in self._findings if f.recommendation == "needs_review")
        self._report = ProductResearchReport(
            brief_title=self._brief.title,
            total_candidates=len(self._findings),
            shortlisted=self._shortlisted,
            findings=tuple(sorted(self._findings, key=lambda f: f.score_total, reverse=True)),
            rejected_count=rejected,
            needs_review_count=needs_review,
            next_actions=self._next_actions,
            metadata={
                "target_market": self._brief.target_market,
                "source_platforms": list(self._brief.source_platforms),
            },
        )
        output = self._report.to_public_dict()
        return StageResult(
            stage=PipelineStage.DELIVERING.value,
            success=True,
            summary=f"Delivered product research report: {len(self._shortlisted)} shortlisted",
            output=output,
            next_stage=PipelineStage.COMPLETED.value,
        )

    @staticmethod
    def _next_stage(current: PipelineStage) -> PipelineStage:
        stages = list(PipelineStage)
        idx = stages.index(current)
        if idx + 1 < len(stages):
            return stages[idx + 1]
        return PipelineStage.COMPLETED


def _score_candidate(candidate: ProductCandidate, require_affiliate_url: bool) -> ProductResearchFinding:
    reasons: list[str] = []
    demand_score = _signal_score(candidate.demand_signals, default=8.0, cap=25.0)
    if demand_score >= 18:
        reasons.append("strong_demand_signals")
    elif demand_score >= 10:
        reasons.append("some_demand_signals")
    else:
        reasons.append("weak_demand_evidence")

    margin_score = _margin_score(candidate)
    if margin_score >= 16:
        reasons.append("good_margin_or_commission")

    creative_score = _signal_score(candidate.creative_signals, default=8.0 if candidate.image_url else 3.0, cap=18.0)
    if candidate.image_url:
        reasons.append("image_available")
    if creative_score >= 13:
        reasons.append("creative_angle_available")

    competition_score = _competition_score(candidate.competition_level, candidate.saturation_level)
    trust_score = round(max(0.0, min(1.0, candidate.marketplace_trust)) * 15.0, 2)

    risk_penalty = min(35.0, len(candidate.risk_flags) * 10.0)
    if candidate.risk_flags:
        reasons.append("risk_flags_present")
    if not candidate.has_affiliate_target:
        reasons.append("affiliate_url_missing")
        if require_affiliate_url:
            risk_penalty += 18.0

    total = round(
        max(0.0, demand_score + margin_score + creative_score + competition_score + trust_score - risk_penalty),
        2,
    )

    if risk_penalty >= 25.0 or total < 38.0:
        recommendation = "skip"
    elif total >= 68.0:
        recommendation = "shortlist"
    else:
        recommendation = "needs_review"

    return ProductResearchFinding(
        candidate=candidate,
        score_total=total,
        demand_score=demand_score,
        margin_score=margin_score,
        creative_score=creative_score,
        competition_score=competition_score,
        trust_score=trust_score,
        risk_penalty=round(risk_penalty, 2),
        recommendation=recommendation,
        reasons=tuple(dict.fromkeys(reasons)),
    )


def _signal_score(signals: tuple, *, default: float, cap: float) -> float:
    if not signals:
        return default
    raw = sum(signal.weighted_value for signal in signals)
    return round(min(cap, raw), 2)


def _margin_score(candidate: ProductCandidate) -> float:
    price_score = 0.0
    if 40 <= candidate.current_price <= 350:
        price_score = 8.0
    elif 350 < candidate.current_price <= 900:
        price_score = 6.0
    elif 0 < candidate.current_price < 40:
        price_score = 4.0
    commission_score = min(10.0, max(0.0, candidate.commission_percent) * 0.8)
    discount_score = min(6.0, candidate.discount_percent * 0.18)
    return round(price_score + commission_score + discount_score, 2)


def _competition_score(competition: str, saturation: str) -> float:
    base = {
        "low": 14.0,
        "medium": 10.0,
        "high": 5.0,
    }.get(competition.lower(), 8.0)
    penalty = {
        "low": 0.0,
        "medium": 2.0,
        "high": 5.0,
    }.get(saturation.lower(), 2.0)
    return round(max(0.0, base - penalty), 2)
