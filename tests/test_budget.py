from __future__ import annotations

import unittest

from reaper.budget import BudgetError, calculate_budget


class BudgetPlannerTests(unittest.TestCase):
    def test_default_weekly_split_uses_exactly_500(self):
        result = calculate_budget()
        self.assertEqual(result["budget_uah"], 500)
        self.assertEqual(result["planned_uah"], 500)
        self.assertEqual(result["remaining_uah"], 0)
        self.assertTrue(result["within_budget"])

    def test_coffee_scenario_matches_ten_espresso_reference(self):
        result = calculate_budget(scenario="coffee")
        amounts = {item["id"]: item["amount_uah"] for item in result["allocations"]}
        self.assertEqual(amounts["leisure"], 460)
        self.assertEqual(amounts["reserve"], 40)

    def test_custom_allocations_report_remaining_or_overage(self):
        result = calculate_budget(500, "weekly", {"food": 350, "transport": 200})
        self.assertEqual(result["planned_uah"], 670)
        self.assertEqual(result["remaining_uah"], -170)
        self.assertEqual(result["over_budget_uah"], 170)
        self.assertFalse(result["within_budget"])

    def test_invalid_amounts_are_rejected(self):
        for value in (-1, 1.5, True, 1_000_001):
            with self.subTest(value=value), self.assertRaises(BudgetError):
                calculate_budget(value)

    def test_unknown_or_invalid_allocations_are_rejected(self):
        with self.assertRaises(BudgetError):
            calculate_budget(scenario="unknown")
        with self.assertRaises(BudgetError):
            calculate_budget(overrides={"mystery": 10})
        with self.assertRaises(BudgetError):
            calculate_budget(overrides={"food": -10})

    def test_reference_prices_keep_their_estimated_ranges(self):
        result = calculate_budget()
        buckwheat = next(row for row in result["reference_prices"] if row["item"] == "Гречка")
        self.assertEqual((buckwheat["min_uah"], buckwheat["max_uah"]), (75, 88))
        self.assertIn("не проверена", result["price_basis"])


if __name__ == "__main__":
    unittest.main()
