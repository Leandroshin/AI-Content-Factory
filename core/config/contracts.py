"""Configuration contracts for AI Content Factory."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Protocol

from .models import AppConfig, ConfigModel


class ConfigLoaderContract(Protocol):
    """Structural contract for configuration loaders."""

    def load(self) -> AppConfig:
        """Return an application configuration placeholder."""


class ConfigRegistryContract(Protocol):
    """Structural contract for configuration registries."""

    def get(self, name: str) -> ConfigModel | None:
        """Return a configuration placeholder by name."""

    def list(self) -> list[ConfigModel]:
        """Return configuration placeholders."""


class ConfigValidatorContract(Protocol):
    """Structural contract for configuration validators."""

    def validate(self, config: AppConfig) -> None:
        """Validate an application configuration placeholder."""


class BaseConfigLoader(ABC):
    """Base contract for configuration loaders."""

    @abstractmethod
    def load(self) -> AppConfig:
        """Return an application configuration placeholder."""