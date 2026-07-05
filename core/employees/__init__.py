"""Employee contract package for AI Content Factory."""

from __future__ import annotations

from .contracts import (
    BaseEmployeeRegistry,
    BaseEmployeeValidator,
    EmployeeFactoryContract,
    EmployeeRegistryContract,
    EmployeeValidatorContract,
)
from .exceptions import (
    EmployeeError,
    EmployeeIdentityError,
    EmployeeNotFoundError,
    EmployeeRegistryError,
    EmployeeValidationError,
)
from .models import (
    Employee,
    EmployeeAvailability,
    EmployeeCapability,
    EmployeeContext,
    EmployeeIdentity,
    EmployeeMetadata,
    EmployeeProfile,
    EmployeeRole,
    EmployeeResult,
    EmployeeStatus,
)
from .cognition import (
    Thought,
    ThoughtContext,
    ThoughtPlan,
    ThoughtResult,
    ThoughtRuntime,
    ThoughtStep,
    ThoughtTrace,
)
from .observability import EmployeeObservabilityProjector, EmployeeObservabilityRecord
from .runtime import EmployeeRuntime, EmployeeRuntimeSnapshot, EmployeeRuntimeState, EmployeeStateChangedEvent

__all__ = [
    "BaseEmployeeRegistry",
    "BaseEmployeeValidator",
    "Thought",
    "ThoughtContext",
    "ThoughtPlan",
    "ThoughtResult",
    "ThoughtRuntime",
    "ThoughtStep",
    "ThoughtTrace",
    "Employee",
    "EmployeeAvailability",
    "EmployeeCapability",
    "EmployeeContext",
    "EmployeeError",
    "EmployeeFactoryContract",
    "EmployeeIdentity",
    "EmployeeIdentityError",
    "EmployeeMetadata",
    "EmployeeNotFoundError",
    "EmployeeProfile",
    "EmployeeRegistryContract",
    "EmployeeRegistryError",
    "EmployeeResult",
    "EmployeeRole",
    "EmployeeRuntime",
    "EmployeeRuntimeSnapshot",
    "EmployeeRuntimeState",
    "EmployeeStateChangedEvent",
    "EmployeeObservabilityProjector",
    "EmployeeObservabilityRecord",
    "EmployeeStatus",
    "EmployeeValidationError",
    "EmployeeValidatorContract",
]