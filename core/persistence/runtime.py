"""Generic persistence layer for foundation dataclass snapshots.

Stateless, side-effect-free persistence using JSON + pathlib.
No database, no SQLite, no external dependencies.

All methods are @staticmethod.
"""

from __future__ import annotations

import importlib
import json
import time
from dataclasses import dataclass, fields
from pathlib import Path
from typing import Any, get_args, get_origin
from uuid import UUID

STORAGE_ROOT = Path("storage")


# ------------------------------------------------------------------
# Data models
# ------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class PersistenceSnapshot:
    """Wrapper that stores a serialised snapshot with metadata.

    Attributes:
        snapshot_id: Unique identifier for this snapshot (usually the UUID str).
        domain: Domain subdirectory (e.g. "conversation", "memory"…).
        saved_at: Unix timestamp of when the snapshot was written.
        type_name: Fully qualified class name (e.g.
            "core.memory.runtime.MemorySnapshot").
        data: The serialised dataclass payload as a JSON-compatible dict.
    """

    snapshot_id: str
    domain: str
    saved_at: float
    type_name: str
    data: dict[str, Any]


@dataclass(frozen=True, slots=True)
class PersistenceResult:
    """Outcome of a single persistence operation.

    Attributes:
        success: True when the operation succeeded.
        snapshot: The reconstructed (or saved) snapshot on success.
        error_message: Human-readable error on failure.
        path: Absolute or relative file path involved.
        duration: Wall-clock time in seconds.
    """

    success: bool
    snapshot: Any = None
    error_message: str = ""
    path: str = ""
    duration: float = 0.0


@dataclass(frozen=True, slots=True)
class PersistenceTrace:
    """Execution trace for a persistence operation.

    Attributes:
        operation: The operation name (save, load, delete, list…).
        domain: Domain subdirectory.
        snapshot_id: Identifier of the snapshot.
        duration: Wall-clock time in seconds.
        success: Whether the operation succeeded.
        path: File path involved.
    """

    operation: str
    domain: str
    snapshot_id: str
    duration: float
    success: bool
    path: str


# ------------------------------------------------------------------
# Internal serialisation helpers
# ------------------------------------------------------------------


def _is_dataclass_type(tp: type) -> bool:
    return hasattr(tp, "__dataclass_fields__")


def _is_uuid_type(tp: type) -> bool:
    return tp is UUID or (isinstance(tp, type) and issubclass(tp, UUID))


def _type_name(obj: Any) -> str:
    cls = obj if isinstance(obj, type) else type(obj)
    return f"{cls.__module__}.{cls.__qualname__}"


def _import_type(type_name: str) -> type:
    module_path, _, class_name = type_name.rpartition(".")
    mod = importlib.import_module(module_path)
    return getattr(mod, class_name)


def _value_to_dict(value: Any) -> Any:
    """Recursively convert a dataclass value to JSON-safe dict."""
    if value is None:
        return None
    if isinstance(value, UUID):
        return str(value)
    if isinstance(value, frozenset):
        return sorted(_value_to_dict(v) for v in value)
    if isinstance(value, (tuple, list)):
        return [_value_to_dict(v) for v in value]
    if isinstance(value, dict):
        return {str(k): _value_to_dict(v) for k, v in value.items()}
    if _is_dataclass_type(type(value)):
        return {f.name: _value_to_dict(getattr(value, f.name)) for f in fields(value)}
    if isinstance(value, (str, int, float, bool)):
        return value
    return str(value)


def _snapshot_to_dict(snapshot: Any) -> dict[str, Any]:
    """Convert any frozen dataclass to a JSON-safe dict."""
    return {f.name: _value_to_dict(getattr(snapshot, f.name)) for f in fields(snapshot)}


def _value_from_dict(value: Any, target_type: type) -> Any:
    """Recursively reconstruct a typed value from a JSON-safe dict."""
    if value is None:
        return None

    origin = get_origin(target_type)
    args = get_args(target_type)

    # --- Union / Optional ---
    if origin is type(Union) or (origin is Union and type(None) in args):
        non_none = [a for a in args if a is not type(None)]
        if non_none:
            return _value_from_dict(value, non_none[0])
        return value

    # --- tuple[X, ...] ---
    if origin is tuple and isinstance(value, list):
        elem_type = args[0] if args else Any
        return tuple(_value_from_dict(v, elem_type) for v in value)

    # --- frozenset[X] ---
    if origin is frozenset and isinstance(value, list):
        elem_type = args[0] if args else Any
        return frozenset(_value_from_dict(v, elem_type) for v in value)

    # --- list[X] ---
    if origin is list and isinstance(value, list):
        elem_type = args[0] if args else Any
        return [_value_from_dict(v, elem_type) for v in value]

    # --- dict[K, V] ---
    if origin is dict and isinstance(value, dict):
        val_type = args[1] if len(args) > 1 else Any
        return {k: _value_from_dict(v, val_type) for k, v in value.items()}

    # --- UUID ---
    if _is_uuid_type(target_type) and isinstance(value, str):
        return UUID(value)

    # --- nested dataclass ---
    if _is_dataclass_type(target_type) and isinstance(value, dict):
        return _from_dict(target_type, value)

    return value


def _from_dict(cls: type, data: dict) -> Any:
    """Generic frozen dataclass reconstruction from a flat JSON dict."""
    from typing import get_type_hints

    hints = get_type_hints(cls)
    kwargs: dict[str, Any] = {}
    for f in fields(cls):
        if f.name not in data:
            continue
        ftype = hints.get(f.name, f.type)
        kwargs[f.name] = _value_from_dict(data[f.name], ftype)
    _apply_immutable_defaults(cls, kwargs, data)
    return cls(**kwargs)


def _apply_immutable_defaults(cls: type, kwargs: dict[str, Any], data: dict[str, Any]) -> None:
    """Fill frozen fields that have defaults but were not in the JSON data."""
    for f in fields(cls):
        if f.name not in kwargs and f.name not in data:
            if f.default_factory is not None:
                kwargs[f.name] = f.default_factory()
            elif f.default is not None:
                kwargs[f.name] = f.default


# ------------------------------------------------------------------
# File-system helpers
# ------------------------------------------------------------------


def _domain_path(domain: str, ensure: bool = False) -> Path:
    p = STORAGE_ROOT / domain
    if ensure:
        p.mkdir(parents=True, exist_ok=True)
    return p


def _snapshot_path(domain: str, snapshot_id: str) -> Path:
    safe_id = str(snapshot_id).replace("/", "_").replace("\\", "_")
    return _domain_path(domain) / f"{safe_id}.json"


def _now() -> float:
    return time.time()


# ------------------------------------------------------------------
# PersistenceRuntime
# ------------------------------------------------------------------


class PersistenceRuntime:
    """Stateless, generic persistence layer for dataclass snapshots.

    All methods are @staticmethod. No mutable state.
    Compatible with any frozen dataclass.
    """

    # --------------------------------------------------------------
    # Core operations
    # --------------------------------------------------------------

    @staticmethod
    def save_snapshot(
        snapshot: Any,
        domain: str,
        snapshot_id: str | UUID | None = None,
    ) -> PersistenceResult:
        """Save a dataclass snapshot to ``storage/{domain}/{id}.json``.

        Args:
            snapshot: Any frozen dataclass instance to persist.
            domain: Subdirectory under ``storage/`` (e.g. ``"memory"``).
            snapshot_id: Explicit ID. When ``None`` the first UUID field
                found on the snapshot is used.

        Returns:
            A PersistenceResult with the saved metadata.
        """
        start = _now()
        try:
            sid = _resolve_id(snapshot, snapshot_id)
            p = _snapshot_path(domain, sid)
            p.parent.mkdir(parents=True, exist_ok=True)

            data = _snapshot_to_dict(snapshot)
            wrapper = PersistenceSnapshot(
                snapshot_id=sid,
                domain=domain,
                saved_at=start,
                type_name=_type_name(snapshot),
                data=data,
            )
            wrapper_dict = _snapshot_to_dict(wrapper)

            with open(p, "w", encoding="utf-8") as f:
                json.dump(wrapper_dict, f, indent=2, ensure_ascii=False)

            return PersistenceResult(
                success=True,
                snapshot=wrapper,
                path=str(p),
                duration=_now() - start,
            )
        except Exception as exc:
            return PersistenceResult(
                success=False,
                error_message=str(exc),
                duration=_now() - start,
            )

    @staticmethod
    def load_snapshot(
        domain: str,
        snapshot_id: str | UUID,
    ) -> PersistenceResult:
        """Load a previously saved snapshot from disk.

        Args:
            domain: Subdirectory under ``storage/``.
            snapshot_id: The snapshot identifier (UUID or string).

        Returns:
            A PersistenceResult. On success ``.snapshot`` contains the
            reconstructed dataclass instance; ``.path`` contains the
            JSON file path.
        """
        start = _now()
        try:
            p = _snapshot_path(domain, snapshot_id)
            if not p.exists():
                return PersistenceResult(
                    success=False,
                    error_message=f"Snapshot not found: {p}",
                    path=str(p),
                    duration=_now() - start,
                )
            with open(p, "r", encoding="utf-8") as f:
                wrapper_dict = json.load(f)

            wrapper = _from_dict(PersistenceSnapshot, wrapper_dict)
            target_class = _import_type(wrapper.type_name)
            snapshot = _from_dict(target_class, wrapper.data)

            return PersistenceResult(
                success=True,
                snapshot=snapshot,
                path=str(p),
                duration=_now() - start,
            )
        except Exception as exc:
            return PersistenceResult(
                success=False,
                error_message=str(exc),
                duration=_now() - start,
            )

    @staticmethod
    def snapshot_exists(domain: str, snapshot_id: str | UUID) -> bool:
        """Check whether a snapshot file exists on disk."""
        return _snapshot_path(domain, snapshot_id).exists()

    @staticmethod
    def delete_snapshot(
        domain: str,
        snapshot_id: str | UUID,
    ) -> PersistenceResult:
        """Delete a previously saved snapshot file.

        Returns success even when the file does not exist (idempotent).
        """
        start = _now()
        try:
            p = _snapshot_path(domain, snapshot_id)
            if p.exists():
                p.unlink()
            return PersistenceResult(
                success=True,
                path=str(p),
                duration=_now() - start,
            )
        except Exception as exc:
            return PersistenceResult(
                success=False,
                error_message=str(exc),
                duration=_now() - start,
            )

    @staticmethod
    def list_snapshots(domain: str) -> PersistenceResult:
        """List all snapshots in a domain directory.

        Returns:
            A PersistenceResult with ``.snapshot`` set to a list of
            ``PersistenceSnapshot`` metadata dicts (id, domain, saved_at,
            type_name). Non-JSON files are silently skipped.
        """
        start = _now()
        try:
            dp = _domain_path(domain)
            if not dp.exists():
                return PersistenceResult(
                    success=True, snapshot=[], duration=_now() - start,
                )
            entries: list[dict[str, Any]] = []
            for child in sorted(dp.iterdir()):
                if child.suffix.lower() != ".json":
                    continue
                try:
                    with open(child, "r", encoding="utf-8") as f:
                        raw = json.load(f)
                    entries.append({
                        "snapshot_id": raw.get("snapshot_id", child.stem),
                        "domain": raw.get("domain", domain),
                        "saved_at": raw.get("saved_at", 0.0),
                        "type_name": raw.get("type_name", ""),
                        "file": child.name,
                    })
                except Exception:
                    entries.append({
                        "snapshot_id": child.stem,
                        "domain": domain,
                        "saved_at": 0.0,
                        "type_name": "",
                        "file": child.name,
                    })
            return PersistenceResult(
                success=True, snapshot=entries, duration=_now() - start,
            )
        except Exception as exc:
            return PersistenceResult(
                success=False,
                error_message=str(exc),
                duration=_now() - start,
            )

    # --------------------------------------------------------------
    # JSON export / import
    # --------------------------------------------------------------

    @staticmethod
    def export_json(
        snapshot: Any,
        filepath: str | Path,
        domain: str = "",
        snapshot_id: str | UUID | None = None,
    ) -> PersistenceResult:
        """Serialise a dataclass snapshot to an arbitrary JSON file.

        Unlike ``save_snapshot`` this writes to any path without the
        ``storage/{domain}/`` convention.

        Args:
            snapshot: The dataclass instance to export.
            filepath: Destination file path.
            domain: Optional domain label stored in the wrapper.
            snapshot_id: Optional explicit ID (auto-detected when None).

        Returns:
            A PersistenceResult.
        """
        start = _now()
        try:
            sid = _resolve_id(snapshot, snapshot_id)
            p = Path(filepath)
            p.parent.mkdir(parents=True, exist_ok=True)

            data = _snapshot_to_dict(snapshot)
            wrapper = PersistenceSnapshot(
                snapshot_id=sid,
                domain=domain,
                saved_at=start,
                type_name=_type_name(snapshot),
                data=data,
            )
            with open(p, "w", encoding="utf-8") as f:
                json.dump(_snapshot_to_dict(wrapper), f, indent=2, ensure_ascii=False)

            return PersistenceResult(
                success=True, snapshot=wrapper, path=str(p),
                duration=_now() - start,
            )
        except Exception as exc:
            return PersistenceResult(
                success=False, error_message=str(exc),
                duration=_now() - start,
            )

    @staticmethod
    def import_json(
        filepath: str | Path,
    ) -> PersistenceResult:
        """Load a dataclass snapshot from an arbitrary JSON file.

        Returns:
            A PersistenceResult. On success ``.snapshot`` contains the
            reconstructed dataclass instance.
        """
        start = _now()
        try:
            p = Path(filepath)
            if not p.exists():
                return PersistenceResult(
                    success=False,
                    error_message=f"File not found: {p}",
                    duration=_now() - start,
                )
            with open(p, "r", encoding="utf-8") as f:
                wrapper_dict = json.load(f)

            wrapper = _from_dict(PersistenceSnapshot, wrapper_dict)
            target_class = _import_type(wrapper.type_name)
            snapshot = _from_dict(target_class, wrapper.data)

            return PersistenceResult(
                success=True, snapshot=snapshot, path=str(p),
                duration=_now() - start,
            )
        except Exception as exc:
            return PersistenceResult(
                success=False, error_message=str(exc),
                duration=_now() - start,
            )

    # --------------------------------------------------------------
    # Utility
    # --------------------------------------------------------------

    @staticmethod
    def clean_domain(domain: str) -> PersistenceResult:
        """Delete all snapshot files in a domain directory.

        The directory itself is preserved. Idempotent.
        """
        start = _now()
        try:
            dp = _domain_path(domain)
            if dp.exists():
                count = 0
                for child in list(dp.iterdir()):
                    if child.suffix.lower() == ".json":
                        child.unlink()
                        count += 1
            return PersistenceResult(
                success=True,
                snapshot={"deleted": count} if dp.exists() else {"deleted": 0},
                duration=_now() - start,
            )
        except Exception as exc:
            return PersistenceResult(
                success=False, error_message=str(exc),
                duration=_now() - start,
            )

    @staticmethod
    def storage_info() -> PersistenceResult:
        """Get an overview of all domains and file counts under storage/.

        Returns a PersistenceResult with .snapshot set to a dict mapping
        domain names to file counts.
        """
        start = _now()
        try:
            root = STORAGE_ROOT
            if not root.exists():
                return PersistenceResult(
                    success=True, snapshot={}, duration=_now() - start,
                )
            info: dict[str, int] = {}
            for child in sorted(root.iterdir()):
                if child.is_dir():
                    count = len(list(child.glob("*.json")))
                    if count:
                        info[child.name] = count
            return PersistenceResult(
                success=True, snapshot=info, duration=_now() - start,
            )
        except Exception as exc:
            return PersistenceResult(
                success=False, error_message=str(exc),
                duration=_now() - start,
            )


# ------------------------------------------------------------------
# Internal helpers
# ------------------------------------------------------------------


def _resolve_id(snapshot: Any, explicit: str | UUID | None) -> str:
    """Return an explicit ID or auto-detect from the snapshot.

    Detection priority:
      1. First UUID field on the snapshot itself.
      2. First UUID field inside the first tuple-of-dataclasses field
         (e.g. MemorySnapshot.records → MemoryRecord.memory_id).
      3. SHA-256 hex digest of the JSON representation as last resort.
    """
    if explicit is not None:
        return str(explicit)

    # 1. Direct UUID field
    for f in fields(snapshot):
        val = getattr(snapshot, f.name)
        if isinstance(val, UUID):
            return str(val)

    # 2. UUID inside tuple fields (records, skills, steps, …)
    for f in fields(snapshot):
        val = getattr(snapshot, f.name)
        if isinstance(val, (tuple, list)) and val:
            first = val[0]
            if hasattr(first, "__dataclass_fields__"):
                for inner_f in fields(first):
                    inner_val = getattr(first, inner_f.name)
                    if isinstance(inner_val, UUID):
                        return str(inner_val)

    # 3. Content-based hash (deterministic across runs)
    import hashlib
    raw = _snapshot_to_dict(snapshot)
    digest = hashlib.sha256(json.dumps(raw, sort_keys=True).encode()).hexdigest()[:16]
    return digest


# Forward declaration for get_type_hints in Python 3.11
from typing import Union
