#!/usr/bin/env python3
"""Validate localized README editions and repository-local links."""
from __future__ import annotations
import re
import sys
from pathlib import Path
from urllib.parse import unquote, urlsplit
ROOT = Path(__file__).resolve().parents[2]
READMES = ("README.md", "README.ru.md", "README.uk.md", "README.zh-CN.md")
MARKDOWN_LINK = re.compile(r"!?(?:\[[^\]]*\])\(\s*(?:<([^>]+)>|([^\s)]+))")
HTML_LINK = re.compile(r"\b(?:href|src)\s*=\s*[\"']([^\"']+)[\"']", re.IGNORECASE)
FENCED_BLOCK = re.compile(r"(?ms)^" + chr(96) * 3 + r".*?^" + chr(96) * 3 + r"[ \t]*$")
def targets(markdown: str):
    text = FENCED_BLOCK.sub("", markdown)
    for match in MARKDOWN_LINK.finditer(text):
        yield match.group(1) or match.group(2)
    yield from HTML_LINK.findall(text)
def validate() -> list[str]:
    errors = []
    paths = [ROOT / name for name in READMES]
    for path in paths:
        if not path.is_file():
            errors.append(f"{path.relative_to(ROOT)}: required language edition is missing")
    for path in paths:
        if not path.is_file():
            continue
        content = path.read_text(encoding="utf-8")
        if not content.strip():
            errors.append(f"{path.relative_to(ROOT)}: file is empty")
            continue
        if not re.search(r"(?m)^#\s+\S", content):
            errors.append(f"{path.relative_to(ROOT)}: missing top-level Markdown heading")
        for raw in targets(content):
            target = raw.strip().strip("\"'")
            if not target:
                continue
            parsed = urlsplit(target)
            if parsed.scheme or parsed.netloc or not parsed.path:
                continue
            rel = unquote(parsed.path)
            candidate = ROOT / rel.lstrip("/") if rel.startswith("/") else path.parent / rel
            resolved = candidate.resolve()
            try:
                resolved.relative_to(ROOT)
            except ValueError:
                errors.append(f"{path.relative_to(ROOT)}: link escapes repository: {target}")
                continue
            if not resolved.exists():
                errors.append(f"{path.relative_to(ROOT)}: broken local link: {target}")
    return errors
if __name__ == "__main__":
    problems = validate()
    if problems:
        for problem in problems:
            print(f"ERROR: {problem}", file=sys.stderr)
        raise SystemExit(1)
    print(f"README check passed: {len(READMES)} language editions; all local links resolve.")
