#!/usr/bin/env python3
"""Validate the MOST feature registry for unique IDs and acyclic dependencies."""
import json, sys
from pathlib import Path

def validate(data):
    features = data.get("features", []); by_id = {}
    for feature in features:
        feature_id = feature.get("id")
        if not feature_id or feature_id in by_id: raise ValueError(f"missing or duplicate feature id: {feature_id!r}")
        if feature.get("status") not in {"planned","specified","implemented","verified","deprecated"}:
            raise ValueError(f"invalid status for {feature_id}")
        by_id[feature_id] = feature
    for feature in features:
        for dependency in feature.get("depends_on", []):
            if dependency not in by_id: raise ValueError(f"{feature['id']} depends on unknown {dependency}")
    visiting, visited = set(), set()
    def visit(feature_id):
        if feature_id in visiting: raise ValueError(f"dependency cycle at {feature_id}")
        if feature_id in visited: return
        visiting.add(feature_id)
        for dependency in by_id[feature_id].get("depends_on", []): visit(dependency)
        visiting.remove(feature_id); visited.add(feature_id)
    for feature_id in by_id: visit(feature_id)
    return len(by_id)

if __name__ == "__main__":
    try: count = validate(json.loads(Path(sys.argv[1]).read_text(encoding="utf-8")))
    except (OSError, ValueError, KeyError, IndexError) as error:
        print(f"MOST registry: FAIL: {error}", file=sys.stderr); raise SystemExit(1)
    print(f"MOST registry: PASS ({count} unique features; dependency graph is acyclic)")
