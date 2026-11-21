#!/usr/bin/env python3
"""Validate the directed 20×20 MOST architecture projection matrix."""
import json
import sys
from itertools import product
from pathlib import Path

SCHEMA = "most.combinatorial-matrix/v1"
BASIS_SIZE = 20
PROJECTION_COUNT = BASIS_SIZE * BASIS_SIZE


def validate(data):
    if not isinstance(data, dict) or data.get("schema") != SCHEMA:
        raise ValueError(f"expected schema {SCHEMA!r}")
    basis = data.get("basis")
    if not isinstance(basis, list) or len(basis) != BASIS_SIZE:
        raise ValueError(f"basis must contain exactly {BASIS_SIZE} elements")
    by_id = {}
    for index, element in enumerate(basis, 1):
        expected = f"E{index:02d}"
        if not isinstance(element, dict) or element.get("id") != expected:
            raise ValueError(f"basis element {index} must have id {expected}")
        for field in ("technical_class", "cultural_qualifier", "action_vector",
                      "action_kind", "architecture_domain", "primary_pipeline_gate"):
            if not isinstance(element.get(field), str) or not element[field].strip():
                raise ValueError(f"{expected} has missing or empty {field}")
        by_id[expected] = element
    projections = data.get("projections")
    if not isinstance(projections, list) or len(projections) != PROJECTION_COUNT:
        actual = len(projections) if isinstance(projections, list) else "not a list"
        raise ValueError(f"projections must contain exactly {PROJECTION_COUNT} records; got {actual}")
    seen_ids, seen_pairs = set(), set()
    for item in projections:
        if not isinstance(item, dict):
            raise ValueError("projection record must be an object")
        pid, row_id, col_id = item.get("id"), item.get("row_id"), item.get("column_id")
        if row_id not in by_id or col_id not in by_id:
            raise ValueError(f"{pid!r} references an unknown basis element")
        expected_id = f"MOST-M20-{int(row_id[1:]):02d}-{int(col_id[1:]):02d}"
        if pid != expected_id:
            raise ValueError(f"projection id mismatch: expected {expected_id}")
        if pid in seen_ids:
            raise ValueError(f"duplicate projection id: {pid}")
        pair = (row_id, col_id)
        if pair in seen_pairs:
            raise ValueError(f"duplicate matrix pair: {row_id} × {col_id}")
        seen_ids.add(pid)
        seen_pairs.add(pair)
        row, col = by_id[row_id], by_id[col_id]
        checks = {
            "source_action": row["action_vector"],
            "target_action": col["action_vector"],
            "source_action_kind": row["action_kind"],
            "target_action_kind": col["action_kind"],
            "domain_path": [row["architecture_domain"], col["architecture_domain"]],
            "pipeline_gate_path": [row["primary_pipeline_gate"], col["primary_pipeline_gate"]],
        }
        for field, expected in checks.items():
            if item.get(field) != expected:
                raise ValueError(f"{pid} {field} does not match the basis")
        if item.get("status") != "specified" or item.get("execution_claim") is not False:
            raise ValueError(f"{pid} must remain specified with execution_claim=false")
        if not isinstance(item.get("intent"), str) or not item["intent"].strip():
            raise ValueError(f"{pid} has no intent description")
    expected_pairs = set(product(by_id, repeat=2))
    missing, extra = expected_pairs - seen_pairs, seen_pairs - expected_pairs
    if missing or extra:
        raise ValueError(f"matrix coverage mismatch: {len(missing)} missing, {len(extra)} extra")
    expected_cardinality = {"basis":20,"rows":20,"columns":20,"projections":400,"diagonal":20,"off_diagonal":380}
    if data.get("cardinality") != expected_cardinality:
        raise ValueError("cardinality metadata does not match the 20×20 product")
    return len(seen_pairs)


def main():
    if len(sys.argv) != 2:
        print("usage: validate_most_matrix.py PATH", file=sys.stderr)
        return 2
    try:
        data = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
        count = validate(data)
    except (OSError, json.JSONDecodeError, TypeError, ValueError, KeyError) as error:
        print(f"MOST matrix: FAIL: {error}", file=sys.stderr)
        return 1
    print(f"MOST matrix: PASS ({count} unique directed projections; 20×20 coverage complete)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
