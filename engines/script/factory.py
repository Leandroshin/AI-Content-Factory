"""Factory contracts for the Script Engine."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Protocol

from engines.base import EngineContext

from .models import ScriptGenerationMode, ScriptRequest, ScriptResponse


class ScriptObjectFactory(Protocol):
    """Contract for creating script engine internal objects."""

    def create_context(self, project_name: str | None = None) -> EngineContext:
        """Create a context placeholder."""

    def create_request(self, topic: str, mode: ScriptGenerationMode) -> ScriptRequest:
        """Create a request placeholder."""

    def create_response(self) -> ScriptResponse:
        """Create a response placeholder."""


class BaseScriptObjectFactory(ABC):
    """Base contract for Script Engine object factories."""

    @abstractmethod
    def create_context(self, project_name: str | None = None) -> EngineContext:
        """Create a context placeholder."""

    @abstractmethod
    def create_request(self, topic: str, mode: ScriptGenerationMode) -> ScriptRequest:
        """Create a request placeholder."""

    @abstractmethod
    def create_response(self) -> ScriptResponse:
        """Create a response placeholder."""
