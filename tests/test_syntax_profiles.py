"""Conformance tests for Reaper's versioned multi-syntax front end."""
from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from reaper.ide_support import highlight_spans
from reaper.ir import lower
from reaper.language_service import LanguageService
from reaper.native_compiler import compile_source
from reaper.parser import parse
from reaper.runtime import Interpreter
from reaper.syntax_profiles import (
    SyntaxProfile,
    SyntaxProfileError,
    available_syntax_profiles,
    register_syntax_profile,
    resolve_syntax_profile,
)


class SyntaxProfileTests(unittest.TestCase):
    def test_builtin_profiles_are_versioned_and_extension_selected(self) -> None:
        profiles = {item.profile_id: item for item in available_syntax_profiles()}
        self.assertIn("reaper", profiles)
        self.assertIn("reaper-flow", profiles)
        self.assertIn("most-ru", profiles)
        self.assertIn("most-uk", profiles)
        self.assertIn("classic", profiles)
        self.assertEqual(resolve_syntax_profile(filename="main.most").profile_id, "most-ru")
        self.assertEqual(resolve_syntax_profile(filename="main.rclass").profile_id, "classic")
        self.assertEqual(resolve_syntax_profile(filename="main.rflow").profile_id, "reaper-flow")
        self.assertEqual(resolve_syntax_profile(filename="main.most-uk").profile_id, "most-uk")

    def test_explicit_profile_overrides_extension_without_content_guessing(self) -> None:
        profile = resolve_syntax_profile("most-uk", "ordinary.rpr")
        self.assertEqual(profile.profile_id, "most-uk")
        with self.assertRaises(SyntaxProfileError):
            resolve_syntax_profile("not-registered")

    def test_alias_profiles_lower_to_the_same_semantic_ir(self) -> None:
        sources = (
            ("main.rpr", "make total := 40 + 2"),
            ("main.most", "пусть total := 40 + 2"),
            ("main.rclass", "let total := 40 + 2"),
        )
        shapes = []
        for filename, source in sources:
            module = lower(parse(source, filename), filename)
            shapes.append(tuple((item.op, item.argument) for item in module.code))
        self.assertEqual(shapes[0], shapes[1])
        self.assertEqual(shapes[0], shapes[2])

    def test_native_aot_parser_accepts_explicit_syntax_override(self) -> None:
        generated = compile_source(
            "let answer := 42", "source.rpr", syntax="classic"
        )
        self.assertIn("INT64_C(42)", generated)

    def test_ukrainian_most_and_classic_functions_share_runtime_semantics(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "math.rclass").write_text(
                "fn triple(value) { return value * 3 }\nexport triple\n",
                encoding="utf-8",
            )
            entry = root / "main.most-uk"
            source = 'імпорт "math.rclass"\nвивести triple(7)\n'
            output: list[str] = []
            Interpreter(output=output.append).run(source, str(entry))
            self.assertEqual(output, ["21"])

    def test_classic_frontend_can_import_a_russian_most_module(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "math.most").write_text(
                "функция удвоить(значение) { вернуть значение * 2 }\nэкспорт удвоить\n",
                encoding="utf-8",
            )
            entry = root / "main.rclass"
            source = 'import "math.most"\nprint удвоить(5)\n'
            output: list[str] = []
            Interpreter(output=output.append).run(source, str(entry))
            self.assertEqual(output, ["10"])

    def test_editor_indexing_and_highlighting_follow_the_selected_profile(self) -> None:
        service = LanguageService()
        self.addCleanup(service.shutdown)
        uri = "file:///project/main.rclass"
        service.open(uri, "fn greet(name) {\n print name\n}")
        analysis = service.analyze(uri)
        self.assertEqual([(item.name, item.kind) for item in analysis.symbols],
                         [("greet", "function")])
        completions = {item["label"] for item in service.completion(uri, "pr")}
        self.assertIn("print", completions)

        spans = highlight_spans("нехай value := 1", "file:///project/main.most-uk")
        self.assertEqual(spans[0].kind, "keyword")

    def test_duplicate_extensions_are_rejected(self) -> None:
        with self.assertRaises(SyntaxProfileError):
            register_syntax_profile(SyntaxProfile(
                "test-collision", "1", (".most",), {"let": "make"},
                "Must not take ownership of an existing extension.",
            ))


if __name__ == "__main__":
    unittest.main()
