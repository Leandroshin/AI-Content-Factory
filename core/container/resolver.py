"""Dependency resolver contracts for AI Content Factory."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any


class DependencyResolver(ABC):
    """Base contract for dependency resolution."""

    @abstractmethod
    def resolve(self, service_name: str) -> Any:
        """Resolve a dependency by name."""
