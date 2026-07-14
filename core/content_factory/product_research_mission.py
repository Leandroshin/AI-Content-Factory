"""Controlled marketplace discovery missions for the Product Research Department."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Protocol
from uuid import UUID, uuid4

from core.departments.product_research import (
    MarketplaceSignal,
    ProductCandidate,
    ProductResearchBrief,
    ProductResearchPipeline,
)
from core.tools.adapters.models import AdapterExecutionResult, ToolRequest


class CatalogSearchAdapter(Protocol):
    """Narrow contract implemented by the read-only marketplace adapter."""

    def execute(self, request: ToolRequest) -> AdapterExecutionResult: ...


@dataclass(frozen=True, slots=True)
class ProductResearchMission:
    """Owner request for a bounded, read-only marketplace search."""

    mission_id: UUID = field(default_factory=uuid4)
    goal: str = ""
    marketplace: str = "mercado_livre"
    category_id: str = ""
    max_price: float | None = None
    result_limit: int = 5
    target_channel: str = "telegram_public"
    timeframe: str = "week"


@dataclass(frozen=True, slots=True)
class ProductResearchMissionResult:
    """Shortlist returned for owner review without publication rights."""

    mission_id: UUID
    status: str
    report: dict[str, Any] = field(default_factory=dict)
    error: str = ""
    provider_status: str = "not_called"
    publication_status: str = "blocked"
    affiliate_links_status: str = "owner_confirmation_required"


class ProductResearchMissionWorker:
    """Bridge marketplace catalog reads into the existing research pipeline."""

    def __init__(self, mercado_livre: CatalogSearchAdapter) -> None:
        self._mercado_livre = mercado_livre

    def run(self, mission: ProductResearchMission) -> ProductResearchMissionResult:
        error = self._validate(mission)
        if error:
            return ProductResearchMissionResult(mission_id=mission.mission_id, status="blocked", error=error)
        if mission.marketplace != "mercado_livre":
            return ProductResearchMissionResult(
                mission_id=mission.mission_id,
                status="needs_input",
                error="Marketplace ainda não possui coleta oficial conectada nesta missão.",
            )

        response = self._mercado_livre.execute(ToolRequest(
            tool_id=uuid4(),
            capability="web_search",
            params={
                "action": "search_items",
                "query": mission.goal,
                "category_id": mission.category_id,
                "limit": min(20, max(mission.result_limit * 3, mission.result_limit)),
                "offset": 0,
            },
        ))
        if not response.success:
            return ProductResearchMissionResult(
                mission_id=mission.mission_id,
                status="blocked",
                error=response.error or "A busca do catálogo não retornou dados utilizáveis.",
            )

        data = response.output.get("data", {})
        raw_results = data.get("results", ()) if isinstance(data, dict) else ()
        candidates = tuple(
            candidate for item in raw_results
            if isinstance(item, dict)
            for candidate in (self._candidate(item, mission),)
            if candidate is not None
        )
        if not candidates:
            return ProductResearchMissionResult(
                mission_id=mission.mission_id,
                status="needs_input",
                error="Nenhum produto compatível foi encontrado nos limites da missão.",
            )

        brief = ProductResearchBrief(
            task_id=mission.mission_id,
            title=f"Pesquisa comercial: {mission.goal}",
            objective="Encontrar produtos auditáveis para curadoria orgânica, sem publicar.",
            target_market="BR",
            niches=(mission.goal,),
            source_platforms=("Mercado Livre",),
            candidates=candidates,
            shortlist_size=mission.result_limit,
            require_affiliate_url=False,
            metadata={
                "target_channel": mission.target_channel,
                "timeframe": mission.timeframe,
                "read_only": True,
            },
        )
        pipeline = ProductResearchPipeline(brief)
        while pipeline.stage not in {"completed", "failed"}:
            pipeline.advance()
        delivered = next((entry.output for entry in reversed(pipeline.stages_log) if entry.stage == "delivering"), {})
        return ProductResearchMissionResult(
            mission_id=mission.mission_id,
            status="review" if pipeline.stage == "completed" else "blocked",
            report=delivered,
            error="" if pipeline.stage == "completed" else "A pontuação dos candidatos falhou.",
        )

    @staticmethod
    def _validate(mission: ProductResearchMission) -> str:
        if not 2 <= len(mission.goal.strip()) <= 120:
            return "A missão precisa ter um objetivo de 2 a 120 caracteres."
        if not 1 <= mission.result_limit <= 10:
            return "A missão aceita de 1 a 10 resultados."
        if mission.max_price is not None and mission.max_price <= 0:
            return "O preço máximo deve ser positivo."
        return ""

    @staticmethod
    def _candidate(item: dict[str, Any], mission: ProductResearchMission) -> ProductCandidate | None:
        title = str(item.get("title", "")).strip()
        source_url = str(item.get("permalink", "")).strip()
        price = _number(item.get("price"))
        if not title or not source_url.startswith("https://") or price <= 0:
            return None
        if mission.max_price is not None and price > mission.max_price:
            return None
        sold = max(0.0, _number(item.get("sold_quantity")))
        available = max(0.0, _number(item.get("available_quantity")))
        original_price = _number(item.get("original_price")) or None
        thumbnail = str(item.get("thumbnail", "")).replace("http://", "https://")
        demand = min(25.0, 6.0 + min(sold, 500.0) / 25.0)
        return ProductCandidate(
            product_name=title,
            marketplace="Mercado Livre",
            category=str(item.get("category_id", "")),
            niche=mission.goal,
            source_url=source_url,
            image_url=thumbnail if thumbnail.startswith("https://") else "",
            current_price=price,
            old_price=original_price,
            marketplace_trust=0.88,
            demand_signals=(MarketplaceSignal(
                name="catalog_demand",
                value=demand,
                source="Mercado Livre Catalog API",
                note=f"sold_quantity={int(sold)}; available_quantity={int(available)}",
            ),),
            creative_signals=(MarketplaceSignal(
                name="catalog_image",
                value=12.0 if thumbnail else 3.0,
                source="Mercado Livre Catalog API",
            ),),
            notes=("affiliate_link_requires_owner_confirmation", "organic_distribution_only_until_policy_review"),
            metadata={
                "item_id": str(item.get("id", "")),
                "sold_quantity": int(sold),
                "available_quantity": int(available),
                "target_channel": mission.target_channel,
                "read_only": True,
            },
        )


def _number(value: Any) -> float:
    try:
        return float(value or 0.0)
    except (TypeError, ValueError):
        return 0.0
