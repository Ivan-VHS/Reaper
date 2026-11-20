"""Command line interface for Reaper."""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
import time
from pathlib import Path

from .audit import AuditLog, AuditLogError, verify_audit_log
from .errors import ReaperError
from .evolution import EvolutionEngine
from .runtime import Interpreter
from .parser import parse
from .systems import format_tracks
from .systems_languages import main as systems_languages_main


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="reaper", description="Run and improve a Reaper language project.")
    parser.add_argument("source", nargs="?", help="path to a .rpr source file, or project directory with --evolve")
    parser.add_argument("--steps", type=int, default=1_000_000, help="maximum execution steps (default: 1000000)")
    parser.add_argument("--items", type=int, default=100_000, help="maximum items in any collection (default: 100000)")
    parser.add_argument("--text-length", type=int, default=1_000_000, help="maximum text length in characters (default: 1000000)")
    parser.add_argument("--version", action="version", version="Reaper 0.1.0")
    parser.add_argument("--audit-log", metavar="PATH", help="append a hash-chained local execution journal")
    parser.add_argument("--verify-audit-log", metavar="PATH", help="verify a journal and exit")
    parser.add_argument("--check", "--lint", dest="check", action="store_true", help="tokenize and parse without running the program")
    parser.add_argument("--repl", action="store_true", help="start the interactive Reaper prompt")
    parser.add_argument("--json", action="store_true", help="emit the run result and diagnostics as JSON")
    parser.add_argument("--profile", action="store_true", help="report elapsed time and interpreter step count")
    parser.add_argument("--systems", action="store_true", help="list the 20 engineering system contracts")
    parser.add_argument("--systems-languages", action="store_true", help="list the 66 systems-language capability profiles")
    parser.add_argument("--language-profile", choices=("pytyliki", "reaper", "oplague"), help="rank systems languages for a project profile")
    parser.add_argument("--available-languages", action="store_true", help="show only candidate toolchains found on PATH")
    parser.add_argument("--systems-json", action="store_true", help="emit the systems-language matrix as JSON")
    parser.add_argument("--evolve", action="store_true", help="run bounded syntax, test and improvement-proposal cycles")
    parser.add_argument("--iterations", type=int, default=1, help="number of evolution quality cycles (1-20)")
    return parser


def main(argv: list[str] | None = None) -> int:
    arguments = sys.argv[1:] if argv is None else argv
    if arguments and arguments[0] == "polyglot":
        from .polyglot import main as polyglot_main
        return polyglot_main(arguments[1:])
    parser = build_parser()
    args = parser.parse_args(arguments)
    if args.repl:
        if args.source or args.check or args.evolve:
            parser.error("--repl cannot be combined with a source, --check or --evolve")
        if args.json:
            parser.error("--repl does not support --json")
        return _repl()
    if args.verify_audit_log:
        if args.source or args.audit_log:
            parser.error("--verify-audit-log cannot be combined with a source or --audit-log")
        try:
            summary = verify_audit_log(args.verify_audit_log)
        except AuditLogError as error:
            print(f"reaper: audit verification failed: {error}", file=sys.stderr)
            return 1
        print(f"Audit log valid: {summary.records} record(s); head={summary.last_hash}")
        return 0
    if args.systems:
        print(format_tracks())
        return 0
    if args.systems_languages or args.language_profile or args.available_languages or args.systems_json:
        matrix_args = ["--profile", args.language_profile or "reaper"]
        if args.available_languages:
            matrix_args.append("--available-only")
        if args.systems_json:
            matrix_args.append("--json")
        return systems_languages_main(matrix_args)
    if args.evolve:
        root = Path(args.source) if args.source else Path.cwd()
        if not root.is_dir():
            parser.error("--evolve expects a project directory, or no source argument")
        try:
            report = EvolutionEngine(root).run(args.iterations)
        except ValueError as error:
            parser.error(str(error))
        print(report.to_json())
        return 0 if report.passed else 1
    if not args.source:
        parser.print_help()
        return 2
    if args.steps < 1:
        parser.error("--steps must be a positive integer")
    if args.items < 1:
        parser.error("--items must be a positive integer")
    if args.text_length < 1:
        parser.error("--text-length must be a positive integer")
    path = Path(args.source)
    output_lines: list[str] = []
    profile_data: dict[str, float | int] | None = None
    try:
        if args.audit_log and Path(args.audit_log).resolve() == path.resolve():
            raise AuditLogError("--audit-log must not overwrite the source file")
        source = path.read_text(encoding="utf-8")
        audit = AuditLog(args.audit_log) if args.audit_log else None
        source_sha256 = hashlib.sha256(source.encode("utf-8")).hexdigest()
        if audit:
            audit.record("source_loaded", source_name=path.name, source_sha256=source_sha256)
        if args.check:
            try:
                parse(source, str(path))
            except ReaperError as error:
                if audit:
                    audit.record("syntax_check_failed", error_type=type(error).__name__)
                raise
            if audit:
                audit.record("syntax_check_passed")
            if args.json:
                print(json.dumps({"ok": True, "mode": "check", "file": str(path)}, ensure_ascii=False))
            else:
                print(f"Reaper: {path} is valid")
            return 0

        def emit(line: str) -> None:
            output_lines.append(str(line))
            if not args.json:
                print(line)

        if audit:
            audit.record("execution_started", steps_limit=args.steps,
                         collection_limit=args.items, text_length_limit=args.text_length)
        started = time.perf_counter()
        interpreter = Interpreter(
            output=emit,
            max_steps=args.steps,
            max_collection_items=args.items,
            max_text_length=args.text_length,
        )
        try:
            interpreter.run(source, str(path))
            profile_data = {
                "elapsed_seconds": round(time.perf_counter() - started, 9),
                "steps": interpreter.steps,
            }
        except ReaperError as error:
            if audit:
                audit.record("execution_failed", error_type=type(error).__name__,
                             output_lines=len(output_lines))
            raise
        if audit:
            audit.record("execution_completed", output_lines=len(output_lines))
        if args.json:
            print(json.dumps({
                "ok": True,
                "file": str(path),
                "output": output_lines,
                "profile": profile_data if args.profile else None,
            }, ensure_ascii=False))
        elif args.profile and profile_data is not None:
            print(
                f"Reaper profile: {profile_data['elapsed_seconds']:.9f}s; "
                f"{profile_data['steps']} execution steps",
                file=sys.stderr,
            )
        return 0
    except AuditLogError as error:
        if args.json:
            print(json.dumps({"ok": False, "error": {"type": type(error).__name__, "message": str(error)}}))
        else:
            print(f"reaper: audit log failure: {error}", file=sys.stderr)
        return 2
    except (OSError, UnicodeError) as error:
        if args.json:
            print(json.dumps({"ok": False, "file": str(path), "error": {"type": type(error).__name__, "message": str(error)}}))
        else:
            print(f"reaper: cannot read {path}: {error}", file=sys.stderr)
        return 2
    except ReaperError as error:
        if args.json:
            print(json.dumps({
                "ok": False,
                "file": str(path),
                "output": output_lines,
                "error": {"type": type(error).__name__, "message": str(error)},
            }, ensure_ascii=False))
        else:
            print(f"reaper: {error}", file=sys.stderr)
        return 1
    except KeyboardInterrupt:
        print("reaper: interrupted", file=sys.stderr)
        return 130



def _repl() -> int:
    """Run a persistent, line-oriented prompt over one complete statement at a time."""
    interpreter = Interpreter()
    print("Reaper REPL 0.1 — enter :quit to exit, :help for help")
    while True:
        try:
            line = input("rpr> ")
        except EOFError:
            print()
            return 0
        command = line.strip()
        if command in {":quit", ":q", ":exit"}:
            return 0
        if command == ":help":
            print("Enter one complete Reaper statement or expression. Commands: :help, :quit")
            continue
        if not command:
            continue
        try:
            interpreter.run(line, "<repl>")
        except ReaperError as error:
            print(f"reaper: {error}", file=sys.stderr)
        except KeyboardInterrupt:
            print()
            return 130
