"""NOO TAH: Node.js runtime integration for Reaper.

NOO TAH delegates JavaScript execution to an official Node.js distribution.
It does not claim to reimplement V8, libuv, or Node's native APIs.
"""
from __future__ import annotations

import argparse
import os
import shutil
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Mapping, Sequence


@dataclass(frozen=True)
class Runtime:
    node: str
    npm: str | None

    @classmethod
    def discover(cls, explicit_node: str | None = None) -> "Runtime":
        node = explicit_node or os.environ.get("NOO_TAH_NODE") or shutil.which("node")
        if not node:
            raise RuntimeError(
                "Node.js was not found. Install an official Node.js LTS release "
                "or set NOO_TAH_NODE to the node executable."
            )
        node_path = Path(node).expanduser()
        if node_path.is_file():
            node = str(node_path.resolve())
        npm = os.environ.get("NOO_TAH_NPM") or shutil.which("npm")
        if not npm:
            candidate = Path(node).with_name("npm.cmd" if os.name == "nt" else "npm")
            npm = str(candidate) if candidate.is_file() else None
        return cls(node=node, npm=npm)

    def command(self, args: Sequence[str], *, cwd: Path | None = None,
                timeout: float | None = None,
                env: Mapping[str, str] | None = None) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [self.node, *map(str, args)],
            cwd=str(cwd) if cwd else None,
            env=dict(env) if env is not None else None,
            text=True,
            encoding="utf-8",
            errors="replace",
            capture_output=True,
            timeout=timeout,
            check=False,
        )

    def npm_command(self, args: Sequence[str], *, cwd: Path | None = None,
                    timeout: float | None = None) -> subprocess.CompletedProcess[str]:
        if not self.npm:
            raise RuntimeError("npm was not found beside Node.js or on PATH.")
        return subprocess.run(
            [self.npm, *map(str, args)],
            cwd=str(cwd) if cwd else None,
            text=True,
            encoding="utf-8",
            errors="replace",
            capture_output=True,
            timeout=timeout,
            check=False,
        )


def _report(result: subprocess.CompletedProcess[str]) -> int:
    if result.stdout:
        print(result.stdout, end="" if result.stdout.endswith("\n") else "\n")
    if result.stderr:
        print(result.stderr, file=sys.stderr,
              end="" if result.stderr.endswith("\n") else "\n")
    return result.returncode


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="reaper-noo-tah",
        description="Run JavaScript and npm workflows through the NOO TAH Node.js bridge.",
    )
    parser.add_argument("--node", help="Explicit path to the Node.js executable")
    sub = parser.add_subparsers(dest="action", required=True)
    sub.add_parser("version", help="Show Node.js and npm versions")
    run = sub.add_parser("run", help="Execute a JavaScript file")
    run.add_argument("file")
    run.add_argument("args", nargs=argparse.REMAINDER)
    check = sub.add_parser("check", help="Syntax-check a JavaScript file")
    check.add_argument("file")
    npm = sub.add_parser("npm", help="Run npm in a project directory")
    npm.add_argument("args", nargs=argparse.REMAINDER)
    install = sub.add_parser("install", help="Install dependencies from package.json")
    install.add_argument("--cwd", default=".")
    install.add_argument("--ci", action="store_true", help="Use npm ci")
    inspector = sub.add_parser("inspect", help="Start Node's inspector for a script")
    inspector.add_argument("file")
    inspector.add_argument("args", nargs=argparse.REMAINDER)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        runtime = Runtime.discover(args.node)
        if args.action == "version":
            node_result = runtime.command(["--version"])
            code = _report(node_result)
            if code:
                return code
            if runtime.npm:
                return _report(runtime.npm_command(["--version"]))
            print("npm: unavailable", file=sys.stderr)
            return 0
        if args.action == "run":
            return _report(runtime.command([args.file, *args.args]))
        if args.action == "check":
            return _report(runtime.command(["--check", args.file]))
        if args.action == "inspect":
            return _report(runtime.command(["--inspect", args.file, *args.args]))
        if args.action == "npm":
            return _report(runtime.npm_command(args.args or ["--help"]))
        if args.action == "install":
            command = ["ci"] if args.ci else ["install"]
            return _report(runtime.npm_command(command, cwd=Path(args.cwd).resolve()))
    except (RuntimeError, OSError, subprocess.TimeoutExpired) as exc:
        print(f"NOO TAH: {exc}", file=sys.stderr)
        return 2
    parser.error("unsupported action")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
