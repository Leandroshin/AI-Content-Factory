"""Department contracts for AI Content Factory."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Protocol

from .models import Department, DepartmentContext, DepartmentResult, DepartmentType


class DepartmentRegistryContract(Protocol):
    """Structural contract for department registries."""

    def get(self, name: str) -> Department | None:
        """Return a department placeholder by name."""

    def list(self) -> list[Department]:
        """Return department placeholders."""


class DepartmentValidatorContract(Protocol):
    """Structural contract for department validators."""

    def validate(self, department: Department) -> None:
        """Validate a department placeholder."""


class BaseDepartmentRegistry(ABC):
    """Base contract for department registries."""

    @abstractmethod
    def get(self, name: str) -> Department | None:
        """Return a department placeholder by name."""

    @abstractmethod
    def list(self) -> list[Department]:
        """Return department placeholders."""


class BaseDepartmentValidator(ABC):
    """Base contract for department validators."""

    @abstractmethod
    def validate(self, department: Department) -> None:
        """Validate a department placeholder."""
