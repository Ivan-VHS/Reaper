"""Unified registry and PATH-only discovery for Reaper's low-level ecosystems.

This module deliberately separates catalogue presence from executable support:
finding a tool on PATH does not prove that a target backend, ABI or runtime works.
"""
from __future__ import annotations

import argparse
import json
import shutil
import sys
from pathlib import Path
from typing import Any, Callable

SCHEMA = "systems-ecosystem-matrix/v1"
EXPECTED_COUNT = 40
CATEGORIES = ("isa", "system-language", "hdl", "vm-bytecode", "specialized")
PROJECT_PROFILES = ("reaper", "pytyliki", "oplague")


def load_matrix(path: str | Path | None = None) -> dict[str, Any]:
    source = Path(path) if path is not None else Path(__file__).with_name("systems_ecosystems.json")
    try:
        data = json.loads(source.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        raise ValueError(f"cannot read systems ecosystem matrix: {error}") from error
    validate_matrix(data)
    return data


def validate_matrix(data: Any) -> int:
    if not isinstance(data, dict) or data.get("schema") != SCHEMA:
        raise ValueError(f"expected schema {SCHEMA}")
    entries = data.get("entries")
    categories = data.get("categories")
    profiles = data.get("profiles")
    if not isinstance(entries, list) or len(entries) != EXPECTED_COUNT:
        raise ValueError(f"catalogue must contain exactly {EXPECTED_COUNT} entries")
    if categories != list(CATEGORIES):
        raise ValueError("catalogue categories do not match the canonical category order")
    if not isinstance(profiles, dict) or set(profiles) != set(PROJECT_PROFILES):
        raise ValueError("profiles must define reaper, pytyliki and oplague")
    ids: set[str] = set()
    indices: set[int] = set()
    names: set[str] = set()
    for item in entries:
        if not isinstance(item, dict):
            raise ValueError("ecosystem entries must be objects")
        identifier, index, name = item.get("id"), item.get("index"), item.get("name")
        if not isinstance(identifier, str) or not identifier or identifier in ids:
            raise ValueError(f"missing or duplicate ecosystem id: {identifier!r}")
        if type(index) is not int or not 1 <= index <= EXPECTED_COUNT or index in indices:
            raise ValueError(f"invalid or duplicate ecosystem index: {index!r}")
        if not isinstance(name, str) or not name or name.casefold() in names:
            raise ValueError(f"missing or duplicate ecosystem name: {name!r}")
        if item.get("category") not in CATEGORIES:
            raise ValueError(f"{identifier}: unknown category {item.get('category')!r}")
        for field in ("family", "model", "summary", "standard"):
            if not isinstance(item.get(field), str) or not item[field].strip():
                raise ValueError(f"{identifier}: missing {field}")
        for field in ("commands", "tags"):
            values = item.get(field)
            if not isinstance(values, list):
                raise ValueError(f"{identifier}: {field} must be a list")
            if field == "tags" and not values:
                raise ValueError(f"{identifier}: tags cannot be empty")
            if not all(isinstance(value, str) and value.strip() for value in values):
                raise ValueError(f"{identifier}: invalid {field} value")
            if len(values) != len(set(values)):
                raise ValueError(f"{identifier}: duplicate {field} value")
        ids.add(identifier)
        indices.add(index)
        names.add(name.casefold())
    if indices != set(range(1, EXPECTED_COUNT + 1)):
        raise ValueError(f"ecosystem indices must cover 1..{EXPECTED_COUNT}")
    for profile, tags in profiles.items():
        if not isinstance(tags, list) or not tags or not all(
            isinstance(tag, str) and tag.strip() for tag in tags
        ):
            raise ValueError(f"invalid project profile {profile!r}")
    return len(entries)


def find_toolchains(
    item: dict[str, Any],
    which: Callable[[str], str | None] = shutil.which,
) -> dict[str, str]:
    """Return candidate executable paths without executing any external program."""
    return {
        command: path
        for command in item["commands"]
        if (path := which(command))
    }


def describe_toolchains(
    item: dict[str, Any],
    which: Callable[[str], str | None] = shutil.which,
) -> tuple[str, dict[str, str]]:
    found = find_toolchains(item, which)
    return ("available" if found else "not-found" if item["commands"] else "not-probed", found)


def _normalize(value: str) -> str:
    return value.strip().casefold().replace("_", "-").replace(" ", "-")


def select_ecosystems(
    data: dict[str, Any],
    profile: str | None = None,
    category: str | None = None,
    target: str | None = None,
    available_only: bool = False,
    which: Callable[[str], str | None] = shutil.which,
) -> list[dict[str, Any]]:
    if profile is not None and profile not in data["profiles"]:
        raise ValueError(f"unknown project profile: {profile}")
    if category is not None and category not in CATEGORIES:
        raise ValueError(f"unknown ecosystem category: {category}")
    preferred = set(data["profiles"].get(profile, [])) if profile else set()
    wanted = _normalize(target) if target else None
    result: list[dict[str, Any]] = []
    for source in data["entries"]:
        if category and source["category"] != category:
            continue
        if wanted and wanted not in {_normalize(source["id"]), _normalize(source["name"])}:
            continue
        item = dict(source)
        tags = set(item["tags"])
        score = len(tags.intersection(preferred))
        if profile and score == 0:
            continue
        state, found = describe_toolchains(item, which)
        if available_only and state != "available":
            continue
        item.update(
            profile_score=score,
            toolchain_state=state,
            toolchains_found=found,
            support_boundary="toolchain-discovery-only",
        )
        result.append(item)
    if profile:
        result.sort(key=lambda item: (-item["profile_score"], item["index"]))
    return result


def render_text(items: list[dict[str, Any]]) -> str:
    lines = [f"Systems ecosystem matrix: {len(items)} result(s)", "-" * 112]
    for item in items:
        found = ", ".join(
            f"{name}={path}" for name, path in item["toolchains_found"].items()
        ) or item["toolchain_state"]
        score = f" | profile score {item['profile_score']}" if item["profile_score"] else ""
        lines.append(
            f"{item['index']:02d}. {item['name']} [{item['category']}/{item['family']}] "
            f"| {item['model']} | toolchain: {found}{score}\n"
            f"    {item['summary']}\n"
            f"    standard: {item['standard']} | tags: {', '.join(item['tags'])}"
        )
    lines.append(
        "Boundary: registry and PATH discovery are implemented; foreign compilers, "
        "simulators, VMs and ISA code generators are not bundled or implied."
    )
    lines.append(
        "PATH-only probe: no compiler execution, installation, compilation, linking, "
        "dynamic loading, emulation or hardware modification."
    )
    return "\n".join(lines)


def main(argv: list[str] | None = None, matrix_path: str | Path | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Inspect Reaper's ISA, systems-language, HDL, VM and GPU ecosystem integrations."
    )
    parser.add_argument("--verify", action="store_true", help="validate all 40 catalogue entries")
    parser.add_argument("--profile", choices=PROJECT_PROFILES, help="rank ecosystems for a project profile")
    parser.add_argument("--category", choices=CATEGORIES, help="filter by ecosystem category")
    parser.add_argument("--target", help="select one exact target by name or canonical id")
    parser.add_argument("--available-only", action="store_true", help="show only PATH-visible toolchain candidates")
    parser.add_argument("--json", action="store_true", help="emit machine-readable JSON")
    args = parser.parse_args(argv)
    try:
        data = load_matrix(matrix_path)
        if args.verify:
            counts = {
                category: sum(item["category"] == category for item in data["entries"])
                for category in CATEGORIES
            }
            print(
                f"Systems ecosystem matrix: PASS ({validate_matrix(data)} entries; "
                + ", ".join(f"{name}={count}" for name, count in counts.items())
                + ")"
            )
            return 0
        items = select_ecosystems(
            data, args.profile, args.category, args.target, args.available_only
        )
        if args.target and not items:
            print(f"systems-ecosystem-matrix: unknown or unavailable target {args.target!r}", file=sys.stderr)
            return 1
        if args.json:
            print(json.dumps(
                {"schema": SCHEMA, "profile": args.profile, "category": args.category, "results": items},
                ensure_ascii=False,
                indent=2,
            ))
        else:
            print(render_text(items))
        return 0
    except (OSError, ValueError) as error:
        print(f"systems-ecosystem-matrix: FAIL: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
