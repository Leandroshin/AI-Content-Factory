"""Employee models for AI Content Factory."""

from __future__ import annotations

from enum import StrEnum
from typing import Any
from uuid import UUID, uuid4

from pydantic import BaseModel, ConfigDict, Field


EmployeeId = UUID


class EmployeeStatus(StrEnum):
    """Lifecycle states for employees."""

    DRAFT = "draft"
    ACTIVE = "active"
    INACTIVE = "inactive"
    SUSPENDED = "suspended"
    ARCHIVED = "archived"


class EmployeeRole(StrEnum):
    """High-level employee roles."""

    GENERIC = "generic"
    ANALYST = "analyst"
    OPERATOR = "operator"
    STRATEGIST = "strategist"
    SYSTEM = "system"


class EmployeeCapability(StrEnum):
    """Capabilities associated with employees."""

    COORDINATE = "coordinate"
    ANALYZE = "analyze"
    REVIEW = "review"
    ROUTE = "route"


class EmployeeIdentity(BaseModel):
    """Identity placeholder for employees."""

    model_config = ConfigDict(extra="ignore", populate_by_name=True)

    employee_id: EmployeeId = Field(default_factory=uuid4)
    username: str | None = None
    display_name: str | None = None
    email: str | None = None


class EmployeeProfile(BaseModel):
    """Profile placeholder for employees."""

    model_config = ConfigDict(extra="ignore", populate_by_name=True)

    full_name: str | None = None
    title: str | None = None
    department_name: str | None = None
    tags: list[str] = Field(default_factory=list)


class EmployeeAvailability(BaseModel):
    """Availability placeholder for employees."""

    model_config = ConfigDict(extra="ignore", populate_by_name=True)

    is_available: bool = True
    timezone: str | None = None
    schedule: dict[str, Any] = Field(default_factory=dict)


class EmployeeMetadata(BaseModel):
    """Metadata placeholder for employees."""

    model_config = ConfigDict(extra="ignore", populate_by_name=True)

    name: str | None = None
    description: str | None = None
    attributes: dict[str, Any] = Field(default_factory=dict)


class EmployeeContext(BaseModel):
    """Context placeholder for employee contracts."""

    model_config = ConfigDict(extra="ignore", populate_by_name=True)

    project_name: str | None = None
    workspace_name: str | None = None
    metadata: EmployeeMetadata | None = None


class EmployeeResult(BaseModel):
    """Result placeholder for employee contracts."""

    model_config = ConfigDict(extra="ignore", populate_by_name=True)

    success: bool = False
    message: str | None = None
    data: dict[str, Any] = Field(default_factory=dict)
    errors: list[str] = Field(default_factory=list)


class Employee(BaseModel):
    """Employee placeholder."""

    model_config = ConfigDict(extra="ignore", populate_by_name=True)

    identity: EmployeeIdentity = Field(default_factory=EmployeeIdentity)
    profile: EmployeeProfile = Field(default_factory=EmployeeProfile)
    availability: EmployeeAvailability = Field(default_factory=EmployeeAvailability)
    role: EmployeeRole = EmployeeRole.GENERIC
    status: EmployeeStatus = EmployeeStatus.DRAFT
    capabilities: list[EmployeeCapability] = Field(default_factory=list)
    context: EmployeeContext | None = None
    metadata: EmployeeMetadata = Field(default_factory=EmployeeMetadata)