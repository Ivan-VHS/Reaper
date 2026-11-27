#!/usr/bin/env python3
"""Validate the Reaper Psychoporter 666 constitution and its adoption profile."""
from __future__ import annotations

import re
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CONSTITUTION_PATH = ROOT / "docs" / "PSYCHOPORTER_666.md"
PROFILE_PATH = ROOT / "docs" / "CONSTITUTION_666_PROFILE.md"

RULE_LINE = re.compile(r"^\s*(?:\*\*)?(\d{1,3})\.(?:\*\*)?\s+\S")
SECTION_LINE = re.compile(r"^## ([IVX]+)\.", re.MULTILINE)
EXPECTED_SECTIONS = ["I", "II", "III", "IV", "V", "VI", "VII", "VIII", "IX", "X", "XI"]
EXPECTED_RANGES = [
    "1–60",
    "61–120",
    "121–180",
    "181–240",
    "241–300",
    "301–360",
    "361–420",
    "421–480",
    "481–540",
    "541–600",
    "601–660",
    "661–666",
]


def validate_constitution(content: str) -> list[str]:
    errors: list[str] = []
    numbers: list[int] = []

    for line in content.splitlines():
        match = RULE_LINE.match(line)
        if match:
            numbers.append(int(match.group(1)))

    expected = list(range(1, 667))
    counts = Counter(numbers)
    missing = [number for number in expected if counts[number] == 0]
    duplicated = sorted(number for number, count in counts.items() if count > 1)
    unexpected = sorted(number for number in counts if number not in expected)

    if missing:
        errors.append("missing rule numbers: " + ", ".join(map(str, missing)))
    if duplicated:
        errors.append("duplicate rule numbers: " + ", ".join(map(str, duplicated)))
    if unexpected:
        errors.append("unexpected rule numbers: " + ", ".join(map(str, unexpected)))
    if numbers != expected:
        errors.append("rules must appear exactly once in ascending order from 1 through 666")

    sections = SECTION_LINE.findall(content)
    if sections != EXPECTED_SECTIONS:
        errors.append(
            "expected eleven numbered spheres I–XI in order; found: "
            + (", ".join(sections) or "(none)")
        )

    if "### Шесть итоговых заповедей" not in content:
        errors.append("the six final commandments heading is missing")
    if "## Авторский Groove-профиль (ненормативное приложение)" not in content:
        errors.append("the non-normative authorial Groove profile is missing")
    if "| XI | 601–666 |" not in content:
        errors.append("sphere XI must map to rules 601–666")

    return errors


def validate_profile(content: str) -> list[str]:
    errors: list[str] = []
    missing = [value for value in EXPECTED_RANGES if f"| {value} |" not in content]
    if missing:
        errors.append("profile is missing range rows: " + ", ".join(missing))

    if "does not" not in content and "не утверждает" not in content:
        errors.append("profile must distinguish the doctrine from implemented features")
    if "verified" not in content or "planned" not in content:
        errors.append("profile must define evidence-based maturity states")

    return errors


def main() -> int:
    try:
        constitution = CONSTITUTION_PATH.read_text(encoding="utf-8")
        profile = PROFILE_PATH.read_text(encoding="utf-8")
    except OSError as error:
        print(f"Psychoporter 666: FAIL: {error}", file=sys.stderr)
        return 1

    errors = validate_constitution(constitution)
    errors.extend(validate_profile(profile))

    if errors:
        print("Psychoporter 666: FAIL")
        for error in errors:
            print(f"- {error}")
        return 1

    print("Psychoporter 666: PASS (666 unique ordered rules, 11 spheres, 6 commandments, 12 profile ranges)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
