"""Built-in plugin host for Reaper's internal product suite."""
from __future__ import annotations
import re
import json
import threading
import time
from pathlib import Path
from dataclasses import asdict, dataclass
from typing import Any, Iterable
from .products import PRODUCTS, ProductError, run_product

@dataclass(frozen=True)
class PluginSpec:
    plugin_id: str
    name: str
    domain: str
    version: str
    description: str
    operation: str
    capabilities: tuple[str, ...]

def _plugin_id(name: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", name.casefold()).strip("-")

PLUGIN_SPECS = tuple(
    PluginSpec(_plugin_id(p.name), p.name, p.domain, "1.0.0", p.purpose, p.primary_service, p.capabilities)
    for p in PRODUCTS
)
_BY_ID = {p.plugin_id: p for p in PLUGIN_SPECS}
_BY_NAME = {p.name.casefold(): p for p in PLUGIN_SPECS}

class PluginError(ValueError):
    """Invalid plugin operation, state transition, or plugin input."""

@dataclass(frozen=True, slots=True)
class PluginExecutionPolicy:
    """Host-owned limits for deterministic, trusted built-in product handlers."""

    max_input_bytes: int = 4 * 1024 * 1024
    max_output_bytes: int = 8 * 1024 * 1024
    max_runtime_ms: int = 30_000
    max_concurrent_per_plugin: int = 4

    def __post_init__(self) -> None:
        bounds = {
            "max_input_bytes": (self.max_input_bytes, 1, 64 * 1024 * 1024),
            "max_output_bytes": (self.max_output_bytes, 1, 128 * 1024 * 1024),
            "max_runtime_ms": (self.max_runtime_ms, 1, 10 * 60 * 1000),
            "max_concurrent_per_plugin": (self.max_concurrent_per_plugin, 1, 64),
        }
        for name, (value, lower, upper) in bounds.items():
            if isinstance(value, bool) or not isinstance(value, int) or not lower <= value <= upper:
                raise PluginError(f"{name} must be an integer in [{lower}, {upper}]")


@dataclass(slots=True)
class _PluginRunStats:
    invocations: int = 0
    successes: int = 0
    failures: int = 0
    in_flight: int = 0
    total_duration_ms: float = 0.0
    max_duration_ms: float = 0.0
    last_duration_ms: float = 0.0
    last_status: str = "never_run"
    last_error: str | None = None


def _encoded_size(value: Any) -> int:
    def encode_default(item: Any) -> str:
        if isinstance(item, Path):
            return str(item)
        raise TypeError(f"unsupported plugin boundary value: {type(item).__name__}")

    try:
        return len(json.dumps(
            value, ensure_ascii=False, sort_keys=True, separators=(",", ":"),
            allow_nan=False, default=encode_default,
        ).encode("utf-8"))
    except (TypeError, ValueError, RecursionError) as error:
        raise PluginError(f"plugin boundary data must be finite JSON-compatible data: {error}") from error


class PluginManager:
    """Manages approved products with bounded dispatch and health metrics.

    Python handlers are synchronous. The runtime budget is an observed deadline:
    the host rejects a late result after return and does not claim to pre-empt it.
    """

    def __init__(
        self,
        enabled: Iterable[str] | None = None,
        *,
        policy: PluginExecutionPolicy | None = None,
    ) -> None:
        self.policy = policy or PluginExecutionPolicy()
        self._enabled = set(_BY_ID) if enabled is None else set()
        if enabled is not None:
            for name in enabled:
                self._enabled.add(self._resolve(name).plugin_id)
        self._lock = threading.RLock()
        self._semaphores = {
            spec.plugin_id: threading.BoundedSemaphore(self.policy.max_concurrent_per_plugin)
            for spec in PLUGIN_SPECS
        }
        self._stats = {spec.plugin_id: _PluginRunStats() for spec in PLUGIN_SPECS}

    def _resolve(self, name: str) -> PluginSpec:
        if not isinstance(name, str):
            raise PluginError(f"plugin name must be text, got {type(name).__name__}")
        key = name.strip().casefold()
        spec = _BY_ID.get(key) or _BY_NAME.get(key)
        if spec is None:
            raise PluginError(f"unknown Reaper plugin: {name!r}")
        return spec

    def list_plugins(self) -> list[dict[str, Any]]:
        rows = []
        with self._lock:
            for spec in PLUGIN_SPECS:
                row = asdict(spec)
                row.update(
                    enabled=spec.plugin_id in self._enabled,
                    host="reaper-python",
                    execution_mode="trusted-builtin",
                    status="enabled" if spec.plugin_id in self._enabled else "disabled",
                )
                rows.append(row)
        return rows

    def get_plugin(self, name: str) -> PluginSpec:
        return self._resolve(name)

    def is_enabled(self, name: str) -> bool:
        with self._lock:
            return self._resolve(name).plugin_id in self._enabled

    def set_enabled(self, name: str, enabled: bool) -> bool:
        spec = self._resolve(name)
        if not isinstance(enabled, bool):
            raise PluginError("enabled state must be boolean")
        with self._lock:
            if enabled:
                self._enabled.add(spec.plugin_id)
            else:
                self._enabled.discard(spec.plugin_id)
        return enabled

    def health(self) -> dict[str, Any]:
        """Return registry readiness and per-product execution metrics."""
        with self._lock:
            plugins = {}
            for spec in PLUGIN_SPECS:
                stats = self._stats[spec.plugin_id]
                plugins[spec.plugin_id] = {
                    "name": spec.name,
                    "enabled": spec.plugin_id in self._enabled,
                    "handler_attached": spec.name in {item.name for item in PRODUCTS},
                    "invocations": stats.invocations,
                    "successes": stats.successes,
                    "failures": stats.failures,
                    "in_flight": stats.in_flight,
                    "last_status": stats.last_status,
                    "last_error": stats.last_error,
                    "last_duration_ms": round(stats.last_duration_ms, 3),
                    "mean_duration_ms": round(stats.total_duration_ms / stats.invocations, 3)
                    if stats.invocations else 0.0,
                    "max_duration_ms": round(stats.max_duration_ms, 3),
                }
            ready = all(item["handler_attached"] for item in plugins.values())
            return {
                "schema": "reaper.plugin-health.v1",
                "status": "ready" if ready else "degraded",
                "live": True,
                "ready": ready,
                "registry_count": len(PLUGIN_SPECS),
                "enabled_count": len(self._enabled),
                "active_invocations": sum(item.in_flight for item in self._stats.values()),
                "policy": {
                    "max_input_bytes": self.policy.max_input_bytes,
                    "max_output_bytes": self.policy.max_output_bytes,
                    "max_runtime_ms": self.policy.max_runtime_ms,
                    "max_concurrent_per_plugin": self.policy.max_concurrent_per_plugin,
                    "deadline_mode": "observed-after-return",
                },
                "plugins": plugins,
            }

    def run(self, name: str, **arguments: Any) -> Any:
        spec = self._resolve(name)
        input_size = _encoded_size(arguments)
        if input_size > self.policy.max_input_bytes:
            raise PluginError(
                f"{spec.name} input exceeds {self.policy.max_input_bytes} bytes"
            )
        started = time.perf_counter()
        semaphore = self._semaphores[spec.plugin_id]
        # Reserve admission and read enabled state atomically with set_enabled().
        with self._lock:
            if spec.plugin_id not in self._enabled:
                raise PluginError(f"plugin {spec.name} is disabled")
            if not semaphore.acquire(blocking=False):
                stats = self._stats[spec.plugin_id]
                stats.failures += 1
                stats.last_status = "concurrency_limited"
                stats.last_error = f"{spec.name} concurrency limit reached"
                raise PluginError(f"{spec.name} concurrency limit reached")
            stats = self._stats[spec.plugin_id]
            stats.invocations += 1
            stats.in_flight += 1
            stats.last_status = "running"
            stats.last_error = None
        try:
            result = run_product(spec.name, spec.operation, **arguments)
            output_size = _encoded_size(result)
            elapsed_ms = (time.perf_counter() - started) * 1000.0
            if output_size > self.policy.max_output_bytes:
                raise PluginError(f"{spec.name} output exceeds {self.policy.max_output_bytes} bytes")
            if elapsed_ms > self.policy.max_runtime_ms:
                raise PluginError(
                    f"{spec.name} exceeded the observed runtime deadline "
                    f"({elapsed_ms:.1f} ms > {self.policy.max_runtime_ms} ms)"
                )
            with self._lock:
                stats.successes += 1
                stats.last_status = "success"
            return result
        except (ProductError, PluginError) as error:
            with self._lock:
                stats.failures += 1
                stats.last_status = "rejected"
                stats.last_error = str(error)[:500]
            raise
        except (TypeError, ValueError, OSError) as error:
            message = f"invalid arguments for {spec.name}: {error}"
            with self._lock:
                stats.failures += 1
                stats.last_status = "error"
                stats.last_error = message[:500]
            raise PluginError(message) from error
        finally:
            elapsed_ms = (time.perf_counter() - started) * 1000.0
            with self._lock:
                stats.in_flight -= 1
                stats.total_duration_ms += elapsed_ms
                stats.last_duration_ms = elapsed_ms
                stats.max_duration_ms = max(stats.max_duration_ms, elapsed_ms)
            semaphore.release()

def list_plugins() -> list[dict[str, Any]]:
    return PluginManager().list_plugins()
