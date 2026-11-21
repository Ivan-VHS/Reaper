"""Codebase wellbeing inventory.

This is a read-only engineering heuristic, not a human mental-health tool.
It does not rank contributors or claim to prove code correctness.
"""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
from typing import Any

CHARTER_PATH = Path(__file__).resolve().parents[1] / "data" / "code-wellbeing" / "codebase-wellbeing.v1.json"
MAX_FILES = 5000
MAX_DEPTH = 16
MAX_FILE_BYTES = 1024 * 1024
MAX_TOTAL_SOURCE_BYTES = 32 * 1024 * 1024
SKIP_DIRS = {".git", "build", "dist", "target", "vendor", "node_modules", ".venv", "venv", "__pycache__", ".pytest_cache"}
SOURCE_EXTENSIONS = {".c", ".h", ".cc", ".cpp", ".cxx", ".hpp", ".hxx", ".py", ".js", ".jsx", ".ts", ".tsx", ".rs", ".go", ".java", ".cs", ".rpr", ".qcs", ".lua"}
DOC_EXTENSIONS = {".md", ".mdx", ".rst", ".adoc"}
DEPENDENCY_FILES = {"pyproject.toml", "requirements.txt", "package.json", "package-lock.json", "pnpm-lock.yaml", "yarn.lock", "Cargo.toml", "Cargo.lock", "go.mod", "go.sum", "poetry.lock", "Pipfile", "Pipfile.lock", "vcpkg.json", "conanfile.py", "conanfile.txt"}
MARKERS = ("TODO", "FIXME", "HACK", "XXX")


class CodeWellbeingError(ValueError):
    """Invalid project path or invalid code-wellbeing charter."""


def load_charter(path: Path = CHARTER_PATH) -> dict[str, Any]:
    try:
        if path.stat().st_size > 256 * 1024:
            raise CodeWellbeingError("code-wellbeing charter exceeds 256 KiB")
        value = json.loads(path.read_text(encoding="utf-8"))
    except OSError as error:
        raise CodeWellbeingError(f"cannot read code-wellbeing charter: {error}") from error
    except (UnicodeError, json.JSONDecodeError) as error:
        raise CodeWellbeingError(f"invalid code-wellbeing charter JSON: {error}") from error
    concept = value.get("concept") if isinstance(value, dict) else None
    if (not isinstance(concept, dict) or concept.get("id") != "code-mental-health"
            or concept.get("is_engineering_metaphor") is not True
            or concept.get("clinical_equivalence") is not False):
        raise CodeWellbeingError("charter must remain an explicitly non-clinical engineering metaphor")
    return value


def _is_test_file(relative: Path) -> bool:
    parts = {part.casefold() for part in relative.parts}
    name = relative.name.casefold()
    return bool(parts & {"test", "tests", "testing", "spec", "specs"}) or name.startswith(("test_", "test.")) or name.endswith(("_test.py", ".spec.js", ".test.js", ".spec.ts", ".test.ts"))


def scan_project(root: str | Path = ".") -> dict[str, Any]:
    charter = load_charter()
    requested_root = Path(root).expanduser()
    if requested_root.is_symlink():
        raise CodeWellbeingError("project root must not be a symbolic link")
    project = requested_root.resolve()
    if not project.is_dir():
        raise CodeWellbeingError(f"project root is not a directory: {project}")

    files: list[Path] = []
    truncated = False
    for current, dirs, filenames in os.walk(project, topdown=True, followlinks=False):
        current_path = Path(current)
        depth = len(current_path.relative_to(project).parts)
        dirs[:] = sorted(
            name for name in dirs
            if name.casefold() not in SKIP_DIRS and not (current_path / name).is_symlink()
        )
        if depth >= MAX_DEPTH:
            if dirs:
                truncated = True
            dirs[:] = []
        for filename in sorted(filenames):
            item = current_path / filename
            try:
                if item.is_symlink() or not item.is_file():
                    continue
                files.append(item)
            except OSError:
                continue
            if len(files) >= MAX_FILES:
                truncated = True
                break
        if truncated:
            break

    relative_files = [item.relative_to(project) for item in files]
    source_files = [p for p in relative_files if p.suffix.casefold() in SOURCE_EXTENSIONS]
    test_files = [p for p in source_files if _is_test_file(p)]
    documentation_files = [p for p in relative_files if p.suffix.casefold() in DOC_EXTENSIONS]
    workflow_files = [
        p for p in relative_files
        if ".github/workflows" in p.as_posix().casefold()
        or p.name.casefold() in {".gitlab-ci.yml", "azure-pipelines.yml", "bitbucket-pipelines.yml"}
    ]
    readme_files = [p for p in relative_files if p.name.casefold().startswith("readme")]
    ownership_files = [
        p for p in relative_files
        if p.name.casefold() == "codeowners" or p.as_posix().casefold().endswith("/codeowners")
    ]
    dependency_files = [p for p in relative_files if p.name in DEPENDENCY_FILES]
    recovery_files = [
        p for p in relative_files
        if any(term in p.name.casefold() for term in ("rollback", "runbook", "recovery", "release-process"))
    ]
    learning_files = [
        p for p in relative_files
        if any(term in p.name.casefold() for term in ("postmortem", "post-mortem", "incident", "adr"))
    ]

    marker_counts = {marker: 0 for marker in MARKERS}
    large_sources: list[str] = []
    scanned_text = 0
    source_bytes_scanned = 0
    source_scan_truncated = False
    for relative in source_files:
        absolute = project / relative
        try:
            file_size = absolute.stat().st_size
            if file_size > MAX_FILE_BYTES:
                source_scan_truncated = True
                continue
            if source_bytes_scanned + file_size > MAX_TOTAL_SOURCE_BYTES:
                source_scan_truncated = True
                continue
            text = absolute.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        source_bytes_scanned += file_size
        scanned_text += 1
        lines = text.splitlines()
        if len(lines) > 1000 and len(large_sources) < 100:
            large_sources.append(relative.as_posix())
        for line in lines:
            for marker in MARKERS:
                if marker in line:
                    marker_counts[marker] += 1

    signals = [
        {"id": "verification", "status": "observed" if test_files and workflow_files else "missing",
         "evidence": [p.as_posix() for p in (test_files[:5] + workflow_files[:5])],
         "note": "Test and CI file presence does not prove coverage, test quality or passing status."},
        {"id": "documentation", "status": "observed" if readme_files else "missing",
         "evidence": [p.as_posix() for p in readme_files[:5]],
         "note": "A README file can still be incomplete or outdated."},
        {"id": "ownership-and-support", "status": "observed" if ownership_files else "unknown",
         "evidence": [p.as_posix() for p in ownership_files[:5]],
         "note": "No ownership file is not proof that maintainers are unavailable."},
        {"id": "dependency-care", "status": "observed" if dependency_files else "unknown",
         "evidence": [p.as_posix() for p in dependency_files[:10]],
         "note": "Manifest presence does not prove dependency freshness or safety."},
        {"id": "change-safety", "status": "observed" if recovery_files else "unknown",
         "evidence": [p.as_posix() for p in recovery_files[:10]],
         "note": "Named rollback or runbook files do not prove recovery has been rehearsed."},
        {"id": "incident-learning", "status": "observed" if learning_files else "unknown",
         "evidence": [p.as_posix() for p in learning_files[:10]],
         "note": "Document presence does not prove that lessons have been applied."},
        {"id": "maintainability-review-cues", "status": "observed",
         "evidence": [f"{key}={value}" for key, value in marker_counts.items()] + [f"large_source_units_over_1000_lines={len(large_sources)}"],
         "note": "Markers and large files are review prompts, not automatic defects."}
    ]
    return {
        "schema_version": 1,
        "concept": charter["concept"]["name"],
        "project": project.name,
        "scan": {"read_only": True, "inventory_truncated": truncated, "file_limit": MAX_FILES,
                 "depth_limit": MAX_DEPTH, "max_source_file_bytes_scanned": MAX_FILE_BYTES, "max_total_source_bytes": MAX_TOTAL_SOURCE_BYTES, "source_text_scan_truncated": source_scan_truncated},
        "inventory": {
            "total_files": len(files), "source_files": len(source_files), "test_files": len(test_files),
            "documentation_files": len(documentation_files), "readme_files": len(readme_files),
            "ci_workflow_files": len(workflow_files), "ownership_files": len(ownership_files),
            "dependency_manifest_files": len(dependency_files), "source_bytes_scanned": source_bytes_scanned, "recovery_guides": len(recovery_files),
            "incident_or_decision_records": len(learning_files), "source_files_text_scanned": scanned_text,
            "maintenance_markers": marker_counts, "large_source_units_over_1000_lines": large_sources
        },
        "signals": signals,
        "reporting_note": "No overall mental-health or code-quality score is computed. Signals describe visible repository evidence only.",
        "privacy_note": "No contributor activity, commit timing, hardware, audio, device telemetry or external service is inspected."
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Read-only Code Mental Health / Codebase Wellbeing inventory.")
    parser.add_argument("path", nargs="?", default=".", help="repository root (default: current directory)")
    parser.add_argument("--json", action="store_true", help="emit machine-readable JSON")
    args = parser.parse_args(argv)
    try:
        report = scan_project(args.path)
    except CodeWellbeingError as error:
        parser.exit(2, f"code-wellbeing: {error}\n")
    if args.json:
        print(json.dumps(report, ensure_ascii=False, indent=2))
    else:
        inventory = report["inventory"]
        print("Code Mental Health / Codebase Wellbeing v1")
        print(f"Project: {report['project']} | files: {inventory['total_files']} | source: {inventory['source_files']} | tests: {inventory['test_files']}")
        print(f"Docs: {inventory['documentation_files']} | CI workflows: {inventory['ci_workflow_files']} | scanned source: {inventory['source_files_text_scanned']}")
        for signal in report["signals"]:
            print(f"- {signal['id']}: {signal['status']} — {signal['note']}")
        print(f"Maintenance markers (review cues): {inventory['maintenance_markers']}")
        print(report["reporting_note"])
        print(report["privacy_note"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
