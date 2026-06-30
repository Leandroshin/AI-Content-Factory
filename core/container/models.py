"""Dependency container contracts for AI Content Factory."""

from __future__ import annotations

from abc import ABC, abstractmethod
from enum import StrEnum
from typing import Any, Callable


class Lifetime(StrEnum):
    """Supported dependency lifetimes."""

    SINGLETON = "singleton"
    SCOPED = "scoped"
    TRANSIENT = "transient"


class ServiceProvider(ABC):
    """Base contract for service providers."""

    lifetime: Lifetime

    @abstractmethod
    def create(self) -> Any:
        """Return a placeholder service instance."""


ServiceFactory = Callable[[], Any]
