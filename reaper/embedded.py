"""Embedded C target discovery, bounded source checks and compile-plan generation.

This module never runs compilers or firmware. It only inspects source text,
checks toolchain names on PATH, and returns an argv-style build plan.
"""
from __future__ import annotations

import re
import shutil
from dataclasses import asdict, dataclass
from typing import Any


MAX_SOURCE_BYTES = 1024 * 1024


@dataclass(frozen=True, slots=True)
class EmbeddedTarget:
    id: str
    architecture: str
    abi: str
    compiler: str
    compiler_candidates: tuple[str, ...]
    word_bits: int
    description: str
    capabilities: tuple[str, ...]
    compile_flags: tuple[str, ...]


_TARGETS = (
    EmbeddedTarget(
        "native-c11", "host-native", "host C ABI", "cc",
        ("cc", "clang", "gcc", "cl"), 0,
        "Portable host-side C11 development and test profile",
        ("host",), ("-std=c11", "-Wall", "-Wextra"),
    ),
    EmbeddedTarget(
        "avr-atmega328p", "AVR8", "avr-gcc ABI", "avr-gcc",
        ("avr-gcc",), 8, "8-bit AVR target profile for ATmega328P",
        ("freestanding", "harvard"), ("-mmcu=atmega328p", "-ffreestanding"),
    ),
    EmbeddedTarget(
        "arm-cortex-m0", "ARM Cortex-M0", "AAPCS", "arm-none-eabi-gcc",
        ("arm-none-eabi-gcc",), 32, "32-bit Cortex-M0 bare-metal profile",
        ("freestanding", "rtos-common"), ("-mcpu=cortex-m0", "-mthumb", "-ffreestanding"),
    ),
    EmbeddedTarget(
        "riscv32-imac", "RISC-V32", "ILP32", "riscv64-unknown-elf-gcc",
        ("riscv64-unknown-elf-gcc",), 32, "32-bit RISC-V IMAC embedded profile",
        ("freestanding", "rtos-common"), ("-march=rv32imac", "-mabi=ilp32", "-ffreestanding"),
    ),
    EmbeddedTarget(
        "msp430-g2553", "MSP430", "MSP430 EABI", "msp430-elf-gcc",
        ("msp430-elf-gcc",), 16, "16-bit MSP430G2553 microcontroller profile",
        ("freestanding", "harvard"), ("-mmcu=msp430g2553", "-ffreestanding"),
    ),
    EmbeddedTarget(
        "xtensa-esp32", "Xtensa LX6", "ESP-IDF Xtensa ABI", "xtensa-esp32-elf-gcc",
        ("xtensa-esp32-elf-gcc",), 32,
        "32-bit ESP32 toolchain profile; board and SDK configuration remain external",
        ("freestanding", "rtos-common"), ("-mlongcalls", "-ffreestanding"),
    ),
    EmbeddedTarget(
        "wasm32-wasi", "WebAssembly32", "WASI", "clang",
        ("clang",), 32, "Portable WebAssembly C target with an explicit WASI runtime boundary",
        ("sandboxed",), ("--target=wasm32-wasi",),
    ),
)


def embedded_targets() -> list[dict[str, Any]]:
    """Return serializable target metadata without probing or executing tools."""
    return [
        {
            **asdict(target),
            "compiler_candidates": list(target.compiler_candidates),
            "capabilities": list(target.capabilities),
            "compile_flags": list(target.compile_flags),
        }
        for target in _TARGETS
    ]


def embedded_profile(name: str) -> dict[str, Any]:
    if not isinstance(name, str):
        raise TypeError("Embedded C profile name must be text")
    for target in _TARGETS:
        if target.id == name.strip().lower():
            return embedded_targets()[_TARGETS.index(target)]
    raise ValueError(f"unknown Embedded C target profile: {name}")


def embedded_toolchain(name: str) -> dict[str, Any]:
    profile = embedded_profile(name)
    executable = next(
        (resolved for candidate in profile["compiler_candidates"]
         if (resolved := shutil.which(candidate)) is not None),
        None,
    )
    return {
        "target": profile["id"],
        "available": executable is not None,
        "executable": executable,
        "candidates": profile["compiler_candidates"],
        "probe": "PATH lookup only; no compiler process was started",
    }


def embedded_inspect(source: str) -> dict[str, Any]:
    """Run bounded lexical heuristics; this is not a C parser or safety proof."""
    if not isinstance(source, str):
        raise TypeError("Embedded C source must be text")
    encoded = source.encode("utf-8")
    if len(encoded) > MAX_SOURCE_BYTES:
        raise ValueError(f"Embedded C source exceeds the {MAX_SOURCE_BYTES}-byte limit")

    def count(pattern: str, flags: int = 0) -> int:
        return len(re.findall(pattern, source, flags))

    includes = count(r"^[ \t]*#[ \t]*include\b", re.MULTILINE)
    heap_calls = count(r"\b(?:malloc|calloc|realloc|free)\s*\(")
    blocking_calls = count(r"\b(?:sleep|usleep|HAL_Delay|vTaskDelay)\s*\(")
    register_markers = count(r"\bvolatile\b|\bGPIO\w*\b|\bPORT\w*\b|\bREG_[A-Z0-9_]+\b|_MMIO")
    host_io_calls = count(r"\b(?:printf|fprintf|fopen)\s*\(")

    warnings = []
    if heap_calls:
        warnings.append("dynamic-allocation")
    if blocking_calls:
        warnings.append("blocking-delay")
    if register_markers:
        warnings.append("register-oriented-code")
    if host_io_calls:
        warnings.append("host-io")

    return {
        "source_bytes": len(encoded),
        "line_count": source.count("\n") + (1 if source else 0),
        "include_count": includes,
        "heap_calls": heap_calls,
        "blocking_calls": blocking_calls,
        "register_markers": register_markers,
        "host_io_calls": host_io_calls,
        "warnings": warnings,
        "executed": False,
        "note": "Lexical advisory only; comments and string literals may affect counts.",
    }


def embedded_build_plan(target_name: str, source: str, output: str = "firmware.elf") -> dict[str, Any]:
    """Create an explicit argv list. No subprocess, shell, linker script or flashing is run."""
    if not isinstance(source, str) or not source.strip() or "\0" in source:
        raise ValueError("source must be a non-empty path")
    if not isinstance(output, str) or not output.strip() or "\0" in output:
        raise ValueError("output must be a non-empty path")
    profile = embedded_profile(target_name)
    toolchain = embedded_toolchain(target_name)
    compiler = toolchain["executable"] or profile["compiler"]
    flags = list(profile["compile_flags"])
    if target_name != "native-c11":
        flags.extend(("-std=c11", "-Os", "-Wall", "-Wextra"))
    command = [compiler, *flags, source, "-o", output]
    return {
        "target": profile["id"],
        "compiler": compiler,
        "compiler_available": toolchain["available"],
        "command": command,
        "shell": False,
        "executed": False,
        "deployment": "not performed",
        "note": "Review and run this command explicitly with a trusted toolchain and board-specific linker configuration.",
    }
