"""Read-only bridge catalogue for 66 low-level language ecosystems.

This module describes source ecosystems and discovers candidate tools on PATH.
It does not execute compilers or claim that Reaper has those backends.
"""
from __future__ import annotations

import argparse
import json
import shutil
import sys
from pathlib import Path
from typing import Any, Callable

SCHEMA = "reaper-reference-ecosystems/v1"
EXPECTED_COUNT = 66
CATEGORIES = (
    "assembly-isa",
    "virtual-isa",
    "compiler-ir",
    "systems-language",
    "vm-language",
    "hdl",
    "gpu-compute",
    "esoteric",
)
PROFILES = ("reaper", "embedded", "gpu", "hdl", "vm", "stack", "esoteric")


def load_registry(path: str | Path | None = None) -> dict[str, Any]:
    source = Path(path) if path is not None else Path(__file__).with_name("reference_ecosystems.json")
    try:
        data = json.loads(source.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        raise ValueError(f"cannot read reference ecosystem registry: {error}") from error
    validate_registry(data)
    return data


def validate_registry(data: Any) -> int:
    if not isinstance(data, dict) or data.get("schema") != SCHEMA:
        raise ValueError(f"expected schema {SCHEMA}")
    languages = data.get("languages")
    profiles = data.get("profiles")
    if data.get("count") != EXPECTED_COUNT or not isinstance(languages, list) or len(languages) != EXPECTED_COUNT:
        raise ValueError("registry must declare and contain exactly 66 entries")
    if not isinstance(profiles, dict) or not profiles:
        raise ValueError("profiles must be a non-empty object")

    ids: set[str] = set()
    indices: set[int] = set()
    names: set[str] = set()
    all_capabilities: set[str] = set()
    for item in languages:
        if not isinstance(item, dict):
            raise ValueError("ecosystem entries must be objects")
        identifier, index, name = item.get("id"), item.get("index"), item.get("name")
        if not isinstance(identifier, str) or not identifier or identifier in ids:
            raise ValueError(f"missing or duplicate ecosystem id: {identifier!r}")
        if type(index) is not int or not 1 <= index <= EXPECTED_COUNT or index in indices:
            raise ValueError(f"invalid or duplicate source index: {index!r}")
        if not isinstance(name, str) or not name or name.casefold() in names:
            raise ValueError(f"missing or duplicate ecosystem name: {name!r}")
        if item.get("category") not in CATEGORIES:
            raise ValueError(f"{identifier}: invalid category {item.get('category')!r}")
        for field in ("integration_layer", "role", "adapter_state"):
            if not isinstance(item.get(field), str) or not item[field]:
                raise ValueError(f"{identifier}: missing {field}")
        if item["adapter_state"] != "catalogued-only":
            raise ValueError(f"{identifier}: unsupported adapter state")
        for field in ("toolchains", "capabilities", "aliases"):
            values = item.get(field)
            if not isinstance(values, list) or not all(isinstance(value, str) and value for value in values):
                raise ValueError(f"{identifier}: invalid {field}")
        if not item["capabilities"]:
            raise ValueError(f"{identifier}: capabilities must not be empty")
        if len(set(item["toolchains"])) != len(item["toolchains"]):
            raise ValueError(f"{identifier}: duplicate toolchain candidate")
        ids.add(identifier)
        indices.add(index)
        names.add(name.casefold())
        all_capabilities.update(item["capabilities"])

    if indices != set(range(1, EXPECTED_COUNT + 1)):
        raise ValueError("source indices must cover 1..66")
    canonical_names = {
        _normalize_name(item["name"]): item["id"]
        for item in languages
    }
    for item in languages:
        for alias in item["aliases"]:
            owner = canonical_names.get(_normalize_name(alias))
            if owner is not None and owner != item["id"]:
                raise ValueError(f"{item['id']}: alias duplicates another canonical name: {alias!r}")

    for profile, tags in profiles.items():
        if not isinstance(profile, str) or not profile or not isinstance(tags, list) or not tags:
            raise ValueError(f"invalid profile {profile!r}")
        if not all(isinstance(tag, str) and tag for tag in tags):
            raise ValueError(f"{profile}: profile tags must be non-empty strings")
        unknown = set(tags) - all_capabilities
        if unknown:
            raise ValueError(f"{profile}: unknown capability tag(s): {', '.join(sorted(unknown))}")
    return len(languages)


def find_toolchains(
    item: dict[str, Any],
    which: Callable[[str], str | None] = shutil.which,
) -> dict[str, str]:
    """Find candidate executable names without invoking them."""
    return {
        command: path
        for command in item["toolchains"]
        if (path := which(command))
    }


def describe_toolchain(
    item: dict[str, Any],
    which: Callable[[str], str | None] = shutil.which,
) -> tuple[str, dict[str, str]]:
    found = find_toolchains(item, which)
    if found:
        return "available", found
    if item["toolchains"]:
        return "not-found", found
    return "not-probed", found


def _normalize_name(value: str) -> str:
    return "".join(character for character in value.casefold() if character.isalnum())


def resolve_ecosystem(data: dict[str, Any], query: str) -> dict[str, Any] | None:
    needle = _normalize_name(query)
    if not needle:
        return None
    for item in data["languages"]:
        candidates = [item["id"], item["name"], *item["aliases"]]
        if any(_normalize_name(candidate) == needle for candidate in candidates):
            return item
    return None


def select_ecosystems(
    data: dict[str, Any],
    category: str | None = None,
    profile: str | None = None,
    available_only: bool = False,
    which: Callable[[str], str | None] = shutil.which,
) -> list[dict[str, Any]]:
    if category is not None and category not in CATEGORIES:
        raise ValueError(f"unknown ecosystem category: {category}")
    if profile is not None and profile not in data["profiles"]:
        raise ValueError(f"unknown ecosystem profile: {profile}")
    preferred = set(data["profiles"].get(profile, [])) if profile else set()
    result: list[dict[str, Any]] = []
    for source in data["languages"]:
        if category is not None and source["category"] != category:
            continue
        item = dict(source)
        score = len(set(item["capabilities"]).intersection(preferred))
        if profile is not None and score == 0:
            continue
        state, found = describe_toolchain(item, which)
        if available_only and state != "available":
            continue
        item.update(profile_score=score, toolchain_state=state, toolchains_found=found)
        result.append(item)
    if profile is not None:
        result.sort(key=lambda item: (-item["profile_score"], item["index"]))
    return result


def render_text(items: list[dict[str, Any]], profile: str | None = None) -> str:
    heading = f"Reference ecosystems: {len(items)} result(s)"
    if profile:
        heading += f" | profile={profile}"
    lines = [heading, "-" * 96]
    for item in items:
        found = ", ".join(f"{name}={path}" for name, path in item["toolchains_found"].items())
        toolchain = found or item["toolchain_state"]
        score = f" | match={item['profile_score']}" if item["profile_score"] else ""
        lines.append(
            f"{item['index']:02d}. {item['name']} [{item['category']} / {item['integration_layer']}]"
            f"\n    toolchain: {toolchain}{score}"
            f"\n    maps to: {', '.join(item['capabilities'])}"
        )
    lines.append("Discovery is PATH-only. No external compiler, assembler, HDL or GPU tool is executed.")
    lines.append("All 66 entries are catalogued references; native Reaper backend support is not implied.")
    return "\n".join(lines)


def _print_json(items: list[dict[str, Any]], profile: str | None = None) -> None:
    print(json.dumps({
        "schema": SCHEMA,
        "profile": profile,
        "count": len(items),
        "adapter_policy": "catalogued-only",
        "results": items,
    }, ensure_ascii=False, indent=2))


def main(argv: list[str] | None = None, registry_path: str | Path | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="reaper compat",
        description="Inspect the 66 low-level language and toolchain reference ecosystems.",
    )
    commands = parser.add_subparsers(dest="command")
    list_parser = commands.add_parser("list", help="list ecosystems")
    list_parser.add_argument("--category", choices=CATEGORIES)
    list_parser.add_argument("--profile", choices=PROFILES)
    list_parser.add_argument("--available-only", action="store_true")
    list_parser.add_argument("--json", action="store_true")
    show_parser = commands.add_parser("show", help="show one ecosystem by name or alias")
    show_parser.add_argument("name")
    show_parser.add_argument("--json", action="store_true")
    verify_parser = commands.add_parser("verify", help="validate the 66-entry registry")
    verify_parser.add_argument("--quiet", action="store_true")
    args = parser.parse_args(argv)

    try:
        data = load_registry(registry_path)
        if args.command == "verify":
            if not args.quiet:
                print(f"Reference ecosystem registry: PASS ({validate_registry(data)} entries)")
            return 0
        if args.command == "show":
            entry = resolve_ecosystem(data, args.name)
            if entry is None:
                print(f"reaper compat: unknown ecosystem {args.name!r}", file=sys.stderr)
                return 2
            state, found = describe_toolchain(entry)
            entry = dict(entry, toolchain_state=state, toolchains_found=found)
            if args.json:
                _print_json([entry])
            else:
                print(render_text([entry]))
            return 0

        # No explicit subcommand is shorthand for "list".
        category = getattr(args, "category", None)
        profile = getattr(args, "profile", None)
        available_only = getattr(args, "available_only", False)
        items = select_ecosystems(data, category, profile, available_only)
        if getattr(args, "json", False):
            _print_json(items, profile)
        else:
            print(render_text(items, profile))
        return 0
    except (OSError, ValueError) as error:
        print(f"reaper compat: FAIL: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
