"""Script Engine for AI Content Factory."""

from __future__ import annotations

from abc import ABC, abstractmethod

from engines.base import BaseEngine, EngineCapability, EngineContext

from .contracts import ScriptContracts
from .models import ScriptRequest, ScriptResponse


class ScriptEngine(ScriptContracts, BaseEngine, ABC):
    """Base contract for the Script Engine."""

    name = "script"
    capabilities = (EngineCapability.READ, EngineCapability.TRANSFORM)

    @abstractmethod
    def build_context(self, project_name: str | None = None) -> EngineContext:
        """Build an execution context placeholder."""

    @abstractmethod
    def prepare_request(
        self,
        action: str,
        payload: dict[str, object],
    ) -> ScriptRequest:
        """Prepare a script request placeholder."""

    @abstractmethod
    def execute(self, request: ScriptRequest, context: EngineContext) -> ScriptResponse:
        """Execute a script request placeholder."""
