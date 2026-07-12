"""Meta Ads read-only adapter demonstration without external API calls."""

from __future__ import annotations

from uuid import uuid4

from core.tools.adapters import (
    ExecutionMode,
    MetaAdsAnalyticsAdapter,
    ToolRequest,
)
from core.tools.http import HttpMethod, HttpResponse, MockHttpClient
from core.tools.provider_settings import ProviderControlCenter
from core.tools.providers import MetaMarketingProvider
from core.tools.secrets import MockSecretProvider, SecretKey

_ASSERTION_COUNTER = 0
_TOKEN = "test_meta_access_token_read_only"
_ACCOUNT_ID = "2069488655023"


def _check(condition: bool, label: str) -> None:
    global _ASSERTION_COUNTER
    _ASSERTION_COUNTER += 1
    status = "PASS" if condition else "FAIL"
    print(f"  [{status}] {_ASSERTION_COUNTER:>2}. {label}")
    if not condition:
        raise AssertionError(label)


def _request(action: str, **params: object) -> ToolRequest:
    return ToolRequest(
        tool_id=uuid4(),
        capability="social_media",
        params={"action": action, **params},
    )


def _adapter(http: MockHttpClient) -> MetaAdsAnalyticsAdapter:
    secrets = MockSecretProvider()
    secrets.set(
        SecretKey(key="meta_access_token", provider="meta_marketing"),
        _TOKEN,
    )
    adapter = MetaAdsAnalyticsAdapter()
    adapter.configure(
        {
            "api_version": "v25.0",
            "ad_account_id": _ACCOUNT_ID,
            "meta_access_token": "configured_via_secret_provider",
        }
    )
    adapter.authenticate()
    adapter.mark_ready()
    adapter.set_execution_mode(ExecutionMode.REAL)
    adapter.set_secret_provider(secrets)
    adapter.set_provider(MetaMarketingProvider())
    adapter.set_http_client(http)
    return adapter


def main() -> None:
    print("=" * 70)
    print("Meta Ads Analytics - Strictly Read Only")
    print("=" * 70)

    print("\nStep 1: provider and lifecycle contract")
    provider = MetaMarketingProvider()
    _check(provider.provider_id == "meta_marketing", "Provider id is stable")
    _check(
        provider.base_url == "https://graph.facebook.com",
        "Official Graph host configured",
    )
    _check(provider.auth_type == "oauth_bearer", "Bearer OAuth is explicit")
    _check(
        provider.rate_limits.max_requests == 4, "Conservative request rate configured"
    )

    lifecycle = MetaAdsAnalyticsAdapter()
    _check(
        lifecycle.required_credential_keys() == ("meta_access_token",),
        "Only access token is required",
    )
    _check(
        lifecycle.validate_configuration({"api_version": "v25.0"}),
        "Configurable Graph version accepted",
    )
    _check(
        not lifecycle.validate_configuration({"api_version": "latest"}),
        "Ambiguous latest version rejected",
    )
    _check(
        not lifecycle.validate_configuration(
            {
                "api_version": "v25.0",
                "ad_account_id": "not-an-account",
            }
        ),
        "Malformed account id rejected",
    )
    _check(
        "ads_read" in lifecycle.owner_guidance().steps[0], "Guidance asks for ads_read"
    )
    _check(
        "ads_management" in lifecycle.owner_guidance().steps[2],
        "Guidance rejects write permission",
    )

    print("\nStep 2: provider control center requires token, cap and approval")
    controlled_secrets = MockSecretProvider()
    center = ProviderControlCenter(secret_provider=controlled_secrets)
    center.register_meta_ads(
        max_requests=1,
        execution_mode=ExecutionMode.REAL,
        api_version="v25.0",
        ad_account_id=_ACCOUNT_ID,
    )
    _check(
        center.snapshot("meta_marketing").status == "missing_credentials",
        "REAL profile starts without token",
    )
    center.set_secret("meta_marketing", "meta_access_token", _TOKEN)
    _check(
        center.snapshot("meta_marketing").status == "awaiting_owner_approval",
        "Token alone cannot enable REAL",
    )
    center.approve_provider("meta_marketing", True)
    controlled_snapshot = center.snapshot("meta_marketing")
    _check(
        controlled_snapshot.status == "real_ready",
        "Owner approval enables read-only REAL",
    )
    _check(controlled_snapshot.metadata["read_only"], "Panel marks provider read-only")
    _check(
        not controlled_snapshot.metadata["write_actions_available"],
        "Panel declares no write actions",
    )

    controlled_http = MockHttpClient(
        default_response=HttpResponse(status_code=200, body={"data": []})
    )
    controlled_adapter = MetaAdsAnalyticsAdapter()
    controlled_adapter.configure(
        {
            "api_version": "v25.0",
            "ad_account_id": _ACCOUNT_ID,
            "meta_access_token": "configured_via_secret_provider",
        }
    )
    controlled_adapter.authenticate()
    controlled_adapter.mark_ready()
    controlled_adapter.set_provider(provider)
    controlled_adapter.set_http_client(controlled_http)
    center.apply_to_meta_ads(controlled_adapter)
    first_controlled = controlled_adapter.execute(_request("list_ad_accounts"))
    second_controlled = controlled_adapter.execute(_request("get_permissions"))
    _check(first_controlled.success, "First approved read request succeeds")
    _check(not second_controlled.success, "Request cap blocks the second call")
    _check(
        second_controlled.output["blocked_by_budget"], "Request-cap block is explicit"
    )
    _check(len(controlled_http.sent_requests) == 1, "Budget block sends no HTTP")

    print("\nStep 3: list ad accounts without exposing token or paging URLs")
    list_http = MockHttpClient(
        default_response=HttpResponse(
            status_code=200,
            body={
                "data": [
                    {
                        "id": f"act_{_ACCOUNT_ID}",
                        "account_id": _ACCOUNT_ID,
                        "name": "Achados Baratos BR",
                        "account_status": 1,
                        "currency": "BRL",
                        "amount_spent": "0",
                    }
                ],
                "paging": {
                    "cursors": {"before": "before-demo", "after": "after-demo"},
                    "next": f"https://graph.facebook.com/page?access_token={_TOKEN}",
                },
            },
        )
    )
    list_adapter = _adapter(list_http)
    listed = list_adapter.execute(_request("list_ad_accounts", limit=25))
    _check(listed.success, "Account inventory succeeds")
    _check(listed.output["read_only"], "Result is marked read-only")
    _check(listed.output["count"] == 1, "One account returned")
    _check(listed.output["data"][0]["currency"] == "BRL", "Account currency preserved")
    _check(listed.output["paging"]["after"] == "after-demo", "Safe cursor preserved")
    _check(listed.output["paging"]["has_next"], "Next-page availability preserved")
    _check("next" not in listed.output["paging"], "Raw paging URL is not exposed")
    _check(_TOKEN not in str(listed), "Token is absent from normalized result")
    last = list_http.last_request()
    assert last is not None
    _check(last.method == HttpMethod.GET, "Inventory uses GET")
    _check(last.url.endswith("/v25.0/me/adaccounts"), "Versioned endpoint is used")
    _check(
        last.headers["Authorization"] == f"Bearer {_TOKEN}",
        "Token uses Authorization header",
    )
    _check("access_token" not in last.params, "Token is never a query parameter")
    _check(last.params["limit"] == "25", "Bounded limit is sent")

    print("\nStep 4: campaigns and insights use fixed field allowlists")
    campaign_http = MockHttpClient(
        default_response=HttpResponse(
            status_code=200,
            body={
                "data": [
                    {
                        "id": "120000000000001",
                        "name": "Campanha pausada",
                        "status": "PAUSED",
                        "effective_status": "PAUSED",
                        "objective": "OUTCOME_TRAFFIC",
                    }
                ]
            },
        )
    )
    campaigns = _adapter(campaign_http).execute(
        _request("list_campaigns", ad_account_id=_ACCOUNT_ID, limit=10)
    )
    _check(campaigns.success, "Campaign listing succeeds")
    campaign_request = campaign_http.last_request()
    assert campaign_request is not None
    _check(
        campaign_request.url.endswith(f"/v25.0/act_{_ACCOUNT_ID}/campaigns"),
        "Campaign endpoint is account-scoped",
    )
    _check(
        "daily_budget" in campaign_request.params["fields"], "Budget is read as a field"
    )
    _check(campaign_request.method == HttpMethod.GET, "Campaign operation remains GET")

    insight_http = MockHttpClient(
        default_response=HttpResponse(
            status_code=200,
            body={
                "data": [
                    {
                        "campaign_id": "120000000000001",
                        "campaign_name": "Campanha pausada",
                        "impressions": "1000",
                        "clicks": "30",
                        "spend": "25.00",
                        "ctr": "3.00",
                        "date_start": "2026-07-01",
                        "date_stop": "2026-07-07",
                    }
                ]
            },
        )
    )
    insights = _adapter(insight_http).execute(
        _request(
            "get_insights",
            ad_account_id=_ACCOUNT_ID,
            level="campaign",
            since="2026-07-01",
            until="2026-07-07",
        )
    )
    _check(insights.success, "Insights query succeeds")
    _check(
        insights.output["monetary_values_are_api_native"],
        "Money values are not guessed",
    )
    insight_request = insight_http.last_request()
    assert insight_request is not None
    _check(insight_request.method == HttpMethod.GET, "Insights operation remains GET")
    _check(
        insight_request.params["level"] == "campaign", "Insight level is allowlisted"
    )
    _check(
        insight_request.params["time_range"]
        == '{"since": "2026-07-01", "until": "2026-07-07"}',
        "Explicit date range is serialized",
    )
    _check("spend" in insight_request.params["fields"], "Spend metric requested")
    _check(
        "actions" in insight_request.params["fields"], "Conversion actions requested"
    )

    print("\nStep 5: invalid analytics requests stop before HTTP")
    validation_http = MockHttpClient()
    validator = _adapter(validation_http)
    invalid_level = validator.execute(
        _request(
            "get_insights",
            ad_account_id=_ACCOUNT_ID,
            level="business",
        )
    )
    invalid_dates = validator.execute(
        _request(
            "get_insights",
            ad_account_id=_ACCOUNT_ID,
            since="2026-07-10",
            until="2026-07-01",
        )
    )
    invalid_limit = validator.execute(_request("list_campaigns", limit=1000))
    missing_account = MetaAdsAnalyticsAdapter()
    missing_account.configure({"api_version": "v25.0"})
    missing = missing_account.execute(_request("list_campaigns"))
    _check(not invalid_level.success, "Unknown insight level rejected")
    _check(not invalid_dates.success, "Reverse date range rejected")
    _check(not invalid_limit.success, "Unbounded page size rejected")
    _check(not missing.success, "Missing account id rejected")
    _check(
        len(validation_http.sent_requests) == 0, "Invalid requests make no HTTP calls"
    )

    print("\nStep 6: every write or unknown action is blocked before HTTP")
    before = len(validation_http.sent_requests)
    blocked_actions = (
        "create_campaign",
        "update_budget",
        "pause_ad",
        "delete_campaign",
        "publish_ad",
        "unknown_action",
    )
    blocked = [validator.execute(_request(action)) for action in blocked_actions]
    _check(all(not item.success for item in blocked), "All write actions fail")
    _check(
        all(item.output["blocked_before_http"] for item in blocked),
        "Blocks are pre-HTTP",
    )
    _check(
        all(item.output["read_only"] for item in blocked),
        "Read-only policy is explicit",
    )
    _check(
        len(validation_http.sent_requests) == before,
        "Writes produce zero HTTP requests",
    )

    print("\nStep 7: Graph errors are normalized and redacted")
    error_http = MockHttpClient(
        default_response=HttpResponse(
            status_code=400,
            body={
                "error": {
                    "message": f"Invalid OAuth access token {_TOKEN}",
                    "type": "OAuthException",
                    "code": 190,
                    "error_subcode": 463,
                    "fbtrace_id": "trace-demo",
                    "access_token": _TOKEN,
                }
            },
        )
    )
    graph_error = _adapter(error_http).execute(_request("get_permissions"))
    _check(not graph_error.success, "Graph API error returns controlled failure")
    _check(graph_error.output["meta_error"]["code"] == 190, "Meta error code preserved")
    _check(
        "access_token" not in graph_error.output["meta_error"], "Token field removed"
    )
    _check(_TOKEN not in str(graph_error), "Token text is redacted from error")

    print(f"\n{'=' * 70}")
    print(f"All {_ASSERTION_COUNTER} assertions passed.")
    print("No Meta API call, campaign change, publication, or spend occurred.")
    print("=" * 70)


if __name__ == "__main__":
    main()
