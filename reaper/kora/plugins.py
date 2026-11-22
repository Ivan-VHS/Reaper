"""Manifest-backed Kora plugin registry."""

from __future__ import annotations

import json
from dataclasses import dataclass
from importlib.resources import files
from typing import Any

from . import runtime


@dataclass(frozen=True)
class Plugin:
    id: str
    name: str
    domain: str
    functions: tuple[str, ...]


class KoraPluginManager:
    def __init__(self) -> None:
        manifest_path = files(__package__).joinpath("manifest.json")
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))

        if manifest.get("schema") != "reaper.kora.plugin-manifest.v1":
            raise ValueError("unsupported Kora manifest")

        self.plugins = {
            item["id"]: Plugin(
                id=item["id"],
                name=item["name"],
                domain=item["domain"],
                functions=tuple(item["functions"]),
            )
            for item in manifest["plugins"]
        }
        self.enabled = set(self.plugins)

    def list_plugins(self) -> list[dict[str, str | int | bool]]:
        return [
            {
                "id": plugin.id,
                "name": plugin.name,
                "domain": plugin.domain,
                "function_count": len(plugin.functions),
                "enabled": plugin.id in self.enabled,
            }
            for plugin in self.plugins.values()
        ]

    def set_enabled(self, plugin_id: str, enabled: bool) -> bool:
        if plugin_id not in self.plugins:
            raise KeyError(plugin_id)

        if enabled:
            self.enabled.add(plugin_id)
        else:
            self.enabled.discard(plugin_id)

        return bool(enabled)

    def call(self, qualified_name: str, *args: Any, **kwargs: Any) -> Any:
        plugin = next(
            (
                candidate
                for candidate in self.plugins.values()
                if qualified_name in candidate.functions
            ),
            None,
        )
        if plugin is None:
            raise ValueError(f"unknown Kora function: {qualified_name}")

        if plugin.id not in self.enabled:
            raise RuntimeError(f"Kora plugin disabled: {plugin.name}")

        module, function = qualified_name.split(".", 1)
        return runtime.call(module, function, *args, **kwargs)
