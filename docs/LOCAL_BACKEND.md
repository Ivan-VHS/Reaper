# Reaper local backend

**Status:** implemented as an opt-in Python reference-runtime service.  
**API contract:** v1.  
**Entry point:** reaper-backend.  
**Owner:** Ivan-VHS.

The backend exposes a small, versioned service boundary around Reaper's existing
parser, conservative type checker and optional restricted interpreter. It does
not change the language grammar, the default CLI workflow or the native C17
capability boundary.

## Operating model

The normal Reaper runtime remains local and offline. No server is started by
installing Reaper, importing the language package, opening Studio, running a
program or using LSP/DAP. Start the backend explicitly:

    reaper-backend serve

The service binds only to a numeric loopback address (127.0.0.1 or ::1).
A non-loopback bind is rejected during configuration validation. At startup, the service displays the active bearer token once to
the controlling terminal. When no token is configured, it generates a
cryptographically random value. The token is held in memory only; it is not
written to SQLite or request logs. An operator may supply a token through
REAPER_BACKEND_TOKEN or --token; configured tokens must contain at least
32 ASCII characters. Prefer the environment variable over --token on systems
where command-line arguments are visible to other local processes.

The service is intentionally not a hosted or LAN-facing API. It does not
enable CORS, accept proxy-forwarded identity headers, or expose a remote bind
option. TLS is not configured because the listener is loopback-only. Do not
publish the port through a tunnel, reverse proxy or port forward.

## HTTP contract

The machine-readable OpenAPI 3.1 contract is maintained in [BACKEND_API_V1.yaml](BACKEND_API_V1.yaml). Keep its schemas and response codes aligned with the implementation when changing API v1.

Requests use HTTP/1.0 or HTTP/1.1 with one request per connection. The parser
requires an unambiguous Content-Length, rejects duplicate headers,
Transfer-Encoding, compressed bodies, unsupported Expect headers,
query strings and fragments. JSON request bodies must be UTF-8, must not
contain duplicate object keys or non-finite numeric constants, and have bounded
nesting and element counts.

Every /v1/* route requires Authorization: Bearer <token>. Mutating or
computational POST routes require an Idempotency-Key containing 1–128 safe
ASCII characters. Responses carry a request_id, X-Request-ID,
Cache-Control: no-store and X-Content-Type-Options: nosniff.

| Route | Method | Authentication | Behavior |
|---|---|---|---|
| /healthz | GET | none | Process liveness; deliberately contains no dependency details |
| /readyz | GET | none | SQLite readiness check |
| /v1/info | GET | bearer | API/runtime versions, supported operations and effective limits |
| /v1/metrics | GET | bearer | Request counts, worker queue, CPU time, available RSS/I/O counters, SQLite footprint, network bytes and rolling p50/p95/p99 latency |
| /v1/check | POST | bearer + idempotency key | Parse and statically analyze a source string without executing it |
| /v1/run | POST | bearer + idempotency key | Optional restricted execution; disabled unless explicitly enabled |

### Check request

    POST /v1/check HTTP/1.1
    Authorization: Bearer <token>
    Idempotency-Key: check-2026-001
    Content-Type: application/json

    {"source":"make answer := 42\nsay(answer)\n"}

The result contains the existing type checker's ok, diagnostics and summary.
A syntactically valid program with type diagnostics is still a successfully
processed request; ok is false and the diagnostics describe the problem.
Invalid source returns a 422 response.

### Restricted execution

Execution is opt-in:

    reaper-backend serve --allow-execution

Example request body:

    {"source":"make answer := 42\nsay(answer)\n","engine":"treewalk"}

The engine field may be treewalk or vm. This endpoint uses a fresh
interpreter for every request, applies the configured Reaper step, call-depth,
collection, text and managed-heap budgets, and captures bounded output.

The backend removes interactive input, file access, native FFI and consent
built-ins before execution, and rejects module imports. The request cannot
select a filename or filesystem path. Output is captured in the response; it
is not written to server stdout. This is a restricted local execution profile,
not an operating-system sandbox or process-isolation boundary. The Python
reference runtime and its interpreter implementation still execute inside the
backend process. Keep the listener on loopback and use it only from trusted
local clients.

## Resource and failure controls

Defaults are deliberately finite:

| Resource | Default |
|---|---:|
| Concurrent client connections | 64 |
| Worker threads | 4 |
| Queued worker operations | 16 |
| Request timeout per I/O phase | 10 seconds |
| Header bytes / header count | 16 KiB / 64 |
| Request body | 2 MiB + 8 KiB |
| Source text | 2 MiB UTF-8 |
| Requests per minute | 600 |
| Interpreter steps | 250,000 |
| Interpreter call depth | 128 |
| Collection elements | 50,000 |
| Text characters | 250,000 |
| Managed heap estimate | 32 MiB |
| Captured output | 128,000 characters |

The event loop handles socket I/O. Parsing, type analysis, interpreter work and
SQLite calls run in a fixed-size ThreadPoolExecutor. An asyncio admission
semaphore bounds active plus queued worker work; saturation produces 503 rather
than an unbounded queue. The configured limits can be adjusted through the CLI.
The managed heap value is Reaper's host-side allocation estimate, not a hard
process-RSS limit.

The backend has no external upstream dependency, so it does not install an
unused circuit breaker. Add one at a future adapter boundary if and when a
real remote dependency is introduced; do not add retries to local deterministic
operations.

## Persistence and idempotency

The SQLite file is local to the operator's user profile by default:
~/.reaper/backend.sqlite3. Set REAPER_BACKEND_DATABASE or pass --database
to choose another path.

The store enables foreign keys, WAL, full synchronous commits and a finite busy
timeout. Schema changes use SQLite's transactional user_version migration
mechanism. An atomic BEGIN IMMEDIATE claim prevents two workers from owning
the same active key. A repeated key with the same request fingerprint replays
the stored status and JSON response; a different fingerprint returns 409; an
active claim returns 409 with Retry-After. Claims have finite leases and
completed results expire after 24 hours by default. The store has a configurable
row cap and evicts the oldest completed cache entries when it reaches capacity;
active claims are not evicted.

The check and restricted-run operations are deterministic and have no exposed
filesystem, interactive or FFI side effects, which makes replay safe. This is
single-process local idempotency, not a distributed exactly-once guarantee.
Request IDs and metrics are process-local; persistent request state is limited
to the idempotency cache.

## Logs, metrics and shutdown

Logs are newline-delimited JSON records with request ID, method, route, status,
duration and byte counts. They deliberately exclude bearer tokens, source text,
program output and request bodies. Latency percentiles are calculated from a
bounded in-memory rolling sample, not from an unbounded history. Metrics expose
worker activity and waiters, cumulative process CPU seconds, peak RSS and block
I/O counters when the host platform provides them, the current SQLite/WAL/SHM
footprint and network bytes. Unsupported OS counters are returned as null.
Metrics reset when the process restarts.

SIGINT/SIGTERM stops the listener, allows active requests to finish for the
configured grace period, cancels remaining connection tasks, then shuts down
the worker pool and closes SQLite. A worker task that is already executing is
not forcibly terminated by asyncio; interpreter step and data limits bound the
supported program path.

## Runtime limits

The main limits can be set at startup. The defaults match the table above.

| CLI option | Default |
|---|---:|
| --max-connections | 64 |
| --workers | 4 |
| --queue-depth | 16 |
| --request-timeout | 10 seconds |
| --shutdown-grace | 10 seconds |
| --max-requests-per-minute | 600 |
| --max-header-bytes / --max-header-count | 16 KiB / 64 |
| --max-body-bytes | 2 MiB + 8 KiB |
| --max-source-bytes | 2 MiB |
| --max-steps / --max-call-depth | 250,000 / 128 |
| --max-collection-items | 50,000 |
| --max-text-length | 250,000 |
| --max-heap-bytes | 32 MiB |
| --max-output-chars | 128,000 |
| --idempotency-ttl | 86,400 seconds |
| --idempotency-lease | 60 seconds |
| --max-idempotency-rows | 50,000 |

## Configuration

| Variable | Equivalent CLI option | Default |
|---|---|---|
| REAPER_BACKEND_HOST | --host | 127.0.0.1 |
| REAPER_BACKEND_PORT | --port | 8765 |
| REAPER_BACKEND_DATABASE | --database | ~/.reaper/backend.sqlite3 |
| REAPER_BACKEND_TOKEN | --token | generated at startup |

Examples:

    reaper-backend serve --workers 6 --queue-depth 12 --max-connections 80
    reaper-backend serve --allow-execution --max-steps 100000
    reaper-backend verify
    reaper-backend backup ./backend-backup.sqlite3

verify runs SQLite's integrity check and reports the supported schema
version. backup uses SQLite's online backup API, verifies the resulting
database, then publishes it with an atomic rename. The command does not restore
or overwrite the live database.

## Validation

    python -m unittest tests.test_backend -v
    python -m unittest discover -s tests -v

The backend tests cover loopback-only binding, bearer authentication, bounded
API use, idempotent replay and conflict handling, restricted execution,
health/readiness, metrics, persistent SQLite claims and verified backups.

Python remains Reaper's compatibility reference runtime. The local backend
does not claim native C17 parity, hardware access, device services, multi-node
coordination, TLS termination, remote authentication or process sandboxing.
