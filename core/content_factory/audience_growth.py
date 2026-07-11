"""Evidence-first planning for short-form audience growth campaigns."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import StrEnum
from typing import Any

from core.content_factory.models import ContentBrief


class GrowthDecisionStatus(StrEnum):
    """Owner-facing state for a trend candidate."""

    BLOCKED = "blocked"
    REVIEW = "review"
    APPROVED = "approved"


@dataclass(frozen=True, slots=True)
class TrendEvidence:
    """Traceable evidence supporting a content opportunity."""

    title: str
    source_url: str
    source_type: str
    observed_at: datetime
    confidence: float = 0.5


@dataclass(frozen=True, slots=True)
class GrowthCandidate:
    """One topic proposed by Strategy Intelligence for owner review."""

    candidate_id: str
    topic: str
    hook: str
    angle: str
    pillar: str
    key_points: tuple[str, ...]
    evidence: tuple[TrendEvidence, ...]
    visual_plan: tuple[str, ...] = field(default_factory=tuple)
    risks: tuple[str, ...] = field(default_factory=tuple)
    series_potential: bool = False
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class GrowthScore:
    """Auditable score used to order candidates, never to auto-publish."""

    total: float
    evidence: float
    freshness: float
    visual: float
    series: float
    alignment: float
    penalty: float


@dataclass(frozen=True, slots=True)
class GrowthDecision:
    """Candidate plus score and explicit approval state."""

    candidate: GrowthCandidate
    score: GrowthScore
    status: GrowthDecisionStatus
    reasons: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class AudienceGrowthPlan:
    """Shortlist and briefs approved for the existing production workflow."""

    decisions: tuple[GrowthDecision, ...]
    approved_briefs: tuple[ContentBrief, ...]
    cadence_per_week: int
    manual_publish: bool = True


class AudienceGrowthPlanner:
    """Connect trend evidence to ContentBrief without bypassing owner review."""

    _BLOCKING_RISKS = frozenset(
        {"copyright_reupload", "income_guarantee", "unsafe_product", "unverified_claim"}
    )

    def __init__(
        self,
        *,
        allowed_pillars: tuple[str, ...] = (
            "gaming",
            "technology_ai",
            "smart_shopping",
            "build_in_public",
        ),
        max_candidates: int = 10,
        cadence_per_week: int = 5,
    ) -> None:
        self._allowed_pillars = frozenset(allowed_pillars)
        self._max_candidates = max(1, max_candidates)
        self._cadence_per_week = max(1, cadence_per_week)

    def build_plan(
        self,
        candidates: tuple[GrowthCandidate, ...],
        *,
        approved_ids: tuple[str, ...] = (),
        now: datetime | None = None,
    ) -> AudienceGrowthPlan:
        """Score candidates and create briefs only for owner-approved IDs."""
        reference_time = now or datetime.now(UTC)
        approved = frozenset(approved_ids)
        decisions = [self._decide(item, approved, reference_time) for item in candidates]
        decisions.sort(key=lambda item: (-item.score.total, item.candidate.candidate_id))
        shortlisted = tuple(decisions[: self._max_candidates])
        briefs = tuple(
            self._to_brief(decision.candidate, decision.score)
            for decision in shortlisted
            if decision.status is GrowthDecisionStatus.APPROVED
        )
        return AudienceGrowthPlan(
            decisions=shortlisted,
            approved_briefs=briefs,
            cadence_per_week=self._cadence_per_week,
        )

    def _decide(
        self,
        candidate: GrowthCandidate,
        approved_ids: frozenset[str],
        now: datetime,
    ) -> GrowthDecision:
        score = self._score(candidate, now)
        blocking = sorted(self._BLOCKING_RISKS.intersection(candidate.risks))
        reasons: list[str] = []

        if not candidate.evidence:
            blocking.append("missing_evidence")
        if candidate.pillar not in self._allowed_pillars:
            blocking.append("off_strategy_pillar")

        if blocking:
            status = GrowthDecisionStatus.BLOCKED
            reasons.extend(f"blocked:{risk}" for risk in sorted(set(blocking)))
        elif candidate.candidate_id in approved_ids:
            status = GrowthDecisionStatus.APPROVED
            reasons.append("owner_approved")
        else:
            status = GrowthDecisionStatus.REVIEW
            reasons.append("awaiting_owner_review")

        reasons.append(f"score:{score.total:.1f}")
        return GrowthDecision(candidate=candidate, score=score, status=status, reasons=tuple(reasons))

    def _score(self, candidate: GrowthCandidate, now: datetime) -> GrowthScore:
        confidences = [max(0.0, min(1.0, item.confidence)) for item in candidate.evidence]
        evidence_score = (sum(confidences) / len(confidences) * 30.0) if confidences else 0.0

        ages = [max(0.0, (now - item.observed_at).total_seconds() / 3600.0) for item in candidate.evidence]
        freshest = min(ages) if ages else float("inf")
        freshness_score = 20.0 if freshest <= 24 else 15.0 if freshest <= 72 else 10.0 if freshest <= 168 else 4.0
        visual_score = min(15.0, len(candidate.visual_plan) * 5.0)
        series_score = 15.0 if candidate.series_potential else 7.0
        alignment_score = 20.0 if candidate.pillar in self._allowed_pillars else 0.0
        penalty = min(40.0, len(candidate.risks) * 8.0)
        total = max(
            0.0,
            min(100.0, evidence_score + freshness_score + visual_score + series_score + alignment_score - penalty),
        )
        return GrowthScore(
            total=round(total, 2),
            evidence=round(evidence_score, 2),
            freshness=freshness_score,
            visual=visual_score,
            series=series_score,
            alignment=alignment_score,
            penalty=penalty,
        )

    def _to_brief(self, candidate: GrowthCandidate, score: GrowthScore) -> ContentBrief:
        return ContentBrief(
            topic=candidate.topic,
            objective=f"Grow the Achados Baratos BR audience with a sourced {candidate.pillar} short.",
            target_audience="Brazilian viewers interested in games, technology and smart shopping",
            platform="tiktok",
            language="pt-BR",
            tone="curious, direct and credible",
            duration_seconds=45,
            video_type="shorts",
            key_points=candidate.key_points,
            call_to_action="Qual desses assuntos voce quer ver no proximo video?",
            metadata={
                "candidate_id": candidate.candidate_id,
                "hook": candidate.hook,
                "angle": candidate.angle,
                "pillar": candidate.pillar,
                "growth_score": score.total,
                "source_urls": tuple(item.source_url for item in candidate.evidence),
                "visual_plan": candidate.visual_plan,
                "manual_publish": True,
                "requires_final_policy_review": True,
                **candidate.metadata,
            },
        )
