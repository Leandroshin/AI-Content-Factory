"""Data models for the Tool Runtime."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any
from uuid import UUID


class ToolStatus(StrEnum):
    """Lifecycle states for a registered tool."""

    UNCONFIGURED = "unconfigured"
    CONFIGURING = "configuring"
    READY = "ready"
    BUSY = "busy"
    ERROR = "error"
    DISABLED = "disabled"


@dataclass(frozen=True, slots=True)
class ToolDefinition:
    """Immutable definition of a single external tool.

    Each tool has metadata about what it needs to function:
    configuration keys, credential keys, and permission keys.
    Actual values are never stored here — only the presence
    flags (has_credentials, has_permissions) are tracked.
    """

    tool_id: UUID
    name: str
    category: str
    description: str
    status: ToolStatus = ToolStatus.UNCONFIGURED
    required_config_keys: tuple[str, ...] = field(default_factory=tuple)
    required_credential_keys: tuple[str, ...] = field(default_factory=tuple)
    required_permission_keys: tuple[str, ...] = field(default_factory=tuple)
    current_config: dict[str, Any] = field(default_factory=dict)
    has_credentials: bool = False
    has_permissions: bool = False
    last_validated: float = 0.0
    error_message: str = ""
    usage_count: int = 0
    last_error: str = ""

    def with_status(self, status: ToolStatus) -> ToolDefinition:
        return ToolDefinition(
            tool_id=self.tool_id, name=self.name,
            category=self.category, description=self.description,
            status=status,
            required_config_keys=self.required_config_keys,
            required_credential_keys=self.required_credential_keys,
            required_permission_keys=self.required_permission_keys,
            current_config=dict(self.current_config),
            has_credentials=self.has_credentials,
            has_permissions=self.has_permissions,
            last_validated=self.last_validated,
            error_message=self.error_message,
            usage_count=self.usage_count,
            last_error=self.last_error,
        )

    def with_config(self, config: dict[str, Any]) -> ToolDefinition:
        merged = dict(self.current_config)
        merged.update(config)
        return ToolDefinition(
            tool_id=self.tool_id, name=self.name,
            category=self.category, description=self.description,
            status=self.status,
            required_config_keys=self.required_config_keys,
            required_credential_keys=self.required_credential_keys,
            required_permission_keys=self.required_permission_keys,
            current_config=merged,
            has_credentials=self.has_credentials,
            has_permissions=self.has_permissions,
            last_validated=self.last_validated,
            error_message=self.error_message,
            usage_count=self.usage_count,
            last_error=self.last_error,
        )

    def with_credentials(self, has: bool) -> ToolDefinition:
        return ToolDefinition(
            tool_id=self.tool_id, name=self.name,
            category=self.category, description=self.description,
            status=self.status,
            required_config_keys=self.required_config_keys,
            required_credential_keys=self.required_credential_keys,
            required_permission_keys=self.required_permission_keys,
            current_config=dict(self.current_config),
            has_credentials=has,
            has_permissions=self.has_permissions,
            last_validated=self.last_validated,
            error_message=self.error_message,
            usage_count=self.usage_count,
            last_error=self.last_error,
        )

    def with_permissions(self, has: bool) -> ToolDefinition:
        return ToolDefinition(
            tool_id=self.tool_id, name=self.name,
            category=self.category, description=self.description,
            status=self.status,
            required_config_keys=self.required_config_keys,
            required_credential_keys=self.required_credential_keys,
            required_permission_keys=self.required_permission_keys,
            current_config=dict(self.current_config),
            has_credentials=self.has_credentials,
            has_permissions=has,
            last_validated=self.last_validated,
            error_message=self.error_message,
            usage_count=self.usage_count,
            last_error=self.last_error,
        )

    def with_error(self, msg: str) -> ToolDefinition:
        return ToolDefinition(
            tool_id=self.tool_id, name=self.name,
            category=self.category, description=self.description,
            status=ToolStatus.ERROR,
            required_config_keys=self.required_config_keys,
            required_credential_keys=self.required_credential_keys,
            required_permission_keys=self.required_permission_keys,
            current_config=dict(self.current_config),
            has_credentials=self.has_credentials,
            has_permissions=self.has_permissions,
            last_validated=self.last_validated,
            error_message=self.error_message,
            usage_count=self.usage_count,
            last_error=msg,
        )
