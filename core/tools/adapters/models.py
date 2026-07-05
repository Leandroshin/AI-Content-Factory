"""Data models for tool adapter requests, responses, lifecycle, and configuration."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any
from uuid import UUID


class ExecutionMode(StrEnum):
    """Execution mode for tool adapters.

    MOCK — return deterministic fake data (default, safe for dev)
    REAL — make actual HTTP/SDK calls to external services
    """
    MOCK = "mock"
    REAL = "real"


class AdapterStatus(StrEnum):
    """Lifecycle states for a tool adapter's configuration readiness.

    UNCONFIGURED  — created but no configuration or credentials provided
    CONFIGURED    — configuration validated successfully
    AUTHENTICATED — credentials provided and validated
    READY         — fully configured, authenticated, and ready to execute
    ERROR         — configuration or credential validation failed
    """
    UNCONFIGURED = "unconfigured"
    CONFIGURED = "configured"
    AUTHENTICATED = "authenticated"
    READY = "ready"
    ERROR = "error"


@dataclass(frozen=True, slots=True)
class CredentialRequirement:
    """Describes a single credential that an adapter requires.

    Each requirement defines what key is needed, a human-readable
    label, and a description of how to obtain the credential.
    """
    key: str
    label: str
    description: str
    required: bool = True


@dataclass(frozen=True, slots=True)
class OwnerGuidance:
    """Step-by-step instructions for the Owner to configure an adapter.

    Each adapter provides concrete guidance so the system can
    tell the user exactly what to do during onboarding.
    """
    steps: tuple[str, ...]
    docs_url: str = ""
    notes: str = ""


@dataclass(frozen=True, slots=True)
class AdapterConfigStatus:
    """Status report for an adapter's configuration readiness."""
    status: AdapterStatus
    missing_config: tuple[str, ...] = field(default_factory=tuple)
    missing_credentials: tuple[str, ...] = field(default_factory=tuple)
    error_message: str = ""


@dataclass(frozen=True, slots=True)
class ToolRequest:
    """Typed request sent to a tool adapter for execution."""
    tool_id: UUID
    capability: str
    params: dict[str, Any] = field(default_factory=dict)
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class ToolResponse:
    """Raw response from a tool adapter before conversion."""
    success: bool
    data: dict[str, Any] = field(default_factory=dict)
    error: str = ""
    duration_ms: float = 0.0


@dataclass(frozen=True, slots=True)
class AdapterExecutionResult:
    """Normalised result produced after executing a tool adapter."""
    success: bool
    summary: str
    output: dict[str, Any] = field(default_factory=dict)
    error: str = ""
