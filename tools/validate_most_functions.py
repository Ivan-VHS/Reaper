#!/usr/bin/env python3
"""Validate the 666-entry MOST function registry."""
from __future__ import annotations
import json
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_PATH = ROOT / "language" / "functions_666.json"
ALLOWED_IMPL = {"specified_only", "partial_outside_most", "planned"}

def validate(data):
    if not isinstance(data, dict) or data.get("schema") != "most.function-registry/v1":
        raise ValueError("unsupported registry schema")
    items = data.get("functions")
    if data.get("entry_count") != 666 or not isinstance(items, list) or len(items) != 666:
        raise ValueError("registry must contain exactly 666 entries")
    srcs = data.get("source_inventory")
    if not isinstance(srcs, list):
        raise ValueError("source_inventory must be an array")
    by_source = {}
    for source in srcs:
        sid = source.get("id")
        if not sid or sid in by_source or not source.get("repository") or not source.get("path"):
            raise ValueError(f"invalid or duplicate source record: {sid!r}")
        by_source[sid] = set(source.get("symbols", []))
    ids, names, domains = set(), set(), Counter()
    for order, item in enumerate(items, 1):
        expected = f"MOST-FN-{order:03d}"
        if item.get("id") != expected or item.get("order") != order:
            raise ValueError(f"unstable sequence at {expected}")
        if expected in ids:
            raise ValueError(f"duplicate ID: {expected}")
        ids.add(expected)
        name = item.get("name")
        if not isinstance(name, str) or not name.strip() or name in names:
            raise ValueError(f"missing or duplicate name at {expected}")
        names.add(name)
        if item.get("status") not in {"specified", "planned", "implemented", "verified", "deprecated"}:
            raise ValueError(f"invalid status at {expected}")
        if item.get("implementation_state") not in ALLOWED_IMPL:
            raise ValueError(f"invalid implementation state at {expected}")
        if item.get("most_native") is not False:
            raise ValueError(f"MOST native implementation is incorrectly implied at {expected}")
        if not isinstance(item.get("contract"), str) or not item["contract"].strip():
            raise ValueError(f"missing contract at {expected}")
        if not item.get("acceptance"):
            raise ValueError(f"missing acceptance checks at {expected}")
        refs = item.get("source_refs", [])
        if item["implementation_state"] == "planned" and refs:
            raise ValueError(f"planned feature has source evidence at {expected}")
        for ref in refs:
            sid = ref.get("source_id")
            if sid not in by_source or not ref.get("symbols") or not set(ref["symbols"]).issubset(by_source[sid]):
                raise ValueError(f"unmatched source evidence at {expected}")
        domains[item.get("domain", "unknown")] += 1
    cursor = 1
    for group in data.get("groups", []):
        if group.get("start") != cursor or group.get("end", 0) < cursor:
            raise ValueError(f"gap/overlap in range {group.get('id')}")
        if group.get("count") != group["end"] - group["start"] + 1:
            raise ValueError(f"wrong range count in {group.get('id')}")
        cursor = group["end"] + 1
    if cursor != 667:
        raise ValueError("groups do not cover 1..666")
    return len(items), len(srcs), domains

def main():
    path = Path(sys.argv[1]) if len(sys.argv) > 1 else DEFAULT_PATH
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        count, source_count, domains = validate(data)
    except (OSError, json.JSONDecodeError, ValueError, TypeError, KeyError) as exc:
        print(f"MOST registry: FAIL: {exc}", file=sys.stderr)
        return 1
    print(f"MOST registry: PASS ({count} entries, {source_count} source records)")
    for domain, total in sorted(domains.items()):
        print(f"  {domain}: {total}")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
