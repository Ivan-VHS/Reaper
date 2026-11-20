from __future__ import annotations

import json
import unittest
from contextlib import redirect_stdout
from io import StringIO
from pathlib import Path
import tempfile

from reaper.cli import main as reaper_cli_main
from reaper.copyright import main, render_text, scan_project


class CopyrightInventoryTests(unittest.TestCase):
    def test_spdx_and_root_notice_inventory(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            (root / "LICENSE").write_text("Project license notice", encoding="utf-8")
            (root / "NOTICE").write_text("Attribution record", encoding="utf-8")
            source = root / "src"
            source.mkdir()
            (source / "declared.py").write_text(
                "# SPDX-License-Identifier: MIT\n# Copyright 2026 Example\nprint('ok')\n",
                encoding="utf-8",
            )
            (source / "inherited.c").write_text("int main(void) { return 0; }\n", encoding="utf-8")
            (root / ".venv").mkdir()
            (root / ".venv" / "ignored.py").write_text("no scan", encoding="utf-8")

            report = scan_project(root)
            self.assertEqual(report["source_files_scanned"], 2)
            self.assertEqual(report["license_files"], ["LICENSE"])
            self.assertEqual(report["notice_files"], ["NOTICE"])
            self.assertEqual(report["counts"]["spdx_declared"], 1)
            self.assertEqual(report["counts"]["missing_file_spdx"], 1)
            declared = next(item for item in report["files"] if item["path"].endswith("declared.py"))
            self.assertEqual(declared["spdx_expression"], "MIT")
            self.assertTrue(declared["copyright_notice"])

    def test_missing_spdx_is_reviewed_even_when_root_license_exists(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            (root / "LICENSE").write_text("License text", encoding="utf-8")
            (root / "module.rs").write_text("fn main() {}", encoding="utf-8")
            report = scan_project(root)
            self.assertEqual(report["counts"]["needs_license_review"], 0)
            self.assertEqual(report["counts"]["missing_file_spdx"], 1)
            self.assertEqual(report["files"][0]["classification"], "repository-license-present")

    def test_unlicensed_source_is_flagged_for_review(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            (root / "code.c").write_text("/* no declaration */\n", encoding="utf-8")
            report = scan_project(root)
            self.assertEqual(report["counts"]["needs_license_review"], 1)
            self.assertEqual(report["files"][0]["classification"], "needs-license-review")

    def test_require_spdx_fails_for_missing_file_header(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            (root / "LICENSE").write_text("License text", encoding="utf-8")
            (root / "code.py").write_text("print('missing SPDX')\n", encoding="utf-8")
            with redirect_stdout(StringIO()):
                self.assertEqual(main([str(root), "--require-spdx"]), 1)

    def test_json_cli_and_text_output(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            (root / "file.py").write_text("# SPDX-License-Identifier: Apache-2.0\n", encoding="utf-8")
            with redirect_stdout(StringIO()) as output:
                self.assertEqual(main([str(root), "--json"]), 0)
            report = json.loads(output.getvalue())
            self.assertEqual(report["counts"]["spdx_declared"], 1)
            self.assertIn("\n", render_text(report))

    def test_reaper_cli_dispatch(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            (root / "module.py").write_text("# SPDX-License-Identifier: MIT\\n", encoding="utf-8")
            with redirect_stdout(StringIO()) as output:
                result = reaper_cli_main(["copyright-scan", str(root), "--json"])
            self.assertEqual(result, 0)
            self.assertEqual(json.loads(output.getvalue())["counts"]["spdx_declared"], 1)

    def test_size_limits_are_reported(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            (root / "large.py").write_text("x" * 100, encoding="utf-8")
            report = scan_project(root, max_file_bytes=10)
            self.assertEqual(report["source_files_scanned"], 0)
            self.assertTrue(any("oversized" in warning for warning in report["warnings"]))


if __name__ == "__main__":
    unittest.main()
