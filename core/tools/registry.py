"""Tool Registry — maps capabilities to tool instances.

Employees never know specific tool names. They request a
capability (e.g. "speech_generation") and the registry finds
the best available tool automatically.

Selection is deterministic:
  1. matching capabilities
  2. only READY tools
  3. highest priority first
  4. registration order as tiebreaker
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Any
from uuid import UUID

from core.events.bus import EventBus
from core.tools.capabilities import Capability
from core.tools.models import ToolStatus
from core.tools.runtime import ToolRuntime, ToolUnavailable

# ------------------------------------------------------------------
# Events — published on the shared EventBus
# ------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class CapabilityRegistered:
    """Published when a tool is registered with capabilities."""
    tool_id: UUID
    name: str
    capabilities: tuple[str, ...]
    priority: int = 0
    timestamp: float = 0.0
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class CapabilityRequested:
    """Published when an employee requests a capability."""
    employee_id: UUID
    task_id: UUID
    capability: str
    reason: str
    timestamp: float = 0.0
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class CapabilityResolved:
    """Published when a capability is resolved to a specific tool."""
    capability: str
    tool_id: UUID
    tool_name: str
    timestamp: float = 0.0
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class CapabilityUnavailable:
    """Published when no tool can fulfil a requested capability."""
    capability: str
    reason: str
    available_tools: int = 0
    timestamp: float = 0.0
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class ToolSelected:
    """Published when the registry selects a specific tool for a capability."""
    capability: str
    tool_id: UUID
    tool_name: str
    priority: int = 0
    timestamp: float = 0.0
    metadata: dict[str, Any] = field(default_factory=dict)


# ------------------------------------------------------------------
# Internal registration record
# ------------------------------------------------------------------

@dataclass(frozen=True, slots=True)
class _CapabilityRecord:
    tool_id: UUID
    name: str
    capabilities: frozenset[Capability]
    priority: int
    registered_at: float


# ------------------------------------------------------------------
# ToolRegistry
# ------------------------------------------------------------------

class ToolRegistry:
    """Maps capabilities to tools and resolves the best available tool.

    The registry decouples employee intent (capability) from
    tool selection. Employees request what they need; the
    registry finds which tool provides it.
    """

    def __init__(
        self,
        tool_runtime: ToolRuntime,
        event_bus: EventBus | None = None,
    ) -> None:
        self._runtime = tool_runtime
        self._event_bus = event_bus
        self._records: dict[UUID, _CapabilityRecord] = {}
        self._disabled: set[UUID] = set()
        self._registration_order: list[UUID] = []

    # --------------------------------------------------------------
    # Registration
    # --------------------------------------------------------------

    def register_tool(
        self,
        tool_id: UUID,
        capabilities: set[Capability],
        *,
        priority: int = 0,
    ) -> CapabilityRegistered:
        """Register a tool with its capabilities.

        Args:
            tool_id: Must match a tool registered in ToolRuntime.
            capabilities: Set of capabilities this tool provides.
            priority: Higher values = preferred over lower.

        Returns:
            CapabilityRegistered event.
        """
        tool = self._runtime.tool_state(tool_id)
        if tool is None:
            raise KeyError(f"Tool {tool_id} not found in ToolRuntime")

        caps = frozenset(capabilities)
        record = _CapabilityRecord(
            tool_id=tool_id,
            name=tool.name,
            capabilities=caps,
            priority=priority,
            registered_at=time.time(),
        )
        self._records[tool_id] = record
        if tool_id not in self._registration_order:
            self._registration_order.append(tool_id)

        event = CapabilityRegistered(
            tool_id=tool_id,
            name=tool.name,
            capabilities=tuple(sorted(c.value for c in caps)),
            priority=priority,
            timestamp=time.time(),
        )
        self._publish(event)
        return event

    def remove_tool(self, tool_id: UUID) -> None:
        """Remove a tool from the registry."""
        self._records.pop(tool_id, None)
        self._disabled.discard(tool_id)
        if tool_id in self._registration_order:
            self._registration_order.remove(tool_id)

    # --------------------------------------------------------------
    # Enable / disable
    # --------------------------------------------------------------

    def enable(self, tool_id: UUID) -> None:
        """Re-enable a previously disabled tool."""
        self._disabled.discard(tool_id)

    def disable(self, tool_id: UUID) -> None:
        """Disable a tool (prevents it from being selected)."""
        if tool_id in self._records:
            self._disabled.add(tool_id)

    # --------------------------------------------------------------
    # Queries
    # --------------------------------------------------------------

    def list_tools(self) -> list[dict[str, Any]]:
        """List all registered tools with their capabilities."""
        result: list[dict[str, Any]] = []
        for record in self._records.values():
            tool = self._runtime.tool_state(record.tool_id)
            result.append({
                "tool_id": record.tool_id,
                "name": record.name,
                "capabilities": sorted(c.value for c in record.capabilities),
                "priority": record.priority,
                "status": tool.status.value if tool else "unknown",
                "disabled": record.tool_id in self._disabled,
            })
        return result

    def list_capabilities(self) -> dict[str, list[dict[str, Any]]]:
        """List all capabilities and which tools provide them."""
        mapping: dict[str, list[dict[str, Any]]] = {}
        for record in self._records.values():
            for cap in record.capabilities:
                key = cap.value
                if key not in mapping:
                    mapping[key] = []
                tool = self._runtime.tool_state(record.tool_id)
                mapping[key].append({
                    "tool_id": record.tool_id,
                    "name": record.name,
                    "priority": record.priority,
                    "status": tool.status.value if tool else "unknown",
                    "disabled": record.tool_id in self._disabled,
                })
        return mapping

    def find_by_capability(self, capability: Capability) -> list[dict[str, Any]]:
        """Find all tools that provide a given capability."""
        result: list[dict[str, Any]] = []
        for record in self._records.values():
            if capability in record.capabilities:
                tool = self._runtime.tool_state(record.tool_id)
                result.append({
                    "tool_id": record.tool_id,
                    "name": record.name,
                    "priority": record.priority,
                    "status": tool.status.value if tool else "unknown",
                    "disabled": record.tool_id in self._disabled,
                })
        return result

    def tool_capabilities(self, tool_id: UUID) -> list[Capability]:
        """Return the capabilities of a specific tool."""
        record = self._records.get(tool_id)
        if record is None:
            return []
        return sorted(record.capabilities, key=lambda c: c.value)

    # --------------------------------------------------------------
    # Resolution
    # --------------------------------------------------------------

    def resolve(
        self,
        capability: Capability,
        employee_id: UUID,
        task_id: UUID | None = None,
    ) -> ToolSelected | CapabilityUnavailable:
        """Resolve a capability to the best available tool.

        Selection criteria (deterministic):
          1. Tool provides the capability
          2. Tool is not disabled in registry
          3. Tool is READY in ToolRuntime
          4. Highest priority wins
          5. Earlier registration order wins (tiebreaker)

        Returns:
            ToolSelected if a tool was found and requested.
            CapabilityUnavailable if no tool is available.
        """
        self._publish(CapabilityRequested(
            employee_id=employee_id,
            task_id=task_id or UUID(int=0),
            capability=capability.value,
            reason=f"Employee {employee_id.hex[:8]} needs {capability.value}",
            timestamp=time.time(),
        ))

        candidates: list[_CapabilityRecord] = []
        for record in self._records.values():
            if record.tool_id in self._disabled:
                continue
            if capability not in record.capabilities:
                continue
            candidates.append(record)

        if not candidates:
            event = CapabilityUnavailable(
                capability=capability.value,
                reason=f"No tool registered with capability '{capability.value}'",
                available_tools=0,
                timestamp=time.time(),
            )
            self._publish(event)
            return event

        candidates.sort(key=lambda r: (-r.priority, self._registration_order.index(r.tool_id)))

        for candidate in candidates:
            availability = self._runtime.check_availability(candidate.tool_id)
            if availability["available"]:
                result = self._runtime.request_tool(
                    candidate.tool_id, employee_id, task_id=task_id,
                )
                if isinstance(result, ToolUnavailable):
                    continue

                self._publish(ToolSelected(
                    capability=capability.value,
                    tool_id=candidate.tool_id,
                    tool_name=candidate.name,
                    priority=candidate.priority,
                    timestamp=time.time(),
                ))
                self._publish(CapabilityResolved(
                    capability=capability.value,
                    tool_id=candidate.tool_id,
                    tool_name=candidate.name,
                    timestamp=time.time(),
                ))
                return ToolSelected(
                    capability=capability.value,
                    tool_id=candidate.tool_id,
                    tool_name=candidate.name,
                    priority=candidate.priority,
                    timestamp=time.time(),
                )

        ready_count = sum(
            1 for c in candidates
            if self._runtime.check_availability(c.tool_id)["available"]
        )
        total_count = len(candidates)
        names = ", ".join(c.name for c in candidates)
        event = CapabilityUnavailable(
            capability=capability.value,
            reason=f"All {total_count} tool(s) providing '{capability.value}' "
                   f"are unavailable: {names}",
            available_tools=ready_count,
            timestamp=time.time(),
        )
        self._publish(event)
        return event

    # --------------------------------------------------------------
    # Internals
    # --------------------------------------------------------------

    def _publish(self, event: Any) -> None:
        if self._event_bus is not None:
            self._event_bus.publish(event)
