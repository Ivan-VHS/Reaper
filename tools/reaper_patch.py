#!/usr/bin/env python3
"""Create, verify, apply and reverse review-gated REAPER patch proposals."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import subprocess
import sys
from pathlib import Path, PurePosixPath

SCHEMA = "reaper.patch-proposal/v2"
SHA256 = re.compile(r"^[0-9a-f]{64}$")


def run_git_bytes(root: Path, *args: str, input_bytes: bytes | None = None) -> bytes:
    result = subprocess.run(
        ["git", "-C", str(root), *args],
        input=input_bytes,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if result.returncode:
        message = result.stderr.decode("utf-8", errors="replace").strip()
        raise RuntimeError(message or f"git {' '.join(args)} failed")
    return result.stdout


def run_git(root: Path, *args: str) -> str:
    return run_git_bytes(root, *args).decode("utf-8", errors="surrogateescape")


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def safe_path(value: str) -> str:
    if not isinstance(value, str) or not value or "\x00" in value or "\\" in value:
        raise ValueError(f"unsafe patch path: {value!r}")
    path = PurePosixPath(value)
    if path.is_absolute() or any(part in ("", ".", "..") for part in path.parts):
        raise ValueError(f"unsafe patch path: {value!r}")
    if path.parts[0] == ".git" or (len(path.parts[0]) >= 2 and path.parts[0][1] == ":"):
        raise ValueError(f"patches may not modify protected path: {value!r}")
    return value


def ensure_no_symlink(root: Path, value: str) -> None:
    current = root
    for part in PurePosixPath(safe_path(value)).parts:
        current = current / part
        if current.is_symlink():
            raise ValueError(f"symlink path component is not allowed: {value}")


def changed_paths(root: Path, patch: bytes) -> list[str]:
    """Ask Git to parse the patch; never infer coverage from diff header regexes."""
    headers = patch.splitlines()
    if any(
        line.startswith((b"rename from ", b"rename to ", b"copy from ", b"copy to "))
        for line in headers
    ):
        raise ValueError("renames and copies are not supported by v1")

    output = run_git_bytes(root, "apply", "--numstat", "-z", "--", input_bytes=patch)
    if not output:
        raise ValueError("patch contains no file changes")

    paths = []
    for record in output.split(b"\0"):
        if not record:
            continue
        fields = record.split(b"\t", 2)
        if len(fields) != 3:
            raise ValueError("Git returned an invalid patch file record")
        try:
            path = os.fsdecode(fields[2])
        except UnicodeError as error:
            raise ValueError("patch contains an invalid file path") from error
        paths.append(safe_path(path))

    if not paths:
        raise ValueError("patch contains no file changes")
    if len(paths) != len(set(paths)):
        raise ValueError("patch contains duplicate file sections")
    return paths


def base_file(root: Path, base: str, path: str) -> tuple[bool, bytes]:
    try:
        content = run_git_bytes(root, "show", "--no-ext-diff", "--no-textconv", f"{base}:{path}")
        return True, content
    except RuntimeError as error:
        # A missing path is expected for newly-created files; other Git failures
        # must not be silently converted into an empty-file hash.
        message = str(error).lower()
        if "does not exist" in message or "exists on disk, but not in" in message or "path '" in message and "does not exist" in message:
            return False, b""
        raise


def create_proposal(root: Path, base: str, head: str, output: Path) -> None:
    patch = run_git_bytes(
        root, "diff", "--no-ext-diff", "--binary", "--no-renames", base, head, "--"
    )
    paths = changed_paths(root, patch)
    files = []
    for path in paths:
        exists, original = base_file(root, base, path)
        files.append({
            "path": path,
            "base_exists": exists,
            "base_sha256": sha256(original),
        })

    manifest = {
        "schema": SCHEMA,
        "base": base,
        "head": head,
        "patch_sha256": sha256(patch),
        "files": files,
        "test_plan": [
            "cmake -S . -B build",
            "cmake --build build --parallel",
            "ctest --test-dir build --output-on-failure",
        ],
        "policy": {
            "automatic_apply": False,
            "automatic_execution": False,
            "review_required": True,
            "rollback": "git apply --reverse after reverse-check",
        },
    }
    output.mkdir(parents=True, exist_ok=True)
    (output / "proposal.patch").write_bytes(patch)
    (output / "manifest.json").write_text(
        json.dumps(manifest, indent=2, ensure_ascii=True) + "\n", encoding="utf-8"
    )
    print(f"proposal created: {output} ({len(paths)} files)")


def read_manifest(proposal: Path) -> tuple[dict, bytes]:
    manifest = json.loads((proposal / "manifest.json").read_text(encoding="utf-8"))
    patch = (proposal / "proposal.patch").read_bytes()
    if not isinstance(manifest, dict) or manifest.get("schema") != SCHEMA:
        raise ValueError("unsupported proposal schema")
    if not isinstance(manifest.get("patch_sha256"), str) or sha256(patch) != manifest["patch_sha256"]:
        raise ValueError("patch digest mismatch; proposal may have been modified")
    return manifest, patch


def validate_manifest_paths(manifest: dict, paths: list[str]) -> list[dict]:
    entries = manifest.get("files")
    if not isinstance(entries, list):
        raise ValueError("manifest files must be an array")
    manifest_paths = []
    for item in entries:
        if not isinstance(item, dict):
            raise ValueError("manifest contains an invalid file entry")
        path = safe_path(item.get("path"))
        if not isinstance(item.get("base_exists"), bool):
            raise ValueError(f"manifest base_exists is missing or invalid: {path}")
        digest = item.get("base_sha256")
        if not isinstance(digest, str) or not SHA256.fullmatch(digest):
            raise ValueError(f"manifest base_sha256 is missing or invalid: {path}")
        manifest_paths.append(path)
    if manifest_paths != paths:
        raise ValueError("manifest file list does not match every parsed patch section")
    return entries


def load_proposal(root: Path, proposal: Path) -> tuple[dict, bytes]:
    manifest, patch = read_manifest(proposal)
    paths = changed_paths(root, patch)
    entries = validate_manifest_paths(manifest, paths)

    for item in entries:
        path = item["path"]
        ensure_no_symlink(root, path)
        target = root / path
        exists = target.exists()
        if target.is_symlink():
            raise ValueError(f"symlink path component is not allowed: {path}")
        if exists != item["base_exists"]:
            raise ValueError(f"base file presence changed: {path}")
        try:
            current = target.read_bytes() if exists else b""
        except OSError as error:
            raise ValueError(f"cannot read base file {path}: {error}") from error
        if sha256(current) != item["base_sha256"]:
            raise ValueError(f"base content changed: {path}")
    return manifest, patch


def verify(root: Path, proposal: Path) -> None:
    _, patch = load_proposal(root, proposal)
    run_git_bytes(root, "apply", "--check", "--", input_bytes=patch)
    print("PASS: patch digest, complete file manifest, safe paths, base bytes and git apply check")


def apply(root: Path, proposal: Path) -> None:
    _, patch = load_proposal(root, proposal)
    run_git_bytes(root, "apply", "--check", "--", input_bytes=patch)
    run_git_bytes(root, "apply", "--", input_bytes=patch)
    print("patch applied; retain proposal directory for rollback")


def rollback(root: Path, proposal: Path) -> None:
    manifest, patch = read_manifest(proposal)
    paths = changed_paths(root, patch)
    entries = validate_manifest_paths(manifest, paths)
    for item in entries:
        ensure_no_symlink(root, item["path"])
    run_git_bytes(root, "apply", "--check", "--reverse", "--", input_bytes=patch)
    run_git_bytes(root, "apply", "--reverse", "--", input_bytes=patch)
    print("rollback applied")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", type=Path, default=Path.cwd())
    sub = parser.add_subparsers(dest="command", required=True)
    create = sub.add_parser("propose")
    create.add_argument("--base", required=True)
    create.add_argument("--head", required=True)
    create.add_argument("--out", type=Path, required=True)
    for name in ("verify", "apply", "rollback"):
        command = sub.add_parser(name)
        command.add_argument("proposal", type=Path)

    args = parser.parse_args(argv)
    root = args.repo.resolve()
    try:
        if args.command == "propose":
            create_proposal(root, args.base, args.head, args.out.resolve())
        elif args.command == "verify":
            verify(root, args.proposal.resolve())
        elif args.command == "apply":
            apply(root, args.proposal.resolve())
        else:
            rollback(root, args.proposal.resolve())
    except (OSError, ValueError, RuntimeError, json.JSONDecodeError) as error:
        print(f"reaper-patch: error: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
