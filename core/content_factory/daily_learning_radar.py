"""Daily source discovery and controlled employee learning workflow."""

from __future__ import annotations

import hashlib
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any


@dataclass(frozen=True, slots=True)
class LearningCandidate:
    """One video observed by an approved collector."""

    title: str
    source_url: str
    creator: str = ""
    transcript_text: str = ""
    screenshot_evidence: str = ""
    observed_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    relevance: float = 0.0
    novelty: float = 0.0
    credibility: float = 0.0
    actionability: float = 0.0
    promotional_risk: float = 0.0
    compliance_risk: float = 0.0
    tags: tuple[str, ...] = field(default_factory=tuple)
    metadata: dict[str, Any] = field(default_factory=dict)

    @property
    def fingerprint(self) -> str:
        value = f"{self.source_url}|{self.title}".casefold().strip()
        return hashlib.sha256(value.encode("utf-8")).hexdigest()


@dataclass(frozen=True, slots=True)
class LearningExperiment:
    """A reversible test proposal; it is not organizational knowledge yet."""

    experiment_id: str
    candidate_fingerprint: str
    title: str
    hypothesis: str
    steps: tuple[str, ...]
    success_metrics: tuple[str, ...]
    required_providers: tuple[str, ...]
    guardrails: tuple[str, ...]
    owner_approval_required: bool = True
    estimated_cost_usd: float = 0.0


@dataclass(frozen=True, slots=True)
class LearningDecision:
    """Auditable result for one candidate."""

    fingerprint: str
    status: str
    score: float
    reasons: tuple[str, ...]
    experiment: LearningExperiment | None = None


@dataclass(frozen=True, slots=True)
class DailyLearningReport:
    """Daily result with no automatic promotion or provider spending."""

    run_at: datetime
    decisions: tuple[LearningDecision, ...]
    selected_count: int
    rejected_count: int
    duplicate_count: int
    no_learning: bool
    next_seen_fingerprints: tuple[str, ...]


class DailyLearningRadar:
    """Triage videos into safe, owner-approved experiments.

    Collection is deliberately outside this class. A browser worker or the owner
    supplies candidates, which keeps personalized browsing and screenshots under
    explicit control. This class never publishes, buys API credits, or promotes
    raw transcripts into employee instructions.
    """

    _CLAIM_TERMS = (
        "faturar",
        "sete digitos",
        "ganhar dinheiro",
        "alta conversao",
        "resultado garantido",
        "perder 9 kg",
        "perder 10 kg",
        "ozempic",
    )
    _COPY_TERMS = ("baixar o criativo", "copiar o criativo", "mesma pessoa", "clonar")

    def __init__(self, *, minimum_score: float = 0.62, max_selected: int = 3) -> None:
        self._minimum_score = max(0.0, min(1.0, minimum_score))
        self._max_selected = max(1, max_selected)

    def run(
        self,
        candidates: tuple[LearningCandidate, ...],
        *,
        seen_fingerprints: tuple[str, ...] = (),
        now: datetime | None = None,
    ) -> DailyLearningReport:
        seen = set(seen_fingerprints)
        decisions: list[LearningDecision] = []
        eligible: list[tuple[float, LearningCandidate, tuple[str, ...]]] = []
        duplicates = 0

        for candidate in candidates:
            if candidate.fingerprint in seen:
                duplicates += 1
                decisions.append(
                    LearningDecision(candidate.fingerprint, "duplicate", 0.0, ("Source was already evaluated.",))
                )
                continue
            seen.add(candidate.fingerprint)
            reasons = self._validation_reasons(candidate)
            score = self._score(candidate)
            if reasons or score < self._minimum_score:
                if score < self._minimum_score:
                    reasons = (*reasons, "Learning value is below the daily threshold.")
                decisions.append(LearningDecision(candidate.fingerprint, "rejected", score, reasons))
                continue
            eligible.append((score, candidate, self._risk_notes(candidate)))

        selected_ids: set[str] = set()
        for score, candidate, risk_notes in sorted(eligible, key=lambda item: item[0], reverse=True)[: self._max_selected]:
            selected_ids.add(candidate.fingerprint)
            decisions.append(
                LearningDecision(
                    candidate.fingerprint,
                    "experiment_proposed",
                    score,
                    ("Candidate has enough evidence for a bounded experiment.", *risk_notes),
                    self._build_experiment(candidate),
                )
            )
        for score, candidate, _ in eligible:
            if candidate.fingerprint not in selected_ids:
                decisions.append(
                    LearningDecision(candidate.fingerprint, "deferred", score, ("Daily experiment capacity reached.",))
                )

        selected = sum(item.status == "experiment_proposed" for item in decisions)
        rejected = sum(item.status == "rejected" for item in decisions)
        return DailyLearningReport(
            run_at=now or datetime.now(UTC),
            decisions=tuple(decisions),
            selected_count=selected,
            rejected_count=rejected,
            duplicate_count=duplicates,
            no_learning=selected == 0,
            next_seen_fingerprints=tuple(dict.fromkeys((*seen_fingerprints, *(item.fingerprint for item in candidates)))),
        )

    def _validation_reasons(self, candidate: LearningCandidate) -> tuple[str, ...]:
        reasons: list[str] = []
        if not candidate.source_url.startswith("https://"):
            reasons.append("Source URL must use HTTPS.")
        if not candidate.transcript_text.strip():
            reasons.append("Transcript is required before evaluation.")
        if not candidate.screenshot_evidence.strip():
            reasons.append("Visual evidence is required before evaluation.")
        if not candidate.title.strip():
            reasons.append("Title is required.")
        return tuple(reasons)

    @staticmethod
    def _score(candidate: LearningCandidate) -> float:
        positive = (
            candidate.relevance * 0.28
            + candidate.novelty * 0.18
            + candidate.credibility * 0.20
            + candidate.actionability * 0.34
        )
        risk = candidate.promotional_risk * 0.12 + candidate.compliance_risk * 0.22
        return round(max(0.0, min(1.0, positive - risk)), 4)

    def _risk_notes(self, candidate: LearningCandidate) -> tuple[str, ...]:
        text = candidate.transcript_text.casefold()
        notes: list[str] = []
        if any(term in text for term in self._CLAIM_TERMS):
            notes.append("Treat revenue, health, and conversion claims as unverified marketing claims.")
        if any(term in text for term in self._COPY_TERMS):
            notes.append("Extract structure only; do not copy a creator, likeness, script, or source creative.")
        return tuple(notes)

    def _build_experiment(self, candidate: LearningCandidate) -> LearningExperiment:
        transcript = candidate.transcript_text.casefold()
        is_ugc = any(term in transcript for term in ("ugc", "avatar", "sora", "nano banana", "kie"))
        if is_ugc:
            hypothesis = "An original UGC-style avatar and scene can improve perceived naturalness without copying a real person."
            steps = (
                "Extract the reference's abstract hook, scene, pacing, and proof structure.",
                "Create an original fictional adult persona, script, setting, and disclosure-safe offer.",
                "Generate one low-cost draft with provider budget approval and provenance metadata.",
                "Run Creative Review for likeness, claim, copyright, disclosure, and visual quality risks.",
                "Compare the draft against the current baseline before any publication.",
            )
            metrics = ("hook_retention_3s", "watch_time", "creative_review_score", "cost_per_approved_variant")
            providers = tuple(name for name in ("image_provider", "video_provider") if name)
        else:
            hypothesis = "The extracted pattern can improve an existing workflow when tested independently."
            steps = (
                "Extract the abstract pattern and supporting evidence.",
                "Build a reversible mock or offline test.",
                "Compare against the current baseline.",
                "Request owner approval before changing production behavior.",
            )
            metrics = ("quality_score", "time_saved", "estimated_cost_usd")
            providers = ()
        guardrails = (
            "No raw transcript becomes an employee instruction.",
            "No third-party likeness, voice, script, or creative is copied.",
            "No health, revenue, or performance claim is published without substantiation.",
            "No provider spend or publication occurs without owner approval.",
            "Only a measured successful experiment may be proposed for knowledge promotion.",
        )
        return LearningExperiment(
            experiment_id=f"learn-{candidate.fingerprint[:16]}",
            candidate_fingerprint=candidate.fingerprint,
            title=f"Test learned pattern: {candidate.title}",
            hypothesis=hypothesis,
            steps=steps,
            success_metrics=metrics,
            required_providers=providers,
            guardrails=guardrails,
        )
