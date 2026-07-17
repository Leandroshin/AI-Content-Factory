"""Prepare review-only media plans after an owner approves a script draft."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any
from uuid import uuid4

from core.company.specialist_employee import EmployeeSkill
from core.content_factory.models import ApprovedScriptDraft, ContentAssetEmployees, ContentBrief
from core.content_factory.workflow import ContentProductionWorkflow
from core.departments.audio.employee import AudioEngineerEmployee
from core.departments.image.employee import ImageDesignerEmployee
from core.departments.video.employee import VideoEditorEmployee
from core.events.bus import EventBus
from core.runtime import CompanyRuntime
from core.tools.http.client import HttpClient
from core.tools.http.errors import HttpError


@dataclass(frozen=True, slots=True)
class DashboardMediaItem:
    opportunity_id: str
    title: str
    channel: str
    category: str
    hook: str
    script: str
    call_to_action: str
    asset_plan: tuple[str, ...] = field(default_factory=tuple)
    sources: tuple[dict[str, str], ...] = field(default_factory=tuple)


@dataclass(frozen=True, slots=True)
class DashboardMediaResult:
    skipped_reason: str = ""
    received: int = 0
    submitted: int = 0
    failed: int = 0
    opportunity_ids: tuple[str, ...] = field(default_factory=tuple)


class DashboardMediaProductionWorker:
    """Run Audio/Image/Video departments without providers or publication."""

    def __init__(self, client: HttpClient, endpoint: str) -> None:
        endpoint = endpoint.strip()
        if not endpoint.startswith("https://") or not endpoint.endswith("/api/intake/media-production"):
            raise ValueError("Media worker endpoint must be the public HTTPS intake route.")
        self._client = client
        self._endpoint = endpoint

    def run_once(self, *, token: str, enabled: bool = False, site_access_token: str = "") -> DashboardMediaResult:
        if not enabled:
            return DashboardMediaResult(skipped_reason="worker_disabled")
        if not token.strip():
            return DashboardMediaResult(skipped_reason="missing_token")
        headers = self._headers(token, site_access_token)
        try:
            response = self._client.get(self._endpoint, headers=headers)
        except HttpError:
            return DashboardMediaResult(skipped_reason="queue_unavailable")
        if response.status_code != 200 or not isinstance(response.body, dict):
            return DashboardMediaResult(skipped_reason="invalid_queue_response")
        items = tuple(filter(None, (self._coerce_item(value) for value in response.body.get("items", ()))))
        if not items:
            return DashboardMediaResult(skipped_reason="queue_empty")

        accepted: list[str] = []
        failed = 0
        for item in items:
            assert item is not None
            payload = self._produce(item)
            try:
                delivery = self._client.post(
                    self._endpoint,
                    headers={**headers, "Content-Type": "application/json"},
                    body=payload,
                )
            except HttpError:
                failed += 1
                continue
            if delivery.status_code == 202:
                accepted.append(item.opportunity_id)
            else:
                failed += 1
        return DashboardMediaResult(
            received=len(items), submitted=len(accepted), failed=failed, opportunity_ids=tuple(accepted)
        )

    @staticmethod
    def _headers(token: str, site_access_token: str) -> dict[str, str]:
        headers = {"Authorization": f"Bearer {token}"}
        if site_access_token.strip():
            headers["OAI-Sites-Authorization"] = f"Bearer {site_access_token.strip()}"
        return headers

    @staticmethod
    def _coerce_item(value: Any) -> DashboardMediaItem | None:
        if not isinstance(value, dict) or value.get("mode") != "MOCK":
            return None
        required = {key: str(value.get(key, "")).strip() for key in ("opportunityId", "title", "hook", "script", "callToAction")}
        if not all(required.values()):
            return None
        return DashboardMediaItem(
            opportunity_id=required["opportunityId"],
            title=required["title"],
            channel=str(value.get("channel", "")).strip(),
            category=str(value.get("category", "")).strip(),
            hook=required["hook"],
            script=required["script"],
            call_to_action=required["callToAction"],
            asset_plan=tuple(str(item).strip() for item in value.get("assetPlan", ()) if str(item).strip()),
            sources=tuple(source for source in value.get("sources", ()) if isinstance(source, dict)),
        )

    @staticmethod
    def _produce(item: DashboardMediaItem) -> dict[str, Any]:
        event_bus = EventBus()
        company = CompanyRuntime(event_bus)
        company.initialize_company()
        employees = ContentAssetEmployees(
            audio_engineer=AudioEngineerEmployee(
                company, uuid4(),
                (EmployeeSkill(name="audio_processing", proficiency=0.9), EmployeeSkill(name="speech_generation", proficiency=0.9)),
                event_bus=event_bus,
            ),
            image_designer=ImageDesignerEmployee(
                company, uuid4(),
                (EmployeeSkill(name="image_generation", proficiency=0.9), EmployeeSkill(name="image_editing", proficiency=0.9)),
                event_bus=event_bus,
            ),
            video_editor=VideoEditorEmployee(
                company, uuid4(), (EmployeeSkill(name="video_editing", proficiency=0.9),), event_bus=event_bus
            ),
        )
        brief = ContentBrief(
            topic=item.title,
            objective="Preparar a pré-produção técnica para revisão do owner.",
            target_audience="público brasileiro do canal",
            platform="tiktok_youtube_shorts",
            language="pt-BR",
            tone="direto e informativo",
            duration_seconds=45,
            video_type="shorts",
            call_to_action=item.call_to_action,
            metadata={"execution_mode": "MOCK", "channel": item.channel, "category": item.category},
        )
        draft = ApprovedScriptDraft(
            hook=item.hook,
            script_text=item.script,
            call_to_action=item.call_to_action,
            asset_plan=item.asset_plan,
            source_references=item.sources,
        )
        result = ContentProductionWorkflow().run_approved_script_assets(brief, draft, employees)
        if not result.success or result.package is None:
            return {
                "opportunityId": item.opportunity_id,
                "status": "failed",
                "reviewNotes": result.error or "Os departamentos não concluíram a pré-produção MOCK.",
                "departments": {},
            }
        outputs = {step.department: step.output for step in result.steps}
        return {
            "opportunityId": item.opportunity_id,
            "status": "media_review",
            "reviewNotes": "Pré-produção concluída em MOCK. Os cards são planos técnicos; nenhum áudio, imagem ou vídeo final foi gerado.",
            "departments": {
                "audio": DashboardMediaProductionWorker._summary(outputs.get("Audio Production", {}), "Áudio"),
                "image": DashboardMediaProductionWorker._summary(outputs.get("Image Production", {}), "Imagem"),
                "video": DashboardMediaProductionWorker._summary(outputs.get("Video Production", {}), "Vídeo"),
            },
            "qualityPassed": result.package.quality_passed,
            "publicationStatus": "blocked",
            "providerStatus": "not_called",
            "finalAssetStatus": "not_generated",
        }

    @staticmethod
    def _summary(output: dict[str, Any], label: str) -> dict[str, Any]:
        return {
            "label": label,
            "status": "planned" if output else "missing",
            "summary": str(output.get("summary") or output.get("delivery_summary") or f"Plano de {label.lower()} validado pelo departamento."),
            "qualityPassed": bool(output.get("quality_passed", True)) if output else False,
        }
