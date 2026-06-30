"""Department models for AI Content Factory."""

from __future__ import annotations

from enum import StrEnum
from typing import Any
from uuid import UUID, uuid4

from pydantic import BaseModel, ConfigDict, Field


class DepartmentStatus(StrEnum):
    """Lifecycle states for departments."""

    DRAFT = "draft"
    ACTIVE = "active"
    INACTIVE = "inactive"
    ARCHIVED = "archived"


class DepartmentType(StrEnum):
    """High-level department categories."""

    CONTENT = "content"
    OPERATIONS = "operations"
    RESEARCH = "research"
    STRATEGY = "strategy"
    SYSTEM = "system"


class DepartmentCapability(StrEnum):
    """Capabilities associated with departments."""

    COORDINATE = "coordinate"
    VALIDATE = "validate"
    ANALYZE = "analyze"
    ROUTE = "route"


class DepartmentMetadata(BaseModel):
    """Metadata placeholder for departments."""

    model_config = ConfigDict(extra="ignore", populate_by_name=True)

    name: str | None = None
    description: str | None = None
    tags: list[str] = Field(default_factory=list)
    extra: dict[str, Any] = Field(default_factory=dict)


class DepartmentContext(BaseModel):
    """Context placeholder for department operations."""

    model_config = ConfigDict(extra="ignore", populate_by_name=True)

    project_name: str | None = None
    department_name: str | None = None
    metadata: DepartmentMetadata | None = None


class DepartmentResult(BaseModel):
    """Result placeholder for department contracts."""

    model_config = ConfigDict(extra="ignore", populate_by_name=True)

    success: bool = False
    status: DepartmentStatus = DepartmentStatus.DRAFT
    message: str | None = None
    data: dict[str, Any] = Field(default_factory=dict)
    errors: list[str] = Field(default_factory=list)


class Department(BaseModel):
    """Department placeholder."""

    model_config = ConfigDict(extra="ignore", populate_by_name=True)

    id: UUID = Field(default_factory=uuid4)
    name: str
    type: DepartmentType = DepartmentType.SYSTEM
    status: DepartmentStatus = DepartmentStatus.DRAFT
    capabilities: list[DepartmentCapability] = Field(default_factory=list)
    context: DepartmentContext | None = None
    metadata: DepartmentMetadata = Field(default_factory=DepartmentMetadata)
