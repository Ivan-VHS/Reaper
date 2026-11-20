"""Read-only 66-slot systems-language and toolchain capability matrix."""
from __future__ import annotations
import argparse, json, shutil, sys
from pathlib import Path
from typing import Any, Callable

SCHEMA = "systems-language-matrix/v1"
EXPECTED_COUNT = 66

def load_matrix(path: str | Path | None = None) -> dict[str, Any]:
    source = Path(path) if path is not None else Path(__file__).with_name("systems_languages.json")
    try:
        data = json.loads(source.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        raise ValueError(f"cannot read systems-language matrix: {error}") from error
    validate_matrix(data)
    return data

def validate_matrix(data: Any) -> int:
    if not isinstance(data, dict) or data.get("schema") != SCHEMA:
        raise ValueError(f"expected schema {SCHEMA}")
    languages, profiles = data.get("languages"), data.get("profiles")
    if not isinstance(languages, list) or len(languages) != EXPECTED_COUNT:
        raise ValueError("catalogue must contain exactly 66 entries")
    if not isinstance(profiles, dict) or not profiles:
        raise ValueError("profiles must be a non-empty object")
    ids, indices = set(), set()
    for item in languages:
        if not isinstance(item, dict): raise ValueError("language entries must be objects")
        identifier, index = item.get("id"), item.get("index")
        if not isinstance(identifier, str) or not identifier or identifier in ids:
            raise ValueError(f"missing or duplicate language id: {identifier!r}")
        if type(index) is not int or not 1 <= index <= 66 or index in indices:
            raise ValueError(f"invalid or duplicate source index: {index!r}")
        for field in ("name", "family", "status"):
            if not isinstance(item.get(field), str) or not item[field]:
                raise ValueError(f"{identifier}: missing {field}")
        for field in ("commands", "tags"):
            values = item.get(field)
            if not isinstance(values, list) or (field == "tags" and not values) or not all(isinstance(v, str) and v for v in values):
                raise ValueError(f"{identifier}: invalid {field}")
        ids.add(identifier); indices.add(index)
    if indices != set(range(1, 67)): raise ValueError("source indices must cover 1..66")
    for item in languages:
        alias = item.get("alias_of")
        if alias is not None and alias not in ids:
            raise ValueError(f"{item['id']}: alias points to unknown id {alias!r}")
    for name, tags in profiles.items():
        if not isinstance(name, str) or not isinstance(tags, list) or not tags:
            raise ValueError(f"invalid profile {name!r}")
    return len(languages)

def find_toolchains(item: dict[str, Any], which: Callable[[str], str | None] = shutil.which) -> dict[str, str]:
    return {command: path for command in item["commands"] if (path := which(command))}

def describe_toolchain(item: dict[str, Any], which: Callable[[str], str | None] = shutil.which) -> tuple[str, dict[str, str]]:
    found = find_toolchains(item, which)
    return ("available" if found else "not-found" if item["commands"] else "not-probed", found)

def select_languages(data: dict[str, Any], profile: str | None = None, tags: set[str] | None = None,
                     available_only: bool = False, which: Callable[[str], str | None] = shutil.which) -> list[dict[str, Any]]:
    if profile is not None and profile not in data["profiles"]: raise ValueError(f"unknown project profile: {profile}")
    preferred = set(data["profiles"].get(profile, [])) if profile else set()
    result = []
    for source in data["languages"]:
        item = dict(source); item_tags = set(item["tags"])
        if tags and not item_tags.intersection(tags): continue
        score = len(item_tags.intersection(preferred))
        if profile and not score: continue
        state, found = describe_toolchain(item, which)
        if available_only and state != "available": continue
        item.update(profile_score=score, toolchain_state=state, toolchains_found=found)
        result.append(item)
    if profile: result.sort(key=lambda item: (-item["profile_score"], item["index"]))
    return result

def render_text(items: list[dict[str, Any]]) -> str:
    lines = [f"Systems language matrix: {len(items)} result(s)", "-" * 100]
    for item in items:
        detail = ", ".join(f"{key}={value}" for key, value in item["toolchains_found"].items()) or item["toolchain_state"]
        score = f" | profile score {item['profile_score']}" if item["profile_score"] else ""
        lines.append(f"{item['index']:02d}. {item['name']} [{item['family']}/{item['status']}] | toolchain: {detail}{score}\n    features: {', '.join(item['tags'])}")
    lines.append("PATH-only probe: no compiler execution, installation, compilation, dynamic loading, or source modification.")
    return "\n".join(lines)

def main(argv: list[str] | None = None, matrix_path: str | Path | None = None) -> int:
    parser = argparse.ArgumentParser(description="Inspect systems-language toolchains and rank capability profiles.")
    parser.add_argument("--verify", action="store_true", help="validate all 66 catalogue positions")
    parser.add_argument("--profile", choices=("pytyliki", "reaper", "oplague"))
    parser.add_argument("--tag", help="comma-separated capability tags")
    parser.add_argument("--available-only", action="store_true")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)
    try:
        data = load_matrix(matrix_path)
        if args.verify:
            aliases = sum(bool(item.get("alias_of")) for item in data["languages"])
            print(f"Systems language matrix: PASS ({len(data['languages'])} slots; {66-aliases} canonical entries; {aliases} aliases)")
            return 0
        tags = {part.strip() for part in args.tag.split(",") if part.strip()} if args.tag else None
        if args.tag and not tags: parser.error("--tag requires a non-empty tag")
        items = select_languages(data, args.profile, tags, args.available_only)
        if args.json:
            print(json.dumps({"schema": SCHEMA, "profile": args.profile, "results": items}, ensure_ascii=False, indent=2))
        else: print(render_text(items))
        return 0
    except (OSError, ValueError) as error:
        print(f"systems-language-matrix: FAIL: {error}", file=sys.stderr); return 1

if __name__ == "__main__": raise SystemExit(main())
