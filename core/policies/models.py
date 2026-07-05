"""Policy models for AI Content Factory."""

from __future__ import annotations

from enum import StrEnum
from typing import Any
from uuid import UUID, uuid4

from pydantic import BaseModel, ConfigDict, Field


PolicyId = UUID


class PolicyStatus(StrEnum):
    """Lifecycle states for policies."""

    DRAFT = "draft"
    ACTIVE = "active"
    INACTIVE = "inactive"
    ARCHIVED = "archived"


class PolicyType(StrEnum):
    """High-level policy categories."""

    ORGANIZATIONAL = "organizational"
    OPERATIONAL = "operational"
    SAFETY = "safety"
    GOVERNANCE = "governance"
    COMPLIANCE = "compliance"


class PolicyScope(StrEnum):
    """Scope levels for policies."""

    GLOBAL = "global"
    COMPANY = "company"
    DIVISION = "division"
    BUSINESS_UNIT = "business_unit"
    ORGANIZATION = "organization"


class PolicyCondition(BaseModel):
    """Condition placeholder for policies."""

    model_config = ConfigDict(extra="ignore", populate_by_name=True)

    name: str | None = None
    expression: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class PolicyConstraint(BaseModel):
    """Constraint placeholder for policies."""

    model_config = ConfigDict(extra="ignore", populate_by_name=True)

    name: str | None = None
    description: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class PolicyMetadata(BaseModel):
    """Metadata placeholder for policies."""

    model_config = ConfigDict(extra="ignore", populate_by_name=True)

    name: str | None = None
    description: str | None = None
    attributes: dict[str, Any] = Field(default_factory=dict)


class PolicyContext(BaseModel):
    """Context placeholder for policy contracts."""

    model_config = ConfigDict(extra="ignore", populate_by_name=True)

    organization_name: str | None = None
    company_name: str | None = None
    metadata: PolicyMetadata | None = None


class PolicyResult(BaseModel):
    """Result placeholder for policy contracts."""

    model_config = ConfigDict(extra="ignore", populate_by_name=True)

    success: bool = False
    message: str | None = None
    data: dict[str, Any] = Field(default_factory=dict)
    errors: list[str] = Field(default_factory=list)


class Policy(BaseModel):
    """Policy placeholder."""

    model_config = ConfigDict(extra="ignore", populate_by_name=True)

    id: PolicyId = Field(default_factory=uuid4)
    name: str
    type: PolicyType = PolicyType.ORGANIZATIONAL
    scope: PolicyScope = PolicyScope.COMPANY
    status: PolicyStatus = PolicyStatus.DRAFT
    conditions: list[PolicyCondition] = Field(default_factory=list)
    constraints: list[PolicyConstraint] = Field(default_factory=list)
    context: PolicyContext | None = None
    metadata: PolicyMetadata = Field(default_factory=PolicyMetadata)