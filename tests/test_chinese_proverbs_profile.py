"""Conformance checks for the 100-item Chinese-proverbs engineering crosswalk."""
from pathlib import Path
import re
import unittest
ROOT = Path(__file__).resolve().parents[1]
DOC = ROOT / "docs" / "CHINESE_PROVERBS_100_ENGINEERING_CROSSWALK.md"
class ChineseProverbsProfileTests(unittest.TestCase):
    def test_all_one_hundred_source_items_are_present_in_order(self):
        text = DOC.read_text(encoding="utf-8")
        ids = [int(value) for value in re.findall(r"^\|\s*(\d{3})\s*\|", text, re.M)]
        self.assertEqual(ids, list(range(1, 101)))
    def test_profile_preserves_safety_and_evidence_boundaries(self):
        text = DOC.read_text(encoding="utf-8").lower()
        for phrase in ("review required", "not a technical proof", "least privilege",
                       "isolated defensive test environments", "exact ci run and commit sha",
                       "do not claim sandboxing"):
            with self.subTest(phrase=phrase):
                self.assertIn(phrase, text)
if __name__ == "__main__":
    unittest.main()
