#!/usr/bin/env python3
"""Compile Reaper expressions to x86-64 ELF assembly, then execute the result."""

from __future__ import annotations

import argparse
import subprocess
import tempfile
from pathlib import Path


HARNESS = r"""
#include <stdint.h>
#include <stdlib.h>

int reaper_program(int64_t *result);

int main(int argc, char **argv) {
    if (argc != 3) return 10;

    const int expected_status = atoi(argv[1]);
    const int64_t expected_value = (int64_t)strtoll(argv[2], 0, 10);
    int64_t result = INT64_C(0x123456789abcdef);

    const int status = reaper_program(&result);
    if (status != expected_status) return 11;
    if (status == 0 && result != expected_value) return 12;
    if (status != 0 && result != INT64_C(0x123456789abcdef)) return 13;
    if (reaper_program(0) != 3) return 14;
    return 0;
}
"""


def run(command: list[str]) -> None:
    result = subprocess.run(command, text=True, capture_output=True, check=False)
    if result.returncode:
        raise RuntimeError(
            f"command failed ({result.returncode}): {' '.join(command)}\n"
            f"{result.stdout}{result.stderr}"
        )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--compiler", type=Path, required=True)
    parser.add_argument("--cc", required=True)
    parser.add_argument("--examples-root", type=Path, required=True)
    args = parser.parse_args()

    cases = (
        ("arithmetic.rpr", 0, "64"),
        ("signed-division.rpr", 0, "-3"),
        ("overflow.rpr", 1, "0"),
        ("division-by-zero.rpr", 2, "0"),
        ("division-overflow.rpr", 1, "0"),
    )

    with tempfile.TemporaryDirectory(prefix="reaper-native-") as temporary:
        work = Path(temporary)
        harness = work / "harness.c"
        harness.write_text(HARNESS, encoding="utf-8")

        for filename, expected_status, expected_value in cases:
            assembly = work / f"{filename}.s"
            executable = work / filename.removesuffix(".rpr")
            run([
                str(args.compiler),
                "--emit-asm",
                str(args.examples_root / filename),
                "-o",
                str(assembly),
            ])
            run([args.cc, str(assembly), str(harness), "-o", str(executable)])
            run([str(executable), str(expected_status), expected_value])

    print("native compiler smoke: 5 generated programs assembled and executed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
