"""Prove approval -> MOCK Script Department draft -> owner review."""

from __future__ import annotations

from core.content_factory import DashboardProductionWorker
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
    endpoint = "https://central.example.com/api/intake/production"
    queue = HttpResponse(status_code=200, body={"items": [{
        "id": "production-gaming-news",
        "opportunityId": "gaming-news",
        "title": "Atualização oficial do jogo confirmada",
        "summary": "A publicadora confirmou um novo mapa e lançamento nesta semana.",
        "channel": "Fase Nova Games",
        "category": "Notícia",
        "mode": "MOCK",
        "sources": [{"label": "Sala de notícias oficial", "url": "https://games.example.com/news"}],
    }]})
    accepted = HttpResponse(status_code=202, body={"accepted": True})
    client = SequenceClient((queue, accepted))
    worker = DashboardProductionWorker(client, endpoint)

    disabled = worker.run_once(token="secret", enabled=False)
    check(disabled.skipped_reason == "worker_disabled", "Worker defaults disabled")
    check(len(client.requests) == 0, "Disabled worker performs no HTTP")

    result = worker.run_once(token="secret", enabled=True, site_access_token="sites-secret")
    check(result.received == 1, "One approved request is received")
    check(result.submitted == 1 and result.failed == 0, "Draft returns to dashboard")
    check(result.opportunity_ids == ("gaming-news",), "Opportunity identity is preserved")
    check(len(client.requests) == 2, "Only queue and result endpoints are called")
    check(client.requests[0].method.value == "GET", "Queue uses GET")
    check(client.requests[1].method.value == "POST", "Draft uses POST")
    check(client.requests[0].headers["Authorization"] == "Bearer secret", "Queue is authenticated")
    check(client.requests[0].headers["OAI-Sites-Authorization"] == "Bearer sites-secret", "Private Sites access is authenticated")
    payload = client.requests[1].body
    check(payload["status"] == "review", "Successful draft returns for review")
    check(payload["opportunityId"] == "gaming-news", "Result targets approved opportunity")
    check(payload["hook"].strip() != "", "Script Department creates a hook")
    check("publicadora confirmou" in payload["script"].lower(), "Draft preserves supplied evidence")
    check("HOOK:" not in payload["script"] and "CTA:" not in payload["script"], "Displayed body does not duplicate labels")
    check(payload["callToAction"].strip() != "", "Draft contains a CTA")
    check(len(payload["assetPlan"]) >= 3, "Visual plan is included")
    check("MOCK" in payload["reviewNotes"], "MOCK mode is explicit")
    check("secret" not in str(payload), "Credential is absent from payload")
    check(all("publish" not in request.url for request in client.requests), "No publication endpoint is called")
    check(all("audio" not in request.url for request in client.requests), "No audio provider is called")
    check(all("video" not in request.url for request in client.requests), "No video provider is called")
    monitor = worker._produce(worker._coerce_item({
        "opportunityId": "daily-radar",
        "title": "Radar diário de GTA 6 e lançamentos",
        "summary": "Monitorar fontes oficiais e produzir somente quando houver novidade.",
        "channel": "Fase Nova Games",
        "category": "Notícia",
        "mode": "MOCK",
        "sources": [{"label": "Oficial", "url": "https://example.com/news"}],
    }))
    check(monitor["status"] == "failed" and "notícia concreta" in monitor["reviewNotes"], "Empty monitoring routines fail the quality gate")
    incomplete_offer = worker._produce(worker._coerce_item({
        "opportunityId": "offer-without-link",
        "title": "Controle em promoção",
        "summary": "O link afiliado ainda precisa ser validado.",
        "channel": "Achados Baratos BR",
        "category": "Oferta",
        "mode": "MOCK",
        "sources": [{"label": "Amazon", "url": "https://www.amazon.com.br/"}],
    }))
    check(incomplete_offer["status"] == "failed" and "Oferta incompleta" in incomplete_offer["reviewNotes"], "Incomplete offers fail before copywriting")
    print(f"All {COUNT} assertions passed.")


if __name__ == "__main__":
    main()
