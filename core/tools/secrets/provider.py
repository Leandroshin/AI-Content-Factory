"""Secret provider abstraction.

SecretProvider defines the contract for storing and retrieving
credentials. MockSecretProvider is an in-memory implementation
for testing — no real secrets are persisted anywhere.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from core.tools.secrets.models import SecretKey, SecretValue


def _default_mask(value: str) -> str:
    """Return a safe masked representation of a value."""
    if len(value) <= 4:
        return "****"
    return f"{value[:2]}...{value[-2:]}"


def _is_empty(value: Any) -> bool:
    return value is None or (isinstance(value, str) and not value.strip())


class SecretProvider(ABC):
    """Abstract secret store.

    Implementations should never log, print, or expose
    secret values in any way.
    """

    @abstractmethod
    def get(self, key: SecretKey) -> SecretValue | None:
        """Retrieve a secret by its key. Returns None if not found."""
        ...

    @abstractmethod
    def set(self, key: SecretKey, value: str) -> None:
        """Store a secret value."""
        ...

    @abstractmethod
    def validate(self, key: SecretKey) -> bool:
        """Check whether a secret exists and is non-empty."""
        ...

    @abstractmethod
    def delete(self, key: SecretKey) -> None:
        """Remove a stored secret."""
        ...

    @abstractmethod
    def list_keys(self) -> list[SecretKey]:
        """Return all stored secret keys."""
        ...

    @staticmethod
    def mask(value: str) -> str:
        """Return a masked version of the value for safe logging."""
        return _default_mask(value)


class MockSecretProvider(SecretProvider):
    """In-memory secret provider for testing.

    No encryption, no persistence — purely for development
    and demo purposes. Never use in production.
    """

    def __init__(self) -> None:
        self._store: dict[str, str] = {}

    def get(self, key: SecretKey) -> SecretValue | None:
        raw = self._store.get(key.key)
        if raw is None:
            return None
        return SecretValue(
            key=key,
            value=raw,
            masked=self.mask(raw),
        )

    def set(self, key: SecretKey, value: str) -> None:
        if _is_empty(value):
            return
        self._store[key.key] = value

    def validate(self, key: SecretKey) -> bool:
        raw = self._store.get(key.key)
        return raw is not None and not _is_empty(raw)

    def delete(self, key: SecretKey) -> None:
        self._store.pop(key.key, None)

    def list_keys(self) -> list[SecretKey]:
        k = sorted(self._store.keys())
        return [SecretKey(key=name) for name in k]
