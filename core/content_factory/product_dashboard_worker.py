"""Pull product URLs from the private dashboard and return intake evidence."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from core.content_factory.product_url_intake import ProductUrlIntake, ProductUrlIntakeStatus
from core.tools.http.client import HttpClient
from core.tools.http.errors import HttpError


@dataclass(frozen=True, slots=True)
class ProductDashboardWorkItem:
    request_id: str
    product_url: str
    affiliate_url: str = ""
    marketplace: str = ""
    evidence_url: str = ""
    language: str = ""
    source_kind: str = "product_page"
    owner_notes: str = ""


@dataclass(frozen=True, slots=True)
class ProductDashboardWorkResult:
    skipped_reason: str = ""
    received: int = 0
    submitted: int = 0
    failed: int = 0
    request_ids: tuple[str, ...] = field(default_factory=tuple)


class ProductDashboardWorker:
    """Execute evidence intake only; creative review and publication stay separate."""

    def __init__(self, client: HttpClient, endpoint: str) -> None:
        endpoint = endpoint.strip()
        if not endpoint.startswith("https://") or not endpoint.endswith("/api/intake/products"):
            raise ValueError("Product worker endpoint must be the public HTTPS intake route.")
        self._client = client
        self._endpoint = endpoint

    def run_once(
        self,
        intake: ProductUrlIntake,
        *,
        token: str,
        enabled: bool = False,
        site_access_token: str = "",
    ) -> ProductDashboardWorkResult:
        if not enabled:
            return ProductDashboardWorkResult(skipped_reason="worker_disabled")
        if not token.strip():
            return ProductDashboardWorkResult(skipped_reason="missing_token")
        try:
            response = self._client.get(
                self._endpoint,
                headers=self._headers(token, site_access_token=site_access_token),
            )
        except HttpError:
            return ProductDashboardWorkResult(skipped_reason="queue_unavailable")
        if response.status_code != 200 or not isinstance(response.body, dict):
            return ProductDashboardWorkResult(skipped_reason="invalid_queue_response")

        items = tuple(self._coerce_item(item) for item in response.body.get("items", ()))
        items = tuple(item for item in items if item is not None)
        if not items:
            return ProductDashboardWorkResult(skipped_reason="queue_empty")

        submitted = 0
        failed = 0
        request_ids: list[str] = []
        for item in items:
            result = intake.intake(
                item.product_url,
                affiliate_url=item.affiliate_url,
                overrides=self._intake_overrides(item),
            )
            payload = self._payload(item, result)
            try:
                delivery = self._client.post(
                    self._endpoint,
                    headers=self._headers(
                        token,
                        site_access_token=site_access_token,
                        include_content_type=True,
                    ),
                    body=payload,
                )
            except HttpError:
                failed += 1
                continue
            if delivery.status_code == 202:
                submitted += 1
                request_ids.append(item.request_id)
            else:
                failed += 1
        return ProductDashboardWorkResult(
            received=len(items),
            submitted=submitted,
            failed=failed,
            request_ids=tuple(request_ids),
        )

    @staticmethod
    def _headers(
        token: str,
        *,
        site_access_token: str,
        include_content_type: bool = False,
    ) -> dict[str, str]:
        headers = {"Authorization": f"Bearer {token}"}
        if site_access_token.strip():
            headers["OAI-Sites-Authorization"] = f"Bearer {site_access_token.strip()}"
        if include_content_type:
            headers["Content-Type"] = "application/json"
        return headers

    @staticmethod
    def _coerce_item(value: Any) -> ProductDashboardWorkItem | None:
        if not isinstance(value, dict):
            return None
        request_id = str(value.get("id", "")).strip()
        product_url = str(value.get("productUrl", "")).strip()
        if not request_id or not product_url.startswith("https://"):
            return None
        source_kind = str(value.get("sourceKind", "product_page")).strip()
        if source_kind not in {"product_page", "sales_page"}:
            source_kind = "product_page"
        return ProductDashboardWorkItem(
            request_id=request_id,
            product_url=product_url,
            affiliate_url=str(value.get("affiliateUrl", "")).strip(),
            marketplace=str(value.get("marketplace", "")).strip(),
            evidence_url=str(value.get("evidenceUrl", "")).strip(),
            language=str(value.get("language", "")).strip(),
            source_kind=source_kind,
            owner_notes=str(value.get("ownerNotes", "")).strip(),
        )

    @staticmethod
    def _intake_overrides(item: ProductDashboardWorkItem) -> dict[str, Any]:
        metadata: dict[str, Any] = {
            "dashboard_source_kind": item.source_kind,
            "dashboard_language": item.language,
        }
        notes: list[str] = []
        if item.evidence_url:
            metadata["dashboard_evidence_url"] = item.evidence_url
            notes.append("owner_provided_evidence_url")
        if item.owner_notes:
            metadata["dashboard_owner_notes_present"] = True
            notes.append("owner_notes_available")
        if item.source_kind == "sales_page":
            metadata["dashboard_requires_promise_review"] = True
            notes.append("sales_page_requires_promise_review")
        return {"metadata": metadata, "notes": tuple(notes)}

    def _payload(self, item: ProductDashboardWorkItem, intake_result: Any) -> dict[str, Any]:
        candidate = intake_result.candidate
        blocked = intake_result.status in {
            ProductUrlIntakeStatus.BLOCKED,
            ProductUrlIntakeStatus.FETCH_FAILED,
        } or candidate is None
        if blocked:
            return {
                "requestId": item.request_id,
                "status": "blocked",
                "title": item.marketplace or "Produto bloqueado",
                "imageUrl": "",
                "analysisSummary": intake_result.error or "A página não pôde ser coletada com segurança.",
                "missingFields": ["coleta_do_produto"],
                "score": 0,
                "confidence": 0,
                "risk": "Alto: evidência insuficiente ou URL bloqueada.",
                "nextAction": "Conferir a URL e completar os dados manualmente antes de tentar novamente.",
                "promiseReview": "Promessa não analisada porque a coleta segura não trouxe evidência suficiente.",
                "creativeRecommendation": "Nenhum criativo deve ser produzido antes de uma página válida ou dados manuais.",
                "commissionNotes": "Comissão não confirmada.",
                "funnelSuggestion": "Reenviar uma URL pública HTTPS ou completar manualmente produto, preço, imagem e link afiliado.",
                "affiliateReadiness": "Bloqueado para AffiliateCommerceWorkflow.",
            }

        missing = list(intake_result.manual_fields)
        if not candidate.has_affiliate_target:
            missing.append("link_afiliado")
        preview = self._workflow_preview(item, candidate)
        missing.extend(preview["missingFields"])
        score = round(min(
            100.0,
            candidate.marketplace_trust * 65.0
            + candidate.discount_percent * 0.6
            + min(candidate.commission_percent, 10.0),
            + preview["scoreAdjustment"],
        ))
        confidence = round(min(100.0, candidate.marketplace_trust * 100.0))
        price = f"R$ {candidate.current_price:.2f}".replace(".", ",")
        return {
            "requestId": item.request_id,
            "status": "needs_input" if missing else "completed",
            "title": candidate.product_name or f"Produto em {item.marketplace}",
            "imageUrl": candidate.image_url,
            "currentPrice": candidate.current_price,
            "oldPrice": (
                candidate.old_price
                if candidate.old_price is not None and candidate.old_price > candidate.current_price
                else None
            ),
            "analysisSummary": (
                f"Dados comerciais coletados. Preço observado: {price}. "
                f"{preview['promiseReview']} {preview['creativeRecommendation']}"
            ),
            "missingFields": list(dict.fromkeys(missing)),
            "score": max(0, min(100, score)),
            "confidence": max(0, min(100, confidence)),
            "risk": preview["risk"],
            "nextAction": preview["nextAction"],
            "promiseReview": preview["promiseReview"],
            "creativeRecommendation": preview["creativeRecommendation"],
            "commissionNotes": preview["commissionNotes"],
            "funnelSuggestion": preview["funnelSuggestion"],
            "affiliateReadiness": preview["affiliateReadiness"],
        }

    @staticmethod
    def _workflow_preview(item: ProductDashboardWorkItem, candidate: Any) -> dict[str, Any]:
        is_sales_page = item.source_kind == "sales_page"
        has_affiliate = candidate.has_affiliate_target
        has_image = bool(candidate.image_url)
        has_commission = candidate.commission_percent > 0
        missing: list[str] = []
        if not has_image:
            missing.append("imagem_do_produto")
        missing.append("revisao_criativa_da_imagem")
        if not has_commission:
            missing.append("comissao_confirmada")
        if is_sales_page:
            missing.append("promessa_e_politicas_da_pagina")
            promise = "Página de venda detectada: validar promessa, prova, garantias e políticas antes de usar tráfego."
            funnel = "Funil sugerido: análise da página -> advertorial/landing própria -> lista Telegram/WhatsApp -> teste pago pequeno somente depois."
            risk = "Médio/alto: página de venda exige checagem de promessa, política de anúncios e pagamento antes de escalar."
            next_action = "Confirmar comissão, revisar promessa da página e decidir se entra em teste orgânico ou advertorial."
            score_adjustment = -8.0
        else:
            promise = "Produto físico detectado: a promessa deve ficar limitada a preço, cupom, benefício concreto e disponibilidade."
            funnel = "Funil sugerido: post manual em Telegram/WhatsApp -> medir cliques -> só depois aquecer página e tráfego."
            risk = "Médio: preço, estoque, comissão e qualidade visual ainda precisam de confirmação final."
            next_action = "Concluir Creative Review, validar link afiliado e decidir se vira postagem manual em canal próprio."
            score_adjustment = 0.0
        if has_affiliate:
            affiliate = "Link afiliado informado; ainda precisa conferência de rastreamento e regras da plataforma."
            score_adjustment += 6.0
        else:
            affiliate = "Sem link afiliado; a fábrica não pode publicar nem prometer comissão."
            score_adjustment -= 10.0
        if has_image:
            creative = "Imagem encontrada; Creative Review decide se mantém, melhora ou troca antes de qualquer peça."
        else:
            creative = "Imagem ausente; funcionário deve buscar asset permitido ou pedir imagem manual antes de criar peça."
        if item.evidence_url:
            next_action += " Usar também a evidência adicional enviada pelo owner."
        return {
            "promiseReview": promise,
            "creativeRecommendation": creative,
            "commissionNotes": affiliate if has_commission else f"{affiliate} Comissão percentual ainda não veio da fonte.",
            "funnelSuggestion": funnel,
            "affiliateReadiness": "Pronto para pré-fluxo AffiliateCommerceWorkflow sem gasto." if has_affiliate else "Pendente antes do AffiliateCommerceWorkflow: link afiliado.",
            "missingFields": tuple(missing),
            "risk": risk,
            "nextAction": next_action,
            "scoreAdjustment": score_adjustment,
        }
