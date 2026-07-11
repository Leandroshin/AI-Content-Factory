"""Daily gaming-news desk connected to the audience growth planner."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from core.content_factory.audience_growth import (
    AudienceGrowthPlan,
    AudienceGrowthPlanner,
    GrowthCandidate,
    TrendEvidence,
)


@dataclass(frozen=True, slots=True)
class GamingNewsSource:
    """Source metadata used to decide whether a claim can become a brief."""

    name: str
    url: str
    source_type: str
    authority: float
    primary: bool = False


@dataclass(frozen=True, slots=True)
class GamingNewsItem:
    """Normalized news item collected by official adapters or web research."""

    title: str
    url: str
    published_at: datetime
    source: GamingNewsSource
    summary: str = ""
    game: str = ""
    tags: tuple[str, ...] = field(default_factory=tuple)
    key_points: tuple[str, ...] = field(default_factory=tuple)
    visual_plan: tuple[str, ...] = field(default_factory=tuple)
    external_id: str = ""
    rumor: bool = False
    metadata: dict[str, Any] = field(default_factory=dict)

    @property
    def fingerprint(self) -> str:
        """Stable identifier for cross-run deduplication."""
        if self.external_id.strip():
            return self.external_id.strip()
        normalized = f"{self.source.name}|{self.url}|{self.title}".casefold().strip()
        return hashlib.sha256(normalized.encode("utf-8")).hexdigest()


@dataclass(frozen=True, slots=True)
class GamingNewsState:
    """Small persisted state for daily no-duplicate monitoring."""

    seen_fingerprints: tuple[str, ...] = field(default_factory=tuple)
    last_run_at: datetime | None = None


@dataclass(frozen=True, slots=True)
class GamingNewsDeskResult:
    """Daily result. no_news=True intentionally produces no content brief."""

    no_news: bool
    new_items: tuple[GamingNewsItem, ...]
    rejected_items: tuple[GamingNewsItem, ...]
    growth_plan: AudienceGrowthPlan
    state: GamingNewsState


class JsonGamingNewsStateStore:
    """Persist only fingerprints and run time, never article bodies."""

    def __init__(self, path: str | Path) -> None:
        self._path = Path(path)

    def load(self) -> GamingNewsState:
        if not self._path.exists():
            return GamingNewsState()
        data = json.loads(self._path.read_text(encoding="utf-8"))
        last_run = data.get("last_run_at")
        return GamingNewsState(
            seen_fingerprints=tuple(str(item) for item in data.get("seen_fingerprints", ())),
            last_run_at=datetime.fromisoformat(last_run) if last_run else None,
        )

    def save(self, state: GamingNewsState) -> None:
        self._path.parent.mkdir(parents=True, exist_ok=True)
        payload = {
            "seen_fingerprints": list(state.seen_fingerprints),
            "last_run_at": state.last_run_at.isoformat() if state.last_run_at else None,
        }
        self._path.write_text(json.dumps(payload, ensure_ascii=True, indent=2), encoding="utf-8")


class GamingNewsDesk:
    """Filter, deduplicate and route relevant gaming news to content planning."""

    _BLOCKED_TAGS = frozenset({"leak", "piracy", "cheat", "unverified"})

    def __init__(
        self,
        planner: AudienceGrowthPlanner | None = None,
        *,
        max_age_hours: float = 72.0,
        minimum_authority: float = 0.65,
        max_seen: int = 2_000,
    ) -> None:
        self._planner = planner or AudienceGrowthPlanner(allowed_pillars=("gaming",))
        self._max_age_hours = max(1.0, max_age_hours)
        self._minimum_authority = max(0.0, min(1.0, minimum_authority))
        self._max_seen = max(100, max_seen)

    def run(
        self,
        items: tuple[GamingNewsItem, ...],
        state: GamingNewsState | None = None,
        *,
        approved_ids: tuple[str, ...] = (),
        now: datetime | None = None,
    ) -> GamingNewsDeskResult:
        """Process one daily collection and create no brief when nothing qualifies."""
        current = state or GamingNewsState()
        reference_time = now or datetime.now(UTC)
        seen = set(current.seen_fingerprints)
        accepted: list[GamingNewsItem] = []
        rejected: list[GamingNewsItem] = []

        for item in items:
            fingerprint = item.fingerprint
            if fingerprint in seen:
                rejected.append(item)
                continue
            seen.add(fingerprint)
            age_hours = max(0.0, (reference_time - item.published_at).total_seconds() / 3600.0)
            blocked_tag = bool(self._BLOCKED_TAGS.intersection(tag.casefold() for tag in item.tags))
            if (
                item.rumor
                or blocked_tag
                or age_hours > self._max_age_hours
                or item.source.authority < self._minimum_authority
                or not item.key_points
            ):
                rejected.append(item)
                continue
            accepted.append(item)

        candidates = tuple(self._to_candidate(item) for item in accepted)
        growth_plan = self._planner.build_plan(
            candidates,
            approved_ids=approved_ids,
            now=reference_time,
        )
        ordered_seen = tuple(list(current.seen_fingerprints) + [item.fingerprint for item in items])
        next_state = GamingNewsState(
            seen_fingerprints=tuple(dict.fromkeys(ordered_seen))[-self._max_seen :],
            last_run_at=reference_time,
        )
        return GamingNewsDeskResult(
            no_news=not accepted,
            new_items=tuple(accepted),
            rejected_items=tuple(rejected),
            growth_plan=growth_plan,
            state=next_state,
        )

    @staticmethod
    def _to_candidate(item: GamingNewsItem) -> GrowthCandidate:
        hook = str(item.metadata.get("hook", "")).strip() or f"Saiu novidade sobre {item.game or item.title}."
        candidate_id = f"gaming-{item.fingerprint[:16]}"
        risk_tags = tuple(
            risk
            for risk in ("copyright_reupload" if item.metadata.get("reupload_only") else "",)
            if risk
        )
        return GrowthCandidate(
            candidate_id=candidate_id,
            topic=item.title,
            hook=hook,
            angle=str(item.metadata.get("angle", "verified gaming news")),
            pillar="gaming",
            key_points=item.key_points,
            evidence=(
                TrendEvidence(
                    title=item.title,
                    source_url=item.url,
                    source_type=item.source.source_type,
                    observed_at=item.published_at,
                    confidence=item.source.authority,
                ),
            ),
            visual_plan=item.visual_plan,
            risks=risk_tags,
            series_potential=bool(item.metadata.get("series_potential", True)),
            metadata={
                "game": item.game,
                "source_name": item.source.name,
                "source_primary": item.source.primary,
                "youtube_shorts_variant": True,
                "subtitles_required": True,
                "avatar_optional": True,
            },
        )
