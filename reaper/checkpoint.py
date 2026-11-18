"""Checksummed JSON snapshots and atomic transactional state storage."""
from __future__ import annotations

import copy
import hashlib
import hmac
import json
import os
import tempfile
from contextlib import contextmanager
from pathlib import Path
from threading import RLock
from typing import Any, Iterator, Mapping


class SnapshotError(RuntimeError):
    pass


def _canonical(value: Any) -> str:
    try:
        return json.dumps(value, sort_keys=True, ensure_ascii=False,
                          separators=(",", ":"), allow_nan=False)
    except (TypeError, ValueError) as error:
        raise SnapshotError(f"state is not JSON-serializable: {error}") from error


class SnapshotStore:
    """Persist application state, not Python stacks or running actor execution."""

    SCHEMA_VERSION = 1

    def __init__(self, path: str | Path) -> None:
        self.path = Path(path)
        self._revision = 0
        self._lock = RLock()

    @property
    def revision(self) -> int:
        return self._revision

    def save(self, state: Any) -> int:
        state_text = _canonical(state)
        checksum = hashlib.sha256(state_text.encode("utf-8")).hexdigest()
        with self._lock:
            current_revision = self._revision
            if self.path.exists():
                try:
                    existing = json.loads(self.path.read_text(encoding="utf-8"))
                    if not isinstance(existing, dict):
                        raise ValueError("snapshot root is not an object")
                    current_revision = max(current_revision, int(existing.get("revision", 0)))
                except (OSError, ValueError, TypeError, AttributeError):
                    raise SnapshotError("cannot replace an unreadable existing snapshot")
            revision = current_revision + 1
            envelope = {
                "schema_version": self.SCHEMA_VERSION,
                "revision": revision,
                "checksum": checksum,
                "state": json.loads(state_text),
            }
            payload = _canonical(envelope)
            self.path.parent.mkdir(parents=True, exist_ok=True)
            descriptor, temporary = tempfile.mkstemp(
                prefix=f".{self.path.name}.", suffix=".tmp", dir=str(self.path.parent)
            )
            try:
                with os.fdopen(descriptor, "w", encoding="utf-8", newline="\n") as stream:
                    stream.write(payload)
                    stream.flush()
                    os.fsync(stream.fileno())
                os.replace(temporary, self.path)
            except OSError:
                try:
                    os.unlink(temporary)
                except OSError:
                    pass
                raise
            self._revision = revision
            return revision

    def load(self) -> Any:
        with self._lock:
            try:
                envelope = json.loads(self.path.read_text(encoding="utf-8"))
            except OSError:
                raise
            except (UnicodeError, json.JSONDecodeError) as error:
                raise SnapshotError(f"snapshot is not valid JSON: {error}") from error
            if not isinstance(envelope, dict):
                raise SnapshotError("snapshot root must be an object")
            if envelope.get("schema_version") != self.SCHEMA_VERSION:
                raise SnapshotError("unsupported snapshot schema version")
            state = envelope.get("state")
            expected = hashlib.sha256(_canonical(state).encode("utf-8")).hexdigest()
            if not hmac.compare_digest(expected, str(envelope.get("checksum", ""))):
                raise SnapshotError("snapshot checksum mismatch")
            revision = envelope.get("revision")
            if isinstance(revision, bool) or not isinstance(revision, int) or revision < 1:
                raise SnapshotError("snapshot revision is invalid")
            self._revision = revision
            return copy.deepcopy(state)


class TransactionalStore:
    """Copy-on-write key/value transactions committed through atomic snapshots."""

    def __init__(self, snapshot: SnapshotStore, initial: Mapping[str, Any] | None = None) -> None:
        self.snapshot = snapshot
        self._lock = RLock()
        try:
            state = snapshot.load()
        except FileNotFoundError:
            state = dict(initial or {})
        if not isinstance(state, dict):
            raise SnapshotError("transactional store root must be an object")
        self._state: dict[str, Any] = state

    def get(self, key: str, default: Any = None) -> Any:
        with self._lock:
            return copy.deepcopy(self._state.get(key, default))

    def snapshot_state(self) -> dict[str, Any]:
        with self._lock:
            return copy.deepcopy(self._state)

    @contextmanager
    def transaction(self) -> Iterator[dict[str, Any]]:
        with self._lock:
            working = copy.deepcopy(self._state)
            yield working
            self.snapshot.save(working)
            self._state = working
