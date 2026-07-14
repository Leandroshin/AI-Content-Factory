"""Hosted product research queue bridge demonstration."""

from core.content_factory.product_research_dashboard_worker import ProductResearchDashboardWorker
from core.content_factory.product_research_mission import ProductResearchMissionWorker
from core.tools.adapters.models import AdapterExecutionResult
from core.tools.http import HttpMethod, HttpResponse, MockHttpClient

_COUNT = 0


class MockCatalogAdapter:
    def execute(self, request):
        return AdapterExecutionResult(success=True, summary="MOCK read", output={
            "data": {"results": [{
                "id": "MLB1234567890", "title": "Controle sem fio", "price": 299.9,
                "original_price": 399.9, "permalink": "https://produto.mercadolivre.com.br/MLB1234567890",
                "thumbnail": "https://http2.mlstatic.com/mock.jpg", "sold_quantity": 120,
                "available_quantity": 50, "category_id": "MLB1055",
            }]}, "read_only": True, "_mock": True,
        })


def check(value: bool, label: str) -> None:
    global _COUNT
    _COUNT += 1
    if not value:
        raise AssertionError(label)
    print(f"  [PASS] {_COUNT:>2}. {label}")


def main() -> None:
    endpoint = "https://central-ai-content-factory.example/api/intake/product-research"
    queue = {
        "missions": [{
            "id": "a7ce3c70-87a5-45c9-a949-4fd7cf523da1",
            "goal": "controle sem fio",
            "marketplaces": ["mercado_livre"],
            "category": "",
            "maxPrice": 500,
            "resultLimit": 5,
            "targetChannel": "telegram_public",
            "timeframe": "week",
        }],
    }
    class RouteMockHttpClient(MockHttpClient):
        def send(self, request):
            self._sent_requests.append(request)
            if request.method == HttpMethod.GET:
                return HttpResponse(status_code=200, body=queue)
            return HttpResponse(status_code=202, body={"accepted": True})

    http = RouteMockHttpClient()
    adapter = MockCatalogAdapter()
    result = ProductResearchDashboardWorker(http, endpoint).run_once(
        ProductResearchMissionWorker(adapter), token="dashboard-secret-token", enabled=True,
    )
    check(result.received == 1, "One hosted mission is received")
    check(result.submitted == 1 and result.failed == 0, "One research report is returned")
    check(len(http.sent_requests) == 2, "Bridge performs one queue read and one result write")
    payload = http.sent_requests[1].body
    check(payload["status"] == "review", "Mission stops at owner review")
    check(payload["report"]["shortlisted"], "Shortlist is delivered to the dashboard")
    check(payload["report"]["shortlisted"][0]["affiliate_url"] == "", "No affiliate link is fabricated")
    check(http.sent_requests[0].headers["Authorization"] == "Bearer dashboard-secret-token", "Intake token is sent in a header")
    disabled_http = MockHttpClient()
    disabled = ProductResearchDashboardWorker(disabled_http, endpoint).run_once(
        ProductResearchMissionWorker(adapter), token="dashboard-secret-token", enabled=False,
    )
    check(disabled.skipped_reason == "worker_disabled", "Worker is opt-in")
    check(not disabled_http.sent_requests, "Disabled worker sends no request")
    print(f"\nAll {_COUNT} assertions passed.")
    print("Publication and paid providers remained blocked.")


if __name__ == "__main__":
    main()
