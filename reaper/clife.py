"""CLife repository lifecycle primitives for Reaper.

The module provides explicit, bounded operations:
- integrity-checked repository checkpoints;
- reviewable reflash plans with stale-base protection and rollback;
- a read-only local repository registry and selected-file propagation plans.

It does not execute repository code, follow symlinks, delete source files, or
silently synchronize repositories. Applying a reflash is always an explicit
caller action.
"""
from __future__ import annotations

import argparse
import base64
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import re
import shutil
import stat
import sys
import tempfile
from typing import Any, Mapping, Sequence
import uuid


CHECKPOINT_SCHEMA = "reaper.clife.checkpoint.v1"
REFLASH_SCHEMA = "reaper.clife.reflash-plan.v1"
NETWORK_SCHEMA = "reaper.clife.repository-network.v1"

_EXCLUDED_DIRS = {
    ".git", ".venv", "venv", "node_modules", "__pycache__",
    ".pytest_cache", ".mypy_cache", ".ruff_cache",
}
_MAX_FILES = 100_000
_MAX_FILE_BYTES = 16 * 1024 * 1024
_MAX_TOTAL_BYTES = 512 * 1024 * 1024
_MAX_PLAN_BYTES = 64 * 1024 * 1024


class CLifeError(ValueError):
    """Raised when a CLife operation cannot be completed safely."""


@dataclass(frozen=True, slots=True)
class CheckpointReport:
    path: str
    files: int
    total_bytes: int
    manifest_sha256: str


@dataclass(frozen=True, slots=True)
class CheckpointVerification:
    valid: bool
    files: int
    total_bytes: int
    errors: tuple[str, ...]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True, slots=True)
class ReflashChange:
    path: str
    base_sha256: str | None
    content_base64: str
    content_sha256: str
    mode: int

    def content(self) -> bytes:
        try:
            value = base64.b64decode(self.content_base64, validate=True)
        except (ValueError, base64.binascii.Error) as error:
            raise CLifeError(f"invalid base64 content for {self.path!r}") from error
        if _sha256(value) != self.content_sha256:
            raise CLifeError(f"content checksum mismatch for {self.path!r}")
        return value


@dataclass(frozen=True, slots=True)
class ReflashPlan:
    root: str
    changes: tuple[ReflashChange, ...]
    schema: str = REFLASH_SCHEMA

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema": self.schema,
            "root": self.root,
            "changes": [asdict(item) for item in self.changes],
        }

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), ensure_ascii=False, indent=2) + "\n"

    @classmethod
    def from_json(cls, source: str) -> "ReflashPlan":
        try:
            payload = json.loads(source)
        except json.JSONDecodeError as error:
            raise CLifeError(f"invalid reflash plan JSON: {error}") from error
        if not isinstance(payload, dict) or payload.get("schema") != REFLASH_SCHEMA:
            raise CLifeError("unsupported reflash plan schema")
        root = payload.get("root")
        raw_changes = payload.get("changes")
        if not isinstance(root, str) or not root or not isinstance(raw_changes, list):
            raise CLifeError("reflash plan requires a root and changes array")
        if not raw_changes or len(raw_changes) > _MAX_FILES:
            raise CLifeError("reflash plan must contain between 1 and 100000 changes")
        changes: list[ReflashChange] = []
        seen: set[str] = set()
        total = 0
        for raw in raw_changes:
            if not isinstance(raw, dict):
                raise CLifeError("each reflash change must be an object")
            path = _normalise_relative(raw.get("path"))
            if path in seen:
                raise CLifeError(f"duplicate reflash path: {path}")
            seen.add(path)
            base_hash = raw.get("base_sha256")
            if base_hash is not None and not _is_sha256(base_hash):
                raise CLifeError(f"invalid base checksum for {path}")
            content_hash = raw.get("content_sha256")
            if not _is_sha256(content_hash):
                raise CLifeError(f"invalid content checksum for {path}")
            encoded = raw.get("content_base64")
            if not isinstance(encoded, str):
                raise CLifeError(f"missing content for {path}")
            try:
                decoded = base64.b64decode(encoded, validate=True)
            except (ValueError, base64.binascii.Error) as error:
                raise CLifeError(f"invalid base64 content for {path}") from error
            if len(decoded) > _MAX_FILE_BYTES or _sha256(decoded) != content_hash:
                raise CLifeError(f"content size or checksum is invalid for {path}")
            total += len(decoded)
            if total > _MAX_PLAN_BYTES:
                raise CLifeError("reflash plan exceeds the 64 MiB content limit")
            mode = raw.get("mode", 0o644)
            if not isinstance(mode, int) or isinstance(mode, bool) or mode < 0 or mode > 0o777:
                raise CLifeError(f"invalid file mode for {path}")
            changes.append(ReflashChange(path, base_hash, encoded, content_hash, mode))
        return cls(str(Path(root).resolve()), tuple(changes))


@dataclass(frozen=True, slots=True)
class ReflashResult:
    checkpoint: str
    changed_paths: tuple[str, ...]
    rolled_back: bool = False

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True, slots=True)
class RepositoryRegistration:
    name: str
    path: str
    fingerprint: str
    files: int


class RepositoryNetwork:
    """Read-only local registry; propagation is returned as a guarded plan."""

    def __init__(self) -> None:
        self._repositories: dict[str, RepositoryRegistration] = {}

    def register(self, name: str, root: str | Path) -> RepositoryRegistration:
        if not isinstance(name, str) or not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_.-]{0,63}", name):
            raise CLifeError("repository name must be 1-64 safe ASCII characters")
        if name in self._repositories:
            raise CLifeError(f"repository {name!r} is already registered")
        directory = _repository_root(root)
        fingerprint, count = _fingerprint(directory)
        registration = RepositoryRegistration(name, str(directory), fingerprint, count)
        self._repositories[name] = registration
        return registration

    def list(self) -> tuple[RepositoryRegistration, ...]:
        return tuple(self._repositories[key] for key in sorted(self._repositories))

    def audit_all(self) -> dict[str, Any]:
        results: list[dict[str, Any]] = []
        for registration in self.list():
            current, count = _fingerprint(Path(registration.path))
            results.append({
                "name": registration.name,
                "path": registration.path,
                "registered_fingerprint": registration.fingerprint,
                "current_fingerprint": current,
                "files": count,
                "changed_since_registration": current != registration.fingerprint,
                "status": "changed" if current != registration.fingerprint else "clear",
            })
        return {"schema": NETWORK_SCHEMA, "repositories": results}

    def plan_propagation(
        self, source_name: str, destination_name: str, paths: Sequence[str]
    ) -> ReflashPlan:
        if source_name == destination_name:
            raise CLifeError("source and destination repositories must differ")
        try:
            source = Path(self._repositories[source_name].path)
            destination = Path(self._repositories[destination_name].path)
        except KeyError as error:
            raise CLifeError(f"unknown repository: {error.args[0]}") from error
        if not paths:
            raise CLifeError("propagation requires at least one explicit file path")
        updates: dict[str, bytes] = {}
        for raw_path in paths:
            relative = _normalise_relative(raw_path)
            source_file = _safe_target(source, relative)
            if not source_file.is_file():
                raise CLifeError(f"source file does not exist: {relative}")
            content = source_file.read_bytes()
            if len(content) > _MAX_FILE_BYTES:
                raise CLifeError(f"source file exceeds the 16 MiB limit: {relative}")
            updates[relative] = content
        return plan_reflash(destination, updates)


def _sha256(content: bytes) -> str:
    return hashlib.sha256(content).hexdigest()


def _is_sha256(value: Any) -> bool:
    return isinstance(value, str) and re.fullmatch(r"[0-9a-f]{64}", value) is not None


def _repository_root(value: str | Path) -> Path:
    root = Path(value).expanduser().resolve()
    if not root.is_dir():
        raise CLifeError(f"repository directory does not exist: {root}")
    return root


def _normalise_relative(value: Any) -> str:
    if not isinstance(value, str) or not value or "\x00" in value:
        raise CLifeError("file path must be a non-empty string")
    portable = value.replace("\\", "/")
    if portable.startswith("/") or re.match(r"^[A-Za-z]:", portable):
        raise CLifeError(f"absolute paths are not allowed: {value!r}")
    parts = portable.split("/")
    if any(part in {"", ".", ".."} for part in parts):
        raise CLifeError(f"unsafe relative path: {value!r}")
    if any(":" in part or part.endswith((" ", ".")) for part in parts):
        raise CLifeError(f"non-portable path component: {value!r}")
    reserved = {"CON", "PRN", "AUX", "NUL", *(f"COM{i}" for i in range(1, 10)), *(f"LPT{i}" for i in range(1, 10))}
    if any(part.split(".", 1)[0].upper() in reserved for part in parts):
        raise CLifeError(f"reserved path component: {value!r}")
    return str(PurePosixPath(*parts))


def _safe_target(root: Path, relative: str) -> Path:
    relative = _normalise_relative(relative)
    candidate = root.joinpath(*PurePosixPath(relative).parts)
    current = root
    for part in PurePosixPath(relative).parts:
        current = current / part
        if current.is_symlink():
            raise CLifeError(f"symlink paths are not supported: {relative}")
    try:
        candidate.resolve(strict=False).relative_to(root)
    except ValueError as error:
        raise CLifeError(f"path escapes repository root: {relative}") from error
    return candidate


def _walk_files(
    root: Path, *, excluded_paths: set[Path] | None = None,
    max_files: int = _MAX_FILES,
) -> list[tuple[str, Path]]:
    excluded = {item.resolve() for item in (excluded_paths or set())}
    files: list[tuple[str, Path]] = []
    for current, directories, filenames in os.walk(root, topdown=True, followlinks=False):
        current_path = Path(current)
        kept: list[str] = []
        for name in sorted(directories):
            directory = current_path / name
            relative_dir = directory.relative_to(root).as_posix()
            if (name in _EXCLUDED_DIRS
                    or relative_dir == ".reaper/checkpoints"
                    or relative_dir.startswith(".reaper/checkpoints/")
                    or directory.resolve() in excluded):
                continue
            if directory.is_symlink():
                raise CLifeError(f"repository contains a symlink directory: {relative_dir}")
            if any(item == directory.resolve() or item in directory.resolve().parents for item in excluded):
                continue
            kept.append(name)
        directories[:] = kept
        for name in sorted(filenames):
            path = current_path / name
            relative = path.relative_to(root).as_posix()
            if path.resolve() in excluded:
                continue
            if path.is_symlink():
                raise CLifeError(f"repository contains a symlink file: {relative}")
            if not path.is_file():
                continue
            files.append((relative, path))
            if len(files) > max_files:
                raise CLifeError(f"repository exceeds the {max_files} file limit")
    files.sort(key=lambda item: item[0])
    return files


def _secure_directory(path: Path) -> None:
    absolute = path.absolute()
    probe = Path(absolute.anchor)
    for part in absolute.parts[1:]:
        probe = probe / part
        if probe.exists() and probe.is_symlink():
            raise CLifeError(f"symlink directory is not allowed: {probe}")


def _atomic_write(path: Path, content: bytes, mode: int = 0o644) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    _secure_directory(path.parent)
    descriptor, temporary = tempfile.mkstemp(prefix=".reaper-clife-", dir=path.parent)
    try:
        with os.fdopen(descriptor, "wb") as stream:
            stream.write(content)
            stream.flush()
            os.fsync(stream.fileno())
        os.chmod(temporary, mode & 0o777)
        os.replace(temporary, path)
    except Exception:
        try:
            os.unlink(temporary)
        except OSError:
            pass
        raise


def create_checkpoint(
    root: str | Path, store: str | Path | None = None, *,
    max_files: int = _MAX_FILES, max_file_bytes: int = _MAX_FILE_BYTES,
    max_total_bytes: int = _MAX_TOTAL_BYTES,
) -> CheckpointReport:
    """Create a content-verified snapshot without following symlinks."""
    directory = _repository_root(root)
    destination_store = Path(store).expanduser().absolute() if store else directory / ".reaper" / "checkpoints"
    _secure_directory(destination_store.parent)
    if destination_store.resolve(strict=False) == directory:
        raise CLifeError("checkpoint store cannot be the repository root")
    excluded = {destination_store.resolve(strict=False)}
    entries = _walk_files(directory, excluded_paths=excluded, max_files=max_files)
    checkpoint_id = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ") + "-" + uuid.uuid4().hex[:10]
    destination_store.mkdir(parents=True, exist_ok=True)
    _secure_directory(destination_store)
    temporary = Path(tempfile.mkdtemp(prefix=".checkpoint-", dir=destination_store))
    total = 0
    records: list[dict[str, Any]] = []
    try:
        files_root = temporary / "files"
        for relative, source in entries:
            data = source.read_bytes()
            if len(data) > max_file_bytes:
                raise CLifeError(f"file exceeds checkpoint size limit: {relative}")
            total += len(data)
            if total > max_total_bytes:
                raise CLifeError("repository exceeds checkpoint total-size limit")
            mode = stat.S_IMODE(source.stat().st_mode) & 0o777
            target = files_root.joinpath(*PurePosixPath(relative).parts)
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(data)
            os.chmod(target, mode)
            records.append({
                "path": relative, "size": len(data), "sha256": _sha256(data), "mode": mode,
            })
        manifest = {
            "schema": CHECKPOINT_SCHEMA,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "root_name": directory.name,
            "files": records,
            "file_count": len(records),
            "total_bytes": total,
        }
        manifest_bytes = (json.dumps(manifest, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n").encode("utf-8")
        manifest_hash = _sha256(manifest_bytes)
        (temporary / "manifest.json").write_bytes(manifest_bytes)
        (temporary / "manifest.sha256").write_text(manifest_hash + "\n", encoding="ascii")
        final = destination_store / checkpoint_id
        os.replace(temporary, final)
        return CheckpointReport(str(final), len(records), total, manifest_hash)
    except Exception:
        shutil.rmtree(temporary, ignore_errors=True)
        raise


def verify_checkpoint(checkpoint: str | Path) -> CheckpointVerification:
    """Verify manifest integrity, path safety, file sizes and every content hash."""
    directory = Path(checkpoint).expanduser().absolute()
    errors: list[str] = []
    total = 0
    records: list[dict[str, Any]] = []
    try:
        if directory.is_symlink() or not directory.is_dir():
            raise CLifeError("checkpoint directory is missing or is a symlink")
        _secure_directory(directory)
        manifest_path = directory / "manifest.json"
        digest_path = directory / "manifest.sha256"
        if manifest_path.is_symlink() or digest_path.is_symlink():
            raise CLifeError("checkpoint manifest files must not be symlinks")
        raw = manifest_path.read_bytes()
        expected_manifest_hash = digest_path.read_text(encoding="ascii").strip()
        if not _is_sha256(expected_manifest_hash) or _sha256(raw) != expected_manifest_hash:
            raise CLifeError("checkpoint manifest checksum mismatch")
        manifest = json.loads(raw.decode("utf-8"))
        if not isinstance(manifest, dict) or manifest.get("schema") != CHECKPOINT_SCHEMA:
            raise CLifeError("unsupported checkpoint schema")
        records = manifest.get("files")
        if not isinstance(records, list) or len(records) > _MAX_FILES:
            raise CLifeError("invalid checkpoint file list")
        seen: set[str] = set()
        expected_paths: set[str] = set()
        for record in records:
            if not isinstance(record, dict):
                errors.append("invalid file record")
                continue
            try:
                relative = _normalise_relative(record.get("path"))
                if relative in seen:
                    raise CLifeError(f"duplicate manifest path: {relative}")
                seen.add(relative)
                expected_paths.add(relative)
                size = record.get("size")
                digest = record.get("sha256")
                mode = record.get("mode")
                if not isinstance(size, int) or isinstance(size, bool) or size < 0 or size > _MAX_FILE_BYTES:
                    raise CLifeError(f"invalid file size: {relative}")
                if not _is_sha256(digest):
                    raise CLifeError(f"invalid content hash: {relative}")
                if not isinstance(mode, int) or isinstance(mode, bool) or mode < 0 or mode > 0o777:
                    raise CLifeError(f"invalid file mode: {relative}")
                target = _safe_target(directory / "files", relative)
                if target.is_symlink() or not target.is_file():
                    raise CLifeError(f"checkpoint file is missing or unsafe: {relative}")
                data = target.read_bytes()
                if len(data) != size or _sha256(data) != digest:
                    raise CLifeError(f"content verification failed: {relative}")
                total += len(data)
                if total > _MAX_TOTAL_BYTES:
                    raise CLifeError("checkpoint exceeds total-size limit")
            except (CLifeError, OSError) as error:
                errors.append(str(error))
        if manifest.get("file_count") != len(records) or manifest.get("total_bytes") != total:
            errors.append("manifest totals do not match verified files")
        actual_paths: set[str] = set()
        files_root = directory / "files"
        if files_root.exists():
            for current, directories, filenames in os.walk(files_root, followlinks=False):
                for name in directories:
                    if (Path(current) / name).is_symlink():
                        errors.append(f"symlink in checkpoint: {(Path(current) / name).relative_to(files_root)}")
                for name in filenames:
                    path = Path(current) / name
                    if path.is_symlink():
                        errors.append(f"symlink in checkpoint: {path.relative_to(files_root)}")
                    else:
                        actual_paths.add(path.relative_to(files_root).as_posix())
        if actual_paths != expected_paths:
            errors.append("checkpoint contains missing or unexpected files")
    except (CLifeError, OSError, UnicodeError, json.JSONDecodeError) as error:
        errors.append(str(error))
    return CheckpointVerification(not errors, len(records), total, tuple(errors))


def restore_checkpoint(checkpoint: str | Path, destination: str | Path) -> Path:
    """Restore into a new or empty destination; never overwrite a populated tree."""
    verification = verify_checkpoint(checkpoint)
    if not verification.valid:
        raise CLifeError("checkpoint verification failed: " + "; ".join(verification.errors))
    source = Path(checkpoint).expanduser().absolute()
    target = Path(destination).expanduser().absolute()
    if target == source or target == source / "files":
        raise CLifeError("restore destination must differ from the checkpoint")
    _secure_directory(target.parent)
    target.parent.mkdir(parents=True, exist_ok=True)
    if target.is_symlink():
        raise CLifeError("restore destination must not be a symlink")
    if target.exists() and (not target.is_dir() or any(target.iterdir())):
        raise CLifeError("restore destination must not exist or must be empty")
    manifest = json.loads((source / "manifest.json").read_text(encoding="utf-8"))
    temporary = Path(tempfile.mkdtemp(prefix=".reaper-restore-", dir=target.parent))
    try:
        for record in manifest["files"]:
            relative = _normalise_relative(record["path"])
            from_path = _safe_target(source / "files", relative)
            to_path = temporary.joinpath(*PurePosixPath(relative).parts)
            to_path.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(from_path, to_path)
            os.chmod(to_path, record["mode"] & 0o777)
        if target.exists():
            target.rmdir()
        os.replace(temporary, target)
        return target
    except Exception:
        shutil.rmtree(temporary, ignore_errors=True)
        raise


def plan_reflash(root: str | Path, updates: Mapping[str, str | bytes]) -> ReflashPlan:
    """Create a non-mutating, hash-guarded plan for adding or replacing files."""
    directory = _repository_root(root)
    if not isinstance(updates, Mapping) or not updates or len(updates) > _MAX_FILES:
        raise CLifeError("updates must be a non-empty mapping of relative paths to text or bytes")
    changes: list[ReflashChange] = []
    seen: set[str] = set()
    total = 0
    for raw_path, value in updates.items():
        relative = _normalise_relative(raw_path)
        if relative in seen:
            raise CLifeError(f"duplicate reflash path: {relative}")
        seen.add(relative)
        if not isinstance(value, (str, bytes)):
            raise CLifeError(f"reflash content must be str or bytes: {relative}")
        content = value.encode("utf-8") if isinstance(value, str) else value
        if len(content) > _MAX_FILE_BYTES:
            raise CLifeError(f"reflash file exceeds the 16 MiB limit: {relative}")
        total += len(content)
        if total > _MAX_PLAN_BYTES:
            raise CLifeError("reflash plan exceeds the 64 MiB content limit")
        target = _safe_target(directory, relative)
        if target.exists() and not target.is_file():
            raise CLifeError(f"reflash target is not a regular file: {relative}")
        before = target.read_bytes() if target.exists() else None
        if before is not None and len(before) > _MAX_FILE_BYTES:
            raise CLifeError(f"existing target exceeds the 16 MiB limit: {relative}")
        mode = stat.S_IMODE(target.stat().st_mode) & 0o777 if target.exists() else 0o644
        changes.append(ReflashChange(
            relative,
            _sha256(before) if before is not None else None,
            base64.b64encode(content).decode("ascii"),
            _sha256(content),
            mode,
        ))
    return ReflashPlan(str(directory), tuple(changes))


def apply_reflash_plan(
    root: str | Path, plan: ReflashPlan, *, checkpoint_store: str | Path | None = None
) -> ReflashResult:
    """Apply a reviewed plan after checking every base hash; rollback on write failure."""
    directory = _repository_root(root)
    if not isinstance(plan, ReflashPlan) or plan.schema != REFLASH_SCHEMA:
        raise CLifeError("unsupported reflash plan")
    if Path(plan.root).resolve() != directory:
        raise CLifeError("reflash plan belongs to a different repository root")
    if not plan.changes:
        raise CLifeError("reflash plan contains no changes")
    total = 0
    prepared: list[tuple[ReflashChange, Path, bytes, bytes | None, int]] = []
    for change in plan.changes:
        relative = _normalise_relative(change.path)
        content = change.content()
        total += len(content)
        if total > _MAX_PLAN_BYTES:
            raise CLifeError("reflash plan exceeds the 64 MiB content limit")
        target = _safe_target(directory, relative)
        if target.exists() and not target.is_file():
            raise CLifeError(f"reflash target is not a regular file: {relative}")
        current = target.read_bytes() if target.exists() else None
        current_hash = _sha256(current) if current is not None else None
        if current_hash != change.base_sha256:
            raise CLifeError(f"stale reflash plan; base content changed: {relative}")
        if current is not None and len(current) > _MAX_FILE_BYTES:
            raise CLifeError(f"existing target exceeds the 16 MiB limit: {relative}")
        mode = stat.S_IMODE(target.stat().st_mode) & 0o777 if current is not None else change.mode
        prepared.append((change, target, content, current, mode))

    snapshot = create_checkpoint(directory, checkpoint_store)
    applied: list[tuple[Path, bytes | None, int]] = []
    try:
        for change, target, content, previous, mode in prepared:
            current = target.read_bytes() if target.exists() else None
            current_hash = _sha256(current) if current is not None else None
            if current_hash != change.base_sha256:
                raise CLifeError(f"stale reflash plan during apply: {change.path}")
            _atomic_write(target, content, mode)
            applied.append((target, previous, mode))
    except Exception as error:
        rollback_errors: list[str] = []
        for target, previous, mode in reversed(applied):
            try:
                if previous is None:
                    target.unlink(missing_ok=True)
                else:
                    _atomic_write(target, previous, mode)
            except OSError as rollback_error:
                rollback_errors.append(f"{target}: {rollback_error}")
        if rollback_errors:
            raise CLifeError(
                f"reflash failed ({error}); rollback incomplete; checkpoint retained at "
                f"{snapshot.path}; " + "; ".join(rollback_errors)
            ) from error
        raise CLifeError(
            f"reflash failed and applied files were rolled back; checkpoint retained at {snapshot.path}: {error}"
        ) from error

    return ReflashResult(snapshot.path, tuple(change.path for change in plan.changes))


def _fingerprint(root: Path) -> tuple[str, int]:
    digest = hashlib.sha256()
    files = _walk_files(root)
    total = 0
    for relative, path in files:
        data = path.read_bytes()
        if len(data) > _MAX_FILE_BYTES:
            raise CLifeError(f"repository file exceeds fingerprint size limit: {relative}")
        total += len(data)
        if total > _MAX_TOTAL_BYTES:
            raise CLifeError("repository exceeds fingerprint total-size limit")
        digest.update(relative.encode("utf-8"))
        digest.update(b"\0")
        digest.update(_sha256(data).encode("ascii"))
        digest.update(b"\n")
    return digest.hexdigest(), len(files)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="reaper clife", description="CLife checkpoint, reflash and repository tools")
    commands = parser.add_subparsers(dest="command", required=True)

    checkpoint_parser = commands.add_parser("checkpoint", help="create a verified repository checkpoint")
    checkpoint_parser.add_argument("root")
    checkpoint_parser.add_argument("--store")

    verify_parser = commands.add_parser("verify", help="verify a checkpoint and all file hashes")
    verify_parser.add_argument("checkpoint")

    restore_parser = commands.add_parser("restore", help="restore into a new or empty directory")
    restore_parser.add_argument("checkpoint")
    restore_parser.add_argument("destination")

    plan_parser = commands.add_parser("plan", help="create a non-mutating reflash plan from a JSON object")
    plan_parser.add_argument("root")
    plan_parser.add_argument("updates_json", help="JSON object mapping relative paths to UTF-8 strings")
    plan_parser.add_argument("--output", required=True)

    apply_parser = commands.add_parser("apply", help="apply a reflash plan after base-hash validation")
    apply_parser.add_argument("root")
    apply_parser.add_argument("plan_json")
    apply_parser.add_argument("--checkpoint-store")

    audit_parser = commands.add_parser("audit", help="fingerprint multiple local repositories without modifying them")
    audit_parser.add_argument("roots", nargs="+", help="local repository directories")

    args = parser.parse_args(argv)
    try:
        if args.command == "checkpoint":
            result = create_checkpoint(args.root, args.store)
            print(json.dumps(asdict(result), ensure_ascii=False, indent=2))
        elif args.command == "verify":
            result = verify_checkpoint(args.checkpoint)
            print(json.dumps(result.to_dict(), ensure_ascii=False, indent=2))
            return 0 if result.valid else 1
        elif args.command == "restore":
            print(json.dumps({"restored_to": str(restore_checkpoint(args.checkpoint, args.destination))}, ensure_ascii=False))
        elif args.command == "plan":
            raw = json.loads(Path(args.updates_json).read_text(encoding="utf-8"))
            if not isinstance(raw, dict):
                raise CLifeError("updates JSON must be an object")
            plan = plan_reflash(args.root, raw)
            output = Path(args.output)
            _atomic_write(output, plan.to_json().encode("utf-8"))
            print(json.dumps({"plan": str(output), "changes": len(plan.changes)}, ensure_ascii=False))
        elif args.command == "apply":
            plan = ReflashPlan.from_json(Path(args.plan_json).read_text(encoding="utf-8"))
            result = apply_reflash_plan(args.root, plan, checkpoint_store=args.checkpoint_store)
            print(json.dumps(result.to_dict(), ensure_ascii=False, indent=2))
        elif args.command == "audit":
            network = RepositoryNetwork()
            for index, root in enumerate(args.roots, start=1):
                network.register(f"repo-{index}", root)
            print(json.dumps(network.audit_all(), ensure_ascii=False, indent=2))
        return 0
    except (CLifeError, OSError, UnicodeError, json.JSONDecodeError) as error:
        print(f"reaper clife: {error}", file=sys.stderr)
        return 2
