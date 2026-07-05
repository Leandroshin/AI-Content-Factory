"""Organization contract package for AI Content Factory."""

from __future__ import annotations

from .contracts import (
    BaseOrganizationRegistry,
    BaseOrganizationValidator,
    OrganizationRegistryContract,
    OrganizationValidatorContract,
)
from .exceptions import (
    OrganizationError,
    OrganizationNotFoundError,
    OrganizationRegistryError,
    OrganizationValidationError,
)
from .models import (
    BusinessUnit,
    Hierarchy,
    Organization,
    OrganizationCompany,
    OrganizationId,
    OrganizationContext,
    OrganizationMetadata,
    OrganizationResult,
    OrganizationStatus,
    ReportingStructure,
    Division,
)

__all__ = [
    "BaseOrganizationRegistry",
    "BaseOrganizationValidator",
    "BusinessUnit",
    "Division",
    "Hierarchy",
    "Organization",
    "OrganizationCompany",
    "OrganizationId",
    "OrganizationContext",
    "OrganizationError",
    "OrganizationMetadata",
    "OrganizationNotFoundError",
    "OrganizationRegistryContract",
    "OrganizationRegistryError",
    "OrganizationResult",
    "OrganizationStatus",
    "OrganizationValidationError",
    "OrganizationValidatorContract",
    "ReportingStructure",
]