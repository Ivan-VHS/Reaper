from __future__ import annotations
import subprocess, tempfile, unittest
from pathlib import Path
from unittest.mock import patch
from tools.hmga_audit import HMGA_CONSTANTS, audit_repository


class HmgaAuditTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        (self.root / ".github/workflows").mkdir(parents=True)
        (self.root / "docs").mkdir()
        (self.root / "tests").mkdir()
        (self.root / ".github/workflows/ci.yml").write_text("name: CI\n", encoding="utf-8")
        (self.root / "docs/HMGA_V2.0.md").write_text("# HMGA\n", encoding="utf-8")
        (self.root / "tests/test_sample.py").write_text("# test\n", encoding="utf-8")

    def tearDown(self):
        self.temp.cleanup()

    def fake_git(self):
        values = {
            ("rev-parse", "--show-toplevel"): (0, str(self.root)),
            ("rev-parse", "--short=12", "HEAD"): (0, "0123456789ab"),
            ("symbolic-ref", "--short", "-q", "HEAD"): (0, "hmga/test"),
            ("status", "--porcelain"): (0, ""),
            ("for-each-ref", "--format=%(refname:short)", "refs/heads", "refs/remotes"):
                (0, "main\norigin/main\nhmga/test"),
            ("rev-list", "--all", "--count"): (0, "42"),
            ("rev-parse", "--is-shallow-repository"): (0, "false"),
        }
        def run(command, **_kwargs):
            code, stdout = values[tuple(command[3:])]
            return subprocess.CompletedProcess(command, code, stdout, "")
        return run

    def test_audit_collects_read_only_metadata(self):
        with patch("tools.hmga_audit.subprocess.run", side_effect=self.fake_git()):
            report = audit_repository(self.root)
        self.assertEqual(report.head, "0123456789ab")
        self.assertEqual(report.branch, "hmga/test")
        self.assertTrue(report.working_tree_clean)
        self.assertFalse(report.shallow_checkout)
        self.assertEqual(report.visible_commit_count, 42)
        self.assertEqual(report.visible_ref_count, 3)
        self.assertEqual(report.ci_workflows, (".github/workflows/ci.yml",))
        self.assertEqual(report.test_file_count, 1)
        self.assertTrue(report.hmga_policy_present)
        self.assertEqual(report.warnings, ())

    def test_missing_contract_items_are_reported(self):
        (self.root / "docs/HMGA_V2.0.md").unlink()
        (self.root / ".github/workflows/ci.yml").unlink()
        (self.root / "tests/test_sample.py").unlink()
        with patch("tools.hmga_audit.subprocess.run", side_effect=self.fake_git()):
            report = audit_repository(self.root)
        self.assertEqual(len(report.warnings), 3)

    def test_exact_specification_constants(self):
        self.assertEqual(HMGA_CONSTANTS, {
            "N_global": "66666666666666",
            "N_sub": "6454684531153413",
            "F_base": "654684676534",
            "M_mult": "646846453",
            "R_base": "54654654",
        })


if __name__ == "__main__":
    unittest.main()
