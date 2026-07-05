"""Read-only observability projector for AI Content Factory."""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Any

from core.company.department_manager import (
    DepartmentPerformanceUpdated,
    EmployeePerformanceUpdated,
    FeedbackRecorded,
    HistoryUpdated,
    PredictionGenerated,
)
from core.departments.runtime import DepartmentStateChangedEvent
from core.employees.runtime import EmployeeStateChangedEvent
from core.events.bus import EventBus
from core.events.domain_events import (
    ApprovalDecided,
    ApprovalRequested,
    ExecutionPersisted,
    ExecutionRestored,
    MemoryDocumentArchived,
    MemoryDocumentCreated,
    MemoryDocumentUpdated,
    ProductionCompleted,
    ProductionStageAdvanced,
    ProductionStarted,
    QualityValidationFinished,
    QualityValidationStarted,
    SessionCreated,
    SessionLoaded,
    SessionSaved,
    SnapshotCreated,
)
from core.tools.http.events import (
    HttpAuthenticationFailed,
    HttpQuotaExceeded,
    HttpRateLimited,
    HttpRequestCompleted,
    HttpRequestFailed,
    HttpRequestStarted,
    HttpRetry,
)
from core.knowledge.runtime import KnowledgeStateChangedEvent
from core.results.runtime import ResultStateChangedEvent
from core.runtime import CompanyStateChangedEvent, TaskRecord
from core.skills.runtime import SkillStateChangedEvent
from core.tasks.runtime import TaskStateChangedEvent
from core.tools.registry import (
    CapabilityRegistered,
    CapabilityRequested,
    CapabilityResolved,
    CapabilityUnavailable as CapUnavailableEvent,
    ToolSelected,
)
from core.tools.runtime import (
    ToolConfigured,
    ToolError,
    ToolExecuted,
    ToolReady,
    ToolRegistered,
    ToolReleased,
    ToolRequested,
    ToolUnavailable,
    ToolValidated,
)
from core.workflows.runtime import WorkflowStateChangedEvent


@dataclass(slots=True)
class CompanySnapshot:
    state: str | None = None


@dataclass(slots=True)
class DepartmentsSnapshot:
    states: dict[str, str] = field(default_factory=dict)


@dataclass(slots=True)
class EmployeesSnapshot:
    states: dict[str, str] = field(default_factory=dict)


@dataclass(slots=True)
class TasksSnapshot:
    states: dict[str, str] = field(default_factory=dict)


@dataclass(slots=True)
class WorkflowsSnapshot:
    states: dict[str, str] = field(default_factory=dict)
    progress: dict[str, float] = field(default_factory=dict)


@dataclass(slots=True)
class ResultsSnapshot:
    states: dict[str, str] = field(default_factory=dict)


@dataclass(slots=True)
class KnowledgeSnapshot:
    states: dict[str, str] = field(default_factory=dict)


@dataclass(slots=True)
class SkillsSnapshot:
    states: dict[str, str] = field(default_factory=dict)


@dataclass(slots=True)
class LearningSnapshot:
    total_feedback_entries: int = 0
    last_success_rate: float = 0.0
    history_entry_count: int = 0
    last_prediction_count: int = 0
    last_prediction_confidence: float = 0.0
    employee_success_rates: dict[str, float] = field(default_factory=dict)
    department_success_rates: dict[str, float] = field(default_factory=dict)


@dataclass(slots=True)
class ToolsSnapshot:
    states: dict[str, str] = field(default_factory=dict)
    usage_counts: dict[str, int] = field(default_factory=dict)
    last_errors: dict[str, str] = field(default_factory=dict)
    last_execution_times: dict[str, float] = field(default_factory=dict)
    adapter_states: dict[str, str] = field(default_factory=dict)
    available_count: int = 0
    blocked_count: int = 0
    configuring_count: int = 0


@dataclass(slots=True)
class HttpSnapshot:
    """Projected HTTP execution metrics across all tools."""
    total_requests: int = 0
    total_retries: int = 0
    total_failures: int = 0
    total_auth_failures: int = 0
    total_quota_exceeded: int = 0
    total_rate_limited: int = 0
    total_timeouts: int = 0
    latency_ms: dict[str, float] = field(default_factory=dict)
    success_rate: float = 0.0


@dataclass(slots=True)
class CapabilitiesSnapshot:
    registered: dict[str, int] = field(default_factory=dict)
    requests: int = 0
    resolutions: int = 0
    unavailable_count: int = 0
    last_selected: str = ""
    last_capability: str = ""


@dataclass(slots=True)
class PersistenceSnapshot:
    session_id: str | None = None
    sessions_count: int = 0
    evidence_count: int = 0
    snapshots_count: int = 0
    last_saved: float | None = None


@dataclass(slots=True)
class OrganizationalMemorySnapshot:
    documents_count: int = 0
    categories: tuple[str, ...] = field(default_factory=tuple)
    active_documents: int = 0
    archived_documents: int = 0


@dataclass(slots=True)
class QualitySnapshot:
    rules_count: int = 0
    reports_count: int = 0
    last_validation_passed: bool | None = None
    last_validation_failed_rules: int = 0


@dataclass(slots=True)
class SessionSnapshot:
    current_session_id: str | None = None
    created_at: float | None = None
    last_activity: float | None = None
    company_state: str | None = None


@dataclass(slots=True)
class ApprovalSnapshot:
    total_requests: int = 0
    pending: int = 0
    approved: int = 0
    rejected: int = 0
    expired: int = 0
    cancelled: int = 0
    latest_approval_id: str = ""
    latest_status: str = ""


@dataclass(slots=True)
class ProductionSnapshot:
    """Generic production snapshot — reutilizado por todos os departamentos."""
    task_id: str | None = None
    pipeline_stage: str = ""
    progress: float = 0.0
    stages_completed: int = 0
    stages_failed: int = 0
    quality_passed: bool = True
    duration_minutes: float = 0.0


@dataclass(slots=True)
class VideoDepartmentSnapshot:
    employees_count: int = 0
    active_productions: int = 0
    pipeline_stages: dict[str, str] = field(default_factory=dict)
    total_productions: int = 0
    successful_productions: int = 0
    failed_productions: int = 0


@dataclass(slots=True)
class VideoProductionSnapshot(ProductionSnapshot):
    """Video-specific production snapshot — estende ProductionSnapshot."""
    video_type: str = ""


@dataclass(slots=True)
class RenderSnapshot:
    output_format: str = ""
    output_resolution: str = ""
    estimated_size_mb: int = 0
    segments_count: int = 0
    effects_count: int = 0
    subtitles: int = 0


@dataclass(slots=True)
class AudioDepartmentSnapshot:
    employees_count: int = 0
    active_productions: int = 0
    pipeline_stages: dict[str, str] = field(default_factory=dict)
    total_productions: int = 0
    successful_productions: int = 0
    failed_productions: int = 0


@dataclass(slots=True)
class AudioProductionSnapshot(ProductionSnapshot):
    """Audio-specific production snapshot — estende ProductionSnapshot."""
    audio_type: str = ""


@dataclass(slots=True)
class ExportSnapshot:
    output_format: str = ""
    output_bitrate: str = ""
    estimated_size_mb: int = 0
    tracks_count: int = 0
    voice_segments_count: int = 0
    effects_count: int = 0


@dataclass(slots=True)
class ImageDepartmentSnapshot:
    employees_count: int = 0
    active_productions: int = 0
    pipeline_stages: dict[str, str] = field(default_factory=dict)
    total_productions: int = 0
    successful_productions: int = 0
    failed_productions: int = 0


@dataclass(slots=True)
class ImageProductionSnapshot(ProductionSnapshot):
    """Image-specific production snapshot — estende ProductionSnapshot."""
    image_type: str = ""


@dataclass(slots=True)
class AssetSnapshot:
    output_format: str = ""
    canvas_width: int = 0
    canvas_height: int = 0
    estimate_size_kb: int = 0
    layers_count: int = 0
    text_overlays_count: int = 0
    variants_count: int = 0


@dataclass(slots=True)
class ScriptDepartmentSnapshot:
    employees_count: int = 0
    active_productions: int = 0
    pipeline_stages: dict[str, str] = field(default_factory=dict)
    total_productions: int = 0
    successful_productions: int = 0
    failed_productions: int = 0


@dataclass(slots=True)
class ScriptProductionSnapshot(ProductionSnapshot):
    """Script-specific production snapshot - extends ProductionSnapshot."""
    script_type: str = ""


@dataclass(slots=True)
class AffiliateDealsDepartmentSnapshot:
    employees_count: int = 0
    active_productions: int = 0
    pipeline_stages: dict[str, str] = field(default_factory=dict)
    total_productions: int = 0
    successful_productions: int = 0
    failed_productions: int = 0


@dataclass(slots=True)
class AffiliateDealsProductionSnapshot(ProductionSnapshot):
    """Affiliate-deals-specific production snapshot."""
    campaign_type: str = ""
    last_recommendation: str = ""


@dataclass(slots=True)
class DealMetricsSnapshot:
    total_offers_analyzed: int = 0
    offers_approved: int = 0
    offers_rejected: int = 0
    offers_awaiting_approval: int = 0
    posts_prepared: int = 0
    pending_publications: int = 0
    marketplace_most_used: str = ""
    last_score: float = 0.0
    last_recommendation: str = ""
    last_publishing_channel: str = ""
    primary_funnel: str = ""
    last_error: str = ""


@dataclass(slots=True)
class ObservabilitySnapshot:
    company: CompanySnapshot = field(default_factory=CompanySnapshot)
    departments: DepartmentsSnapshot = field(default_factory=DepartmentsSnapshot)
    employees: EmployeesSnapshot = field(default_factory=EmployeesSnapshot)
    tasks: TasksSnapshot = field(default_factory=TasksSnapshot)
    workflows: WorkflowsSnapshot = field(default_factory=WorkflowsSnapshot)
    results: ResultsSnapshot = field(default_factory=ResultsSnapshot)
    knowledge: KnowledgeSnapshot = field(default_factory=KnowledgeSnapshot)
    skills: SkillsSnapshot = field(default_factory=SkillsSnapshot)
    learning: LearningSnapshot = field(default_factory=LearningSnapshot)
    tools: ToolsSnapshot = field(default_factory=ToolsSnapshot)
    capabilities: CapabilitiesSnapshot = field(default_factory=CapabilitiesSnapshot)
    http: HttpSnapshot = field(default_factory=HttpSnapshot)
    persistence: PersistenceSnapshot = field(default_factory=PersistenceSnapshot)
    organizational_memory: OrganizationalMemorySnapshot = field(default_factory=OrganizationalMemorySnapshot)
    quality: QualitySnapshot = field(default_factory=QualitySnapshot)
    session: SessionSnapshot = field(default_factory=SessionSnapshot)
    approvals: ApprovalSnapshot = field(default_factory=ApprovalSnapshot)
    video_department: VideoDepartmentSnapshot = field(default_factory=VideoDepartmentSnapshot)
    video_production: VideoProductionSnapshot = field(default_factory=VideoProductionSnapshot)
    render: RenderSnapshot = field(default_factory=RenderSnapshot)
    audio_department: AudioDepartmentSnapshot = field(default_factory=AudioDepartmentSnapshot)
    audio_production: AudioProductionSnapshot = field(default_factory=AudioProductionSnapshot)
    export: ExportSnapshot = field(default_factory=ExportSnapshot)
    image_department: ImageDepartmentSnapshot = field(default_factory=ImageDepartmentSnapshot)
    image_production: ImageProductionSnapshot = field(default_factory=ImageProductionSnapshot)
    asset: AssetSnapshot = field(default_factory=AssetSnapshot)
    script_department: ScriptDepartmentSnapshot = field(default_factory=ScriptDepartmentSnapshot)
    script_production: ScriptProductionSnapshot = field(default_factory=ScriptProductionSnapshot)
    affiliate_deals_department: AffiliateDealsDepartmentSnapshot = field(default_factory=AffiliateDealsDepartmentSnapshot)
    affiliate_deals_production: AffiliateDealsProductionSnapshot = field(default_factory=AffiliateDealsProductionSnapshot)
    deal_metrics: DealMetricsSnapshot = field(default_factory=DealMetricsSnapshot)
    production: ProductionSnapshot = field(default_factory=ProductionSnapshot)
    events: list[str] = field(default_factory=list)
    task_records: dict[str, TaskRecord] = field(default_factory=dict)


class BaseProjector(ABC):
    """Base class for all projection engines in the AI Content Factory."""

    def __init__(self, event_bus: EventBus | None = None) -> None:
        if event_bus is not None:
            self.register_to(event_bus)

    def register_to(self, event_bus: EventBus) -> None:
        """Register mapped event handlers to the EventBus."""
        for event_type, handler in self.get_event_mappings().items():
            event_bus.subscribe(event_type, handler)

    @abstractmethod
    def get_event_mappings(self) -> dict[type[Any], Callable[[Any], None]]:
        """Return a mapping from event classes to their handler methods."""
        raise NotImplementedError


class ObservabilityProjector(BaseProjector):
    """Read-only projector driven only by EventBus events."""

    def __init__(self, event_bus: EventBus | None = None) -> None:
        self.snapshot = ObservabilitySnapshot()
        self._task_department_map: dict[str, str] = {}
        super().__init__(event_bus)

    def get_event_mappings(self) -> dict[type[Any], Callable[[Any], None]]:
        return {
            CompanyStateChangedEvent: self.handle_company_event,
            DepartmentStateChangedEvent: self.handle_department_event,
            EmployeeStateChangedEvent: self.handle_employee_event,
            TaskStateChangedEvent: self.handle_task_event,
            WorkflowStateChangedEvent: self.handle_workflow_event,
            ResultStateChangedEvent: self.handle_result_event,
            KnowledgeStateChangedEvent: self.handle_knowledge_event,
            SkillStateChangedEvent: self.handle_skill_event,
            FeedbackRecorded: self.handle_feedback_recorded,
            HistoryUpdated: self.handle_history_updated,
            PredictionGenerated: self.handle_prediction_generated,
            EmployeePerformanceUpdated: self.handle_employee_performance,
            DepartmentPerformanceUpdated: self.handle_department_performance,
            ToolRegistered: self.handle_tool_registered,
            ToolRequested: self.handle_tool_requested,
            ToolUnavailable: self.handle_tool_unavailable,
            ToolConfigured: self.handle_tool_configured,
            ToolValidated: self.handle_tool_validated,
            ToolReady: self.handle_tool_ready,
            ToolError: self.handle_tool_error,
            ToolExecuted: self.handle_tool_executed,
            ToolReleased: self.handle_tool_released,
            CapabilityRegistered: self.handle_capability_registered,
            CapabilityRequested: self.handle_capability_requested,
            CapabilityResolved: self.handle_capability_resolved,
            CapUnavailableEvent: self.handle_capability_unavailable,
            ToolSelected: self.handle_tool_selected,
            # Production events
            ProductionStarted: self.handle_production_started,
            ProductionStageAdvanced: self.handle_production_stage_advanced,
            ProductionCompleted: self.handle_production_completed,
            # New persistence/memory/quality events
            SessionCreated: self.handle_session_created,
            SessionLoaded: self.handle_session_loaded,
            SessionSaved: self.handle_session_saved,
            SnapshotCreated: self.handle_snapshot_created,
            ExecutionPersisted: self.handle_execution_persisted,
            ExecutionRestored: self.handle_execution_restored,
            MemoryDocumentCreated: self.handle_memory_document_created,
            MemoryDocumentUpdated: self.handle_memory_document_updated,
            MemoryDocumentArchived: self.handle_memory_document_archived,
            QualityValidationStarted: self.handle_quality_started,
            QualityValidationFinished: self.handle_quality_finished,
            ApprovalRequested: self.handle_approval_requested,
            ApprovalDecided: self.handle_approval_decided,
            # HTTP events
            HttpRequestStarted: self.handle_http_request_started,
            HttpRequestCompleted: self.handle_http_request_completed,
            HttpRequestFailed: self.handle_http_request_failed,
            HttpRetry: self.handle_http_retry,
            HttpRateLimited: self.handle_http_rate_limited,
            HttpAuthenticationFailed: self.handle_http_auth_failed,
            HttpQuotaExceeded: self.handle_http_quota_exceeded,
        }

    def handle_company_event(self, event: CompanyStateChangedEvent) -> None:
        self.snapshot.company.state = event.new_state.value
        self.snapshot.events.append(f"company:{event.previous_state.value}->{event.new_state.value}")

    def handle_department_event(self, event: DepartmentStateChangedEvent) -> None:
        self.snapshot.departments.states[str(event.department_id)] = event.new_state.value
        self.snapshot.events.append(f"department:{event.previous_state.value}->{event.new_state.value}:{event.department_id}")

    def handle_employee_event(self, event: EmployeeStateChangedEvent) -> None:
        self.snapshot.employees.states[str(event.employee_id)] = event.new_state.value
        self.snapshot.events.append(f"employee:{event.previous_state.value}->{event.new_state.value}:{event.employee_id}")

    def handle_task_event(self, event: TaskStateChangedEvent) -> None:
        task_id_str = str(event.task_id)
        self.snapshot.tasks.states[task_id_str] = event.new_state.value
        self.snapshot.events.append(f"task:{event.previous_state.value}->{event.new_state.value}:{event.task_id}")

        title = event.payload.get("title") if event.payload else None
        if task_id_str not in self.snapshot.task_records:
            if title is None:
                title = f"Task {task_id_str[:8]}"
            self.snapshot.task_records[task_id_str] = TaskRecord(
                task_id=event.task_id,
                title=title,
                assigned_employee_id=event.employee_id,
                state=event.new_state.value,
                metadata=event.payload or {},
            )
        else:
            existing = self.snapshot.task_records[task_id_str]
            self.snapshot.task_records[task_id_str] = TaskRecord(
                task_id=event.task_id,
                title=existing.title if title is None else title,
                assigned_employee_id=event.employee_id or existing.assigned_employee_id,
                state=event.new_state.value,
                metadata={**existing.metadata, **(event.payload or {})},
            )

    def handle_workflow_event(self, event: WorkflowStateChangedEvent) -> None:
        self.snapshot.workflows.states[str(event.workflow_id)] = event.new_state.value
        self.snapshot.workflows.progress[str(event.workflow_id)] = event.progress
        self.snapshot.events.append(f"workflow:{event.previous_state.value}->{event.new_state.value}:{event.workflow_id}")

    def handle_result_event(self, event: ResultStateChangedEvent) -> None:
        self.snapshot.results.states[str(event.result_id)] = event.new_state.value
        self.snapshot.events.append(f"result:{event.previous_state.value}->{event.new_state.value}:{event.result_id}")

    def handle_knowledge_event(self, event: KnowledgeStateChangedEvent) -> None:
        self.snapshot.knowledge.states[str(event.knowledge_id)] = event.new_state.value
        self.snapshot.events.append(f"knowledge:{event.previous_state.value}->{event.new_state.value}:{event.knowledge_id}")

    def handle_skill_event(self, event: SkillStateChangedEvent) -> None:
        self.snapshot.skills.states[str(event.skill_id)] = event.new_state.value
        self.snapshot.events.append(f"skill:{event.previous_state.value}->{event.new_state.value}:{event.skill_id}")

    def handle_feedback_recorded(self, event: FeedbackRecorded) -> None:
        self.snapshot.learning.total_feedback_entries = event.total_entries
        self.snapshot.learning.last_success_rate = event.success_rate
        self.snapshot.events.append(
            f"feedback:task={event.task_id.hex[:8]}:"
            f"emp={event.employee_id.hex[:8]}:"
            f"success={event.success}:"
            f"rate={event.success_rate:.2f}"
        )

    def handle_history_updated(self, event: HistoryUpdated) -> None:
        self.snapshot.learning.history_entry_count = event.entry_count
        self.snapshot.events.append(
            f"history:domain={event.domain}:"
            f"entries={event.entry_count}:"
            f"improving={event.improving_count}:"
            f"declining={event.declining_count}"
        )

    def handle_prediction_generated(self, event: PredictionGenerated) -> None:
        self.snapshot.learning.last_prediction_count = event.total_predictions
        self.snapshot.learning.last_prediction_confidence = event.avg_confidence
        self.snapshot.events.append(
            f"prediction:domain={event.domain}:"
            f"total={event.total_predictions}:"
            f"confidence={event.avg_confidence:.2f}:"
            f"up={event.upward_count}:"
            f"down={event.downward_count}"
        )

    def handle_employee_performance(self, event: EmployeePerformanceUpdated) -> None:
        self.snapshot.learning.employee_success_rates[str(event.employee_id)] = event.success_rate
        self.snapshot.events.append(
            f"employee_perf:emp={event.employee_id.hex[:8]}:"
            f"completed={event.tasks_completed}:"
            f"rate={event.success_rate:.2f}"
        )

    def handle_department_performance(self, event: DepartmentPerformanceUpdated) -> None:
        self.snapshot.learning.department_success_rates[event.department] = event.success_rate
        self.snapshot.events.append(
            f"dept_perf:dept={event.department}:"
            f"completed={event.tasks_completed}:"
            f"rate={event.success_rate:.2f}"
        )

    # ------------------------------------------------------------------
    # Tool event handlers
    # ------------------------------------------------------------------

    def _refresh_tool_counts(self) -> None:
        states = list(self.snapshot.tools.states.values())
        self.snapshot.tools.available_count = sum(1 for s in states if s == "ready")
        self.snapshot.tools.blocked_count = sum(1 for s in states if s in ("error", "disabled"))
        self.snapshot.tools.configuring_count = sum(1 for s in states if s in ("unconfigured", "configuring", "busy"))

    def handle_tool_registered(self, event: ToolRegistered) -> None:
        tid = event.tool_id.hex[:8]
        self.snapshot.tools.states[tid] = "registered"
        self.snapshot.tools.usage_counts[tid] = 0
        self.snapshot.tools.last_errors[tid] = ""
        self.snapshot.tools.last_execution_times[tid] = 0.0
        self.snapshot.tools.adapter_states[tid] = "unconfigured"
        self._refresh_tool_counts()
        self.snapshot.events.append(f"tool:registered:{event.name}:{tid}")

    def handle_tool_requested(self, event: ToolRequested) -> None:
        tid = event.tool_id.hex[:8]
        self.snapshot.events.append(
            f"tool:requested:{event.tool_name}:{tid}:emp={event.employee_id.hex[:8]}"
        )

    def handle_tool_unavailable(self, event: ToolUnavailable) -> None:
        tid = event.tool_id.hex[:8]
        self.snapshot.tools.states[tid] = "unavailable"
        self.snapshot.tools.last_errors[tid] = event.reason
        self._refresh_tool_counts()
        self.snapshot.events.append(
            f"tool:unavailable:{event.tool_name}:{tid}:"
            f"reason={event.reason}:missing={len(event.missing_items)}"
        )

    def handle_tool_configured(self, event: ToolConfigured) -> None:
        tid = event.tool_id.hex[:8]
        self.snapshot.tools.states[tid] = "configuring"
        if event.config_keys:
            self.snapshot.tools.adapter_states[tid] = "configured"
        else:
            self.snapshot.tools.adapter_states[tid] = "authenticated"
        self._refresh_tool_counts()
        self.snapshot.events.append(
            f"tool:configured:{event.name}:{tid}:keys={len(event.config_keys)}"
        )

    def handle_tool_validated(self, event: ToolValidated) -> None:
        tid = event.tool_id.hex[:8]
        self.snapshot.events.append(
            f"tool:validated:{event.name}:{tid}:success={event.success}"
        )

    def handle_tool_ready(self, event: ToolReady) -> None:
        tid = event.tool_id.hex[:8]
        self.snapshot.tools.states[tid] = "ready"
        self.snapshot.tools.last_errors[tid] = ""
        self.snapshot.tools.adapter_states[tid] = "ready"
        self._refresh_tool_counts()
        self.snapshot.events.append(f"tool:ready:{event.name}:{tid}")

    def handle_tool_error(self, event: ToolError) -> None:
        tid = event.tool_id.hex[:8]
        self.snapshot.tools.states[tid] = "error"
        self.snapshot.tools.last_errors[tid] = event.error_message
        self.snapshot.tools.adapter_states[tid] = "error"
        self._refresh_tool_counts()
        self.snapshot.events.append(
            f"tool:error:{event.name}:{tid}:{event.error_message}"
        )

    def handle_tool_released(self, event: ToolReleased) -> None:
        tid = event.tool_id.hex[:8]
        self.snapshot.tools.states[tid] = "ready"
        self.snapshot.tools.usage_counts[tid] = self.snapshot.tools.usage_counts.get(tid, 0) + 1
        self._refresh_tool_counts()
        self.snapshot.events.append(
            f"tool:released:{event.name}:{tid}:emp={event.employee_id.hex[:8]}"
        )

    # ------------------------------------------------------------------
    # HTTP event handler (stub — fires when adapters execute in REAL mode)
    # ------------------------------------------------------------------

    def _project_http_metrics(self) -> None:
        """Recalculate derived HTTP metrics."""
        total = self.snapshot.http.total_requests
        failures = self.snapshot.http.total_failures
        if total > 0:
            self.snapshot.http.success_rate = round(
                (total - failures) / total * 100.0, 2
            )

    def handle_tool_executed(self, event: ToolExecuted) -> None:
        tid = event.tool_id.hex[:8]
        self.snapshot.tools.usage_counts[tid] = self.snapshot.tools.usage_counts.get(tid, 0) + 1
        self.snapshot.tools.last_execution_times[tid] = event.timestamp or event.duration_ms or 0.0
        self.snapshot.events.append(
            f"tool:executed:{event.name}:{tid}:"
            f"cap={event.capability}:"
            f"success={event.success}:"
            f"duration={event.duration_ms:.1f}ms"
        )

    # ------------------------------------------------------------------
    # Capability event handlers
    # ------------------------------------------------------------------

    def handle_capability_registered(self, event: CapabilityRegistered) -> None:
        for cap in event.capabilities:
            self.snapshot.capabilities.registered[cap] = \
                self.snapshot.capabilities.registered.get(cap, 0) + 1
        caps_str = ",".join(event.capabilities)
        self.snapshot.events.append(
            f"capability:registered:{event.name}:{caps_str}:priority={event.priority}"
        )

    def handle_capability_requested(self, event: CapabilityRequested) -> None:
        self.snapshot.capabilities.requests += 1
        self.snapshot.capabilities.last_capability = event.capability
        self.snapshot.events.append(
            f"capability:requested:{event.capability}:"
            f"emp={event.employee_id.hex[:8]}"
        )

    def handle_capability_resolved(self, event: CapabilityResolved) -> None:
        self.snapshot.capabilities.resolutions += 1
        self.snapshot.capabilities.last_selected = event.tool_name
        self.snapshot.events.append(
            f"capability:resolved:{event.capability}->{event.tool_name}"
        )

    def handle_capability_unavailable(self, event: CapUnavailableEvent) -> None:
        self.snapshot.capabilities.unavailable_count += 1
        self.snapshot.events.append(
            f"capability:unavailable:{event.capability}:"
            f"reason={event.reason}"
        )

    def handle_tool_selected(self, event: ToolSelected) -> None:
        self.snapshot.capabilities.last_selected = event.tool_name
        self.snapshot.events.append(
            f"capability:selected:{event.capability}->{event.tool_name}:"
            f"priority={event.priority}"
        )

    # ------------------------------------------------------------------
    # Persistence / Session event handlers
    # ------------------------------------------------------------------

    def handle_session_created(self, event: SessionCreated) -> None:
        sid = str(event.session_id)
        self.snapshot.session.current_session_id = sid
        self.snapshot.session.created_at = event.timestamp
        self.snapshot.session.last_activity = event.timestamp
        self.snapshot.session.company_state = "initialized"
        self.snapshot.persistence.session_id = sid
        self.snapshot.persistence.sessions_count += 1
        self.snapshot.persistence.last_saved = event.timestamp
        self.snapshot.events.append(
            f"session:created:{sid[:8]}"
        )

    def handle_session_loaded(self, event: SessionLoaded) -> None:
        sid = str(event.session_id)
        self.snapshot.session.current_session_id = sid
        self.snapshot.session.last_activity = event.timestamp
        self.snapshot.persistence.session_id = sid
        self.snapshot.events.append(
            f"session:loaded:{sid[:8]}"
        )

    def handle_session_saved(self, event: SessionSaved) -> None:
        self.snapshot.session.last_activity = event.timestamp
        self.snapshot.persistence.last_saved = event.timestamp
        self.snapshot.events.append(
            f"session:saved:{str(event.session_id)[:8]}"
        )

    def handle_snapshot_created(self, event: SnapshotCreated) -> None:
        self.snapshot.persistence.snapshots_count += 1
        self.snapshot.events.append(
            f"snapshot:created:{str(event.session_id)[:8]}"
        )

    def handle_execution_persisted(self, event: ExecutionPersisted) -> None:
        self.snapshot.persistence.evidence_count += 1
        self.snapshot.events.append(
            f"execution:persisted:{event.component}:{event.action}:{str(event.execution_id)[:8]}"
        )

    def handle_execution_restored(self, event: ExecutionRestored) -> None:
        self.snapshot.events.append(
            f"execution:restored:{event.component}:{event.action}:{str(event.execution_id)[:8]}"
        )

    # ------------------------------------------------------------------
    # Organizational Memory event handlers
    # ------------------------------------------------------------------

    def handle_memory_document_created(self, event: MemoryDocumentCreated) -> None:
        self.snapshot.organizational_memory.documents_count += 1
        self.snapshot.organizational_memory.active_documents += 1
        self.snapshot.events.append(
            f"memory:created:{event.category}:{event.title}:{str(event.document_id)[:8]}"
        )

    def handle_memory_document_updated(self, event: MemoryDocumentUpdated) -> None:
        self.snapshot.events.append(
            f"memory:updated:{event.category}:{event.title}:v{event.version}:{str(event.document_id)[:8]}"
        )

    def handle_memory_document_archived(self, event: MemoryDocumentArchived) -> None:
        self.snapshot.organizational_memory.archived_documents += 1
        self.snapshot.organizational_memory.active_documents = max(
            0, self.snapshot.organizational_memory.active_documents - 1
        )
        self.snapshot.events.append(
            f"memory:archived:{event.title}:{str(event.document_id)[:8]}"
        )

    # ------------------------------------------------------------------
    # Quality event handlers
    # ------------------------------------------------------------------

    # ------------------------------------------------------------------
    # Production event handlers — populate department snapshots
    # ------------------------------------------------------------------

    def _dept_snapshot(self, department: str):
        dept = department.lower()
        if dept == "video":
            return self.snapshot.video_department, self.snapshot.video_production, self.snapshot.render
        elif dept == "audio":
            return self.snapshot.audio_department, self.snapshot.audio_production, self.snapshot.export
        elif dept == "image":
            return self.snapshot.image_department, self.snapshot.image_production, self.snapshot.asset
        elif dept == "script":
            return self.snapshot.script_department, self.snapshot.script_production, None
        elif dept == "affiliate_deals":
            return self.snapshot.affiliate_deals_department, self.snapshot.affiliate_deals_production, self.snapshot.deal_metrics
        return None, None, None

    def _set_production_type(self, dept: str, prod_snapshot, prod_type: str) -> None:
        if dept == "video":
            prod_snapshot.video_type = prod_type
        elif dept == "audio":
            prod_snapshot.audio_type = prod_type
        elif dept == "image":
            prod_snapshot.image_type = prod_type
        elif dept == "script":
            prod_snapshot.script_type = prod_type
        elif dept == "affiliate_deals":
            prod_snapshot.campaign_type = prod_type

    def handle_production_started(self, event: ProductionStarted) -> None:
        sid = str(event.task_id)[:8]
        dept = event.department.lower()

        self._task_department_map[sid] = dept
        self.snapshot.production.task_id = sid
        self.snapshot.production.pipeline_stage = event.stage
        self.snapshot.production.progress = 0.0
        self.snapshot.production.stages_completed = 0
        self.snapshot.production.stages_failed = 0

        dept_snap, prod_snap, detail_snap = self._dept_snapshot(dept)
        if dept_snap is not None:
            dept_snap.active_productions += 1
            dept_snap.total_productions += 1
            dept_snap.pipeline_stages[sid] = event.stage
            prod_snap.task_id = sid
            prod_snap.pipeline_stage = event.stage
            prod_snap.progress = 0.0
            prod_snap.stages_completed = 0
            prod_snap.stages_failed = 0
            prod_snap.quality_passed = True
            prod_snap.duration_minutes = 0.0
            self._set_production_type(dept, prod_snap, event.production_type)

        self.snapshot.events.append(
            f"production:started:{sid}:dept={dept}:stage={event.stage}:type={event.production_type}"
        )

    def handle_production_stage_advanced(self, event: ProductionStageAdvanced) -> None:
        sid = str(event.task_id)[:8]
        dept = event.department.lower()

        self.snapshot.production.pipeline_stage = event.stage
        self.snapshot.production.progress = event.progress
        self.snapshot.production.stages_completed = event.stages_completed
        self.snapshot.production.stages_failed = event.stages_failed

        dept_snap, prod_snap, _ = self._dept_snapshot(dept)
        if dept_snap is not None:
            dept_snap.pipeline_stages[sid] = event.stage
            prod_snap.pipeline_stage = event.stage
            prod_snap.progress = event.progress
            prod_snap.stages_completed = event.stages_completed
            prod_snap.stages_failed = event.stages_failed

        status = "ok" if event.success else "fail"
        log = f"production:stage:{sid}:{event.stage}:{status}:stages_completed={event.stages_completed}:stages_failed={event.stages_failed}"
        if event.error:
            log += f":error={event.error[:60]}"
        self.snapshot.events.append(log)

    def handle_production_completed(self, event: ProductionCompleted) -> None:
        sid = str(event.task_id)[:8]
        dept = event.department.lower()

        final_stage = "completed" if event.success else "failed"
        self.snapshot.production.pipeline_stage = final_stage
        self.snapshot.production.progress = 100.0 if event.success else 0.0
        self.snapshot.production.quality_passed = event.output.get("quality_passed", True)
        self.snapshot.production.duration_minutes = event.duration_minutes

        dept_snap, prod_snap, detail_snap = self._dept_snapshot(dept)
        if dept_snap is not None:
            dept_snap.active_productions = max(0, dept_snap.active_productions - 1)
            if event.success:
                dept_snap.successful_productions += 1
            else:
                dept_snap.failed_productions += 1
            dept_snap.pipeline_stages[sid] = final_stage
            prod_snap.pipeline_stage = final_stage
            prod_snap.progress = 100.0 if event.success else 0.0
            prod_snap.quality_passed = event.output.get("quality_passed", True)
            prod_snap.duration_minutes = event.duration_minutes

            if dept == "video":
                render_info = event.output.get("render", {})
                if render_info:
                    detail_snap.output_format = render_info.get("output_format", "")
                    detail_snap.output_resolution = render_info.get("output_resolution", "")
                    detail_snap.estimated_size_mb = render_info.get("estimated_size_mb", 0)
                    detail_snap.segments_count = event.output.get("segments_count", 0)
                    detail_snap.subtitles = event.output.get("subtitles_count", 0)
            elif dept == "audio":
                export_info = event.output.get("export", {})
                if export_info:
                    detail_snap.output_format = export_info.get("output_format", "")
                    detail_snap.output_bitrate = export_info.get("output_bitrate", "")
                    detail_snap.estimated_size_mb = export_info.get("estimated_size_mb", 0)
                    detail_snap.tracks_count = event.output.get("tracks_count", 0)
                    detail_snap.voice_segments_count = event.output.get("voice_segments_count", 0)
            elif dept == "image":
                export_info = event.output.get("export", {})
                if export_info:
                    detail_snap.output_format = export_info.get("output_format", "")
                    detail_snap.canvas_width = export_info.get("canvas_width", 0)
                    detail_snap.canvas_height = export_info.get("canvas_height", 0)
                    detail_snap.estimate_size_kb = export_info.get("estimate_size_kb", 0)
                    detail_snap.layers_count = event.output.get("layers_count", 0)
                    detail_snap.text_overlays_count = event.output.get("text_overlays_count", 0)
                    detail_snap.variants_count = event.output.get("variants_count", 0)
            elif dept == "affiliate_deals":
                recommendation = event.output.get("recommendation", "")
                prod_snap.last_recommendation = recommendation
                detail_snap.total_offers_analyzed += event.output.get("offers_analyzed", 0)
                if recommendation in ("post_now", "needs_review") and event.output.get("compliance_passed", False):
                    detail_snap.offers_approved += 1
                if recommendation == "skip" or event.output.get("publishing_status") in ("rejected", "blocked"):
                    detail_snap.offers_rejected += 1
                if event.output.get("publishing_status") == "pending_approval":
                    detail_snap.offers_awaiting_approval += 1
                    detail_snap.pending_publications += 1
                if event.output.get("publishing_status") in ("pending_approval", "ready"):
                    detail_snap.posts_prepared += 1
                product = event.output.get("product_offer", {})
                marketplace = product.get("marketplace", {}).get("name", "") if product else ""
                if marketplace:
                    detail_snap.marketplace_most_used = marketplace
                detail_snap.last_score = event.output.get("score_total", 0.0)
                detail_snap.last_recommendation = recommendation
                plan = event.output.get("publishing_plan", {})
                if plan:
                    detail_snap.last_publishing_channel = plan.get("channel", {}).get("name", "")
                detail_snap.primary_funnel = event.output.get("primary_funnel", "")
                if not event.success:
                    detail_snap.last_error = event.output.get("error", "")

        status = "completed" if event.success else "failed"
        self.snapshot.events.append(
            f"production:{status}:{sid}:dept={dept}:"
            f"duration={event.duration_minutes:.1f}min:"
            f"quality={event.output.get('quality_passed', True)}"
        )

    # ------------------------------------------------------------------
    # Quality event handlers
    # ------------------------------------------------------------------

    def handle_quality_started(self, event: QualityValidationStarted) -> None:
        self.snapshot.quality.reports_count += 1
        self.snapshot.events.append(
            f"quality:started:{str(event.execution_id)[:8]}"
        )

    def handle_quality_finished(self, event: QualityValidationFinished) -> None:
        self.snapshot.quality.rules_count = event.total_rules
        self.snapshot.quality.last_validation_passed = event.passed
        self.snapshot.quality.last_validation_failed_rules = event.failed_rules
        self.snapshot.production.quality_passed = event.passed

        # Propagate to department-specific production snapshot
        eid = str(event.execution_id)[:8]
        dept = self._task_department_map.get(eid)
        if dept:
            _, prod_snap, _ = self._dept_snapshot(dept)
            if prod_snap is not None:
                prod_snap.quality_passed = event.passed

        self.snapshot.events.append(
            f"quality:finished:{eid}:"
            f"passed={event.passed}:"
            f"passed_rules={event.passed_rules}/"
            f"{event.total_rules}"
        )

    # ------------------------------------------------------------------
    # Approval event handlers
    # ------------------------------------------------------------------

    def handle_approval_requested(self, event: ApprovalRequested) -> None:
        snap = self.snapshot.approvals
        snap.total_requests += 1
        snap.pending += 1
        snap.latest_approval_id = str(event.approval_id)[:8]
        snap.latest_status = "pending"
        self.snapshot.events.append(
            f"approval:requested:{snap.latest_approval_id}:source={event.source}:risk={event.risk_level}"
        )

    def handle_approval_decided(self, event: ApprovalDecided) -> None:
        snap = self.snapshot.approvals
        status = event.status
        if snap.pending > 0:
            snap.pending -= 1
        if status == "approved":
            snap.approved += 1
        elif status == "rejected":
            snap.rejected += 1
        elif status == "expired":
            snap.expired += 1
        elif status == "cancelled":
            snap.cancelled += 1
        snap.latest_approval_id = str(event.approval_id)[:8]
        snap.latest_status = status
        self.snapshot.events.append(
            f"approval:decided:{snap.latest_approval_id}:status={status}:by={event.decided_by}"
        )

    # ------------------------------------------------------------------
    # HTTP event handlers — auto-project HttpSnapshot
    # ------------------------------------------------------------------

    def _refresh_http_metrics(self) -> None:
        h = self.snapshot.http
        total = h.total_requests
        failures = h.total_failures
        if total > 0:
            h.success_rate = round((total - failures) / total * 100.0, 2)
        else:
            h.success_rate = 100.0

    def handle_http_request_started(self, event: HttpRequestStarted) -> None:
        self.snapshot.http.total_requests += 1
        self.snapshot.events.append(
            f"http:started:{event.method}:{event.url[:60]}"
        )

    def handle_http_request_completed(self, event: HttpRequestCompleted) -> None:
        self.snapshot.http.latency_ms[str(event.status_code)] = event.elapsed_ms
        self._refresh_http_metrics()
        self.snapshot.events.append(
            f"http:completed:status={event.status_code}:"
            f"elapsed={event.elapsed_ms:.1f}ms"
        )

    def handle_http_request_failed(self, event: HttpRequestFailed) -> None:
        self.snapshot.http.total_failures += 1
        self._refresh_http_metrics()
        self.snapshot.events.append(
            f"http:failed:{event.error_type}:{event.error_message[:60]}"
        )

    def handle_http_retry(self, event: HttpRetry) -> None:
        self.snapshot.http.total_retries += 1
        self.snapshot.events.append(
            f"http:retry:attempt={event.attempt}:"
            f"status={event.status_code}:delay={event.delay:.1f}s"
        )

    def handle_http_rate_limited(self, event: HttpRateLimited) -> None:
        self.snapshot.http.total_rate_limited += 1
        self.snapshot.events.append(
            f"http:rate_limited:retry_after={event.retry_after}:"
            f"limit={event.limit}:remaining={event.remaining}"
        )

    def handle_http_auth_failed(self, event: HttpAuthenticationFailed) -> None:
        self.snapshot.http.total_auth_failures += 1
        self.snapshot.http.total_failures += 1
        self._refresh_http_metrics()
        self.snapshot.events.append(
            f"http:auth_failed:{event.reason[:60]}"
        )

    def handle_http_quota_exceeded(self, event: HttpQuotaExceeded) -> None:
        self.snapshot.http.total_quota_exceeded += 1
        self.snapshot.http.total_failures += 1
        self._refresh_http_metrics()
        self.snapshot.events.append(
            f"http:quota_exceeded:{event.quota_type}:limit={event.limit}"
        )
