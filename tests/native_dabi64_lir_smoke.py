#!/usr/bin/env python3
"""Compile a complete scalar Reaper program for the DuckOS DABI64 v1 ABI."""

from __future__ import annotations

import argparse
import subprocess
import tempfile
from pathlib import Path


CALLER = r"""
#include "dabi64_lir_abi.h"

#include <stdint.h>
#include <string.h>

int duck_program(void);
int duck_fn_2(void);
int duck_fn_3(void);
int duck_fn_4(void);

static int invoke_program(const DuckCallFrame *frame, DuckCallResult *result) {
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

static int invoke_calculate(const DuckCallFrame *frame, DuckCallResult *result) {
    long status;
    __asm__ volatile(
        "movq %%rsp, %%rbx\n\t"
        "andq $-32, %%rsp\n\t"
        "movq %1, %%r10\n\t"
        "movq %2, %%r11\n\t"
        "call duck_fn_2\n\t"
        "movq %%rbx, %%rsp\n\t"
        : "=a"(status)
        : "r"(frame), "r"(result)
        : "rbx", "rcx", "rdx", "rsi", "rdi",
          "r8", "r9", "r10", "r11", "memory", "cc"
    );
    return (int)status;
}

static int invoke_overflow(const DuckCallFrame *frame, DuckCallResult *result) {
    long status;
    __asm__ volatile(
        "movq %%rsp, %%rbx\n\t"
        "andq $-32, %%rsp\n\t"
        "movq %1, %%r10\n\t"
        "movq %2, %%r11\n\t"
        "call duck_fn_3\n\t"
        "movq %%rbx, %%rsp\n\t"
        : "=a"(status)
        : "r"(frame), "r"(result)
        : "rbx", "rcx", "rdx", "rsi", "rdi",
          "r8", "r9", "r10", "r11", "memory", "cc"
    );
    return (int)status;
}

static int invoke_divide(const DuckCallFrame *frame, DuckCallResult *result) {
    long status;
    __asm__ volatile(
        "movq %%rsp, %%rbx\n\t"
        "andq $-32, %%rsp\n\t"
        "movq %1, %%r10\n\t"
        "movq %2, %%r11\n\t"
        "call duck_fn_4\n\t"
        "movq %%rbx, %%rsp\n\t"
        : "=a"(status)
        : "r"(frame), "r"(result)
        : "rbx", "rcx", "rdx", "rsi", "rdi",
          "r8", "r9", "r10", "r11", "memory", "cc"
    );
    return (int)status;
}

static void init_frame(
    DuckCallFrame *frame,
    uint32_t argument_count,
    const DuckValue *arguments
) {
    memset(frame, 0, sizeof *frame);
    frame->magic = DUCK_ABI_MAGIC;
    frame->abi_major = DUCK_ABI_MAJOR;
    frame->abi_minor = DUCK_ABI_MINOR;
    frame->byte_size = sizeof *frame;
    frame->argument_count = argument_count;
    frame->arguments = arguments;
}

static void init_result(DuckCallResult *result) {
    result->value.payload = UINT64_C(0x123456789abcdef);
    result->value.kind = DUCK_VALUE_UNIT;
    result->value.flags = 0;
}

int main(void) {
    DuckCallFrame frame __attribute__((aligned(16)));
    DuckCallResult result __attribute__((aligned(16)));
    DuckValue argument __attribute__((aligned(16))) = {3, DUCK_VALUE_I64, 0};

    init_frame(&frame, 0, 0);
    init_result(&result);
    if (invoke_program(&frame, &result) != DUCK_STATUS_OK) return 20;
    if (result.value.kind != DUCK_VALUE_UNIT || result.value.flags != 0) return 21;

    init_frame(&frame, 1, &argument);
    init_result(&result);
    if (invoke_calculate(&frame, &result) != DUCK_STATUS_OK) return 22;
    if (result.value.payload != 50 || result.value.kind != DUCK_VALUE_I64 ||
        result.value.flags != 0) return 23;

    argument.payload = INT64_MAX;
    init_frame(&frame, 1, &argument);
    init_result(&result);
    uint64_t untouched = result.value.payload;
    if (invoke_overflow(&frame, &result) != 16) return 24;
    if (result.value.payload != untouched) return 25;

    argument.payload = 0;
    init_frame(&frame, 1, &argument);
    init_result(&result);
    untouched = result.value.payload;
    if (invoke_divide(&frame, &result) != 17) return 26;
    if (result.value.payload != untouched) return 27;

    argument.kind = 2;
    init_frame(&frame, 1, &argument);
    init_result(&result);
    untouched = result.value.payload;
    if (invoke_calculate(&frame, &result) != DUCK_STATUS_BAD_ARGUMENT_LAYOUT) return 28;
    if (result.value.payload != untouched) return 29;

    init_frame(&frame, 0, 0);
    init_result(&result);
    frame.magic = 0;
    if (invoke_program(&frame, &result) != 2) return 30;

    frame.magic = DUCK_ABI_MAGIC;
    frame.abi_major = 2;
    if (invoke_program(&frame, &result) != 3) return 31;

    frame.abi_major = DUCK_ABI_MAJOR;
    frame.byte_size = 47;
    if (invoke_program(&frame, &result) != 4) return 32;

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
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--test-include", type=Path, required=True)
    args = parser.parse_args()

    with tempfile.TemporaryDirectory(prefix="reaper-dabi64-lir-") as directory:
        work = Path(directory)
        assembly = work / "program.s"
        caller = work / "caller.c"
        executable = work / "program"
        caller.write_text(CALLER, encoding="utf-8")

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
            args.cc,
            "-std=c11",
            "-O0",
            "-I",
            str(args.test_include),
            str(assembly),
            str(caller),
            "-o",
            str(executable),
        ])
        run([str(executable)])

    print("DuckOS DABI64 LIR smoke: functions, locals, calls, branches and while loops executed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
