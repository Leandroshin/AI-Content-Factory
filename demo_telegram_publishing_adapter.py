"""Demonstration: Telegram publishing adapter.

Flow:
  1. Register Telegram in ProviderControlCenter
  2. Prove token masking and REAL-mode approval gates
  3. Execute get_me and send_message through MockHttpClient
  4. Feed an Affiliate Deals message into TelegramAdapter
"""

from __future__ import annotations

from uuid import uuid4

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
from core.tools import (
    ExecutionMode,
    HttpResponse,
    MockHttpClient,
    MockSecretProvider,
    ProviderControlCenter,
    SecretKey,
    TelegramAdapter,
    TelegramProvider,
    ToolRequest,
)
from core.tools.http.real_client import _sanitize_http_text


_ASSERTION_COUNTER: int = 0
_TOKEN = "test_telegram_token_1234567890"


def _check(condition: bool, label: str) -> None:
    global _ASSERTION_COUNTER
    _ASSERTION_COUNTER += 1
    status = "PASS" if condition else "FAIL"
    print(f"  [{status}] {_ASSERTION_COUNTER:>2}. {label}")
    if not condition:
        raise AssertionError(label)


def _configured_adapter(
    center: ProviderControlCenter,
    http: MockHttpClient,
) -> TelegramAdapter:
    adapter = TelegramAdapter()
    adapter.configure({"bot_token": "configured_via_secret_provider"})
    adapter.authenticate()
    adapter.mark_ready()
    adapter.set_provider(TelegramProvider())
    adapter.set_http_client(http)
    center.apply_to_telegram(adapter)
    return adapter


def _send_request(
    *,
    text: str,
    approved: bool,
    chat_id: str = "-1001234567890",
) -> ToolRequest:
    return ToolRequest(
        tool_id=uuid4(),
        capability="social_media",
        params={
            "action": "send_message",
            "chat_id": chat_id,
            "text": text,
            "approved": approved,
            "disable_web_page_preview": True,
        },
    )


def _affiliate_message() -> str:
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
    delivery = pipeline.stages_log[-1].output
    return str(delivery["message_body"])


def main() -> None:
    print("=" * 70)
    print("Telegram Publishing Adapter - Safe Bot Publishing")
    print("=" * 70)

    print("\n" + "-" * 70)
    print("Step 1: Register Telegram provider controls")
    print("-" * 70)
    secrets = MockSecretProvider()
    center = ProviderControlCenter(secret_provider=secrets)
    center.register_telegram(max_messages=1, max_requests=4)

    snap = center.snapshot("telegram")
    _check(snap.provider == "telegram", "Telegram profile registered")
    _check(snap.execution_mode == "mock", "Default mode is MOCK")
    _check(snap.status == "safe_mock", "MOCK profile is safe")
    _check(snap.missing_secret_keys == ("bot_token",), "Bot token starts missing")

    center.set_secret("telegram", "bot_token", _TOKEN)
    snap = center.snapshot("telegram")
    dashboard_text = str(center.dashboard_state())
    _check(snap.configured_secret_keys == ("bot_token",), "Bot token marked configured")
    _check(_TOKEN not in dashboard_text, "Dashboard never exposes raw token")
    _check("te...90" in dashboard_text, "Dashboard exposes masked token hint")

    print("\n" + "-" * 70)
    print("Step 2: REAL mode requires owner approval and budget")
    print("-" * 70)
    center.set_execution_mode("telegram", ExecutionMode.REAL)
    snap = center.snapshot("telegram")
    _check(snap.execution_mode == "real", "Telegram switched to REAL")
    _check(snap.status == "awaiting_owner_approval", "REAL awaits owner approval")
    _check(not snap.can_execute_real, "Cannot execute REAL before approval")

    center.approve_provider("telegram", True)
    snap = center.snapshot("telegram")
    _check(snap.status == "real_ready", "Telegram is REAL-ready after approval")
    _check(snap.can_execute_real, "Telegram can execute REAL after key + budget + approval")

    print("\n" + "-" * 70)
    print("Step 3: Validate bot via get_me")
    print("-" * 70)
    get_me_http = MockHttpClient(default_response=HttpResponse(
        status_code=200,
        headers={"content-type": "application/json"},
        body={
            "ok": True,
            "result": {
                "id": 123456789,
                "is_bot": True,
                "first_name": "AI Content Factory",
                "username": "ai_content_factory_bot",
                "can_join_groups": True,
                "can_read_all_group_messages": False,
            },
        },
    ))
    adapter = _configured_adapter(center, get_me_http)
    get_me = adapter.execute(ToolRequest(
        tool_id=uuid4(),
        capability="social_media",
        params={"action": "get_me"},
    ))
    _check(get_me.success, "get_me succeeds through MockHttpClient")
    _check(get_me.output["username"] == "ai_content_factory_bot", "Bot username returned")
    _check(_TOKEN not in str(get_me), "get_me result does not expose token")
    _check(len(get_me_http.sent_requests) == 1, "get_me sends one HTTP request")
    _check(
        _sanitize_http_text(
            "https://api.telegram.org/bot123456789:ABCdef_1234567890ABCdef_1234567890/getMe"
        ).endswith("/bot<redacted>/getMe"),
        "Telegram URL sanitizer redacts bot token",
    )

    print("\n" + "-" * 70)
    print("Step 4: send_message gates")
    print("-" * 70)
    send_http = MockHttpClient(default_response=HttpResponse(
        status_code=200,
        headers={"content-type": "application/json"},
        body={"ok": True, "result": {"message_id": 4242}},
    ))
    sender = _configured_adapter(center, send_http)

    blocked_approval = sender.execute(_send_request(text="Oferta teste", approved=False))
    _check(not blocked_approval.success, "REAL send is blocked without approved=True")
    _check(len(send_http.sent_requests) == 0, "Approval block sends no HTTP")

    missing_chat = sender.execute(_send_request(text="Oferta teste", approved=True, chat_id=""))
    _check(not missing_chat.success, "REAL send is blocked without chat_id")
    _check(len(send_http.sent_requests) == 0, "Missing chat_id sends no HTTP")

    too_long = sender.execute(_send_request(text="x" * 4097, approved=True))
    _check(not too_long.success, "REAL send blocks messages over 4096 chars")
    _check(too_long.output["max_text_length"] == 4096, "Telegram length limit is surfaced")
    _check(len(send_http.sent_requests) == 0, "Long message sends no HTTP")

    sent = sender.execute(_send_request(text="Oferta aprovada para Telegram", approved=True))
    _check(sent.success, "Approved REAL send succeeds through MockHttpClient")
    _check(sent.output["status"] == "sent", "Telegram output status is sent")
    _check(sent.output["message_id"] == 4242, "Telegram message_id returned")
    _check(len(send_http.sent_requests) == 1, "Approved send makes one HTTP request")
    last = send_http.last_request()
    assert last is not None
    _check(last.body["link_preview_options"]["is_disabled"], "Link preview disabled by default")
    _check(_TOKEN not in str(sent), "send result does not expose token")

    print("\n" + "-" * 70)
    print("Step 5: Budget blocks additional REAL sends")
    print("-" * 70)
    second = sender.execute(_send_request(text="Segunda oferta", approved=True))
    _check(not second.success, "Second send blocked by one-message budget")
    _check(second.output["_blocked_by_budget"], "Budget block is explicit")
    _check(len(send_http.sent_requests) == 1, "Budget block sends no extra HTTP")
    usage = center.snapshot("telegram").usage_summary
    assert usage is not None
    _check(usage.requests == 2, "Usage tracks get_me and send_message attempts")
    _check(usage.billable_units == 1, "Usage tracks one billable message")

    print("\n" + "-" * 70)
    print("Step 6: Affiliate Deals message can feed TelegramAdapter")
    print("-" * 70)
    affiliate_text = _affiliate_message()
    _check("TUDOPRIME" in affiliate_text, "Affiliate message includes coupon")
    _check("Link de afiliado" in affiliate_text, "Affiliate message includes disclosure")
    _check(len(affiliate_text) <= 4096, "Affiliate message fits Telegram limit")

    mock_sender = TelegramAdapter()
    mock_sender.configure({"bot_token": _TOKEN})
    mock_sender.authenticate()
    mock_sender.mark_ready()
    mock_result = mock_sender.execute(_send_request(text=affiliate_text, approved=True))
    _check(mock_result.success, "Affiliate message can be prepared in MOCK Telegram mode")
    _check(mock_result.output["text_length"] == len(affiliate_text), "Telegram output keeps text length")

    print(f"\n{'=' * 70}")
    print(f"All {_ASSERTION_COUNTER} assertions passed.")
    print(f"{'=' * 70}")


if __name__ == "__main__":
    main()
