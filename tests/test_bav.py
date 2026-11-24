from __future__ import annotations

import unittest
from pathlib import Path

from reaper.bav import merge_reports


class BAVMergeTests(unittest.TestCase):
    def setUp(self) -> None:
        self.root = Path("/tmp/bav-test")

    def test_blocked_verdict_has_precedence(self) -> None:
        merged = merge_reports(
            {"verdict": "review", "risk_score": 14, "findings": [
                {"rule_id": "M-02", "severity": "high", "enforcement": "review",
                 "path": "src/app.py", "line": 2, "message": "dynamic execution"}
            ], "policy": {"rules_total": 66}, "scan": {}},
            {"verdict": "blocked", "risk_score": 25, "findings": [
                {"rule_id": "BAV-J-001", "severity": "critical", "enforcement": "block",
                 "path": "src/App.java", "line": 4, "message": "credential detected"}
            ], "policy": {"rules_total": 8}, "scan": {}},
            self.root,
        )
        self.assertEqual(merged["verdict"], "blocked")
        self.assertEqual(merged["risk_score"], 25)
        self.assertEqual(merged["findings_count"], 2)

    def test_duplicate_findings_are_deduplicated_without_losing_source(self) -> None:
        finding = {"rule_id": "A-04", "severity": "critical", "enforcement": "block",
                   "path": "src/a.py", "line": 1, "message": "bad encoding"}
        merged = merge_reports(
            {"verdict": "blocked", "risk_score": 25, "findings": [finding],
             "policy": {"rules_total": 66}, "scan": {}},
            {"verdict": "blocked", "risk_score": 25, "findings": [finding],
             "policy": {"rules_total": 8}, "scan": {}},
            self.root,
        )
        self.assertEqual(merged["findings_count"], 1)
        self.assertEqual(merged["findings"][0]["component"], "beelzebul")

    def test_clean_verdict_requires_both_engines_to_be_clear(self) -> None:
        merged = merge_reports(
            {"verdict": "clear", "risk_score": 0, "findings": [],
             "policy": {"rules_total": 66}, "scan": {}},
            {"verdict": "clear", "risk_score": 0, "findings": [],
             "policy": {"rules_total": 8}, "scan": {}},
            self.root,
        )
        self.assertEqual(merged["verdict"], "clear")
        self.assertTrue(merged["scan"]["read_only"])
        self.assertFalse(merged["scan"]["project_code_executed"])


if __name__ == "__main__":
    unittest.main()
