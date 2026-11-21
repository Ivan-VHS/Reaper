"""Durable, integrity-checked snapshots for the Reaper reference runtime.

The capsule store is deliberately explicit: a host must inject its storage root
before programs can read or write snapshots. It uses atomic file replacement and
SHA-256 checksums to detect accidental corruption; it is not encryption, a
signature system, an OS sandbox, or a guarantee against a hostile local writer.
"""
from __future__ import annotations

import hashlib
import json
import math
import os
import re
import tempfile
import threading
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


SNAPSHOT_FORMAT = "reaper.immortality-capsule.v1"
HEAD_FORMAT = "reaper.immortality-capsule-head.v1"
_DEFAULT_MAX_SNAPSHOT_BYTES = 8 * 1024 * 1024
_DEFAULT_MAX_SNAPSHOTS = 16
_CAPSULE_ID = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,63}$")
_SNAPSHOT_NAME = re.compile(r"^snapshot-(\d{8})-([a-f0-9]{8})\.json$")
_WINDOWS_RESERVED = {
    "CON", "PRN", "AUX", "NUL",
    *(f"COM{i}" for i in range(1, 10)),
    *(f"LPT{i}" for i in range(1, 10)),
}


class CapsuleStoreError(ValueError):
    """Base error for invalid capsule data or storage operations."""


class CapsuleNotFoundError(CapsuleStoreError):
    """Raised when no snapshot exists for the requested capsule."""


class CapsuleIntegrityError(CapsuleStoreError):
    """Raised when snapshots exist but none pass integrity validation."""


@dataclass(frozen=True, slots=True)
class CapsuleSnapshot:
    capsule_id: str
    revision: int
    created_at: str
    payload: Any
    sha256: str
    recovered: bool = False
    filename: str = ""

    def to_dict(self) -> dict[str, Any]:
        """Return JSON-ready metadata without copying the payload."""
        return {
            "capsule_id": self.capsule_id,
            "revision": self.revision,
            "created_at": self.created_at,
            "sha256": self.sha256,
            "recovered": self.recovered,
            "filename": self.filename,
        }


class CapsuleStore:
    """Append-only, bounded snapshots with automatic fallback recovery.

    Each capsule gets an isolated directory. Snapshots are immutable files; a
    small HEAD document is replaced atomically only after a snapshot is durable.
    If HEAD or its referenced snapshot is damaged, load() scans older valid
    snapshots and repairs HEAD to the newest recoverable revision.
    """

    def __init__(
        self,
        root: str | os.PathLike[str],
        *,
        max_snapshot_bytes: int = _DEFAULT_MAX_SNAPSHOT_BYTES,
        max_snapshots: int = _DEFAULT_MAX_SNAPSHOTS,
    ) -> None:
        if isinstance(max_snapshot_bytes, bool) or not isinstance(max_snapshot_bytes, int) or max_snapshot_bytes < 256:
            raise ValueError("max_snapshot_bytes must be an integer of at least 256")
        if isinstance(max_snapshots, bool) or not isinstance(max_snapshots, int) or max_snapshots < 2:
            raise ValueError("max_snapshots must be an integer of at least 2")
        self.root = Path(root).expanduser().resolve()
        self.max_snapshot_bytes = max_snapshot_bytes
        self.max_snapshots = max_snapshots
        self._lock = threading.RLock()
        self.root.mkdir(parents=True, exist_ok=True)
        if not self.root.is_dir():
            raise ValueError("capsule root must be a directory")

    @staticmethod
    def _validate_id(capsule_id: Any) -> str:
        if not isinstance(capsule_id, str) or not _CAPSULE_ID.fullmatch(capsule_id):
            raise CapsuleStoreError(
                "capsule id must be 1-64 ASCII letters, digits, dots, underscores or hyphens; "
                "it must start with a letter or digit"
            )
        if capsule_id.endswith(".") or capsule_id.split(".", 1)[0].upper() in _WINDOWS_RESERVED:
            raise CapsuleStoreError("capsule id is reserved or not portable across platforms")
        return capsule_id

    def _capsule_dir(self, capsule_id: Any, *, create: bool = False) -> Path:
        safe_id = self._validate_id(capsule_id)
        directory = self.root / safe_id
        if directory.is_symlink():
            raise CapsuleStoreError("capsule directory must not be a symbolic link")
        resolved = directory.resolve()
        try:
            resolved.relative_to(self.root)
        except ValueError as error:
            raise CapsuleStoreError("capsule path escapes the configured root") from error
        if create:
            directory.mkdir(parents=False, exist_ok=True)
            if directory.is_symlink() or not directory.is_dir():
                raise CapsuleStoreError("capsule path is not a regular directory")
        return directory

    @staticmethod
    def _validate_payload(value: Any, *, depth: int = 0, active: set[int] | None = None) -> None:
        if depth > 64:
            raise CapsuleStoreError("capsule payload nesting exceeds 64 levels")
        if active is None:
            active = set()
        if value is None or isinstance(value, (str, bool, int)):
            return
        if isinstance(value, float):
            if not math.isfinite(value):
                raise CapsuleStoreError("capsule payload numbers must be finite")
            return
        if isinstance(value, list):
            identity = id(value)
            if identity in active:
                raise CapsuleStoreError("capsule payload must not contain circular references")
            active.add(identity)
            try:
                for item in value:
                    CapsuleStore._validate_payload(item, depth=depth + 1, active=active)
            finally:
                active.remove(identity)
            return
        if isinstance(value, dict):
            identity = id(value)
            if identity in active:
                raise CapsuleStoreError("capsule payload must not contain circular references")
            active.add(identity)
            try:
                for key, item in value.items():
                    if not isinstance(key, str):
                        raise CapsuleStoreError("capsule map keys must be text")
                    CapsuleStore._validate_payload(item, depth=depth + 1, active=active)
            finally:
                active.remove(identity)
            return
        raise CapsuleStoreError(
            f"unsupported capsule value type: {type(value).__name__}; "
            "use JSON-compatible maps, lists, text, numbers, booleans or null"
        )

    @staticmethod
    def _canonical_bytes(value: Any) -> bytes:
        try:
            return json.dumps(
                value,
                ensure_ascii=False,
                allow_nan=False,
                sort_keys=True,
                separators=(",", ":"),
            ).encode("utf-8")
        except (TypeError, ValueError, UnicodeEncodeError, RecursionError) as error:
            raise CapsuleStoreError(f"capsule data cannot be encoded as canonical JSON: {error}") from error

    @staticmethod
    def _sha256(data: bytes) -> str:
        return hashlib.sha256(data).hexdigest()

    @staticmethod
    def _reject_constant(value: str) -> None:
        raise ValueError(f"non-standard JSON numeric constant {value!r} is not permitted")

    def _atomic_write(self, destination: Path, data: bytes) -> None:
        temporary: str | None = None
        try:
            descriptor, temporary = tempfile.mkstemp(
                prefix=f".{destination.name}.", suffix=".tmp", dir=destination.parent
            )
            with os.fdopen(descriptor, "wb") as stream:
                stream.write(data)
                stream.flush()
                os.fsync(stream.fileno())
            os.replace(temporary, destination)
            temporary = None
            if os.name == "posix":
                try:
                    directory_fd = os.open(destination.parent, os.O_RDONLY)
                    try:
                        os.fsync(directory_fd)
                    finally:
                        os.close(directory_fd)
                except OSError:
                    # Some filesystems do not permit directory fsync.
                    pass
        except OSError as error:
            raise CapsuleStoreError(f"atomic capsule write failed: {error}") from error
        finally:
            if temporary is not None:
                try:
                    os.unlink(temporary)
                except FileNotFoundError:
                    pass

    def _snapshot_paths(self, directory: Path) -> list[Path]:
        paths: list[Path] = []
        for path in directory.glob("snapshot-*.json"):
            match = _SNAPSHOT_NAME.fullmatch(path.name)
            if match and path.is_file() and not path.is_symlink():
                paths.append(path)
        return sorted(
            paths,
            key=lambda item: (int(_SNAPSHOT_NAME.fullmatch(item.name).group(1)), item.name),
            reverse=True,
        )

    def _read_snapshot(
        self, path: Path, capsule_id: str, expected_digest: str | None = None
    ) -> CapsuleSnapshot:
        try:
            if path.is_symlink() or not path.is_file():
                raise CapsuleIntegrityError("snapshot is not a regular file")
            raw = path.read_bytes()
            if len(raw) > self.max_snapshot_bytes:
                raise CapsuleIntegrityError("snapshot exceeds the configured size limit")
            value = json.loads(raw.decode("utf-8"), parse_constant=self._reject_constant)
        except CapsuleIntegrityError:
            raise
        except (OSError, UnicodeDecodeError, json.JSONDecodeError, ValueError) as error:
            raise CapsuleIntegrityError(f"cannot read snapshot {path.name}: {error}") from error
        if not isinstance(value, dict) or value.get("format") != SNAPSHOT_FORMAT:
            raise CapsuleIntegrityError("snapshot format is invalid")
        if value.get("capsule_id") != capsule_id:
            raise CapsuleIntegrityError("snapshot capsule id does not match its directory")
        revision = value.get("revision")
        if isinstance(revision, bool) or not isinstance(revision, int) or revision < 1:
            raise CapsuleIntegrityError("snapshot revision is invalid")
        filename_match = _SNAPSHOT_NAME.fullmatch(path.name)
        if filename_match is None or int(filename_match.group(1)) != revision:
            raise CapsuleIntegrityError("snapshot filename and revision do not match")
        created_at = value.get("created_at")
        if not isinstance(created_at, str) or not created_at:
            raise CapsuleIntegrityError("snapshot timestamp is invalid")
        payload = value.get("payload")
        try:
            self._validate_payload(payload)
            payload_bytes = self._canonical_bytes(payload)
        except CapsuleStoreError as error:
            raise CapsuleIntegrityError(f"snapshot payload is invalid: {error}") from error
        payload_digest = self._sha256(payload_bytes)
        if value.get("payload_sha256") != payload_digest:
            raise CapsuleIntegrityError("payload checksum mismatch")
        body = {key: item for key, item in value.items() if key != "snapshot_sha256"}
        snapshot_digest = self._sha256(self._canonical_bytes(body))
        if value.get("snapshot_sha256") != snapshot_digest:
            raise CapsuleIntegrityError("snapshot checksum mismatch")
        if expected_digest is not None and expected_digest != snapshot_digest:
            raise CapsuleIntegrityError("HEAD checksum does not match snapshot")
        return CapsuleSnapshot(
            capsule_id=capsule_id,
            revision=revision,
            created_at=created_at,
            payload=payload,
            sha256=snapshot_digest,
            recovered=False,
            filename=path.name,
        )

    def _read_head(self, directory: Path, capsule_id: str) -> tuple[Path, str] | None:
        head_path = directory / "HEAD.json"
        if head_path.is_symlink() or not head_path.is_file():
            return None
        try:
            raw = head_path.read_bytes()
            if len(raw) > 4096:
                return None
            head = json.loads(raw.decode("utf-8"), parse_constant=self._reject_constant)
        except (OSError, UnicodeDecodeError, json.JSONDecodeError, ValueError):
            return None
        if not isinstance(head, dict) or head.get("format") != HEAD_FORMAT:
            return None
        if head.get("capsule_id") != capsule_id:
            return None
        filename = head.get("file")
        digest = head.get("snapshot_sha256")
        revision = head.get("revision")
        filename_match = _SNAPSHOT_NAME.fullmatch(filename) if isinstance(filename, str) else None
        if filename_match is None:
            return None
        if (
            isinstance(revision, bool)
            or not isinstance(revision, int)
            or revision != int(filename_match.group(1))
        ):
            return None
        if not isinstance(digest, str) or not re.fullmatch(r"[a-f0-9]{64}", digest):
            return None
        path = directory / filename
        if path.is_symlink() or not path.is_file():
            return None
        return path, digest

    def _write_head(self, directory: Path, snapshot: CapsuleSnapshot) -> None:
        head = {
            "format": HEAD_FORMAT,
            "capsule_id": snapshot.capsule_id,
            "revision": snapshot.revision,
            "file": snapshot.filename,
            "snapshot_sha256": snapshot.sha256,
        }
        self._atomic_write(directory / "HEAD.json", self._canonical_bytes(head))

    def _prune(self, directory: Path) -> None:
        paths = self._snapshot_paths(directory)
        for path in paths[self.max_snapshots:]:
            try:
                path.unlink()
            except OSError as error:
                raise CapsuleStoreError(f"cannot prune old capsule snapshot {path.name}: {error}") from error

    def save(self, capsule_id: str, payload: Any) -> CapsuleSnapshot:
        safe_id = self._validate_id(capsule_id)
        self._validate_payload(payload)
        payload_bytes = self._canonical_bytes(payload)
        if len(payload_bytes) > self.max_snapshot_bytes:
            raise CapsuleStoreError(
                f"capsule payload is {len(payload_bytes)} bytes; limit is {self.max_snapshot_bytes}"
            )
        # Serialize and reload so the committed snapshot is detached from
        # subsequent caller mutations.
        stable_payload = json.loads(payload_bytes.decode("utf-8"))
        with self._lock:
            directory = self._capsule_dir(safe_id, create=True)
            existing = self._snapshot_paths(directory)
            revision = max(
                (int(_SNAPSHOT_NAME.fullmatch(path.name).group(1)) for path in existing),
                default=0,
            ) + 1
            if revision > 99_999_999:
                raise CapsuleStoreError("capsule revision limit (99,999,999) reached")
            created_at = datetime.now(timezone.utc).isoformat(timespec="milliseconds").replace("+00:00", "Z")
            body = {
                "format": SNAPSHOT_FORMAT,
                "capsule_id": safe_id,
                "revision": revision,
                "created_at": created_at,
                "payload_sha256": self._sha256(payload_bytes),
                "payload": stable_payload,
            }
            snapshot_digest = self._sha256(self._canonical_bytes(body))
            envelope = {**body, "snapshot_sha256": snapshot_digest}
            snapshot_bytes = self._canonical_bytes(envelope)
            if len(snapshot_bytes) > self.max_snapshot_bytes:
                raise CapsuleStoreError(
                    f"capsule snapshot is {len(snapshot_bytes)} bytes; limit is {self.max_snapshot_bytes}"
                )
            suffix = uuid.uuid4().hex[:8]
            filename = f"snapshot-{revision:08d}-{suffix}.json"
            snapshot = CapsuleSnapshot(
                capsule_id=safe_id,
                revision=revision,
                created_at=created_at,
                payload=stable_payload,
                sha256=snapshot_digest,
                filename=filename,
            )
            self._atomic_write(directory / filename, snapshot_bytes)
            self._write_head(directory, snapshot)
            self._prune(directory)
            return snapshot

    def load(self, capsule_id: str, *, recover: bool = True) -> CapsuleSnapshot:
        safe_id = self._validate_id(capsule_id)
        with self._lock:
            directory = self._capsule_dir(safe_id)
            if not directory.exists():
                raise CapsuleNotFoundError(f"capsule {safe_id!r} does not exist")
            paths = self._snapshot_paths(directory)
            if not paths:
                raise CapsuleNotFoundError(f"capsule {safe_id!r} has no snapshots")
            head = self._read_head(directory, safe_id)
            candidates: list[tuple[Path, str | None]] = []
            if head is not None:
                candidates.append(head)
            head_name = head[0].name if head else None
            candidates.extend((path, None) for path in paths if path.name != head_name)
            errors: list[str] = []
            for index, (path, expected_digest) in enumerate(candidates):
                try:
                    snapshot = self._read_snapshot(path, safe_id, expected_digest)
                except CapsuleIntegrityError as error:
                    errors.append(str(error))
                    continue
                recovered = index > 0 or head is None
                if recovered:
                    snapshot = CapsuleSnapshot(
                        capsule_id=snapshot.capsule_id,
                        revision=snapshot.revision,
                        created_at=snapshot.created_at,
                        payload=snapshot.payload,
                        sha256=snapshot.sha256,
                        recovered=True,
                        filename=snapshot.filename,
                    )
                    if recover:
                        self._write_head(directory, snapshot)
                return snapshot
            detail = "; ".join(errors[:3]) or "no verifiable snapshots"
            raise CapsuleIntegrityError(f"capsule {safe_id!r} has no valid snapshot: {detail}")

    def verify(self, capsule_id: str) -> dict[str, Any]:
        safe_id = self._validate_id(capsule_id)
        with self._lock:
            directory = self._capsule_dir(safe_id)
            if not directory.exists():
                return {"capsule_id": safe_id, "valid": False, "recoverable": False, "reason": "not_found"}
            paths = self._snapshot_paths(directory)
            if not paths:
                return {"capsule_id": safe_id, "valid": False, "recoverable": False, "reason": "no_snapshots"}
            head = self._read_head(directory, safe_id)
            head_valid = False
            if head is not None:
                try:
                    self._read_snapshot(head[0], safe_id, head[1])
                    head_valid = True
                except CapsuleIntegrityError:
                    pass
            selected = None
            if head_valid and head is not None:
                selected = self._read_snapshot(head[0], safe_id, head[1])
            else:
                for path in paths:
                    try:
                        selected = self._read_snapshot(path, safe_id)
                        break
                    except CapsuleIntegrityError:
                        continue
            return {
                "capsule_id": safe_id,
                "valid": selected is not None,
                "head_valid": head_valid,
                "recoverable": selected is not None and not head_valid,
                "revision": selected.revision if selected else None,
                "sha256": selected.sha256 if selected else None,
                "checked_snapshots": len(paths),
            }

    def list_capsules(self) -> list[dict[str, Any]]:
        with self._lock:
            result: list[dict[str, Any]] = []
            for directory in sorted(self.root.iterdir(), key=lambda item: item.name.casefold()):
                if directory.is_symlink() or not directory.is_dir() or not _CAPSULE_ID.fullmatch(directory.name):
                    continue
                status = self.verify(directory.name)
                if status["valid"]:
                    result.append(status)
            return result
