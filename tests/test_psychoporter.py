"""Regression tests for the Psychoporter 666 document validator."""
from __future__ import annotations

import re
import unittest

from tools.validate_psychoporter import (
    CONSTITUTION_PATH,
    PROFILE_PATH,
    validate_constitution,
    validate_profile,
)


class PsychoporterValidatorTests(unittest.TestCase):
    def setUp(self) -> None:
        self.constitution = CONSTITUTION_PATH.read_text(encoding="utf-8")
        self.profile = PROFILE_PATH.read_text(encoding="utf-8")

    def test_repository_documents_are_valid(self) -> None:
        self.assertEqual(validate_constitution(self.constitution), [])
        self.assertEqual(validate_profile(self.profile), [])

    def test_missing_rule_is_rejected(self) -> None:
        changed = re.sub(r"^100\..*\n", "", self.constitution, count=1, flags=re.MULTILINE)
        errors = validate_constitution(changed)
        self.assertTrue(any("missing rule numbers: 100" in error for error in errors))

    def test_duplicate_rule_is_rejected(self) -> None:
        rule = next(line for line in self.constitution.splitlines() if line.startswith("100. "))
        changed = self.constitution.replace(rule + "\n", rule + "\n" + rule + "\n", 1)
        errors = validate_constitution(changed)
        self.assertTrue(any("duplicate rule numbers: 100" in error for error in errors))

    def test_profile_must_cover_every_canonical_range(self) -> None:
        changed = "\n".join(
            line for line in self.profile.splitlines() if "| 601–660 |" not in line
        )
        errors = validate_profile(changed)
        self.assertTrue(any("601–660" in error for error in errors))

    def test_numbered_spheres_must_remain_in_order(self) -> None:
        changed = self.constitution.replace("## II. Синтаксис", "## III. Синтаксис", 1)
        errors = validate_constitution(changed)
        self.assertTrue(any("eleven numbered spheres" in error for error in errors))


if __name__ == "__main__":
    unittest.main()
