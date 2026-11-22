"""Read-only inventory and hash-pinned locks for local compiler toolchains.

No compiler, formatter, debugger or package manager is executed by this module.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
from typing import Any

INVENTORY_SCHEMA = "reaper.toolchain-inventory.v1"
LOCK_SCHEMA = "reaper.toolchain-lock.v1"
MAX_EXECUTABLE_BYTES = 512 * 1024 * 1024
TOOLS = (
    ("cmake", "build", ("cmake",)),
    ("ninja", "build", ("ninja",)),
    ("make", "build", ("make", "gmake")),
    ("cc", "native", ("cc", "clang", "gcc", "cl")),
    ("cxx", "native", ("c++", "clang++", "g++", "cl")),
    ("rustc", "native", ("rustc",)),
    ("cargo", "native", ("cargo",)),
    ("python", "runtime", ("python3", "python")),
    ("node", "runtime", ("node",)),
    ("npm", "packages", ("npm",)),
    ("wasmtime", "sandbox", ("wasmtime",)),
    ("wasmer", "sandbox", ("wasmer",)),
    ("clang-format", "format", ("clang-format",)),
    ("ruff", "format", ("ruff",)),
    ("black", "format", ("black",)),
    ("rustfmt", "format", ("rustfmt",)),
    ("prettier", "format", ("prettier",)),
    ("gdb", "debug", ("gdb",)),
    ("lldb", "debug", ("lldb",)),
    ("bison", "parser", ("bison",)),
    ("flex", "parser", ("flex",)),
    ("antlr", "parser", ("antlr4", "antlr")),
)


class ToolchainError(ValueError):
    """Raised when a toolchain inventory or lock violates its schema."""


def _find_tool(candidates: tuple[str, ...], search_path: str | None) -> Path | None:
    for candidate in candidates:
        located = shutil.which(candidate, path=search_path)
        if not located:
            continue
        path = Path(located).resolve(strict=False)
        try:
            if path.is_file() and os.access(path, os.X_OK):
                return path
        except OSError:
            continue
    return None


def discover_toolchain(search_path: str | None = None) -> dict[str, Any]:
    """Inspect PATH entries without invoking discovered programs."""
    entries = []
    for name, category, candidates in TOOLS:
        path = _find_tool(candidates, search_path)
        entries.append({
            "id": name,
            "category": category,
            "available": path is not None,
            "path": str(path) if path else None,
            "version": "not-probed",
        })
    return {
        "schema": INVENTORY_SCHEMA,
        "probe": "filesystem-path-lookup-only",
        "tools": entries,
    }


def _sha256(path: Path) -> str:
    try:
        size = path.stat().st_size
        if size > MAX_EXECUTABLE_BYTES:
            raise ToolchainError(f"{path.name} exceeds the executable hash limit")
        digest = hashlib.sha256()
        with path.open("rb") as stream:
            for chunk in iter(lambda: stream.read(1024 * 1024), b""):
                digest.update(chunk)
        return digest.hexdigest()
    except OSError as error:
        raise ToolchainError(f"cannot hash {path}: {error}") from error


def create_lock(inventory: Any) -> dict[str, Any]:
    if not isinstance(inventory, dict) or inventory.get("schema") != INVENTORY_SCHEMA:
        raise ToolchainError(f"inventory must use {INVENTORY_SCHEMA}")
    tools = inventory.get("tools")
    if not isinstance(tools, list) or len(tools) != len(TOOLS):
        raise ToolchainError("inventory tool table is incomplete")
    locked = []
    seen = set()
    for item in tools:
        if not isinstance(item, dict) or item.get("id") not in {tool[0] for tool in TOOLS}:
            raise ToolchainError("inventory contains an unknown tool")
        if item["id"] in seen:
            raise ToolchainError("inventory contains duplicate tools")
        seen.add(item["id"])
        path_text = item.get("path")
        if not item.get("available"):
            locked.append({"id": item["id"], "available": False, "path": None, "sha256": None})
            continue
        if not isinstance(path_text, str) or not path_text:
            raise ToolchainError(f"{item['id']} has no resolved path")
        path = Path(path_text)
        if path.is_symlink() or not path.is_file():
            raise ToolchainError(f"{item['id']} path must be a regular, non-symlink file")
        locked.append({
            "id": item["id"], "available": True,
            "path": str(path.resolve()), "sha256": _sha256(path),
        })
    return {"schema": LOCK_SCHEMA, "hash": "sha256", "tools": locked}


def verify_lock(lock: Any, search_path: str | None = None) -> dict[str, Any]:
    if not isinstance(lock, dict) or lock.get("schema") != LOCK_SCHEMA or lock.get("hash") != "sha256":
        raise ToolchainError(f"lock must use {LOCK_SCHEMA} and sha256")
    items = lock.get("tools")
    if not isinstance(items, list) or len(items) != len(TOOLS):
        raise ToolchainError("lock tool table is incomplete")
    current = discover_toolchain(search_path)
    found = {item["id"]: item for item in current["tools"]}
    results = []
    for item in items:
        if not isinstance(item, dict) or item.get("id") not in found:
            raise ToolchainError("lock contains an unknown tool")
        actual = found[item["id"]]
        expected_available = item.get("available")
        match = bool(expected_available) == bool(actual["available"])
        reason = "availability matches"
        if expected_available and actual["available"]:
            if actual["path"] != item.get("path"):
                match, reason = False, "resolved path changed"
            else:
                try:
                    match = _sha256(Path(actual["path"])) == item.get("sha256")
                except ToolchainError:
                    match = False
                reason = "content hash matches" if match else "content hash changed"
        results.append({"id": item["id"], "matches": match, "reason": reason})
    return {"schema": "reaper.toolchain-verification.v1",
            "valid": all(item["matches"] for item in results), "tools": results}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Inspect and pin local compiler and IDE toolchains without running them.")
    parser.add_argument("--output", type=Path, help="Write the inventory or verification report to this path")
    parser.add_argument("--path", help="Explicit PATH string for a reproducible inventory")
    parser.add_argument("--lock", type=Path, help="Create a SHA-256 lock from the discovered toolchain")
    parser.add_argument("--verify-lock", type=Path, help="Verify a previously created toolchain lock")
    args = parser.parse_args(argv)
    if args.lock is not None and args.verify_lock is not None:
        parser.error("--lock and --verify-lock cannot be used together")
    try:
        inventory = discover_toolchain(args.path)
        if args.lock is not None:
            result = create_lock(inventory)
        elif args.verify_lock is not None:
            try:
                lock = json.loads(args.verify_lock.read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError) as error:
                raise ToolchainError(f"cannot read a valid toolchain lock: {error}") from error
            result = verify_lock(lock, args.path)
        else:
            result = inventory
        encoded = json.dumps(result, ensure_ascii=False, indent=2, allow_nan=False) + "\\n"
        if args.output:
            args.output.write_text(encoded, encoding="utf-8", newline="\\n")
        else:
            print(encoded, end="")
        return 0 if result.get("valid", True) else 1
    except (OSError, ToolchainError, TypeError, ValueError) as error:
        parser.exit(2, f"toolchain inspection failed: {error}\\n")


if __name__ == "__main__":
    raise SystemExit(main())
