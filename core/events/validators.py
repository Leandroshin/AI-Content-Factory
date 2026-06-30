"""Domain event validator contracts for AI Content Factory."""

from __future__ import annotations

from abc import ABC, abstractmethod

from .contracts import BaseEventValidator
from .models import BaseEvent


class EventValidator(BaseEventValidator, ABC):
    """Base event validator contract."""

    @abstractmethod
    def validate(self, event: BaseEvent) -> None:
        """Validate a domain event placeholder."""
