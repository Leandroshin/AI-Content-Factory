"""Prove review-only delivery from Gaming News Desk to the dashboard."""

from __future__ import annotations

from datetime import UTC, datetime

from core.content_factory import (
    GamingDashboardBridge,
    GamingNewsDesk,
    GamingNewsItem,
    GamingNewsSource,
)
from core.tools.http import HttpResponse, MockHttpClient


COUNT = 0


def check(condition: bool, label: str) -> None:
    global COUNT
    COUNT += 1
    if not condition:
        raise AssertionError(label)


def main() -> None:
    now = datetime(2026, 7, 13, 9, 0, tzinfo=UTC)
    source = GamingNewsSource(
        name="Official Games Newsroom",
        url="https://games.example.com/news",
        source_type="official_publisher",
        authority=0.96,
        primary=True,
    )
    item = GamingNewsItem(
        title="New game update confirmed",
        url="https://games.example.com/news/update",
        published_at=now,
        source=source,
        game="Example Game",
        key_points=("Official update", "New map", "Launch this week"),
        visual_plan=("official page", "gameplay excerpt", "captions"),
        external_id="official-update-2026-07-13",
    )
    review = GamingNewsDesk().run((item,), now=now)
    client = MockHttpClient(default_response=HttpResponse(status_code=202, body={"accepted": True}))
    endpoint = "https://central.example.com/api/intake/gaming"
    bridge = GamingDashboardBridge(client, endpoint)

    disabled = bridge.publish(review, token="secret", enabled=False)
    check(disabled.skipped_reason == "bridge_disabled", "Bridge defaults disabled")
    check(len(client.sent_requests) == 0, "Disabled bridge sends no HTTP")

    sent = bridge.publish(review, token="secret", enabled=True)
    check(sent.eligible == 1, "One review is eligible")
    check(sent.accepted == 1 and sent.failed == 0, "Review is accepted")
    check(len(sent.submissions) == 1, "Submission is audited")
    check(sent.submissions[0].status_code == 202, "HTTP acceptance is retained")
    request = client.last_request()
    check(request is not None, "Request exists")
    check(request.url == endpoint, "Endpoint is exact")
    check("secret" not in request.url, "Token is absent from URL")
    check(request.headers["Authorization"] == "Bearer secret", "Token uses authorization header")
    check(request.body["id"].startswith("gaming-"), "Candidate ID is a safe slug")
    check(request.body["source"] == source.name, "Source name is preserved")
    check(request.body["channel"] == "Fase Nova Games", "Channel is explicit")
    check(request.body["sources"][0]["sourceType"] == "official", "Source type is normalized")
    check(request.body["priority"] in {"medium", "high"}, "Priority is bounded")
    check(0 <= request.body["score"] <= 100, "Score is bounded")
    check(request.body["confidence"] == 96, "Confidence is converted to percent")

    no_news = GamingNewsDesk().run((), now=now)
    skipped = bridge.publish(no_news, token="secret", enabled=True)
    check(skipped.skipped_reason == "no_news", "No-news days are skipped")
    check(len(client.sent_requests) == 1, "No-news creates no extra request")

    approved = GamingNewsDesk().run((item,), approved_ids=(review.growth_plan.decisions[0].candidate.candidate_id,), now=now)
    no_review = bridge.publish(approved, token="secret", enabled=True)
    check(no_review.skipped_reason == "no_review_items", "Approved content is not re-enqueued")
    check(len(client.sent_requests) == 1, "Approved content creates no extra request")
    print(f"All {COUNT} assertions passed.")


if __name__ == "__main__":
    main()
