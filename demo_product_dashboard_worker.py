"""Prove dashboard URL intake without affiliate fabrication or publication."""

from __future__ import annotations

from core.content_factory import ProductDashboardWorker, ProductUrlIntake
from core.tools.http import HttpClient, HttpRequest, HttpResponse


COUNT = 0


def check(condition: bool, label: str) -> None:
    global COUNT
    COUNT += 1
    if not condition:
        raise AssertionError(label)


class SequenceClient(HttpClient):
    def __init__(self, responses: tuple[HttpResponse, ...]) -> None:
        super().__init__()
        self.responses = list(responses)
        self.requests: list[HttpRequest] = []

    def send(self, request: HttpRequest) -> HttpResponse:
        self.requests.append(request)
        if not self.responses:
            raise AssertionError("Unexpected HTTP request")
        return self.responses.pop(0)


def main() -> None:
    endpoint = "https://central.example.com/api/intake/products"
    product_url = "https://www.amazon.com.br/dp/example"
    queue = HttpResponse(status_code=200, body={"items": [{
        "id": "request-1",
        "productUrl": product_url,
        "affiliateUrl": "",
        "marketplace": "Amazon Brasil",
        "status": "queued",
        "evidenceUrl": "https://example.com/review",
        "language": "pt-BR",
        "sourceKind": "product_page",
        "ownerNotes": "Oferta vista em grupo de cupons; validar imagem e rastreamento.",
    }]})
    html = HttpResponse(status_code=200, body="""
      <html><head><script type="application/ld+json">{
        "@type":"Product","name":"Controle Gamer Pro","image":"https://images.example.com/controller.jpg",
        "offers":{"@type":"Offer","price":"299.90","priceCurrency":"BRL","availability":"InStock"}
      }</script></head></html>
    """)
    accepted = HttpResponse(status_code=202, body={"accepted": True})
    client = SequenceClient((queue, html, accepted))
    worker = ProductDashboardWorker(client, endpoint)
    intake = ProductUrlIntake(client, clock=lambda: 1_783_938_600.0)

    disabled = worker.run_once(intake, token="secret", enabled=False)
    check(disabled.skipped_reason == "worker_disabled", "Worker defaults disabled")
    check(len(client.requests) == 0, "Disabled worker performs no HTTP")

    result = worker.run_once(intake, token="secret", enabled=True, site_access_token="sites-secret")
    check(result.received == 1, "One dashboard request is received")
    check(result.submitted == 1 and result.failed == 0, "Evidence result returns to dashboard")
    check(result.request_ids == ("request-1",), "Processed request remains auditable")
    check(len(client.requests) == 3, "Only queue, product, and result requests occur")
    check(client.requests[0].url == endpoint, "Worker polls exact endpoint")
    check(client.requests[0].headers["Authorization"] == "Bearer secret", "Queue uses bearer auth")
    check(client.requests[0].headers["OAI-Sites-Authorization"] == "Bearer sites-secret", "Private Sites access is authenticated")
    check(client.requests[1].url == product_url, "Owner product URL is collected once")
    check(client.requests[2].url == endpoint, "Result returns to exact endpoint")
    payload = client.requests[2].body
    check(payload["requestId"] == "request-1", "Request identity is preserved")
    check(payload["title"] == "Controle Gamer Pro", "Structured product name is extracted")
    check(payload["imageUrl"].startswith("https://"), "Structured image is preserved")
    check(payload["currentPrice"] == 299.90, "Collected current price is returned as structured data")
    check(payload["oldPrice"] is None, "Absent previous price remains explicit")
    check(payload["status"] == "needs_input", "Item waits for remaining gates")
    check("link_afiliado" in payload["missingFields"], "Missing affiliate link is explicit")
    check("revisao_criativa_da_imagem" in payload["missingFields"], "Creative image review remains pending")
    check("Creative Review" in payload["analysisSummary"], "Worker does not pretend visual review happened")
    check("Produto físico detectado" in payload["promiseReview"], "Promise review is returned")
    check("Imagem encontrada" in payload["creativeRecommendation"], "Creative recommendation is returned")
    check("Sem link afiliado" in payload["commissionNotes"], "Commission readiness is explicit")
    check("Telegram/WhatsApp" in payload["funnelSuggestion"], "No-spend funnel is suggested")
    check("AffiliateCommerceWorkflow" in payload["affiliateReadiness"], "Affiliate workflow readiness is named")
    check("secret" not in str(payload), "Credential is absent from result payload")
    check(all("publish" not in request.url for request in client.requests), "No publication endpoint is called")

    missing = worker.run_once(intake, token="", enabled=True)
    check(missing.skipped_reason == "missing_token", "Missing token blocks polling")
    check(len(client.requests) == 3, "Missing token adds no request")
    print(f"All {COUNT} assertions passed.")


if __name__ == "__main__":
    main()
