#!/usr/bin/env python3
"""Wrap tool-specific JSON output in the shared Ivan-VHS report envelope v1."""
from __future__ import annotations
import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import platform
import sys
from typing import Any

MAX_RESULT_BYTES = 16 * 1024 * 1024
PROJECT_LIMITATIONS = {
    "pytyliki": ("hardware inspection is read-only", "performance claims require measurements on the target host"),
    "reaper": ("the runtime is not an operating-system sandbox",),
    "ventusample": ("processing is offline", "the tool does not determine rights to source material"),
    "oplague": ("analysis is read-only", "no driver is installed or modified", "heuristic findings are not malware or compatibility verdicts"),
}

class EnvelopeError(ValueError):
    """Raised when report metadata or its result is invalid."""

def _text(value: Any, label: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise EnvelopeError(f"{label} must be a non-empty string")
    return value.strip()

def _hex(value: str | None, label: str, minimum: int, maximum: int) -> str | None:
    if value is None or value == "":
        return None
    if not isinstance(value, str) or not minimum <= len(value) <= maximum:
        raise EnvelopeError(f"{label} must contain {minimum}–{maximum} hexadecimal characters")
    if any(char not in "0123456789abcdefABCDEF" for char in value):
        raise EnvelopeError(f"{label} must be hexadecimal")
    return value.lower()

def sha256_file(path: str | Path) -> str:
    digest = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()

def build_envelope(*, tool: str, version: str, commit: str | None, result: Any,
                   limitations: list[str] | tuple[str, ...] | None = None,
                   input_kind: str = "none", input_sha256: str | None = None,
                   created: str | None = None, os_name: str | None = None,
                   architecture: str | None = None) -> dict[str, Any]:
    tool_name = _text(tool, "tool name").lower()
    if any(char not in "abcdefghijklmnopqrstuvwxyz0123456789-_" for char in tool_name):
        raise EnvelopeError("tool name may contain only lowercase letters, digits, '-' and '_'")
    version_text = _text(version, "tool version")
    commit_hash = _hex(commit, "commit", 7, 64)
    input_hash = _hex(input_sha256, "input SHA-256", 64, 64)
    kind = _text(input_kind, "input kind").lower()
    if created is None:
        created = datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
    elif not _text(created, "created timestamp").endswith("Z"):
        raise EnvelopeError("created timestamp must be an ISO-8601 UTC timestamp ending in 'Z'")
    combined: list[str] = []
    for item in list(PROJECT_LIMITATIONS.get(tool_name, ())) + list(limitations or []):
        entry = _text(item, "limitation")
        if entry not in combined:
            combined.append(entry)
    return {
        "envelope": "ivan-vhs.report.v1",
        "tool": {"name": tool_name, "version": version_text, "commit": commit_hash},
        "created": created,
        "platform": {"os": os_name or platform.system().lower() or "unknown",
                     "arch": architecture or platform.machine().lower() or "unknown"},
        "input": {"kind": kind, "sha256": input_hash},
        "result": result,
        "limitations": combined,
    }

def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Wrap JSON output in ivan-vhs.report.v1.")
    parser.add_argument("--tool", required=True)
    parser.add_argument("--version", default=os.environ.get("IVAN_VHS_TOOL_VERSION", "unknown"))
    parser.add_argument("--commit", default=os.environ.get("GITHUB_SHA") or os.environ.get("IVAN_VHS_COMMIT"))
    parser.add_argument("--input-kind", default="none")
    parser.add_argument("--input-file", help="record only its SHA-256; the local path is never included")
    parser.add_argument("--limitation", action="append", default=[])
    args = parser.parse_args(argv)
    try:
        raw = sys.stdin.read(MAX_RESULT_BYTES + 1)
        if len(raw.encode("utf-8")) > MAX_RESULT_BYTES:
            raise EnvelopeError(f"JSON result exceeds the {MAX_RESULT_BYTES}-byte limit")
        result = json.loads(raw)
        report = build_envelope(
            tool=args.tool, version=args.version, commit=args.commit, result=result,
            limitations=args.limitation, input_kind="file" if args.input_file else args.input_kind,
            input_sha256=sha256_file(args.input_file) if args.input_file else None,
        )
    except (EnvelopeError, OSError, json.JSONDecodeError) as error:
        print(f"report-envelope: {error}", file=sys.stderr)
        return 2
    json.dump(report, sys.stdout, ensure_ascii=False, indent=2, sort_keys=True)
    sys.stdout.write("\n")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
