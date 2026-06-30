"""Department validator contracts for AI Content Factory."""

from __future__ import annotations

from abc import ABC, abstractmethod

from .contracts import BaseDepartmentValidator
from .models import Department


class DepartmentValidator(BaseDepartmentValidator, ABC):
    """Base department validator contract."""

    @abstractmethod
    def validate(self, department: Department) -> None:
        """Validate a department placeholder."""
