"""Command-line entry point for the portable Reaper compiler front end.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from .compiler import StaticTypeError, compile_source, optimize
from .errors import ReaperError


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="reaperc",
        description="Compile Reaper source into verified portable Quarry IR."
    )
    parser.add_argument("source", help="path to a .rpr source file")
    parser.add_argument("--optimize", action="store_true", help="fold safe literal expressions")
    parser.add_argument("--allow-type-errors", action="store_true",
                        help="emit IR with diagnostics instead of rejecting type errors")
    args = parser.parse_args(argv)
    path = Path(args.source)
    try:
        source = path.read_text(encoding="utf-8")
        unit = compile_source(source, str(path))
        if unit.diagnostics and not args.allow_type_errors:
            raise StaticTypeError(unit.diagnostics)
        stats = None
        if args.optimize:
            unit, stats = optimize(unit)
        result = unit.as_dict()
        if stats is not None:
            result["optimization"] = {
                "nodes_before": stats.nodes_before,
                "nodes_after": stats.nodes_after,
                "folded_expressions": stats.folded_expressions,
            }
        print(json.dumps(result, ensure_ascii=False, sort_keys=True, indent=2))
        return 0
    except (OSError, UnicodeError) as error:
        print(f"reaperc: cannot read {path}: {error}", file=sys.stderr)
        return 2
    except (ReaperError, StaticTypeError, ValueError) as error:
        print(f"reaperc: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
