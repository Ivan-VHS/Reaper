from __future__ import annotations

import unittest
from dataclasses import replace

from reaper.gift_planner import (
    Candy, allocate_equal, allocate_weighted, build_candy_basket,
    build_greeting_graph, combination_count, percent_of, plan_gift,
)


class GiftPlannerTests(unittest.TestCase):
    def setUp(self) -> None:
        self.catalog = (
            Candy("Praline", "chocolate", 18, 30, 5, 14),
            Candy("Truffle", "truffle", 24, 20, 5, 16),
            Candy("Wafer", "wafer", 12, 25, 3, 18),
        )

    def test_integer_split_and_percent(self) -> None:
        self.assertEqual(allocate_equal(500, 5), (100, 100, 100, 100, 100))
        self.assertEqual(allocate_equal(10, 3), (4, 3, 3))
        self.assertEqual(allocate_weighted(500, (2, 1, 1)), (250, 125, 125))
        self.assertEqual(percent_of(500, 25), 125)
        self.assertEqual(percent_of(500, 1), 5)

    def test_combination_count_exact_and_symmetric(self) -> None:
        self.assertEqual(combination_count(5, 2), 10)
        self.assertEqual(combination_count(5, 3), 10)
        self.assertEqual(combination_count(5, 0), 1)

    def test_basket_respects_budget_and_stock(self) -> None:
        lines, spent = build_candy_basket(100, self.catalog)
        self.assertLessEqual(spent, 100)
        self.assertEqual(spent, sum(line.line_total for line in lines))
        self.assertTrue(all(line.quantity > 0 for line in lines))
        self.assertTrue(all(line.line_total == line.unit_price * line.quantity for line in lines))

    def test_plan_conserves_budget_and_builds_greeting_graph(self) -> None:
        plan = plan_gift(
            500, 5, self.catalog, ("hello", "best wishes", "congrats"), sender_count=2,
        )
        self.assertTrue(plan.verify())
        self.assertEqual(plan.allocations, (100, 100, 100, 100, 100))
        self.assertEqual(len(plan.baskets), 5)
        self.assertEqual(len(plan.greeting_edges), 10)
        self.assertEqual(plan.greeting_edges[-1].template_index, 2)
        self.assertFalse(replace(plan, baskets=()).verify())
        self.assertFalse(replace(plan, spent=plan.spent + 1).verify())

    def test_invalid_values_rejected(self) -> None:
        calls = (
            lambda: allocate_equal(500, 0),
            lambda: allocate_weighted(500, (0, 0)),
            lambda: percent_of(500, 101),
            lambda: combination_count(4, 5),
            lambda: build_candy_basket(100, (Candy("bad", "candy", 0, 1),)),
            lambda: build_greeting_graph(1, 1, 0),
            lambda: plan_gift(500, 2, self.catalog, weights=(1,)),
        )
        for call in calls:
            with self.subTest(call=call):
                with self.assertRaises((TypeError, ValueError)):
                    call()


if __name__ == "__main__":
    unittest.main()
