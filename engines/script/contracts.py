"""Script engine contracts for AI Content Factory."""

from __future__ import annotations

from abc import ABC, abstractmethod

from engines.base import BaseEngine, EngineContext

from .models import ScriptGenerationMode, ScriptRequest, ScriptResponse


class ScriptContracts(ABC):
    """Shared contracts for the Script Engine."""

    @abstractmethod
    def build_script_request(self, topic: str, mode: ScriptGenerationMode) -> ScriptRequest:
        """Build a script request placeholder."""

    @abstractmethod
    def parse_response(self, response: ScriptResponse) -> str:
        """Parse a response placeholder into the final text representation."""


class ScriptEngineContract(BaseEngine, ScriptContracts):
    """Base contract for the Script Engine."""

    def build_context(self, project_name: str | None = None) -> EngineContext:
        raise NotImplementedError

    def prepare_request(self, action: str, payload: dict[str, object]) -> ScriptRequest:
        raise NotImplementedError

    def execute(self, request: ScriptRequest, context: EngineContext) -> ScriptResponse:
        raise NotImplementedError
