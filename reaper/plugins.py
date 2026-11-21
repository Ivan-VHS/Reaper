"""Built-in plugin host for Reaper's internal product suite."""
from __future__ import annotations
import re
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

class PluginManager:
    """Manages built-in plugins and dispatches only approved product operations."""
    def __init__(self, enabled: Iterable[str] | None = None) -> None:
        self._enabled = set(_BY_ID) if enabled is None else set()
        if enabled is not None:
            for name in enabled:
                self._enabled.add(self._resolve(name).plugin_id)

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
        for spec in PLUGIN_SPECS:
            row = asdict(spec)
            row.update(enabled=spec.plugin_id in self._enabled,
                       host="reaper-python",
                       status="enabled" if spec.plugin_id in self._enabled else "disabled")
            rows.append(row)
        return rows

    def get_plugin(self, name: str) -> PluginSpec:
        return self._resolve(name)

    def is_enabled(self, name: str) -> bool:
        return self._resolve(name).plugin_id in self._enabled

    def set_enabled(self, name: str, enabled: bool) -> bool:
        spec = self._resolve(name)
        if not isinstance(enabled, bool):
            raise PluginError("enabled state must be boolean")
        if enabled:
            self._enabled.add(spec.plugin_id)
        else:
            self._enabled.discard(spec.plugin_id)
        return enabled

    def run(self, name: str, **arguments: Any) -> Any:
        spec = self._resolve(name)
        if spec.plugin_id not in self._enabled:
            raise PluginError(f"plugin {spec.name} is disabled")
        try:
            return run_product(spec.name, spec.operation, **arguments)
        except ProductError:
            raise
        except TypeError as error:
            raise PluginError(f"invalid arguments for {spec.name}: {error}") from error

def list_plugins() -> list[dict[str, Any]]:
    return PluginManager().list_plugins()
