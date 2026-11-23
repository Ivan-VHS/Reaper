#!/usr/bin/env python3
"""Assemble Reaper DABI64 GNU assembly and mark the ELF object as DuckOS."""

from __future__ import annotations

import argparse
import struct
import subprocess
from pathlib import Path


ELF_OSABI_DUCKOS = 0xD5
ELF_MACHINE_X86_64 = 62


def run(command: list[str]) -> None:
    result = subprocess.run(command, text=True, capture_output=True, check=False)
    if result.returncode:
        raise RuntimeError(
            f"command failed ({result.returncode}): {' '.join(command)}\n"
            f"{result.stdout}{result.stderr}"
        )


def read_elf_sections(data: bytearray) -> tuple[int, list[str]]:
    if len(data) < 64 or data[:4] != b"\x7fELF":
        raise ValueError("assembler output is not an ELF file")
    if data[4] != 2 or data[5] != 1:
        raise ValueError("DuckOS DABI64 requires ELF64 little-endian objects")

    machine = struct.unpack_from("<H", data, 18)[0]
    if machine != ELF_MACHINE_X86_64:
        raise ValueError(f"expected ELF machine x86-64 (62), got {machine}")

    section_offset = struct.unpack_from("<Q", data, 40)[0]
    section_entry_size = struct.unpack_from("<H", data, 58)[0]
    section_count = struct.unpack_from("<H", data, 60)[0]
    names_index = struct.unpack_from("<H", data, 62)[0]
    if section_count == 0 or names_index >= section_count:
        raise ValueError("ELF section table is missing or malformed")
    if section_entry_size < 64:
        raise ValueError("ELF64 section header entry is too small")
    if section_offset > len(data) or section_count > (len(data) - section_offset) // section_entry_size:
        raise ValueError("ELF section table exceeds the object file")

    def section_at(index: int) -> tuple[int, int, int]:
        offset = section_offset + index * section_entry_size
        name_offset = struct.unpack_from("<I", data, offset)[0]
        file_offset = struct.unpack_from("<Q", data, offset + 24)[0]
        file_size = struct.unpack_from("<Q", data, offset + 32)[0]
        if file_offset > len(data) or file_size > len(data) - file_offset:
            raise ValueError(f"ELF section {index} points outside the object file")
        return name_offset, file_offset, file_size

    _, names_offset, names_size = section_at(names_index)
    names = bytes(data[names_offset:names_offset + names_size])
    sections: list[str] = []
    for index in range(section_count):
        name_offset, _, _ = section_at(index)
        if name_offset >= len(names):
            raise ValueError("ELF section name points outside the string table")
        end = names.find(b"\0", name_offset)
        if end < 0:
            raise ValueError("ELF section name is not terminated")
        sections.append(names[name_offset:end].decode("ascii", errors="strict"))
    return machine, sections


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--cc", required=True, help="host assembler driver, normally cc")
    parser.add_argument("--assembly", type=Path, required=True)
    parser.add_argument("--object", type=Path, required=True)
    args = parser.parse_args()

    args.object.parent.mkdir(parents=True, exist_ok=True)
    run([args.cc, "-c", str(args.assembly), "-o", str(args.object)])

    data = bytearray(args.object.read_bytes())
    _, sections = read_elf_sections(data)
    if ".note.duckos.abi" not in sections:
        raise ValueError("object is missing the .note.duckos.abi contract note")

    data[7] = ELF_OSABI_DUCKOS
    args.object.write_bytes(data)

    verified = bytearray(args.object.read_bytes())
    machine, verified_sections = read_elf_sections(verified)
    if verified[7] != ELF_OSABI_DUCKOS:
        raise ValueError("failed to mark ELF EI_OSABI as DuckOS")
    if ".note.duckos.abi" not in verified_sections:
        raise ValueError("DuckOS ABI note disappeared after object finalization")

    print(
        f"DuckOS object: {args.object} "
        f"(ELF64, machine={machine}, EI_OSABI=0x{verified[7]:02x}, DABI64 note)"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
