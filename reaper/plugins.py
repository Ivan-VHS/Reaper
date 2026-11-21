"""Versioned plugin host for built-ins and explicitly trusted local extensions.

Discovery reads metadata only. External Python code is imported only after the caller
makes an explicit trust decision. In-process Python extensions are NOT OS-sandboxed.
"""
from __future__ import annotations

import hashlib
import importlib.util
import json
import re
import sys
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Iterable

from .products import PRODUCTS, ProductError, run_product

PLUGIN_SCHEMA = "ivan-vhs.plugin.v1"
PLUGIN_API_VERSION = 1
HOST_VERSION = "0.1.0"
_MAX_MANIFEST_BYTES = 64 * 1024
_MAX_DISCOVERED_PLUGINS = 256
_ID = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
_SEMVER = re.compile(r"^(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)(?:-[0-9A-Za-z.-]+)?(?:\+[0-9A-Za-z.-]+)?$")


@dataclass(frozen=True)
class PluginSpec:
    plugin_id: str
    name: str
    domain: str
    version: str
    description: str
    operation: str
    capabilities: tuple[str, ...]
    api_version: int = PLUGIN_API_VERSION
    source: str = "builtin"
    manifest_path: str = ""
    entrypoint: str = ""


@dataclass(frozen=True)
class PluginContext:
    host_id: str
    host_version: str
    plugin_id: str


class PluginHostAPI:
    """Small SDK context; it deliberately grants no implicit host file or network access."""
    def __init__(self, context: PluginContext) -> None:
        self.context = context
        self._messages: list[str] = []

    def log(self, message: str) -> None:
        self._messages.append(str(message)[:2000])

    @property
    def messages(self) -> tuple[str, ...]:
        return tuple(self._messages)


def _plugin_id(name: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", name.casefold()).strip("-")


PLUGIN_SPECS = tuple(
    PluginSpec(_plugin_id(p.name), p.name, p.domain, "1.0.0", p.purpose,
               p.primary_service, tuple(p.capabilities))
    for p in PRODUCTS
)
_BY_ID = {p.plugin_id: p for p in PLUGIN_SPECS}
_BY_NAME = {p.name.casefold(): p for p in PLUGIN_SPECS}


class PluginError(ValueError):
    """Invalid plugin operation, state transition, manifest, or extension call."""


class PluginManager:
    """Discovers metadata safely and dispatches built-ins or trusted local extensions."""

    def __init__(self, enabled: Iterable[str] | None = None,
                 plugin_dirs: Iterable[str | Path] | None = None) -> None:
        self._enabled = set(_BY_ID) if enabled is None else set()
        if enabled is not None:
            for name in enabled:
                self._enabled.add(self._resolve(name).plugin_id)
        self._external: dict[str, PluginSpec] = {}
        self._loaded: dict[str, tuple[Any, str, PluginHostAPI]] = {}
        self.discovery_errors: list[str] = []
        if plugin_dirs:
            self.discover(plugin_dirs)

    def _resolve(self, name: str) -> PluginSpec:
        if not isinstance(name, str):
            raise PluginError(f"plugin name must be text, got {type(name).__name__}")
        key = name.strip().casefold()
        spec = _BY_ID.get(key) or _BY_NAME.get(key) or self._external.get(key)
        if spec is None:
            spec = next((p for p in self._external.values()
                         if p.name.casefold() == key), None)
        if spec is None:
            raise PluginError(f"unknown Reaper plugin: {name!r}")
        return spec

    @staticmethod
    def _read_manifest(path: Path) -> PluginSpec:
        try:
            if path.is_symlink() or path.stat().st_size > _MAX_MANIFEST_BYTES:
                raise PluginError("manifest is a symlink or exceeds the 64 KiB limit")
            data = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, UnicodeError, json.JSONDecodeError) as error:
            raise PluginError(f"cannot read manifest: {error}") from error
        required = {"schema", "id", "name", "version", "api_version", "host",
                    "domain", "description", "capabilities", "entrypoint"}
        if not isinstance(data, dict):
            raise PluginError("manifest root must be an object")
        missing = required - data.keys()
        if missing:
            raise PluginError(f"manifest missing fields: {', '.join(sorted(missing))}")
        identifier = data["id"]
        if data["schema"] != PLUGIN_SCHEMA:
            raise PluginError(f"unsupported schema: {data['schema']!r}")
        if not isinstance(identifier, str) or not _ID.fullmatch(identifier):
            raise PluginError("plugin id must be lowercase kebab-case")
        if not isinstance(data["name"], str) or not data["name"].strip():
            raise PluginError("plugin name must be non-empty text")
        if not isinstance(data["version"], str) or not _SEMVER.fullmatch(data["version"]):
            raise PluginError("plugin version must use semantic versioning")
        if type(data["api_version"]) is not int or data["api_version"] != PLUGIN_API_VERSION:
            raise PluginError(f"unsupported plugin API version: {data['api_version']!r}")
        if not isinstance(data["host"], dict) or data["host"].get("id") != "reaper":
            raise PluginError("manifest host.id must be 'reaper'")
        for field in ("domain", "description"):
            if not isinstance(data[field], str) or not data[field].strip():
                raise PluginError(f"manifest {field} must be non-empty text")
        capabilities = data["capabilities"]
        if (not isinstance(capabilities, list) or len(capabilities) > 32
                or any(not isinstance(v, str) or not v.strip() for v in capabilities)):
            raise PluginError("capabilities must contain at most 32 non-empty strings")
        entrypoint = data["entrypoint"]
        if not isinstance(entrypoint, str) or ":" not in entrypoint:
            raise PluginError("entrypoint must use 'relative_file.py:create_plugin' form")
        filename, symbol = entrypoint.split(":", 1)
        relative = Path(filename)
        if (not filename or relative.is_absolute() or ".." in relative.parts
                or relative.suffix != ".py"
                or not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", symbol)):
            raise PluginError("entrypoint must reference a local Python file and valid factory")
        root = path.parent.resolve()
        target = (root / relative).resolve()
        if root not in target.parents or not target.is_file():
            raise PluginError("entrypoint must exist inside the plugin package directory")
        return PluginSpec(identifier, data["name"].strip(), data["domain"].strip(),
                          data["version"], data["description"].strip(), "execute",
                          tuple(capabilities), data["api_version"], "external",
                          str(path.resolve()), entrypoint)

    def discover(self, directories: Iterable[str | Path]) -> list[dict[str, Any]]:
        """Find plugin.json manifests without importing or executing extension code."""
        paths: list[Path] = []
        for item in directories:
            root = Path(item).expanduser()
            if root.is_file() and root.name == "plugin.json":
                paths.append(root)
            elif root.is_dir():
                paths.extend(sorted(root.rglob("plugin.json")))
            if len(paths) >= _MAX_DISCOVERED_PLUGINS:
                paths = paths[:_MAX_DISCOVERED_PLUGINS]
                break
        for path in paths:
            try:
                spec = self._read_manifest(path)
                if spec.plugin_id in _BY_ID or spec.plugin_id in self._external:
                    raise PluginError(f"duplicate plugin id: {spec.plugin_id}")
                if any(p.name.casefold() == spec.name.casefold()
                       for p in self._external.values()):
                    raise PluginError(f"duplicate plugin name: {spec.name}")
                self._external[spec.plugin_id] = spec
                self._enabled.discard(spec.plugin_id)
            except PluginError as error:
                self.discovery_errors.append(f"{path}: {error}")
        return [asdict(p) for p in self._external.values()]

    def list_plugins(self) -> list[dict[str, Any]]:
        rows = []
        for spec in (*PLUGIN_SPECS, *self._external.values()):
            loaded = spec.plugin_id in self._loaded
            enabled = spec.plugin_id in self._enabled
            row = asdict(spec)
            row.update(enabled=enabled, loaded=loaded, host="reaper-python",
                       status="loaded" if loaded else ("enabled" if enabled else "disabled"))
            rows.append(row)
        return rows

    def get_plugin(self, name: str) -> PluginSpec:
        return self._resolve(name)

    def is_enabled(self, name: str) -> bool:
        return self._resolve(name).plugin_id in self._enabled

    def is_loaded(self, name: str) -> bool:
        return self._resolve(name).plugin_id in self._loaded

    def set_enabled(self, name: str, enabled: bool) -> bool:
        spec = self._resolve(name)
        if not isinstance(enabled, bool):
            raise PluginError("enabled state must be boolean")
        if enabled:
            self._enabled.add(spec.plugin_id)
        else:
            self.unload(spec.plugin_id)
            self._enabled.discard(spec.plugin_id)
        return enabled

    def load(self, name: str, *, trusted: bool = False) -> None:
        """Import one extension after an explicit user trust decision.

        Python runs in-process with normal OS privileges; this is not a sandbox.
        """
        spec = self._resolve(name)
        if spec.source != "external":
            return
        if not trusted:
            raise PluginError("review extension source and pass trusted=True to execute it")
        if spec.plugin_id not in self._enabled:
            raise PluginError(f"plugin {spec.name} is disabled")
        if spec.plugin_id in self._loaded:
            return
        root = Path(spec.manifest_path).parent.resolve()
        filename, factory_name = spec.entrypoint.split(":", 1)
        target = (root / filename).resolve()
        if root not in target.parents or not target.is_file():
            raise PluginError("extension entrypoint escaped its package directory")
        module_name = "_reaper_ext_" + spec.plugin_id.replace("-", "_") + "_" + hashlib.sha256(
            target.read_bytes()).hexdigest()[:12]
        module_spec = importlib.util.spec_from_file_location(module_name, target)
        if module_spec is None or module_spec.loader is None:
            raise PluginError(f"cannot import extension entrypoint: {target}")
        module = importlib.util.module_from_spec(module_spec)
        sys.modules[module_name] = module
        api = PluginHostAPI(PluginContext("reaper", HOST_VERSION, spec.plugin_id))
        try:
            module_spec.loader.exec_module(module)
            factory = getattr(module, factory_name, None)
            if not callable(factory):
                raise PluginError(f"factory {factory_name!r} is not callable")
            instance = factory(api)
            if not callable(getattr(instance, "run", None)):
                raise PluginError("factory must return an object with run(operation, arguments)")
            on_load = getattr(instance, "on_load", None)
            if callable(on_load):
                on_load(api.context)
            self._loaded[spec.plugin_id] = (instance, module_name, api)
        except Exception as error:
            sys.modules.pop(module_name, None)
            if isinstance(error, PluginError):
                raise
            raise PluginError(f"extension {spec.name} failed to load: {error}") from error

    def unload(self, name: str) -> None:
        spec = self._resolve(name)
        loaded = self._loaded.pop(spec.plugin_id, None)
        if loaded is None:
            return
        instance, module_name, api = loaded
        try:
            callback = getattr(instance, "on_unload", None)
            if callable(callback):
                callback(api.context)
        except Exception as error:
            raise PluginError(f"extension {spec.name} failed during unload: {error}") from error
        finally:
            sys.modules.pop(module_name, None)

    def run(self, name: str, **arguments: Any) -> Any:
        spec = self._resolve(name)
        if spec.plugin_id not in self._enabled:
            raise PluginError(f"plugin {spec.name} is disabled")
        if spec.source == "external":
            loaded = self._loaded.get(spec.plugin_id)
            if loaded is None:
                raise PluginError(f"plugin {spec.name} is not loaded; call load(..., trusted=True) first")
            try:
                result = loaded[0].run(spec.operation, dict(arguments))
                json.dumps(result, ensure_ascii=False)
                return result
            except Exception as error:
                if isinstance(error, PluginError):
                    raise
                raise PluginError(f"plugin {spec.name} failed: {error}") from error
        try:
            return run_product(spec.name, spec.operation, **arguments)
        except ProductError:
            raise
        except TypeError as error:
            raise PluginError(f"invalid arguments for {spec.name}: {error}") from error

    def emit(self, event: str, payload: dict[str, Any] | None = None) -> dict[str, Any]:
        """Publish JSON-compatible events to currently loaded, enabled extensions."""
        if not isinstance(event, str) or not 1 <= len(event) <= 80:
            raise PluginError("event name must contain 1-80 characters")
        data = {} if payload is None else dict(payload)
        json.dumps(data, ensure_ascii=False)
        results = {}
        for plugin_id, (instance, _module_name, _api) in tuple(self._loaded.items()):
            if plugin_id not in self._enabled:
                continue
            callback = getattr(instance, "on_event", None)
            if callable(callback):
                try:
                    result = callback(event, data)
                    json.dumps(result, ensure_ascii=False)
                    results[plugin_id] = result
                except Exception as error:
                    raise PluginError(f"plugin {plugin_id} failed on event {event}: {error}") from error
        return results


def list_plugins() -> list[dict[str, Any]]:
    return PluginManager().list_plugins()
