from __future__ import annotations

import io
import json
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from unittest.mock import patch

from reaper import Interpreter
from reaper.cli import main


class ExtendedRuntimeTests(unittest.TestCase):
    def capture(self, source: str, **limits: int) -> list[str]:
        output: list[str] = []
        Interpreter(output=output.append, **limits).run(source)
        return output

    def test_filter_reduce_aliases_and_stable_sorting(self) -> None:
        source = """
        craft even(value) { yield value % 2 == 0 }
        craft parity(value) { yield value % 2 }
        craft add(total, value) { yield total + value }
        emit [1, 2, 3, 4] :: filter(even) :: reduce(0, add)
        emit sort_by([3, 2, 1, 4], parity, "asc")
        emit sorted([1, 3, 2], "desc")
        """
        self.assertEqual(self.capture(source), ["6", "[2, 4, 3, 1]", "[3, 2, 1]"])

    def test_chunk_take_drop_flatten_unique_and_reverse(self) -> None:
        source = """
        emit chunk([1, 2, 3, 4, 5], 2)
        emit take([1, 2, 3, 4], 2)
        emit drop([1, 2, 3, 4], 2)
        emit flatten([[1, 2], [3], [4, 5]])
        emit unique([1, 1, true, 2, 2])
        emit reverse("reaper")
        """
        self.assertEqual(
            self.capture(source),
            ["[[1, 2], [3, 4], [5]]", "[1, 2]", "[3, 4]",
             "[1, 2, 3, 4, 5]", "[1, true, 2]", "reaper"[::-1]],
        )

    def test_string_pipeline_and_utf8(self) -> None:
        source = """
        make words := "  Привет | Reaper  " :: trim() :: split("|") :: map(trim) :: map(upper)
        emit words :: join(" / ")
        emit replace("абракадабра", "бра", "БРА")
        emit contains("ёжик", "ёж")
        emit starts_with("Reaper Studio", "Reaper")
        emit ends_with("source.rpr", ".rpr")
        """
        self.assertEqual(
            self.capture(source),
            ["ПРИВЕТ / REAPER", "аБРАкадаБРА", "true", "true", "true"],
        )

    def test_collection_and_text_limits_apply_to_new_operations(self) -> None:
        interpreter = Interpreter(output=lambda _line: None, max_collection_items=2)
        with self.assertRaisesRegex(Exception, "collection item limit"):
            interpreter.run('emit "a,b,c" :: split(",")')
        interpreter = Interpreter(output=lambda _line: None, max_text_length=4)
        with self.assertRaisesRegex(Exception, "text length limit"):
            interpreter.run('emit join(["abc", "def"], ",")')

    def test_zero_and_invalid_collection_arguments_fail(self) -> None:
        for source, message in (
            ("emit chunk([1], 0)", "positive whole number"),
            ("emit take([1], -1)", "non-negative whole number"),
            ('emit split("abc", "")', "separator cannot be empty"),
            ('emit sorted([1, 2], "sideways")', "sort direction"),
        ):
            with self.subTest(source=source):
                with self.assertRaisesRegex(Exception, message):
                    self.capture(source)


class CliEnhancementTests(unittest.TestCase):
    def test_version_reports_language_edition(self) -> None:
        stdout = io.StringIO()
        with redirect_stdout(stdout):
            with self.assertRaises(SystemExit) as raised:
                main(["--version"])
        self.assertEqual(raised.exception.code, 0)
        self.assertIn("Reaper 0.2.0", stdout.getvalue())

    def test_json_run_and_profile(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "sample.rpr"
            path.write_text('emit "hello"\nemit 2 + 2\n', encoding="utf-8")
            stdout = io.StringIO()
            with redirect_stdout(stdout):
                code = main(["--json", "--profile", str(path)])
            result = json.loads(stdout.getvalue())
        self.assertEqual(code, 0)
        self.assertTrue(result["ok"])
        self.assertEqual(result["output"], ["hello", "4"])
        self.assertGreater(result["profile"]["steps"], 0)
        self.assertGreaterEqual(result["profile"]["elapsed_seconds"], 0)

    def test_json_diagnostics_capture_runtime_error(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "broken.rpr"
            path.write_text("emit 1 / 0\n", encoding="utf-8")
            stdout = io.StringIO()
            with redirect_stdout(stdout):
                code = main(["--json", str(path)])
            result = json.loads(stdout.getvalue())
        self.assertEqual(code, 1)
        self.assertFalse(result["ok"])
        self.assertEqual(result["error"]["type"], "ReaperRuntimeError")
        self.assertIn("division by zero", result["error"]["message"])

    def test_repl_keeps_one_environment_between_lines(self) -> None:
        stdout = io.StringIO()
        with patch("builtins.input", side_effect=["make value := 7", "emit value", ":quit"]):
            with redirect_stdout(stdout):
                code = main(["--repl"])
        self.assertEqual(code, 0)
        self.assertIn("7", stdout.getvalue())


if __name__ == "__main__":
    unittest.main()
