#!/usr/bin/env python3
"""Build a deterministic, dependency-aware implementation plan for MOST features."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from validate_features import validate

DONE = {"implemented", "verified"}


def build_plan(data: dict, targets: list[str] | None = None) -> dict:
    """Return dependency closure, topological work order, and current blockers."""
    validate(data)
    features = data["features"]
    by_id = {item["id"]: item for item in features}
    if targets:
        unknown = sorted(set(targets) - by_id.keys())
        if unknown:
            raise ValueError("unknown target feature(s): " + ", ".join(unknown))
        selected = set()

        def include(feature_id: str) -> None:
            if feature_id in selected:
                return
            selected.add(feature_id)
            for dependency in by_id[feature_id].get("depends_on", []):
                include(dependency)

        for target in targets:
            include(target)
    else:
        selected = set(by_id)

    ordered: list[str] = []
    visited: set[str] = set()

    def visit(feature_id: str) -> None:
        if feature_id in visited:
            return
        for dependency in by_id[feature_id].get("depends_on", []):
            if dependency in selected:
                visit(dependency)
        visited.add(feature_id)
        ordered.append(feature_id)

    for item in features:
        if item["id"] in selected:
            visit(item["id"])

    work = []
    for feature_id in ordered:
        item = by_id[feature_id]
        if item.get("status") in DONE:
            continue
        blockers = [
            dependency for dependency in item.get("depends_on", [])
            if by_id[dependency].get("status") not in DONE
        ]
        work.append({
            "id": feature_id,
            "name": item["name"],
            "area": item["area"],
            "status": item["status"],
            "ready": not blockers,
            "blocked_by": blockers,
            "acceptance": item.get("acceptance", []),
        })

    return {
        "schema": "most.implementation-plan/v1",
        "language": data.get("language", "MOST"),
        "edition": data.get("edition", "unknown"),
        "selected": [feature_id for feature_id in ordered],
        "work_order": [item["id"] for item in work],
        "ready": [item["id"] for item in work if item["ready"]],
        "blocked": [item["id"] for item in work if not item["ready"]],
        "items": work,
        "summary": {
            "selected": len(ordered),
            "completed": sum(by_id[key].get("status") in DONE for key in ordered),
            "remaining": len(work),
            "ready": sum(item["ready"] for item in work),
            "blocked": sum(not item["ready"] for item in work),
        },
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("registry", type=Path, nargs="?", default=Path("language/features.json"))
    parser.add_argument("--target", action="append", dest="targets",
                        help="feature ID to plan; repeat to combine targets")
    parser.add_argument("--format", choices=("text", "json"), default="text")
    args = parser.parse_args(argv)
    try:
        data = json.loads(args.registry.read_text(encoding="utf-8"))
        result = build_plan(data, args.targets)
    except (OSError, json.JSONDecodeError, ValueError, KeyError) as error:
        print(f"MOST planner: FAIL: {error}", file=sys.stderr)
        return 1

    if args.format == "json":
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        summary = result["summary"]
        print(f"MOST {result['edition']} implementation plan")
        print(f"Selected: {summary['selected']} | remaining: {summary['remaining']} | "
              f"ready: {summary['ready']} | blocked: {summary['blocked']}")
        for item in result["items"]:
            state = "READY" if item["ready"] else "BLOCKED by " + ", ".join(item["blocked_by"])
            print(f"{item['id']} [{item['status']}] {state} — {item['name']}")
            for gate in item["acceptance"]:
                print(f"  - {gate}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
