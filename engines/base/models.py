"""Shared engine models for AI Content Factory."""

from __future__ import annotations

from abc import ABC, abstractmethod
from enum import StrEnum
from typing import Any
from uuid import UUID, uuid4

from pydantic import BaseModel, ConfigDict, Field


class EngineStatus(StrEnum):
    """Supported engine statuses."""

    IDLE = "idle"
    READY = "ready"
    RUNNING = "running"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    PAUSED = "paused"


class EngineCapability(StrEnum):
    """Shared capability flags for engines."""

    READ = "read"
    WRITE = "write"
    VALIDATE = "validate"
    TRANSFORM = "transform"
    ORCHESTRATE = "orchestrate"


class EngineContext(BaseModel):
    """Execution context shared by engines."""

    model_config = ConfigDict(extra="ignore", populate_by_name=True)

    project_name: str | None = None
    engine_name: str
    correlation_id: str | None = None
    capabilities: list[EngineCapability] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)


class EngineRequest(BaseModel):
    """Shared engine request placeholder."""

    model_config = ConfigDict(extra="ignore", populate_by_name=True)

    id: UUID = Field(default_factory=uuid4)
    action: str
    payload: dict[str, Any] = Field(default_factory=dict)
    metadata: dict[str, Any] = Field(default_factory=dict)


class EngineResponse(BaseModel):
    """Shared engine response placeholder."""

    model_config = ConfigDict(extra="ignore", populate_by_name=True)

    success: bool = False
    engine_name: str | None = None
    status: EngineStatus = EngineStatus.IDLE
    data: dict[str, Any] = Field(default_factory=dict)
    errors: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)


class BaseEngine(ABC):
    """Base contract shared by all engines."""

    name: str
    capabilities: tuple[EngineCapability, ...]

    @abstractmethod
    def build_context(self, project_name: str | None = None) -> EngineContext:
        """Build an execution context placeholder."""

    @abstractmethod
    def prepare_request(self, action: str, payload: dict[str, Any]) -> EngineRequest:
        """Prepare a request placeholder."""

    @abstractmethod
    def execute(
        self,
        request: EngineRequest,
        context: EngineContext,
    ) -> EngineResponse:
        """Execute a request placeholder and return a response placeholder."""