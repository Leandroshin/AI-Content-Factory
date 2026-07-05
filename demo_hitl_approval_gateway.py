"""Demonstration: human approval gate before Telegram publication.

Flow:
  1. Build an affiliate deal Telegram message
  2. Create a human approval request
  3. Send the approval prompt through TelegramAdapter in MOCK mode
  4. Prove publication is blocked while pending/rejected
  5. Approve and publish the message through the same adapter
  6. Project approval metrics into observability
"""

from __future__ import annotations

import time
from uuid import uuid4

from core.approval import ApprovalRuntime, ApprovalStatus, TelegramApprovalGateway
from core.departments.affiliate_deals import (
    AffiliateDealTask,
    AffiliateLink,
    AudienceGrowthPlan,
    CouponInfo,
    DealCampaign,
    MarketplaceSource,
    PriceSnapshot,
    ProductOffer,
)
from core.departments.affiliate_deals.pipeline import AffiliateDealsPipeline, PipelineStage
from core.events.bus import EventBus
from core.observability import ObservabilityProjector
from core.tools import TelegramAdapter, ToolRequest


_ASSERTION_COUNTER: int = 0
_TOKEN = "test_telegram_token_approval_gateway"
_OWNER_CHAT_ID = "-1001234567890"


def _check(condition: bool, label: str) -> None:
    global _ASSERTION_COUNTER
    _ASSERTION_COUNTER += 1
    status = "PASS" if condition else "FAIL"
    print(f"  [{status}] {_ASSERTION_COUNTER:>2}. {label}")
    if not condition:
        raise AssertionError(label)


def _send_request(text: str, approved: bool) -> ToolRequest:
    return ToolRequest(
        tool_id=uuid4(),
        capability="social_media",
        params={
            "action": "send_message",
            "chat_id": _OWNER_CHAT_ID,
            "text": text,
            "approved": approved,
        },
    )


def _affiliate_delivery() -> dict[str, object]:
    amazon = MarketplaceSource(
        name="amazon",
        display_name="Amazon",
        trust_score=0.92,
        supports_affiliate_links=True,
    )
    offer = ProductOffer(
        marketplace=amazon,
        product_name="PlayStation DualSense Controle sem fio - Gray Camouflage",
        category="gamer",
        audience="gamers e compradores de tecnologia",
        product_url="https://amazon.example/dualsense",
        image_url="https://img.example/dualsense.jpg",
        price=PriceSnapshot(
            old_price=499.90,
            current_price=327.22,
            payment_terms="no Pix",
            shipping_notes="Prime",
        ),
        coupon=CouponInfo(code="TUDOPRIME"),
        affiliate=AffiliateLink(
            original_url="https://amazon.example/dualsense",
            affiliate_url="https://amzn.example/seu-link-afiliado",
            tracking_id="shin-20",
        ),
        urgency_level="flash",
        stock_status="available",
        source_label="telegram_reference",
    )
    task = AffiliateDealTask(
        task_id=uuid4(),
        title="Preparar oferta DualSense para Telegram",
        campaign=DealCampaign(
            name="Achados Tech Prime",
            niche="tech_gamer",
            target_audience="compradores brasileiros buscando ofertas reais",
        ),
        offers=(offer,),
        preferred_channel="telegram",
        audience_growth_plan=AudienceGrowthPlan(primary_funnel="facebook_warmup_to_telegram"),
        require_human_approval=True,
        auto_publish_allowed=False,
    )

    pipeline = AffiliateDealsPipeline(task)
    while pipeline.stage not in (PipelineStage.COMPLETED.value, PipelineStage.FAILED.value):
        pipeline.advance()
    return dict(pipeline.stages_log[-1].output)


def main() -> None:
    print("=" * 70)
    print("HITL Approval Gateway - Telegram Publication Gate")
    print("=" * 70)

    event_bus = EventBus()
    observer = ObservabilityProjector(event_bus)
    approvals = ApprovalRuntime(event_bus=event_bus)

    telegram = TelegramAdapter()
    telegram.configure({"bot_token": _TOKEN})
    telegram.authenticate()
    telegram.mark_ready()
    gateway = TelegramApprovalGateway(
        approvals,
        telegram,
        owner_chat_id=_OWNER_CHAT_ID,
    )

    print("\n" + "-" * 70)
    print("Step 1: Build an affiliate deal pending approval")
    print("-" * 70)
    delivery = _affiliate_delivery()
    message = str(delivery["message_body"])
    _check(delivery["publishing_status"] == "pending_approval", "Affiliate deal waits for approval")
    _check("TUDOPRIME" in message, "Message includes coupon")
    _check("Link de afiliado" in message, "Message includes affiliate disclosure")
    _check(len(message) <= 4096, "Message fits Telegram")

    print("\n" + "-" * 70)
    print("Step 2: Create approval request and notify owner")
    print("-" * 70)
    request = approvals.request_approval(
        title="Publicar oferta DualSense no Telegram",
        preview_text=message,
        payload={
            "telegram_text": message,
            "chat_id": _OWNER_CHAT_ID,
            "publishing_status": delivery["publishing_status"],
            "score_total": delivery["score_total"],
        },
        requester="AffiliateDealsEmployee",
        source="affiliate_deals",
        subject_type="telegram_publication",
        subject_id=str(delivery["task_id"]),
        risk_level="medium",
    )
    _check(request.status == ApprovalStatus.PENDING, "Approval request starts pending")
    _check(approvals.snapshot().pending == 1, "Approval queue has one pending item")
    _check("telegram_text" not in str(request.public_dict()), "Public view hides private payload keys")

    notification = gateway.send_approval_request(request)
    _check(notification.success, "Approval notification is sent in MOCK Telegram mode")
    _check(notification.output["status"] == "sent_mock", "Notification stays mock-safe")
    _check(_TOKEN not in str(notification), "Telegram token is not exposed")

    print("\n" + "-" * 70)
    print("Step 3: Pending and adapter gates block publication")
    print("-" * 70)
    blocked_pending = gateway.publish_if_approved(request.approval_id)
    _check(not blocked_pending.success, "Gateway blocks publication while pending")
    _check(blocked_pending.output["approval_status"] == "pending", "Blocked output shows pending status")

    direct_block = telegram.execute(_send_request(message, approved=False))
    _check(not direct_block.success, "TelegramAdapter also blocks without approved=True")
    _check(direct_block.output["status"] == "approval_required", "Adapter surfaces approval_required")

    print("\n" + "-" * 70)
    print("Step 4: Owner approves and publication is released")
    print("-" * 70)
    decision = approvals.approve(
        request.approval_id,
        decided_by="Shin",
        reason="Oferta conferida e pronta para publicar.",
    )
    _check(decision.approved, "Decision is approved")
    _check(approvals.is_approved(request.approval_id), "Runtime recognizes approved request")
    released = approvals.release_payload(request.approval_id)
    _check(released["telegram_text"] == message, "Approved payload is released")

    published = gateway.publish_if_approved(request.approval_id)
    _check(published.success, "Approved publication succeeds in MOCK Telegram mode")
    _check(published.output["status"] == "sent_mock", "Published status is sent_mock")
    _check(published.output["text_length"] == len(message), "Telegram output preserves text length")

    print("\n" + "-" * 70)
    print("Step 5: Rejected and expired requests remain blocked")
    print("-" * 70)
    rejected = approvals.request_approval(
        title="Oferta com preco duvidoso",
        preview_text="Oferta precisa de revisao manual.",
        payload={"telegram_text": "nao publicar"},
        requester="AffiliateDealsEmployee",
        source="affiliate_deals",
        risk_level="high",
    )
    reject_decision = approvals.reject(
        rejected.approval_id,
        decided_by="Shin",
        reason="Preco ainda nao foi validado.",
    )
    _check(reject_decision.status == ApprovalStatus.REJECTED, "Reject decision is recorded")
    blocked_rejected = gateway.publish_if_approved(rejected.approval_id)
    _check(not blocked_rejected.success, "Gateway blocks rejected publication")

    expired = approvals.request_approval(
        title="Oferta expirada",
        preview_text="Cupom venceu antes da revisao.",
        payload={"telegram_text": "cupom vencido"},
        requester="AffiliateDealsEmployee",
        source="affiliate_deals",
        expires_at=time.time() - 1.0,
    )
    approvals.expire_due()
    _check(approvals.require(expired.approval_id).status == ApprovalStatus.EXPIRED, "Expired request is closed")
    blocked_expired = gateway.publish_if_approved(expired.approval_id)
    _check(not blocked_expired.success, "Gateway blocks expired publication")

    print("\n" + "-" * 70)
    print("Step 6: Observability tracks the approval queue")
    print("-" * 70)
    snap = approvals.snapshot()
    _check(snap.total_requests == 3, "Runtime snapshot counts all requests")
    _check(snap.pending == 0, "Runtime snapshot has no pending requests")
    _check(snap.approved == 1, "Runtime snapshot counts approved")
    _check(snap.rejected == 1, "Runtime snapshot counts rejected")
    _check(snap.expired == 1, "Runtime snapshot counts expired")

    projected = observer.snapshot.approvals
    _check(projected.total_requests == 3, "Observability counts approval requests")
    _check(projected.pending == 0, "Observability pending count is cleared")
    _check(projected.approved == 1, "Observability counts approved decisions")
    _check(projected.rejected == 1, "Observability counts rejected decisions")
    _check(projected.expired == 1, "Observability counts expired decisions")
    _check(any(e.startswith("approval:decided") for e in observer.snapshot.events), "Approval events are logged")

    print(f"\n{'=' * 70}")
    print(f"All {_ASSERTION_COUNTER} assertions passed.")
    print(f"{'=' * 70}")


if __name__ == "__main__":
    main()
