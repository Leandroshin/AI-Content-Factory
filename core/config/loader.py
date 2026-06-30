"""Configuration loader contracts for AI Content Factory."""

from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path

from .contracts import BaseConfigLoader
from .models import AppConfig


class ConfigLoader(BaseConfigLoader, ABC):
    """Base configuration loader contract."""

    def __init__(self, base_path: Path | None = None) -> None:
        self.base_path = base_path or Path.cwd()

    @abstractmethod
    def load(self) -> AppConfig:
        """Return an application configuration placeholder."""