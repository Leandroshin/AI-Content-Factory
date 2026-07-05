"""Secret data models.

Secrets are always masked in repr/str to prevent accidental
exposure in logs or error messages.
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True, slots=True)
class SecretKey:
    """Identifier for a single secret/credential.

    The key maps to a specific credential slot (e.g. 'api_key',
    'personal_access_token') for a given tool or provider.
    """
    key: str
    provider: str = ""
    tool_id: str = ""


@dataclass(frozen=True, slots=True)
class SecretValue:
    """A secret value that masks itself in repr/str output.

    The raw value is accessible via the 'value' attribute but
    is never printed or logged. Only 'masked' is shown.
    """
    key: SecretKey
    value: str
    masked: str = field(default="****")

    def __repr__(self) -> str:
        return f"SecretValue(key={self.key.key!r}, masked={self.masked!r})"

    def __str__(self) -> str:
        return self.masked
