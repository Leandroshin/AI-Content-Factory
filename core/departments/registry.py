"""Department registry contracts for AI Content Factory."""

from __future__ import annotations

from abc import ABC, abstractmethod

from .contracts import BaseDepartmentRegistry
from .models import Department


class DepartmentRegistry(BaseDepartmentRegistry, ABC):
    """Base department registry contract."""

    @abstractmethod
    def get(self, name: str) -> Department | None:
        """Return a department placeholder by name."""

    @abstractmethod
    def list(self) -> list[Department]:
        """Return department placeholders."""
