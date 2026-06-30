"""Provider contracts for AI Content Factory."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any


class ContainerProvider(ABC):
    """Base contract for container providers."""

    @abstractmethod
    def register(self, service_name: str) -> Any:
        """Register a service placeholder in the container."""
