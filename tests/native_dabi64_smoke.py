#!/usr/bin/env python3
"""Assemble, link and execute programs using the DuckOS DABI64 v1 convention."""

from __future__ import annotations

import argparse
import subprocess
import tempfile
from pathlib import Path


HARNESS = r"""
#include <stdint.h>
#include <stdlib.h>

typedef struct {
    uint64_t payload;
    uint32_t kind;
    uint32_t flags;
} DuckValue;

typedef struct {
    DuckValue value;
} DuckCallResult;

typedef struct {
    uint32_t magic;
    uint16_t major;
    uint16_t minor;
    uint32_t byte_size;
    uint32_t argument_count;
    uint32_t capture_count;
    uint32_t flags;
    uint32_t reserved0;
    uint32_t reserved1;
    const DuckValue *arguments;
    const DuckValue *captures;
} DuckCallFrame;

int duck_program(void);

static int invoke(const DuckCallFrame *frame, DuckCallResult *result) {
    long status;
    __asm__ volatile(
        "movq %%rsp, %%rbx\n\t"
        "andq $-32, %%rsp\n\t"
        "movq %1, %%r10\n\t"
        "movq %2, %%r11\n\t"
        "call duck_program\n\t"
        "movq %%rbx, %%rsp\n\t"
        : "=a"(status)
        : "r"(frame), "r"(result)
        : "rbx", "rcx", "rdx", "rsi", "rdi",
          "r8", "r9", "r10", "r11", "memory", "cc"
    );
    return (int)status;
}

int main(int argc, char **argv) {
    if (argc != 3) return 20;

    const int expected_status = atoi(argv[1]);
    const int64_t expected_value = (int64_t)strtoll(argv[2], 0, 10);
    DuckCallFrame frame __attribute__((aligned(16))) = {
        UINT32_C(0x49424144), 1, 0, sizeof(DuckCallFrame),
        0, 0, 0, 0, 0, 0, 0
    };
    DuckCallResult result __attribute__((aligned(16))) = {
        { UINT64_C(0x123456789abcdef), 2, 0 }
    };

    const int status = invoke(&frame, &result);
    if (status != expected_status) return 21;
    if (status == 0 && (result.value.payload != (uint64_t)expected_value ||
                        result.value.kind != 1 || result.value.flags != 0)) return 22;
    if (status != 0 && result.value.payload != UINT64_C(0x123456789abcdef)) return 23;

    if (invoke(&frame, 0) != 1) return 24;
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
        ("arithmetic.rpr", 0, "65"),
        ("signed-division.rpr", 0, "-3"),
        ("overflow.rpr", 16, "0"),
        ("division-by-zero.rpr", 17, "0"),
        ("division-overflow.rpr", 16, "0"),
    )

    with tempfile.TemporaryDirectory(prefix="reaper-dabi64-") as temporary:
        work = Path(temporary)
        caller = work / "caller.c"
        caller.write_text(HARNESS, encoding="utf-8")

        for filename, expected_status, expected_value in cases:
            assembly = work / f"{filename}.s"
            executable = work / filename.removesuffix(".rpr")
            run([
                str(args.compiler), "--emit-asm", "--target", "duckos-dabi64-v1",
                str(args.examples_root / filename), "-o", str(assembly),
            ])
            run([args.cc, str(assembly), str(caller), "-o", str(executable)])
            run([str(executable), str(expected_status), expected_value])

    print("DuckOS DABI64 smoke: 5 programs assembled, linked and executed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
