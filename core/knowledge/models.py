"""Knowledge models for AI Content Factory."""

from __future__ import annotations

from enum import StrEnum
from typing import Any
from uuid import UUID, uuid4

from pydantic import BaseModel, ConfigDict, Field


class KnowledgeStatus(StrEnum):
    """Lifecycle states for knowledge entries."""

    DRAFT = "draft"
    ACTIVE = "active"
    ARCHIVED = "archived"
    DEPRECATED = "deprecated"


class KnowledgeCategory(StrEnum):
    """High-level knowledge categories."""

    PROJECT = "project"
    ENGINE = "engine"
    PROMPT = "prompt"
    EVENT = "event"
    SYSTEM = "system"


class KnowledgeSource(BaseModel):
    """Source placeholder for knowledge entries."""

    model_config = ConfigDict(extra="ignore", populate_by_name=True)

    name: str
    origin: str | None = None
    uri: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class KnowledgeMetadata(BaseModel):
    """Metadata placeholder for knowledge entries."""

    model_config = ConfigDict(extra="ignore", populate_by_name=True)

    title: str | None = None
    description: str | None = None
    tags: list[str] = Field(default_factory=list)
    extra: dict[str, Any] = Field(default_factory=dict)


class KnowledgeContext(BaseModel):
    """Context placeholder for knowledge operations."""

    model_config = ConfigDict(extra="ignore", populate_by_name=True)

    project_name: str | None = None
    engine_name: str | None = None
    metadata: KnowledgeMetadata | None = None


class KnowledgeResult(BaseModel):
    """Result placeholder for knowledge operations."""

    model_config = ConfigDict(extra="ignore", populate_by_name=True)

    success: bool = False
    status: KnowledgeStatus = KnowledgeStatus.DRAFT
    message: str | None = None
    data: dict[str, Any] = Field(default_factory=dict)
    errors: list[str] = Field(default_factory=list)


class KnowledgeEntry(BaseModel):
    """Knowledge entry placeholder."""

    model_config = ConfigDict(extra="ignore", populate_by_name=True)

    id: UUID = Field(default_factory=uuid4)
    key: str
    category: KnowledgeCategory = KnowledgeCategory.SYSTEM
    status: KnowledgeStatus = KnowledgeStatus.DRAFT
    source: KnowledgeSource | None = None
    context: KnowledgeContext | None = None
    metadata: KnowledgeMetadata = Field(default_factory=KnowledgeMetadata)
    content: dict[str, Any] = Field(default_factory=dict)
