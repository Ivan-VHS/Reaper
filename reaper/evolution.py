"""Deterministic, safety-first evolution checks for the Reaper project.

The engine never rewrites source code autonomously. It measures the current
repository, runs the project's tests, and emits actionable proposals. A future
patch generator can consume these proposals behind review and verification gates.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
import json
import re
from pathlib import Path
import subprocess
import sys
from time import perf_counter
from typing import Any


@dataclass(frozen=True)
class CheckResult:
    name: str
    passed: bool
    duration_seconds: float
    summary: str


@dataclass(frozen=True)
class EvolutionReport:
    root: str
    iterations: int
    checks: tuple[CheckResult, ...]
    proposals: tuple[str, ...]

    @property
    def passed(self) -> bool:
        return bool(self.checks) and all(check.passed for check in self.checks)

    def to_dict(self) -> dict[str, Any]:
        result = asdict(self)
        result["passed"] = self.passed
        return result

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), ensure_ascii=False, indent=2)


class EvolutionEngine:
    """Run bounded, repeatable quality cycles without mutating project files."""

    MAX_ITERATIONS = 20
    DEFAULT_TIMEOUT_SECONDS = 120

    def __init__(self, root: str | Path, timeout_seconds: int = DEFAULT_TIMEOUT_SECONDS):
        self.root = Path(root).resolve()
        self.timeout_seconds = timeout_seconds

    def _syntax_check(self) -> CheckResult:
        started = perf_counter()
        files = sorted(self.root.joinpath("reaper").rglob("*.py"))
        failures: list[str] = []
        for path in files:
            try:
                compile(path.read_text(encoding="utf-8"), str(path), "exec")
            except (OSError, UnicodeError, SyntaxError) as error:
                failures.append(f"{path.relative_to(self.root)}: {error}")
        return CheckResult(
            "python-syntax",
            not failures and bool(files),
            perf_counter() - started,
            f"{len(files)} source files checked" if not failures else "; ".join(failures),
        )

    def _unit_tests(self) -> CheckResult:
        started = perf_counter()
        tests = self.root / "tests"
        if not tests.is_dir():
            return CheckResult("unit-tests", False, 0.0, "tests/ directory not found")
        try:
            result = subprocess.run(
                [sys.executable, "-m", "unittest", "discover", "-s", "tests", "-v"],
                cwd=self.root,
                capture_output=True,
                text=True,
                timeout=self.timeout_seconds,
                check=False,
            )
        except subprocess.TimeoutExpired:
            return CheckResult(
                "unit-tests", False, perf_counter() - started,
                f"test suite exceeded {self.timeout_seconds}s timeout",
            )
        output = (result.stdout + "\n" + result.stderr).strip()
        tail = "\n".join(output.splitlines()[-12:])
        if re.search(r"\bRan\s+0\s+tests?\b", output, flags=re.IGNORECASE):
            return CheckResult(
                "unit-tests", False, perf_counter() - started,
                "test suite discovered zero tests; add at least one test case",
            )
        return CheckResult(
            "unit-tests", result.returncode == 0, perf_counter() - started,
            tail or f"test process exited with code {result.returncode}",
        )

    def _proposals(self) -> tuple[str, ...]:
        source_files = sorted(self.root.joinpath("reaper").rglob("*.py"))
        test_root = self.root / "tests"
        test_text = ""
        if test_root.is_dir():
            test_text = "\n".join(
                path.read_text(encoding="utf-8", errors="replace")
                for path in test_root.rglob("*.py")
            )
        proposals: list[str] = []
        if not source_files:
            proposals.append("Restore or create the reaper/ source package.")
        if not test_root.is_dir():
            proposals.append("Add a tests/ suite before accepting language changes.")
        else:
            for source in source_files:
                if source.name == "__init__.py":
                    continue
                stem = source.stem
                if stem not in test_text and f"test_{stem}" not in test_text:
                    proposals.append(
                        f"Add focused tests for reaper/{source.relative_to(self.root.joinpath('reaper'))}; "
                        "confirm behavior before refactoring it."
                    )
        if not proposals:
            proposals.append(
                "No obvious source-to-test coverage gaps found by the filename heuristic; "
                "add semantic, fuzz and differential tests for the next compiler milestone."
            )
        proposals.append(
            "Keep language evolution proposal-driven: every new syntax or builtin needs a "
            "specification, compatibility decision, negative tests and resource bounds."
        )
        return tuple(proposals)

    def run(self, iterations: int = 1) -> EvolutionReport:
        if not 1 <= iterations <= self.MAX_ITERATIONS:
            raise ValueError(f"iterations must be between 1 and {self.MAX_ITERATIONS}")
        if self.timeout_seconds < 1:
            raise ValueError("timeout_seconds must be positive")

        checks: list[CheckResult] = []
        for cycle in range(1, iterations + 1):
            syntax = self._syntax_check()
            checks.append(CheckResult(
                f"cycle-{cycle}:{syntax.name}", syntax.passed,
                syntax.duration_seconds, syntax.summary,
            ))
            if not syntax.passed:
                break
            tests = self._unit_tests()
            checks.append(CheckResult(
                f"cycle-{cycle}:{tests.name}", tests.passed,
                tests.duration_seconds, tests.summary,
            ))
            if not tests.passed:
                break

        return EvolutionReport(
            str(self.root), iterations, tuple(checks), self._proposals()
        )
