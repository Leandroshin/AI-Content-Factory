"""Formatter contracts for the logging subsystem."""

from __future__ import annotations

from abc import ABC, abstractmethod

from .models import LogEntry, LogFormat


class LogFormatter(ABC):
    """Base formatter contract."""

    format: LogFormat

    @abstractmethod
    def format_entry(self, entry: LogEntry) -> str:
        """Return the serialized representation for a log entry."""


class TextLogFormatter(LogFormatter):
    """Placeholder formatter for textual logs."""

    format = LogFormat.TEXT

    def format_entry(self, entry: LogEntry) -> str:
        return entry.message


class JsonLogFormatter(LogFormatter):
    """Placeholder formatter for JSON logs."""

    format = LogFormat.JSON

    def format_entry(self, entry: LogEntry) -> str:
        return entry.message