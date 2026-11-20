# SPDX-License-Identifier: Apache-2.0
"""Conservative source-license and attribution inventory for Reaper projects.

This is a review aid, not a plagiarism detector or legal opinion. It reads source
headers and repository-level notice files; it cannot establish provenance,
ownership, permission, or license compatibility.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
from pathlib import Path
from typing import Any

SPDX_RE = re.compile(r"SPDX-License-Identifier:\s*([^\r\n*]+)", re.IGNORECASE)
COPYRIGHT_RE = re.compile(r"(?:copyright|©|\(c\))", re.IGNORECASE)
SOURCE_EXTENSIONS = {
    ".rpr", ".py", ".pyi", ".c", ".h", ".cc", ".cpp", ".cxx", ".hpp",
    ".rs", ".zig", ".d", ".di", ".nim", ".adb", ".ads", ".mod", ".obn",
    ".v", ".vh", ".sv", ".svh", ".vhd", ".vhdl", ".scala", ".sc", ".bsv",
    ".wat", ".ll", ".bc", ".java", ".kt", ".smali", ".lua", ".fs", ".forth",
    ".4th", ".ps", ".bf", ".b", ".bliss", ".asm", ".s", ".inc", ".glsl",
    ".vert", ".frag", ".comp", ".hlsl", ".ptx",
}
IGNORED_DIRS = {
    ".git", ".hg", ".svn", ".venv", "venv", "__pycache__", ".pytest_cache",
    ".mypy_cache", ".ruff_cache", "node_modules", "dist", "build",
}
DEFAULT_MAX_FILES = 20_000
DEFAULT_MAX_FILE_BYTES = 2 * 1024 * 1024
DEFAULT_MAX_TOTAL_BYTES = 64 * 1024 * 1024


def _root_notices(root: Path) -> tuple[list[str], list[str]]:
    licenses: list[str] = []
    notices: list[str] = []
    try:
        for child in root.iterdir():
            if not child.is_file() or child.is_symlink():
                continue
            name = child.name.casefold()
            if name in {"license", "license.txt", "copying", "copying.txt"} or name.startswith(("license.", "copying.")):
                licenses.append(child.name)
            elif name == "notice" or name.startswith("notice."):
                notices.append(child.name)
    except OSError as error:
        raise ValueError(f"cannot inspect project root: {error}") from error
    return sorted(licenses), sorted(notices)


def scan_project(
    project: str | Path,
    *,
    max_files: int = DEFAULT_MAX_FILES,
    max_file_bytes: int = DEFAULT_MAX_FILE_BYTES,
    max_total_bytes: int = DEFAULT_MAX_TOTAL_BYTES,
) -> dict[str, Any]:
    root = Path(project).expanduser().resolve()
    if not root.exists() or not root.is_dir():
        raise ValueError(f"project path is not a directory: {root}")
    for name, value in (
        ("max_files", max_files),
        ("max_file_bytes", max_file_bytes),
        ("max_total_bytes", max_total_bytes),
    ):
        if type(value) is not int or value < 1:
            raise ValueError(f"{name} must be a positive integer")

    license_files, notice_files = _root_notices(root)
    records: list[dict[str, Any]] = []
    warnings: list[str] = []
    total_bytes = 0
    scanned = 0

    for current, directories, filenames in os.walk(root, topdown=True, followlinks=False):
        current_path = Path(current)
        directories[:] = [
            directory for directory in directories
            if directory not in IGNORED_DIRS
            and not (current_path / directory).is_symlink()
        ]
        for filename in sorted(filenames):
            path = current_path / filename
            if path.is_symlink() or path.suffix.casefold() not in SOURCE_EXTENSIONS:
                continue
            if scanned >= max_files:
                warnings.append(f"scan stopped at max_files={max_files}")
                break
            try:
                size = path.stat().st_size
                if size > max_file_bytes:
                    warnings.append(f"skipped oversized source file: {path.relative_to(root).as_posix()}")
                    continue
                if total_bytes + size > max_total_bytes:
                    warnings.append(f"scan stopped at max_total_bytes={max_total_bytes}")
                    break
                raw = path.read_bytes()
            except OSError as error:
                warnings.append(f"could not read {path.relative_to(root).as_posix()}: {error}")
                continue
            total_bytes += len(raw)
            scanned += 1
            header = raw[: min(len(raw), 16_384)].decode("utf-8", errors="replace")
            header = "\n".join(header.splitlines()[:80])
            match = SPDX_RE.search(header)
            expression = match.group(1).strip().rstrip("*/").strip() if match else None
            has_copyright = bool(COPYRIGHT_RE.search(header))
            if expression:
                classification = "spdx-declared"
            elif license_files:
                classification = "repository-license-present"
            else:
                classification = "needs-license-review"
            records.append({
                "path": path.relative_to(root).as_posix(),
                "bytes": len(raw),
                "spdx_expression": expression,
                "copyright_notice": has_copyright,
                "classification": classification,
            })
        else:
            continue
        break

    counts = {
        "spdx_declared": sum(item["classification"] == "spdx-declared" for item in records),
        "missing_file_spdx": sum(item["spdx_expression"] is None for item in records),
        "repository_license_present": sum(item["classification"] == "repository-license-present" for item in records),
        "needs_license_review": sum(item["classification"] == "needs-license-review" for item in records),
        "copyright_notices": sum(item["copyright_notice"] for item in records),
    }
    return {
        "schema": "reaper.copyright-inventory/v1",
        "project": str(root),
        "license_files": license_files,
        "notice_files": notice_files,
        "source_files_scanned": scanned,
        "source_bytes_scanned": total_bytes,
        "counts": counts,
        "warnings": warnings,
        "files": records,
        "limitations": [
            "A notice or SPDX identifier is recorded, not legally validated.",
            "A repository-level LICENSE file is reported as present; license inheritance is not legally inferred.",
            "The scan cannot detect copied code, establish authorship, prove permission, or determine license compatibility.",
            "Review vendored code, generated files, binary assets, dependencies and external toolchains separately.",
        ],
    }


def render_text(report: dict[str, Any]) -> str:
    counts = report["counts"]
    lines = [
        f"Copyright inventory: {report['project']}",
        f"Source files scanned: {report['source_files_scanned']} ({report['source_bytes_scanned']} bytes)",
        f"Root license files: {', '.join(report['license_files']) or 'none found'}",
        f"Root notice files: {', '.join(report['notice_files']) or 'none found'}",
        (
            "SPDX-declared: {spdx_declared}; missing file-level SPDX: {missing_file_spdx}; "
            "repository LICENSE present: {repository_license_present}; review needed: "
            "{needs_license_review}; copyright notices: {copyright_notices}"
        ).format(**counts),
    ]
    for item in report["files"]:
        expression = item["spdx_expression"] or "no file-level SPDX identifier"
        lines.append(f"  {item['classification']}: {item['path']} [{expression}]")
    if report["warnings"]:
        lines.append("Warnings:")
        lines.extend(f"  - {warning}" for warning in report["warnings"])
    lines.extend([
        "",
        "This inventory is not a plagiarism detector or legal opinion.",
        "It does not certify ownership, permission, attribution completeness or license compatibility.",
    ])
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="reaper copyright-scan",
        description="Inventory source SPDX identifiers and repository-level copyright notices.",
    )
    parser.add_argument("project", nargs="?", default=".", help="project directory to inspect")
    parser.add_argument("--json", action="store_true", help="emit the complete inventory as JSON")
    parser.add_argument(
        "--require-spdx",
        action="store_true",
        help="return failure if any scanned source file lacks an explicit SPDX header",
    )
    parser.add_argument("--max-files", type=int, default=DEFAULT_MAX_FILES)
    parser.add_argument("--max-file-bytes", type=int, default=DEFAULT_MAX_FILE_BYTES)
    parser.add_argument("--max-total-bytes", type=int, default=DEFAULT_MAX_TOTAL_BYTES)
    args = parser.parse_args(argv)
    try:
        report = scan_project(
            args.project,
            max_files=args.max_files,
            max_file_bytes=args.max_file_bytes,
            max_total_bytes=args.max_total_bytes,
        )
    except (OSError, ValueError) as error:
        print(f"reaper-copyright-scan: FAIL: {error}", file=sys.stderr)
        return 2
    if args.json:
        print(json.dumps(report, ensure_ascii=False, indent=2))
    else:
        print(render_text(report))
    if args.require_spdx and report["counts"]["missing_file_spdx"]:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
