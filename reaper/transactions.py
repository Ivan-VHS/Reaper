"""Bounded, rollback-capable state transitions for Reaper hosts.

The module operates on JSON-compatible in-memory state only. It does not flash
firmware, load executable code, or modify operating-system resources.
"""
from __future__ import annotations

import asyncio
import copy
import hashlib
import json
import threading
from dataclasses import dataclass
from typing import Any, Callable, Iterable


class TransactionError(RuntimeError):
    """Base error raised by a transactional operation."""


class TransactionConflict(TransactionError):
    """The committed generation changed since the transaction was opened."""


class TransactionLimitError(TransactionError):
    """A staged payload exceeded its configured bounds."""


@dataclass(frozen=True, slots=True)
class Snapshot:
    generation: int
    schema_version: int
    checksum: str
    payload: Any


_MISSING = object()


def _canonical(value: Any, max_bytes: int) -> tuple[Any, str]:
    try:
        rendered = json.dumps(
            value, ensure_ascii=False, sort_keys=True, separators=(",", ":"),
            allow_nan=False,
        )
        encoded = rendered.encode("utf-8")
    except (TypeError, ValueError, RecursionError) as error:
        raise TransactionError(f"state must be finite JSON-compatible data: {error}") from error
    if len(encoded) > max_bytes:
        raise TransactionLimitError(f"state exceeds {max_bytes} bytes")
    return copy.deepcopy(value), hashlib.sha256(encoded).hexdigest()


class RuntimeTransaction:
    """Optimistic state transaction with integrity checks and explicit rollback."""

    def __init__(
        self,
        payload: Any,
        *,
        schema_version: int = 1,
        max_bytes: int = 4 * 1024 * 1024,
        event_sink: Callable[[str, int], None] | None = None,
    ) -> None:
        if isinstance(schema_version, bool) or not isinstance(schema_version, int) or schema_version < 1:
            raise ValueError("schema_version must be a positive whole number")
        if isinstance(max_bytes, bool) or not isinstance(max_bytes, int) or max_bytes < 1:
            raise ValueError("max_bytes must be a positive whole number")
        self._lock = threading.RLock()
        self._max_bytes = max_bytes
        self._event_sink = event_sink
        self._generation = 0
        self._schema_version = schema_version
        self._committed_schema_version = schema_version
        self._committed, self._checksum = _canonical(payload, max_bytes)
        self._staged = copy.deepcopy(self._committed)
        self._staged_checksum = self._checksum
        self._binding: Any = None
        self._failed: str | None = None

    @property
    def generation(self) -> int:
        with self._lock:
            return self._generation

    @property
    def schema_version(self) -> int:
        with self._lock:
            return self._schema_version

    @property
    def staged(self) -> Any:
        with self._lock:
            return copy.deepcopy(self._staged)

    def _event(self, name: str) -> None:
        if self._event_sink is not None:
            self._event_sink(name, self._generation)

    def _stage(self, value: Any) -> None:
        staged, digest = _canonical(value, self._max_bytes)
        self._staged = staged
        self._staged_checksum = digest
        self._failed = None

    def patch(self, path: Iterable[str | int], value: Any = _MISSING) -> RuntimeTransaction:
        """Replace (or delete) a nested mapping/list value without mutating the source."""
        parts = tuple(path)
        if not parts:
            raise TransactionError("patch path cannot be empty")
        with self._lock:
            candidate = copy.deepcopy(self._staged)
            parent = candidate
            for part in parts[:-1]:
                if isinstance(part, bool) or not isinstance(part, (str, int)):
                    raise TransactionError("patch path items must be string keys or integer indexes")
                try:
                    parent = parent[part]
                except (KeyError, IndexError, TypeError) as error:
                    raise TransactionError(f"patch path does not exist at {part!r}") from error
            leaf = parts[-1]
            if isinstance(parent, dict) and isinstance(leaf, str):
                if value is _MISSING:
                    if leaf not in parent:
                        raise TransactionError(f"patch key does not exist: {leaf}")
                    del parent[leaf]
                else:
                    parent[leaf] = value
            elif isinstance(parent, list) and isinstance(leaf, int) and not isinstance(leaf, bool):
                if leaf < 0 or leaf >= len(parent):
                    raise TransactionError("patch list index is outside the current state")
                if value is _MISSING:
                    del parent[leaf]
                else:
                    parent[leaf] = value
            else:
                raise TransactionError("patch target must be a mapping key or existing list index")
            self._stage(candidate)
            self._event("PATCH_STAGED")
            return self

    def rebind(self, name: str, value: Any) -> RuntimeTransaction:
        if not isinstance(name, str) or not name or len(name) > 128:
            raise TransactionError("binding name must contain 1..128 characters")
        with self._lock:
            if not isinstance(self._staged, dict):
                raise TransactionError("rebind requires mapping state")
            candidate = copy.deepcopy(self._staged)
            candidate[name] = value
            self._stage(candidate)
            self._binding = name
            self._event("REBIND_STAGED")
            return self

    def remap(self, mapping: dict[str, str]) -> RuntimeTransaction:
        if not isinstance(mapping, dict) or not all(
            isinstance(old, str) and old and isinstance(new, str) and new for old, new in mapping.items()
        ):
            raise TransactionError("remap requires a non-empty string-to-string key map")
        with self._lock:
            if not isinstance(self._staged, dict):
                raise TransactionError("remap requires mapping state")
            if len(set(mapping.values())) != len(mapping):
                raise TransactionError("remap destinations must be unique")
            missing = set(mapping) - self._staged.keys()
            if missing:
                raise TransactionError(f"remap source key is missing: {sorted(missing)[0]}")
            candidate = copy.deepcopy(self._staged)
            moved = {new: candidate[old] for old, new in mapping.items()}
            for old in mapping:
                del candidate[old]
            for new, item in moved.items():
                if new in candidate:
                    raise TransactionError(f"remap destination already exists: {new}")
                candidate[new] = item
            self._stage(candidate)
            self._event("REMAP_STAGED")
            return self

    def hot_swap(self, replacement: Any) -> RuntimeTransaction:
        with self._lock:
            self._stage(replacement)
            self._event("HOT_SWAP_STAGED")
            return self

    def migrate(self, target_schema: int, transform: Callable[[Any], Any]) -> RuntimeTransaction:
        if isinstance(target_schema, bool) or not isinstance(target_schema, int):
            raise TransactionError("target schema must be a whole number")
        if not callable(transform):
            raise TransactionError("migration transform must be callable")
        with self._lock:
            if target_schema <= self._schema_version:
                raise TransactionError("migrations must move to a higher schema version")
            candidate = transform(copy.deepcopy(self._staged))
            staged, digest = _canonical(candidate, self._max_bytes)
            self._staged = staged
            self._staged_checksum = digest
            self._schema_version = target_schema
            self._failed = None
            self._event("MIGRATE_STAGED")
            return self

    def validate(self) -> bool:
        with self._lock:
            _, digest = _canonical(self._staged, self._max_bytes)
            return digest == self._staged_checksum

    def _commit(self, expected_generation: int | None, event: str) -> Snapshot:
        with self._lock:
            expected = self._generation if expected_generation is None else expected_generation
            if expected != self._generation:
                raise TransactionConflict(
                    f"generation conflict: expected {expected}, current {self._generation}"
                )
            _, digest = _canonical(self._staged, self._max_bytes)
            if digest != self._staged_checksum:
                raise TransactionError("staged state checksum mismatch")
            self._committed = copy.deepcopy(self._staged)
            self._checksum = digest
            self._committed_schema_version = self._schema_version
            self._generation += 1
            self._event(event)
            return self.snapshot()

    def flash(self, expected_generation: int | None = None) -> Snapshot:
        return self._commit(expected_generation, "FLASH_COMMITTED")

    def reflash(self, expected_generation: int | None = None) -> Snapshot:
        return self._commit(expected_generation, "REFLASH_COMMITTED")

    def sync(self) -> Snapshot:
        return self._commit(None, "SYNC_COMMITTED")

    async def async_flash(self, expected_generation: int | None = None) -> Snapshot:
        """Run the same bounded commit operation off the event loop."""
        return await asyncio.to_thread(self.flash, expected_generation)

    @staticmethod
    async def await_result(task: "asyncio.Task[Snapshot] | asyncio.Future[Snapshot]") -> Snapshot:
        return await task

    def rollback(self) -> Snapshot:
        with self._lock:
            self._staged = copy.deepcopy(self._committed)
            self._staged_checksum = self._checksum
            self._schema_version = self._committed_schema_version
            self._failed = None
            self._event("ROLLBACK")
            return self.snapshot()

    def snapshot(self) -> Snapshot:
        with self._lock:
            return Snapshot(
                generation=self._generation,
                schema_version=self._committed_schema_version,
                checksum=self._checksum,
                payload=copy.deepcopy(self._committed),
            )

    def emit(self, name: str) -> None:
        if not isinstance(name, str) or not name or len(name) > 128:
            raise TransactionError("event name must contain 1..128 characters")
        with self._lock:
            self._event(name)

    def yield_value(self, value: Any) -> Any:
        self.emit("YIELD_CHECKPOINT")
        return value

    @staticmethod
    def return_value(value: Any = None) -> Any:
        return value

    @staticmethod
    def throw(message: str) -> None:
        raise TransactionError(str(message))

    def panic(self, message: str) -> None:
        with self._lock:
            self._failed = str(message)[:512]
            self._event("PANIC_RECORDED")
        raise TransactionError(f"panic: {self._failed}")

    @staticmethod
    def assert_condition(condition: Any, message: str = "assertion failed") -> None:
        if not condition:
            raise TransactionError(message)

    @staticmethod
    def catch(operation: Callable[..., Any], *args: Any, **kwargs: Any) -> tuple[Any, str | None]:
        try:
            return operation(*args, **kwargs), None
        except TransactionError as error:
            return None, str(error)
