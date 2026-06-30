"""Request builders for the Script Engine."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Protocol

from .models import ScriptGenerationMode, ScriptRequest


class ScriptRequestBuilder(Protocol):
    """Contract for building script requests."""

    def build(self, topic: str, mode: ScriptGenerationMode) -> ScriptRequest:
        """Build a script request placeholder."""


class BaseScriptRequestBuilder(ABC):
    """Base contract for script request builders."""

    @abstractmethod
    def build(self, topic: str, mode: ScriptGenerationMode) -> ScriptRequest:
        """Build a script request placeholder."""
