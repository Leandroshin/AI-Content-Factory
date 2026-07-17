"""Prove second HITL gate -> MOCK media plans -> owner review."""

from __future__ import annotations

from core.content_factory import DashboardMediaProductionWorker
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
    endpoint = "https://central.example.com/api/intake/media-production"
    queue = HttpResponse(status_code=200, body={"items": [{
        "opportunityId": "gaming-news",
        "title": "Atualização oficial confirmada",
        "channel": "Fase Nova Games",
        "category": "Notícia",
        "hook": "A atualização acaba de ser confirmada.",
        "script": "A publicadora confirmou um novo mapa para esta semana.",
        "callToAction": "Acompanhe a próxima atualização verificada.",
        "assetPlan": ["Abrir com a fonte oficial.", "Usar gameplay autorizado."],
        "sources": [{"label": "Fonte oficial", "url": "https://games.example.com/news"}],
        "mode": "MOCK",
    }]})
    client = SequenceClient((queue, HttpResponse(status_code=202, body={"accepted": True})))
    worker = DashboardMediaProductionWorker(client, endpoint)

    check(worker.run_once(token="secret").skipped_reason == "worker_disabled", "Worker defaults disabled")
    check(not client.requests, "Disabled worker performs no HTTP")
    result = worker.run_once(token="secret", enabled=True, site_access_token="site-secret")
    check(result.received == 1, "One approved script is received")
    check(result.submitted == 1 and result.failed == 0, "Media plan returns to dashboard")
    check(result.opportunity_ids == ("gaming-news",), "Opportunity identity is preserved")
    check(len(client.requests) == 2, "Only queue and result endpoints are called")
    check(client.requests[0].method.value == "GET" and client.requests[1].method.value == "POST", "Queue and delivery use bounded methods")
    check(client.requests[0].headers["Authorization"] == "Bearer secret", "Queue is authenticated")
    check(client.requests[0].headers["OAI-Sites-Authorization"] == "Bearer site-secret", "Private Site is authenticated")
    payload = client.requests[1].body
    check(payload["status"] == "media_review", "Successful pre-production returns for review")
    check(set(payload["departments"]) == {"audio", "image", "video"}, "Three concrete departments return plans")
    check(all(part["status"] == "planned" for part in payload["departments"].values()), "Every department plan is explicit")
    check(payload["qualityPassed"] is True, "Plan quality gate passes")
    check(payload["providerStatus"] == "not_called", "No provider is called")
    check(payload["finalAssetStatus"] == "not_generated", "No final asset is claimed")
    check(payload["publicationStatus"] == "blocked", "Publication remains blocked")
    check("secret" not in str(payload), "Credentials never enter the result")
    check(all(request.url == endpoint for request in client.requests), "No external provider or publication endpoint is contacted")
    print(f"All {COUNT} assertions passed.")


if __name__ == "__main__":
    main()
