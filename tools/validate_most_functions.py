#!/usr/bin/env python3
"""Validate the 666-entry MOST function registry and its architecture categories."""
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

    groups = data.get("groups")
    if not isinstance(groups, list) or not groups:
        raise ValueError("groups must be a non-empty array")
    cursor = 1
    group_by_order = {}
    for group in groups:
        start, end = group.get("start"), group.get("end")
        if start != cursor or not isinstance(end, int) or end < cursor:
            raise ValueError(f"gap/overlap in range {group.get('id')}")
        if group.get("count") != end - start + 1:
            raise ValueError(f"wrong range count in {group.get('id')}")
        group_id = group.get("id")
        if not isinstance(group_id, str) or not group_id:
            raise ValueError("group has no stable id")
        for order in range(start, end + 1):
            group_by_order[order] = group_id
        cursor = end + 1
    if cursor != 667:
        raise ValueError("groups do not cover 1..666")

    categories = data.get("architecture_categories")
    if data.get("category_scheme") != "dak-reaper-architecture/v1":
        raise ValueError("unsupported or missing architecture category scheme")
    if not isinstance(categories, list) or not categories:
        raise ValueError("architecture_categories must be a non-empty array")

    category_by_id = {}
    group_category = {}
    for category in categories:
        category_id = category.get("id")
        if not isinstance(category_id, str) or not category_id or category_id in category_by_id:
            raise ValueError(f"missing or duplicate architecture category: {category_id!r}")
        if not isinstance(category.get("title"), str) or not category["title"].strip():
            raise ValueError(f"missing title for category {category_id}")
        if not isinstance(category.get("description"), str) or not category["description"].strip():
            raise ValueError(f"missing description for category {category_id}")
        if not isinstance(category.get("count"), int) or category["count"] < 1:
            raise ValueError(f"invalid count for category {category_id}")
        source_groups = category.get("source_groups")
        if not isinstance(source_groups, list) or not source_groups:
            raise ValueError(f"category {category_id} has no source groups")
        category_by_id[category_id] = category
        for group_id in source_groups:
            if group_id in group_category:
                raise ValueError(f"source group assigned to multiple categories: {group_id}")
            group_category[group_id] = category_id

    known_groups = {group["id"] for group in groups}
    if set(group_category) != known_groups:
        missing = sorted(known_groups - set(group_category))
        unknown = sorted(set(group_category) - known_groups)
        raise ValueError(f"category/group mapping mismatch; missing={missing}, unknown={unknown}")

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
    category_counts = Counter()
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

        source_group = group_by_order[order]
        expected_category = group_category[source_group]
        category_id = item.get("architecture_category")
        if category_id not in category_by_id:
            raise ValueError(f"unknown architecture category at {expected}: {category_id!r}")
        if category_id != expected_category:
            raise ValueError(
                f"wrong architecture category at {expected}: "
                f"expected {expected_category}, got {category_id}"
            )
        category_counts[category_id] += 1

        refs = item.get("source_refs", [])
        if item["implementation_state"] == "planned" and refs:
            raise ValueError(f"planned feature has source evidence at {expected}")
        for ref in refs:
            sid = ref.get("source_id")
            if sid not in by_source or not ref.get("symbols") or not set(ref["symbols"]).issubset(by_source[sid]):
                raise ValueError(f"unmatched source evidence at {expected}")
        domains[item.get("domain", "unknown")] += 1

    for category_id, category in category_by_id.items():
        actual = category_counts[category_id]
        if actual != category["count"]:
            raise ValueError(
                f"wrong category count for {category_id}: "
                f"declared {category['count']}, found {actual}"
            )
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
    for category in data["architecture_categories"]:
        print(f"  {category['id']}: {category['count']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
