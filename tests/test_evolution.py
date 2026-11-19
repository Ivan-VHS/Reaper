from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from reaper.evolution import EvolutionEngine


class EvolutionEngineTests(unittest.TestCase):
    def make_project(
        self, source: str = "value = 1\n", *, include_test: bool = True
    ) -> Path:
        directory = Path(tempfile.mkdtemp())
        package = directory / "reaper"
        package.mkdir()
        (package / "__init__.py").write_text("", encoding="utf-8")
        (package / "sample.py").write_text(source, encoding="utf-8")
        (directory / "tests").mkdir()
        (directory / "tests" / "__init__.py").write_text("", encoding="utf-8")
        if include_test:
            (directory / "tests" / "test_smoke.py").write_text(
                "import unittest\n\n"
                "class SmokeTests(unittest.TestCase):\n"
                "    def test_smoke(self):\n"
                "        self.assertEqual(1 + 1, 2)\n",
                encoding="utf-8",
            )
        return directory

    def test_syntax_check_and_report_are_machine_readable(self) -> None:
        root = self.make_project()
        report = EvolutionEngine(root).run()
        self.assertTrue(report.passed)
        self.assertIn('"passed": true', report.to_json())
        self.assertEqual(report.iterations, 1)

    def test_empty_test_suite_fails_closed(self) -> None:
        root = self.make_project(include_test=False)
        report = EvolutionEngine(root).run()
        self.assertFalse(report.passed)
        self.assertIn("zero tests", report.checks[1].summary)

    def test_syntax_error_fails_closed_without_running_tests(self) -> None:
        root = self.make_project("def broken(:\n")
        report = EvolutionEngine(root).run()
        self.assertFalse(report.passed)
        self.assertEqual(len(report.checks), 1)
        self.assertIn("python-syntax", report.checks[0].name)

    def test_iteration_budget_is_bounded(self) -> None:
        root = self.make_project()
        with self.assertRaises(ValueError):
            EvolutionEngine(root).run(0)
        with self.assertRaises(ValueError):
            EvolutionEngine(root).run(21)

    def test_missing_module_test_is_reported_as_proposal(self) -> None:
        root = self.make_project()
        report = EvolutionEngine(root).run()
        self.assertTrue(any("sample.py" in item for item in report.proposals))


if __name__ == "__main__":
    unittest.main()
