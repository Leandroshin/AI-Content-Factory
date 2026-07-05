"""Task priority definitions for AI Content Factory."""

from __future__ import annotations

from enum import StrEnum


class TaskPriority(StrEnum):
    """Priority levels for tasks."""

    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    CRITICAL = "critical"