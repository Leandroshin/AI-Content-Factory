"""Logging models for AI Content Factory."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path
from typing import Mapping, Any


class LogLevel(StrEnum):
    """Supported logging levels."""

    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


class LogFormat(StrEnum):
    """Supported log output formats."""

    TEXT = "text"
    JSON = "json"


@dataclass(frozen=True, slots=True)
class LoggerContext:
    """Context attached to log records."""

    module: str
    project: str | None = None
    engine: str | None = None
    correlation_id: str | None = None


@dataclass(frozen=True, slots=True)
class CorrelationContext:
    """Correlation metadata for tracing events."""

    correlation_id: str
    request_id: str | None = None


@dataclass(frozen=True, slots=True)
class LogEntry:
    """Structured log entry contract."""

    level: LogLevel
    message: str
    context: LoggerContext
    extra: Mapping[str, Any] | None = None
    destination: Path | None = None