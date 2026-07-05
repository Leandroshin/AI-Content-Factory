"""Helper utilities for PersistenceRuntime integration with stateful runtimes."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any
from uuid import UUID

from core.persistence.runtime import PersistenceRuntime


def save_if_enabled(
    persistence: PersistenceRuntime | None,
    snapshot: Any,
    domain: str,
    snapshot_id: str | UUID | None = None,
) -> None:
    """Save snapshot if persistence is enabled.

    Args:
        persistence: The PersistenceRuntime instance (or None).
        snapshot: The dataclass snapshot to save.
        domain: Domain subdirectory under ``storage/``.
        snapshot_id: Optional explicit snapshot ID (auto-detected when None).
    """
    if persistence is not None:
        persistence.save_snapshot(snapshot, domain, snapshot_id)


@dataclass(frozen=True, slots=True)
class CompanyTaskEntrySnapshot:
    """Lightweight frozen snapshot of a company task entry for persistence.

    Excludes orchestrator_snapshot (Any) to keep serialization clean.
    """

    task_id: UUID
    title: str
    stage: str
    metadata: dict[str, Any] = field(default_factory=dict)
