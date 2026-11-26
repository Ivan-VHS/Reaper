from __future__ import annotations

import contextlib
import io
import json
import unittest

from reaper.cli import main


class FrameworkPortfolioCliTests(unittest.TestCase):
    def run_cli(self, *arguments: str) -> tuple[int, str, str]:
        stdout = io.StringIO()
        stderr = io.StringIO()
        with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
            code = main(list(arguments))
        return code, stdout.getvalue(), stderr.getvalue()

    def test_framework_list_reports_the_unified_catalogue(self) -> None:
        code, stdout, stderr = self.run_cli("--frameworks")
        self.assertEqual(code, 0, stderr)
        result = json.loads(stdout)
        self.assertEqual(result["module_count"], 60)
        self.assertEqual(result["integration_surface_count"], 19)
        self.assertEqual(result["external_framework_count"], 20)
        self.assertEqual(result["total_discoverable_entries"], 99)

    def test_framework_info_finds_a_new_module(self) -> None:
        code, stdout, stderr = self.run_cli("--framework-info", "Vorke")
        self.assertEqual(code, 0, stderr)
        result = json.loads(stdout)
        self.assertEqual(result["id"], "framework.vorke")
        self.assertEqual(result["record_type"], "framework")

    def test_framework_info_finds_external_rforge_archetype(self) -> None:
        code, stdout, stderr = self.run_cli("--framework-info", "Plague")
        self.assertEqual(code, 0, stderr)
        result = json.loads(stdout)
        self.assertEqual(result["record_type"], "adjacent_framework")
        self.assertEqual(result["collection_id"], "rforge")
        self.assertEqual(result["status"], "source_present_runtime_validation_pending")

    def test_framework_search_includes_integration_surfaces(self) -> None:
        code, stdout, stderr = self.run_cli("--framework-search", "federation")
        self.assertEqual(code, 0, stderr)
        result = json.loads(stdout)
        self.assertGreater(result["count"], 0)
        self.assertTrue(
            any(item["record_type"] == "integration_surface" for item in result["results"])
        )

    def test_framework_info_reports_unknown_entries(self) -> None:
        code, stdout, stderr = self.run_cli("--framework-info", "not-a-framework")
        self.assertEqual(code, 1)
        self.assertEqual(stdout, "")
        self.assertIn("framework not found", stderr)


if __name__ == "__main__":
    unittest.main()
