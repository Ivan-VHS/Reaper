#!/usr/bin/env python3
# Copyright (c) 2026 Ivan-VHS
# SPDX-License-Identifier: Apache-2.0
"""Inventory installed language toolchains without invoking project code."""
from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
from dataclasses import asdict, dataclass
from typing import Sequence


@dataclass(frozen=True)
class Toolchain:
    language: str
    command: str
    version_args: tuple[str, ...]
    family: str


@dataclass(frozen=True)
class ProbeResult:
    language: str
    command: str
    family: str
    available: bool
    executable: str | None
    version: str | None
    error: str | None = None


# This is a capability catalogue, not a bundled copy of any listed compiler.
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
    executable = shutil.which(tool.command, path=path)
    if executable is None:
        return ProbeResult(tool.language, tool.command, tool.family, False, None, None)

    try:
        completed = subprocess.run(
            [executable, *tool.version_args],
            stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            errors="replace",
            timeout=timeout,
            check=False,
            shell=False,
            env={**os.environ, "NO_COLOR": "1", "TERM": "dumb"},
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        return ProbeResult(tool.language, tool.command, tool.family, True, executable, None, type(exc).__name__)

    version = _version_text(completed.stdout, completed.stderr)
    error = None if completed.returncode == 0 else f"version probe exited {completed.returncode}"
    return ProbeResult(tool.language, tool.command, tool.family, True, executable, version, error)


def inventory(tools: Sequence[Toolchain] = TOOLCHAINS, path: str | None = None, timeout: float = 2.0) -> list[ProbeResult]:
    return [probe_toolchain(tool, path=path, timeout=timeout) for tool in tools]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Read-only inventory of installed programming-language toolchains")
    parser.add_argument("--json", action="store_true", help="emit machine-readable JSON")
    parser.add_argument("--available-only", action="store_true", help="hide toolchains not found on PATH")
    parser.add_argument("--timeout", type=float, default=2.0, help="per-tool version probe timeout (0.1–10 seconds)")
    args = parser.parse_args(argv)
    if not 0.1 <= args.timeout <= 10:
        parser.error("--timeout must be between 0.1 and 10 seconds")

    results = inventory(timeout=args.timeout)
    if args.available_only:
        results = [result for result in results if result.available]
    if args.json:
        print(json.dumps([asdict(result) for result in results], ensure_ascii=False, indent=2))
    else:
        for result in results:
            state = "FOUND" if result.available else "missing"
            version = f" — {result.version}" if result.version else ""
            note = f" ({result.error})" if result.error else ""
            print(f"{state:7} {result.language:20} {result.command}{version}{note}")
        found = sum(result.available for result in results)
        print(f"\n{found}/{len(results)} toolchains detected")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
