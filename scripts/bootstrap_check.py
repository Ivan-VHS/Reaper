#!/usr/bin/env python3
"""Reproducibility preflight for the native bootstrap compiler; not self-hosting."""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path


def capture(binary: Path, *arguments: str) -> str:
    result = subprocess.run(
        [str(binary), *arguments],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )

    if result.returncode:
        command = " ".join(arguments)
        message = result.stderr.strip()
        raise RuntimeError(f"{binary} {command} failed: {message}")

    return result.stdout


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--compiler", type=Path, required=True)
    parser.add_argument(
        "--source",
        type=Path,
        default=Path("examples/hello.rpr"),
    )
    args = parser.parse_args()
    binary = args.compiler.resolve()

    if not binary.is_file():
        raise SystemExit(f"compiler not found: {binary}")

    first_version = capture(binary, "--version")
    second_version = capture(binary, "--version")
    first_tokens = capture(binary, "--tokens", str(args.source))
    second_tokens = capture(binary, "--tokens", str(args.source))

    if first_version != second_version or first_tokens != second_tokens:
        raise SystemExit(
            "bootstrap preflight failed: repeated output is not deterministic"
        )

    print("PASS: native compiler responds deterministically to version and lexer smoke tests")
    print("LIMIT: this is a reproducibility preflight, not a self-hosting compiler proof")


if __name__ == "__main__":
    try:
        main()
    except (OSError, RuntimeError) as error:
        print(f"bootstrap-check: {error}", file=sys.stderr)
        raise SystemExit(1)
