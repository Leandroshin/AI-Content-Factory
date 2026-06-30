"""Handler contracts for the logging subsystem."""

from __future__ import annotations

from abc import ABC, abstractmethod

from .models import LogEntry


class BaseLogHandler(ABC):
    """Base logging handler contract."""

    @abstractmethod
    def emit(self, entry: LogEntry) -> None:
        """Handle a structured log entry."""


class ConsoleLogHandler(BaseLogHandler):
    """Placeholder console handler."""

    def emit(self, entry: LogEntry) -> None:
        return None


class FileLogHandler(BaseLogHandler):
    """Placeholder file handler."""

    def emit(self, entry: LogEntry) -> None:
        return None