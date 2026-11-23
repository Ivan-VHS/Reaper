#!/usr/bin/env python3
"""Verify complete DABI64 Reaper source can become a DuckOS-marked ELF object."""

from __future__ import annotations

import argparse
import subprocess
import tempfile
from pathlib import Path


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
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--assembler-script", type=Path, required=True)
    args = parser.parse_args()

    with tempfile.TemporaryDirectory(prefix="reaper-dabi64-object-") as directory:
        work = Path(directory)
        assembly = work / "program.s"
        object_file = work / "program.o"

        run([
            str(args.compiler),
            "--emit-asm",
            "--target",
            "duckos-dabi64-v1",
            str(args.source),
            "-o",
            str(assembly),
        ])
        run([
            "python3",
            str(args.assembler_script),
            "--cc",
            args.cc,
            "--assembly",
            str(assembly),
            "--object",
            str(object_file),
        ])

        data = object_file.read_bytes()
        if data[:4] != b"\x7fELF" or data[4] != 2 or data[5] != 1:
            raise RuntimeError("expected an ELF64 little-endian object")
        if data[7] != 0xD5:
            raise RuntimeError(f"wrong DuckOS EI_OSABI marker: 0x{data[7]:02x}")

    print("DuckOS object smoke: complete DABI64 program assembled to ELF64 ET_REL")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
