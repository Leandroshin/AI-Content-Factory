"""Core departments package for AI Content Factory."""

from .contracts import BaseDepartmentRegistry, BaseDepartmentValidator, DepartmentRegistryContract, DepartmentValidatorContract
from .exceptions import DepartmentError, DepartmentRegistryError, DepartmentValidationError
from .models import Department, DepartmentCapability, DepartmentContext, DepartmentMetadata, DepartmentResult, DepartmentStatus, DepartmentType
from .registry import DepartmentRegistry
from .validators import DepartmentValidator

__all__ = [
    "BaseDepartmentRegistry",
    "BaseDepartmentValidator",
    "Department",
    "DepartmentCapability",
    "DepartmentContext",
    "DepartmentError",
    "DepartmentMetadata",
    "DepartmentRegistry",
    "DepartmentRegistryContract",
    "DepartmentRegistryError",
    "DepartmentResult",
    "DepartmentStatus",
    "DepartmentType",
    "DepartmentValidationError",
    "DepartmentValidator",
    "DepartmentValidatorContract",
]
