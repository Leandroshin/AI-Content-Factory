"""Organization contracts for AI Content Factory."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Protocol

from .models import (
    BusinessUnit,
    Division,
    Organization,
    OrganizationContext,
    OrganizationId,
    OrganizationMetadata,
)


class OrganizationRegistryContract(Protocol):
    """Structural contract for organization registries."""

    def get(self, organization_id: OrganizationId) -> Organization | None:
        """Return an organization placeholder by identifier."""

    def list(self) -> list[Organization]:
        """Return organization placeholders."""


class OrganizationValidatorContract(Protocol):
    """Structural contract for organization validators."""

    def validate(self, organization: Organization) -> None:
        """Validate an organization placeholder."""

    def validate_context(self, context: OrganizationContext) -> None:
        """Validate an organization context placeholder."""

    def validate_metadata(self, metadata: OrganizationMetadata) -> None:
        """Validate an organization metadata placeholder."""


class BaseOrganizationRegistry(ABC):
    """Base contract for organization registries."""

    @abstractmethod
    def get(self, organization_id: OrganizationId) -> Organization | None:
        """Return an organization placeholder by identifier."""

    @abstractmethod
    def list(self) -> list[Organization]:
        """Return organization placeholders."""

    @abstractmethod
    def register(self, organization: Organization) -> None:
        """Register an organization placeholder."""

    @abstractmethod
    def unregister(self, organization_id: OrganizationId) -> None:
        """Remove an organization placeholder from the registry."""


class BaseOrganizationValidator(ABC):
    """Base contract for organization validators."""

    @abstractmethod
    def validate(self, organization: Organization) -> None:
        """Validate an organization placeholder."""

    @abstractmethod
    def validate_context(self, context: OrganizationContext) -> None:
        """Validate an organization context placeholder."""

    @abstractmethod
    def validate_metadata(self, metadata: OrganizationMetadata) -> None:
        """Validate an organization metadata placeholder."""