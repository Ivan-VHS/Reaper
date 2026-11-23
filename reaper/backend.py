"""Opt-in, loopback-only HTTP host for the Reaper reference runtime.

The regular Reaper CLI remains offline. This server is started explicitly and
accepts only bounded JSON requests over a loopback socket.
"""

from __future__ import annotations

import argparse
import asyncio
import concurrent.futures
import hashlib
import hmac
import ipaddress
import json
import logging
import math
import os
import re
import secrets
import signal
import sys
import time
import uuid
from collections import Counter, deque
from dataclasses import dataclass
from functools import partial
from pathlib import Path
from typing import Any, Callable
from urllib.parse import urlsplit

from . import __version__ as REAPER_VERSION
from .backend_store import BackendStore, BackendStoreError
from .errors import ReaperError
from .parser import Node, parse
from .typecheck import TypeChecker


API_VERSION = 1
_LOG = logging.getLogger("reaper.backend")
_HEADER_NAME = re.compile(r"^[!#$%&'*+\-.^_|~0-9A-Za-z]+$")
_METHOD = re.compile(r"^[A-Z]{1,16}$")
_REQUEST_ID = re.compile(r"^[A-Za-z0-9._:-]{1,96}$")
_IDEMPOTENCY_KEY = re.compile(r"^[A-Za-z0-9._:-]{1,128}$")

_REASONS = {
    200: "OK",
    400: "Bad Request",
    401: "Unauthorized",
    403: "Forbidden",
    404: "Not Found",
    405: "Method Not Allowed",
    408: "Request Timeout",
    411: "Length Required",
    413: "Content Too Large",
    415: "Unsupported Media Type",
    417: "Expectation Failed",
    422: "Unprocessable Content",
    429: "Too Many Requests",
    431: "Request Header Fields Too Large",
    500: "Internal Server Error",
    503: "Service Unavailable",
}


@dataclass(frozen=True, slots=True)
class BackendConfig:
    host: str = "127.0.0.1"
    port: int = 8765
    database: Path = Path.home() / ".reaper" / "backend.sqlite3"
    token: str = ""
    allow_execution: bool = False
    request_timeout: float = 10.0
    shutdown_grace: float = 10.0
    max_connections: int = 64
    max_workers: int = 4
    queue_depth: int = 16
    max_requests_per_minute: int = 600
    max_header_bytes: int = 16 * 1024
    max_header_count: int = 64
    max_body_bytes: int = 2 * 1024 * 1024 + 8192
    max_source_bytes: int = 2 * 1024 * 1024
    max_steps: int = 250_000
    max_call_depth: int = 128
    max_collection_items: int = 50_000
    max_text_length: int = 250_000
    max_heap_bytes: int = 32 * 1024 * 1024
    max_output_chars: int = 128_000
    idempotency_ttl: int = 86_400
    idempotency_lease: int = 60
    max_idempotency_rows: int = 50_000

    def __post_init__(self) -> None:
        try:
            address = ipaddress.ip_address(self.host)
        except ValueError as error:
            raise ValueError("backend host must be a numeric loopback IP address") from error
        if not address.is_loopback:
            raise ValueError("backend may bind only to a loopback IP address")
        if isinstance(self.port, bool) or not isinstance(self.port, int) or not 0 <= self.port <= 65535:
            raise ValueError("port must be an integer from 0 through 65535")
        if not math.isfinite(self.request_timeout) or self.request_timeout <= 0:
            raise ValueError("request_timeout must be finite and positive")
        if not math.isfinite(self.shutdown_grace) or self.shutdown_grace <= 0:
            raise ValueError("shutdown_grace must be finite and positive")
        positive = (
            self.max_connections,
            self.max_workers,
            self.max_requests_per_minute,
            self.max_header_bytes,
            self.max_header_count,
            self.max_body_bytes,
            self.max_source_bytes,
            self.max_steps,
            self.max_call_depth,
            self.max_collection_items,
            self.max_text_length,
            self.max_heap_bytes,
            self.max_output_chars,
            self.idempotency_ttl,
            self.idempotency_lease,
            self.max_idempotency_rows,
        )
        if any(isinstance(value, bool) or value < 1 for value in positive):
            raise ValueError("backend resource limits must be positive integers")
        if isinstance(self.queue_depth, bool) or self.queue_depth < 0:
            raise ValueError("queue_depth must be a non-negative integer")
        if self.max_source_bytes > self.max_body_bytes:
            raise ValueError("max_source_bytes cannot exceed max_body_bytes")
        if self.max_header_bytes > 64 * 1024:
            raise ValueError("max_header_bytes cannot exceed 65536")
        if self.max_header_count > 256:
            raise ValueError("max_header_count cannot exceed 256")
        if self.max_body_bytes > 16 * 1024 * 1024:
            raise ValueError("max_body_bytes cannot exceed 16 MiB")
        token = self.token.strip() if self.token else secrets.token_urlsafe(32)
        if len(token) < 32:
            raise ValueError("backend bearer token must contain at least 32 characters")
        object.__setattr__(self, "token", token)
        object.__setattr__(self, "database", Path(self.database).expanduser())


@dataclass(frozen=True, slots=True)
class HttpRequest:
    method: str
    path: str
    headers: dict[str, str]
    body: bytes
    request_id: str


class RequestFailure(Exception):
    def __init__(
        self,
        status: int,
        code: str,
        message: str,
        headers: dict[str, str] | None = None,
    ) -> None:
        super().__init__(message)
        self.status = status
        self.code = code
        self.message = message
        self.headers = headers or {}


class OutputLimitExceeded(RuntimeError):
    pass


class BackendMetrics:
    """Bounded in-memory request counters and a rolling latency sample."""

    def __init__(self, sample_size: int = 512) -> None:
        self._counts: Counter[str] = Counter()
        self._latencies: deque[float] = deque(maxlen=sample_size)
        self._bytes_in = 0
        self._bytes_out = 0

    def record(self, status: int, duration_ms: float, bytes_in: int, bytes_out: int) -> None:
        self._counts[str(status)] += 1
        self._counts["total"] += 1
        if status >= 400:
            self._counts["errors"] += 1
        self._latencies.append(max(0.0, duration_ms))
        self._bytes_in += max(0, bytes_in)
        self._bytes_out += max(0, bytes_out)

    def snapshot(self, active_connections: int, queued_capacity: int) -> dict[str, Any]:
        values = sorted(self._latencies)

        def percentile(fraction: float) -> float:
            if not values:
                return 0.0
            index = max(0, math.ceil(fraction * len(values)) - 1)
            return round(values[index], 3)

        return {
            "requests": dict(self._counts),
            "active_connections": active_connections,
            "worker_capacity": queued_capacity,
            "latency_ms": {
                "sample_count": len(values),
                "p50": percentile(0.50),
                "p95": percentile(0.95),
                "p99": percentile(0.99),
            },
            "bytes": {"received": self._bytes_in, "sent": self._bytes_out},
        }


class BackendServer:
    """Bounded asyncio transport with a small, explicit Reaper service surface."""

    def __init__(self, config: BackendConfig) -> None:
        self.config = config
        self.store = BackendStore(
            config.database,
            lease_seconds=config.idempotency_lease,
            retention_seconds=config.idempotency_ttl,
            max_rows=config.max_idempotency_rows,
        )
        self.executor = concurrent.futures.ThreadPoolExecutor(
            max_workers=config.max_workers,
            thread_name_prefix="reaper-backend",
        )
        self.metrics = BackendMetrics()
        self._server: asyncio.AbstractServer | None = None
        self._work_slots: asyncio.Semaphore | None = None
        self._tasks: set[asyncio.Task[Any]] = set()
        self._active_connections = 0
        self._recent_requests: deque[float] = deque()
        self._closing = False
        self._closed = False

    @property
    def address(self) -> tuple[str, int]:
        if self._server is None or not self._server.sockets:
            raise RuntimeError("backend server has not started")
        host, port = self._server.sockets[0].getsockname()[:2]
        return str(host), int(port)

    @property
    def url(self) -> str:
        host, port = self.address
        rendered_host = f"[{host}]" if ":" in host else host
        return f"http://{rendered_host}:{port}"

    async def start(self) -> None:
        if self._server is not None or self._closed:
            raise RuntimeError("backend server cannot be started in its current state")
        self._work_slots = asyncio.Semaphore(self.config.max_workers + self.config.queue_depth)
        self._server = await asyncio.start_server(
            self._accept_connection,
            host=self.config.host,
            port=self.config.port,
            limit=self.config.max_header_bytes,
            backlog=self.config.max_connections,
        )

    async def wait_closed(self) -> None:
        if self._server is not None:
            await self._server.wait_closed()

    def _accept_connection(
        self,
        reader: asyncio.StreamReader,
        writer: asyncio.StreamWriter,
    ) -> None:
        if self._closing or self._active_connections >= self.config.max_connections:
            writer.write(
                b"HTTP/1.1 503 Service Unavailable\r\n"
                b"Connection: close\r\nContent-Length: 0\r\n\r\n"
            )
            writer.close()
            return
        self._active_connections += 1
        task = asyncio.create_task(self._handle_connection(reader, writer))
        self._tasks.add(task)
        task.add_done_callback(self._connection_finished)

    def _connection_finished(self, task: asyncio.Task[Any]) -> None:
        self._tasks.discard(task)
        self._active_connections = max(0, self._active_connections - 1)
        if not task.cancelled():
            try:
                task.exception()
            except Exception:
                pass

    async def _handle_connection(
        self,
        reader: asyncio.StreamReader,
        writer: asyncio.StreamWriter,
    ) -> None:
        started = time.monotonic()
        request: HttpRequest | None = None
        status = 500
        response_size = 0
        request_size = 0
        request_id = uuid.uuid4().hex
        response_headers: dict[str, str] = {}
        payload: dict[str, Any]
        try:
            request = await self._read_request(reader)
            request_id = request.request_id
            request_size = len(request.body)
            status, payload, response_headers = await self._dispatch(request)
        except RequestFailure as error:
            status = error.status
            response_headers = error.headers
            payload = self._error_payload(error.code, error.message, request_id)
        except asyncio.TimeoutError:
            status = 408
            payload = self._error_payload("request_timeout", "request timed out", request_id)
        except (asyncio.IncompleteReadError, ConnectionError):
            status = 400
            payload = self._error_payload("incomplete_request", "request was interrupted", request_id)
        except Exception:
            status = 500
            payload = self._error_payload(
                "internal_error",
                "backend could not complete the request",
                request_id,
            )
            _LOG.exception("backend request failed", extra={"request_id": request_id})
        finally:
            duration_ms = (time.monotonic() - started) * 1000.0
            try:
                response_size = await self._write_response(
                    writer,
                    status,
                    payload,
                    request_id,
                    response_headers,
                )
            except (ConnectionError, asyncio.TimeoutError):
                pass
            self.metrics.record(status, duration_ms, request_size, response_size)
            _LOG.info(
                json.dumps(
                    {
                        "event": "http_request",
                        "request_id": request_id,
                        "method": request.method if request else "UNKNOWN",
                        "path": request.path if request else "UNKNOWN",
                        "status": status,
                        "duration_ms": round(duration_ms, 3),
                        "request_bytes": request_size,
                        "response_bytes": response_size,
                    },
                    separators=(",", ":"),
                    sort_keys=True,
                )
            )
            writer.close()
            try:
                await asyncio.wait_for(writer.wait_closed(), timeout=self.config.request_timeout)
            except (asyncio.TimeoutError, ConnectionError):
                writer.transport.abort()

    async def _read_request(self, reader: asyncio.StreamReader) -> HttpRequest:
        try:
            raw = await asyncio.wait_for(
                reader.readuntil(b"\r\n\r\n"),
                timeout=self.config.request_timeout,
            )
        except asyncio.LimitOverrunError as error:
            raise RequestFailure(
                431,
                "headers_too_large",
                "request headers exceed the configured limit",
            ) from error
        if len(raw) > self.config.max_header_bytes:
            raise RequestFailure(431, "headers_too_large", "request headers exceed the configured limit")

        lines = raw[:-4].split(b"\r\n")
        if not lines or not lines[0]:
            raise RequestFailure(400, "bad_request", "request line is missing")
        try:
            request_line = lines[0].decode("ascii")
        except UnicodeDecodeError as error:
            raise RequestFailure(400, "bad_request", "request line must be ASCII") from error
        parts = request_line.split(" ")
        if len(parts) != 3 or not _METHOD.fullmatch(parts[0]):
            raise RequestFailure(400, "bad_request", "request line is malformed")
        method, target, version = parts
        if version not in {"HTTP/1.0", "HTTP/1.1"}:
            raise RequestFailure(400, "http_version", "only HTTP/1.0 and HTTP/1.1 are supported")
        if not target.startswith("/") or any(ord(char) < 33 or ord(char) > 126 for char in target):
            raise RequestFailure(400, "request_target", "only an origin-form request path is accepted")
        parsed_target = urlsplit(target)
        if parsed_target.query or parsed_target.fragment or parsed_target.path != target:
            raise RequestFailure(400, "request_target", "query strings and fragments are not accepted")

        if len(lines) - 1 > self.config.max_header_count:
            raise RequestFailure(431, "too_many_headers", "too many request headers")
        headers: dict[str, str] = {}
        for line in lines[1:]:
            if not line or b":" not in line:
                raise RequestFailure(400, "bad_header", "request header is malformed")
            name_bytes, value_bytes = line.split(b":", 1)
            try:
                name = name_bytes.decode("ascii").lower()
                value = value_bytes.decode("latin-1").strip()
            except UnicodeDecodeError as error:
                raise RequestFailure(400, "bad_header", "request header is malformed") from error
            if not _HEADER_NAME.fullmatch(name) or any(
                (ord(char) < 32 and char != "\t") or ord(char) == 127 for char in value
            ):
                raise RequestFailure(400, "bad_header", "request header contains invalid characters")
            if name in headers:
                raise RequestFailure(400, "duplicate_header", "duplicate request headers are not accepted")
            headers[name] = value

        if version == "HTTP/1.1" and not headers.get("host"):
            raise RequestFailure(400, "host_required", "HTTP/1.1 requests require a Host header")
        if "expect" in headers:
            raise RequestFailure(417, "expectation_failed", "Expect headers are not supported")
        if "transfer-encoding" in headers:
            raise RequestFailure(400, "transfer_encoding", "chunked and encoded request bodies are not supported")
        if headers.get("content-encoding", "identity").lower() != "identity":
            raise RequestFailure(415, "content_encoding", "compressed request bodies are not supported")

        content_length_text = headers.get("content-length")
        if content_length_text is None:
            if method == "POST":
                raise RequestFailure(411, "length_required", "POST requests require Content-Length")
            content_length = 0
        else:
            if not content_length_text.isdigit() or len(content_length_text) > 10:
                raise RequestFailure(400, "content_length", "Content-Length is invalid")
            content_length = int(content_length_text)
        if content_length > self.config.max_body_bytes:
            raise RequestFailure(413, "body_too_large", "request body exceeds the configured limit")
        if method != "POST" and content_length:
            raise RequestFailure(400, "unexpected_body", "request body is not accepted for this method")

        if method == "POST":
            content_type = headers.get("content-type", "").split(";", 1)[0].strip().lower()
            if content_type != "application/json":
                raise RequestFailure(415, "content_type", "POST requests require application/json")

        try:
            body = await asyncio.wait_for(
                reader.readexactly(content_length),
                timeout=self.config.request_timeout,
            )
        except asyncio.IncompleteReadError as error:
            raise RequestFailure(400, "incomplete_body", "request body ended before Content-Length") from error

        incoming_id = headers.get("x-request-id", "")
        request_id = incoming_id if _REQUEST_ID.fullmatch(incoming_id) else uuid.uuid4().hex
        return HttpRequest(method, parsed_target.path, headers, body, request_id)

    async def _dispatch(
        self,
        request: HttpRequest,
    ) -> tuple[int, dict[str, Any], dict[str, str]]:
        if request.path in {"/healthz", "/readyz"}:
            if request.method != "GET":
                raise RequestFailure(405, "method_not_allowed", "this endpoint accepts GET only")
            if request.path == "/healthz":
                return 200, {"status": "alive"}, {}
            try:
                ready = await self._run_blocking(self.store.ping)
            except Exception:
                ready = False
            if not ready:
                return 503, {"status": "not_ready"}, {}
            return 200, {"status": "ready"}, {}

        if not request.path.startswith("/v1/"):
            raise RequestFailure(404, "not_found", "endpoint does not exist")
        if not self._authorized(request):
            raise RequestFailure(
                401,
                "unauthorized",
                "a valid bearer token is required",
                {"WWW-Authenticate": "Bearer"},
            )
        if not self._allow_request_rate():
            raise RequestFailure(
                429,
                "rate_limited",
                "request rate limit exceeded",
                {"Retry-After": "1"},
            )

        if request.path == "/v1/info" and request.method == "GET":
            return 200, {
                "api_version": API_VERSION,
                "reaper_version": REAPER_VERSION,
                "service": "reaper-local-backend",
                "capabilities": {
                    "source_check": True,
                    "restricted_execution": self.config.allow_execution,
                    "persistent_idempotency": True,
                    "remote_binding": False,
                    "native_ffi": False,
                },
                "limits": {
                    "source_bytes": self.config.max_source_bytes,
                    "steps": self.config.max_steps,
                    "call_depth": self.config.max_call_depth,
                    "collection_items": self.config.max_collection_items,
                    "heap_bytes_estimate": self.config.max_heap_bytes,
                    "output_characters": self.config.max_output_chars,
                    "max_connections": self.config.max_connections,
                    "worker_threads": self.config.max_workers,
                },
            }, {}
        if request.path == "/v1/metrics" and request.method == "GET":
            return 200, self.metrics.snapshot(
                self._active_connections,
                self.config.max_workers + self.config.queue_depth,
            ), {}
        if request.path == "/v1/check" and request.method == "POST":
            payload = self._decode_json(request.body)
            source = self._source(payload, allowed={"source"})
            key = self._idempotency_key(request)
            fingerprint = self._fingerprint({"source": source})
            return await self._idempotent(
                "check",
                key,
                fingerprint,
                partial(self._check_source, source),
            )
        if request.path == "/v1/run" and request.method == "POST":
            if not self.config.allow_execution:
                raise RequestFailure(
                    403,
                    "execution_disabled",
                    "execution is disabled; restart with --allow-execution to opt in",
                )
            payload = self._decode_json(request.body)
            source = self._source(payload, allowed={"source", "engine"})
            engine = payload.get("engine", "treewalk")
            if engine not in {"treewalk", "vm"}:
                raise RequestFailure(422, "invalid_engine", "engine must be treewalk or vm")
            key = self._idempotency_key(request)
            fingerprint = self._fingerprint({"source": source, "engine": engine})
            return await self._idempotent(
                "run",
                key,
                fingerprint,
                partial(self._run_source, source, engine),
            )
        if request.path in {"/v1/info", "/v1/metrics", "/v1/check", "/v1/run"}:
            raise RequestFailure(405, "method_not_allowed", "method is not allowed for this endpoint")
        raise RequestFailure(404, "not_found", "endpoint does not exist")

    def _authorized(self, request: HttpRequest) -> bool:
        scheme, separator, supplied = request.headers.get("authorization", "").partition(" ")
        return (
            separator == " "
            and scheme.lower() == "bearer"
            and bool(supplied)
            and hmac.compare_digest(supplied, self.config.token)
        )

    def _allow_request_rate(self) -> bool:
        now = time.monotonic()
        cutoff = now - 60.0
        while self._recent_requests and self._recent_requests[0] <= cutoff:
            self._recent_requests.popleft()
        if len(self._recent_requests) >= self.config.max_requests_per_minute:
            return False
        self._recent_requests.append(now)
        return True

    def _decode_json(self, body: bytes) -> dict[str, Any]:
        try:
            payload = json.loads(
                body.decode("utf-8"),
                object_pairs_hook=self._unique_object,
                parse_constant=self._reject_constant,
            )
        except RequestFailure:
            raise
        except (UnicodeDecodeError, json.JSONDecodeError, RecursionError) as error:
            raise RequestFailure(400, "invalid_json", "request body must be valid UTF-8 JSON") from error
        if not isinstance(payload, dict):
            raise RequestFailure(400, "invalid_json", "top-level JSON value must be an object")
        self._validate_json_depth(payload)
        return payload

    @staticmethod
    def _unique_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
        result: dict[str, Any] = {}
        for key, value in pairs:
            if key in result:
                raise RequestFailure(400, "duplicate_json_key", "duplicate JSON object keys are not accepted")
            result[key] = value
        return result

    @staticmethod
    def _reject_constant(value: str) -> None:
        raise RequestFailure(400, "invalid_json_number", f"JSON constant {value} is not permitted")

    @staticmethod
    def _validate_json_depth(value: Any) -> None:
        pending = [(value, 0)]
        visited = 0
        while pending:
            current, depth = pending.pop()
            visited += 1
            if depth > 32 or visited > 20_000:
                raise RequestFailure(400, "json_too_complex", "JSON nesting or item count exceeds the limit")
            if isinstance(current, dict):
                pending.extend((item, depth + 1) for item in current.values())
            elif isinstance(current, list):
                pending.extend((item, depth + 1) for item in current)

    def _source(self, payload: dict[str, Any], *, allowed: set[str]) -> str:
        unknown = set(payload) - allowed
        if unknown:
            raise RequestFailure(422, "unknown_fields", "request contains unsupported fields")
        source = payload.get("source")
        if not isinstance(source, str):
            raise RequestFailure(422, "source_required", "source must be a UTF-8 string")
        try:
            source_size = len(source.encode("utf-8"))
        except UnicodeEncodeError as error:
            raise RequestFailure(422, "source_encoding", "source contains invalid Unicode") from error
        if source_size > self.config.max_source_bytes:
            raise RequestFailure(413, "source_too_large", "source exceeds the configured byte limit")
        return source

    @staticmethod
    def _idempotency_key(request: HttpRequest) -> str:
        key = request.headers.get("idempotency-key", "")
        if not _IDEMPOTENCY_KEY.fullmatch(key):
            raise RequestFailure(
                400,
                "idempotency_key_required",
                "Idempotency-Key must contain 1..128 safe ASCII characters",
            )
        return key

    @staticmethod
    def _fingerprint(payload: dict[str, Any]) -> str:
        encoded = json.dumps(
            payload,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
            allow_nan=False,
        ).encode("utf-8")
        return hashlib.sha256(encoded).hexdigest()

    async def _idempotent(
        self,
        scope: str,
        key: str,
        fingerprint: str,
        operation: Callable[[], tuple[int, dict[str, Any]]],
    ) -> tuple[int, dict[str, Any], dict[str, str]]:
        try:
            claim = await self._run_blocking(
                self.store.reserve,
                scope,
                key,
                fingerprint,
            )
        except (BackendStoreError, OSError):
            raise RequestFailure(503, "storage_unavailable", "idempotency storage is unavailable")

        if claim.state == "cached":
            return int(claim.status_code or 200), claim.response or {}, {"Idempotency-Replayed": "true"}
        if claim.state == "conflict":
            raise RequestFailure(
                409,
                "idempotency_conflict",
                "this idempotency key was already used with a different request",
            )
        if claim.state == "pending":
            raise RequestFailure(
                409,
                "request_in_progress",
                "an operation with this idempotency key is still in progress",
                {"Retry-After": "1"},
            )
        if claim.state != "claimed" or claim.owner is None:
            raise RequestFailure(503, "storage_state", "idempotency storage returned an invalid state")

        try:
            status, response = await self._run_blocking(operation)
            await self._run_blocking(
                self.store.complete,
                scope,
                key,
                fingerprint,
                claim.owner,
                status,
                response,
            )
        except RequestFailure:
            await self._best_effort_abandon(scope, key, claim.owner)
            raise
        except Exception:
            await self._best_effort_abandon(scope, key, claim.owner)
            raise
        return status, response, {}

    async def _best_effort_abandon(self, scope: str, key: str, owner: str) -> None:
        try:
            await self._run_blocking(self.store.abandon, scope, key, owner)
        except Exception:
            _LOG.warning("could not release an idempotency claim")

    def _check_source(self, source: str) -> tuple[int, dict[str, Any]]:
        try:
            tree = parse(source, "<backend-request>")
            result = TypeChecker("<backend-request>").check(tree)
            return 200, {"api_version": API_VERSION, **result.as_dict()}
        except ReaperError as error:
            return 422, {
                "api_version": API_VERSION,
                "ok": False,
                "error": {"code": "source_error", "message": str(error)},
            }
        except (RecursionError, ValueError) as error:
            return 422, {
                "api_version": API_VERSION,
                "ok": False,
                "error": {"code": "source_limit", "message": str(error)},
            }

    def _run_source(self, source: str, engine: str) -> tuple[int, dict[str, Any]]:
        try:
            tree = parse(source, "<backend-request>")
            type_result = TypeChecker("<backend-request>").check(tree)
            if not type_result.ok:
                return 422, {
                    "api_version": API_VERSION,
                    "ok": False,
                    "error": {"code": "type_error", "message": "source did not pass static type analysis"},
                    "diagnostics": [item.as_dict() for item in type_result.diagnostics],
                }
            if self._contains_import(tree):
                return 422, {
                    "api_version": API_VERSION,
                    "ok": False,
                    "error": {
                        "code": "restricted_effect",
                        "message": "module imports are disabled in backend execution",
                    },
                }

            from .runtime import Interpreter

            output: list[str] = []
            output_size = 0

            def capture(line: str) -> None:
                nonlocal output_size
                next_size = output_size + len(line)
                if next_size > self.config.max_output_chars:
                    raise OutputLimitExceeded("program output limit exceeded")
                output.append(line)
                output_size = next_size

            interpreter = Interpreter(
                output=capture,
                max_steps=self.config.max_steps,
                max_call_depth=self.config.max_call_depth,
                max_collection_items=self.config.max_collection_items,
                max_text_length=self.config.max_text_length,
                allow_native_ffi=False,
                max_heap_bytes=self.config.max_heap_bytes,
                max_open_resources=1,
            )
            forbidden_builtins = {
                "ask",
                "file_open",
                "file_read",
                "file_write",
                "file_close",
                "with_file",
                "ffi_open",
                "ffi_bind",
                "ffi_close",
                "pytyliki_open",
                "consent_check",
                "consent_revoke",
            }
            for name in forbidden_builtins:
                interpreter.globals.values.pop(name, None)

            result = interpreter.run(source, filename="<backend-request>", engine=engine)
            return 200, {
                "api_version": API_VERSION,
                "ok": True,
                "engine": engine,
                "output": output,
                "result": self._json_safe(result),
                "steps": interpreter.steps,
            }
        except OutputLimitExceeded as error:
            return 422, {
                "api_version": API_VERSION,
                "ok": False,
                "error": {"code": "output_limit", "message": str(error)},
            }
        except ReaperError as error:
            return 422, {
                "api_version": API_VERSION,
                "ok": False,
                "error": {"code": "runtime_error", "message": str(error)},
            }
        except (ArithmeticError, RecursionError, TypeError, ValueError) as error:
            return 422, {
                "api_version": API_VERSION,
                "ok": False,
                "error": {"code": "runtime_error", "message": str(error)},
            }

    @staticmethod
    def _contains_import(tree: Node) -> bool:
        pending = [tree]
        while pending:
            node = pending.pop()
            if node.kind == "import":
                return True
            pending.extend(node.children or [])
        return False

    @staticmethod
    def _json_safe(value: Any, *, depth: int = 0, seen: set[int] | None = None) -> Any:
        if depth > 24:
            return {"type": "depth_limit"}
        if value is None or isinstance(value, (str, bool, int)):
            return value
        if isinstance(value, float):
            return value if math.isfinite(value) else None
        if seen is None:
            seen = set()
        if isinstance(value, (list, tuple, dict)):
            identity = id(value)
            if identity in seen:
                return {"type": "cycle"}
            seen.add(identity)
            try:
                if isinstance(value, dict):
                    result: dict[str, Any] = {}
                    for key, item in list(value.items())[:10_000]:
                        if isinstance(key, str):
                            result[key] = BackendServer._json_safe(item, depth=depth + 1, seen=seen)
                    return result
                return [
                    BackendServer._json_safe(item, depth=depth + 1, seen=seen)
                    for item in value[:10_000]
                ]
            finally:
                seen.discard(identity)
        return {"type": type(value).__name__}

    async def _run_blocking(self, function: Callable[..., Any], *args: Any) -> Any:
        if self._work_slots is None or self._closing:
            raise RequestFailure(503, "shutting_down", "backend is shutting down")
        try:
            await asyncio.wait_for(
                self._work_slots.acquire(),
                timeout=self.config.request_timeout,
            )
        except asyncio.TimeoutError as error:
            raise RequestFailure(
                503,
                "worker_capacity",
                "backend worker capacity is exhausted",
                {"Retry-After": "1"},
            ) from error

        loop = asyncio.get_running_loop()
        future = loop.run_in_executor(self.executor, partial(function, *args))
        cancelled = False
        try:
            return await asyncio.shield(future)
        except asyncio.CancelledError:
            cancelled = True
            future.add_done_callback(lambda _done: loop.call_soon_threadsafe(self._work_slots.release))
            raise
        finally:
            if not cancelled:
                self._work_slots.release()

    async def _write_response(
        self,
        writer: asyncio.StreamWriter,
        status: int,
        payload: dict[str, Any],
        request_id: str,
        extra_headers: dict[str, str],
    ) -> int:
        body = json.dumps(
            {"request_id": request_id, **payload},
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
            allow_nan=False,
        ).encode("utf-8")
        header_items = {
            "Content-Type": "application/json; charset=utf-8",
            "Content-Length": str(len(body)),
            "Connection": "close",
            "Cache-Control": "no-store",
            "X-Content-Type-Options": "nosniff",
            "X-Request-ID": request_id,
            **extra_headers,
        }
        head = (
            f"HTTP/1.1 {status} {_REASONS.get(status, 'Unknown')}\r\n"
            + "".join(f"{name}: {value}\r\n" for name, value in header_items.items())
            + "\r\n"
        ).encode("latin-1")
        writer.write(head + body)
        await asyncio.wait_for(writer.drain(), timeout=self.config.request_timeout)
        return len(head) + len(body)

    @staticmethod
    def _error_payload(code: str, message: str, request_id: str) -> dict[str, Any]:
        return {
            "error": {"code": code, "message": message},
            "request_id": request_id,
        }

    async def close(self) -> None:
        if self._closed:
            return
        self._closing = True
        if self._server is not None:
            self._server.close()
            await self._server.wait_closed()

        tasks = list(self._tasks)
        if tasks:
            try:
                await asyncio.wait_for(
                    asyncio.gather(*tasks, return_exceptions=True),
                    timeout=self.config.shutdown_grace,
                )
            except asyncio.TimeoutError:
                for task in tasks:
                    task.cancel()
                await asyncio.gather(*tasks, return_exceptions=True)

        self.executor.shutdown(wait=True, cancel_futures=True)
        self.store.close()
        self._closed = True


def _configure_logging() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(message)s",
        stream=sys.stderr,
    )


async def _serve(config: BackendConfig) -> None:
    server = BackendServer(config)
    await server.start()
    _configure_logging()
    host, port = server.address
    print(f"Reaper local backend: {server.url}", file=sys.stderr)
    print(f"Bearer token (shown once; do not share): {config.token}", file=sys.stderr)
    print("Health: /healthz   Readiness: /readyz   API: /v1/info", file=sys.stderr)
    _LOG.info(
        json.dumps(
            {
                "event": "backend_started",
                "host": host,
                "port": port,
                "api_version": API_VERSION,
                "execution_enabled": config.allow_execution,
            },
            separators=(",", ":"),
            sort_keys=True,
        )
    )

    stop = asyncio.Event()
    loop = asyncio.get_running_loop()
    for signum in (signal.SIGINT, signal.SIGTERM):
        try:
            loop.add_signal_handler(signum, stop.set)
        except (NotImplementedError, RuntimeError):
            try:
                signal.signal(signum, lambda _signum, _frame: loop.call_soon_threadsafe(stop.set))
            except (ValueError, OSError):
                pass
    try:
        await stop.wait()
    finally:
        await server.close()


def _database_from_env() -> str:
    return os.environ.get(
        "REAPER_BACKEND_DATABASE",
        str(Path.home() / ".reaper" / "backend.sqlite3"),
    )


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="reaper-backend",
        description="Run or inspect Reaper's optional local backend.",
    )
    commands = parser.add_subparsers(dest="command", required=True)

    serve = commands.add_parser("serve", help="start the loopback-only backend")
    serve.add_argument("--host", default=os.environ.get("REAPER_BACKEND_HOST", "127.0.0.1"))
    serve.add_argument("--port", type=int, default=int(os.environ.get("REAPER_BACKEND_PORT", "8765")))
    serve.add_argument("--database", default=_database_from_env())
    serve.add_argument("--token", default=os.environ.get("REAPER_BACKEND_TOKEN", ""))
    serve.add_argument("--allow-execution", action="store_true")
    serve.add_argument("--request-timeout", type=float, default=10.0)
    serve.add_argument("--shutdown-grace", type=float, default=10.0)
    serve.add_argument("--max-connections", type=int, default=64)
    serve.add_argument("--workers", type=int, default=4)
    serve.add_argument("--queue-depth", type=int, default=16)
    serve.add_argument("--max-requests-per-minute", type=int, default=600)
    serve.add_argument("--max-source-bytes", type=int, default=2 * 1024 * 1024)
    serve.add_argument("--max-steps", type=int, default=250_000)
    serve.add_argument("--max-heap-bytes", type=int, default=32 * 1024 * 1024)
    serve.add_argument("--max-output-chars", type=int, default=128_000)

    verify = commands.add_parser("verify", help="run SQLite integrity and schema checks")
    verify.add_argument("--database", default=_database_from_env())

    backup = commands.add_parser("backup", help="create an atomic, verified SQLite backup")
    backup.add_argument("destination")
    backup.add_argument("--database", default=_database_from_env())
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _build_parser().parse_args(argv)
    try:
        if args.command == "serve":
            config = BackendConfig(
                host=args.host,
                port=args.port,
                database=Path(args.database),
                token=args.token,
                allow_execution=args.allow_execution,
                request_timeout=args.request_timeout,
                shutdown_grace=args.shutdown_grace,
                max_connections=args.max_connections,
                max_workers=args.workers,
                queue_depth=args.queue_depth,
                max_requests_per_minute=args.max_requests_per_minute,
                max_source_bytes=args.max_source_bytes,
                max_body_bytes=max(2 * 1024 * 1024 + 8192, args.max_source_bytes + 8192),
                max_steps=args.max_steps,
                max_heap_bytes=args.max_heap_bytes,
                max_output_chars=args.max_output_chars,
            )
            asyncio.run(_serve(config))
            return 0

        store = BackendStore(args.database)
        try:
            if args.command == "verify":
                result = store.integrity_check()
                print(json.dumps({"integrity": result, "schema_version": store.SCHEMA_VERSION}))
                return 0 if result == "ok" else 1
            if args.command == "backup":
                destination = store.backup(args.destination)
                print(json.dumps({"backup": str(destination), "integrity": "ok"}))
                return 0
        finally:
            store.close()
    except (ValueError, BackendStoreError, OSError) as error:
        print(f"reaper-backend: {error}", file=sys.stderr)
        return 2
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
