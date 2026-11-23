"""Durable, bounded idempotency storage for the optional local backend."""

from __future__ import annotations

import json
import os
import sqlite3
import tempfile
import threading
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any


class BackendStoreError(RuntimeError):
    """A storage operation failed or the database schema is incompatible."""


@dataclass(frozen=True, slots=True)
class IdempotencyClaim:
    state: str
    owner: str | None = None
    status_code: int | None = None
    response: dict[str, Any] | None = None


class BackendStore:
    """Single-process SQLite store with atomic claims and replayable responses.

    The database is deliberately local. A connection lock serializes access to
    the shared connection while the server's bounded worker pool keeps SQLite
    work off the event loop.
    """

    SCHEMA_VERSION = 1

    def __init__(
        self,
        path: str | os.PathLike[str],
        *,
        lease_seconds: int = 60,
        retention_seconds: int = 86_400,
        max_rows: int = 50_000,
    ) -> None:
        limits = (lease_seconds, retention_seconds, max_rows)
        if any(isinstance(value, bool) or not isinstance(value, int) or value < 1 for value in limits):
            raise ValueError("store limits must be positive integers")
        self.path = Path(path).expanduser()
        self.lease_seconds = lease_seconds
        self.retention_seconds = retention_seconds
        self.max_rows = max_rows
        self._lock = threading.RLock()
        self._closed = False

        try:
            self.path.parent.mkdir(parents=True, exist_ok=True)
            self._connection = sqlite3.connect(
                str(self.path),
                timeout=5.0,
                isolation_level=None,
                check_same_thread=False,
            )
            self._connection.row_factory = sqlite3.Row
            self._connection.execute("PRAGMA busy_timeout = 5000")
            self._connection.execute("PRAGMA foreign_keys = ON")
            self._connection.execute("PRAGMA journal_mode = WAL")
            self._connection.execute("PRAGMA synchronous = FULL")
            self._migrate()
        except Exception as error:
            connection = getattr(self, "_connection", None)
            if connection is not None:
                try:
                    connection.close()
                except sqlite3.Error:
                    pass
            if isinstance(error, BackendStoreError):
                raise
            if isinstance(error, (OSError, sqlite3.Error)):
                raise BackendStoreError(f"cannot open backend database: {error}") from error
            raise

    def _migrate(self) -> None:
        self._connection.execute("BEGIN EXCLUSIVE")
        try:
            # Re-read after acquiring the write lock: another process may have
            # completed the first migration while this connection was waiting.
            version = int(self._connection.execute("PRAGMA user_version").fetchone()[0])
            if version > self.SCHEMA_VERSION:
                raise BackendStoreError(
                    f"database schema {version} is newer than supported schema {self.SCHEMA_VERSION}"
                )
            if version < 1:
                self._connection.execute(
                    """
                    CREATE TABLE idempotency (
                        scope TEXT NOT NULL,
                        idempotency_key TEXT NOT NULL,
                        request_hash TEXT NOT NULL CHECK(length(request_hash) = 64),
                        state TEXT NOT NULL CHECK(state IN ('pending', 'complete')),
                        owner TEXT NOT NULL,
                        status_code INTEGER,
                        response_json TEXT,
                        updated_at REAL NOT NULL,
                        expires_at REAL NOT NULL,
                        PRIMARY KEY (scope, idempotency_key),
                        CHECK (
                            (state = 'pending' AND status_code IS NULL AND response_json IS NULL)
                            OR
                            (state = 'complete' AND status_code IS NOT NULL AND response_json IS NOT NULL)
                        )
                    )
                    """
                )
                self._connection.execute(
                    "CREATE INDEX idempotency_expiry ON idempotency(state, expires_at)"
                )
            self._connection.execute(f"PRAGMA user_version = {self.SCHEMA_VERSION}")
            self._connection.execute("COMMIT")
        except Exception:
            self._connection.execute("ROLLBACK")
            raise

    def reserve(
        self,
        scope: str,
        key: str,
        request_hash: str,
    ) -> IdempotencyClaim:
        """Claim a new operation or return its cached/in-progress state."""
        if not scope or len(scope) > 64:
            raise ValueError("idempotency scope must contain 1..64 characters")
        if not key or len(key) > 128:
            raise ValueError("idempotency key must contain 1..128 characters")
        if (
            not isinstance(request_hash, str)
            or len(request_hash) != 64
            or any(char not in "0123456789abcdef" for char in request_hash)
        ):
            raise ValueError("request hash must be a lowercase SHA-256 hex digest")

        now = time.time()
        owner = os.urandom(16).hex()
        with self._lock:
            self._ensure_open()
            connection = self._connection
            connection.execute("BEGIN IMMEDIATE")
            try:
                connection.execute(
                    "DELETE FROM idempotency WHERE expires_at <= ?",
                    (now,),
                )
                row = connection.execute(
                    """
                    SELECT request_hash, state, owner, status_code, response_json, updated_at
                    FROM idempotency
                    WHERE scope = ? AND idempotency_key = ?
                    """,
                    (scope, key),
                ).fetchone()

                if row is not None:
                    if row["request_hash"] != request_hash:
                        claim = IdempotencyClaim("conflict")
                    elif row["state"] == "complete":
                        try:
                            response = json.loads(row["response_json"])
                        except (TypeError, json.JSONDecodeError) as error:
                            raise BackendStoreError("cached response is corrupt") from error
                        claim = IdempotencyClaim(
                            "cached",
                            status_code=int(row["status_code"]),
                            response=response,
                        )
                    elif float(row["updated_at"]) + self.lease_seconds > now:
                        claim = IdempotencyClaim("pending")
                    else:
                        connection.execute(
                            """
                            UPDATE idempotency
                            SET owner = ?, updated_at = ?, expires_at = ?
                            WHERE scope = ? AND idempotency_key = ? AND state = 'pending'
                            """,
                            (
                                owner,
                                now,
                                now + self.lease_seconds,
                                scope,
                                key,
                            ),
                        )
                        claim = IdempotencyClaim("claimed", owner=owner)
                else:
                    count = int(
                        connection.execute("SELECT COUNT(*) FROM idempotency").fetchone()[0]
                    )
                    if count >= self.max_rows:
                        evict_count = count - self.max_rows + 1
                        stale = connection.execute(
                            """
                            SELECT scope, idempotency_key
                            FROM idempotency
                            WHERE state = 'complete'
                            ORDER BY updated_at ASC
                            LIMIT ?
                            """,
                            (evict_count,),
                        ).fetchall()
                        for item in stale:
                            connection.execute(
                                "DELETE FROM idempotency WHERE scope = ? AND idempotency_key = ?",
                                (item["scope"], item["idempotency_key"]),
                            )
                    count = int(
                        connection.execute("SELECT COUNT(*) FROM idempotency").fetchone()[0]
                    )
                    if count >= self.max_rows:
                        raise BackendStoreError("idempotency store is full")
                    connection.execute(
                        """
                        INSERT INTO idempotency (
                            scope, idempotency_key, request_hash, state, owner,
                            status_code, response_json, updated_at, expires_at
                        ) VALUES (?, ?, ?, 'pending', ?, NULL, NULL, ?, ?)
                        """,
                        (
                            scope,
                            key,
                            request_hash,
                            owner,
                            now,
                            now + self.lease_seconds,
                        ),
                    )
                    claim = IdempotencyClaim("claimed", owner=owner)

                connection.execute("COMMIT")
                return claim
            except Exception:
                connection.execute("ROLLBACK")
                raise

    def complete(
        self,
        scope: str,
        key: str,
        request_hash: str,
        owner: str,
        status_code: int,
        response: dict[str, Any],
    ) -> None:
        if isinstance(status_code, bool) or not isinstance(status_code, int) or not 100 <= status_code <= 599:
            raise ValueError("invalid HTTP status code")
        if not isinstance(response, dict):
            raise ValueError("idempotency response must be a JSON object")
        try:
            rendered = json.dumps(
                response,
                ensure_ascii=False,
                sort_keys=True,
                separators=(",", ":"),
                allow_nan=False,
            )
        except (TypeError, ValueError, RecursionError) as error:
            raise BackendStoreError(f"response is not bounded JSON data: {error}") from error
        if len(rendered.encode("utf-8")) > 4 * 1024 * 1024:
            raise BackendStoreError("idempotency response exceeds the 4 MiB storage limit")

        now = time.time()
        with self._lock:
            self._ensure_open()
            cursor = self._connection.execute(
                """
                UPDATE idempotency
                SET state = 'complete', status_code = ?, response_json = ?,
                    updated_at = ?, expires_at = ?
                WHERE scope = ? AND idempotency_key = ? AND request_hash = ?
                    AND owner = ? AND state = 'pending'
                """,
                (
                    status_code,
                    rendered,
                    now,
                    now + self.retention_seconds,
                    scope,
                    key,
                    request_hash,
                    owner,
                ),
            )
            if cursor.rowcount != 1:
                raise BackendStoreError("idempotency claim expired or was replaced")

    def abandon(self, scope: str, key: str, owner: str) -> None:
        with self._lock:
            self._ensure_open()
            self._connection.execute(
                """
                DELETE FROM idempotency
                WHERE scope = ? AND idempotency_key = ? AND owner = ? AND state = 'pending'
                """,
                (scope, key, owner),
            )

    def ping(self) -> bool:
        with self._lock:
            self._ensure_open()
            return self._connection.execute("SELECT 1").fetchone()[0] == 1

    def storage_bytes(self) -> int:
        """Return the current size of the database and its SQLite sidecar files."""
        total = 0
        for candidate in (
            self.path,
            Path(str(self.path) + "-wal"),
            Path(str(self.path) + "-shm"),
            Path(str(self.path) + "-journal"),
        ):
            try:
                total += candidate.stat().st_size
            except FileNotFoundError:
                continue
        return total

    def integrity_check(self) -> str:
        with self._lock:
            self._ensure_open()
            row = self._connection.execute("PRAGMA integrity_check").fetchone()
            return str(row[0])

    def backup(self, destination: str | os.PathLike[str]) -> Path:
        """Create and verify a consistent SQLite backup, then atomically publish it."""
        target = Path(destination).expanduser().resolve()
        source = self.path.resolve()
        if target == source:
            raise ValueError("backup destination must differ from the live database")
        target.parent.mkdir(parents=True, exist_ok=True)
        descriptor, temporary_name = tempfile.mkstemp(
            prefix=f".{target.name}.",
            suffix=".tmp",
            dir=str(target.parent),
        )
        os.close(descriptor)
        temporary = Path(temporary_name)
        try:
            with self._lock:
                self._ensure_open()
                backup_connection = sqlite3.connect(str(temporary), timeout=5.0)
                try:
                    self._connection.backup(backup_connection)
                    result = backup_connection.execute("PRAGMA integrity_check").fetchone()[0]
                    if result != "ok":
                        raise BackendStoreError(f"backup integrity check failed: {result}")
                finally:
                    backup_connection.close()
            with temporary.open("rb+") as stream:
                os.fsync(stream.fileno())
            os.replace(temporary, target)
            try:
                directory_fd = os.open(target.parent, os.O_RDONLY)
            except OSError:
                directory_fd = None
            if directory_fd is not None:
                try:
                    os.fsync(directory_fd)
                finally:
                    os.close(directory_fd)
            return target
        except (OSError, sqlite3.Error) as error:
            raise BackendStoreError(f"cannot create database backup: {error}") from error
        finally:
            try:
                temporary.unlink()
            except FileNotFoundError:
                pass

    def close(self) -> None:
        with self._lock:
            if self._closed:
                return
            self._connection.close()
            self._closed = True

    def _ensure_open(self) -> None:
        if self._closed:
            raise BackendStoreError("backend database is closed")
