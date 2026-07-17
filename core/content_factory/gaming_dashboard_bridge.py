"""Controlled bridge from Gaming News Desk reviews to the hosted dashboard."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC
from typing import Any

from core.content_factory.audience_growth import GrowthDecision, GrowthDecisionStatus
from core.content_factory.gaming_news_desk import GamingNewsDeskResult
from core.tools.http.client import HttpClient
from core.tools.http.errors import HttpError


@dataclass(frozen=True, slots=True)
class DashboardSubmission:
    """Auditable outcome for one dashboard intake attempt."""

    candidate_id: str
    accepted: bool
    status_code: int = 0
    error: str = ""


@dataclass(frozen=True, slots=True)
class GamingDashboardBridgeResult:
    """Summary that never exposes the bearer token or response body."""

    skipped_reason: str = ""
    eligible: int = 0
    accepted: int = 0
    failed: int = 0
    submissions: tuple[DashboardSubmission, ...] = field(default_factory=tuple)


class GamingDashboardBridge:
    """Send review-only gaming opportunities to the dashboard intake."""

    def __init__(self, client: HttpClient, endpoint: str) -> None:
        endpoint = endpoint.strip()
        if not endpoint.startswith("https://") or not endpoint.endswith("/api/intake/gaming"):
            raise ValueError("Gaming dashboard endpoint must be the public HTTPS intake route.")
        self._client = client
        self._endpoint = endpoint

    def publish(
        self,
        desk_result: GamingNewsDeskResult,
        *,
        token: str,
        enabled: bool = False,
        channel: str = "Fase Nova Games",
    ) -> GamingDashboardBridgeResult:
        """Publish only REVIEW decisions; this never starts content production."""
        if not enabled:
            return GamingDashboardBridgeResult(skipped_reason="bridge_disabled")
        if desk_result.no_news:
            return GamingDashboardBridgeResult(skipped_reason="no_news")
        if not token.strip():
            return GamingDashboardBridgeResult(skipped_reason="missing_token")

        decisions = tuple(
            decision
            for decision in desk_result.growth_plan.decisions
            if decision.status is GrowthDecisionStatus.REVIEW
        )
        if not decisions:
            return GamingDashboardBridgeResult(skipped_reason="no_review_items")

        submissions = tuple(
            self._submit(decision, token=token, channel=channel)
            for decision in decisions
        )
        return GamingDashboardBridgeResult(
            eligible=len(decisions),
            accepted=sum(item.accepted for item in submissions),
            failed=sum(not item.accepted for item in submissions),
            submissions=submissions,
        )

    def _submit(self, decision: GrowthDecision, *, token: str, channel: str) -> DashboardSubmission:
        candidate = decision.candidate
        payload = self._payload(decision, channel=channel)
        try:
            response = self._client.post(
                self._endpoint,
                headers={
                    "Authorization": f"Bearer {token}",
                    "Content-Type": "application/json",
                },
                body=payload,
            )
        except HttpError as exc:
            return DashboardSubmission(
                candidate_id=candidate.candidate_id,
                accepted=False,
                error=type(exc).__name__,
            )
        accepted = response.status_code == 202
        return DashboardSubmission(
            candidate_id=candidate.candidate_id,
            accepted=accepted,
            status_code=response.status_code,
            error="" if accepted else f"HTTP {response.status_code}",
        )

    @staticmethod
    def _payload(decision: GrowthDecision, *, channel: str) -> dict[str, Any]:
        candidate = decision.candidate
        evidence = candidate.evidence[:8]
        confidence = round(
            (sum(item.confidence for item in evidence) / len(evidence)) * 100
        ) if evidence else 0
        updated_at = max(item.observed_at for item in evidence).astimezone(UTC).isoformat()
        risks = ", ".join(candidate.risks) if candidate.risks else "Baixo: pauta passa por revisao humana e checagem das fontes."
        key_points = " ".join(candidate.key_points)
        summary = key_points[:600] or candidate.hook[:600]
        return {
            "id": candidate.candidate_id,
            "title": candidate.topic[:180],
            "source": str(candidate.metadata.get("source_name", "Gaming News Desk"))[:80],
            "channel": channel[:80],
            "category": "Noticia",
            "summary": summary,
            "priority": "high" if decision.score.total >= 80 else "medium",
            "score": round(decision.score.total),
            "confidence": max(0, min(100, confidence)),
            "risk": risks[:500],
            "nextAction": "Conferir as fontes e aprovar ou rejeitar a pauta.",
            "updatedAt": updated_at,
            "sources": [
                {
                    "label": item.title[:160],
                    "url": item.source_url,
                    "sourceType": GamingDashboardBridge._source_type(item.source_type),
                    "publishedAt": item.observed_at.astimezone(UTC).isoformat(),
                }
                for item in evidence
            ],
        }

    @staticmethod
    def _source_type(value: str) -> str:
        normalized = value.casefold()
        if "official" in normalized or "publisher" in normalized:
            return "official"
        if "market" in normalized or "store" in normalized:
            return "marketplace"
        if "report" in normalized or "press" in normalized or "news" in normalized:
            return "reporting"
        return "signal"
