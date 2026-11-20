"""Small, explicit Embedded C project tooling for Reaper Studio and the CLI.

The build path invokes a user-installed cross compiler with an argv vector (never
through a shell). It does not flash devices or silently access hardware.
"""
from __future__ import annotations

import argparse
import json
import re
import shutil
import struct
import subprocess
import sys
import xml.etree.ElementTree as ET
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any


class EmbeddedError(RuntimeError):
    """An invalid embedded project, profile, or build operation."""


@dataclass(frozen=True)
class Region:
    name: str
    base: int
    size: int


@dataclass(frozen=True)
class McuProfile:
    id: str
    architecture: str
    compiler: str
    flags: tuple[str, ...]
    clock_hz: int
    flash: Region
    sram: Region
    stack_bytes: int

    def to_dict(self) -> dict[str, Any]:
        return {
            "version": 1,
            "id": self.id,
            "architecture": self.architecture,
            "compiler": self.compiler,
            "compiler_flags": list(self.flags),
            "clock_hz": self.clock_hz,
            "flash": asdict(self.flash),
            "sram": asdict(self.sram),
            "stack_bytes": self.stack_bytes,
            "sources": ["src/main.c"],
            "linker_script": "linker.ld",
        }


PROFILES: dict[str, McuProfile] = {
    "cortex-m4-reference": McuProfile(
        "cortex-m4-reference", "arm-cortex-m", "arm-none-eabi-gcc",
        ("-mcpu=cortex-m4", "-mthumb"), 84_000_000,
        Region("FLASH", 0x08000000, 512 * 1024),
        Region("SRAM", 0x20000000, 128 * 1024), 2048,
    ),
    "riscv32imc-reference": McuProfile(
        "riscv32imc-reference", "riscv32", "riscv64-unknown-elf-gcc",
        ("-march=rv32imc", "-mabi=ilp32"), 50_000_000,
        Region("FLASH", 0x20000000, 256 * 1024),
        Region("SRAM", 0x80000000, 64 * 1024), 2048,
    ),
    "avr-atmega328p": McuProfile(
        "avr-atmega328p", "avr", "avr-gcc", ("-mmcu=atmega328p",),
        16_000_000, Region("FLASH", 0, 32 * 1024),
        Region("SRAM", 0x800100, 2 * 1024), 256,
    ),
}

MAIN_TEMPLATE = """#include <stdint.h>

/* A hardware-neutral bring-up loop.
 * Replace this counter with SVD-derived, device-specific GPIO operations.
 * This example deliberately does not guess a vendor's MMIO addresses.
 */
static volatile uint32_t heartbeat;

int main(void)
{
    for (;;) {
        heartbeat++;
    }
}
"""


def _positive_int(value: Any, field: str, allow_zero: bool = False) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise EmbeddedError(f"{field} must be an integer")
    if value < (0 if allow_zero else 1):
        raise EmbeddedError(f"{field} must be {'non-negative' if allow_zero else 'positive'}")
    return value


def profile_from_dict(raw: dict[str, Any]) -> McuProfile:
    if not isinstance(raw, dict):
        raise EmbeddedError("embedded profile must be a JSON object")
    if raw.get("version", 1) != 1:
        raise EmbeddedError("unsupported embedded profile version")

    def region(key: str) -> Region:
        item = raw.get(key)
        if not isinstance(item, dict):
            raise EmbeddedError(f"profile is missing the {key} memory region")
        base = _positive_int(item.get("base"), f"{key}.base", allow_zero=True)
        size = _positive_int(item.get("size"), f"{key}.size")
        if base + size > 0x1_0000_0000:
            raise EmbeddedError(f"{key} region exceeds the 32-bit address space")
        name = str(item.get("name", key.upper()))
        if not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", name):
            raise EmbeddedError(f"{key}.name must be a linker-safe identifier")
        return Region(name, base, size)

    flash, sram = region("flash"), region("sram")
    if flash.base < sram.base + sram.size and sram.base < flash.base + flash.size:
        raise EmbeddedError("FLASH and SRAM regions overlap")
    flags = raw.get("compiler_flags", [])
    if not isinstance(flags, list) or not all(isinstance(x, str) and x for x in flags):
        raise EmbeddedError("compiler_flags must be a list of non-empty strings")
    profile = McuProfile(
        id=str(raw.get("id", raw.get("name", "custom"))),
        architecture=str(raw.get("architecture", "custom")),
        compiler=str(raw.get("compiler", "")),
        flags=tuple(flags),
        clock_hz=_positive_int(raw.get("clock_hz", 1), "clock_hz"),
        flash=flash,
        sram=sram,
        stack_bytes=_positive_int(raw.get("stack_bytes", 0), "stack_bytes", allow_zero=True),
    )
    if not profile.id or not profile.compiler or profile.stack_bytes > sram.size:
        raise EmbeddedError("profile requires id/compiler and stack_bytes <= SRAM size")
    return profile


def list_profiles() -> list[dict[str, Any]]:
    return [PROFILES[key].to_dict() for key in sorted(PROFILES)]


def get_profile(profile_id: str) -> McuProfile:
    try:
        return PROFILES[profile_id]
    except KeyError as error:
        raise EmbeddedError(f"unknown MCU profile: {profile_id}") from error


def linker_script(profile: McuProfile) -> str:
    return f"""/* Generated reference linker script; verify addresses against the MCU datasheet. */
ENTRY(main)
MEMORY
{{
  {profile.flash.name} (rx)  : ORIGIN = 0x{profile.flash.base:08X}, LENGTH = {profile.flash.size}
  {profile.sram.name} (rwx) : ORIGIN = 0x{profile.sram.base:08X}, LENGTH = {profile.sram.size}
}}
_estack = ORIGIN({profile.sram.name}) + LENGTH({profile.sram.name}) - {profile.stack_bytes};
SECTIONS
{{
  .text : {{ KEEP(*(.isr_vector)) *(.text*) *(.rodata*) }} > {profile.flash.name}
  .data : {{ _sdata = .; *(.data*) _edata = .; }} > {profile.sram.name} AT> {profile.flash.name}
  .bss (NOLOAD) : {{ _sbss = .; *(.bss*) *(COMMON) _ebss = .; }} > {profile.sram.name}
  .noinit (NOLOAD) : {{ *(.noinit*) }} > {profile.sram.name}
  /DISCARD/ : {{ *(.comment*) *(.note*) }}
}}
"""


def init_project(directory: str | Path, profile_id: str = "cortex-m4-reference",
                 force: bool = False) -> Path:
    root = Path(directory).expanduser().resolve()
    profile = get_profile(profile_id)
    root.mkdir(parents=True, exist_ok=True)
    files = {
        root / "embedded.json": json.dumps(profile.to_dict(), indent=2) + "\n",
        root / "linker.ld": linker_script(profile),
        root / "src" / "main.c": MAIN_TEMPLATE,
    }
    conflicts = [str(path) for path in files if path.exists()]
    if conflicts and not force:
        raise EmbeddedError("refusing to overwrite existing files: " + ", ".join(conflicts))
    for path, body in files.items():
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(body, encoding="utf-8", newline="\n")
    return root


def load_project(directory: str | Path) -> tuple[Path, dict[str, Any], McuProfile]:
    root = Path(directory).expanduser().resolve()
    config_path = root / "embedded.json"
    try:
        raw = json.loads(config_path.read_text(encoding="utf-8"))
    except OSError as error:
        raise EmbeddedError(f"cannot read {config_path}: {error}") from error
    except json.JSONDecodeError as error:
        raise EmbeddedError(f"invalid JSON in {config_path}: {error}") from error
    profile = profile_from_dict(raw)
    return root, raw, profile


def _inside_project(root: Path, relative: str) -> Path:
    candidate = (root / relative).resolve()
    try:
        candidate.relative_to(root)
    except ValueError as error:
        raise EmbeddedError(f"project path escapes its root: {relative}") from error
    return candidate


def parse_diagnostics(output: str) -> list[dict[str, Any]]:
    pattern = re.compile(
        r"^(?P<file>.*?):(?P<line>\d+)(?::(?P<column>\d+))?:\s*"
        r"(?P<severity>fatal error|error|warning|note):\s*(?P<message>.*)$"
    )
    results = []
    for line in output.splitlines():
        match = pattern.match(line.strip())
        if match:
            item = match.groupdict()
            item["line"] = int(item["line"])
            item["column"] = int(item["column"]) if item["column"] else None
            results.append(item)
    return results


def parse_size_output(output: str) -> dict[str, int]:
    sections: dict[str, int] = {}
    for line in output.splitlines():
        match = re.match(r"^\s*(\.[A-Za-z0-9_.$-]+)\s+(\d+)(?:\s+0x[0-9a-fA-F]+)?\s*$", line)
        if match:
            sections[match.group(1)] = int(match.group(2))
    return sections


def parse_map_file(path: str | Path) -> dict[str, int]:
    sections: dict[str, int] = {}
    pattern = re.compile(r"^\s*(\.[A-Za-z0-9_.$-]+)\s+0x[0-9a-fA-F]+\s+0x([0-9a-fA-F]+)")
    try:
        lines = Path(path).read_text(encoding="utf-8", errors="replace").splitlines()
    except OSError:
        return sections
    for line in lines:
        match = pattern.match(line)
        if match:
            name, size_hex = match.groups()
            sections[name] = max(sections.get(name, 0), int(size_hex, 16))
    return sections


def memory_budget(profile: McuProfile, sections: dict[str, int]) -> dict[str, Any]:
    def total(names: tuple[str, ...]) -> int:
        return sum(max(0, int(sections.get(name, 0))) for name in names)
    text = total((".text", ".isr_vector"))
    rodata = total((".rodata",))
    data = total((".data",))
    bss = total((".bss", ".noinit"))
    flash_used = text + rodata + data
    sram_used = data + bss + profile.stack_bytes
    return {
        "flash_used": flash_used,
        "flash_total": profile.flash.size,
        "flash_percent": round(flash_used * 100.0 / profile.flash.size, 3),
        "flash_ok": flash_used <= profile.flash.size,
        "sram_static_used": data + bss,
        "stack_reserved": profile.stack_bytes,
        "sram_used_with_stack": sram_used,
        "sram_total": profile.sram.size,
        "sram_percent": round(sram_used * 100.0 / profile.sram.size, 2),
        "sram_ok": sram_used <= profile.sram.size,
        "sections": dict(sorted(sections.items())),
    }


def _tool_path(name: str) -> str | None:
    candidate = Path(name).expanduser()
    if candidate.is_absolute() or candidate.parent != Path("."):
        return str(candidate.resolve()) if candidate.is_file() else None
    return shutil.which(name)


def _run(command: list[str], cwd: Path, timeout: float) -> subprocess.CompletedProcess[str]:
    try:
        return subprocess.run(
            command, cwd=str(cwd), capture_output=True, text=True,
            encoding="utf-8", errors="replace", timeout=timeout, check=False,
        )
    except subprocess.TimeoutExpired as error:
        raise EmbeddedError(f"toolchain timed out after {timeout:g}s: {command[0]}") from error
    except OSError as error:
        raise EmbeddedError(f"could not start toolchain {command[0]}: {error}") from error


def build_project(directory: str | Path, timeout: float = 90.0) -> dict[str, Any]:
    if timeout <= 0 or timeout > 900:
        raise EmbeddedError("build timeout must be in the range (0, 900] seconds")
    root, raw, profile = load_project(directory)
    compiler = _tool_path(profile.compiler)
    if not compiler:
        raise EmbeddedError(
            f"cross compiler not found: {profile.compiler}. Install the matching GNU toolchain "
            "and add it to PATH; discovery itself never installs or runs tools."
        )
    extra_flags = raw.get("extra_flags", [])
    if not isinstance(extra_flags, list) or not all(isinstance(x, str) and x for x in extra_flags):
        raise EmbeddedError("extra_flags must be a list of non-empty strings")
    sources_raw = raw.get("sources", ["src/main.c"])
    if not isinstance(sources_raw, list) or not sources_raw:
        raise EmbeddedError("sources must be a non-empty list")
    sources = []
    for entry in sources_raw:
        if not isinstance(entry, str) or not entry.endswith((".c", ".S", ".s")):
            raise EmbeddedError(f"unsupported source entry: {entry!r}")
        path = _inside_project(root, entry)
        if not path.is_file():
            raise EmbeddedError(f"source file does not exist: {entry}")
        sources.append(str(path))
    linker = _inside_project(root, str(raw.get("linker_script", "linker.ld")))
    if not linker.is_file():
        raise EmbeddedError(f"linker script does not exist: {linker}")
    build_dir = root / "build"
    build_dir.mkdir(exist_ok=True)
    elf, map_path = build_dir / "firmware.elf", build_dir / "firmware.map"
    command = [
        compiler, *profile.flags, *extra_flags,
        "-std=c11", "-ffreestanding", "-fno-builtin",
        "-fdata-sections", "-ffunction-sections", "-nostdlib",
        f"-Wl,-Map={map_path}", "-Wl,--gc-sections", f"-T{linker}",
        *sources, "-o", str(elf),
    ]
    result = _run(command, root, timeout)
    combined = (result.stdout or "") + (result.stderr or "")
    diagnostics = parse_diagnostics(combined)
    if result.returncode != 0:
        detail = "\n".join(f"{d['file']}:{d['line']}: {d['severity']}: {d['message']}" for d in diagnostics)
        raise EmbeddedError(
            f"build failed with exit code {result.returncode}\n{detail or combined.strip() or 'compiler returned no diagnostics'}"
        )
    if not elf.is_file():
        raise EmbeddedError("compiler reported success but firmware.elf was not created")
    sections: dict[str, int] = {}
    compiler_name = Path(profile.compiler).name
    size_tool_name = re.sub(r"gcc(?:\.exe)?$", "size", compiler_name, flags=re.IGNORECASE)
    size_tool = _tool_path(size_tool_name) if size_tool_name != compiler_name else None
    if size_tool:
        size_result = _run([size_tool, "-A", str(elf)], root, min(timeout, 20.0))
        sections = parse_size_output(size_result.stdout) if size_result.returncode == 0 else {}
    if not sections:
        sections = parse_map_file(map_path)
    budget = memory_budget(profile, sections)
    artifacts = {"elf": str(elf), "map": str(map_path)}
    objcopy_name = re.sub(r"gcc(?:\.exe)?$", "objcopy", compiler_name, flags=re.IGNORECASE)
    objcopy = _tool_path(objcopy_name) if objcopy_name != compiler_name else None
    if objcopy:
        for suffix, fmt in (("bin", "binary"), ("hex", "ihex")):
            output = build_dir / f"firmware.{suffix}"
            copy_result = _run([objcopy, "-O", fmt, str(elf), str(output)], root, min(timeout, 20.0))
            if copy_result.returncode == 0 and output.is_file():
                artifacts[suffix] = str(output)
            elif copy_result.stderr:
                diagnostics.extend(parse_diagnostics(copy_result.stderr))
    return {
        "ok": True,
        "compiler": compiler,
        "command": command,
        "diagnostics": diagnostics,
        "artifacts": artifacts,
        "budget": budget,
        "over_budget": not (budget["flash_ok"] and budget["sram_ok"]),
    }


@dataclass
class SimRegister:
    name: str
    address: int
    value: int = 0
    writable_mask: int = 0xFFFFFFFF
    access: str = "read-write"


class RegisterBank:
    """Deterministic simulated MMIO register bank; never maps host addresses."""
    def __init__(self) -> None:
        self._registers: dict[str, SimRegister] = {}

    def add(self, register: SimRegister) -> None:
        if not register.name or register.name in self._registers:
            raise EmbeddedError(f"duplicate or empty register name: {register.name!r}")
        if not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_.]*", register.name):
            raise EmbeddedError("register name contains unsupported characters")
        if not 0 <= register.address <= 0xFFFFFFFF:
            raise EmbeddedError("register address must fit in 32 bits")
        if not 0 <= register.value <= 0xFFFFFFFF or not 0 <= register.writable_mask <= 0xFFFFFFFF:
            raise EmbeddedError("register value and writable mask must fit in uint32")
        if register.access not in {"read-only", "write-only", "read-write"}:
            raise EmbeddedError(f"unsupported register access mode: {register.access}")
        if register.access == "read-only" and register.writable_mask:
            raise EmbeddedError("read-only register cannot have writable bits")
        self._registers[register.name] = register

    def read(self, name: str) -> int:
        try:
            register = self._registers[name]
        except KeyError as error:
            raise EmbeddedError(f"unknown simulated register: {name}") from error
        if register.access == "write-only":
            raise EmbeddedError(f"register is write-only: {name}")
        return register.value

    def write(self, name: str, value: int) -> int:
        try:
            register = self._registers[name]
        except KeyError as error:
            raise EmbeddedError(f"unknown simulated register: {name}") from error
        if register.access == "read-only":
            raise EmbeddedError(f"register is read-only: {name}")
        if not isinstance(value, int) or value < 0 or value > 0xFFFFFFFF:
            raise EmbeddedError("register value must fit in uint32")
        if value & ~register.writable_mask:
            raise EmbeddedError(f"write touches reserved/read-only bits: {name}")
        register.value = (register.value & ~register.writable_mask) | value
        return register.value

    def snapshot(self) -> dict[str, dict[str, int | str]]:
        return {
            name: {"address": item.address, "value": item.value,
                   "writable_mask": item.writable_mask, "access": item.access}
            for name, item in sorted(self._registers.items())
        }


def load_svd(path: str | Path) -> RegisterBank:
    """Import the common CMSIS-SVD peripheral/register subset using stdlib XML."""
    bank = RegisterBank()
    try:
        root = ET.parse(path).getroot()
    except (OSError, ET.ParseError) as error:
        raise EmbeddedError(f"cannot parse SVD file: {error}") from error
    for peripheral in root.findall(".//peripheral"):
        base_node = peripheral.find("baseAddress")
        if base_node is None or not base_node.text:
            continue
        base = int(base_node.text.strip(), 0)
        for node in peripheral.findall("./registers/register"):
            name_node, offset_node = node.find("name"), node.find("addressOffset")
            if name_node is None or offset_node is None or not name_node.text or not offset_node.text:
                continue
            name = f"{peripheral.findtext('name', 'PERIPH')}.{name_node.text.strip()}"
            reset = int((node.findtext("resetValue") or "0").strip(), 0)
            access = (node.findtext("access") or "read-write").strip()
            if access not in {"read-only", "write-only", "read-write"}:
                continue
            mask = 0 if access == "read-only" else 0xFFFFFFFF
            bank.add(SimRegister(name, base + int(offset_node.text.strip(), 0), reset, mask, access))
    return bank


def crc8(data: bytes) -> int:
    crc = 0
    for value in data:
        crc ^= value
        for _ in range(8):
            crc = ((crc << 1) ^ 0x07) & 0xFF if crc & 0x80 else (crc << 1) & 0xFF
    return crc


def encode_telemetry_frame(command: int, payload: bytes = b"") -> bytes:
    if not 0 <= command <= 255 or len(payload) > 4096:
        raise EmbeddedError("telemetry command must be uint8 and payload <= 4096 bytes")
    body = bytes((command,)) + struct.pack("<H", len(payload)) + payload
    return b"\xA5" + body + bytes((crc8(body),))


class TelemetryDecoder:
    """Incremental A5/command/length/payload/CRC8 telemetry decoder."""
    def __init__(self, max_payload: int = 4096) -> None:
        if not 0 <= max_payload <= 4096:
            raise EmbeddedError("max_payload must be 0..4096")
        self.max_payload = max_payload
        self._buffer = bytearray()

    def feed(self, chunk: bytes) -> list[tuple[int, bytes]]:
        self._buffer.extend(chunk)
        frames: list[tuple[int, bytes]] = []
        while True:
            try:
                start = self._buffer.index(0xA5)
            except ValueError:
                self._buffer.clear()
                break
            if start:
                del self._buffer[:start]
            if len(self._buffer) < 5:
                break
            command = self._buffer[1]
            length = self._buffer[2] | (self._buffer[3] << 8)
            if length > self.max_payload:
                del self._buffer[0]
                continue
            frame_size = 1 + 1 + 2 + length + 1
            if len(self._buffer) < frame_size:
                break
            body = bytes(self._buffer[1:4 + length])
            expected = self._buffer[4 + length]
            if crc8(body) == expected:
                frames.append((command, bytes(self._buffer[4:4 + length])))
                del self._buffer[:frame_size]
            else:
                del self._buffer[0]
        return frames


def inspect_project(directory: str | Path) -> dict[str, Any]:
    root, raw, profile = load_project(directory)
    return {
        "project": str(root),
        "profile": profile.to_dict(),
        "toolchain": _tool_path(profile.compiler) is not None,
        "sources": list(raw.get("sources", ["src/main.c"])),
        "linker_script": str(_inside_project(root, str(raw.get("linker_script", "linker.ld")))),
        "build_directory": str(root / "build"),
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="reaper embedded", description="Embedded C project workbench")
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser("profiles", help="list built-in reference MCU profiles")
    profile_parser = commands.add_parser("profile", help="show one profile as JSON")
    profile_parser.add_argument("profile_id", choices=sorted(PROFILES))
    init_parser = commands.add_parser("init", help="create a starter Embedded C project")
    init_parser.add_argument("directory")
    init_parser.add_argument("--profile", default="cortex-m4-reference", choices=sorted(PROFILES))
    init_parser.add_argument("--force", action="store_true", help="replace the three generated starter files")
    for name in ("inspect", "build"):
        item = commands.add_parser(name, help=f"{name} an Embedded C project")
        item.add_argument("directory")
    commands.choices["build"].add_argument("--timeout", type=float, default=90.0)
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        if args.command == "profiles":
            print(json.dumps(list_profiles(), indent=2))
        elif args.command == "profile":
            print(json.dumps(get_profile(args.profile_id).to_dict(), indent=2))
        elif args.command == "init":
            root = init_project(args.directory, args.profile, args.force)
            print(f"Embedded C project created: {root}")
            print("Review embedded.json and linker.ld against the exact MCU datasheet before flashing.")
        elif args.command == "inspect":
            print(json.dumps(inspect_project(args.directory), indent=2))
        elif args.command == "build":
            result = build_project(args.directory, args.timeout)
            print(json.dumps(result, indent=2))
            if result["over_budget"]:
                print("WARNING: linked image exceeds the configured FLASH/SRAM budget.", file=sys.stderr)
                return 3
        return 0
    except (EmbeddedError, OSError, ValueError) as error:
        print(f"reaper embedded: {error}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
