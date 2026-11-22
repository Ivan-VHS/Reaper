#!/usr/bin/env python3
# Copyright (c) 2026 Ivan-VHS
# SPDX-License-Identifier: Apache-2.0
"""Reaper Toolchain Atlas: deterministic, read-only inventory of language tools."""
from __future__ import annotations
import argparse, json, os, platform, re, shutil, subprocess, sys, time
from concurrent.futures import ThreadPoolExecutor
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Sequence

@dataclass(frozen=True)
class Toolchain:
    language: str
    command: str
    version_args: tuple[str, ...]
    family: str
    role: str = "compiler_or_runtime"

@dataclass(frozen=True)
class ProbeResult:
    language: str
    command: str
    family: str
    role: str
    available: bool
    executable: str | None
    version: str | None
    status: str
    duration_ms: float | None
    return_code: int | None = None
    error: str | None = None

TOOLCHAINS: tuple[Toolchain, ...] = (
    Toolchain("Go", "go", ("version",), "compiled"),
    Toolchain("Rust", "rustc", ("--version",), "compiled"),
    Toolchain("C#/.NET", "dotnet", ("--version",), "managed"),
    Toolchain("Java", "java", ("-version",), "managed"),
    Toolchain("Kotlin", "kotlinc", ("-version",), "managed"),
    Toolchain("Scala", "scala", ("-version",), "managed"),
    Toolchain("Swift", "swift", ("--version",), "compiled"),
    Toolchain("Dart", "dart", ("--version",), "managed"),
    Toolchain("TypeScript/Node", "node", ("--version",), "runtime"),
    Toolchain("Deno", "deno", ("--version",), "runtime"),
    Toolchain("Bun", "bun", ("--version",), "runtime"),
    Toolchain("PHP", "php", ("--version",), "runtime"),
    Toolchain("Perl", "perl", ("-e", "print $^V"), "runtime"),
    Toolchain("Haskell", "ghc", ("--numeric-version",), "compiled"),
    Toolchain("OCaml", "ocamlc", ("-version",), "compiled"),
    Toolchain("Erlang", "erl", ("-noshell", "-eval", "io:format(\"~s\", [erlang:system_info(otp_release)]), halt()."), "runtime"),
    Toolchain("Gleam", "gleam", ("--version",), "compiled"),
    Toolchain("Elm", "elm", ("--version",), "compiled"),
    Toolchain("PureScript", "purs", ("--version",), "compiled"),
    Toolchain("ReScript", "rescript", ("--version",), "compiled"),
    Toolchain("Crystal", "crystal", ("--version",), "compiled"),
    Toolchain("D", "dmd", ("--version",), "compiled"),
    Toolchain("V", "v", ("version",), "compiled"),
    Toolchain("Odin", "odin", ("version",), "compiled"),
    Toolchain("Raku", "raku", ("-v",), "runtime"),
    Toolchain("R", "R", ("--version",), "runtime"),
    Toolchain("Fortran", "gfortran", ("--version",), "compiled"),
    Toolchain("Ada", "gnatmake", ("--version",), "compiled"),
    Toolchain("Free Pascal", "fpc", ("-iV",), "compiled"),
    Toolchain("Forth", "gforth", ("--version",), "runtime"),
    Toolchain("Guile Scheme", "guile", ("--version",), "runtime"),
    Toolchain("Chicken Scheme", "csc", ("-version",), "compiled"),
    Toolchain("Common Lisp", "sbcl", ("--version",), "runtime"),
    Toolchain("Prolog", "swipl", ("--version",), "runtime"),
    Toolchain("Wren", "wren", ("--version",), "runtime"),
    Toolchain("Janet", "janet", ("--version",), "runtime"),
    Toolchain("Fennel", "fennel", ("--version",), "runtime"),
    Toolchain("MoonScript", "moon", ("--version",), "compiled"),
    Toolchain("mruby", "mruby", ("--version",), "runtime"),
    Toolchain("MicroPython", "micropython", ("--version",), "runtime"),
    Toolchain("Starlark/Bazel", "bazel", ("--version",), "build"),
    Toolchain("Jsonnet", "jsonnet", ("--version",), "runtime"),
    Toolchain("CUE", "cue", ("version",), "runtime"),
    Toolchain("Nix", "nix", ("--version",), "build"),
    Toolchain("Lean", "lean", ("--version",), "proof"),
    Toolchain("Idris", "idris2", ("--version",), "proof"),
    Toolchain("Agda", "agda", ("--version",), "proof"),
    Toolchain("Rocq", "rocq", ("--version",), "proof"),
    Toolchain("Dhall", "dhall", ("--version",), "runtime"),
    Toolchain("Mojo", "mojo", ("--version",), "compiled"),
    Toolchain("Roc", "roc", ("--version",), "compiled"),
    Toolchain("Koka", "koka", ("--version",), "compiled"),
    Toolchain("Unison", "unison", ("--version",), "runtime"),
    Toolchain("WebAssembly/wasmtime", "wasmtime", ("--version",), "runtime"),
)

def _version_text(stdout: str, stderr: str) -> str | None:
    joined = "\n".join(part.strip() for part in (stdout, stderr) if part.strip())
    if not joined:
        return None
    first = next((line.strip() for line in joined.splitlines() if line.strip()), "")
    return re.sub(r"\s+", " ", first)[:240] or None

def probe_toolchain(tool: Toolchain, path: str | None = None, timeout: float = 2.0) -> ProbeResult:
    if not 0.1 <= timeout <= 10:
        raise ValueError("timeout must be between 0.1 and 10 seconds")
    executable = shutil.which(tool.command, path=path)
    if executable is None:
        return ProbeResult(tool.language, tool.command, tool.family, tool.role, False,
                           None, None, "missing", None)
    started = time.perf_counter()
    try:
        completed = subprocess.run(
            [executable, *tool.version_args], stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, errors="replace",
            timeout=timeout, check=False, shell=False,
            env={**os.environ, "NO_COLOR": "1", "TERM": "dumb", "LC_ALL": "C"},
        )
    except subprocess.TimeoutExpired:
        elapsed = round((time.perf_counter() - started) * 1000, 2)
        return ProbeResult(tool.language, tool.command, tool.family, tool.role, True,
                           executable, None, "timeout", elapsed, error="version probe timed out")
    except OSError as exc:
        elapsed = round((time.perf_counter() - started) * 1000, 2)
        return ProbeResult(tool.language, tool.command, tool.family, tool.role, True,
                           executable, None, "error", elapsed, error=type(exc).__name__)
    elapsed = round((time.perf_counter() - started) * 1000, 2)
    version = _version_text(completed.stdout, completed.stderr)
    status = "ok" if completed.returncode == 0 and version else "error"
    error = None if status == "ok" else (
        f"version probe exited {completed.returncode}" if completed.returncode else "no version text returned"
    )
    return ProbeResult(tool.language, tool.command, tool.family, tool.role, True,
                       executable, version, status, elapsed, completed.returncode, error)

def inventory(tools: Sequence[Toolchain] = TOOLCHAINS, path: str | None = None,
              timeout: float = 2.0, workers: int = 4) -> list[ProbeResult]:
    if not 1 <= workers <= 16:
        raise ValueError("workers must be between 1 and 16")
    if not 0.1 <= timeout <= 10:
        raise ValueError("timeout must be between 0.1 and 10 seconds")
    with ThreadPoolExecutor(max_workers=workers, thread_name_prefix="reaper-probe") as pool:
        return list(pool.map(lambda item: probe_toolchain(item, path=path, timeout=timeout), tools))

def build_report(results: Sequence[ProbeResult]) -> dict[str, object]:
    records = [asdict(result) for result in results]
    by_family: dict[str, dict[str, int]] = {}
    for result in results:
        group = by_family.setdefault(result.family, {"total": 0, "found": 0, "ok": 0, "failed": 0})
        group["total"] += 1
        group["found"] += int(result.available)
        group["ok"] += int(result.status == "ok")
        group["failed"] += int(result.status in {"timeout", "error"})
    return {
        "schema": "reaper.toolchain-atlas.v1",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "host": {"platform": platform.system(), "release": platform.release(),
                 "architecture": platform.machine(), "python": platform.python_version()},
        "summary": {
            "catalogue_size": len(results),
            "available": sum(result.available for result in results),
            "verified": sum(result.status == "ok" for result in results),
            "missing": sum(result.status == "missing" for result in results),
            "failed": sum(result.status in {"timeout", "error"} for result in results),
        },
        "families": by_family, "toolchains": records,
        "policy": {"source": "fixed_version_probe_arguments", "shell_execution": False,
                   "project_code_execution": False, "bounded_timeout": True},
    }

def render_markdown(report: dict[str, object]) -> str:
    summary = report["summary"]
    lines = [
        "# Reaper Toolchain Atlas", "", f"Generated: {report['generated_at']}", "",
        f"Detected {summary['available']} of {summary['catalogue_size']} toolchains; "
        f"{summary['verified']} answered the version probe, {summary['failed']} probes failed.",
        "", "| Family | Total | Found | Verified | Failed |",
        "|---|---:|---:|---:|---:|",
    ]
    for family, values in report["families"].items():
        lines.append(f"| {family} | {values['total']} | {values['found']} | {values['ok']} | {values['failed']} |")
    lines.extend(["", "| Language | Command | Status | Version |", "|---|---|---|---|"])
    tick = chr(96)
    for item in report["toolchains"]:
        version = (item["version"] or "").replace("|", "\\|")
        lines.append(f"| {item['language']} | {tick}{item['command']}{tick} | {item['status']} | {version} |")
    return "\n".join(lines) + "\n"

def render_table(results: Sequence[ProbeResult]) -> str:
    lines = []
    for item in results:
        version = f" — {item.version}" if item.version else ""
        detail = f" ({item.error})" if item.error else ""
        elapsed = f"{item.duration_ms:.2f}" if item.duration_ms is not None else "-"
        lines.append(f"{item.status:7} {item.language:20} {item.command:14} {elapsed:>8} ms{version}{detail}")
    found = sum(item.available for item in results)
    verified = sum(item.status == "ok" for item in results)
    lines.append(f"\n{found}/{len(results)} present · {verified} version probes verified")
    return "\n".join(lines)

def main(argv: list[str] | None = None) -> int:
    families = sorted({tool.family for tool in TOOLCHAINS})
    parser = argparse.ArgumentParser(description="Read-only inventory of installed language toolchains")
    parser.add_argument("--format", choices=("table", "json", "markdown"), default="table")
    parser.add_argument("--available-only", action="store_true", help="hide toolchains not found on PATH")
    parser.add_argument("--family", choices=families, action="append", help="limit the inventory to a tool family")
    parser.add_argument("--timeout", type=float, default=2.0, help="per-tool version probe timeout (0.1–10 seconds)")
    parser.add_argument("--workers", type=int, default=4, help="parallel probes (1–16; output order remains stable)")
    parser.add_argument("--search-path", help="alternate PATH used only for tool discovery")
    parser.add_argument("--output", help="write the selected report format to a file")
    args = parser.parse_args(argv)
    if not 0.1 <= args.timeout <= 10:
        parser.error("--timeout must be between 0.1 and 10 seconds")
    if not 1 <= args.workers <= 16:
        parser.error("--workers must be between 1 and 16")
    selected = [tool for tool in TOOLCHAINS if not args.family or tool.family in args.family]
    try:
        results = inventory(selected, path=args.search_path, timeout=args.timeout, workers=args.workers)
    except ValueError as exc:
        parser.error(str(exc))
    if args.available_only:
        results = [item for item in results if item.available]
    report = build_report(results)
    if args.format == "json":
        rendered = json.dumps(report, ensure_ascii=False, indent=2) + "\n"
    elif args.format == "markdown":
        rendered = render_markdown(report)
    else:
        rendered = render_table(results) + "\n"
    if args.output:
        target = Path(args.output)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(rendered, encoding="utf-8")
    else:
        sys.stdout.write(rendered)
    return 1 if report["summary"]["failed"] else 0

if __name__ == "__main__":
    raise SystemExit(main())
