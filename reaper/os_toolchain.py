"""Freestanding build driver for Reaper OS projects.

This driver compiles native C and assembly system modules. It deliberately
does not claim to compile general .rpr programs to machine code yet.
"""

from __future__ import annotations

import argparse
import json
import shlex
import shutil
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Sequence


PROJECT_SCHEMA = "reaper.os-project/v1"

TARGETS = {
    "x86_64-unknown-none-elf": {
        "architecture": "x86_64",
        "format": "elf",
        "compile_flags": ("-mno-red-zone",),
    },
    "aarch64-unknown-none-elf": {
        "architecture": "aarch64",
        "format": "elf",
        "compile_flags": (),
    },
    "riscv64-unknown-none-elf": {
        "architecture": "riscv64",
        "format": "elf",
        "compile_flags": (),
    },
}

_ALLOWED_KEYS = {
    "schema",
    "name",
    "target",
    "format",
    "entry",
    "output",
    "sources",
    "include_dirs",
    "linker_script",
    "compiler",
    "linker",
    "optimization",
    "compile_flags",
    "link_flags",
}


class ProjectError(ValueError):
    """A project manifest is incomplete or internally inconsistent."""


@dataclass(frozen=True, slots=True)
class OsProject:
    manifest: Path
    name: str
    target: str
    output_format: str
    entry: str
    output: Path
    sources: tuple[Path, ...]
    include_dirs: tuple[Path, ...]
    linker_script: Path
    compiler: str
    linker: str
    optimization: str
    compile_flags: tuple[str, ...]
    link_flags: tuple[str, ...]


def _resolve(base: Path, value: object, field: str) -> Path:
    if not isinstance(value, str) or not value.strip():
        raise ProjectError(f"{field} must be a non-empty path")
    return (base / value).resolve()


def _string_list(data: dict, key: str, *, required: bool = False) -> tuple[str, ...]:
    value = data.get(key, [])
    if not isinstance(value, list) or (required and not value):
        suffix = " and must not be empty" if required else ""
        raise ProjectError(f"{key} must be a JSON array of strings{suffix}")
    if any(not isinstance(item, str) or not item.strip() or "\x00" in item for item in value):
        raise ProjectError(f"{key} entries must be non-empty strings without NUL bytes")
    return tuple(value)


def load_project(manifest: str | Path) -> OsProject:
    path = Path(manifest).expanduser().resolve()
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except OSError as error:
        raise ProjectError(f"cannot read project manifest {path}: {error}") from error
    except json.JSONDecodeError as error:
        raise ProjectError(f"invalid JSON in {path}:{error.lineno}:{error.colno}: {error.msg}") from error

    if not isinstance(data, dict):
        raise ProjectError("project manifest must contain a JSON object")
    unknown = sorted(set(data) - _ALLOWED_KEYS)
    if unknown:
        raise ProjectError(f"unknown project field(s): {', '.join(unknown)}")
    if data.get("schema") != PROJECT_SCHEMA:
        raise ProjectError(f"schema must be {PROJECT_SCHEMA!r}")

    target = data.get("target")
    if target not in TARGETS:
        available = ", ".join(TARGETS)
        raise ProjectError(f"unsupported target {target!r}; supported targets: {available}")

    output_format = data.get("format", TARGETS[target]["format"])
    if output_format != TARGETS[target]["format"]:
        raise ProjectError(
            f"target {target!r} currently supports {TARGETS[target]['format']!r}, "
            f"not {output_format!r}"
        )

    entry = data.get("entry", "_start")
    if not isinstance(entry, str) or not entry or any(char.isspace() for char in entry):
        raise ProjectError("entry must be a non-empty symbol name without whitespace")

    name = data.get("name", path.parent.name)
    if not isinstance(name, str) or not name.strip():
        raise ProjectError("name must be a non-empty string")

    raw_sources = _string_list(data, "sources", required=True)
    sources = tuple(_resolve(path.parent, item, "sources") for item in raw_sources)
    for source in sources:
        if source.suffix not in {".c", ".s", ".S"}:
            raise ProjectError(f"unsupported source type {source.suffix!r}: {source.name}")

    raw_includes = _string_list(data, "include_dirs")
    include_dirs = tuple(_resolve(path.parent, item, "include_dirs") for item in raw_includes)

    linker_script_value = data.get("linker_script")
    linker_script = _resolve(path.parent, linker_script_value, "linker_script")
    output_value = data.get("output", "build/kernel.elf")
    output = _resolve(path.parent, output_value, "output")

    compiler = data.get("compiler", "clang")
    linker = data.get("linker", "lld")
    optimization = data.get("optimization", "2")
    if not isinstance(compiler, str) or not compiler.strip():
        raise ProjectError("compiler must be a non-empty executable name")
    if linker not in {"lld"}:
        raise ProjectError("linker must be 'lld'; other linker drivers are not wired yet")
    if optimization not in {"0", "1", "2", "3", "s", "z"}:
        raise ProjectError("optimization must be one of: 0, 1, 2, 3, s, z")

    compile_flags = _string_list(data, "compile_flags")
    link_flags = _string_list(data, "link_flags")
    return OsProject(
        manifest=path,
        name=name,
        target=target,
        output_format=output_format,
        entry=entry,
        output=output,
        sources=sources,
        include_dirs=include_dirs,
        linker_script=linker_script,
        compiler=compiler,
        linker=linker,
        optimization=optimization,
        compile_flags=compile_flags,
        link_flags=link_flags,
    )


def validate_project_files(project: OsProject) -> None:
    missing = [path for path in (*project.sources, project.linker_script, *project.include_dirs)
               if not path.exists()]
    if missing:
        rendered = "\n  ".join(str(path) for path in missing)
        raise ProjectError(f"project file(s) not found:\n  {rendered}")
    if not project.linker_script.is_file():
        raise ProjectError(f"linker_script is not a file: {project.linker_script}")
    for source in project.sources:
        if not source.is_file():
            raise ProjectError(f"source is not a file: {source}")
    for include_dir in project.include_dirs:
        if not include_dir.is_dir():
            raise ProjectError(f"include_dirs entry is not a directory: {include_dir}")


def resolve_tool(name: str) -> str | None:
    candidate = Path(name).expanduser()
    if candidate.parent != Path(".") or candidate.is_absolute():
        return str(candidate.resolve()) if candidate.is_file() else None
    return shutil.which(name)


def build_plan(project: OsProject) -> list[list[str]]:
    target = TARGETS[project.target]
    compiler = resolve_tool(project.compiler) or project.compiler
    build_dir = project.output.parent
    commands: list[list[str]] = []
    objects: list[Path] = []

    for index, source in enumerate(project.sources):
        object_path = build_dir / f"{index:02d}-{source.stem}.o"
        objects.append(object_path)
        command = [
            compiler,
            f"--target={project.target}",
            "-ffreestanding",
            "-fno-builtin",
            "-fno-stack-protector",
            "-fno-pic",
            "-fno-pie",
            "-fno-unwind-tables",
            "-fno-asynchronous-unwind-tables",
            f"-O{project.optimization}",
            *target["compile_flags"],
        ]
        if source.suffix == ".c":
            command.extend(["-std=c17", "-Wall", "-Wextra", "-Wpedantic"])
        else:
            command.extend(["-x", "assembler-with-cpp"])
        for include_dir in project.include_dirs:
            command.extend(["-I", str(include_dir)])
        command.extend(project.compile_flags)
        command.extend(["-c", str(source), "-o", str(object_path)])
        commands.append(command)

    link_command = [
        compiler,
        f"--target={project.target}",
        "-fuse-ld=lld",
        "-nostdlib",
        "-static",
        f"-Wl,-T,{project.linker_script}",
        f"-Wl,-e,{project.entry}",
        "-Wl,--build-id=none",
        *project.link_flags,
        *(str(item) for item in objects),
        "-o",
        str(project.output),
    ]
    commands.append(link_command)
    return commands


def _print_command(command: Sequence[str]) -> None:
    print("$ " + shlex.join(command))


def build_project(project: OsProject, *, dry_run: bool = False) -> int:
    validate_project_files(project)
    compiler = resolve_tool(project.compiler)
    linker = shutil.which("ld.lld")
    if compiler is None:
        print(f"reaper os: compiler not found: {project.compiler}", file=sys.stderr)
        return 127
    if linker is None:
        print("reaper os: LLVM lld not found (expected ld.lld on PATH)", file=sys.stderr)
        return 127

    commands = build_plan(project)
    if dry_run:
        for command in commands:
            _print_command(command)
        return 0

    project.output.parent.mkdir(parents=True, exist_ok=True)
    for command in commands:
        _print_command(command)
        try:
            completed = subprocess.run(command, check=False)
        except OSError as error:
            print(f"reaper os: could not start {command[0]}: {error}", file=sys.stderr)
            return 127
        if completed.returncode != 0:
            print(f"reaper os: command failed with exit code {completed.returncode}", file=sys.stderr)
            return completed.returncode
    print(f"Reaper OS: built {project.output} ({project.target}, {project.output_format})")
    return 0


def doctor() -> int:
    tools = (("clang", "clang"), ("LLVM linker", "ld.lld"))
    missing = False
    for label, executable in tools:
        path = shutil.which(executable)
        status = path if path else "not found"
        print(f"{label:16} {status}")
        missing |= path is None
    print("Supported targets:")
    for target, details in TARGETS.items():
        print(f"  {target} ({details['format']})")
    return 1 if missing else 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="reaper os",
        description="Build freestanding native system modules for Reaper OS projects.",
    )
    commands = parser.add_subparsers(dest="command", required=True)

    check = commands.add_parser("check", help="validate a project manifest and its files")
    check.add_argument("manifest", nargs="?", default="reaper-os.json")

    build = commands.add_parser("build", help="compile and link a freestanding ELF image")
    build.add_argument("manifest", nargs="?", default="reaper-os.json")
    build.add_argument("--dry-run", action="store_true", help="print the build plan without running tools")

    commands.add_parser("doctor", help="check the installed cross-toolchain")
    commands.add_parser("targets", help="list supported freestanding targets")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if args.command == "doctor":
        return doctor()
    if args.command == "targets":
        for target in TARGETS:
            print(target)
        return 0

    try:
        project = load_project(args.manifest)
        validate_project_files(project)
    except ProjectError as error:
        print(f"reaper os: {error}", file=sys.stderr)
        return 2

    if args.command == "check":
        print(
            f"Reaper OS project OK: {project.name} "
            f"({project.target}, entry={project.entry}, {len(project.sources)} source(s))"
        )
        return 0
    return build_project(project, dry_run=args.dry_run)


if __name__ == "__main__":
    raise SystemExit(main())
