"""Metadata-only interoperability catalogue for external low-level ecosystems.

This module discovers optional executables on PATH. It never invokes toolchains,
loads foreign code, compiles source or claims that Reaper implements a backend.
"""
from __future__ import annotations

import argparse
import json
import shutil
import sys
from pathlib import Path
from typing import Any, Callable

SCHEMA = "reaper-interop-matrix/v1"
EXPECTED_COUNT = 40
EXPECTED_GROUP_COUNTS = {
    "isa": 7,
    "systems-language": 9,
    "hdl": 5,
    "bytecode-vm": 9,
    "specialized": 10,
}


def load_matrix(path: str | Path | None = None) -> dict[str, Any]:
    source = Path(path) if path is not None else Path(__file__).with_name("interop_matrix.json")
    try:
        data = json.loads(source.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        raise ValueError(f"cannot read interoperability matrix: {error}") from error
    validate_matrix(data)
    return data


def validate_matrix(data: Any) -> int:
    if not isinstance(data, dict) or data.get("schema") != SCHEMA:
        raise ValueError(f"expected schema {SCHEMA}")
    entries = data.get("entries")
    groups = data.get("groups")
    if not isinstance(entries, list) or len(entries) != EXPECTED_COUNT:
        raise ValueError(f"catalogue must contain exactly {EXPECTED_COUNT} entries")
    if not isinstance(groups, dict) or set(groups) != set(EXPECTED_GROUP_COUNTS):
        raise ValueError("catalogue groups do not match the supported group set")
    ids: set[str] = set()
    names: set[str] = set()
    counts = {group: 0 for group in EXPECTED_GROUP_COUNTS}
    for item in entries:
        if not isinstance(item, dict):
            raise ValueError("interoperability entries must be objects")
        identifier, name, group = item.get("id"), item.get("name"), item.get("group")
        if not isinstance(identifier, str) or not identifier or identifier in ids:
            raise ValueError(f"missing or duplicate entry id: {identifier!r}")
        if not isinstance(name, str) or not name or name.casefold() in names:
            raise ValueError(f"missing or duplicate entry name: {name!r}")
        if group not in EXPECTED_GROUP_COUNTS:
            raise ValueError(f"{name}: unknown group {group!r}")
        if not isinstance(item.get("kind"), str) or not item["kind"]:
            raise ValueError(f"{name}: missing kind")
        if not isinstance(item.get("description"), str) or not item["description"]:
            raise ValueError(f"{name}: missing description")
        commands = item.get("commands")
        if not isinstance(commands, list) or not all(
            isinstance(command, str) and command and "/" not in command and chr(92) not in command
            for command in commands
        ):
            raise ValueError(f"{name}: invalid command candidates")
        ids.add(identifier)
        names.add(name.casefold())
        counts[group] += 1
    if counts != EXPECTED_GROUP_COUNTS:
        raise ValueError(f"unexpected group distribution: {counts}")
    if data.get("count") != EXPECTED_COUNT:
        raise ValueError("matrix count field does not match entries")
    return len(entries)


def inspect_toolchains(
    entry: dict[str, Any],
    which: Callable[[str], str | None] = shutil.which,
) -> dict[str, Any]:
    found = {
        command: path
        for command in entry["commands"]
        if (path := which(command)) is not None
    }
    state = "available" if found else "not-found" if entry["commands"] else "metadata-only"
    return {**entry, "toolchain_state": state, "toolchains_found": found}


def select_entries(
    data: dict[str, Any],
    group: str | None = None,
    available_only: bool = False,
    which: Callable[[str], str | None] = shutil.which,
) -> list[dict[str, Any]]:
    if group is not None and group not in EXPECTED_GROUP_COUNTS:
        raise ValueError(f"unknown interoperability group: {group}")
    result = []
    for entry in data["entries"]:
        if group and entry["group"] != group:
            continue
        inspected = inspect_toolchains(entry, which)
        if available_only and inspected["toolchain_state"] != "available":
            continue
        result.append(inspected)
    return result


def render_text(items: list[dict[str, Any]]) -> str:
    lines = [f"Reaper interoperability catalogue: {len(items)} result(s)", "-" * 104]
    for item in items:
        found = ", ".join(f"{name}={path}" for name, path in item["toolchains_found"].items())
        state = found or item["toolchain_state"]
        lines.append(
            f"{item['name']} [{item['group']}/{item['kind']}] | toolchain: {state}\n"
            f"    {item['description']}"
        )
    lines.extend([
        "",
        "Discovery only: Reaper checks executable names on PATH; it does not run, install,",
        "compile, emulate or dynamically load these external tools.",
        "A discovered command is not proof of a supported backend, target ABI or code generation.",
    ])
    return "\n".join(lines)


def main(argv: list[str] | None = None, matrix_path: str | Path | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="reaper interop",
        description="Inspect low-level ecosystem metadata and PATH-visible toolchain candidates.",
    )
    parser.add_argument("action", nargs="?", choices=("list", "verify"), default="list")
    parser.add_argument("--group", choices=tuple(EXPECTED_GROUP_COUNTS))
    parser.add_argument("--available-only", action="store_true")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)
    try:
        data = load_matrix(matrix_path)
        if args.action == "verify":
            print(f"Interoperability catalogue: PASS ({validate_matrix(data)} entries)")
            return 0
        items = select_entries(data, args.group, args.available_only)
        if args.json:
            print(json.dumps({
                "schema": SCHEMA,
                "support_level": data["support_level"],
                "group": args.group,
                "results": items,
            }, ensure_ascii=False, indent=2))
        else:
            print(render_text(items))
        return 0
    except (OSError, ValueError) as error:
        print(f"reaper-interop: FAIL: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
