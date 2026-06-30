"""Service container contracts for AI Content Factory."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from .resolver import DependencyResolver
from .registry import ServiceRegistry


class ServiceContainer(ABC):
    """Base contract for the application service container."""

    registry: ServiceRegistry

    @abstractmethod
    def resolve(self, service_name: str) -> Any:
        """Resolve a registered dependency placeholder."""

    @abstractmethod
    def scope(self) -> DependencyResolver:
        """Return a scoped resolver placeholder."""
