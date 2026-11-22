"""Structural AST comparison for Reaper source files.

Formatting, comments and source locations are ignored by default. Token kinds,
operators, literal values and tree shape remain part of the comparison.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys
from typing import Any

from .errors import ReaperError
from .parser import Node, parse


def _plain_value(value: Any) -> Any:
    if isinstance(value, tuple):
        return [_plain_value(item) for item in value]
    if isinstance(value, list):
        return [_plain_value(item) for item in value]
    if isinstance(value, dict):
        return {str(key): _plain_value(item) for key, item in sorted(value.items(), key=lambda pair: str(pair[0]))}
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    return repr(value)


def ast_to_data(node: Node, *, include_locations: bool = False) -> dict[str, Any]:
    """Convert a parser node to a stable JSON-compatible structure."""
    result: dict[str, Any] = {
        "kind": node.kind,
        "value": _plain_value(node.value),
        "children": [
            ast_to_data(child, include_locations=include_locations)
            if child is not None else None
            for child in (node.children or [])
        ],
        # Lexemes are intentionally omitted: keyword aliases and whitespace
        # should not create false semantic diffs.
        "token_kind": node.token.kind,
    }
    if include_locations:
        result["location"] = {
            "line": node.token.line,
            "column": node.token.column,
        }
    return result


def diff_data(before: Any, after: Any, path: str = "$") -> list[dict[str, Any]]:
    """Return a deterministic list of structural changes between JSON values."""
    if before == after:
        return []
    if isinstance(before, dict) and isinstance(after, dict):
        changes: list[dict[str, Any]] = []
        for key in sorted(set(before) | set(after)):
            child_path = f"{path}.{key}"
            if key not in before:
                changes.append({"path": child_path, "before": None, "after": after[key], "change": "added"})
            elif key not in after:
                changes.append({"path": child_path, "before": before[key], "after": None, "change": "removed"})
            else:
                changes.extend(diff_data(before[key], after[key], child_path))
        return changes
    if isinstance(before, list) and isinstance(after, list):
        changes = []
        common = min(len(before), len(after))
        for index in range(common):
            changes.extend(diff_data(before[index], after[index], f"{path}[{index}]"))
        for index in range(common, len(before)):
            changes.append({"path": f"{path}[{index}]", "before": before[index], "after": None, "change": "removed"})
        for index in range(common, len(after)):
            changes.append({"path": f"{path}[{index}]", "before": None, "after": after[index], "change": "added"})
        return changes
    return [{"path": path, "before": before, "after": after, "change": "changed"}]


def compare_sources(
    before_source: str,
    after_source: str,
    *,
    before_name: str = "<before>",
    after_name: str = "<after>",
    include_locations: bool = False,
) -> dict[str, Any]:
    """Parse and compare two Reaper source strings."""
    before_ast = ast_to_data(parse(before_source, before_name), include_locations=include_locations)
    after_ast = ast_to_data(parse(after_source, after_name), include_locations=include_locations)
    changes = diff_data(before_ast, after_ast)
    return {
        "schema": "reaper.ast-diff.v1",
        "equal": not changes,
        "before": before_name,
        "after": after_name,
        "include_locations": include_locations,
        "changes": changes,
        "change_count": len(changes),
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Compare Reaper files by parsed AST, not formatting.")
    parser.add_argument("before", type=Path, help="original .rpr file")
    parser.add_argument("after", type=Path, help="updated .rpr file")
    parser.add_argument("--include-locations", action="store_true", help="include line and column in the AST comparison")
    args = parser.parse_args(argv)

    try:
        before_text = args.before.read_text(encoding="utf-8")
        after_text = args.after.read_text(encoding="utf-8")
        report = compare_sources(
            before_text,
            after_text,
            before_name=str(args.before),
            after_name=str(args.after),
            include_locations=args.include_locations,
        )
    except (OSError, UnicodeError, ReaperError, ValueError) as error:
        print(f"reaper-ast-diff: {error}", file=sys.stderr)
        return 2

    print(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True))
    return 0 if report["equal"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
