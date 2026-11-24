from __future__ import annotations

import json
import tempfile
import unittest
from contextlib import redirect_stdout
from io import StringIO
from pathlib import Path

from reaper.cli import main


class StaticCheckCliTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.source = Path(self.temporary.name) / "sample.rpr"

    def invoke(self, *arguments: str) -> tuple[int, str]:
        output = StringIO()
        with redirect_stdout(output):
            exit_code = main([*arguments])
        return exit_code, output.getvalue()

    def test_check_runs_type_analysis_by_default(self) -> None:
        self.source.write_text('make invalid := "text" * 2\n', encoding="utf-8")
        exit_code, output = self.invoke("--check", str(self.source))
        self.assertEqual(exit_code, 1)
        self.assertIn("RPR-T0004", output)
        self.assertIn("static checks", output)

    def test_syntax_only_preserves_legacy_parser_check(self) -> None:
        self.source.write_text('make invalid := "text" * 2\n', encoding="utf-8")
        exit_code, output = self.invoke("--check", "--syntax-only", str(self.source))
        self.assertEqual(exit_code, 0)
        self.assertIn("syntax is valid", output)
        self.assertNotIn("RPR-T0004", output)

    def test_json_mode_contains_type_diagnostics(self) -> None:
        self.source.write_text('emit "text" * 2\n', encoding="utf-8")
        exit_code, output = self.invoke("--check", "--json", str(self.source))
        self.assertEqual(exit_code, 1)
        result = json.loads(output)
        self.assertFalse(result["ok"])
        self.assertEqual(result["mode"], "static-check")
        self.assertEqual(result["diagnostics"][0]["code"], "RPR-T0004")
        self.assertEqual(result["summary"]["errors"], 1)

    def test_json_syntax_only_skips_type_analysis(self) -> None:
        self.source.write_text('emit "text" * 2\n', encoding="utf-8")
        exit_code, output = self.invoke("--check", "--syntax-only", "--json", str(self.source))
        self.assertEqual(exit_code, 0)
        result = json.loads(output)
        self.assertTrue(result["ok"])
        self.assertEqual(result["mode"], "syntax-check")
        self.assertEqual(result["diagnostics"], [])

    def test_valid_function_pipeline_passes(self) -> None:
        self.source.write_text(
            "craft double(value) { yield value * 2 }\n"
            "make values := [1, 2, 3] :: map(double)\n"
            "emit values\n",
            encoding="utf-8",
        )
        exit_code, output = self.invoke("--check", str(self.source))
        self.assertEqual(exit_code, 0, output)
        self.assertIn("supported types are valid", output)


if __name__ == "__main__":
    unittest.main()
