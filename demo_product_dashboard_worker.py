"""Prove dashboard URL intake without affiliate fabrication or publication."""

from __future__ import annotations

from core.content_factory import ProductDashboardWorker, ProductUrlIntake
from core.content_factory.product_dashboard_worker import ProductDashboardWorkItem
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
    check("revisao_criativa_da_imagem" not in payload["missingFields"], "Official structured image needs no custom creative")
    check("Creative Review" in payload["analysisSummary"], "Worker does not pretend visual review happened")
    check("Produto físico detectado" in payload["promiseReview"], "Promise review is returned")
    check("Imagem encontrada" in payload["creativeRecommendation"], "Creative recommendation is returned")
    check("Sem link afiliado" in payload["commissionNotes"], "Commission readiness is explicit")
    check("Telegram/WhatsApp" in payload["funnelSuggestion"], "No-spend funnel is suggested")
    check("AffiliateCommerceWorkflow" in payload["affiliateReadiness"], "Affiliate workflow readiness is named")
    check(payload["affiliateLinkVerified"] is False, "Missing affiliate link is never treated as verified")
    check(payload["officialImageVerified"] is True, "Structured HTTPS product image is verified as official preview")
    check(payload["availabilityState"] == "in_stock", "Structured availability is normalized")
    check("secret" not in str(payload), "Credential is absent from result payload")
    check(all("publish" not in request.url for request in client.requests), "No publication endpoint is called")

    missing = worker.run_once(intake, token="", enabled=True)
    check(missing.skipped_reason == "missing_token", "Missing token blocks polling")
    check(len(client.requests) == 3, "Missing token adds no request")

    official_item = ProductDashboardWorkItem(
        request_id="request-2",
        product_url="https://meli.la/example",
        affiliate_url="https://meli.la/1pJ1S7s",
        marketplace="Mercado Livre",
        channel_registered=True,
    )
    check(worker._official_affiliate_link(official_item), "Official Mercado Livre short link is verified")
    check(not worker._official_affiliate_link(ProductDashboardWorkItem(
        request_id="request-3",
        product_url="https://example.com/product",
        affiliate_url="https://example.com/tracker",
        marketplace="Mercado Livre",
    )), "Third-party link cannot impersonate an official affiliate link")
    check(worker._availability_state("OutOfStock") == "out_of_stock", "Out-of-stock state is normalized")

    monetized_url = "https://meli.la/1pJ1S7s"
    official_queue = HttpResponse(status_code=200, body={"items": [{
        "id": "request-4",
        "productUrl": monetized_url,
        "affiliateUrl": monetized_url,
        "marketplace": "Mercado Livre",
        "status": "queued",
        "targetChannel": "telegram_public",
        "channelRegistered": True,
    }]})
    official_html = HttpResponse(status_code=200, body="""
      <html><head><script type="application/ld+json">{
        "@type":"Product","name":"Kit duas câmeras Wi-Fi",
        "image":"https://http2.mlstatic.com/cameras.jpg",
        "offers":{"@type":"Offer","price":"307.74","priceCurrency":"BRL","availability":"InStock"}
      }</script></head></html>
    """)
    official_accepted = HttpResponse(status_code=202, body={"accepted": True})
    official_client = SequenceClient((official_queue, official_html, official_accepted))
    official_worker = ProductDashboardWorker(official_client, endpoint)
    official_intake = ProductUrlIntake(official_client, clock=lambda: 1_783_938_600.0)
    official_result = official_worker.run_once(official_intake, token="secret", enabled=True)
    check(official_result.submitted == 1, "Verified Mercado Livre result returns to dashboard")
    official_payload = official_client.requests[2].body
    check(official_payload["status"] == "completed", "Verified offer clears deterministic intake gates")
    check(official_payload["affiliateLinkVerified"] is True, "Official meli.la link is ready for commission tracking")
    check(official_payload["officialImageVerified"] is True, "Marketplace image is ready for official link preview")
    check(official_payload["availabilityState"] == "in_stock", "Available offer is eligible for packaging")
    check(official_payload["missingFields"] == [], "Verified offer has no fabricated manual blockers")
    print(f"All {COUNT} assertions passed.")


if __name__ == "__main__":
    main()
