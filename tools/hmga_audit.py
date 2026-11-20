#!/usr/bin/env python3
"""Read-only HMGA audit; exact constants are metadata, never workload sizes."""
from __future__ import annotations
import argparse, json, subprocess, sys
from dataclasses import asdict, dataclass
from pathlib import Path

HMGA_CONSTANTS = {
    "N_global": "66666666666666",
    "N_sub": "6454684531153413",
    "F_base": "654684676534",
    "M_mult": "646846453",
    "R_base": "54654654",
}
SOURCE_SUFFIXES = {".c", ".h", ".cc", ".cpp", ".py", ".rs", ".go", ".js", ".ts"}


@dataclass(frozen=True)
class AuditReport:
    repository_root: str
    head: str
    branch: str
    working_tree_clean: bool
    shallow_checkout: bool
    visible_commit_count: int
    visible_ref_count: int
    ci_workflows: tuple[str, ...]
    test_file_count: int
    hmga_policy_present: bool
    warnings: tuple[str, ...]


def _git(root: Path, *arguments: str, allow_failure: bool = False) -> str:
    command = ["git", "-C", str(root), *arguments]
    result = subprocess.run(command, check=False, capture_output=True, text=True,
                            encoding="utf-8", errors="replace", timeout=15)
    if result.returncode:
        if allow_failure:
            return ""
        detail = result.stderr.strip() or f"exit status {result.returncode}"
        raise RuntimeError(f"git {' '.join(arguments)} failed: {detail}")
    return result.stdout.strip()


def audit_repository(repository: str | Path = ".") -> AuditReport:
    requested = Path(repository).expanduser().resolve()
    if not requested.is_dir():
        raise ValueError(f"not a directory: {requested}")
    root = Path(_git(requested, "rev-parse", "--show-toplevel")).resolve()
    head = _git(root, "rev-parse", "--short=12", "HEAD")
    branch = _git(root, "symbolic-ref", "--short", "-q", "HEAD", allow_failure=True) or "DETACHED"
    clean = not bool(_git(root, "status", "--porcelain"))
    refs = _git(root, "for-each-ref", "--format=%(refname:short)", "refs/heads", "refs/remotes")
    ref_count = sum(bool(line.strip()) for line in refs.splitlines())
    commit_count = int(_git(root, "rev-list", "--all", "--count") or "0")
    shallow = _git(root, "rev-parse", "--is-shallow-repository").lower() == "true"
    workflow_dir = root / ".github" / "workflows"
    workflows = tuple(sorted(
        p.relative_to(root).as_posix() for p in workflow_dir.glob("*")
        if p.is_file() and p.suffix.lower() in {".yml", ".yaml"}
    )) if workflow_dir.is_dir() else ()
    tests_dir = root / "tests"
    test_files = tuple(p for p in tests_dir.rglob("*")
                       if p.is_file() and p.suffix.lower() in SOURCE_SUFFIXES) if tests_dir.is_dir() else ()
    policy = (root / "docs" / "HMGA_V2.0.md").is_file()
    warnings = []
    if not workflows:
        warnings.append("no GitHub Actions workflow found")
    if not test_files:
        warnings.append("no source test files found under tests/")
    if not policy:
        warnings.append("docs/HMGA_V2.0.md is missing")
    return AuditReport(str(root), head, branch, clean, shallow, commit_count,
                       ref_count, workflows, len(test_files), policy, tuple(warnings))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Read-only HMGA repository audit")
    parser.add_argument("--repo", default=".")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--strict", action="store_true")
    args = parser.parse_args(argv)
    try:
        report = audit_repository(args.repo)
    except (OSError, RuntimeError, ValueError) as error:
        print(f"hmga-audit: {error}", file=sys.stderr)
        return 2
    payload = asdict(report)
    payload["hmga_constants"] = HMGA_CONSTANTS
    if args.json:
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    else:
        print(f"Repository: {report.repository_root}")
        print(f"HEAD / branch: {report.head} / {report.branch}")
        print(f"Working tree clean: {'yes' if report.working_tree_clean else 'no'}")
        print(f"Shallow checkout: {'yes' if report.shallow_checkout else 'no'}")
        print(f"Visible commits / refs: {report.visible_commit_count} / {report.visible_ref_count}")
        print(f"CI workflows / test files: {len(report.ci_workflows)} / {report.test_file_count}")
        print(f"HMGA policy: {'present' if report.hmga_policy_present else 'missing'}")
        for warning in report.warnings:
            print(f"WARNING: {warning}")
        if not report.warnings:
            print("Contract checks: PASS")
        print("HMGA constants: exact metadata; not executable workload sizes")
    return 1 if args.strict and report.warnings else 0


if __name__ == "__main__":
    raise SystemExit(main())
