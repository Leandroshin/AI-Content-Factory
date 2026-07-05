"""Tool Runtime — manages lifecycle, availability, and access to tools.

Flow:
  Employee -> ToolRuntime.request_tool() -> checks availability
     |                                        |
  if READY <---- validate_tool()          if not ready
     |                                        |
  execute_tool()                    ToolUnavailable event
     |                                        |
  release_tool()               Owner configures/provides creds
                                         |
                                   validate_tool() -> READY
                                         |
                                   Employee resumes via provide_tool()

Tool Adapters:
  register_adapter(tool_id, adapter)  — plug an adapter into a tool
  execute_tool(tool_id, request)      — delegate execution to the adapter
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Any
from uuid import UUID

from core.events.bus import EventBus
from core.tools.adapters.base import AbstractToolAdapter
from core.tools.adapters.models import AdapterExecutionResult, ToolRequest
from core.tools.models import ToolDefinition, ToolStatus


# ------------------------------------------------------------------
# Events — published on the shared EventBus
# ------------------------------------------------------------------

@dataclass(frozen=True, slots=True)
class ToolRegistered:
    tool_id: UUID
    name: str
    category: str
    description: str = ""
    timestamp: float = 0.0
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class ToolRequested:
    tool_id: UUID
    employee_id: UUID
    tool_name: str
    task_id: UUID | None = None
    timestamp: float = 0.0
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class ToolUnavailable:
    tool_id: UUID
    employee_id: UUID
    tool_name: str
    reason: str
    missing_items: tuple[str, ...] = field(default_factory=tuple)
    owner_instructions: str = ""
    timestamp: float = 0.0
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class ToolConfigured:
    tool_id: UUID
    name: str
    config_keys: tuple[str, ...] = field(default_factory=tuple)
    timestamp: float = 0.0
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class ToolValidated:
    tool_id: UUID
    name: str
    success: bool
    timestamp: float = 0.0
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class ToolReady:
    tool_id: UUID
    name: str
    timestamp: float = 0.0
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class ToolError:
    tool_id: UUID
    name: str
    error_message: str
    timestamp: float = 0.0
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class ToolReleased:
    tool_id: UUID
    employee_id: UUID
    name: str
    timestamp: float = 0.0
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class ToolExecuted:
    """Published when a tool adapter completes execution."""
    tool_id: UUID
    name: str
    capability: str
    success: bool
    summary: str
    duration_ms: float = 0.0
    timestamp: float = 0.0
    metadata: dict[str, Any] = field(default_factory=dict)


# ------------------------------------------------------------------
# ToolRuntime
# ------------------------------------------------------------------

_NOT_CONFIGURED = "tool not configured"
_MISSING_CREDENTIALS = "credentials missing"
_MISSING_PERMISSIONS = "permissions missing"
_TOOL_ERROR = "tool error"
_TOOL_DISABLED = "tool disabled"


class ToolRuntime:
    """Central registry and lifecycle manager for external tools.

    Employees request tools via this runtime, which checks
    availability and returns whether the tool is READY or what
    is missing (config, credentials, permissions).
    """

    def __init__(self, event_bus: EventBus | None = None) -> None:
        self._event_bus = event_bus
        self._tools: dict[UUID, ToolDefinition] = {}
        self._current_user: dict[UUID, UUID | None] = {}
        self._adapters: dict[UUID, AbstractToolAdapter] = {}
        self._credential_store: dict[UUID, dict[str, str]] = {}

    # --------------------------------------------------------------
    # Registration
    # --------------------------------------------------------------

    def register_tool(self, definition: ToolDefinition) -> ToolRegistered:
        """Register a new tool in the runtime."""
        self._tools[definition.tool_id] = definition
        self._current_user[definition.tool_id] = None
        event = ToolRegistered(
            tool_id=definition.tool_id,
            name=definition.name,
            category=definition.category,
            description=definition.description,
            timestamp=time.time(),
        )
        self._publish(event)
        return event

    def list_tools(self) -> list[ToolDefinition]:
        """Return all registered tools."""
        return list(self._tools.values())

    def tool_state(self, tool_id: UUID) -> ToolDefinition | None:
        """Return a tool definition by ID."""
        return self._tools.get(tool_id)

    def find_by_name(self, name: str) -> ToolDefinition | None:
        """Find a tool by its display name (case-insensitive)."""
        name_lower = name.lower()
        for t in self._tools.values():
            if t.name.lower() == name_lower:
                return t
        return None

    # --------------------------------------------------------------
    # Availability
    # --------------------------------------------------------------

    def check_availability(self, tool_id: UUID) -> dict[str, Any]:
        """Check if a tool is ready for use.

        Returns a dict with:
          - available: bool
          - status: current ToolStatus value
          - missing: tuple of reason strings (empty if ready)
        """
        tool = self._require_tool(tool_id)
        missing: list[str] = []

        if tool.status == ToolStatus.DISABLED:
            return {"available": False, "status": ToolStatus.DISABLED.value,
                    "missing": (_TOOL_DISABLED,)}

        if tool.status == ToolStatus.ERROR:
            missing.append(f"{_TOOL_ERROR}: {tool.error_message}")

        if tool.status in (ToolStatus.UNCONFIGURED, ToolStatus.CONFIGURING):
            missing_config = [k for k in tool.required_config_keys
                              if k not in tool.current_config]
            if missing_config:
                missing.append(f"Missing config keys: {', '.join(missing_config)}")

        if not tool.has_credentials and tool.required_credential_keys:
            missing.append(f"{_MISSING_CREDENTIALS}: {', '.join(tool.required_credential_keys)}")

        if not tool.has_permissions and tool.required_permission_keys:
            missing.append(f"{_MISSING_PERMISSIONS}: {', '.join(tool.required_permission_keys)}")

        return {
            "available": len(missing) == 0,
            "status": tool.status.value,
            "missing": tuple(missing),
        }

    def request_tool(self, tool_id: UUID, employee_id: UUID,
                     task_id: UUID | None = None) -> ToolReady | ToolUnavailable:
        """Employee requests access to a tool.

        Returns ToolReady if the tool is immediately available.
        Returns ToolUnavailable with missing items otherwise.

        The employee should enter AWAITING_TOOL and wait for
        ToolReady event before retrying.
        """
        tool = self._require_tool(tool_id)
        availability = self.check_availability(tool_id)

        self._publish(ToolRequested(
            tool_id=tool_id, employee_id=employee_id,
            tool_name=tool.name, task_id=task_id,
            timestamp=time.time(),
        ))

        if not availability["available"]:
            missing = availability["missing"]
            instructions = (
                f"Configure '{tool.name}': provide required config, "
                f"credentials and permissions, then call validate_tool()."
            )
            event = ToolUnavailable(
                tool_id=tool_id, employee_id=employee_id,
                tool_name=tool.name, reason=availability["status"],
                missing_items=missing,
                owner_instructions=instructions,
                timestamp=time.time(),
            )
            self._publish(event)
            return event

        self._tools[tool_id] = tool.with_status(ToolStatus.BUSY)
        self._current_user[tool_id] = employee_id
        event = ToolReady(
            tool_id=tool_id, name=tool.name,
            timestamp=time.time(),
        )
        self._publish(event)
        return event

    # --------------------------------------------------------------
    # Configuration
    # --------------------------------------------------------------

    def configure_tool(self, tool_id: UUID,
                       config: dict[str, Any]) -> ToolConfigured:
        """Provide configuration values for a tool."""
        tool = self._require_tool(tool_id)
        updated = tool.with_config(config).with_status(ToolStatus.CONFIGURING)
        self._tools[tool_id] = updated
        event = ToolConfigured(
            tool_id=tool_id, name=tool.name,
            config_keys=tuple(config.keys()),
            timestamp=time.time(),
        )
        self._publish(event)
        return event

    def provide_credentials(self, tool_id: UUID) -> ToolConfigured:
        """Mark that all required credentials have been provided."""
        tool = self._require_tool(tool_id)
        updated = tool.with_credentials(True).with_status(ToolStatus.CONFIGURING)
        self._tools[tool_id] = updated
        event = ToolConfigured(
            tool_id=tool_id, name=tool.name,
            timestamp=time.time(),
        )
        self._publish(event)
        return event

    def grant_permissions(self, tool_id: UUID) -> ToolConfigured:
        """Mark that all required permissions have been granted."""
        tool = self._require_tool(tool_id)
        updated = tool.with_permissions(True).with_status(ToolStatus.CONFIGURING)
        self._tools[tool_id] = updated
        event = ToolConfigured(
            tool_id=tool_id, name=tool.name,
            timestamp=time.time(),
        )
        self._publish(event)
        return event

    # --------------------------------------------------------------
    # Validation
    # --------------------------------------------------------------

    def validate_tool(self, tool_id: UUID) -> ToolValidated:
        """Validate tool configuration and mark READY or ERROR."""
        tool = self._require_tool(tool_id)
        availability = self.check_availability(tool_id)
        success = availability["available"]

        if success:
            self._tools[tool_id] = tool.with_status(ToolStatus.READY)
        else:
            msg = "; ".join(availability["missing"]) if availability["missing"] else "validation failed"
            self._tools[tool_id] = tool.with_error(msg)

        event = ToolValidated(
            tool_id=tool_id, name=tool.name,
            success=success,
            timestamp=time.time(),
        )
        self._publish(event)

        if success:
            self._publish(ToolReady(
                tool_id=tool_id, name=tool.name,
                timestamp=time.time(),
            ))

        return event

    # --------------------------------------------------------------
    # Lifecycle
    # --------------------------------------------------------------

    def release_tool(self, tool_id: UUID, employee_id: UUID) -> ToolReleased:
        """Release a tool after use."""
        tool = self._require_tool(tool_id)
        updated = ToolDefinition(
            tool_id=tool.tool_id, name=tool.name,
            category=tool.category, description=tool.description,
            status=ToolStatus.READY,
            required_config_keys=tool.required_config_keys,
            required_credential_keys=tool.required_credential_keys,
            required_permission_keys=tool.required_permission_keys,
            current_config=dict(tool.current_config),
            has_credentials=tool.has_credentials,
            has_permissions=tool.has_permissions,
            last_validated=tool.last_validated,
            error_message="",
            usage_count=tool.usage_count + 1,
            last_error=tool.last_error,
        )
        self._tools[tool_id] = updated
        self._current_user[tool_id] = None
        event = ToolReleased(
            tool_id=tool_id, employee_id=employee_id,
            name=tool.name,
            timestamp=time.time(),
        )
        self._publish(event)
        return event

    # --------------------------------------------------------------
    # Adapter lifecycle
    # --------------------------------------------------------------

    def register_adapter(self, tool_id: UUID, adapter: AbstractToolAdapter) -> None:
        """Associate an adapter with a registered tool.

        The tool must already be registered via register_tool().
        The adapter provides the execution logic; the runtime
        manages lifecycle and access control.
        """
        self._require_tool(tool_id)
        self._adapters[tool_id] = adapter

    def list_adapters(self) -> list[tuple[UUID, str]]:
        """List all registered adapters with their tool IDs."""
        return [(tid, a.tool_name) for tid, a in self._adapters.items()]

    def find_adapter(self, tool_id: UUID) -> AbstractToolAdapter | None:
        """Find the adapter associated with a tool ID."""
        return self._adapters.get(tool_id)

    def execute_tool(
        self,
        tool_id: UUID,
        request: ToolRequest,
    ) -> AdapterExecutionResult:
        """Execute a tool via its registered adapter.

        The tool must be in BUSY state (requested by an employee).
        Returns an AdapterExecutionResult with the outcome.
        """
        tool = self._require_tool(tool_id)
        if tool.status != ToolStatus.BUSY:
            return AdapterExecutionResult(
                success=False,
                summary="",
                error=f"Tool '{tool.name}' is not BUSY (status={tool.status.value})",
            )

        adapter = self._adapters.get(tool_id)
        if adapter is None:
            return AdapterExecutionResult(
                success=False,
                summary="",
                error=f"No adapter registered for tool '{tool.name}'",
            )

        start = time.time()
        result = adapter.execute(request)
        elapsed = (time.time() - start) * 1000.0

        self._publish(ToolExecuted(
            tool_id=tool_id,
            name=tool.name,
            capability=request.capability,
            success=result.success,
            summary=result.summary,
            duration_ms=round(elapsed, 2),
            timestamp=time.time(),
        ))

        return result

    # --------------------------------------------------------------
    # Credential store
    # --------------------------------------------------------------

    def provide_credential(self, tool_id: UUID, key: str, value: str) -> None:
        """Store a single credential value for a tool.

        Credentials are encapsulated in ToolRuntime — never in Employee.
        Future: implement encryption-at-rest, OAuth token refresh, etc.
        """
        if tool_id not in self._credential_store:
            self._credential_store[tool_id] = {}
        self._credential_store[tool_id][key] = value

    def get_credentials(self, tool_id: UUID) -> dict[str, str]:
        """Return all stored credentials for a tool (copy)."""
        return dict(self._credential_store.get(tool_id, {}))

    def list_credential_keys(self, tool_id: UUID) -> list[str]:
        """Return the credential keys stored for a tool."""
        return list(self._credential_store.get(tool_id, {}).keys())

    # --------------------------------------------------------------
    # Internals
    # --------------------------------------------------------------

    def _require_tool(self, tool_id: UUID) -> ToolDefinition:
        tool = self._tools.get(tool_id)
        if tool is None:
            raise KeyError(f"Tool {tool_id} not found")
        return tool

    def _publish(self, event: Any) -> None:
        if self._event_bus is not None:
            self._event_bus.publish(event)
