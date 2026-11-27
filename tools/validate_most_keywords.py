#!/usr/bin/env python3
"""Validate that the МОСТ alias manifest matches Python and C17 lexers."""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from reaper.lexer import KEYWORD_ALIASES, KEYWORDS  # noqa: E402


def _initializer_body(source: str, declaration: str) -> str | None:
    """Return a C initializer body while allowing ordinary source formatting."""
    match = re.search(
        declaration + r"\s*=\s*\{(?P<body>.*?)\}\s*;",
        source,
        flags=re.DOTALL,
    )
    return match.group("body") if match is not None else None


def validate(root: Path = ROOT) -> list[str]:
    errors: list[str] = []
    manifest_path = root / "language" / "most_keyword_aliases.json"
    profile_path = root / "language" / "most_russian_native_profile.json"
    c_path = root / "src" / "lexer.c"

    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        profile = json.loads(profile_path.read_text(encoding="utf-8"))
        c_source = c_path.read_text(encoding="utf-8")
    except (OSError, json.JSONDecodeError) as exc:
        return [f"cannot load МОСТ contract: {exc}"]

    entries = manifest.get("aliases")
    if not isinstance(entries, list):
        return ["manifest.aliases must be a list"]

    expected = {entry["source"]: entry["canonical"] for entry in entries}
    if len(expected) != len(entries):
        errors.append("manifest contains duplicate source spellings")
    if expected != KEYWORD_ALIASES:
        errors.append("Python KEYWORD_ALIASES differs from the JSON manifest")

    runtime_canonical = {
        entry["canonical"] for entry in entries if entry.get("support") == "runtime"
    }
    reserved_canonical = {
        entry["canonical"] for entry in entries if entry.get("support") == "lexical_reserved"
    }
    if not runtime_canonical.issubset(KEYWORDS):
        errors.append("runtime aliases must map to existing Python parser keywords")
    if runtime_canonical | reserved_canonical != set(expected.values()):
        errors.append("manifest support classes do not cover all canonical aliases")

    alias_declaration = (
        r"static\s+const\s+ReaperKeywordAlias\s+russian_aliases\s*\[\s*\]"
    )
    alias_body = _initializer_body(c_source, alias_declaration)
    if alias_body is None:
        errors.append("C17 alias table is missing")
    else:
        alias_pairs = re.findall(
            r'\{\s*"([^"]+)"\s*,\s*"([^"]+)"\s*\}',
            alias_body,
        )
        native_aliases = dict(alias_pairs)
        if len(native_aliases) != len(alias_pairs):
            errors.append("C17 alias table contains duplicate source spellings")
        if native_aliases != expected:
            errors.append("C17 russian_aliases differs from the JSON manifest")

    keyword_declaration = (
        r"static\s+const\s+char\s*\*\s*const\s+keywords\s*\[\s*\]"
    )
    keyword_body = _initializer_body(c_source, keyword_declaration)
    if keyword_body is None:
        errors.append("C17 keyword table is missing")
    else:
        native_keywords = set(re.findall(r'"([^"]+)"', keyword_body))
        if not set(expected).issubset(native_keywords):
            errors.append("one or more Russian aliases are absent from C17 keywords")
        if not set(expected.values()).issubset(native_keywords):
            errors.append("one or more canonical keywords are absent from C17 keywords")

    if manifest.get("schema") != "most-keyword-aliases/v1":
        errors.append("unsupported alias manifest schema")
    if len(entries) != 102:
        errors.append(f"expected 102 aliases, found {len(entries)}")
    if sum(entry.get("support") == "runtime" for entry in entries) != 38:
        errors.append("expected exactly 38 runtime-supported aliases")
    if sum(entry.get("support") == "lexical_reserved" for entry in entries) != 64:
        errors.append("expected exactly 64 lexically reserved aliases")

    principles = profile.get("principles")
    if (
        profile.get("principle_count") != 20
        or not isinstance(principles, list)
        or len(principles) != 20
    ):
        errors.append("Russian native profile must contain exactly 20 principles")
    elif len({item.get("id") for item in principles}) != 20:
        errors.append("Russian native profile principle IDs must be unique")

    rights = profile.get("rights", {})
    for key in (
        "author_and_contributor_rights",
        "third_party_rights",
        "ownership_boundary",
    ):
        if not rights.get(key):
            errors.append(f"rights.{key} must be documented")

    return errors


def main() -> int:
    errors = validate()
    if errors:
        for error in errors:
            print(f"ERROR: {error}")
        return 1

    print(
        "МОСТ contract valid: 102 exact aliases, 38 runtime aliases, "
        "64 lexical reservations, 20 principles."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
