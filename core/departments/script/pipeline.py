"""Deterministic script production pipeline.

Each stage advances through a rule-based state machine.
No AI, no LLM, no external API.
"""

from __future__ import annotations

from enum import StrEnum
from typing import Any

from core.departments.base.pipeline import ProductionPipeline, StageResult
from core.departments.script.models import (
    CallToAction,
    HookVariant,
    NarrationBlock,
    RetentionBeat,
    ScriptBrief,
    ScriptExportProfile,
    ScriptSection,
    ScriptTask,
)


class PipelineStage(StrEnum):
    """Stages of the script production pipeline."""
    CREATED = "created"
    ANALYZING = "analyzing"
    RESEARCHING_CONTEXT = "researching_context"
    STRUCTURING = "structuring"
    WRITING = "writing"
    REVISING = "revising"
    VARIATION_GENERATION = "variation_generation"
    EXPORTING = "exporting"
    DELIVERING = "delivering"
    COMPLETED = "completed"
    FAILED = "failed"


class ScriptProductionPipeline(ProductionPipeline):
    """Deterministic script production state machine."""

    def __init__(self, task: ScriptTask) -> None:
        super().__init__()
        self._task = task
        self._stage: str = PipelineStage.CREATED.value
        self._research_notes: tuple[str, ...] = ()
        self._outline: tuple[dict[str, Any], ...] = ()
        self._script_output: dict[str, Any] = {}
        self._variants_output: tuple[dict[str, Any], ...] = ()
        self._export_output: dict[str, Any] = {}

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    @property
    def stage(self) -> str:
        return self._stage

    @property
    def task(self) -> ScriptTask:
        return self._task

    @property
    def progress(self) -> float:
        stages = list(PipelineStage)
        try:
            idx = stages.index(PipelineStage(self._stage))
            return round((idx / (len(stages) - 1)) * 100, 1)
        except (ValueError, KeyError):
            return 0.0

    def advance(self) -> StageResult:
        handlers = {
            PipelineStage.CREATED: self._stage_created,
            PipelineStage.ANALYZING: self._stage_analyzing,
            PipelineStage.RESEARCHING_CONTEXT: self._stage_researching_context,
            PipelineStage.STRUCTURING: self._stage_structuring,
            PipelineStage.WRITING: self._stage_writing,
            PipelineStage.REVISING: self._stage_revising,
            PipelineStage.VARIATION_GENERATION: self._stage_variation_generation,
            PipelineStage.EXPORTING: self._stage_exporting,
            PipelineStage.DELIVERING: self._stage_delivering,
        }

        try:
            current = PipelineStage(self._stage)
        except (ValueError, KeyError):
            self._stages_log.append(StageResult(
                stage=self._stage, success=False, error=f"Unknown stage: {self._stage}",
            ))
            self._stage = PipelineStage.FAILED.value
            return self._stages_log[-1]

        handler = handlers.get(current)
        if handler is None:
            self._stages_log.append(StageResult(
                stage=self._stage, success=False, error=f"No handler for: {self._stage}",
            ))
            self._stage = PipelineStage.FAILED.value
            return self._stages_log[-1]

        result = handler()
        self._stages_log.append(result)
        if result.next_stage:
            self._stage = result.next_stage
        elif result.success:
            self._stage = self._next_stage(current).value
        else:
            self._stage = PipelineStage.FAILED.value

        return result

    def reset(self) -> None:
        super().reset()
        self._stage = PipelineStage.CREATED.value
        self._research_notes = ()
        self._outline = ()
        self._script_output = {}
        self._variants_output = ()
        self._export_output = {}

    # ------------------------------------------------------------------
    # Stage handlers
    # ------------------------------------------------------------------

    def _stage_created(self) -> StageResult:
        return StageResult(
            stage=PipelineStage.CREATED.value,
            success=True,
            summary=f"Task '{self._task.title}' created",
            output={"task_id": str(self._task.task_id), "script_type": self._task.script_type},
            next_stage=PipelineStage.ANALYZING.value,
        )

    def _stage_analyzing(self) -> StageResult:
        st = self._task.script_type
        valid_types = (
            "video", "shorts", "reels", "tiktok", "narration",
            "hook", "storytelling", "ad", "tutorial", "voiceover",
        )
        if st not in valid_types:
            return StageResult(
                stage=PipelineStage.ANALYZING.value,
                success=False,
                error=f"Unsupported script type: '{st}'. Must be one of {valid_types}",
            )
        if self._task.duration_seconds <= 0:
            return StageResult(
                stage=PipelineStage.ANALYZING.value,
                success=False,
                error="Duration must be greater than zero",
            )

        brief = self._task.brief
        analysis = {
            "script_type": st,
            "duration_seconds": self._task.duration_seconds,
            "topic": brief.topic,
            "objective": brief.objective,
            "target_audience": brief.target_audience,
            "tone": brief.tone,
            "language": brief.language,
            "platform": brief.platform,
            "hooks_count": len(self._task.hooks),
            "sections_count": len(self._task.sections),
            "variants_count": len(self._task.variants),
            "required_capabilities": list(self._task.requires_capabilities),
        }
        return StageResult(
            stage=PipelineStage.ANALYZING.value,
            success=True,
            summary=f"Analyzed: {st}, {brief.platform}, {self._task.duration_seconds}s",
            output=analysis,
            next_stage=PipelineStage.RESEARCHING_CONTEXT.value,
        )

    def _stage_researching_context(self) -> StageResult:
        brief = self._task.brief
        notes = list(brief.key_points)
        if not notes:
            notes.append(_fallback_key_point(brief, self._task.title))
        if brief.objective:
            notes.append(f"Objective: {brief.objective}")
        if brief.target_audience:
            notes.append(f"Audience: {brief.target_audience}")
        self._research_notes = tuple(notes)

        return StageResult(
            stage=PipelineStage.RESEARCHING_CONTEXT.value,
            success=True,
            summary=f"Context researched: {len(self._research_notes)} note(s)",
            output={
                "context_notes": list(self._research_notes),
                "constraints_count": len(brief.constraints),
            },
            next_stage=PipelineStage.STRUCTURING.value,
        )

    def _stage_structuring(self) -> StageResult:
        sections = self._task.sections or _default_sections(self._task)
        outline = tuple(
            {
                "name": section.name,
                "purpose": section.purpose or _purpose_for_section(section.name),
                "duration_seconds": section.target_duration_seconds,
                "order": section.order,
            }
            for section in sections
        )
        self._outline = outline

        return StageResult(
            stage=PipelineStage.STRUCTURING.value,
            success=True,
            summary=f"Structured: {len(outline)} section(s)",
            output={
                "sections_count": len(outline),
                "outline": list(outline),
                "retention_beats_count": len(self._task.retention_beats),
            },
            next_stage=PipelineStage.WRITING.value,
        )

    def _stage_writing(self) -> StageResult:
        brief = self._task.brief
        sections = self._task.sections or _default_sections(self._task)
        hook = _select_hook(self._task.hooks, brief, self._task.title)
        cta = _select_cta(self._task.call_to_action, brief.platform)
        body_parts = [
            _section_text(section, brief, idx, self._research_notes)
            for idx, section in enumerate(sections)
        ]
        retention_lines = [
            f"[{round(beat.timestamp_seconds)}s] {beat.technique}: {beat.message}"
            for beat in self._task.retention_beats if beat.message
        ]
        narration = _narration_blocks(self._task.narration_blocks, body_parts)

        script_text = "\n\n".join(
            part for part in (
                f"HOOK: {hook.text}",
                *body_parts,
                "RETENTION:\n" + "\n".join(retention_lines) if retention_lines else "",
                f"CTA: {cta.text}",
            )
            if part
        )
        word_count = _word_count(script_text)
        self._script_output = {
            "hook": hook.text,
            "hook_style": hook.style,
            "call_to_action": cta.text,
            "cta_type": cta.action_type,
            "script_text": script_text,
            "word_count": word_count,
            "sections_written": len(sections),
            "narration_blocks": narration,
            "narration_blocks_count": len(narration),
            "retention_beats_count": len(self._task.retention_beats),
        }

        return StageResult(
            stage=PipelineStage.WRITING.value,
            success=True,
            summary=f"Written: {word_count} words, hook and CTA included",
            output=dict(self._script_output),
            next_stage=PipelineStage.REVISING.value,
        )

    def _stage_revising(self) -> StageResult:
        word_count = self._script_output.get("word_count", 0)
        target_words = max(25, round(self._task.duration_seconds * 2.3))
        clarity_score = min(1.0, round(word_count / target_words, 2))
        structure_score = 1.0 if self._outline else 0.5
        has_hook = bool(self._script_output.get("hook"))
        has_cta = bool(self._script_output.get("call_to_action"))

        return StageResult(
            stage=PipelineStage.REVISING.value,
            success=True,
            summary=f"Revised: clarity={clarity_score}, structure={structure_score}",
            output={
                "clarity_score": clarity_score,
                "structure_score": structure_score,
                "has_hook": has_hook,
                "has_cta": has_cta,
                "target_words": target_words,
            },
            next_stage=PipelineStage.VARIATION_GENERATION.value,
        )

    def _stage_variation_generation(self) -> StageResult:
        variants = self._task.variants
        generated: list[dict[str, Any]] = []
        if not variants:
            generated.append(_default_variant(self._task, self._script_output))
        else:
            for variant in variants:
                generated.append({
                    "name": variant.name,
                    "angle": variant.angle or "core",
                    "hook": variant.hook or self._script_output.get("hook", ""),
                    "body": variant.body or self._script_output.get("script_text", ""),
                    "call_to_action": (
                        variant.call_to_action
                        or self._script_output.get("call_to_action", "")
                    ),
                    "language": variant.language,
                })
        self._variants_output = tuple(generated)

        return StageResult(
            stage=PipelineStage.VARIATION_GENERATION.value,
            success=True,
            summary=f"Variations: {len(self._variants_output)} variant(s)",
            output={
                "variants_generated": len(self._variants_output),
                "variants": list(self._variants_output),
            },
            next_stage=PipelineStage.EXPORTING.value,
        )

    def _stage_exporting(self) -> StageResult:
        export = self._task.export_profile or ScriptExportProfile(
            language=self._task.brief.language,
            platform_template=self._task.brief.platform,
        )
        self._export_output = {
            "output_format": export.format,
            "output_language": export.language,
            "platform_template": export.platform_template,
            "include_timestamps": export.include_timestamps,
            "include_narration": export.include_narration,
            "include_sections": export.include_sections,
            "word_count": self._script_output.get("word_count", 0),
            "estimated_read_time_seconds": _estimate_read_time_seconds(
                self._script_output.get("word_count", 0)
            ),
            "sections_count": len(self._outline),
            "variants_count": len(self._variants_output),
            "has_hook": bool(self._script_output.get("hook")),
            "has_cta": bool(self._script_output.get("call_to_action")),
        }
        return StageResult(
            stage=PipelineStage.EXPORTING.value,
            success=True,
            summary=f"Exported: {export.format}, {len(self._variants_output)} variant(s)",
            output=dict(self._export_output),
            next_stage=PipelineStage.DELIVERING.value,
        )

    def _stage_delivering(self) -> StageResult:
        brief = self._task.brief
        delivery = {
            "task_id": str(self._task.task_id),
            "title": self._task.title,
            "script_type": self._task.script_type,
            "duration_seconds": self._task.duration_seconds,
            "target_audience": brief.target_audience,
            "objective": brief.objective,
            "language": brief.language,
            "platform": brief.platform,
            "hook": self._script_output.get("hook", ""),
            "call_to_action": self._script_output.get("call_to_action", ""),
            "script_text": self._script_output.get("script_text", ""),
            "word_count": self._script_output.get("word_count", 0),
            "export": dict(self._export_output),
            "sections_count": len(self._outline),
            "variants_count": len(self._variants_output),
            "variants": list(self._variants_output),
            "narration_blocks_count": self._script_output.get("narration_blocks_count", 0),
            "retention_beats_count": self._script_output.get("retention_beats_count", 0),
        }
        return StageResult(
            stage=PipelineStage.DELIVERING.value,
            success=True,
            summary=f"Delivered: '{self._task.title}' ({self._task.script_type}, "
                    f"{delivery['word_count']} words)",
            output=delivery,
            next_stage=PipelineStage.COMPLETED.value,
        )

    @staticmethod
    def _next_stage(current: PipelineStage) -> PipelineStage:
        stages = list(PipelineStage)
        idx = stages.index(current)
        if idx + 1 < len(stages):
            return stages[idx + 1]
        return PipelineStage.COMPLETED


# ==================================================================
# Module-level helpers
# ==================================================================


def _fallback_key_point(brief: ScriptBrief, title: str) -> str:
    topic = brief.topic or title or "topic"
    audience = brief.target_audience or "audience"
    return f"Explain {topic} for {audience}"


def _default_sections(task: ScriptTask) -> tuple[ScriptSection, ...]:
    duration = task.duration_seconds
    if task.script_type in ("shorts", "reels", "tiktok"):
        return (
            ScriptSection(name="hook", purpose="Stop scroll", target_duration_seconds=3, order=1),
            ScriptSection(name="value", purpose="Deliver core point", target_duration_seconds=max(8, duration - 8), order=2),
            ScriptSection(name="cta", purpose="Drive action", target_duration_seconds=5, order=3),
        )
    return (
        ScriptSection(name="hook", purpose="Open with a clear promise", target_duration_seconds=8, order=1),
        ScriptSection(name="context", purpose="Frame the problem", target_duration_seconds=max(10, duration // 4), order=2),
        ScriptSection(name="story", purpose="Develop the narrative", target_duration_seconds=max(20, duration // 2), order=3),
        ScriptSection(name="cta", purpose="Close with action", target_duration_seconds=8, order=4),
    )


def _purpose_for_section(name: str) -> str:
    return {
        "hook": "Capture attention",
        "context": "Set up context",
        "story": "Move the narrative",
        "value": "Deliver useful value",
        "cta": "Ask for action",
    }.get(name, "Support the script objective")


def _select_hook(
    hooks: tuple[HookVariant, ...], brief: ScriptBrief, title: str
) -> HookVariant:
    if hooks:
        return hooks[0]
    topic = brief.topic or title
    audience = brief.target_audience or "your audience"
    return HookVariant(
        text=f"What if {audience} could understand {topic} in one clear story?",
        style="curiosity",
        platform=brief.platform,
        retention_score=0.75,
    )


def _select_cta(cta: CallToAction | None, platform: str) -> CallToAction:
    if cta is not None:
        return cta
    return CallToAction(
        text=f"Follow for the next practical step on {platform}.",
        action_type="engagement",
        placement="end",
        urgency="medium",
    )


def _section_text(
    section: ScriptSection,
    brief: ScriptBrief,
    index: int,
    notes: tuple[str, ...],
) -> str:
    if section.content:
        return f"{section.name.upper()}: {section.content}"
    note = notes[index % len(notes)] if notes else _fallback_key_point(brief, section.name)
    tone = brief.tone or "clear"
    objective = brief.objective or "move the audience to the next step"
    return (
        f"{section.name.upper()}: Use a {tone} tone to connect '{note}' "
        f"with the objective: {objective}."
    )


def _narration_blocks(
    blocks: tuple[NarrationBlock, ...], body_parts: list[str]
) -> list[dict[str, Any]]:
    if blocks:
        return [
            {
                "speaker": block.speaker,
                "text": block.text,
                "start_time": block.start_time,
                "duration_seconds": block.duration_seconds,
                "style": block.style,
            }
            for block in blocks
        ]
    return [
        {
            "speaker": "narrator",
            "text": part,
            "start_time": float(idx * 10),
            "duration_seconds": 10.0,
            "style": "natural",
        }
        for idx, part in enumerate(body_parts)
    ]


def _default_variant(task: ScriptTask, script_output: dict[str, Any]) -> dict[str, Any]:
    return {
        "name": "base",
        "angle": task.brief.objective or "core message",
        "hook": script_output.get("hook", ""),
        "body": script_output.get("script_text", ""),
        "call_to_action": script_output.get("call_to_action", ""),
        "language": task.brief.language,
    }


def _word_count(text: str) -> int:
    return len([part for part in text.replace("\n", " ").split(" ") if part.strip()])


def _estimate_read_time_seconds(word_count: int) -> int:
    words_per_second = 2.5
    return max(1, round(word_count / words_per_second))
