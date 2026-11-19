#!/usr/bin/env python3
"""Reproducibility preflight for the native bootstrap compiler; not self-hosting."""
import argparse, subprocess, sys
from pathlib import Path

def capture(binary, *args):
    result = subprocess.run([str(binary), *args], text=True, stdout=subprocess.PIPE,
        stderr=subprocess.PIPE, check=False)
    if result.returncode: raise RuntimeError(f"{binary} {' '.join(args)} failed: {result.stderr.strip()}")
    return result.stdout

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--compiler", type=Path, required=True)
    parser.add_argument("--source", type=Path, default=Path("examples/hello.rpr"))
    args = parser.parse_args(); binary = args.compiler.resolve()
    if not binary.is_file(): raise SystemExit(f"compiler not found: {binary}")
    version_a, version_b = capture(binary, "--version"), capture(binary, "--version")
    tokens_a, tokens_b = capture(binary, "--tokens", str(args.source)), capture(binary, "--tokens", str(args.source))
    if version_a != version_b or tokens_a != tokens_b:
        raise SystemExit("bootstrap preflight failed: repeated output is not deterministic")
    print("PASS: native compiler responds deterministically to version and lexer smoke tests")
    print("LIMIT: this is a reproducibility preflight, not a self-hosting compiler proof")

if __name__ == "__main__":
    try: main()
    except (OSError, RuntimeError) as error:
        print(f"bootstrap-check: {error}", file=sys.stderr); raise SystemExit(1)
