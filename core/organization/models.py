"""Organization models for AI Content Factory."""

from __future__ import annotations

from enum import StrEnum
from typing import Any
from uuid import UUID, uuid4

from pydantic import BaseModel, ConfigDict, Field


OrganizationId = UUID


class OrganizationStatus(StrEnum):
    """Lifecycle states for organizations."""

    DRAFT = "draft"
    ACTIVE = "active"
    INACTIVE = "inactive"
    ARCHIVED = "archived"


class OrganizationCompany(StrEnum):
    """High-level company classifications."""

    PRODUCT = "product"
    HOLDING = "holding"
    PLATFORM = "platform"
    SERVICE = "service"


class BusinessUnit(BaseModel):
    """Business unit placeholder."""

    model_config = ConfigDict(extra="ignore", populate_by_name=True)

    id: UUID = Field(default_factory=uuid4)
    name: str
    description: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class Division(BaseModel):
    """Division placeholder."""

    model_config = ConfigDict(extra="ignore", populate_by_name=True)

    id: UUID = Field(default_factory=uuid4)
    name: str
    business_unit_name: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class Hierarchy(BaseModel):
    """Hierarchy placeholder."""

    model_config = ConfigDict(extra="ignore", populate_by_name=True)

    level: str | None = None
    path: list[str] = Field(default_factory=list)


class ReportingStructure(BaseModel):
    """Reporting structure placeholder."""

    model_config = ConfigDict(extra="ignore", populate_by_name=True)

    manager: str | None = None
    reports_to: str | None = None
    hierarchy: Hierarchy | None = None


class OrganizationMetadata(BaseModel):
    """Metadata placeholder for organizations."""

    model_config = ConfigDict(extra="ignore", populate_by_name=True)

    name: str | None = None
    description: str | None = None
    attributes: dict[str, Any] = Field(default_factory=dict)


class OrganizationContext(BaseModel):
    """Context placeholder for organization contracts."""

    model_config = ConfigDict(extra="ignore", populate_by_name=True)

    company_name: str | None = None
    workspace_name: str | None = None
    metadata: OrganizationMetadata | None = None


class OrganizationResult(BaseModel):
    """Result placeholder for organization contracts."""

    model_config = ConfigDict(extra="ignore", populate_by_name=True)

    success: bool = False
    message: str | None = None
    data: dict[str, Any] = Field(default_factory=dict)
    errors: list[str] = Field(default_factory=list)


class Organization(BaseModel):
    """Organization placeholder."""

    model_config = ConfigDict(extra="ignore", populate_by_name=True)

    id: OrganizationId = Field(default_factory=uuid4)
    name: str
    company: OrganizationCompany = OrganizationCompany.PRODUCT
    status: OrganizationStatus = OrganizationStatus.DRAFT
    business_units: list[BusinessUnit] = Field(default_factory=list)
    divisions: list[Division] = Field(default_factory=list)
    hierarchy: Hierarchy | None = None
    reporting_structure: ReportingStructure | None = None
    context: OrganizationContext | None = None
    metadata: OrganizationMetadata = Field(default_factory=OrganizationMetadata)