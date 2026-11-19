#!/usr/bin/env python3
"""Create, verify, apply and reverse review-gated REAPER patch proposals."""
from __future__ import annotations
import argparse, hashlib, json, re, subprocess, sys
from pathlib import Path, PurePosixPath, PureWindowsPath

SCHEMA = "reaper.patch-proposal/v1"
DIFF_PATH = re.compile(r"^diff --git a/(.+) b/(.+)$")

def run_git(root, *args, input_text=None):
    result = subprocess.run(["git", "-C", str(root), *args], input=input_text, text=True,
        stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False)
    if result.returncode:
        raise RuntimeError(result.stderr.strip() or f"git {' '.join(args)} failed")
    return result.stdout

def sha256(data):
    return hashlib.sha256(data).hexdigest()

def safe_path(value):
    if not isinstance(value, str) or not value or "\x00" in value:
        raise ValueError(f"unsafe patch path: {value!r}")
    # Git patches are slash-separated, but the same paths may be applied on
    # Windows. Reject Windows separators, drives, UNC paths and NTFS streams
    # before any filesystem or git operation can interpret them differently.
    if "\\" in value or ":" in value:
        raise ValueError(f"unsafe cross-platform patch path: {value!r}")
    path = PurePosixPath(value)
    windows_path = PureWindowsPath(value)
    if (path.is_absolute() or windows_path.is_absolute() or windows_path.drive or
            any(part in ("", ".", "..") for part in path.parts)):
        raise ValueError(f"unsafe patch path: {value!r}")
    if path.parts[0].casefold() == ".git":
        raise ValueError("patches may not modify .git")
    return value

def ensure_no_symlink(root, value):
    current = root
    for part in PurePosixPath(safe_path(value)).parts:
        current = current / part
        if current.is_symlink():
            raise ValueError(f"symlink path component is not allowed: {value}")

def changed_paths(patch):
    found = []
    for line in patch.splitlines():
        match = DIFF_PATH.match(line)
        if match:
            left, right = safe_path(match.group(1)), safe_path(match.group(2))
            if left != right:
                raise ValueError("renames are not supported by v1")
            found.append(left)
    if not found:
        raise ValueError("patch contains no tracked file changes")
    if len(found) != len(set(found)):
        raise ValueError("patch contains duplicate file sections")
    return found

def create_proposal(root, base, head, output):
    patch = run_git(root, "diff", "--no-ext-diff", "--binary", "--no-renames", base, head, "--")
    paths = changed_paths(patch)
    files = []
    for path in paths:
        try: original = run_git(root, "show", f"{base}:{path}").encode()
        except RuntimeError: original = b""
        files.append({"path": path, "base_sha256": sha256(original)})
    manifest = {"schema": SCHEMA, "base": base, "head": head,
        "patch_sha256": sha256(patch.encode()), "files": files,
        "test_plan": ["cmake -S . -B build", "cmake --build build --parallel",
                      "ctest --test-dir build --output-on-failure"],
        "policy": {"automatic_apply": False, "automatic_execution": False,
                   "review_required": True, "rollback": "git apply --reverse after reverse-check"}}
    output.mkdir(parents=True, exist_ok=True)
    (output / "proposal.patch").write_text(patch, encoding="utf-8")
    (output / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    print(f"proposal created: {output} ({len(paths)} files)")

def load_proposal(root, proposal):
    manifest = json.loads((proposal / "manifest.json").read_text(encoding="utf-8"))
    patch = (proposal / "proposal.patch").read_text(encoding="utf-8")
    if manifest.get("schema") != SCHEMA: raise ValueError("unsupported proposal schema")
    if sha256(patch.encode()) != manifest.get("patch_sha256"):
        raise ValueError("patch digest mismatch; proposal may have been modified")
    paths = changed_paths(patch)
    if paths != [item["path"] for item in manifest.get("files", [])]:
        raise ValueError("manifest file list does not match patch")
    for item in manifest["files"]:
        ensure_no_symlink(root, item["path"])
        try: current = (root / item["path"]).read_bytes()
        except FileNotFoundError: current = b""
        if sha256(current) != item["base_sha256"]:
            raise ValueError(f"base content changed: {item['path']}")
    return manifest, patch

def verify(root, proposal):
    _, patch = load_proposal(root, proposal)
    run_git(root, "apply", "--check", input_text=patch)
    print("PASS: digest, paths, base hashes and git apply check")

def apply(root, proposal):
    _, patch = load_proposal(root, proposal)
    run_git(root, "apply", "--check", input_text=patch)
    run_git(root, "apply", input_text=patch)
    print("patch applied; retain proposal directory for rollback")

def rollback(root, proposal):
    manifest = json.loads((proposal / "manifest.json").read_text(encoding="utf-8"))
    patch = (proposal / "proposal.patch").read_text(encoding="utf-8")
    if manifest.get("schema") != SCHEMA or sha256(patch.encode()) != manifest.get("patch_sha256"):
        raise ValueError("invalid proposal or patch digest mismatch")
    if changed_paths(patch) != [item["path"] for item in manifest.get("files", [])]:
        raise ValueError("manifest file list does not match patch")
    for item in manifest["files"]:
        ensure_no_symlink(root, item["path"])
    run_git(root, "apply", "--check", "--reverse", input_text=patch)
    run_git(root, "apply", "--reverse", input_text=patch)
    print("rollback applied")

def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", type=Path, default=Path.cwd())
    sub = parser.add_subparsers(dest="command", required=True)
    create = sub.add_parser("propose")
    create.add_argument("--base", required=True); create.add_argument("--head", required=True)
    create.add_argument("--out", type=Path, required=True)
    for name in ("verify", "apply", "rollback"):
        command = sub.add_parser(name); command.add_argument("proposal", type=Path)
    args = parser.parse_args(argv); root = args.repo.resolve()
    try:
        if args.command == "propose": create_proposal(root, args.base, args.head, args.out.resolve())
        elif args.command == "verify": verify(root, args.proposal.resolve())
        elif args.command == "apply": apply(root, args.proposal.resolve())
        else: rollback(root, args.proposal.resolve())
    except (OSError, ValueError, RuntimeError, json.JSONDecodeError) as exc:
        print(f"reaper-patch: error: {exc}", file=sys.stderr); return 1
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
