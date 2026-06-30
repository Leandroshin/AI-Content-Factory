"""Service registry contracts for AI Content Factory."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from .models import Lifetime, ServiceFactory, ServiceProvider


class ServiceRegistry(ABC):
    """Base contract for service registration."""

    @abstractmethod
    def register_factory(
        self,
        service_name: str,
        factory: ServiceFactory,
        lifetime: Lifetime = Lifetime.TRANSIENT,
    ) -> None:
        """Register a service factory placeholder."""

    @abstractmethod
    def register_provider(
        self,
        service_name: str,
        provider: ServiceProvider,
    ) -> None:
        """Register a service provider placeholder."""

    @abstractmethod
    def get(self, service_name: str) -> Any:
        """Return a registered service placeholder."""
