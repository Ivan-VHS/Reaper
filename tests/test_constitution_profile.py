"""Validate that the engineering rule implementation profile stays complete and explicit."""

from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
PROFILE = ROOT / "docs" / "ENGINEERING_CONSTITUTION_PROFILE.md"


class ConstitutionProfileTests(unittest.TestCase):
    def test_profile_exists_and_covers_all_six_rule_ranges(self):
        self.assertTrue(PROFILE.is_file())
        text = PROFILE.read_text(encoding="utf-8").lower()
        for rule_range in ("1–111", "112–222", "223–333", "334–444", "445–555", "556–666"):
            with self.subTest(rule_range=rule_range):
                self.assertIn(rule_range, text)

    def test_profile_preserves_truthful_conformance_states(self):
        text = PROFILE.read_text(encoding="utf-8").lower()
        for state in ("implemented", "partial", "planned", "not applicable"):
            with self.subTest(state=state):
                self.assertIn(state, text)

    def test_profile_does_not_claim_the_full_constitution_is_shipped(self):
        text = PROFILE.read_text(encoding="utf-8").lower()
        self.assertIn("does not claim", text)
        self.assertIn("tests and ci evidence", text)


if __name__ == "__main__":
    unittest.main()
