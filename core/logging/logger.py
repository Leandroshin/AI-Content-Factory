"""Logger orchestration contracts for AI Content Factory."""

from __future__ import annotations

from dataclasses import dataclass, field

from .handlers import BaseLogHandler
from .models import LogEntry, LoggerContext


@dataclass(slots=True)
class LogManager:
    """Coordinates logging handlers and context."""

    context: LoggerContext
    handlers: list[BaseLogHandler] = field(default_factory=list)

    def log(self, entry: LogEntry) -> None:
        """Dispatch a log entry to the configured handlers."""

        for handler in self.handlers:
            handler.emit(entry)


def get_logger(context: LoggerContext) -> LogManager:
    """Return a logging manager for the given context."""

    return LogManager(context=context)