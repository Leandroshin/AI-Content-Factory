"""Response parsing contracts for the Script Engine."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Protocol

from .models import ScriptResponse


class ScriptResponseParser(Protocol):
    """Contract for parsing script responses."""

    def parse(self, response: ScriptResponse) -> ScriptResponse:
        """Parse a response placeholder into a normalized response."""


class BaseScriptResponseParser(ABC):
    """Base contract for script response parsers."""

    @abstractmethod
    def parse(self, response: ScriptResponse) -> ScriptResponse:
        """Parse a response placeholder into a normalized response."""
