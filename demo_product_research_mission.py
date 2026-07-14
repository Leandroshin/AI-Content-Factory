"""Product discovery mission demonstration without external calls or publication."""

from core.content_factory.product_research_mission import ProductResearchMission, ProductResearchMissionWorker
from core.tools.adapters.models import AdapterExecutionResult


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

_ASSERTIONS = 0


def check(value: bool, label: str) -> None:
    global _ASSERTIONS
    _ASSERTIONS += 1
    if not value:
        raise AssertionError(label)
    print(f"  [PASS] {_ASSERTIONS:>2}. {label}")


def main() -> None:
    adapter = MockCatalogAdapter()
    worker = ProductResearchMissionWorker(adapter)

    result = worker.run(ProductResearchMission(
        goal="controle sem fio",
        result_limit=3,
        max_price=500.0,
        target_channel="telegram_public",
    ))
    check(result.status == "review", "MOCK catalog reaches owner review")
    check(result.publication_status == "blocked", "Publication remains blocked")
    check(result.provider_status == "not_called", "No paid provider is called")
    check(result.affiliate_links_status == "owner_confirmation_required", "Affiliate link must be confirmed")
    check(result.report["total_candidates"] == 1, "Catalog candidate reaches Product Research")
    check(len(result.report["shortlisted"]) == 1, "Product Research returns a visual shortlist candidate")
    candidate = result.report["shortlisted"][0]
    check(candidate["marketplace"] == "Mercado Livre", "Marketplace provenance is preserved")
    check(candidate["affiliate_url"] == "", "Worker never fabricates an affiliate URL")
    check(candidate["metadata"]["read_only"], "Candidate records read-only evidence")
    check("affiliate_url_missing" in candidate["reasons"], "Missing monetization is explicit")

    invalid = worker.run(ProductResearchMission(goal="x", result_limit=50))
    check(invalid.status == "blocked", "Invalid unbounded mission is rejected")
    unsupported = worker.run(ProductResearchMission(goal="cafeteira", marketplace="amazon"))
    check(unsupported.status == "needs_input", "Unconnected marketplace stays pending")
    check(unsupported.publication_status == "blocked", "Unsupported marketplace cannot publish")
    print(f"\nAll {_ASSERTIONS} assertions passed.")
    print("No product was published, purchased, advertised, or monetized.")


if __name__ == "__main__":
    main()
