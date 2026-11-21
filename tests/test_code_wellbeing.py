"""Tests for the read-only codebase wellbeing inventory."""
from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from reaper.code_wellbeing import CodeWellbeingError, load_charter, scan_project


class CodeWellbeingTests(unittest.TestCase):
    def test_empty_project_reports_missing_evidence_without_score(self):
        with tempfile.TemporaryDirectory() as directory:
            report = scan_project(directory)
        self.assertEqual(report["inventory"]["total_files"], 0)
        self.assertNotIn("score", report)
        self.assertTrue(report["scan"]["read_only"])

    def test_inventory_detects_source_tests_readme_and_workflow(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "src").mkdir()
            (root / "tests").mkdir()
            (root / ".github" / "workflows").mkdir(parents=True)
            (root / "README.md").write_text("# Demo", encoding="utf-8")
            (root / "src" / "main.py").write_text("# TODO: review\nprint('ok')\n", encoding="utf-8")
            (root / "tests" / "test_main.py").write_text("def test_ok(): pass\n", encoding="utf-8")
            (root / ".github" / "workflows" / "ci.yml").write_text("name: CI\n", encoding="utf-8")
            report = scan_project(root)
        self.assertEqual(report["inventory"]["source_files"], 2)
        self.assertEqual(report["inventory"]["test_files"], 1)
        self.assertEqual(report["inventory"]["readme_files"], 1)
        self.assertEqual(report["inventory"]["ci_workflow_files"], 1)
        self.assertEqual(report["inventory"]["maintenance_markers"]["TODO"], 1)

    def test_ignored_build_and_vendor_trees_are_not_scanned(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            for folder in ("build", "vendor", "node_modules", ".git"):
                (root / folder).mkdir()
                (root / folder / "generated.py").write_text("pass\n", encoding="utf-8")
            report = scan_project(root)
        self.assertEqual(report["inventory"]["total_files"], 0)

    def test_missing_or_invalid_root_is_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            with self.assertRaises(CodeWellbeingError):
                scan_project(Path(directory) / "missing")

    def test_charter_is_explicitly_engineering_only(self):
        concept = load_charter()["concept"]
        self.assertTrue(concept["is_engineering_metaphor"])
        self.assertFalse(concept["clinical_equivalence"])

    def test_maintenance_markers_are_not_defects(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "main.py").write_text("# FIXME: context needed\n", encoding="utf-8")
            report = scan_project(root)
        finding = next(x for x in report["signals"] if x["id"] == "maintainability-review-cues")
        self.assertIn("not automatic defects", finding["note"])
        self.assertEqual(report["inventory"]["maintenance_markers"]["FIXME"], 1)

    def test_large_source_file_is_reported_as_partial_scan(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "large.py").write_text("x" * (1024 * 1024 + 16), encoding="utf-8")
            report = scan_project(root)
        self.assertTrue(report["scan"]["source_text_scan_truncated"])
        self.assertLessEqual(report["inventory"]["source_bytes_scanned"], 32 * 1024 * 1024)

    def test_json_report_is_serializable(self):
        with tempfile.TemporaryDirectory() as directory:
            report = scan_project(directory)
        self.assertIsInstance(json.dumps(report), str)


if __name__ == "__main__":
    unittest.main()
