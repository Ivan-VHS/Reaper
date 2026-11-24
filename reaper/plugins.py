"""Built-in plugin host for Reaper's internal product suite."""
from __future__ import annotations

import re
import threading
from dataclasses import asdict, dataclass
from typing import Any, Iterable

from .capabilities import (
    CapabilityAuthority,
    CapabilityDenied,
    CapabilityError,
    CapabilityRequest,
    CapabilityToken,
)
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
    """Dispatches built-ins only while a matching scoped capability is active."""

    def __init__(
        self,
        enabled: Iterable[str] | None = None,
        *,
        authority: CapabilityAuthority | None = None,
        capability_ttl_seconds: int = 3_600,
    ) -> None:
        if isinstance(enabled, str):
            raise PluginError("enabled plugins must be an iterable of complete names, not a string")
        if isinstance(capability_ttl_seconds, bool) or not isinstance(capability_ttl_seconds, int):
            raise PluginError("capability_ttl_seconds must be an integer")
        if not 1 <= capability_ttl_seconds <= 86_400:
            raise PluginError("plugin capability TTL must be within 1..86400 seconds")
        if authority is not None and not isinstance(authority, CapabilityAuthority):
            raise PluginError("authority must be a CapabilityAuthority")
        self._authority = authority or CapabilityAuthority(max_ttl_seconds=capability_ttl_seconds)
        self._owns_authority = authority is None
        if capability_ttl_seconds > self._authority.max_ttl_seconds:
            raise PluginError("plugin capability TTL exceeds authority policy")
        self._capability_ttl_seconds = capability_ttl_seconds
        self._enabled: set[str] = set()
        self._grants: dict[str, CapabilityToken] = {}
        self._lock = threading.RLock()
        names = (spec.name for spec in PLUGIN_SPECS) if enabled is None else enabled
        try:
            for name in names:
                self.set_enabled(name, True)
        except Exception:
            self.close()
            raise

    def _resolve(self, name: str) -> PluginSpec:
        if not isinstance(name, str):
            raise PluginError(f"plugin name must be text, got {type(name).__name__}")
        key = name.strip().casefold()
        spec = _BY_ID.get(key) or _BY_NAME.get(key)
        if spec is None:
            raise PluginError(f"unknown Reaper plugin: {name!r}")
        return spec

    @staticmethod
    def _principal(spec: PluginSpec) -> str:
        return f"reaper-plugin:{spec.plugin_id}"

    @staticmethod
    def _resource(spec: PluginSpec) -> str:
        return f"plugins/{spec.plugin_id}"

    def _issue_grant(self, spec: PluginSpec) -> CapabilityToken:
        request = CapabilityRequest.parse(
            {
                "principal": self._principal(spec),
                "resource": self._resource(spec),
                "actions": ("invoke", spec.operation, *spec.capabilities),
                "ttl_seconds": self._capability_ttl_seconds,
            },
            max_ttl_seconds=self._authority.max_ttl_seconds,
        )
        return self._authority.issue(request)

    def _grant_is_active(self, spec: PluginSpec) -> bool:
        token = self._grants.get(spec.plugin_id)
        if token is None:
            return False
        try:
            self._authority.verify(
                token,
                principal=self._principal(spec),
                resource=self._resource(spec),
                action="invoke",
            )
            self._authority.verify(
                token,
                principal=self._principal(spec),
                resource=self._resource(spec),
                action=spec.operation,
            )
            return True
        except CapabilityDenied:
            return False

    def list_plugins(self) -> list[dict[str, Any]]:
        with self._lock:
            rows = []
            for spec in PLUGIN_SPECS:
                row = asdict(spec)
                active = spec.plugin_id in self._enabled and self._grant_is_active(spec)
                row.update(
                    enabled=active,
                    host="reaper-python",
                    status="enabled" if active else "disabled",
                    capability_grant="active" if active else "absent_or_revoked",
                )
                rows.append(row)
            return rows

    def get_plugin(self, name: str) -> PluginSpec:
        return self._resolve(name)

    def is_enabled(self, name: str) -> bool:
        spec = self._resolve(name)
        with self._lock:
            return spec.plugin_id in self._enabled and self._grant_is_active(spec)

    def set_enabled(self, name: str, enabled: bool) -> bool:
        spec = self._resolve(name)
        if not isinstance(enabled, bool):
            raise PluginError("enabled state must be boolean")
        with self._lock:
            if enabled:
                current = self._grants.get(spec.plugin_id)
                if current is not None and self._grant_is_active(spec):
                    self._enabled.add(spec.plugin_id)
                    return True
                if current is not None:
                    self._authority.revoke(current)
                try:
                    token = self._issue_grant(spec)
                except CapabilityError as error:
                    raise PluginError(f"cannot issue plugin capability for {spec.name}: {error}") from error
                self._grants[spec.plugin_id] = token
                self._enabled.add(spec.plugin_id)
            else:
                self._enabled.discard(spec.plugin_id)
                current = self._grants.pop(spec.plugin_id, None)
                if current is not None:
                    self._authority.revoke(current)
            return enabled

    def revoke_capabilities(self, name: str) -> bool:
        """Revoke one plugin's grant and disable it atomically from this host."""
        spec = self._resolve(name)
        with self._lock:
            self._enabled.discard(spec.plugin_id)
            token = self._grants.pop(spec.plugin_id, None)
            return self._authority.revoke(token) if token is not None else False

    def run(self, name: str, **arguments: Any) -> Any:
        spec = self._resolve(name)
        with self._lock:
            if spec.plugin_id not in self._enabled:
                raise PluginError(f"plugin {spec.name} is disabled")
            token = self._grants.get(spec.plugin_id)
            if token is None:
                self._enabled.discard(spec.plugin_id)
                raise PluginError(f"plugin {spec.name} has no active capability grant")
            try:
                with self._authority.authorized(
                    token,
                    principal=self._principal(spec),
                    resource=self._resource(spec),
                    action="invoke",
                ):
                    self._authority.verify(
                        token,
                        principal=self._principal(spec),
                        resource=self._resource(spec),
                        action=spec.operation,
                    )
                    return run_product(spec.name, spec.operation, **arguments)
            except CapabilityDenied as error:
                self._enabled.discard(spec.plugin_id)
                self._grants.pop(spec.plugin_id, None)
                raise PluginError(f"plugin {spec.name} has no active capability grant") from error
            except ProductError:
                raise
            except TypeError as error:
                raise PluginError(f"invalid arguments for {spec.name}: {error}") from error

    def close(self) -> None:
        """Revoke this manager's grants; close only an authority it owns."""
        with self._lock:
            for token in tuple(self._grants.values()):
                self._authority.revoke(token)
            self._grants.clear()
            self._enabled.clear()
            if self._owns_authority:
                self._authority.close()


def list_plugins() -> list[dict[str, Any]]:
    manager = PluginManager()
    try:
        return manager.list_plugins()
    finally:
        manager.close()
