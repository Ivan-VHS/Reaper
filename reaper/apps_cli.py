"""CLI for listing, describing and running the first-party Reaper application suite."""
from __future__ import annotations

import argparse
import json
import os
import sys
import tempfile
from pathlib import Path
from typing import Any

from .apps import ApplicationInputError, describe_app, list_apps, run_app

MAX_INPUT_BYTES = 4 * 1024 * 1024
MAX_OUTPUT_BYTES = 16 * 1024 * 1024


def _unique_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"duplicate JSON key: {key}")
        result[key] = value
    return result


def _reject_constant(value: str) -> None:
    raise ValueError(f"non-finite JSON number is not permitted: {value}")


def _read_payload(path_text: str) -> dict[str, Any]:
    if path_text == "-":
        raw = sys.stdin.buffer.read(MAX_INPUT_BYTES + 1)
    else:
        path = Path(path_text).expanduser()
        if path.is_symlink():
            raise ApplicationInputError("JSON input must not be a symbolic link")
        resolved = path.resolve(strict=True)
        if not resolved.is_file():
            raise ApplicationInputError("JSON input must be a regular file")
        if resolved.stat().st_size > MAX_INPUT_BYTES:
            raise ApplicationInputError(f"JSON input exceeds {MAX_INPUT_BYTES} bytes")
        raw = resolved.read_bytes()
    if len(raw) > MAX_INPUT_BYTES:
        raise ApplicationInputError(f"JSON input exceeds {MAX_INPUT_BYTES} bytes")
    try:
        payload = json.loads(
            raw.decode("utf-8"),
            object_pairs_hook=_unique_object,
            parse_constant=_reject_constant,
        )
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise ApplicationInputError(f"invalid UTF-8 JSON: {error}") from error
    if not isinstance(payload, dict):
        raise ApplicationInputError("application input must be a JSON object")
    return payload


def _encode(value: Any) -> bytes:
    try:
        encoded = (json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + "\n").encode("utf-8")
    except (TypeError, ValueError, OverflowError) as error:
        raise ApplicationInputError(f"application result is not finite JSON: {error}") from error
    if len(encoded) > MAX_OUTPUT_BYTES:
        raise ApplicationInputError(f"application output exceeds {MAX_OUTPUT_BYTES} bytes")
    return encoded


def _write_output(path_text: str, value: Any) -> str | None:
    encoded = _encode(value)
    if path_text == "-":
        sys.stdout.buffer.write(encoded)
        return None
    destination = Path(path_text).expanduser()
    if destination.is_symlink():
        raise ApplicationInputError("JSON output must not be a symbolic link")
    if not destination.parent.is_dir():
        raise ApplicationInputError("JSON output parent directory must already exist")
    if destination.exists() and destination.is_dir():
        raise ApplicationInputError("JSON output path must not be a directory")
    fd, temporary = tempfile.mkstemp(prefix=f".{destination.name}.", suffix=".tmp", dir=str(destination.parent))
    try:
        with os.fdopen(fd, "wb") as stream:
            stream.write(encoded)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, destination)
    except BaseException:
        try:
            os.unlink(temporary)
        except OSError:
            pass
        raise
    return str(destination.resolve())


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="reaper apps", description="First-party Reaper JSON application suite")
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser("list", help="list available applications")
    describe = commands.add_parser("describe", help="show one application contract")
    describe.add_argument("app_id")
    execute = commands.add_parser("run", help="run one application against a JSON object")
    execute.add_argument("app_id")
    execute.add_argument("--input", required=True, metavar="PATH", help="JSON input file, or '-' for stdin")
    execute.add_argument("--output", metavar="PATH", help="write the result atomically to this path, or '-' for stdout")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(sys.argv[1:] if argv is None else argv)
    try:
        if args.command == "list":
            result = list_apps()
        elif args.command == "describe":
            result = describe_app(args.app_id)
        elif args.command == "run":
            payload = _read_payload(args.input)
            result = run_app(args.app_id, payload)
            if args.output:
                written = _write_output(args.output, result)
                print(json.dumps({"ok": True, "app_id": args.app_id, "written": written}, ensure_ascii=False))
                return 0
        else:
            parser.error("unsupported application command")
            return 2
        sys.stdout.buffer.write(_encode(result))
        return 0
    except (ApplicationInputError, OSError, ValueError) as error:
        print(json.dumps({"ok": False, "error": str(error)}, ensure_ascii=False), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
