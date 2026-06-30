"""Configuration registry contracts for AI Content Factory."""

from __future__ import annotations

from abc import ABC, abstractmethod

from .contracts import ConfigRegistryContract
from .models import ConfigModel


class ConfigRegistry(ConfigRegistryContract, ABC):
    """Base configuration registry contract."""

    @abstractmethod
    def get(self, name: str) -> ConfigModel | None:
        """Return a configuration placeholder by name."""

    @abstractmethod
    def list(self) -> list[ConfigModel]:
        """Return configuration placeholders."""