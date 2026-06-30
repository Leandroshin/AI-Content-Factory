"""Configuration models for AI Content Factory."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class ConfigModel(BaseModel):
    """Shared base model for configuration structures."""

    model_config = ConfigDict(extra="ignore", populate_by_name=True)


class EnvironmentConfig(ConfigModel):
    """Application environment settings."""

    name: str = Field(default="development")
    log_level: str = Field(default="INFO")
    output_dir: Path = Field(default=Path("output"))
    temp_dir: Path = Field(default=Path("temp"))


class ProjectConfig(ConfigModel):
    """Project-specific settings."""

    name: str
    topic: str | None = None
    niche: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class AppConfig(ConfigModel):
    """Top-level application configuration."""

    environment: EnvironmentConfig = Field(default_factory=EnvironmentConfig)
    project: ProjectConfig | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)