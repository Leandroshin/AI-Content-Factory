"""Policy contracts for AI Content Factory."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Protocol

from .models import Policy, PolicyContext, PolicyId, PolicyMetadata, PolicyResult


class PolicyRegistryContract(Protocol):
    """Structural contract for policy registries."""

    def get(self, policy_id: PolicyId) -> Policy | None:
        """Return a policy placeholder by identifier."""

    def list(self) -> list[Policy]:
        """Return policy placeholders."""


class PolicyValidatorContract(Protocol):
    """Structural contract for policy validators."""

    def validate(self, policy: Policy) -> None:
        """Validate a policy placeholder."""

    def validate_context(self, context: PolicyContext) -> None:
        """Validate a policy context placeholder."""

    def validate_metadata(self, metadata: PolicyMetadata) -> None:
        """Validate a policy metadata placeholder."""


class BasePolicyRegistry(ABC):
    """Base contract for policy registries."""

    @abstractmethod
    def get(self, policy_id: PolicyId) -> Policy | None:
        """Return a policy placeholder by identifier."""

    @abstractmethod
    def list(self) -> list[Policy]:
        """Return policy placeholders."""

    @abstractmethod
    def register(self, policy: Policy) -> None:
        """Register a policy placeholder."""

    @abstractmethod
    def unregister(self, policy_id: PolicyId) -> None:
        """Remove a policy placeholder from the registry."""


class BasePolicyValidator(ABC):
    """Base contract for policy validators."""

    @abstractmethod
    def validate(self, policy: Policy) -> None:
        """Validate a policy placeholder."""

    @abstractmethod
    def validate_context(self, context: PolicyContext) -> None:
        """Validate a policy context placeholder."""

    @abstractmethod
    def validate_metadata(self, metadata: PolicyMetadata) -> None:
        """Validate a policy metadata placeholder."""