from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from reaper import Interpreter, ParseError
from reaper.diagnostic_catalog import diagnose_exception
from reaper.maza import MazaError
from reaper.lexer import tokenize
from reaper.parser import parse
from reaper.typecheck import TypeChecker


FOUNDATION_V1 = '''export make version := 1
craft add(left, right) {
    yield left + right
}
export add
'''

FOUNDATION_V2 = '''export make version := 2
craft add(left, right) {
    yield left + right + 1
}
export add
'''


class MazaSyntaxTests(unittest.TestCase):
    def test_keyword_and_exact_russian_alias(self) -> None:
        self.assertEqual(
            [item.kind for item in tokenize('maza "base.rpr" as base')[:-1]],
            ["MAZA", "STRING", "AS", "IDENT"],
        )
        self.assertEqual(
            [item.kind for item in tokenize('маза "base.rpr" как основа')[:-1]],
            ["MAZA", "STRING", "AS", "IDENT"],
        )

    def test_parser_requires_explicit_namespace_alias(self) -> None:
        tree = parse('maza "base.rpr" as base')
        self.assertEqual(tree.children[0].kind, "maza")
        self.assertEqual(tree.children[0].value, ("base.rpr", "base"))
        with self.assertRaises(ParseError):
            parse('maza "base.rpr"')

    def test_maza_errors_have_a_dedicated_diagnostic(self) -> None:
        diagnostic = diagnose_exception(MazaError("missing foundation"))
        self.assertEqual(diagnostic.code, "RPR-E0110")

    def test_remote_source_is_rejected_without_fetching(self) -> None:
        root = self.workspace()
        interpreter = Interpreter(output=lambda _line: None)
        with self.assertRaisesRegex(MazaError, "local .rpr paths only"):
            interpreter.run(
                'maza "https://example.invalid/foundation.rpr" as remote',
                str(root / "main.rpr"),
            )

    def test_symbolic_link_source_is_rejected_before_resolution(self) -> None:
        root = self.workspace()
        alias = root / "linked.rpr"
        try:
            alias.symlink_to(root / "foundation.rpr")
        except (OSError, NotImplementedError):
            self.skipTest("symbolic links are unavailable on this host")
        interpreter = Interpreter(output=lambda _line: None)
        with self.assertRaisesRegex(MazaError, "symbolic-link sources"):
            interpreter.run(
                'maza "linked.rpr" as linked',
                str(root / "main.rpr"),
            )

    def test_typechecker_registers_foundation_namespace(self) -> None:
        tree = parse('maza "base.rpr" as base\nemit base["version"]')
        result = TypeChecker().check(tree)
        self.assertTrue(result.ok, result.diagnostics)


class MazaRuntimeTests(unittest.TestCase):
    def workspace(self, foundation: str = FOUNDATION_V1):
        directory = tempfile.TemporaryDirectory()
        root = Path(directory.name)
        (root / "foundation.rpr").write_text(foundation, encoding="utf-8")
        (root / "main.rpr").write_text("", encoding="utf-8")
        self.addCleanup(directory.cleanup)
        return root

    def run_source(self, root: Path, source: str, engine: str = "treewalk"):
        output: list[str] = []
        interpreter = Interpreter(output=output.append, maza_poll_interval_ms=50)
        result = interpreter.run(source, str(root / "main.rpr"), engine=engine)
        return output, interpreter, result

    def test_treewalk_attaches_namespace_and_calls_exported_function(self) -> None:
        root = self.workspace()
        output, interpreter, _ = self.run_source(
            root,
            'maza "foundation.rpr" as base\n'
            'emit base["version"]\n'
            'emit base["add"](20, 22)',
        )
        self.assertEqual(output, ["1", "42"])
        self.assertEqual(interpreter.maza.status("base")["state"], "active")
        self.assertEqual(interpreter.maza.status("base")["revision"], 1)

    def test_vm_attaches_foundation_through_verified_ir(self) -> None:
        root = self.workspace()
        output, interpreter, _ = self.run_source(
            root,
            'maza "foundation.rpr" as base\n'
            'emit base["add"](20, 22)',
            engine="vm",
        )
        self.assertEqual(output, ["42"])
        self.assertEqual(interpreter.maza.status("base")["state"], "active")

    def test_safe_point_refresh_updates_existing_namespace_in_place(self) -> None:
        root = self.workspace()
        output: list[str] = []
        interpreter = Interpreter(output=output.append, maza_poll_interval_ms=50)
        source_file = str(root / "main.rpr")
        interpreter.run('maza "foundation.rpr" as base', source_file)
        namespace = interpreter.globals.get("base")
        (root / "foundation.rpr").write_text(FOUNDATION_V2, encoding="utf-8")
        interpreter.maza._links["base"].next_poll_ns = 0
        interpreter.run('emit base["version"]\nemit base["add"](20, 22)', source_file)
        self.assertEqual(output, ["2", "43"])
        self.assertIs(interpreter.globals.get("base"), namespace)
        self.assertEqual(interpreter.maza.status("base")["revision"], 2)

    def test_invalid_update_keeps_last_good_namespace(self) -> None:
        root = self.workspace()
        output: list[str] = []
        interpreter = Interpreter(output=output.append, maza_poll_interval_ms=50)
        source_file = str(root / "main.rpr")
        interpreter.run('maza "foundation.rpr" as base', source_file)
        (root / "foundation.rpr").write_text("export make version :=\n", encoding="utf-8")
        interpreter.maza._links["base"].next_poll_ns = 0
        interpreter.run('emit base["version"]\nemit maza_status("base")["state"]', source_file)
        self.assertEqual(output, ["1", "degraded"])
        self.assertEqual(interpreter.maza.status("base")["revision"], 1)
        self.assertIsNotNone(interpreter.maza.status("base")["last_error"])

    def test_manual_refresh_and_detach(self) -> None:
        root = self.workspace()
        output: list[str] = []
        interpreter = Interpreter(output=output.append)
        source_file = str(root / "main.rpr")
        interpreter.run('maza "foundation.rpr" as base', source_file)
        (root / "foundation.rpr").write_text(FOUNDATION_V2, encoding="utf-8")
        self.assertEqual(interpreter.maza.refresh("base")["revision"], 2)
        self.assertTrue(interpreter.maza.detach("base"))
        self.assertFalse(interpreter.maza.links())
        self.assertFalse(interpreter.maza.detach("base"))

    def test_repeated_attachment_is_idempotent(self) -> None:
        root = self.workspace()
        interpreter = Interpreter(output=lambda _line: None)
        source_file = str(root / "main.rpr")
        interpreter.run('maza "foundation.rpr" as base', source_file)
        interpreter.run('maza "foundation.rpr" as base', source_file)
        self.assertEqual(interpreter.maza.status("base")["revision"], 1)

    def test_module_graph_contains_maza_dependencies(self) -> None:
        root = self.workspace()
        (root / "main.rpr").write_text('maza "foundation.rpr" as base', encoding="utf-8")
        interpreter = Interpreter(output=lambda _line: None)
        graph = interpreter.module_loader.scan(str(root / "main.rpr"))
        self.assertEqual(len(graph[str(root / "main.rpr")]), 1)


if __name__ == "__main__":
    unittest.main()
