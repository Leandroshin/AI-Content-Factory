"""Mercado Livre catalog adapter demonstration without external API calls."""

from __future__ import annotations

from uuid import uuid4

from core.tools.adapters import ExecutionMode, MercadoLivreCatalogAdapter, ToolRequest
from core.tools.http import HttpMethod, HttpResponse, MockHttpClient
from core.tools.provider_settings import ProviderControlCenter
from core.tools.providers import MercadoLivreProvider
from core.tools.secrets import MockSecretProvider, SecretKey

_ASSERTION_COUNTER = 0
_TOKEN = "test_mercado_livre_access_token_read_only"


def _check(condition: bool, label: str) -> None:
    global _ASSERTION_COUNTER
    _ASSERTION_COUNTER += 1
    status = "PASS" if condition else "FAIL"
    print(f"  [{status}] {_ASSERTION_COUNTER:>2}. {label}")
    if not condition:
        raise AssertionError(label)


def _request(action: str, **params: object) -> ToolRequest:
    return ToolRequest(tool_id=uuid4(), capability="web_search", params={"action": action, **params})


def _adapter(http: MockHttpClient) -> MercadoLivreCatalogAdapter:
    secrets = MockSecretProvider()
    secrets.set(SecretKey(key="mercado_livre_access_token", provider="mercado_livre"), _TOKEN)
    adapter = MercadoLivreCatalogAdapter()
    adapter.configure({"site_id": "MLB", "mercado_livre_access_token": "configured_via_secret_provider"})
    adapter.authenticate()
    adapter.mark_ready()
    adapter.set_execution_mode(ExecutionMode.REAL)
    adapter.set_secret_provider(secrets)
    adapter.set_provider(MercadoLivreProvider())
    adapter.set_http_client(http)
    return adapter


def main() -> None:
    print("=" * 70)
    print("Mercado Livre Catalog - Strictly Read Only")
    print("=" * 70)

    provider = MercadoLivreProvider()
    _check(provider.provider_id == "mercado_livre", "Provider id is stable")
    _check(provider.base_url == "https://api.mercadolibre.com", "Official API host configured")
    _check(provider.auth_type == "oauth_bearer", "OAuth bearer is explicit")

    lifecycle = MercadoLivreCatalogAdapter()
    _check(lifecycle.validate_configuration({"site_id": "MLB"}), "Brazilian site id accepted")
    _check(not lifecycle.validate_configuration({"site_id": "br"}), "Malformed site id rejected")
    _check(lifecycle.required_credential_keys() == ("mercado_livre_access_token",), "Only OAuth access token is required at runtime")
    _check("bloqueados" in lifecycle.owner_guidance().notes, "Guidance declares write blocks")

    secrets = MockSecretProvider()
    center = ProviderControlCenter(secret_provider=secrets)
    center.register_mercado_livre(max_requests=1, execution_mode=ExecutionMode.REAL)
    _check(center.snapshot("mercado_livre").status == "missing_credentials", "REAL starts without token")
    center.set_secret("mercado_livre", "mercado_livre_access_token", _TOKEN)
    _check(center.snapshot("mercado_livre").status == "awaiting_owner_approval", "Token alone cannot enable REAL")
    center.approve_provider("mercado_livre", True)
    snapshot = center.snapshot("mercado_livre")
    _check(snapshot.status == "real_ready", "Owner approval enables bounded reads")
    _check(snapshot.metadata["read_only"], "Control panel marks provider read-only")
    _check(not snapshot.metadata["write_actions_available"], "Control panel exposes no writes")

    controlled_http = MockHttpClient(default_response=HttpResponse(status_code=200, body={"id": "MLB1234567890"}))
    controlled = MercadoLivreCatalogAdapter()
    controlled.configure({"site_id": "MLB", "mercado_livre_access_token": "configured_via_secret_provider"})
    controlled.authenticate()
    controlled.mark_ready()
    controlled.set_provider(provider)
    controlled.set_http_client(controlled_http)
    center.apply_to_mercado_livre(controlled)
    first = controlled.execute(_request("get_item", item_id="MLB1234567890"))
    second = controlled.execute(_request("get_category", category_id="MLB1055"))
    _check(first.success, "First approved read succeeds")
    _check(not second.success and second.output["blocked_by_budget"], "Request cap blocks the second read")
    _check(len(controlled_http.sent_requests) == 1, "Budget block sends no HTTP")

    item_http = MockHttpClient(default_response=HttpResponse(status_code=200, body={
        "id": "MLB1234567890", "title": "Controle sem fio", "price": 299.9,
        "permalink": "https://produto.mercadolivre.com.br/MLB1234567890",
        "access_token": _TOKEN,
    }))
    item = _adapter(item_http).execute(_request("get_item", item_id="MLB1234567890"))
    _check(item.success and item.output["read_only"], "Item detail is explicitly read-only")
    _check(item.output["data"]["title"] == "Controle sem fio", "Catalog fields are preserved")
    _check("access_token" not in item.output["data"], "Token-shaped fields are removed")
    _check(_TOKEN not in str(item), "Raw token is absent from normalized output")
    last = item_http.last_request()
    assert last is not None
    _check(last.method == HttpMethod.GET, "Item detail uses GET")
    _check(last.url.endswith("/items/MLB1234567890"), "Item endpoint is allowlisted")
    _check(last.headers["Authorization"] == f"Bearer {_TOKEN}", "Token stays in Authorization header")
    _check("access_token" not in last.params, "Token is not a query parameter")
    _check("permalink" in last.params["attributes"], "Fixed field allowlist is requested")

    search_http = MockHttpClient(default_response=HttpResponse(status_code=200, body={"paging": {"total": 1}, "results": [{"id": "MLB1234567890"}]}))
    searched = _adapter(search_http).execute(_request("search_items", query="controle sem fio", category_id="MLB1055", limit=20, offset=0))
    _check(searched.success, "Bounded catalog search succeeds")
    search_request = search_http.last_request()
    assert search_request is not None
    _check(search_request.method == HttpMethod.GET, "Catalog search uses GET")
    _check(search_request.url.endswith("/sites/MLB/search"), "Search stays on Brazilian site")
    _check(search_request.params["q"] == "controle sem fio", "Query is preserved")
    _check(search_request.params["limit"] == "20", "Page size is bounded")
    _check(search_request.params["category"] == "MLB1055", "Category filter is validated")

    invalid_http = MockHttpClient()
    validator = _adapter(invalid_http)
    invalid = (
        validator.execute(_request("get_item", item_id="123")),
        validator.execute(_request("search_items", query="x")),
        validator.execute(_request("search_items", query="controle", limit=500)),
        validator.execute(_request("multiget_items", item_ids=["MLB1234567890"] * 21)),
    )
    _check(all(not result.success for result in invalid), "Malformed and unbounded reads fail")
    _check(len(invalid_http.sent_requests) == 0, "Invalid reads stop before HTTP")

    writes = ("create_item", "update_item", "pause_item", "answer_question", "buy", "delete_item", "unknown")
    blocked = [validator.execute(_request(action)) for action in writes]
    _check(all(not result.success for result in blocked), "Every write or unknown action fails")
    _check(all(result.output["blocked_before_http"] for result in blocked), "All write blocks happen pre-HTTP")
    _check(all(result.output["read_only"] for result in blocked), "Read-only policy is visible in every block")
    _check(len(invalid_http.sent_requests) == 0, "Writes produce zero HTTP requests")

    print(f"\n{'=' * 70}")
    print(f"All {_ASSERTION_COUNTER} assertions passed.")
    print("No Mercado Livre publication, message, sale, purchase, or account change occurred.")
    print("=" * 70)


if __name__ == "__main__":
    main()
