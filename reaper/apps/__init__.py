"""Reaper first-party application suite: bounded JSON-in/JSON-out services."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Callable

from . import (
    api_gateway,
    bf_vm,
    dag_runner,
    driver_manifest,
    game_tuner,
    latency_probe,
    ledger_reconcile,
    log_sieve,
    most_build,
    physics_bench,
    secret_patrol,
    span_indexer,
    table_cleaner,
    telemetry_guard,
    text_shield,
)
from .common import ApplicationInputError, require_object

_MANIFEST_PATH = Path(__file__).with_name("manifest.json")
_MANIFEST = json.loads(_MANIFEST_PATH.read_text(encoding="utf-8"))
_HANDLERS: dict[str, Callable[[dict[str, Any]], dict[str, Any]]] = {
    "telemetry_guard": telemetry_guard.run,
    "log_sieve": log_sieve.run,
    "game_tuner": game_tuner.run,
    "table_cleaner": table_cleaner.run,
    "api_gateway": api_gateway.run,
    "secret_patrol": secret_patrol.run,
    "latency_probe": latency_probe.run,
    "dag_runner": dag_runner.run,
    "span_indexer": span_indexer.run,
    "ledger_reconcile": ledger_reconcile.run,
    "driver_manifest": driver_manifest.run,
    "most_build": most_build.run,
    "text_shield": text_shield.run,
    "physics_bench": physics_bench.run,
    "bf_vm": bf_vm.run,
}
_CATALOG = {item["id"]: item for item in _MANIFEST["applications"]}

if set(_CATALOG) != set(_HANDLERS):
    raise RuntimeError("application manifest and executable handler registry differ")


def list_apps() -> dict[str, Any]:
    return {
        "schema": "reaper.application-suite.v1",
        "version": _MANIFEST["version"],
        "count": len(_CATALOG),
        "applications": [_CATALOG[key] for key in sorted(_CATALOG)],
    }


def describe_app(app_id: str) -> dict[str, Any]:
    if not isinstance(app_id, str) or app_id not in _CATALOG:
        raise ApplicationInputError(f"unknown Reaper application: {app_id}")
    return {"schema": "reaper.application-info.v1", **_CATALOG[app_id]}


def run_app(app_id: str, payload: Any) -> dict[str, Any]:
    if not isinstance(app_id, str) or app_id not in _HANDLERS:
        raise ApplicationInputError(f"unknown Reaper application: {app_id}")
    data = require_object(payload)
    result = _HANDLERS[app_id](data)
    return {
        "schema": "reaper.application-result.v1",
        "app_id": app_id,
        "ok": True,
        "result": result,
    }


__all__ = ["ApplicationInputError", "describe_app", "list_apps", "run_app"]
