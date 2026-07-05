"""Skill models for AI Content Factory."""

from __future__ import annotations

from enum import StrEnum
from typing import Any
from uuid import UUID, uuid4

from pydantic import BaseModel, ConfigDict, Field


SkillId = UUID


class SkillStatus(StrEnum):
    """Lifecycle states for skills."""

    DRAFT = "draft"
    ACTIVE = "active"
    INACTIVE = "inactive"
    ARCHIVED = "archived"


class SkillLevel(StrEnum):
    """Competency levels for skills."""

    BASIC = "basic"
    INTERMEDIATE = "intermediate"
    ADVANCED = "advanced"
    EXPERT = "expert"


class SkillCategory(StrEnum):
    """High-level skill categories."""

    ANALYSIS = "analysis"
    COORDINATION = "coordination"
    COMMUNICATION = "communication"
    STRATEGY = "strategy"
    RESEARCH = "research"
    SYSTEM = "system"


class SkillCapability(StrEnum):
    """Capabilities associated with skills."""

    OBSERVE = "observe"
    ANALYZE = "analyze"
    ROUTE = "route"
    PLAN = "plan"
    REVIEW = "review"
    SYNTHESIZE = "synthesize"


class SkillProfile(BaseModel):
    """Profile placeholder for skills."""

    model_config = ConfigDict(extra="ignore", populate_by_name=True)

    name: str | None = None
    description: str | None = None
    tags: list[str] = Field(default_factory=list)


class SkillMetadata(BaseModel):
    """Metadata placeholder for skills."""

    model_config = ConfigDict(extra="ignore", populate_by_name=True)

    name: str | None = None
    description: str | None = None
    attributes: dict[str, Any] = Field(default_factory=dict)


class SkillContext(BaseModel):
    """Context placeholder for skill contracts."""

    model_config = ConfigDict(extra="ignore", populate_by_name=True)

    project_name: str | None = None
    workspace_name: str | None = None
    metadata: SkillMetadata | None = None


class Skill(BaseModel):
    """Skill placeholder."""

    model_config = ConfigDict(extra="ignore", populate_by_name=True)

    id: SkillId = Field(default_factory=uuid4)
    profile: SkillProfile = Field(default_factory=SkillProfile)
    category: SkillCategory = SkillCategory.SYSTEM
    level: SkillLevel = SkillLevel.BASIC
    status: SkillStatus = SkillStatus.DRAFT
    capabilities: list[SkillCapability] = Field(default_factory=list)
    context: SkillContext | None = None
    metadata: SkillMetadata = Field(default_factory=SkillMetadata)