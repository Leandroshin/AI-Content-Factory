"""Script Department - specialized script production for AI Company."""

from __future__ import annotations

from .employee import ScriptWriterEmployee
from .models import (
    CallToAction,
    HookVariant,
    NarrationBlock,
    RetentionBeat,
    ScriptBrief,
    ScriptExportProfile,
    ScriptProject,
    ScriptSection,
    ScriptTask,
    ScriptVariant,
)
from .pipeline import PipelineStage, ScriptProductionPipeline

__all__ = [
    "CallToAction",
    "HookVariant",
    "NarrationBlock",
    "PipelineStage",
    "RetentionBeat",
    "ScriptBrief",
    "ScriptExportProfile",
    "ScriptProductionPipeline",
    "ScriptProject",
    "ScriptSection",
    "ScriptTask",
    "ScriptVariant",
    "ScriptWriterEmployee",
]
