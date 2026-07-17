"""Controlled bridge from affiliate commerce reviews to the hosted dashboard."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any
from urllib.parse import urlsplit

from core.approval import ApprovalStatus
from core.content_factory.affiliate_workflow import AffiliateFactoryWorkflowResult
from core.content_factory.product_url_intake import (
    ProductUrlBatchResult,
    ProductUrlIntakeResult,
    ProductUrlIntakeStatus,
)
from core.tools.http.client import HttpClient
from core.tools.http.errors import HttpError


@dataclass(frozen=True, slots=True)
class CommerceDashboardSubmission:
    """Auditable result that does not expose credentials or response bodies."""

    item_id: str
    item_type: str
    accepted: bool
    status_code: int = 0
    error: str = ""


@dataclass(frozen=True, slots=True)
class CommerceDashboardBridgeResult:
    """Bounded summary for one product or workflow synchronization."""

    skipped_reason: str = ""
    eligible: int = 0
    accepted: int = 0
    failed: int = 0
    blocked: int = 0
    submissions: tuple[CommerceDashboardSubmission, ...] = field(default_factory=tuple)


class CommerceDashboardBridge:
    """Send complete review items to the dashboard without executing decisions."""

    def __init__(self, client: HttpClient, endpoint: str) -> None:
        endpoint = endpoint.strip()
        if not endpoint.startswith("https://") or not endpoint.endswith("/api/intake/commerce"):
            raise ValueError("Commerce dashboard endpoint must be the public HTTPS intake route.")
        self._client = client
        self._endpoint = endpoint

    def publish_product_intake(
        self,
        batch: ProductUrlBatchResult,
        *,
        token: str,
        enabled: bool = False,
        channel: str = "Achados Baratos BR",
    ) -> CommerceDashboardBridgeResult:
        """Queue only complete products that already have an affiliate target."""
        if not enabled:
            return CommerceDashboardBridgeResult(skipped_reason="bridge_disabled")
        if not token.strip():
            return CommerceDashboardBridgeResult(skipped_reason="missing_token")

        eligible = tuple(item for item in batch.results if self._product_is_eligible(item))
        blocked = len(batch.results) - len(eligible)
        if not eligible:
            return CommerceDashboardBridgeResult(
                skipped_reason="no_complete_affiliate_products",
                blocked=blocked,
            )
        submissions = tuple(
            self._submit(
                item_id=f"product-{item.candidate.candidate_id}",
                item_type="product",
                payload=self._product_payload(item, channel=channel),
                token=token,
            )
            for item in eligible
            if item.candidate is not None
        )
        return self._result(submissions, blocked=blocked)

    def publish_workflow_review(
        self,
        result: AffiliateFactoryWorkflowResult,
        *,
        token: str,
        enabled: bool = False,
        channel: str = "Achados Baratos BR",
    ) -> CommerceDashboardBridgeResult:
        """Queue a pending HITL preview; never approve or publish it."""
        if not enabled:
            return CommerceDashboardBridgeResult(skipped_reason="bridge_disabled")
        if not token.strip():
            return CommerceDashboardBridgeResult(skipped_reason="missing_token")
        if not self._workflow_is_eligible(result):
            return CommerceDashboardBridgeResult(
                skipped_reason="workflow_not_waiting_for_owner",
                blocked=1,
            )
        approval = result.approval_request
        assert approval is not None
        submission = self._submit(
            item_id=f"affiliate-{approval.approval_id}",
            item_type="affiliate_workflow",
            payload=self._workflow_payload(result, channel=channel),
            token=token,
        )
        return self._result((submission,))

    def _submit(
        self,
        *,
        item_id: str,
        item_type: str,
        payload: dict[str, Any],
        token: str,
    ) -> CommerceDashboardSubmission:
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
            return CommerceDashboardSubmission(
                item_id=item_id,
                item_type=item_type,
                accepted=False,
                error=type(exc).__name__,
            )
        accepted = response.status_code == 202
        return CommerceDashboardSubmission(
            item_id=item_id,
            item_type=item_type,
            accepted=accepted,
            status_code=response.status_code,
            error="" if accepted else f"HTTP {response.status_code}",
        )

    @staticmethod
    def _product_is_eligible(item: ProductUrlIntakeResult) -> bool:
        candidate = item.candidate
        return bool(
            item.status is ProductUrlIntakeStatus.READY
            and candidate is not None
            and candidate.product_name.strip()
            and candidate.current_price > 0
            and candidate.image_url.strip()
            and candidate.has_affiliate_target
            and _public_https(candidate.source_url)
        )

    @staticmethod
    def _workflow_is_eligible(result: AffiliateFactoryWorkflowResult) -> bool:
        package = result.package
        approval = result.approval_request
        publication_succeeded = bool(
            result.publication_result is not None and result.publication_result.success
        )
        return bool(
            result.success
            and package is not None
            and approval is not None
            and approval.status is ApprovalStatus.PENDING
            and package.approval_status == ApprovalStatus.PENDING.value
            and package.publishing_status in {"pending_approval", "ready"}
            and package.message_body.strip()
            and not publication_succeeded
            and _public_https(_workflow_source_url(result))
        )

    @staticmethod
    def _product_payload(item: ProductUrlIntakeResult, *, channel: str) -> dict[str, Any]:
        candidate = item.candidate
        assert candidate is not None
        evidence = item.evidence
        score = round(min(100.0, candidate.marketplace_trust * 70.0 + candidate.discount_percent * 0.6 + min(candidate.commission_percent, 10.0)))
        confidence = round(min(100.0, candidate.marketplace_trust * 100.0))
        price = f"R$ {candidate.current_price:.2f}".replace(".", ",")
        discount = f" Desconto observado: {candidate.discount_percent:.0f}%." if candidate.discount_percent else ""
        return {
            "id": f"product-{candidate.candidate_id}",
            "title": candidate.product_name[:180],
            "source": str(candidate.metadata.get("source_label", candidate.marketplace))[:80],
            "channel": channel[:80],
            "category": "Produto afiliado",
            "summary": f"Produto coletado por URL por {price}.{discount} Link afiliado presente; ainda exige revisão comercial e criativa."[:600],
            "priority": "high" if score >= 80 else "medium",
            "score": score,
            "confidence": confidence,
            "risk": "Médio: preço, estoque, comissão, imagem e destino do link devem ser reconfirmados antes da publicação.",
            "nextAction": "Revisar a oferta no painel e, depois, executar o workflow com HITL separado.",
            "updatedAt": datetime.fromtimestamp(evidence.fetched_at, tz=UTC).isoformat(),
            "sources": [{
                "label": f"Página do produto em {evidence.marketplace}"[:160],
                "url": candidate.source_url,
                "sourceType": "marketplace",
                "publishedAt": None,
            }],
        }

    @staticmethod
    def _workflow_payload(
        result: AffiliateFactoryWorkflowResult,
        *,
        channel: str,
    ) -> dict[str, Any]:
        package = result.package
        approval = result.approval_request
        assert package is not None and approval is not None
        research = result.output_for("Product Research")
        selected = _selected_product(research, package.selected_product_name)
        source_url = str(selected.get("source_url", ""))
        marketplace = str(selected.get("marketplace", "Affiliate Commerce Workflow"))
        score = round(max(0.0, min(100.0, package.deal_score)))
        return {
            "id": f"affiliate-{approval.approval_id}",
            "title": f"Revisar oferta: {package.selected_product_name}"[:180],
            "source": "Affiliate Commerce Workflow",
            "channel": channel[:80],
            "category": "Campanha afiliada",
            "summary": approval.preview_text[:600],
            "priority": "high" if score >= 80 else "medium",
            "score": score,
            "confidence": round(max(0.0, min(100.0, package.product_research_score))),
            "risk": "Médio: o painel revisa a produção, mas não libera a publicação. O HITL interno continua obrigatório.",
            "nextAction": "Conferir oferta e fontes. A publicação no Telegram exige aprovação separada no HITL da fábrica.",
            "updatedAt": datetime.fromtimestamp(approval.created_at, tz=UTC).isoformat(),
            "sources": [{
                "label": f"Produto selecionado em {marketplace}"[:160],
                "url": source_url,
                "sourceType": "marketplace",
                "publishedAt": None,
            }],
        }

    @staticmethod
    def _result(
        submissions: tuple[CommerceDashboardSubmission, ...],
        *,
        blocked: int = 0,
    ) -> CommerceDashboardBridgeResult:
        return CommerceDashboardBridgeResult(
            eligible=len(submissions),
            accepted=sum(item.accepted for item in submissions),
            failed=sum(not item.accepted for item in submissions),
            blocked=blocked,
            submissions=submissions,
        )


def _public_https(url: str) -> bool:
    try:
        parsed = urlsplit(url.strip())
    except ValueError:
        return False
    return bool(parsed.scheme == "https" and parsed.hostname and not parsed.username and not parsed.password)


def _selected_product(research: dict[str, Any], product_name: str) -> dict[str, Any]:
    return next(
        (
            item
            for item in research.get("shortlisted", ())
            if isinstance(item, dict) and str(item.get("product_name", "")) == product_name
        ),
        {},
    )


def _workflow_source_url(result: AffiliateFactoryWorkflowResult) -> str:
    if result.package is None:
        return ""
    selected = _selected_product(
        result.output_for("Product Research"),
        result.package.selected_product_name,
    )
    return str(selected.get("source_url", ""))
