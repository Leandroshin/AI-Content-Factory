"""Models for concrete AI Content Factory workflows."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any
from uuid import UUID, uuid4

from core.departments.audio.employee import AudioEngineerEmployee
from core.departments.image.employee import ImageDesignerEmployee
from core.departments.script.employee import ScriptWriterEmployee
from core.departments.video.employee import VideoEditorEmployee


@dataclass(frozen=True, slots=True)
class ContentBrief:
    """Brief for a concrete short-form content production workflow."""

    topic: str
    objective: str
    target_audience: str = ""
    platform: str = "youtube_shorts"
    language: str = "pt-BR"
    tone: str = "clear"
    duration_seconds: int = 45
    video_type: str = "shorts"
    key_points: tuple[str, ...] = field(default_factory=tuple)
    call_to_action: str = "Follow the build if you want to see the factory become real."
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class ContentWorkflowEmployees:
    """Employees required by the minimum content workflow."""

    script_writer: ScriptWriterEmployee
    audio_engineer: AudioEngineerEmployee
    image_designer: ImageDesignerEmployee
    video_editor: VideoEditorEmployee


@dataclass(frozen=True, slots=True)
class ContentWorkflowStepResult:
    """Result for one department step in the content workflow."""

    department: str
    task_id: UUID
    success: bool
    summary: str = ""
    output: dict[str, Any] = field(default_factory=dict)
    error: str = ""


@dataclass(frozen=True, slots=True)
class ContentManagementTaskResult:
    """DepartmentManager task lifecycle mapped to one content workflow step."""

    workflow_department: str
    manager_department: str
    manager_task_id: UUID
    manager_task_title: str
    deliverable: str
    employee_id: UUID
    assigned: bool
    started: bool
    completed: bool
    success: bool
    error: str = ""


@dataclass(frozen=True, slots=True)
class ContentProductionPackage:
    """Final package produced by the minimum content workflow."""

    package_id: UUID = field(default_factory=uuid4)
    workflow: str = "brief_to_short_video"
    script_task_id: UUID | None = None
    audio_task_id: UUID | None = None
    image_task_id: UUID | None = None
    video_task_id: UUID | None = None
    final_format: str = ""
    final_resolution: str = ""
    duration_seconds: int = 0
    quality_passed: bool = False
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class ContentWorkflowResult:
    """Overall result for a concrete content production workflow."""

    success: bool
    package: ContentProductionPackage | None = None
    steps: tuple[ContentWorkflowStepResult, ...] = field(default_factory=tuple)
    summary: str = ""
    error: str = ""

    def output_for(self, department: str) -> dict[str, Any]:
        """Return the output for a department name, or an empty dict."""
        key = department.lower()
        for step in self.steps:
            if step.department.lower() == key:
                return dict(step.output)
        return {}


@dataclass(frozen=True, slots=True)
class ContentManagedWorkflowResult:
    """Workflow result plus executive plan and DepartmentManager progress."""

    success: bool
    workflow_result: ContentWorkflowResult | None = None
    plan_id: UUID | None = None
    management_tasks: tuple[ContentManagementTaskResult, ...] = field(default_factory=tuple)
    progress_pct: float = 0.0
    completed_tasks: int = 0
    total_tasks: int = 0
    company_progress: dict[str, Any] = field(default_factory=dict)
    health_state: dict[str, Any] = field(default_factory=dict)
    error: str = ""
