"""Command line interface for Reaper."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from .errors import ReaperError
from .evolution import EvolutionEngine
from .runtime import Interpreter
from .parser import parse
from .systems import format_tracks


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="reaper", description="Run and improve a Reaper language project.")
    parser.add_argument("source", nargs="?", help="path to a .rpr source file, or project directory with --evolve")
    parser.add_argument("--steps", type=int, default=1_000_000, help="maximum execution steps (default: 1000000)")
    parser.add_argument("--items", type=int, default=100_000, help="maximum items in any collection (default: 100000)")
    parser.add_argument("--text-length", type=int, default=1_000_000, help="maximum text length in characters (default: 1000000)")
    parser.add_argument("--version", action="version", version="Reaper 0.1.0")
    parser.add_argument("--check", action="store_true", help="tokenize and parse without running the program")
    parser.add_argument("--systems", action="store_true", help="list the 20 engineering system contracts")
    parser.add_argument("--evolve", action="store_true", help="run bounded syntax, test and improvement-proposal cycles")
    parser.add_argument("--iterations", type=int, default=1, help="number of evolution quality cycles (1-20)")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if args.systems:
        print(format_tracks())
        return 0
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
    try:
        source = path.read_text(encoding="utf-8")
        if args.check:
            parse(source, str(path))
            print(f"Reaper: {path} is valid")
            return 0
        Interpreter(
            max_steps=args.steps,
            max_collection_items=args.items,
            max_text_length=args.text_length,
        ).run(source, str(path))
        return 0
    except (OSError, UnicodeError) as error:
        print(f"reaper: cannot read {path}: {error}", file=sys.stderr)
        return 2
    except ReaperError as error:
        print(f"reaper: {error}", file=sys.stderr)
        return 1
    except KeyboardInterrupt:
        print("reaper: interrupted", file=sys.stderr)
        return 130
