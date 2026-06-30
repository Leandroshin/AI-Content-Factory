"""Validation contracts for the Script Engine."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Protocol

from .models import ScriptRequest


class ScriptInputValidator(Protocol):
    """Contract for validating script inputs."""

    def validate_topic(self, topic: str) -> None:
        """Validate a topic placeholder."""

    def validate_request(self, request: ScriptRequest) -> None:
        """Validate a request placeholder."""


class BaseScriptValidator(ABC):
    """Base contract for script validation."""

    @abstractmethod
    def validate_topic(self, topic: str) -> None:
        """Validate a topic placeholder."""

    @abstractmethod
    def validate_request(self, request: ScriptRequest) -> None:
        """Validate a request placeholder."""
