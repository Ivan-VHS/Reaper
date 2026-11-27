"""Live, local-first Reaper foundation attachments (MAZA)."""
from __future__ import annotations

import hashlib
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .errors import ReaperRuntimeError


class MazaError(ReaperRuntimeError):
    """A MAZA foundation could not be attached or refreshed safely."""


@dataclass(slots=True)
class MazaLink:
    alias: str
    specifier: str
    importer: str
    path: Path
    namespace: dict[str, Any]
    environment: Any
    signature: tuple[int, int]
    sha256: str
    poll_interval_ms: int
    revision: int = 1
    state: str = "active"
    last_error: str | None = None
    last_checked_utc: str | None = None
    last_updated_utc: str | None = None
    next_poll_ns: int = 0


class MazaManager:
    """Keeps explicit .rpr foundations live for the lifetime of an interpreter."""

    MIN_POLL_INTERVAL_MS = 50
    MAX_POLL_INTERVAL_MS = 60_000
    MAX_LINKS = 128

    def __init__(self, interpreter: Any, poll_interval_ms: int = 1_000) -> None:
        if (
            isinstance(poll_interval_ms, bool)
            or not isinstance(poll_interval_ms, int)
            or not self.MIN_POLL_INTERVAL_MS <= poll_interval_ms <= self.MAX_POLL_INTERVAL_MS
        ):
            raise ValueError(
                f"MAZA poll interval must be {self.MIN_POLL_INTERVAL_MS}..{self.MAX_POLL_INTERVAL_MS} ms"
            )
        self.interpreter = interpreter
        self.poll_interval_ms = poll_interval_ms
        self._links: dict[str, MazaLink] = {}
        self._polling = False

    @staticmethod
    def _utc_now() -> str:
        return datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")

    def _source_path(self, specifier: str, importer: str) -> Path:
        if not isinstance(specifier, str) or not specifier.strip():
            raise MazaError("MAZA source path must be non-empty text")
        if "://" in specifier:
            raise MazaError("MAZA accepts local .rpr paths only; remote sources are not fetched")
        base = Path(importer).resolve().parent if not importer.startswith("<") else Path.cwd()
        candidate = Path(specifier)
        if not candidate.is_absolute():
            candidate = base / candidate
        if candidate.is_symlink():
            raise MazaError(f"MAZA refuses symbolic-link sources: {candidate}")
        try:
            target = self.interpreter.module_loader.resolve(str(candidate), importer)
        except Exception as error:
            raise MazaError(f"MAZA cannot resolve {specifier!r}: {error}") from error
        if candidate.is_symlink() or target.is_symlink():
            raise MazaError(f"MAZA refuses symbolic-link sources: {target}")
        return target

    def _fingerprint(self, path: Path) -> tuple[tuple[int, int], str]:
        if path.is_symlink() or not path.is_file():
            raise MazaError(f"MAZA source must be a regular, non-symlink file: {path}")
        try:
            before = path.stat()
            if before.st_size > self.interpreter.module_loader.max_source_bytes:
                raise MazaError(
                    f"MAZA source exceeds the {self.interpreter.module_loader.max_source_bytes}-byte limit"
                )
            raw = path.read_bytes()
            after = path.stat()
        except OSError as error:
            raise MazaError(f"MAZA cannot read {path}: {error}") from error
        signature = (after.st_mtime_ns, after.st_size)
        if (before.st_mtime_ns, before.st_size) != signature or len(raw) != after.st_size:
            raise MazaError(f"MAZA source changed while it was being inspected: {path}")
        return signature, hashlib.sha256(raw).hexdigest()

    @staticmethod
    def _has_binding(environment: Any, name: str) -> bool:
        scope = environment
        while scope is not None:
            if name in getattr(scope, "values", {}):
                return True
            scope = getattr(scope, "parent", None)
        return False

    def attach(self, specifier: str, alias: str, importer: str, environment: Any) -> dict[str, Any]:
        if not isinstance(alias, str) or not alias.isidentifier():
            raise MazaError("MAZA namespace alias must be a valid Reaper identifier")
        path = self._source_path(specifier, importer)
        current = self._links.get(alias)
        if current is not None:
            if current.path != path:
                raise MazaError(f"MAZA alias {alias!r} is already attached to {current.path}")
            if self._has_binding(environment, alias):
                if environment.get(alias) is not current.namespace:
                    raise MazaError(f"MAZA namespace alias {alias!r} resolves to a different value")
            else:
                environment.define(alias, current.namespace)
            return current.namespace
        if len(self._links) >= self.MAX_LINKS:
            raise MazaError(f"MAZA active-link limit ({self.MAX_LINKS}) exceeded")
        if self._has_binding(environment, alias):
            raise MazaError(f"MAZA namespace {alias!r} is already defined")

        signature, digest = self._fingerprint(path)
        try:
            exports = self.interpreter.module_loader.load(str(path), importer, reload=True)
            after_signature, after_digest = self._fingerprint(path)
            if signature != after_signature or digest != after_digest:
                raise MazaError(f"MAZA source changed during attachment: {path}")
        except MazaError:
            raise
        except Exception as error:
            raise MazaError(f"MAZA could not attach {path}: {error}") from error

        namespace = dict(exports)
        environment.define(alias, namespace)
        now = time.monotonic_ns()
        timestamp = self._utc_now()
        self._links[alias] = MazaLink(
            alias=alias, specifier=str(path), importer=importer, path=path,
            namespace=namespace, environment=environment, signature=after_signature,
            sha256=after_digest, poll_interval_ms=self.poll_interval_ms,
            last_checked_utc=timestamp, last_updated_utc=timestamp,
            next_poll_ns=now + self.poll_interval_ms * 1_000_000,
        )
        return namespace

    def _refresh_link(self, link: MazaLink, *, force: bool) -> bool:
        if self._polling:
            return False
        self._polling = True
        link.last_checked_utc = self._utc_now()
        try:
            signature, digest = self._fingerprint(link.path)
            if not force and digest == link.sha256:
                link.signature = signature
                link.state = "active"
                link.last_error = None
                return True
            exports = self.interpreter.module_loader.load(link.specifier, link.importer, reload=True)
            after_signature, after_digest = self._fingerprint(link.path)
            if signature != after_signature or digest != after_digest:
                raise MazaError(f"MAZA source changed during refresh: {link.path}")
            link.namespace.clear()
            link.namespace.update(exports)
            link.signature = after_signature
            link.sha256 = after_digest
            link.revision += 1
            link.state = "active"
            link.last_error = None
            link.last_updated_utc = self._utc_now()
            return True
        except Exception as error:
            link.state = "degraded"
            link.last_error = str(error)[:1_024]
            return False
        finally:
            self._polling = False

    def poll(self) -> None:
        """Refresh due links at interpreter safe points without replacing last-good exports on failure."""
        if self._polling or not self._links:
            return
        now = time.monotonic_ns()
        for link in tuple(self._links.values()):
            if now < link.next_poll_ns:
                continue
            link.next_poll_ns = now + link.poll_interval_ms * 1_000_000
            self._refresh_link(link, force=False)

    def refresh(self, alias: str) -> dict[str, Any]:
        link = self._links.get(alias)
        if link is None:
            raise MazaError(f"MAZA namespace {alias!r} is not attached")
        self._refresh_link(link, force=True)
        return self.status(alias)

    def detach(self, alias: str) -> bool:
        link = self._links.pop(alias, None)
        if link is None:
            return False
        binding = getattr(link.environment, "values", {}).get(alias)
        if getattr(binding, "value", None) is link.namespace:
            del link.environment.values[alias]
        return True

    def status(self, alias: str) -> dict[str, Any]:
        link = self._links.get(alias)
        if link is None:
            raise MazaError(f"MAZA namespace {alias!r} is not attached")
        return self._status(link)

    @staticmethod
    def _status(link: MazaLink) -> dict[str, Any]:
        return {
            "alias": link.alias, "source": str(link.path), "state": link.state,
            "revision": link.revision, "sha256": link.sha256,
            "poll_interval_ms": link.poll_interval_ms,
            "last_checked_utc": link.last_checked_utc,
            "last_updated_utc": link.last_updated_utc, "last_error": link.last_error,
        }

    def links(self) -> list[dict[str, Any]]:
        return [self._status(self._links[name]) for name in sorted(self._links)]

    def roots(self) -> list[Any]:
        return [link.namespace for link in self._links.values()]

    def serve(self) -> None:
        """Keep a foreground supervisor alive and poll MAZA links until interrupted."""
        if not self._links:
            raise MazaError("MAZA supervisor requires at least one attached foundation")
        while self._links:
            self.poll()
            time.sleep(self.poll_interval_ms / 1_000)
