"""Build an idempotent HTTP/IPC routing decision without opening a listener."""
from __future__ import annotations

import hashlib
import json
from typing import Any

from .common import ApplicationInputError, require_array, require_object, require_text


def _fingerprint(method: str, path: str, body: Any) -> str:
    canonical = json.dumps({"method": method, "path": path, "body": body},
                           ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def run(payload: dict[str, Any]) -> dict[str, Any]:
    request = require_object(payload.get("request"), "request")
    request_id = require_text(request.get("request_id"), "request.request_id")
    method = require_text(request.get("method"), "request.method").upper()
    path = require_text(request.get("path"), "request.path")
    if not path.startswith("/"):
        raise ApplicationInputError("request.path must start with '/'")
    fingerprint = _fingerprint(method, path, request.get("body"))
    cache = require_object(payload.get("cache", {}), "cache")
    routes_raw = payload.get("routes", [])
    if not isinstance(routes_raw, list):
        raise ApplicationInputError("'routes' must be an array")
    routes = routes_raw

    cached = cache.get(request_id)
    if cached is not None:
        entry = require_object(cached, f"cache[{request_id}]")
        if entry.get("fingerprint") != fingerprint:
            raise ApplicationInputError("idempotency_key_reused_with_different_request")
        if "response" not in entry:
            raise ApplicationInputError("cached idempotency entry has no response")
        return {"decision": "replay", "request_id": request_id, "response": entry["response"],
                "fingerprint": fingerprint, "cache_hit": True}

    route_id = None
    handler = None
    for index, candidate in enumerate(routes):
        route = require_object(candidate, f"routes[{index}]")
        route_method = require_text(route.get("method"), f"routes[{index}].method").upper()
        route_path = require_text(route.get("path"), f"routes[{index}].path")
        if route_method == method and route_path == path:
            route_id = route.get("id", f"route-{index + 1}")
            handler = require_text(route.get("handler"), f"routes[{index}].handler")
            break

    if route_id is None:
        response = {"status": 404, "body": {"error": "route_not_found"}}
        decision = "not_found"
    else:
        response = {"status": 202, "body": {"request_id": request_id, "handler": handler, "payload": request.get("body")}}
        decision = "dispatch_plan"

    return {
        "decision": decision,
        "request_id": request_id,
        "route_id": route_id,
        "response": response,
        "fingerprint": fingerprint,
        "cache_hit": False,
        "dispatch_performed": False,
        "next_cache_entry": {"fingerprint": fingerprint, "response": response},
    }
