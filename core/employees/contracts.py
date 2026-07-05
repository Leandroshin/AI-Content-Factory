"""Employee contracts for AI Content Factory."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Protocol

from .models import Employee, EmployeeContext, EmployeeId, EmployeeProfile


class EmployeeRegistryContract(Protocol):
    """Structural contract for employee registries."""

    def get(self, employee_id: EmployeeId) -> Employee | None:
        """Return an employee placeholder by identifier."""

    def list(self) -> list[Employee]:
        """Return employee placeholders."""


class EmployeeValidatorContract(Protocol):
    """Structural contract for employee validators."""

    def validate(self, employee: Employee) -> None:
        """Validate an employee placeholder."""

    def validate_context(self, context: EmployeeContext) -> None:
        """Validate an employee context placeholder."""

    def validate_profile(self, profile: EmployeeProfile) -> None:
        """Validate an employee profile placeholder."""


class EmployeeFactoryContract(Protocol):
    """Structural contract for employee factories."""

    def create(self, context: EmployeeContext) -> Employee:
        """Create an employee placeholder from context."""


class BaseEmployeeRegistry(ABC):
    """Base contract for employee registries."""

    @abstractmethod
    def get(self, employee_id: EmployeeId) -> Employee | None:
        """Return an employee placeholder by identifier."""

    @abstractmethod
    def list(self) -> list[Employee]:
        """Return employee placeholders."""

    @abstractmethod
    def register(self, employee: Employee) -> None:
        """Register an employee placeholder."""

    @abstractmethod
    def unregister(self, employee_id: EmployeeId) -> None:
        """Remove an employee placeholder from the registry."""


class BaseEmployeeValidator(ABC):
    """Base contract for employee validators."""

    @abstractmethod
    def validate(self, employee: Employee) -> None:
        """Validate an employee placeholder."""

    @abstractmethod
    def validate_context(self, context: EmployeeContext) -> None:
        """Validate an employee context placeholder."""

    @abstractmethod
    def validate_profile(self, profile: EmployeeProfile) -> None:
        """Validate an employee profile placeholder."""