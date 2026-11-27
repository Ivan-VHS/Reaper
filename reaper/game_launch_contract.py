"""Reaper adapter for DuckOS game-launch manifests.

A task is data, not permission to execute. Reaper validates the launch contract
and returns an argv/cwd/environment description for a trusted host such as
DuckOS; this module never creates a process or invokes a shell.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Any

PROFILE_SCHEMA = "duckos.game-launch-profile.v1"
TASK_SCHEMA = "reaper.game-launch-task.v1"
MAX_PROFILE_BYTES = 1024 * 1024
MAX_ARGUMENTS = 256
ALLOWED_ENVIRONMENT = {"LANG", "LC_ALL", "LC_CTYPE", "TZ", "WINEDEBUG"}


class GameLaunchContractError(ValueError):
    """Raised when a game-launch manifest cannot be safely represented."""


def _string(value: Any, field: str, maximum: int = 4096) -> str:
    if not isinstance(value, str) or not value.strip() or len(value) > maximum or "\x00" in value:
        raise GameLaunchContractError(f"{field} must be non-empty text no longer than {maximum} characters")
    return value.strip()


def _existing_path(value: str, base: Path, field: str, kind: str) -> Path:
    candidate = Path(value).expanduser()
    relative = not candidate.is_absolute()
    if relative:
        candidate = base / candidate
    if candidate.is_symlink():
        raise GameLaunchContractError(f"{field} must not be a symbolic link")
    try:
        resolved = candidate.resolve(strict=True)
    except OSError as error:
        raise GameLaunchContractError(f"{field} does not exist: {error}") from error
    if relative:
        try:
            resolved.relative_to(base)
        except ValueError as error:
            raise GameLaunchContractError(f"relative {field} must stay inside the manifest directory") from error
    valid = resolved.is_file() if kind == "file" else resolved.is_dir()
    if not valid:
        raise GameLaunchContractError(f"{field} must point to an existing {kind}")
    return resolved


def build_game_launch_task(profile: dict[str, Any], base_directory: str | Path = ".") -> dict[str, Any]:
    if not isinstance(profile, dict) or profile.get("schema") != PROFILE_SCHEMA:
        raise GameLaunchContractError(f"expected a {PROFILE_SCHEMA} manifest")
    game_id = _string(profile.get("id"), "id", 128)
    game_name = _string(profile.get("name"), "name", 128)
    base = Path(base_directory).expanduser().resolve()

    executable_text = _string(profile.get("executable"), "executable", 2048)
    executable_path = _existing_path(executable_text, base, "executable", "file")
    executable = str(executable_path)

    working_text = _string(profile.get("working_directory", "."), "working_directory", 2048)
    working_path = _existing_path(working_text, base, "working_directory", "directory")

    arguments = profile.get("arguments", [])
    if not isinstance(arguments, list) or len(arguments) > MAX_ARGUMENTS:
        raise GameLaunchContractError(f"arguments must contain at most {MAX_ARGUMENTS} entries")
    argv_tail: list[str] = []
    for index, value in enumerate(arguments):
        if not isinstance(value, str) or len(value) > 4096 or "\x00" in value:
            raise GameLaunchContractError(f"arguments[{index}] is invalid")
        argv_tail.append(value)

    runtime = profile.get("runtime")
    if not isinstance(runtime, dict) or runtime.get("backend") != "wine":
        raise GameLaunchContractError("only the explicitly external Wine backend can be described by this adapter")
    runtime_executable = _string(runtime.get("executable", "wine"), "runtime.executable", 2048)
    runtime_path = Path(runtime_executable).expanduser()
    if runtime_path.is_absolute():
        if runtime_path.is_symlink() or not runtime_path.is_file() or not os.access(runtime_path, os.X_OK):
            raise GameLaunchContractError("absolute runtime.executable must be an executable regular file")
        runtime_executable = str(runtime_path.resolve())

    prefix_value = runtime.get("prefix")
    prefix = None
    if prefix_value is not None:
        prefix_text = _string(prefix_value, "runtime.prefix", 2048)
        prefix_path = _existing_path(prefix_text, base, "runtime.prefix", "directory")
        prefix = str(prefix_path)

    environment = profile.get("environment", {})
    if not isinstance(environment, dict):
        raise GameLaunchContractError("environment must be an object")
    environment_overrides: dict[str, str] = {}
    for key, value in environment.items():
        if key not in ALLOWED_ENVIRONMENT:
            raise GameLaunchContractError(f"environment variable {key!r} is not allowed")
        if not isinstance(value, str) or len(value) > 1024 or "\x00" in value:
            raise GameLaunchContractError(f"environment.{key} must be safe text")
        environment_overrides[key] = value
    if prefix:
        environment_overrides["WINEPREFIX"] = prefix

    return {
        "schema": TASK_SCHEMA,
        "game_id": game_id,
        "game_name": game_name,
        "target": "windows-xp-sp3",
        "argv": [runtime_executable, executable, *argv_tail],
        "working_directory": str(working_path.resolve()),
        "environment_overrides": environment_overrides,
        "shell": False,
        "execution_performed": False,
        "process_created": False,
        "requires_trusted_host_executor": True,
        "runtime_is_external": True,
    }


def load_game_launch_task(path: str | Path) -> dict[str, Any]:
    source = Path(path).expanduser()
    if source.is_symlink() or not source.is_file():
        raise GameLaunchContractError("manifest path must be a regular, non-symlink file")
    try:
        if source.stat().st_size > MAX_PROFILE_BYTES:
            raise GameLaunchContractError("manifest exceeds the 1 MiB input limit")
        payload = json.loads(source.read_text(encoding="utf-8"))
    except OSError as error:
        raise GameLaunchContractError(f"cannot read manifest: {error}") from error
    except json.JSONDecodeError as error:
        raise GameLaunchContractError(f"manifest is not valid JSON: {error}") from error
    return build_game_launch_task(payload, source.parent)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="reaper-game-contract", description="Validate a DuckOS game profile and emit a non-executing Reaper task.")
    parser.add_argument("profile", type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args(argv)
    try:
        task = load_game_launch_task(args.profile)
        encoded = json.dumps(task, ensure_ascii=False, indent=2, allow_nan=False) + "\n"
        if args.output:
            if args.output.resolve() == args.profile.resolve():
                raise GameLaunchContractError("task output must not overwrite its input manifest")
            args.output.parent.mkdir(parents=True, exist_ok=True)
            args.output.write_text(encoded, encoding="utf-8", newline="\n")
        else:
            print(encoded, end="")
        return 0
    except (GameLaunchContractError, OSError, ValueError, TypeError) as error:
        print(f"reaper-game-contract: {error}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
