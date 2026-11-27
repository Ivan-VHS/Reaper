from __future__ import annotations

import json
import unittest

from tools.validate_most_keywords import ROOT, validate


class MostRussianNativeProfileTests(unittest.TestCase):
    def test_alias_manifest_matches_both_lexers(self) -> None:
        self.assertEqual(validate(ROOT), [])

    def test_profile_contains_twenty_distinct_principles(self) -> None:
        profile = json.loads(
            (ROOT / "language" / "most_russian_native_profile.json").read_text(encoding="utf-8")
        )
        principles = profile["principles"]
        self.assertEqual(len(principles), 20)
        self.assertEqual(len({item["id"] for item in principles}), 20)
        self.assertEqual(profile["principle_count"], 20)

    def test_profile_preserves_project_and_third_party_rights(self) -> None:
        profile = json.loads(
            (ROOT / "language" / "most_russian_native_profile.json").read_text(encoding="utf-8")
        )
        rights = profile["rights"]
        self.assertEqual(rights["project_license"], "Apache-2.0")
        self.assertIn("third-party", rights["third_party_rights"].lower())
        self.assertIn("attribution", rights["third_party_rights"].lower())

    def test_lexical_reservations_are_not_misrepresented_as_runtime(self) -> None:
        manifest = json.loads(
            (ROOT / "language" / "most_keyword_aliases.json").read_text(encoding="utf-8")
        )
        runtime = [item for item in manifest["aliases"] if item["support"] == "runtime"]
        reserved = [item for item in manifest["aliases"] if item["support"] == "lexical_reserved"]
        self.assertEqual(len(runtime), 38)
        self.assertEqual(len(reserved), 64)


if __name__ == "__main__":
    unittest.main()
