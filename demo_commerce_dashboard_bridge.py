"""Prove safe commerce review delivery to the hosted dashboard."""

from __future__ import annotations

from uuid import UUID

from core.approval import ApprovalRequest, ApprovalStatus
from core.content_factory import (
    AffiliateFactoryWorkflowResult,
    AffiliatePublicationPackage,
    CommerceDashboardBridge,
    ProductUrlBatchResult,
    ProductUrlEvidence,
    ProductUrlIntakeResult,
    ProductUrlIntakeStatus,
)
from core.content_factory.models import ContentWorkflowStepResult
from core.departments.product_research import ProductCandidate
from core.tools.http import HttpResponse, MockHttpClient


COUNT = 0


def check(condition: bool, label: str) -> None:
    global COUNT
    COUNT += 1
    if not condition:
        raise AssertionError(label)


def _ready_product(*, affiliate: bool = True) -> ProductUrlIntakeResult:
    candidate = ProductCandidate(
        candidate_id=UUID("11111111-1111-4111-8111-111111111111"),
        product_name="Controle gamer sem fio",
        marketplace="amazon",
        category="games",
        source_url="https://www.amazon.com.br/dp/example",
        affiliate_url="https://amzn.to/example" if affiliate else "",
        image_url="https://images.example.com/controller.jpg",
        current_price=299.90,
        old_price=399.90,
        commission_percent=4.0,
        marketplace_trust=0.92,
        metadata={"source_label": "Amazon Brasil"},
    )
    return ProductUrlIntakeResult(
        status=ProductUrlIntakeStatus.READY,
        evidence=ProductUrlEvidence(
            requested_url=candidate.source_url,
            canonical_url=candidate.source_url,
            marketplace="Amazon Brasil",
            fetched_at=1_783_938_600.0,
            http_status=200,
            extractor="json_ld",
            product_name=candidate.product_name,
            current_price=candidate.current_price,
            old_price=candidate.old_price,
            currency="BRL",
            image_url=candidate.image_url,
        ),
        candidate=candidate,
    )


def _pending_workflow() -> AffiliateFactoryWorkflowResult:
    approval = ApprovalRequest(
        approval_id=UUID("22222222-2222-4222-8222-222222222222"),
        title="Publicar oferta",
        preview_text="Controle gamer com desconto e aviso de afiliado.",
        status=ApprovalStatus.PENDING,
        created_at=1_783_938_600.0,
    )
    package = AffiliatePublicationPackage(
        package_id=UUID("33333333-3333-4333-8333-333333333333"),
        selected_product_name="Controle gamer sem fio",
        product_research_score=88.0,
        creative_action="keep",
        creative_score=91.0,
        deal_score=86.0,
        recommendation="post_now",
        publishing_status="pending_approval",
        message_body=approval.preview_text,
        approval_id=approval.approval_id,
        approval_status="pending",
    )
    research = ContentWorkflowStepResult(
        department="Product Research",
        task_id=UUID("44444444-4444-4444-8444-444444444444"),
        success=True,
        output={
            "shortlisted": ({
                "product_name": package.selected_product_name,
                "marketplace": "amazon",
                "source_url": "https://www.amazon.com.br/dp/example",
            },),
        },
    )
    return AffiliateFactoryWorkflowResult(
        success=True,
        package=package,
        steps=(research,),
        approval_request=approval,
        summary="Waiting for owner approval",
    )


def main() -> None:
    client = MockHttpClient(default_response=HttpResponse(status_code=202, body={"accepted": True}))
    endpoint = "https://central.example.com/api/intake/commerce"
    bridge = CommerceDashboardBridge(client, endpoint)

    batch = ProductUrlBatchResult(results=(_ready_product(), _ready_product(affiliate=False)))
    disabled = bridge.publish_product_intake(batch, token="secret", enabled=False)
    check(disabled.skipped_reason == "bridge_disabled", "Bridge defaults disabled")
    check(len(client.sent_requests) == 0, "Disabled bridge sends no HTTP")

    products = bridge.publish_product_intake(batch, token="secret", enabled=True)
    check(products.eligible == 1, "Only complete affiliate product is eligible")
    check(products.blocked == 1, "Product without affiliate URL is blocked")
    check(products.accepted == 1 and products.failed == 0, "Eligible product is accepted")
    request = client.last_request()
    check(request is not None, "Product request exists")
    check(request.url == endpoint, "Commerce endpoint is exact")
    check("secret" not in request.url, "Token is absent from URL")
    check(request.headers["Authorization"] == "Bearer secret", "Token uses bearer header")
    check(request.body["category"] == "Produto afiliado", "Product category is explicit")
    check(request.body["sources"][0]["sourceType"] == "marketplace", "Marketplace evidence is retained")
    check("public" not in request.body["nextAction"].lower(), "Product queue does not claim publication")

    workflow = bridge.publish_workflow_review(_pending_workflow(), token="secret", enabled=True)
    check(workflow.eligible == 1 and workflow.accepted == 1, "Pending HITL workflow enters review")
    request = client.last_request()
    check(request is not None and request.body["category"] == "Campanha afiliada", "Workflow category is explicit")
    check("HITL" in request.body["nextAction"], "Separate HITL remains explicit")
    check("não libera" in request.body["risk"], "Dashboard decision does not release publishing")

    approved_result = _pending_workflow()
    approved = ApprovalRequest(
        approval_id=approved_result.approval_request.approval_id,
        title="Publicar oferta",
        preview_text="Oferta aprovada",
        status=ApprovalStatus.APPROVED,
    )
    approved_result = AffiliateFactoryWorkflowResult(
        success=True,
        package=approved_result.package,
        steps=approved_result.steps,
        approval_request=approved,
    )
    skipped = bridge.publish_workflow_review(approved_result, token="secret", enabled=True)
    check(skipped.skipped_reason == "workflow_not_waiting_for_owner", "Approved workflow is not requeued")
    check(skipped.blocked == 1, "Non-pending workflow is counted as blocked")
    check(len(client.sent_requests) == 2, "No publication or extra HTTP is triggered")

    missing = bridge.publish_product_intake(batch, token="", enabled=True)
    check(missing.skipped_reason == "missing_token", "Missing token blocks synchronization")
    check(len(client.sent_requests) == 2, "Missing token sends no HTTP")
    print(f"All {COUNT} assertions passed.")


if __name__ == "__main__":
    main()
