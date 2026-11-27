from __future__ import annotations

import json
import unittest
from pathlib import Path


class PytyReContractTests(unittest.TestCase):
    def test_reciprocal_contract_is_complete_and_versioned(self) -> None:
        path = Path(__file__).resolve().parents[1] / "contracts" / "pytyre.reciprocal.v1.json"
        contract = json.loads(path.read_text(encoding="utf-8"))
        self.assertEqual(contract["schema"], "pytyre.reciprocal-development.v1")
        self.assertEqual(contract["system"]["name"], "PytyRe")
        self.assertEqual(contract["system"]["definition"], "Reaper + Pytyliki")
        self.assertEqual(
            {item["id"] for item in contract["interfaces"]},
            {"pytyliki.c-abi.v1", "reaper.c-abi.v1"},
        )
        self.assertEqual(
            {item["direction"] for item in contract["interfaces"]},
            {"pytyliki-to-reaper", "reaper-to-pytyliki"},
        )
        self.assertTrue(contract["development_policy"]["change_rule"])
        self.assertTrue(contract["safety_boundaries"])
        self.assertEqual(contract["repositories"]["reaper"]["baseline_commit"], "c3d89dd91da880e523867bd8d0724a6edc6b3cf6")
        self.assertEqual(contract["repositories"]["pytyliki"]["baseline_commit"], "41edd2bd33fbf554c8a8cbdc1ddd97847e1f9a53")


if __name__ == "__main__":
    unittest.main()
