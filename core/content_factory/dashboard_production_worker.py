"""Produce review-only script drafts for approved dashboard opportunities."""

from __future__ import annotations

from dataclasses import dataclass, field
import re
from typing import Any
from urllib.parse import urlsplit
from uuid import uuid4

from core.company.specialist_employee import EmployeeSkill, ReceivedTask, TaskDecision
from core.departments.script.employee import ScriptWriterEmployee
from core.events.bus import EventBus
from core.runtime import CompanyRuntime
from core.tools.http.client import HttpClient
from core.tools.http.errors import HttpError


@dataclass(frozen=True, slots=True)
class DashboardProductionItem:
    opportunity_id: str
    title: str
    summary: str
    channel: str
    category: str
    sources: tuple[dict[str, str], ...] = field(default_factory=tuple)


@dataclass(frozen=True, slots=True)
class DashboardProductionResult:
    skipped_reason: str = ""
    received: int = 0
    submitted: int = 0
    failed: int = 0
    opportunity_ids: tuple[str, ...] = field(default_factory=tuple)


class DashboardProductionWorker:
    """Run Script Department in MOCK and return drafts without rendering or publishing."""

    def __init__(self, client: HttpClient, endpoint: str) -> None:
        endpoint = endpoint.strip()
        if not endpoint.startswith("https://") or not endpoint.endswith("/api/intake/production"):
            raise ValueError("Production worker endpoint must be the public HTTPS intake route.")
        self._client = client
        self._endpoint = endpoint

    def run_once(
        self,
        *,
        token: str,
        enabled: bool = False,
        site_access_token: str = "",
    ) -> DashboardProductionResult:
        if not enabled:
            return DashboardProductionResult(skipped_reason="worker_disabled")
        if not token.strip():
            return DashboardProductionResult(skipped_reason="missing_token")
        try:
            response = self._client.get(
                self._endpoint,
                headers=self._headers(token, site_access_token=site_access_token),
            )
        except HttpError:
            return DashboardProductionResult(skipped_reason="queue_unavailable")
        if response.status_code != 200 or not isinstance(response.body, dict):
            return DashboardProductionResult(skipped_reason="invalid_queue_response")

        items = tuple(self._coerce_item(value) for value in response.body.get("items", ()))
        items = tuple(item for item in items if item is not None)
        if not items:
            return DashboardProductionResult(skipped_reason="queue_empty")

        submitted = 0
        failed = 0
        accepted_ids: list[str] = []
        for item in items:
            payload = self._produce(item)
            try:
                delivery = self._client.post(
                    self._endpoint,
                    headers=self._headers(
                        token,
                        site_access_token=site_access_token,
                        include_content_type=True,
                    ),
                    body=payload,
                )
            except HttpError:
                failed += 1
                continue
            if delivery.status_code == 202:
                submitted += 1
                accepted_ids.append(item.opportunity_id)
            else:
                failed += 1
        return DashboardProductionResult(
            received=len(items),
            submitted=submitted,
            failed=failed,
            opportunity_ids=tuple(accepted_ids),
        )

    @staticmethod
    def _headers(
        token: str,
        *,
        site_access_token: str,
        include_content_type: bool = False,
    ) -> dict[str, str]:
        headers = {"Authorization": f"Bearer {token}"}
        if site_access_token.strip():
            headers["OAI-Sites-Authorization"] = f"Bearer {site_access_token.strip()}"
        if include_content_type:
            headers["Content-Type"] = "application/json"
        return headers

    @staticmethod
    def _coerce_item(value: Any) -> DashboardProductionItem | None:
        if not isinstance(value, dict) or value.get("mode") != "MOCK":
            return None
        opportunity_id = str(value.get("opportunityId", "")).strip()
        title = str(value.get("title", "")).strip()
        if not opportunity_id or not title:
            return None
        sources = tuple(
            {"label": str(source.get("label", "")), "url": str(source.get("url", ""))}
            for source in value.get("sources", ())
            if isinstance(source, dict) and str(source.get("url", "")).startswith("https://")
        )
        return DashboardProductionItem(
            opportunity_id=opportunity_id,
            title=title,
            summary=str(value.get("summary", "")).strip(),
            channel=str(value.get("channel", "")).strip(),
            category=str(value.get("category", "")).strip(),
            sources=sources,
        )

    def _produce(self, item: DashboardProductionItem) -> dict[str, Any]:
        if self._is_monitoring_instruction(item):
            return self._failed(
                item,
                "A pauta descreve uma rotina de monitoramento, mas não contém uma notícia concreta. Aguarde o radar encontrar um fato novo antes de produzir.",
            )
        if self._is_incomplete_offer(item):
            return self._failed(
                item,
                "Oferta incompleta: falta uma página específica do produto e/ou um link de afiliado validado. Cole esses dados em Produtos antes de produzir o anúncio.",
            )
        event_bus = EventBus()
        company = CompanyRuntime(event_bus)
        company.initialize_company()
        writer = ScriptWriterEmployee(
            company_runtime=company,
            employee_id=uuid4(),
            skills=(
                EmployeeSkill(name="text_generation", proficiency=0.95),
                EmployeeSkill(name="document_generation", proficiency=0.90),
                EmployeeSkill(name="storytelling", proficiency=0.90),
            ),
            event_bus=event_bus,
        )
        hook = self._hook(item)
        cta = self._cta(item)
        task = ReceivedTask(
            task_id=uuid4(),
            title=f"Dashboard draft: {item.title}",
            description="Prepare a sourced review draft without audio, rendering, spending, or publication.",
            department="Script Production",
            required_skills=("text_generation", "document_generation"),
            context={
                "script_type": "shorts",
                "duration_seconds": 45,
                "brief": {
                    "topic": item.title,
                    "objective": "Preparar um primeiro rascunho fiel às evidências para revisão do owner.",
                    "target_audience": "público brasileiro interessado no canal",
                    "tone": "direto e informativo",
                    "language": "pt-BR",
                    "platform": "tiktok_youtube_shorts",
                    "key_points": (item.summary,),
                },
                "sections": (
                    {"name": "hook", "purpose": "Interromper o scroll sem exagero", "target_duration_seconds": 5, "content": hook, "order": 1},
                    {"name": "body", "purpose": "Explicar somente o que as fontes sustentam", "target_duration_seconds": 32, "content": item.summary, "order": 2},
                    {"name": "cta", "purpose": "Encerrar sem promessa enganosa", "target_duration_seconds": 8, "content": cta, "order": 3},
                ),
                "hooks": ({"text": hook, "style": "direct", "retention_score": 0.82},),
                "cta": {"text": cta, "action_type": "engagement", "placement": "end"},
                "variants": ({"name": "informativa", "angle": "evidence_first"},),
                "export_profile": {"format": "markdown", "language": "pt-BR", "platform_template": "shorts", "include_timestamps": True},
                "source_count": len(item.sources),
            },
        )
        if writer.receive_task(task) is not TaskDecision.ACCEPTED:
            return self._failed(item, "O Script Department recusou a pauta.")
        result = writer.execute_task(task.task_id)
        if not result.success:
            return self._failed(item, result.error or "O Script Department não concluiu o rascunho.")
        output = dict(result.output)
        script = self._body_from_script(str(output.get("script_text", "")), fallback=item.summary)
        if not script:
            return self._failed(item, "O rascunho foi concluído sem texto utilizável.")
        return {
            "opportunityId": item.opportunity_id,
            "status": "review",
            "hook": str(output.get("hook", hook)).strip(),
            "script": script,
            "callToAction": str(output.get("call_to_action", cta)).strip(),
            "assetPlan": self._asset_plan(item),
            "reviewNotes": "Primeiro rascunho produzido pelo Script Department em modo MOCK. Confira fatos, tom e plano visual antes de liberar áudio ou vídeo.",
        }

    @staticmethod
    def _body_from_script(script: str, *, fallback: str) -> str:
        bodies = re.findall(
            r"(?:^|\n)BODY:\s*(.+?)(?=\n(?:HOOK|CTA):|\Z)",
            script.strip(),
            flags=re.IGNORECASE | re.DOTALL,
        )
        cleaned = " ".join(" ".join(body.split()) for body in bodies if body.strip()).strip()
        return cleaned or fallback.strip()

    @staticmethod
    def _is_monitoring_instruction(item: DashboardProductionItem) -> bool:
        title = item.title.casefold()
        summary = item.summary.casefold()
        return title.startswith("radar diário") or (
            "monitorar fontes" in summary
            and "quando houver novidade" in summary
        )

    @staticmethod
    def _is_incomplete_offer(item: DashboardProductionItem) -> bool:
        category = item.category.casefold()
        if "oferta" not in category and "produto" not in category:
            return False
        summary = item.summary.casefold()
        affiliate_missing = "link afiliado" in summary and any(
            marker in summary for marker in ("ainda", "precisa", "pendente", "falt")
        )
        has_specific_page = any(
            urlsplit(source.get("url", "")).path.strip("/")
            for source in item.sources
        )
        return affiliate_missing or not has_specific_page

    @staticmethod
    def _hook(item: DashboardProductionItem) -> str:
        if "oferta" in item.category.lower() or "produto" in item.category.lower():
            return f"Vale a pena olhar esta oferta antes que o preço mude: {item.title}."
        return f"Isto acabou de entrar no radar: {item.title}."

    @staticmethod
    def _cta(item: DashboardProductionItem) -> str:
        return "Acompanhe o canal para receber a próxima atualização verificada." if "game" in item.channel.lower() else "Confira os dados e decida se esta oportunidade faz sentido para você."

    @staticmethod
    def _asset_plan(item: DashboardProductionItem) -> list[str]:
        plan = ["Abrir com a evidência principal e identificar claramente a fonte."]
        if "oferta" in item.category.lower() or "produto" in item.category.lower():
            plan.extend(("Usar imagem limpa do produto, sem marca de outro vendedor.", "Mostrar preço e condição apenas após reconfirmação manual."))
        else:
            plan.extend(("Usar captura da fonte oficial ou veículo confiável.", "Intercalar gameplay ou material autorizado com legendas dinâmicas."))
        plan.append("Encerrar com disclosure adequado ao canal; nenhuma publicação automática.")
        return plan

    @staticmethod
    def _failed(item: DashboardProductionItem, error: str) -> dict[str, Any]:
        return {
            "opportunityId": item.opportunity_id,
            "status": "failed",
            "hook": "",
            "script": "",
            "callToAction": "",
            "assetPlan": [],
            "reviewNotes": error,
        }
