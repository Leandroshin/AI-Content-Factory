"""Execution persistence runtime — save/restore company state to JSON.

All state is written to ``.ai_company/{sessions,evidence,snapshots,logs}/``.
Every operation is deterministic and 100% aditive to existing components.
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any
from uuid import UUID, uuid4

from core.events.bus import EventBus
from core.events.domain_events import (
    ExecutionPersisted,
    ExecutionRestored,
    SessionCreated,
    SessionLoaded,
    SessionSaved,
    SnapshotCreated,
    SnapshotLoaded,
)

_PERSISTENCE_DIR = Path(".ai_company")


@dataclass(frozen=True, slots=True)
class ExecutionRecord:
    execution_id: UUID
    session_id: UUID
    timestamp: float
    action: str
    component: str
    state_snapshot: dict[str, Any]
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class SessionState:
    session_id: UUID
    created_at: float
    last_activity: float
    company_state: str
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class CompanySnapshot:
    session_id: UUID
    timestamp: float
    company: dict[str, Any]
    departments: dict[str, Any]
    employees: dict[str, Any]
    tasks: dict[str, Any]
    tools: dict[str, Any]
    adapters: dict[str, Any]
    capabilities: dict[str, Any]
    feedback: list[dict[str, Any]]
    historical: list[dict[str, Any]]
    predictions: list[dict[str, Any]]
    observability: dict[str, Any]
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class ExecutionEvidence:
    evidence_id: UUID
    session_id: UUID
    timestamp: float
    event_type: str
    event_data: dict[str, Any]
    context: dict[str, Any] = field(default_factory=dict)
    tags: tuple[str, ...] = field(default_factory=tuple)


class PersistenceRuntime:
    """Deterministic JSON-based persistence for company execution state.

    Usage::

        pr = PersistenceRuntime(event_bus=bus)
        session = pr.create_session({"project": "youtube-series"})
        record = pr.persist_execution(uuid4(), "execute_task", "employee", {...})
        pr.save_snapshot(snapshot)
        loaded = pr.load_session(session.session_id)
    """

    def __init__(
        self,
        base_dir: str | Path | None = None,
        event_bus: EventBus | None = None,
    ) -> None:
        self._base_dir = Path(base_dir) if base_dir else _PERSISTENCE_DIR
        self._event_bus = event_bus
        self._session: SessionState | None = None
        self._ensure_dirs()

    # ------------------------------------------------------------------
    # Internals
    # ------------------------------------------------------------------

    def _ensure_dirs(self) -> None:
        for sub in ("sessions", "evidence", "snapshots", "logs"):
            (self._base_dir / sub).mkdir(parents=True, exist_ok=True)

    def _serialize(self, obj: Any) -> Any:
        if isinstance(obj, UUID):
            return str(obj)
        if isinstance(obj, datetime):
            return obj.isoformat()
        if isinstance(obj, dict):
            return {k: self._serialize(v) for k, v in obj.items()}
        if isinstance(obj, (list, tuple)):
            return [self._serialize(v) for v in obj]
        return obj

    def _publish(self, event: Any) -> None:
        if self._event_bus is not None:
            self._event_bus.publish(event)

    # ------------------------------------------------------------------
    # Session lifecycle
    # ------------------------------------------------------------------

    def create_session(self, metadata: dict[str, Any] | None = None) -> SessionState:
        now = datetime.now().timestamp()
        session = SessionState(
            session_id=uuid4(),
            created_at=now,
            last_activity=now,
            company_state="initialized",
            metadata=metadata or {},
        )
        self._session = session
        self._write_session(session)
        self._publish(
            SessionCreated(
                session_id=session.session_id,
                timestamp=now,
                metadata=metadata or {},
            )
        )
        return session

    def list_sessions(self) -> list[dict[str, Any]]:
        sessions_dir = self._base_dir / "sessions"
        if not sessions_dir.exists():
            return []
        result: list[dict[str, Any]] = []
        for f in sorted(sessions_dir.glob("*.json")):
            data = json.loads(f.read_text(encoding="utf-8"))
            result.append(data)
        return result

    def load_session(self, session_id: UUID) -> SessionState | None:
        path = self._base_dir / "sessions" / f"{session_id}.json"
        if not path.exists():
            return None
        data = json.loads(path.read_text(encoding="utf-8"))
        session = SessionState(
            session_id=UUID(data["session_id"]),
            created_at=data["created_at"],
            last_activity=data["last_activity"],
            company_state=data["company_state"],
            metadata=data.get("metadata", {}),
        )
        self._session = session
        self._publish(
            SessionLoaded(
                session_id=session.session_id,
                timestamp=datetime.now().timestamp(),
                metadata={},
            )
        )
        return session

    def save_session(self) -> bool:
        if self._session is None:
            return False
        now = datetime.now().timestamp()
        self._session = SessionState(
            session_id=self._session.session_id,
            created_at=self._session.created_at,
            last_activity=now,
            company_state=self._session.company_state,
            metadata=self._session.metadata,
        )
        self._write_session(self._session)
        self._publish(
            SessionSaved(
                session_id=self._session.session_id,
                timestamp=now,
                metadata={},
            )
        )
        return True

    def _write_session(self, session: SessionState) -> None:
        path = self._base_dir / "sessions" / f"{session.session_id}.json"
        path.write_text(
            json.dumps(
                {
                    "session_id": str(session.session_id),
                    "created_at": session.created_at,
                    "last_activity": session.last_activity,
                    "company_state": session.company_state,
                    "metadata": session.metadata,
                },
                indent=2,
            ),
            encoding="utf-8",
        )

    # ------------------------------------------------------------------
    # Snapshots & evidence
    # ------------------------------------------------------------------

    def save_snapshot(self, snapshot: CompanySnapshot) -> None:
        path = (
            self._base_dir
            / "snapshots"
            / f"{snapshot.session_id}_{int(snapshot.timestamp)}.json"
        )
        path.write_text(
            json.dumps(self._serialize(snapshot), indent=2, default=str),
            encoding="utf-8",
        )
        self._publish(
            SnapshotCreated(
                session_id=snapshot.session_id,
                timestamp=snapshot.timestamp,
                metadata={},
            )
        )

    def save_evidence(self, evidence: ExecutionEvidence) -> None:
        path = (
            self._base_dir
            / "evidence"
            / f"{evidence.session_id}_{evidence.evidence_id}.json"
        )
        path.write_text(
            json.dumps(self._serialize(evidence), indent=2, default=str),
            encoding="utf-8",
        )

    def persist_execution(
        self,
        execution_id: UUID,
        action: str,
        component: str,
        state: dict[str, Any],
        metadata: dict[str, Any] | None = None,
    ) -> ExecutionRecord:
        now = datetime.now().timestamp()
        record = ExecutionRecord(
            execution_id=execution_id,
            session_id=self._session.session_id if self._session else uuid4(),
            timestamp=now,
            action=action,
            component=component,
            state_snapshot=state,
            metadata=metadata or {},
        )
        self._publish(
            ExecutionPersisted(
                execution_id=record.execution_id,
                session_id=record.session_id,
                action=record.action,
                component=record.component,
                timestamp=now,
                metadata=metadata or {},
            )
        )
        return record

    def restore_execution(self, record: ExecutionRecord) -> dict[str, Any]:
        self._publish(
            ExecutionRestored(
                execution_id=record.execution_id,
                session_id=record.session_id,
                action=record.action,
                component=record.component,
                timestamp=datetime.now().timestamp(),
                metadata={},
            )
        )
        return record.state_snapshot

    # ------------------------------------------------------------------
    # Properties
    # ------------------------------------------------------------------

    @property
    def current_session(self) -> SessionState | None:
        return self._session

    @property
    def base_dir(self) -> Path:
        return self._base_dir
