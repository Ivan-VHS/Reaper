from __future__ import annotations

import unittest

from reaper import Interpreter
from reaper.impact import DIMENSIONS, catalog, find_profile, rank_profiles, search_profiles


class ImpactProfileTests(unittest.TestCase):
    def test_catalog_is_complete_and_sequential(self):
        profiles = catalog()
        self.assertEqual(len(profiles), 20)
        self.assertEqual([item["id"] for item in profiles], list(range(1, 21)))
        self.assertTrue(all(set(item["ranks"]) == set(DIMENSIONS) for item in profiles))

    def test_search_and_lookup_use_all_three_terms(self):
        self.assertEqual(find_profile("Баллистический")["id"], 1)
        self.assertEqual(search_profiles("ГИГАНТСКИЙ")[0]["id"], 5)
        self.assertEqual(find_profile(20)["sound"], "Оглушительность")

    def test_unknown_and_ambiguous_queries_fail(self):
        with self.assertRaises(ValueError):
            find_profile("not-a-profile")
        with self.assertRaises(ValueError):
            find_profile("гром")

    def test_rank_is_stable_and_descending(self):
        ordered = rank_profiles(catalog(), "reach")
        ranks = [item["ranks"]["reach"] for item in ordered]
        self.assertEqual(ranks, sorted(ranks, reverse=True))
        self.assertEqual(ordered[0]["id"], 5)

    def test_language_builtins_are_executable(self):
        output: list[str] = []
        source = """
        make item := impact_profile("Баллистический")
        emit item["sound"]
        emit size(impact_rank(impact_catalog(), "reach"))
        emit size(impact_search("Гиперзвуковой"))
        """
        Interpreter(output=output.append).run(source)
        self.assertEqual(output, ["Грохот", "20", "1"])


if __name__ == "__main__":
    unittest.main()
