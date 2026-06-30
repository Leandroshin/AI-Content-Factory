"""Configuration validator contracts for AI Content Factory."""

from __future__ import annotations

from abc import ABC, abstractmethod

from .contracts import ConfigValidatorContract
from .models import AppConfig


class ConfigValidator(ConfigValidatorContract, ABC):
    """Base configuration validator contract."""

    @abstractmethod
    def validate(self, config: AppConfig) -> None:
        """Validate an application configuration placeholder."""