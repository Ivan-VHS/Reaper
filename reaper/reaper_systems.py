"""Experimental runtime systems inspired by the Reapers architecture.

These are bounded, in-process reference implementations. They deliberately
avoid claiming network-level zero cost, native JIT compilation, safe automatic
C/C++ translation, or hard real-time latency guarantees.
"""
from __future__ import annotations

import hashlib
import hmac
import json
import math
import threading
import time
from collections import deque
from contextlib import contextmanager
from contextvars import ContextVar
from dataclasses import dataclass
from enum import Enum
from functools import wraps
from types import MappingProxyType
from typing import Any, Callable, Iterator, Mapping, TypeVar


class ArchitectureError(RuntimeError):
    """Base error for the experimental Reaper runtime systems."""


class MissingEffectError(ArchitectureError):
    """Raised when code requests an effect not present in its scope."""


class CapabilityError(ArchitectureError):
    """Raised when an operation lacks an explicit capability grant."""


class MailboxFull(ArchitectureError):
    """Raised when a bounded SovereignUnit mailbox has no free slot."""


@dataclass(frozen=True, slots=True)
class ArchitectureFeature:
    id: int
    name: str
    implementation: str
    boundary: str


ARCHITECTURE_FEATURES: tuple[ArchitectureFeature, ...] = (
    ArchitectureFeature(1, "Citadel Relays", "In-process typed endpoint routing", "No network transport or serialization is implied."),
    ArchitectureFeature(2, "Epochal Harvesting", "Explicit epoch allocation, promotion and bulk release", "Python object reclamation is not hard real-time or guaranteed O(1)."),
    ArchitectureFeature(3, "Indoctrination Effects", "Scoped ContextVar effect bindings and required-effect decorators", "Effects are explicit host API scopes, not compiler-injected rewrites."),
    ArchitectureFeature(4, "Harbinger Tiering", "Call profiling and pluggable hot-call specialization", "No machine-code JIT is included in the Python interpreter."),
    ArchitectureFeature(5, "Synthesis IR", "Versioned canonical semantic IR with stable SHA-256 identifiers", "IR is not yet the parser AST or a native executable backend."),
    ArchitectureFeature(6, "Dragon's Teeth FFI", "Typed callable adapters gated by explicit FFI permissions", "No arbitrary native library loading or automatic C/C++ translation."),
    ArchitectureFeature(7, "Dark Space", "Bounded JSON snapshots with digest and optional HMAC authentication", "Snapshots preserve data, not Python stacks, sockets or exact CPU instruction state."),
    ArchitectureFeature(8, "Sovereign Units", "Sequential actors with bounded mailboxes and snapshot support", "Single-process actors; no distributed consensus or multi-million-thread claim."),
    ArchitectureFeature(9, "Vanguard Sentinel", "Health probes with bounded, explicit recovery callbacks", "Recovery is local and callback-driven; no cloud orchestration is built in."),
)


def architecture_summary() -> str:
    """Return a stable overview of the nine experimental architecture systems."""
    lines = ["Reaper architecture systems (experimental implementation status):"]
    for feature in ARCHITECTURE_FEATURES:
        lines.append(f"{feature.id:02d} | {feature.name} | {feature.implementation}")
        lines.append(f"    Boundary: {feature.boundary}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# 1. Citadel Relays — local reference routing, with no serialization layer.


@dataclass(frozen=True, slots=True)
class _Relay:
    handler: Callable[[Any], Any]
    payload_type: type[Any] | tuple[type[Any], ...] | None


class RelayNetwork:
    """Thread-safe in-process message routing between named endpoints.

    Payload objects are passed by reference. This avoids a serialization copy
    inside this process, but does not make the operation zero-cost and does not
    provide a network transport.
    """

    def __init__(self) -> None:
        self._routes: dict[str, _Relay] = {}
        self._lock = threading.RLock()

    def register(
        self,
        destination: str,
        handler: Callable[[Any], Any],
        *,
        payload_type: type[Any] | tuple[type[Any], ...] | None = None,
    ) -> None:
        if not destination or not destination.strip():
            raise ValueError("destination must be a non-empty name")
        if not callable(handler):
            raise TypeError("handler must be callable")
        with self._lock:
            if destination in self._routes:
                raise ArchitectureError(f"relay destination '{destination}' is already registered")
            self._routes[destination] = _Relay(handler, payload_type)

    def unregister(self, destination: str) -> bool:
        with self._lock:
            return self._routes.pop(destination, None) is not None

    def transmit(self, destination: str, payload: Any) -> Any:
        with self._lock:
            relay = self._routes.get(destination)
        if relay is None:
            raise ArchitectureError(f"unknown relay destination '{destination}'")
        if relay.payload_type is not None and not isinstance(payload, relay.payload_type):
            expected = getattr(relay.payload_type, "__name__", str(relay.payload_type))
            raise TypeError(f"relay '{destination}' expected payload type {expected}")
        return relay.handler(payload)

    def destinations(self) -> tuple[str, ...]:
        with self._lock:
            return tuple(sorted(self._routes))


# ---------------------------------------------------------------------------
# 2. Epochal Harvesting — explicit regions with promotion at epoch boundaries.


@dataclass(frozen=True, slots=True)
class EpochReport:
    generation: int
    allocation_count: int
    reclaimed_count: int
    promoted: tuple[Any, ...]

    @property
    def promoted_count(self) -> int:
        return len(self.promoted)


class EpochArena:
    """A simple region arena for explicit lifetime grouping.

    "allocate" retains references until "harvest". "promote" returns a
    selected value in the harvest report. Clearing the arena drops its own
    references; Python's allocator and finalizers determine actual reclamation.
    """

    def __init__(self) -> None:
        self.generation = 0
        self._allocations: list[Any] = []
        self._allocated_ids: set[int] = set()
        self._promoted: list[Any] = []
        self._promoted_ids: set[int] = set()
        self.last_report: EpochReport | None = None
        self._entered = False

    def allocate(self, value: Any) -> Any:
        self._allocations.append(value)
        self._allocated_ids.add(id(value))
        return value

    def promote(self, value: Any) -> Any:
        identity = id(value)
        if identity not in self._allocated_ids:
            raise ArchitectureError("only values allocated in the active epoch can be promoted")
        if identity not in self._promoted_ids:
            self._promoted.append(value)
            self._promoted_ids.add(identity)
        return value

    def harvest(self) -> EpochReport:
        report = EpochReport(
            generation=self.generation,
            allocation_count=len(self._allocations),
            reclaimed_count=len(self._allocations) - len(self._promoted),
            promoted=tuple(self._promoted),
        )
        self._allocations.clear()
        self._allocated_ids.clear()
        self._promoted.clear()
        self._promoted_ids.clear()
        self.generation += 1
        self.last_report = report
        return report

    def __enter__(self) -> "EpochArena":
        if self._entered:
            raise ArchitectureError("an EpochArena context cannot be entered recursively")
        self._entered = True
        return self

    def __exit__(self, exc_type: Any, exc: Any, traceback: Any) -> None:
        try:
            self.harvest()
        finally:
            self._entered = False


# ---------------------------------------------------------------------------
# 3. Indoctrination Effects — scoped, explicit dynamic effect environments.


_EFFECTS: ContextVar[Mapping[str, Any]] = ContextVar(
    "reaper_effects", default=MappingProxyType({})
)
_F = TypeVar("_F", bound=Callable[..., Any])


@contextmanager
def effect_scope(**effects: Any) -> Iterator[Mapping[str, Any]]:
    """Temporarily add effect bindings; nested scopes inherit outer bindings."""
    if any(not name or not name.strip() for name in effects):
        raise ValueError("effect names must be non-empty")
    merged = dict(_EFFECTS.get())
    merged.update(effects)
    view = MappingProxyType(merged)
    token = _EFFECTS.set(view)
    try:
        yield view
    finally:
        _EFFECTS.reset(token)


def require_effect(name: str) -> Any:
    """Return a scoped effect or fail closed when it has not been granted."""
    if not name or not name.strip():
        raise ValueError("effect name must be non-empty")
    effects = _EFFECTS.get()
    if name not in effects:
        raise MissingEffectError(f"required effect '{name}' is not available in this scope")
    return effects[name]


def requires_effects(*names: str) -> Callable[[_F], _F]:
    """Guard a host function by checking its required scoped effects."""
    if not names or any(not name or not name.strip() for name in names):
        raise ValueError("at least one non-empty effect name is required")

    def decorate(function: _F) -> _F:
        @wraps(function)
        def guarded(*args: Any, **kwargs: Any) -> Any:
            for name in names:
                require_effect(name)
            return function(*args, **kwargs)
        return guarded  # type: ignore[return-value]

    return decorate


# ---------------------------------------------------------------------------
# 4. Harbinger Tiering — measured hot-call dispatch with an optimizer seam.


class ProfileTier(str, Enum):
    COLD = "cold"
    HOT = "hot"
    SPECIALIZED = "specialized"


@dataclass(frozen=True, slots=True)
class ProfileSnapshot:
    name: str
    calls: int
    total_duration_ns: int
    max_duration_ns: int
    tier: ProfileTier


@dataclass(slots=True)
class _ProfileState:
    calls: int = 0
    total_ns: int = 0
    max_ns: int = 0
    specialized: Callable[..., Any] | None = None


class HotspotProfiler:
    """Measure named calls and allow an explicit optimized callable to be plugged in.

    This is an adaptive-dispatch interface, not a machine-code JIT. A native or
    bytecode backend may register a specialization after the site becomes hot.
    """

    def __init__(self, hot_threshold: int = 100) -> None:
        if hot_threshold < 1:
            raise ValueError("hot_threshold must be positive")
        self.hot_threshold = hot_threshold
        self._profiles: dict[str, _ProfileState] = {}
        self._lock = threading.RLock()

    def record(self, name: str, duration_ns: int) -> ProfileSnapshot:
        if not name or not name.strip():
            raise ValueError("profile name must be non-empty")
        if duration_ns < 0:
            raise ValueError("duration_ns cannot be negative")
        with self._lock:
            state = self._profiles.setdefault(name, _ProfileState())
            state.calls += 1
            state.total_ns += duration_ns
            state.max_ns = max(state.max_ns, duration_ns)
            return self._snapshot(name, state)

    def register_specialization(self, name: str, function: Callable[..., Any]) -> None:
        if not callable(function):
            raise TypeError("specialization must be callable")
        with self._lock:
            state = self._profiles.get(name)
            if state is None or state.calls < self.hot_threshold:
                raise ArchitectureError("a specialization can only be registered for a hot call site")
            state.specialized = function

    def invoke(self, name: str, baseline: Callable[..., Any], *args: Any, **kwargs: Any) -> Any:
        if not callable(baseline):
            raise TypeError("baseline must be callable")
        with self._lock:
            state = self._profiles.setdefault(name, _ProfileState())
            target = state.specialized or baseline
        started = time.perf_counter_ns()
        try:
            return target(*args, **kwargs)
        finally:
            self.record(name, time.perf_counter_ns() - started)

    def snapshot(self, name: str) -> ProfileSnapshot:
        with self._lock:
            state = self._profiles.get(name)
            if state is None:
                raise KeyError(name)
            return self._snapshot(name, state)

    def _snapshot(self, name: str, state: _ProfileState) -> ProfileSnapshot:
        if state.specialized is not None:
            tier = ProfileTier.SPECIALIZED
        elif state.calls >= self.hot_threshold:
            tier = ProfileTier.HOT
        else:
            tier = ProfileTier.COLD
        return ProfileSnapshot(name, state.calls, state.total_ns, state.max_ns, tier)


# ---------------------------------------------------------------------------
# 5. Synthesis — versioned canonical IR shared by syntax and data tooling.


_IR_SCALARS = (str, int, float, bool, type(None))


def _validate_scalar(value: Any) -> None:
    if type(value) not in _IR_SCALARS:
        raise TypeError("IR literal and attribute values must be scalar JSON values")
    if isinstance(value, float) and not math.isfinite(value):
        raise ValueError("IR floating-point values must be finite")


@dataclass(frozen=True, slots=True)
class IRNode:
    op: str
    children: tuple["IRNode", ...] = ()
    literal: str | int | float | bool | None = None
    attributes: tuple[tuple[str, str | int | float | bool | None], ...] = ()

    def __post_init__(self) -> None:
        if not self.op or not self.op.strip():
            raise ValueError("IR operation name must be non-empty")
        object.__setattr__(self, "children", tuple(self.children))
        if any(not isinstance(child, IRNode) for child in self.children):
            raise TypeError("IR children must be IRNode instances")
        _validate_scalar(self.literal)
        normalized: list[tuple[str, str | int | float | bool | None]] = []
        seen: set[str] = set()
        for key, value in self.attributes:
            if not key or key in seen:
                raise ValueError("IR attributes must have unique, non-empty names")
            _validate_scalar(value)
            seen.add(key)
            normalized.append((key, value))
        object.__setattr__(self, "attributes", tuple(sorted(normalized)))

    def to_data(self) -> dict[str, Any]:
        return {
            "op": self.op,
            "literal": self.literal,
            "attributes": {key: value for key, value in self.attributes},
            "children": [child.to_data() for child in self.children],
        }


@dataclass(frozen=True, slots=True)
class IRModule:
    roots: tuple[IRNode, ...]
    edition: str = "0.2-experimental"
    format_version: int = 1

    def __post_init__(self) -> None:
        object.__setattr__(self, "roots", tuple(self.roots))
        if any(not isinstance(root, IRNode) for root in self.roots):
            raise TypeError("IR roots must be IRNode instances")
        if not self.edition or not self.edition.strip():
            raise ValueError("IR edition must be non-empty")
        if self.format_version != 1:
            raise ValueError("only IR format version 1 is supported")

    def to_data(self) -> dict[str, Any]:
        return {
            "format": "reaper-semantic-ir",
            "format_version": self.format_version,
            "edition": self.edition,
            "roots": [root.to_data() for root in self.roots],
        }

    def canonical_bytes(self) -> bytes:
        text = json.dumps(self.to_data(), ensure_ascii=False, sort_keys=True,
                          separators=(",", ":"), allow_nan=False)
        return text.encode("utf-8")

    @property
    def digest(self) -> str:
        return hashlib.sha256(self.canonical_bytes()).hexdigest()

    def equivalent_to(self, other: object) -> bool:
        return isinstance(other, IRModule) and self.canonical_bytes() == other.canonical_bytes()


# ---------------------------------------------------------------------------
# 6. Dragon's Teeth — explicit typed FFI adapter and deny-by-default grants.


@dataclass(frozen=True, slots=True)
class FFIPermissions:
    symbols: frozenset[str]

    def __init__(self, symbols: Iterator[str] | tuple[str, ...] | list[str] | set[str] | frozenset[str]) -> None:
        normalized = frozenset(symbols)
        if any(not item or not item.strip() for item in normalized):
            raise ValueError("FFI permission symbols must be non-empty")
        object.__setattr__(self, "symbols", normalized)

    def allows(self, symbol: str) -> bool:
        return symbol in self.symbols or "*" in self.symbols


@dataclass(frozen=True, slots=True)
class ForeignFunctionSpec:
    name: str
    argument_types: tuple[type[Any] | tuple[type[Any], ...], ...]
    result_type: type[Any] | tuple[type[Any], ...]

    def __post_init__(self) -> None:
        if not self.name or not self.name.strip():
            raise ValueError("foreign function name must be non-empty")
        object.__setattr__(self, "argument_types", tuple(self.argument_types))


def _matches_type(value: Any, expected: type[Any] | tuple[type[Any], ...]) -> bool:
    candidates = expected if isinstance(expected, tuple) else (expected,)
    if int in candidates and isinstance(value, bool):
        return False
    return isinstance(value, candidates)


@dataclass(frozen=True, slots=True)
class ForeignFunction:
    spec: ForeignFunctionSpec
    implementation: Callable[..., Any]

    def __post_init__(self) -> None:
        if not callable(self.implementation):
            raise TypeError("foreign implementation must be callable")

    def __call__(self, *arguments: Any) -> Any:
        permissions = require_effect("ffi")
        if not isinstance(permissions, FFIPermissions) or not permissions.allows(self.spec.name):
            raise CapabilityError(f"FFI symbol '{self.spec.name}' is not permitted")
        if len(arguments) != len(self.spec.argument_types):
            raise TypeError(f"{self.spec.name} expects {len(self.spec.argument_types)} arguments")
        for index, (value, expected) in enumerate(zip(arguments, self.spec.argument_types)):
            if not _matches_type(value, expected):
                raise TypeError(f"argument {index + 1} of {self.spec.name} has an invalid type")
        result = self.implementation(*arguments)
        if not _matches_type(result, self.spec.result_type):
            raise TypeError(f"result of {self.spec.name} has an invalid type")
        return result


# ---------------------------------------------------------------------------
# 7. Dark Space — bounded, integrity-checked JSON snapshots.


@dataclass(frozen=True, slots=True)
class StateSnapshot:
    codec_version: int
    payload: bytes
    digest: str
    mac: str | None = None


class SnapshotCodec:
    """Serialize data state without pickle or executable object deserialization."""

    VERSION = 1

    def __init__(self, max_bytes: int = 1_048_576) -> None:
        if max_bytes < 1:
            raise ValueError("max_bytes must be positive")
        self.max_bytes = max_bytes

    @staticmethod
    def _plain_json(value: Any, path: str = "$") -> Any:
        if value is None or type(value) in (str, bool, int):
            return value
        if isinstance(value, float):
            if not math.isfinite(value):
                raise ValueError(f"{path} contains a non-finite number")
            return value
        if isinstance(value, (list, tuple)):
            return [SnapshotCodec._plain_json(item, f"{path}[]") for item in value]
        if isinstance(value, dict):
            if any(not isinstance(key, str) for key in value):
                raise TypeError(f"{path} map keys must be text")
            return {key: SnapshotCodec._plain_json(item, f"{path}.{key}") for key, item in value.items()}
        raise TypeError(f"{path} contains unsupported value type {type(value).__name__}")

    @staticmethod
    def _signed_bytes(version: int, payload: bytes) -> bytes:
        return f"reaper-snapshot-v{version}:".encode("ascii") + payload

    @staticmethod
    def _validate_key(key: bytes | None) -> None:
        if key is not None and (not isinstance(key, bytes) or len(key) < 16):
            raise ValueError("snapshot HMAC key must contain at least 16 bytes")

    def freeze(self, state: Any, *, key: bytes | None = None) -> StateSnapshot:
        self._validate_key(key)
        plain = self._plain_json(state)
        payload = json.dumps(plain, ensure_ascii=False, sort_keys=True,
                             separators=(",", ":"), allow_nan=False).encode("utf-8")
        if len(payload) > self.max_bytes:
            raise ArchitectureError(f"snapshot size limit ({self.max_bytes} bytes) exceeded")
        digest = hashlib.sha256(payload).hexdigest()
        mac = hmac.new(key, self._signed_bytes(self.VERSION, payload), hashlib.sha256).hexdigest() if key else None
        return StateSnapshot(self.VERSION, payload, digest, mac)

    def restore(self, snapshot: StateSnapshot, *, key: bytes | None = None) -> Any:
        self._validate_key(key)
        if not isinstance(snapshot, StateSnapshot):
            raise TypeError("snapshot must be a StateSnapshot")
        if snapshot.codec_version != self.VERSION:
            raise ArchitectureError(f"unsupported snapshot version {snapshot.codec_version}")
        if len(snapshot.payload) > self.max_bytes:
            raise ArchitectureError(f"snapshot size limit ({self.max_bytes} bytes) exceeded")
        digest = hashlib.sha256(snapshot.payload).hexdigest()
        if not hmac.compare_digest(digest, snapshot.digest):
            raise ArchitectureError("snapshot integrity check failed")
        if snapshot.mac is not None:
            if key is None:
                raise CapabilityError("an authenticated snapshot requires its HMAC key")
            expected = hmac.new(key, self._signed_bytes(snapshot.codec_version, snapshot.payload), hashlib.sha256).hexdigest()
            if not hmac.compare_digest(expected, snapshot.mac):
                raise CapabilityError("snapshot authentication failed")
        elif key is not None:
            raise CapabilityError("snapshot does not contain an authentication tag")
        try:
            value = json.loads(snapshot.payload.decode("utf-8"))
        except (UnicodeError, json.JSONDecodeError) as error:
            raise ArchitectureError("snapshot payload is not valid UTF-8 JSON") from error
        return value


# ---------------------------------------------------------------------------
# 8. Sovereign Units — sequential actors with bounded mailboxes.


class SovereignUnit:
    """A local actor with isolated JSON state and a bounded FIFO mailbox.

    A handler receives "(state, message)" and returns "(new_state, result)".
    Failed messages are consumed (not retried) and the prior state is retained.
    """

    def __init__(
        self,
        unit_id: str,
        initial_state: Any,
        handler: Callable[[Any, Any], tuple[Any, Any]],
        *,
        mailbox_capacity: int = 256,
    ) -> None:
        if not unit_id or not unit_id.strip():
            raise ValueError("unit_id must be non-empty")
        if mailbox_capacity < 1:
            raise ValueError("mailbox_capacity must be positive")
        if not callable(handler):
            raise TypeError("handler must be callable")
        self.unit_id = unit_id
        self.mailbox_capacity = mailbox_capacity
        self._state = SnapshotCodec._plain_json(initial_state)
        self._handler = handler
        self._mailbox: deque[Any] = deque()
        self._lock = threading.RLock()
        self._processing = False
        self._hibernated = False
        self.processed_count = 0

    @property
    def passport(self) -> str:
        """Stable public identifier hash; it is not an authentication credential."""
        return hashlib.sha256(("reaper-sovereign-v1:" + self.unit_id).encode("utf-8")).hexdigest()

    @property
    def state(self) -> Any:
        with self._lock:
            if self._hibernated:
                raise ArchitectureError("unit is hibernated")
            return SnapshotCodec._plain_json(self._state)

    @property
    def mailbox_size(self) -> int:
        with self._lock:
            return len(self._mailbox)

    @property
    def is_hibernated(self) -> bool:
        with self._lock:
            return self._hibernated

    def send(self, message: Any) -> None:
        plain = SnapshotCodec._plain_json(message)
        with self._lock:
            if self._hibernated:
                raise ArchitectureError("cannot send to a hibernated unit")
            if len(self._mailbox) >= self.mailbox_capacity:
                raise MailboxFull(f"mailbox capacity ({self.mailbox_capacity}) reached")
            self._mailbox.append(plain)

    def process_one(self) -> tuple[bool, Any]:
        with self._lock:
            if self._hibernated:
                raise ArchitectureError("unit is hibernated")
            if self._processing:
                raise ArchitectureError("unit is already processing a message")
            if not self._mailbox:
                return False, None
            message = self._mailbox.popleft()
            state = SnapshotCodec._plain_json(self._state)
            self._processing = True
        try:
            outcome = self._handler(state, message)
            if not isinstance(outcome, tuple) or len(outcome) != 2:
                raise ArchitectureError("actor handler must return (new_state, result)")
            new_state = SnapshotCodec._plain_json(outcome[0])
            result = outcome[1]
        except Exception:
            with self._lock:
                self._processing = False
            raise
        with self._lock:
            self._state = new_state
            self.processed_count += 1
            self._processing = False
        return True, result

    def drain(self, max_messages: int | None = None) -> list[Any]:
        if max_messages is not None and max_messages < 1:
            raise ValueError("max_messages must be positive")
        results: list[Any] = []
        while max_messages is None or len(results) < max_messages:
            processed, result = self.process_one()
            if not processed:
                break
            results.append(result)
        return results

    def hibernate(self, codec: SnapshotCodec | None = None, *, key: bytes | None = None) -> StateSnapshot:
        codec = codec or SnapshotCodec()
        with self._lock:
            if self._hibernated:
                raise ArchitectureError("unit is already hibernated")
            if self._processing:
                raise ArchitectureError("cannot hibernate while a message is being processed")
            envelope = {
                "unit_id": self.unit_id,
                "state": self._state,
                "mailbox": list(self._mailbox),
                "processed_count": self.processed_count,
            }
            snapshot = codec.freeze(envelope, key=key)
            self._state = None
            self._mailbox.clear()
            self._hibernated = True
            return snapshot

    @classmethod
    def awaken(
        cls,
        snapshot: StateSnapshot,
        handler: Callable[[Any, Any], tuple[Any, Any]],
        *,
        codec: SnapshotCodec | None = None,
        key: bytes | None = None,
        mailbox_capacity: int = 256,
    ) -> "SovereignUnit":
        payload = (codec or SnapshotCodec()).restore(snapshot, key=key)
        if not isinstance(payload, dict) or not {"unit_id", "state", "mailbox", "processed_count"}.issubset(payload):
            raise ArchitectureError("snapshot does not contain a SovereignUnit envelope")
        mailbox = payload["mailbox"]
        processed_count = payload["processed_count"]
        if not isinstance(mailbox, list) or isinstance(processed_count, bool) or not isinstance(processed_count, int) or processed_count < 0:
            raise ArchitectureError("SovereignUnit snapshot metadata is invalid")
        if len(mailbox) > mailbox_capacity:
            raise ArchitectureError("restored mailbox exceeds configured capacity")
        unit = cls(payload["unit_id"], payload["state"], handler, mailbox_capacity=mailbox_capacity)
        unit._mailbox.extend(SnapshotCodec._plain_json(message) for message in mailbox)
        unit.processed_count = processed_count
        return unit


# ---------------------------------------------------------------------------
# 9. Vanguard Sentinel — deterministic health probes and bounded recovery.


@dataclass(frozen=True, slots=True)
class HealthReport:
    name: str
    healthy: bool
    recovered: bool
    detail: str
    recovery_count: int


@dataclass(slots=True)
class _Watch:
    probe: Callable[[], bool]
    recover: Callable[[], Any]
    max_recoveries: int
    recovery_count: int = 0


class VanguardSentinel:
    """Run registered health probes and invoke explicit local recovery hooks."""

    def __init__(self) -> None:
        self._watches: dict[str, _Watch] = {}
        self._lock = threading.RLock()
        self._inspection_lock = threading.Lock()

    def watch(
        self,
        name: str,
        probe: Callable[[], bool],
        recover: Callable[[], Any],
        *,
        max_recoveries: int = 1,
    ) -> None:
        if not name or not name.strip():
            raise ValueError("watch name must be non-empty")
        if not callable(probe) or not callable(recover):
            raise TypeError("probe and recover must be callable")
        if max_recoveries < 0:
            raise ValueError("max_recoveries cannot be negative")
        with self._lock:
            if name in self._watches:
                raise ArchitectureError(f"watch '{name}' is already registered")
            self._watches[name] = _Watch(probe, recover, max_recoveries)

    def inspect(self) -> tuple[HealthReport, ...]:
        # Serialize inspections so concurrent polls cannot exceed a recovery budget.
        with self._inspection_lock:
            with self._lock:
                watches = tuple(self._watches.items())
            reports: list[HealthReport] = []
            for name, watch in watches:
                try:
                    healthy = bool(watch.probe())
                    detail = "healthy" if healthy else "health probe reported unhealthy"
                except Exception as error:
                    healthy = False
                    detail = f"health probe raised {type(error).__name__}: {error}"
                recovered = False
                if not healthy and watch.recovery_count < watch.max_recoveries:
                    watch.recovery_count += 1
                    try:
                        watch.recover()
                        recovered = True
                    except Exception as error:
                        detail += f"; recovery raised {type(error).__name__}: {error}"
                reports.append(HealthReport(name, healthy, recovered, detail, watch.recovery_count))
            return tuple(reports)
