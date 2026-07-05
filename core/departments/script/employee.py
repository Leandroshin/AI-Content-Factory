"""ScriptWriterEmployee specialized in script production.

Inherits ProductionEmployee and only implements script-specific hooks.
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Any
from uuid import UUID

from core.company.department_manager import DepartmentManager
from core.company.quality import QualityRuntime
from core.company.specialist_employee import (
    EmployeeSkill,
    EmployeeStatus,
    ReceivedTask,
    TaskAccepted,
    TaskDecision,
)
from core.departments.base.employee import ProductionEmployee
from core.departments.base.pipeline import ProductionPipeline
from core.departments.script.models import (
    CallToAction,
    HookVariant,
    NarrationBlock,
    RetentionBeat,
    ScriptBrief,
    ScriptExportProfile,
    ScriptSection,
    ScriptTask,
    ScriptVariant,
)
from core.departments.script.pipeline import PipelineStage, ScriptProductionPipeline
from core.events.bus import EventBus
from core.runtime import CompanyRuntime as CoreCompanyRuntime
from core.tools.capabilities import Capability
from core.tools.registry import ToolRegistry
from core.tools.runtime import ToolRuntime


@dataclass(frozen=True, slots=True)
class ScriptCapability:
    """Domain-specific script capability metadata."""
    name: str
    proficiency: float = 0.5
    enabled: bool = True


@dataclass(frozen=True, slots=True)
class ProductionMetrics:
    """Metrics accumulated across a script production run."""
    total_stages: int = 0
    completed_stages: int = 0
    failed_stages: int = 0
    sections_written: int = 0
    hooks_generated: int = 0
    variants_generated: int = 0
    narration_blocks: int = 0
    retention_beats: int = 0
    export_format: str = ""
    word_count: int = 0
    quality_passed: bool = False
    quality_corrections: tuple[str, ...] = field(default_factory=tuple)
    duration_minutes: float = 0.0


class ScriptWriterEmployee(ProductionEmployee):
    """Specialist employee for script production."""

    _DEPARTMENT_KEYWORD = "script"

    def __init__(
        self,
        company_runtime: CoreCompanyRuntime,
        employee_id: UUID,
        skills: tuple[EmployeeSkill, ...] = (),
        *,
        event_bus: EventBus | None = None,
        department_manager: DepartmentManager | None = None,
        tool_runtime: ToolRuntime | None = None,
        tool_registry: ToolRegistry | None = None,
        quality_runtime: QualityRuntime | None = None,
    ) -> None:
        super().__init__(
            company_runtime=company_runtime,
            employee_id=employee_id,
            skills=skills,
            event_bus=event_bus,
            department_manager=department_manager,
            tool_runtime=tool_runtime,
            tool_registry=tool_registry,
            quality_runtime=quality_runtime,
        )
        self._script_capabilities: dict[str, ScriptCapability] = {
            "video_scripts": ScriptCapability(name="video_scripts", proficiency=0.9),
            "short_form": ScriptCapability(name="short_form", proficiency=0.88),
            "narration": ScriptCapability(name="narration", proficiency=0.86),
            "hooks": ScriptCapability(name="hooks", proficiency=0.9),
            "storytelling": ScriptCapability(name="storytelling", proficiency=0.84),
            "retention_structure": ScriptCapability(name="retention_structure", proficiency=0.82),
            "calls_to_action": ScriptCapability(name="calls_to_action", proficiency=0.85),
            "language_adaptation": ScriptCapability(name="language_adaptation", proficiency=0.78),
            "script_variation": ScriptCapability(name="script_variation", proficiency=0.8),
            "creative_briefing": ScriptCapability(name="creative_briefing", proficiency=0.86),
            "text_revision": ScriptCapability(name="text_revision", proficiency=0.87),
        }
        self._current_script_task: ScriptTask | None = None

    # ------------------------------------------------------------------
    # Properties
    # ------------------------------------------------------------------

    @property
    def script_capabilities(self) -> dict[str, ScriptCapability]:
        return dict(self._script_capabilities)

    # ------------------------------------------------------------------
    # Task handling
    # ------------------------------------------------------------------

    def receive_task(self, task: ReceivedTask) -> TaskDecision:
        if not _is_script_department(task.department):
            return super().receive_task(task)

        if self._workload >= self._max_workload:
            return super().receive_task(task)

        self._tasks[task.task_id] = task
        self._current_task_id = task.task_id
        self._workload += 1
        self._status = EmployeeStatus.ANALYZING

        ctx = task.context
        brief = _coerce_brief(ctx.get("brief"), task, ctx)
        export_profile = _coerce_export_profile(ctx.get("export_profile"), brief)

        self._current_script_task = ScriptTask(
            task_id=task.task_id,
            title=task.title,
            script_type=ctx.get("script_type", "video"),
            duration_seconds=ctx.get("duration_seconds", 60),
            brief=brief,
            sections=_coerce_sections(ctx.get("sections", ())),
            hooks=_coerce_hooks(ctx.get("hooks", ())),
            call_to_action=_coerce_cta(ctx.get("call_to_action", ctx.get("cta"))),
            narration_blocks=_coerce_narration_blocks(ctx.get("narration_blocks", ())),
            retention_beats=_coerce_retention_beats(ctx.get("retention_beats", ())),
            variants=_coerce_variants(ctx.get("variants", ()), brief.language),
            export_profile=export_profile,
            quality_rules=tuple(ctx.get("quality_rules", ())),
            metadata=dict(ctx),
        )
        self._pipeline = ScriptProductionPipeline(self._current_script_task)

        self._publish(TaskAccepted(
            employee_id=self._employee_id,
            task_id=task.task_id,
            title=task.title,
            difficulty=0.5,
            estimated_time_minutes=self._estimate_duration(ctx),
            timestamp=time.time(),
        ))
        return TaskDecision.ACCEPTED

    def _check_reject(self, task: ReceivedTask) -> str | None:
        if not _is_script_department(task.department):
            return f"Department '{task.department}' is not script"
        if self._workload >= self._max_workload:
            return "Workload limit reached (max 3)"
        return None

    # ------------------------------------------------------------------
    # Pipeline
    # ------------------------------------------------------------------

    def _build_pipeline(self, task: ReceivedTask) -> ProductionPipeline:
        return ScriptProductionPipeline(self._current_script_task)

    def _estimate_duration(self, ctx: dict[str, Any]) -> int:
        dur = ctx.get("duration_seconds", 60)
        base = max(1, dur // 45)
        script_type = ctx.get("script_type", "video")
        type_factor = {
            "video": 1.5,
            "shorts": 1.0,
            "reels": 1.0,
            "tiktok": 1.0,
            "narration": 1.2,
            "hook": 0.5,
            "storytelling": 2.0,
            "ad": 1.4,
            "tutorial": 2.2,
            "voiceover": 1.2,
        }.get(script_type, 1.0)
        variants = ctx.get("variants", ())
        variant_factor = max(1, len(variants) or 1)
        return max(1, round(base * type_factor + (variant_factor - 1)))

    def _get_production_type(self) -> str:
        if self._current_script_task:
            return self._current_script_task.script_type
        return ""

    # ------------------------------------------------------------------
    # Output building
    # ------------------------------------------------------------------

    def _build_output_from_stages(
        self, final_output: dict[str, Any], summary_parts: list[str],
    ) -> None:
        for slog in self._pipeline.stages_log:
            if slog.stage == PipelineStage.DELIVERING.value:
                final_output.update(slog.output)
                summary_parts.append(slog.summary)
            if slog.stage == PipelineStage.EXPORTING.value:
                final_output["export"] = slog.output
            if slog.stage == PipelineStage.WRITING.value:
                for key in (
                    "hook", "call_to_action", "script_text", "word_count",
                    "narration_blocks_count", "retention_beats_count",
                ):
                    if key in slog.output:
                        final_output[key] = slog.output[key]
            if slog.stage == PipelineStage.STRUCTURING.value:
                final_output["sections_count"] = slog.output.get("sections_count", 0)
            if slog.stage == PipelineStage.VARIATION_GENERATION.value:
                final_output["variants_count"] = slog.output.get("variants_generated", 0)
                final_output["variants"] = slog.output.get("variants", [])
            if slog.stage == PipelineStage.REVISING.value:
                final_output["clarity_score"] = slog.output.get("clarity_score", 0.0)
                final_output["structure_score"] = slog.output.get("structure_score", 0.0)

    def _build_metrics(
        self,
        stages_completed: int,
        stages_failed: int,
        final_output: dict[str, Any],
        duration: float,
    ) -> ProductionMetrics:
        return ProductionMetrics(
            total_stages=stages_completed + stages_failed,
            completed_stages=stages_completed,
            failed_stages=stages_failed,
            sections_written=final_output.get("sections_count", 0),
            hooks_generated=1 if final_output.get("hook") else 0,
            variants_generated=final_output.get("variants_count", 0),
            narration_blocks=final_output.get("narration_blocks_count", 0),
            retention_beats=final_output.get("retention_beats_count", 0),
            export_format=final_output.get("export", {}).get("output_format", ""),
            word_count=final_output.get("word_count", 0),
            quality_passed=final_output.get("quality_passed", True),
            quality_corrections=tuple(final_output.get("quality_issues", [])),
            duration_minutes=round(duration, 2),
        )

    def _build_summary(self, success: bool, summary_parts: list[str]) -> str:
        if summary_parts:
            return " | ".join(summary_parts)
        return "Script production completed" if success else "Script production failed"

    # ------------------------------------------------------------------
    # Quality
    # ------------------------------------------------------------------

    def _run_quality_check(self, output: dict[str, Any]) -> tuple[bool, list[str]]:
        if self._quality_runtime is None:
            return True, []

        exec_id = self._current_task_id or UUID(int=0)
        export = output.get("export", {})
        report = self._quality_runtime.validate(exec_id, {
            "success": output.get("error", "") == "",
            "error": output.get("error", ""),
            "output_format": export.get("output_format", ""),
            "script_type": output.get("script_type", ""),
            "target_audience": output.get("target_audience", ""),
            "objective": output.get("objective", ""),
            "hook_present": bool(output.get("hook")),
            "cta_present": bool(output.get("call_to_action")),
            "sections_count": output.get("sections_count", 0),
            "variants_count": output.get("variants_count", 0),
            "language": output.get("language", ""),
        })

        if report.passed:
            return True, []
        return False, self._quality_runtime.generate_correction(report)

    # ------------------------------------------------------------------
    # Capability analysis
    # ------------------------------------------------------------------

    def analyze_capability_needs(self) -> tuple[Capability, ...]:
        needed: list[Capability] = [
            Capability.TEXT_GENERATION,
            Capability.DOCUMENT_GENERATION,
        ]

        task = self._current_script_task
        if task is not None:
            if task.brief.key_points or task.metadata.get("requires_research"):
                needed.append(Capability.WEB_SEARCH)
            if task.metadata.get("requires_browser_research"):
                needed.append(Capability.BROWSER_AUTOMATION)
            source_language = task.metadata.get("source_language")
            if source_language and source_language != task.brief.language:
                needed.append(Capability.TRANSLATION)
            if task.variants:
                needed.append(Capability.STORAGE)

        return tuple(dict.fromkeys(needed))

    # ------------------------------------------------------------------
    # State
    # ------------------------------------------------------------------

    def state(self) -> dict[str, Any]:
        base = super().state()
        base["script_capabilities"] = {
            k: {"name": v.name, "proficiency": v.proficiency, "enabled": v.enabled}
            for k, v in self._script_capabilities.items()
        }
        base["current_script_task"] = (
            {
                "title": self._current_script_task.title,
                "script_type": self._current_script_task.script_type,
                "duration_seconds": self._current_script_task.duration_seconds,
                "platform": self._current_script_task.brief.platform,
                "language": self._current_script_task.brief.language,
            }
            if self._current_script_task else None
        )
        metrics = base["production_metrics"]
        metrics["sections_written"] = getattr(self._production_metrics, "sections_written", 0)
        metrics["hooks_generated"] = getattr(self._production_metrics, "hooks_generated", 0)
        metrics["variants_generated"] = getattr(self._production_metrics, "variants_generated", 0)
        metrics["narration_blocks"] = getattr(self._production_metrics, "narration_blocks", 0)
        metrics["retention_beats"] = getattr(self._production_metrics, "retention_beats", 0)
        metrics["export_format"] = getattr(self._production_metrics, "export_format", "")
        metrics["word_count"] = getattr(self._production_metrics, "word_count", 0)
        return base


# ==================================================================
# Coercion helpers
# ==================================================================


def _is_script_department(department: str) -> bool:
    lowered = department.lower()
    return "script" in lowered or "roteiro" in lowered


def _coerce_brief(raw: Any, task: ReceivedTask, ctx: dict[str, Any]) -> ScriptBrief:
    if isinstance(raw, ScriptBrief):
        return raw
    data = raw if isinstance(raw, dict) else {}
    return ScriptBrief(
        topic=data.get("topic", ctx.get("topic", task.title)),
        objective=data.get("objective", ctx.get("objective", task.description)),
        target_audience=data.get("target_audience", ctx.get("target_audience", "")),
        tone=data.get("tone", ctx.get("tone", "clear")),
        language=data.get("language", ctx.get("language", "pt-BR")),
        platform=data.get("platform", ctx.get("platform", "youtube")),
        key_points=tuple(data.get("key_points", ctx.get("key_points", ()))),
        constraints=tuple(data.get("constraints", ctx.get("constraints", ()))),
        metadata=dict(data.get("metadata", {})),
    )


def _coerce_export_profile(raw: Any, brief: ScriptBrief) -> ScriptExportProfile:
    if isinstance(raw, ScriptExportProfile):
        return raw
    data = raw if isinstance(raw, dict) else {}
    return ScriptExportProfile(
        format=data.get("format", "markdown"),
        language=data.get("language", brief.language),
        include_timestamps=data.get("include_timestamps", True),
        include_narration=data.get("include_narration", True),
        include_sections=data.get("include_sections", True),
        platform_template=data.get("platform_template", brief.platform),
        metadata=dict(data.get("metadata", {})),
    )


def _coerce_sections(raw: Any) -> tuple[ScriptSection, ...]:
    items = _as_iterable(raw)
    return tuple(
        item if isinstance(item, ScriptSection) else ScriptSection(
            name=item.get("name", "section"),
            purpose=item.get("purpose", ""),
            target_duration_seconds=item.get("target_duration_seconds", 10),
            content=item.get("content", ""),
            order=item.get("order", idx + 1),
            metadata=dict(item.get("metadata", {})),
        )
        for idx, item in enumerate(items) if isinstance(item, (ScriptSection, dict))
    )


def _coerce_hooks(raw: Any) -> tuple[HookVariant, ...]:
    items = _as_iterable(raw)
    return tuple(
        item if isinstance(item, HookVariant) else HookVariant(
            text=item.get("text", ""),
            style=item.get("style", "curiosity"),
            platform=item.get("platform", ""),
            retention_score=item.get("retention_score", 0.0),
            metadata=dict(item.get("metadata", {})),
        )
        for item in items if isinstance(item, (HookVariant, dict))
    )


def _coerce_cta(raw: Any) -> CallToAction | None:
    if raw is None:
        return None
    if isinstance(raw, CallToAction):
        return raw
    if isinstance(raw, str):
        return CallToAction(text=raw)
    if isinstance(raw, dict):
        return CallToAction(
            text=raw.get("text", ""),
            action_type=raw.get("action_type", "engagement"),
            placement=raw.get("placement", "end"),
            urgency=raw.get("urgency", "medium"),
            metadata=dict(raw.get("metadata", {})),
        )
    return None


def _coerce_narration_blocks(raw: Any) -> tuple[NarrationBlock, ...]:
    items = _as_iterable(raw)
    return tuple(
        item if isinstance(item, NarrationBlock) else NarrationBlock(
            speaker=item.get("speaker", "narrator"),
            text=item.get("text", ""),
            start_time=item.get("start_time", 0.0),
            duration_seconds=item.get("duration_seconds", 5.0),
            style=item.get("style", "natural"),
            metadata=dict(item.get("metadata", {})),
        )
        for item in items if isinstance(item, (NarrationBlock, dict))
    )


def _coerce_retention_beats(raw: Any) -> tuple[RetentionBeat, ...]:
    items = _as_iterable(raw)
    return tuple(
        item if isinstance(item, RetentionBeat) else RetentionBeat(
            timestamp_seconds=item.get("timestamp_seconds", 0.0),
            technique=item.get("technique", "pattern_interrupt"),
            message=item.get("message", ""),
            metadata=dict(item.get("metadata", {})),
        )
        for item in items if isinstance(item, (RetentionBeat, dict))
    )


def _coerce_variants(raw: Any, language: str) -> tuple[ScriptVariant, ...]:
    items = _as_iterable(raw)
    return tuple(
        item if isinstance(item, ScriptVariant) else ScriptVariant(
            name=item.get("name", "variant"),
            angle=item.get("angle", ""),
            hook=item.get("hook", ""),
            body=item.get("body", ""),
            call_to_action=item.get("call_to_action", ""),
            language=item.get("language", language),
            metadata=dict(item.get("metadata", {})),
        )
        for item in items if isinstance(item, (ScriptVariant, dict))
    )


def _as_iterable(raw: Any) -> tuple[Any, ...]:
    if raw is None:
        return ()
    if isinstance(raw, tuple):
        return raw
    if isinstance(raw, list):
        return tuple(raw)
    return (raw,)
