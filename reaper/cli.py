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
from .diagnostic_catalog import diagnose_exception, explain_diagnostic
from .evolution import EvolutionEngine
from .runtime import Interpreter
from .modules import ModuleLoader
from .parser import parse
from .systems import format_tracks
from .systems_languages import main as systems_languages_main
from .systems_architectures import main as systems_architectures_main
from .token_catalog import CATALOG_GROUPS, catalog_summary, token_catalog, token_info
from .products import ProductError, get_product, list_products
from .plugins import PluginError, PluginManager


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="reaper", description="Run and improve a Reaper language project.")
    parser.add_argument("source", nargs="?", help="path to a .rpr source file, or project directory with --evolve")
    parser.add_argument("--steps", type=int, default=1_000_000, help="maximum execution steps (default: 1000000)")
    parser.add_argument("--items", type=int, default=100_000, help="maximum items in any collection (default: 100000)")
    parser.add_argument("--text-length", type=int, default=1_000_000, help="maximum text length in characters (default: 1000000)")
    parser.add_argument("--version", action="version", version="Reaper 0.1.0")
    parser.add_argument("--audit-log", metavar="PATH", help="append a hash-chained local execution journal")
    parser.add_argument("--verify-audit-log", metavar="PATH", help="verify a journal and exit")
    parser.add_argument("--check", "--lint", dest="check", action="store_true", help="parse and run static type analysis without executing the program")
    parser.add_argument("--syntax-only", action="store_true", help="limit --check to lexer/parser validation and skip static type analysis")
    parser.add_argument("--repl", action="store_true", help="start the interactive Reaper prompt")
    parser.add_argument("--json", action="store_true", help="emit the run result and diagnostics as JSON")
    parser.add_argument("--profile", action="store_true", help="report elapsed time and interpreter step count")
    parser.add_argument("--engine", choices=("treewalk", "vm"), default="treewalk", help="execution engine (default: treewalk)")
    parser.add_argument("--allow-native-ffi", action="store_true", help="allow loading native C ABI libraries")
    native_group = parser.add_mutually_exclusive_group()
    native_group.add_argument("--emit-c", metavar="PATH", help="emit the checked native C17 subset to PATH; use '-' for stdout")
    native_group.add_argument("--native", metavar="PATH", help="compile the checked native C17 subset to a host executable")
    parser.add_argument("--cc", metavar="COMPILER", help="GCC/Clang-compatible compiler for --native; otherwise CC or PATH is used")
    parser.add_argument("--optimization", choices=("0", "1", "2", "3", "s"), default="2", help="native build optimization level (default: 2)")

    parser.add_argument("--module-graph", action="store_true", help="print the transitive .rpr dependency graph as JSON without executing code")
    parser.add_argument("--heap-bytes", type=int, default=64 * 1024 * 1024, help="managed heap ceiling in bytes")
    parser.add_argument("--open-resources", type=int, default=64, help="maximum simultaneously open managed files")
    parser.add_argument("--systems", action="store_true", help="list the 20 engineering system contracts")
    parser.add_argument("--systems-languages", action="store_true", help="list the 66 systems-language capability profiles")
    parser.add_argument("--language-profile", choices=("pytyliki", "reaper", "oplague"), help="rank systems languages for a project profile")
    parser.add_argument("--available-languages", action="store_true", help="show only candidate toolchains found on PATH")
    parser.add_argument("--systems-json", action="store_true", help="emit the systems-language matrix as JSON")
    parser.add_argument("--systems-architectures", action="store_true", help="list the 14 CPU, MCU and virtual-ISA architecture profiles")
    parser.add_argument("--architecture-profile", choices=("pytyliki", "reaper", "oplague"), help="rank target architectures for a project profile")
    parser.add_argument("--available-architectures", action="store_true", help="show only architecture toolchain candidates found on PATH")
    parser.add_argument("--architectures-json", action="store_true", help="emit the architecture matrix as JSON")
    parser.add_argument("--catalog", action="store_true", help="print all reserved symbolic tokens as JSON")
    parser.add_argument("--catalog-group", choices=CATALOG_GROUPS, help="filter --catalog by domain")
    parser.add_argument("--catalog-token", metavar="LEXEME", help="show metadata for one token lexeme")
    parser.add_argument("--products", action="store_true", help="list integrated internal Reaper products")
    parser.add_argument("--product-info", metavar="NAME", help="show one integrated internal product contract")
    parser.add_argument("--plugins", action="store_true", help="list built-in Reaper plugins")
    parser.add_argument("--plugin-info", metavar="NAME", help="show one built-in plugin contract")
    parser.add_argument("--run-plugin", metavar="NAME", help="run the primary operation of an enabled built-in plugin")
    parser.add_argument("--plugin-args", default="{}", metavar="JSON", help="object of plugin arguments for --run-plugin")
    parser.add_argument("--evolve", action="store_true", help="run bounded syntax, test and improvement-proposal cycles")
    parser.add_argument("--iterations", type=int, default=1, help="number of evolution quality cycles (1-20)")
    return parser


def main(argv: list[str] | None = None) -> int:
    arguments = sys.argv[1:] if argv is None else argv
    if arguments and arguments[0] == "--explain":
        if len(arguments) != 2:
            print("Usage: python -m reaper --explain RPR-E0013", file=sys.stderr)
            return 2
        definition = explain_diagnostic(arguments[1])
        if definition is None:
            print(f"reaper: unknown diagnostic code: {arguments[1]}", file=sys.stderr)
            return 2
        print(f"{definition['code']}  {definition['title']}")
        print(f"Severity: {definition['severity']}\n")
        print(f"What happened\n  {definition['summary']}\n")
        print(f"Typical causes\n  {definition['causes']}\n")
        print(f"How to fix it\n  {definition['help']}")
        return 0
    if arguments and arguments[0] == "jora":
        from .jora import main as jora_main
        return jora_main(arguments[1:])
    if arguments and arguments[0] == "lsp":
        from .lsp import serve as lsp_serve
        return lsp_serve()
    if arguments and arguments[0] == "dap":
        from .dap import serve as dap_serve
        return dap_serve()
    if arguments and arguments[0] == "typecheck":
        from .typecheck import main as typecheck_main
        return typecheck_main(arguments[1:])
    if arguments and arguments[0] == "embedded":
        from .embedded import main as embedded_main
        return embedded_main(arguments[1:])
    if arguments and arguments[0] == "polyglot":
        from .polyglot import main as polyglot_main
        return polyglot_main(arguments[1:])
    if arguments and arguments[0] == "budget":
        from .budget import main as budget_main
        return budget_main(arguments[1:])
    if arguments and arguments[0] == "polyglot-code":
        from .polyglot_code import main as polyglot_code_main
        return polyglot_code_main(arguments[1:])
    parser = build_parser()
    args = parser.parse_args(arguments)
    if args.syntax_only and not args.check:
        parser.error("--syntax-only requires --check")
    native_requested = args.emit_c is not None or args.native is not None
    if args.cc is not None and args.native is None:
        parser.error("--cc requires --native")
    if args.optimization != "2" and args.native is None:
        parser.error("--optimization requires --native")
    if native_requested:
        conflicting_mode = any((
            args.check, args.repl, args.evolve, args.audit_log, args.verify_audit_log,
            args.module_graph, args.catalog, args.catalog_group is not None,
            args.catalog_token is not None, args.products, args.product_info is not None,
            args.plugins, args.plugin_info is not None, args.run_plugin is not None,
            args.systems, args.systems_languages, args.language_profile is not None,
            args.available_languages, args.systems_json, args.systems_architectures,
            args.architecture_profile is not None, args.available_architectures,
            args.architectures_json, args.profile, args.engine != "treewalk",
            args.allow_native_ffi,
        ))
        if conflicting_mode:
            parser.error("native compilation cannot be combined with other execution, inspection, audit, or FFI modes")
        if not args.source:
            parser.error("--emit-c and --native require a .rpr source file")
        if args.json and args.emit_c == "-":
            parser.error("--json cannot be combined with --emit-c -")
        try:
            from .native_compiler import build_executable, compile_source

            source_path = Path(args.source)
            source_text = source_path.read_text(encoding="utf-8")
            if args.emit_c is not None:
                generated = compile_source(source_text, str(source_path))
                if args.emit_c == "-":
                    sys.stdout.write(generated)
                else:
                    destination = Path(args.emit_c).expanduser().resolve()
                    if destination == source_path.resolve():
                        raise ValueError("C output must not overwrite its Reaper source file")
                    destination.parent.mkdir(parents=True, exist_ok=True)
                    destination.write_text(generated, encoding="utf-8", newline="\n")
                    if args.json:
                        print(json.dumps({
                            "ok": True, "mode": "emit-c",
                            "file": str(source_path), "output": str(destination),
                        }, ensure_ascii=False))
                    else:
                        print(f"Reaper: native C17 source written to {destination}")
            else:
                executable = build_executable(
                    source_text,
                    args.native,
                    filename=str(source_path),
                    compiler=args.cc,
                    optimization=args.optimization,
                )
                if args.json:
                    print(json.dumps({
                        "ok": True, "mode": "native",
                        "file": str(source_path), "executable": str(executable),
                    }, ensure_ascii=False))
                else:
                    print(f"Reaper: native executable created at {executable}")
            return 0
        except (ReaperError, OSError, UnicodeError, ValueError, RuntimeError) as error:
            if args.json:
                print(json.dumps({
                    "ok": False,
                    "file": args.source,
                    "error": {"type": type(error).__name__, "message": str(error)},
                }, ensure_ascii=False))
            else:
                print(f"reaper: native compilation failed: {error}", file=sys.stderr)
            return 1
    if args.plugins or args.plugin_info or args.run_plugin:
        if args.source or args.audit_log or args.verify_audit_log:
            parser.error("plugin host commands cannot be combined with a source or audit-log option")
        if sum(bool(value) for value in (args.plugins, args.plugin_info, args.run_plugin)) != 1:
            parser.error("--plugins, --plugin-info and --run-plugin are mutually exclusive")
        manager = PluginManager()
        try:
            if args.plugin_info:
                selected = manager.get_plugin(args.plugin_info)
                from dataclasses import asdict
                result = asdict(selected)
                result["enabled"] = manager.is_enabled(selected.plugin_id)
                result["host"] = "reaper-python"
                result["status"] = "enabled" if result["enabled"] else "disabled"
            elif args.run_plugin:
                plugin_arguments = json.loads(args.plugin_args)
                if not isinstance(plugin_arguments, dict):
                    raise PluginError("--plugin-args must decode to a JSON object")
                result = {"plugin": manager.get_plugin(args.run_plugin).plugin_id,
                          "result": manager.run(args.run_plugin, **plugin_arguments)}
            else:
                result = {"count": len(manager.list_plugins()), "plugins": manager.list_plugins()}
        except (PluginError, ProductError, json.JSONDecodeError, TypeError) as error:
            print(f"reaper: plugin host failed: {error}", file=sys.stderr)
            return 2
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0
    if args.products or args.product_info:
        if args.source or args.audit_log or args.verify_audit_log:
            parser.error("product registry inspection cannot be combined with a source or audit-log option")
        if args.products and args.product_info:
            parser.error("--products and --product-info are mutually exclusive")
        if args.product_info:
            try:
                from dataclasses import asdict
                result = asdict(get_product(args.product_info))
            except ProductError as error:
                print(f"reaper: {error}", file=sys.stderr)
                return 2
        else:
            result = {"count": len(list_products()), "products": list_products()}
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0
    if args.module_graph:
        if not args.source:
            parser.error("--module-graph requires a .rpr entry file")
        try:
            graph = ModuleLoader(Interpreter()).scan(str(Path(args.source)))
        except (OSError, UnicodeError, ReaperError, ValueError) as error:
            print(f"reaper: module graph failed: {error}", file=sys.stderr)
            return 1
        print(json.dumps(graph, ensure_ascii=False, indent=2))
        return 0
    if args.catalog or args.catalog_group is not None or args.catalog_token is not None:
        if args.source or args.audit_log or args.verify_audit_log:
            parser.error("catalogue inspection cannot be combined with a source or audit-log option")
        if args.catalog_token is not None:
            if args.catalog or args.catalog_group is not None:
                parser.error("--catalog-token cannot be combined with --catalog or --catalog-group")
            entry = token_info(args.catalog_token)
            if entry is None:
                print(f"reaper: unknown catalogue token {args.catalog_token!r}", file=sys.stderr)
                return 1
            print(json.dumps(entry, ensure_ascii=False, indent=2))
            return 0
        if not args.catalog:
            parser.error("--catalog-group requires --catalog")
        print(json.dumps({"summary": catalog_summary(), "tokens": token_catalog(args.catalog_group)}, ensure_ascii=False, indent=2))
        return 0
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
    if args.systems_architectures or args.architecture_profile or args.available_architectures or args.architectures_json:
        matrix_args = []
        if args.architecture_profile:
            matrix_args.extend(["--profile", args.architecture_profile])
        if args.available_architectures:
            matrix_args.append("--available-only")
        if args.architectures_json:
            matrix_args.append("--json")
        return systems_architectures_main(matrix_args)
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
    if args.heap_bytes < 1:
        parser.error("--heap-bytes must be a positive integer")
    if args.open_resources < 1:
        parser.error("--open-resources must be a positive integer")
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
                tree = parse(source, str(path))
            except ReaperError as error:
                if audit:
                    audit.record("syntax_check_failed", error_type=type(error).__name__)
                raise

            diagnostics = []
            if not args.syntax_only:
                from .typecheck import TypeChecker

                checked = TypeChecker(str(path)).check(tree)
                diagnostics = [item.as_dict() for item in checked.diagnostics]

            errors = [item for item in diagnostics if item["severity"] == "error"]
            if audit:
                audit.record(
                    "static_check_completed",
                    syntax_only=args.syntax_only,
                    type_errors=len(errors),
                    type_diagnostics=len(diagnostics),
                )

            result = {
                "ok": not errors,
                "mode": "syntax-check" if args.syntax_only else "static-check",
                "file": str(path),
                "diagnostics": diagnostics,
                "summary": {
                    "errors": len(errors),
                    "warnings": sum(item["severity"] == "warning" for item in diagnostics),
                },
            }
            if args.json:
                print(json.dumps(result, ensure_ascii=False))
            else:
                for item in diagnostics:
                    print(
                        f"{path}:{item['line']}:{item['column']}: "
                        f"{item['severity']} {item['code']}: {item['message']}"
                    )
                if errors:
                    print(f"Reaper: {path} failed static checks ({len(errors)} error(s))")
                elif args.syntax_only:
                    print(f"Reaper: {path} syntax is valid")
                else:
                    print(f"Reaper: {path} syntax and supported types are valid")
            return 0 if not errors else 1

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
            allow_native_ffi=args.allow_native_ffi,
            max_heap_bytes=args.heap_bytes,
            max_open_resources=args.open_resources,
        )
        try:
            interpreter.run(source, str(path), engine=args.engine)
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
                "diagnostic": diagnose_exception(error, str(path)).to_dict(),
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
