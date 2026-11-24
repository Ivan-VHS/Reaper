"""Unified Java/Reaper BAV (Beelzebul Antivirus) orchestration.

The Java guard performs deterministic Java-specific SAST and safe text inspection.
The existing 66-rule Python engine remains the canonical policy evaluator.
Both scanners are read-only and never execute the inspected project.
"""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[1]
JAVA_SOURCE = PROJECT_ROOT / "security" / "java" / "src" / "main" / "java" / "org" / "ivanvhs" / "bav" / "Bav.java"
PYTHON_SCANNER = PROJECT_ROOT / "tools" / "beelzebul.py"
JAVA_MAIN = "org.ivanvhs.bav.Bav"
SEVERITY_WEIGHT = {"critical": 25, "high": 12, "medium": 5, "low": 2, "info": 1}


class BAVError(RuntimeError):
    """A required security scanner or its policy could not be executed safely."""


def _clean_environment() -> dict[str, str]:
    env = os.environ.copy()
    for key in (
        "JAVA_TOOL_OPTIONS",
        "JDK_JAVA_OPTIONS",
        "_JAVA_OPTIONS",
        "CLASSPATH",
        "PYTHONPATH",
        "PYTHONHOME",
    ):
        env.pop(key, None)
    env["PYTHONUTF8"] = "1"
    return env


def _run_json(command: list[str], *, cwd: Path, env: dict[str, str], timeout: int) -> dict[str, Any]:
    try:
        completed = subprocess.run(
            command,
            cwd=cwd,
            env=env,
            stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=timeout,
            check=False,
            shell=False,
        )
    except FileNotFoundError as exc:
        raise BAVError(f"required executable is unavailable: {command[0]}") from exc
    except subprocess.TimeoutExpired as exc:
        raise BAVError(f"scanner exceeded its {timeout}-second execution limit") from exc
    try:
        report = json.loads(completed.stdout)
    except json.JSONDecodeError as exc:
        detail = completed.stderr.strip().splitlines()
        reason = detail[-1] if detail else "scanner did not produce a valid JSON report"
        raise BAVError(f"scanner failed safely: {reason[:240]}") from exc
    if not isinstance(report, dict):
        raise BAVError("scanner returned a non-object report")
    if completed.returncode not in (0, 1, 2):
        raise BAVError(f"scanner exited with unexpected status {completed.returncode}")
    return report


def merge_reports(beelzebul: dict[str, Any], java_guard: dict[str, Any], root: Path) -> dict[str, Any]:
    """Merge component reports without suppressing or reclassifying findings."""
    merged: dict[tuple[str, str, int | None, str], dict[str, Any]] = {}
    for component, report in (("beelzebul", beelzebul), ("java_guard", java_guard)):
        findings = report.get("findings", [])
        if not isinstance(findings, list):
            raise BAVError(f"{component} returned an invalid findings collection")
        for finding in findings:
            if not isinstance(finding, dict):
                raise BAVError(f"{component} returned an invalid finding")
            rule_id = str(finding.get("rule_id", ""))
            path = str(finding.get("path", ""))
            line = finding.get("line")
            message = str(finding.get("message", ""))
            key = (rule_id, path, line if isinstance(line, int) else None, message)
            item = dict(finding)
            item["component"] = component
            merged.setdefault(key, item)

    findings = sorted(
        merged.values(),
        key=lambda item: (
            str(item.get("path", "")),
            item.get("line") if isinstance(item.get("line"), int) else 0,
            str(item.get("rule_id", "")),
            str(item.get("message", "")),
        ),
    )
    component_verdicts = {beelzebul.get("verdict"), java_guard.get("verdict")}
    if "blocked" in component_verdicts:
        verdict = "blocked"
    elif "review" in component_verdicts or findings:
        verdict = "review"
    else:
        verdict = "clear"

    component_risks = [
        value for value in (beelzebul.get("risk_score"), java_guard.get("risk_score"))
        if isinstance(value, (int, float))
    ]
    risk_score = min(100, max(component_risks, default=0))
    beelzebul_scan = beelzebul.get("scan", {})
    java_scan = java_guard.get("scan", {})
    scan = {
        "root": str(root),
        "tracked_paths": max(
            int(beelzebul_scan.get("tracked_paths", 0) or 0),
            int(java_scan.get("tracked_paths", 0) or 0),
        ),
        "text_files_scanned": max(
            int(beelzebul_scan.get("text_files_scanned", 0) or 0),
            int(java_scan.get("text_files_scanned", 0) or 0),
        ),
        "bytes_scanned": max(
            int(beelzebul_scan.get("total_bytes_scanned", 0) or 0),
            int(java_scan.get("bytes_scanned", 0) or 0),
        ),
        "read_only": True,
        "project_code_executed": False,
    }
    return {
        "schema": "bav.security.report.v1",
        "scanner": {"name": "BAV — Beelzebul Antivirus for Reaper", "version": "1.0.0"},
        "repository": str(root),
        "verdict": verdict,
        "risk_score": risk_score,
        "findings_count": len(findings),
        "findings": findings,
        "components": {
            "beelzebul": {
                "verdict": beelzebul.get("verdict", "unknown"),
                "risk_score": beelzebul.get("risk_score", 0),
                "findings_count": beelzebul.get("findings_count", len(beelzebul.get("findings", []))),
                "rules_total": beelzebul.get("policy", {}).get("rules_total", 66),
            },
            "java_guard": {
                "verdict": java_guard.get("verdict", "unknown"),
                "risk_score": java_guard.get("risk_score", 0),
                "findings_count": java_guard.get("findings_count", len(java_guard.get("findings", []))),
                "rules_total": java_guard.get("policy", {}).get("rules_total", 8),
            },
        },
        "policy": {
            "canonical": "security/beelzebul.v1.json",
            "beelzebul_rules": beelzebul.get("policy", {}).get("rules_total", 66),
            "java_guard_rules": java_guard.get("policy", {}).get("rules_total", 8),
            "secret_values_in_reports": False,
        },
        "scan": scan,
    }


def _write_report(path: Path, report: dict[str, Any]) -> None:
    path = path.expanduser().resolve()
    path.parent.mkdir(parents=True, exist_ok=True)
    encoded = json.dumps(report, ensure_ascii=False, indent=2) + "\n"
    temporary: Path | None = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w", encoding="utf-8", newline="\n", dir=path.parent,
            prefix=f".{path.name}.", suffix=".tmp", delete=False,
        ) as stream:
            temporary = Path(stream.name)
            stream.write(encoded)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
    finally:
        if temporary is not None:
            try:
                temporary.unlink(missing_ok=True)
            except OSError:
                pass


def _format_text(report: dict[str, Any]) -> str:
    lines = [
        f"BAV {report['scanner']['version']} — {report['repository']}",
        f"Verdict: {report['verdict'].upper()} | risk: {report['risk_score']}/100",
        (
            "Engines: "
            f"Beelzebul {report['components']['beelzebul']['verdict']} "
            f"({report['components']['beelzebul']['findings_count']} findings), "
            f"Java Guard {report['components']['java_guard']['verdict']} "
            f"({report['components']['java_guard']['findings_count']} findings)"
        ),
        "Mode: read-only; inspected project code is never executed.",
    ]
    if not report["findings"]:
        lines.append("No automated findings.")
    for finding in report["findings"]:
        location = finding.get("path", "<unknown>")
        if finding.get("line"):
            location += f":{finding['line']}"
        lines.append(
            f"[{str(finding.get('severity', 'info')).upper()} / "
            f"{str(finding.get('enforcement', 'observe')).upper()}] "
            f"{finding.get('rule_id', 'UNKNOWN')} {location}: {finding.get('message', '')}"
        )
        if finding.get("remediation"):
            lines.append(f"  Fix: {finding['remediation']}")
    lines.append("A clear repository scan is not a malware-free or security certification.")
    return "\n".join(lines)


def scan(root: Path, policy: Path | None = None, base_ref: str | None = None) -> dict[str, Any]:
    root = root.expanduser().resolve(strict=True)
    if not root.is_dir():
        raise BAVError("scan root must be an existing directory")
    policy_path = (policy or (root / "security" / "beelzebul.v1.json")).expanduser().resolve(strict=True)
    if not policy_path.is_file():
        raise BAVError("canonical Beelzebul policy is not a regular file")
    if not JAVA_SOURCE.is_file() or not PYTHON_SCANNER.is_file():
        raise BAVError("BAV engine sources are incomplete; refusing a partial scan")

    env = _clean_environment()
    javac = "javac"
    java = "java"
    python = sys.executable
    with tempfile.TemporaryDirectory(prefix="reaper-bav-") as temporary:
        classes = Path(temporary) / "classes"
        classes.mkdir()
        compile_result = subprocess.run(
            [javac, "--release", "17", "-encoding", "UTF-8", "-d", str(classes), str(JAVA_SOURCE)],
            cwd=PROJECT_ROOT,
            env=env,
            stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=60,
            check=False,
            shell=False,
        )
        if compile_result.returncode != 0:
            details = compile_result.stderr.strip().splitlines()
            reason = details[-1] if details else "javac compilation failed"
            raise BAVError(f"Java Guard compilation failed: {reason[:240]}")

        java_report = _run_json(
            [java, "-Xms16m", "-Xmx256m", "-Dfile.encoding=UTF-8", "-cp", str(classes),
             JAVA_MAIN, "scan", "--root", str(root), "--json"],
            cwd=PROJECT_ROOT,
            env=env,
            timeout=90,
        )
        legacy_command = [
            python, "-I", str(PYTHON_SCANNER),
            "--root", str(root), "--policy", str(policy_path), "--json",
        ]
        if base_ref:
            legacy_command.extend(["--base-ref", base_ref])
        beelzebul_report = _run_json(
            legacy_command, cwd=PROJECT_ROOT, env=env, timeout=120
        )
    if beelzebul_report.get("schema") not in (None, "beelzebul.report.v1"):
        raise BAVError("canonical Beelzebul engine returned an unexpected report schema")
    return merge_reports(beelzebul_report, java_report, root)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="reaper security scan",
        description="Run the unified, read-only Java/Reaper BAV security pipeline.",
    )
    parser.add_argument("--root", type=Path, default=Path.cwd(), help="repository root to inspect")
    parser.add_argument("--policy", type=Path, help="canonical Beelzebul JSON policy")
    parser.add_argument("--base-ref", help="Git base ref for change-correlation checks")
    parser.add_argument("--json", action="store_true", help="emit the unified machine-readable report")
    parser.add_argument("--output", type=Path, help="atomically write the unified JSON report")
    parser.add_argument("--strict-review", action="store_true", help="return 1 when review findings exist")
    args = parser.parse_args(argv)
    try:
        report = scan(args.root, args.policy, args.base_ref)
    except (BAVError, OSError, ValueError) as exc:
        print(f"BAV ERROR: {exc}", file=sys.stderr)
        return 2

    encoded = json.dumps(report, ensure_ascii=False, indent=2)
    if args.output:
        try:
            _write_report(args.output, report)
        except OSError as exc:
            print(f"BAV ERROR: cannot write report: {exc}", file=sys.stderr)
            return 2
    print(encoded if args.json else _format_text(report))
    if report["verdict"] == "blocked":
        return 2
    if args.strict_review and report["verdict"] == "review":
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
