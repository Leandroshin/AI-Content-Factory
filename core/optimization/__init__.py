"""Auto Optimization Runtime package for AI Content Factory."""

from __future__ import annotations

from .runtime import (
    ACTION_STATE_COMPLETED,
    ACTION_STATE_FAILED,
    ACTION_STATE_MANUAL,
    ACTION_STATE_PENDING,
    ACTION_STATE_ROLLED_BACK,
    ACTION_STATE_RUNNING,
    ACTION_STATE_SKIPPED,
    AutoOptimizationRuntime,
    DEFAULT_COOLDOWN_SECONDS,
    DEFAULT_MAX_RETRIES,
    DEFAULT_RETRY_DELAY_SECONDS,
    OPTIMIZATION_DOMAIN,
    OptimizationActionState,
    OptimizationExecution,
    OptimizationResult,
    OptimizationSnapshot,
    OptimizationTrace,
)

__all__ = [
    "ACTION_STATE_COMPLETED",
    "ACTION_STATE_FAILED",
    "ACTION_STATE_MANUAL",
    "ACTION_STATE_PENDING",
    "ACTION_STATE_ROLLED_BACK",
    "ACTION_STATE_RUNNING",
    "ACTION_STATE_SKIPPED",
    "AutoOptimizationRuntime",
    "DEFAULT_COOLDOWN_SECONDS",
    "DEFAULT_MAX_RETRIES",
    "DEFAULT_RETRY_DELAY_SECONDS",
    "OPTIMIZATION_DOMAIN",
    "OptimizationActionState",
    "OptimizationExecution",
    "OptimizationResult",
    "OptimizationSnapshot",
    "OptimizationTrace",
]
