"""Deliver hosted research missions to the controlled Product Research worker."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any
from uuid import UUID

from core.content_factory.product_research_mission import ProductResearchMission, ProductResearchMissionWorker
from core.tools.http.client import HttpClient
from core.tools.http.errors import HttpError


@dataclass(frozen=True, slots=True)
class ProductResearchDashboardResult:
    skipped_reason: str = ""
    received: int = 0
    submitted: int = 0
    failed: int = 0
    mission_ids: tuple[str, ...] = field(default_factory=tuple)


class ProductResearchDashboardWorker:
    """Pull bounded missions and return reports; never publish or create links."""

    def __init__(self, client: HttpClient, endpoint: str) -> None:
        endpoint = endpoint.strip()
        if not endpoint.startswith("https://") or not endpoint.endswith("/api/intake/product-research"):
            raise ValueError("Research worker endpoint must be the public HTTPS intake route.")
        self._client = client
        self._endpoint = endpoint

    def run_once(
        self,
        worker: ProductResearchMissionWorker,
        *,
        token: str,
        enabled: bool = False,
        site_access_token: str = "",
    ) -> ProductResearchDashboardResult:
        if not enabled:
            return ProductResearchDashboardResult(skipped_reason="worker_disabled")
        if not token.strip():
            return ProductResearchDashboardResult(skipped_reason="missing_token")
        try:
            response = self._client.get(self._endpoint, headers=self._headers(token, site_access_token))
        except HttpError:
            return ProductResearchDashboardResult(skipped_reason="queue_unavailable")
        if response.status_code != 200 or not isinstance(response.body, dict):
            return ProductResearchDashboardResult(skipped_reason="invalid_queue_response")
        raw = response.body.get("missions", ())
        missions = tuple(self._coerce(value) for value in raw if isinstance(value, dict))
        missions = tuple(value for value in missions if value is not None)
        if not missions:
            return ProductResearchDashboardResult(skipped_reason="queue_empty")

        submitted = 0
        failed = 0
        ids: list[str] = []
        for mission in missions:
            result = worker.run(mission)
            payload = {
                "missionId": str(result.mission_id),
                "status": result.status,
                "report": result.report,
                "error": result.error,
            }
            try:
                delivery = self._client.post(
                    self._endpoint,
                    headers=self._headers(token, site_access_token, content_type=True),
                    body=payload,
                )
            except HttpError:
                failed += 1
                continue
            if delivery.status_code == 202:
                submitted += 1
                ids.append(str(result.mission_id))
            else:
                failed += 1
        return ProductResearchDashboardResult(
            received=len(missions), submitted=submitted, failed=failed, mission_ids=tuple(ids),
        )

    @staticmethod
    def _headers(token: str, site_access_token: str, *, content_type: bool = False) -> dict[str, str]:
        headers = {"Authorization": f"Bearer {token}"}
        if site_access_token.strip():
            headers["OAI-Sites-Authorization"] = f"Bearer {site_access_token.strip()}"
        if content_type:
            headers["Content-Type"] = "application/json"
        return headers

    @staticmethod
    def _coerce(value: dict[str, Any]) -> ProductResearchMission | None:
        try:
            mission_id = UUID(str(value.get("id", "")))
            marketplaces = value.get("marketplaces", ())
            marketplace = str(marketplaces[0]) if isinstance(marketplaces, list) and marketplaces else ""
            return ProductResearchMission(
                mission_id=mission_id,
                goal=str(value.get("goal", "")),
                marketplace=marketplace,
                category_id=(
                    str(value.get("category", ""))
                    if str(value.get("category", "")).startswith("MLB")
                    else ""
                ),
                max_price=float(value["maxPrice"]) if value.get("maxPrice") is not None else None,
                result_limit=int(value.get("resultLimit", 5)),
                target_channel=str(value.get("targetChannel", "telegram_public")),
                timeframe=str(value.get("timeframe", "week")),
            )
        except (TypeError, ValueError):
            return None
