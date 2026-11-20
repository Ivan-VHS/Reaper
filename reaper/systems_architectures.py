"""Read-only CPU, MCU and virtual-ISA target capability matrix."""
from __future__ import annotations

import argparse
import json
import shutil
import sys
from pathlib import Path
from typing import Any, Callable

SCHEMA = "systems-architecture-matrix/v1"
EXPECTED_COUNT = 14
PROJECT_PROFILES = ("pytyliki", "reaper", "oplague")


def load_matrix(path: str | Path | None = None) -> dict[str, Any]:
    source = Path(path) if path is not None else Path(__file__).with_name("systems_architectures.json")
    try:
        data = json.loads(source.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        raise ValueError(f"cannot read systems-architecture matrix: {error}") from error
    validate_matrix(data)
    return data


def validate_matrix(data: Any) -> int:
    if not isinstance(data, dict) or data.get("schema") != SCHEMA:
        raise ValueError(f"expected schema {SCHEMA}")
    architectures, profiles = data.get("architectures"), data.get("profiles")
    if not isinstance(architectures, list) or len(architectures) != EXPECTED_COUNT:
        raise ValueError(f"catalogue must contain exactly {EXPECTED_COUNT} architectures")
    if not isinstance(profiles, dict) or not profiles:
        raise ValueError("profiles must be a non-empty object")
    if set(profiles) != set(PROJECT_PROFILES):
        raise ValueError(f"profiles must be exactly {PROJECT_PROFILES}")
    ids, indices, names = set(), set(), set()
    for item in architectures:
        if not isinstance(item, dict):
            raise ValueError("architecture entries must be objects")
        identifier, index, name = item.get("id"), item.get("index"), item.get("name")
        if not isinstance(identifier, str) or not identifier or identifier in ids:
            raise ValueError(f"missing or duplicate architecture id: {identifier!r}")
        if type(index) is not int or not 1 <= index <= EXPECTED_COUNT or index in indices:
            raise ValueError(f"invalid or duplicate architecture index: {index!r}")
        if not isinstance(name, str) or not name or name.casefold() in names:
            raise ValueError(f"missing or duplicate architecture name: {name!r}")
        if type(item.get("word_bits")) is not int or item["word_bits"] not in {8, 16, 32, 64, 128}:
            raise ValueError(f"{name}: invalid word_bits")
        for field in ("family", "vendor", "class", "pointer_model", "endianness", "execution_model"):
            if not isinstance(item.get(field), str) or not item[field]:
                raise ValueError(f"{name}: missing {field}")
        for field in ("abi", "commands", "tags"):
            values = item.get(field)
            if not isinstance(values, list) or not all(isinstance(value, str) and value for value in values):
                raise ValueError(f"{name}: invalid {field}")
            if field == "tags" and not values:
                raise ValueError(f"{name}: tags cannot be empty")
        decoration = item.get("windows_inf_decoration")
        if decoration is not None and (not isinstance(decoration, str) or not decoration.startswith("NT")):
            raise ValueError(f"{name}: invalid Windows INF decoration")
        ids.add(identifier)
        indices.add(index)
        names.add(name.casefold())
    if indices != set(range(1, EXPECTED_COUNT + 1)):
        raise ValueError(f"architecture indices must cover 1..{EXPECTED_COUNT}")
    for profile, tags in profiles.items():
        if not isinstance(tags, list) or not tags or not all(isinstance(tag, str) and tag for tag in tags):
            raise ValueError(f"invalid profile {profile!r}")
    return len(architectures)


def find_toolchains(item: dict[str, Any], which: Callable[[str], str | None] = shutil.which) -> dict[str, str]:
    return {command: path for command in item["commands"] if (path := which(command))}


def describe_toolchains(item: dict[str, Any], which: Callable[[str], str | None] = shutil.which) -> tuple[str, dict[str, str]]:
    found = find_toolchains(item, which)
    return ("available" if found else "not-found" if item["commands"] else "not-probed", found)


def select_architectures(
    data: dict[str, Any],
    profile: str | None = None,
    tags: set[str] | None = None,
    available_only: bool = False,
    which: Callable[[str], str | None] = shutil.which,
) -> list[dict[str, Any]]:
    if profile is not None and profile not in data["profiles"]:
        raise ValueError(f"unknown project profile: {profile}")
    preferred = set(data["profiles"].get(profile, [])) if profile else set()
    result: list[dict[str, Any]] = []
    for source in data["architectures"]:
        item = dict(source)
        item_tags = set(item["tags"])
        if tags and not item_tags.intersection(tags):
            continue
        score = len(item_tags.intersection(preferred))
        if profile and not score:
            continue
        state, found = describe_toolchains(item, which)
        if available_only and state != "available":
            continue
        item.update(profile_score=score, toolchain_state=state, toolchains_found=found)
        result.append(item)
    if profile:
        result.sort(key=lambda item: (-item["profile_score"], item["index"]))
    return result


def render_text(items: list[dict[str, Any]]) -> str:
    lines = [f"Systems architecture matrix: {len(items)} result(s)", "-" * 112]
    for item in items:
        found = ", ".join(f"{name}={path}" for name, path in item["toolchains_found"].items()) or item["toolchain_state"]
        score = f" | profile score {item['profile_score']}" if item["profile_score"] else ""
        decoration = f" | INF={item['windows_inf_decoration']}" if item.get("windows_inf_decoration") else ""
        lines.append(
            f"{item['index']:02d}. {item['name']} [{item['family']}/{item['class']}] | "
            f"{item['word_bits']}-bit / {item['endianness']} | toolchain: {found}{decoration}{score}\n"
            f"    ABI: {', '.join(item['abi']) or 'not specified'} | {item['execution_model']}\n"
            f"    tags: {', '.join(item['tags'])}"
        )
    lines.append("PATH-only probe: no compiler execution, installation, compilation, linking, emulation, or hardware modification.")
    lines.append("Windows INF decoration is one compatibility clue, not a complete driver compatibility verdict.")
    return "\n".join(lines)


def main(argv: list[str] | None = None, matrix_path: str | Path | None = None) -> int:
    parser = argparse.ArgumentParser(description="Inspect system architecture profiles and PATH-visible toolchain candidates.")
    parser.add_argument("--verify", action="store_true", help="validate all 14 architecture catalogue positions")
    parser.add_argument("--profile", choices=PROJECT_PROFILES, help="rank architectures for a project profile")
    parser.add_argument("--tag", help="comma-separated architecture capability tags")
    parser.add_argument("--available-only", action="store_true", help="show only profiles with a candidate command found on PATH")
    parser.add_argument("--json", action="store_true", help="emit machine-readable JSON")
    args = parser.parse_args(argv)
    try:
        data = load_matrix(matrix_path)
        if args.verify:
            print(f"Systems architecture matrix: PASS ({validate_matrix(data)} profiles)")
            return 0
        tags = {part.strip() for part in args.tag.split(",") if part.strip()} if args.tag else None
        if args.tag and not tags:
            parser.error("--tag requires a non-empty tag")
        items = select_architectures(data, args.profile, tags, args.available_only)
        if args.json:
            print(json.dumps({"schema": SCHEMA, "profile": args.profile, "results": items}, ensure_ascii=False, indent=2))
        else:
            print(render_text(items))
        return 0
    except (OSError, ValueError) as error:
        print(f"systems-architecture-matrix: FAIL: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
