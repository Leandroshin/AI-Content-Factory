"""Public interfaces for the Script Engine."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Protocol

from engines.base import EngineContext

from .models import ScriptGenerationMode, ScriptRequest, ScriptResponse


class ScriptEnginePublicInterface(ABC):
    """Public contract for the Script Engine."""

    @abstractmethod
    def build_context(self, project_name: str | None = None) -> EngineContext:
        """Build an execution context placeholder."""

    @abstractmethod
    def build_script_request(self, topic: str, mode: ScriptGenerationMode) -> ScriptRequest:
        """Build a script request placeholder."""

    @abstractmethod
    def validate_topic(self, topic: str) -> None:
        """Validate a topic placeholder."""

    @abstractmethod
    def validate_request(self, request: ScriptRequest) -> None:
        """Validate a request placeholder."""

    @abstractmethod
    def parse_response(self, response: ScriptResponse) -> ScriptResponse:
        """Parse a response placeholder into a normalized response."""


class ScriptEngineProtocol(Protocol):
    """Structural protocol for the Script Engine."""

    def build_context(self, project_name: str | None = None) -> EngineContext:
        """Build an execution context placeholder."""

    def build_script_request(self, topic: str, mode: ScriptGenerationMode) -> ScriptRequest:
        """Build a script request placeholder."""

    def validate_topic(self, topic: str) -> None:
        """Validate a topic placeholder."""

    def validate_request(self, request: ScriptRequest) -> None:
        """Validate a request placeholder."""

    def parse_response(self, response: ScriptResponse) -> ScriptResponse:
        """Parse a response placeholder into a normalized response."""
