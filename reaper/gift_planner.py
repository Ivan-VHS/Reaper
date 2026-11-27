"""Exact, deterministic gift-budget planning built on integer arithmetic.

Currency is supplied as integer units (whole UAH or kopiykas). Candy selection is
a transparent preference/price greedy heuristic, not a global knapsack guarantee.
"""
from __future__ import annotations

import argparse
import json
import math
from dataclasses import asdict, dataclass
from fractions import Fraction
from typing import Sequence

from .decomposition import distribute_weighted, split_evenly

MAX_RECIPIENTS = 256
MAX_CANDIES = 256
MAX_BUDGET = 10_000_000


@dataclass(frozen=True, slots=True)
class Candy:
    name: str
    category: str
    price: int
    stock: int
    preference: int = 1
    weight_grams: int = 0

    def validate(self) -> None:
        if not isinstance(self.name, str) or not self.name.strip():
            raise ValueError("candy name must be non-empty text")
        if not isinstance(self.category, str) or not self.category.strip():
            raise ValueError("candy category must be non-empty text")
        for label, value, minimum in (
            ("price", self.price, 1), ("stock", self.stock, 0),
            ("preference", self.preference, 1), ("weight_grams", self.weight_grams, 0),
        ):
            if isinstance(value, bool) or not isinstance(value, int) or value < minimum:
                raise ValueError(f"{label} must be an integer >= {minimum}")


@dataclass(frozen=True, slots=True)
class CandyLine:
    candy_index: int
    candy_name: str
    category: str
    unit_price: int
    quantity: int
    line_total: int
    weight_grams: int


@dataclass(frozen=True, slots=True)
class GreetingEdge:
    sender_index: int
    recipient_index: int
    template_index: int


@dataclass(frozen=True, slots=True)
class GiftPlan:
    budget: int
    allocations: tuple[int, ...]
    baskets: tuple[tuple[CandyLine, ...], ...]
    spent: int
    remaining: int
    greeting_edges: tuple[GreetingEdge, ...]

    def verify(self) -> bool:
        if len(self.allocations) != len(self.baskets):
            return False
        if sum(self.allocations) != self.budget:
            return False
        if self.spent + self.remaining != self.budget or not 0 <= self.spent <= self.budget:
            return False
        basket_spent = 0
        for basket, allocation in zip(self.baskets, self.allocations):
            basket_total = sum(line.line_total for line in basket)
            if basket_total > allocation:
                return False
            basket_spent += basket_total
        return basket_spent == self.spent


def allocate_equal(total: int, recipients: int) -> tuple[int, ...]:
    """Split an integer total; earlier recipients receive indivisible remainder."""
    _validate_total(total)
    _validate_count(recipients, MAX_RECIPIENTS, "recipients")
    return split_evenly(total, recipients)


def allocate_weighted(total: int, weights: Sequence[int]) -> tuple[int, ...]:
    """Allocate by integer weights with largest remainders and stable ties."""
    _validate_total(total)
    if not isinstance(weights, (list, tuple)) or not weights:
        raise ValueError("weights must be a non-empty list or tuple")
    if len(weights) > MAX_RECIPIENTS:
        raise ValueError(f"at most {MAX_RECIPIENTS} weights are supported")
    for index, weight in enumerate(weights):
        if isinstance(weight, bool) or not isinstance(weight, int) or weight < 0:
            raise ValueError(f"weights[{index}] must be a non-negative integer")
    return distribute_weighted(total, weights)


def percent_of(total: int, percent: int) -> int:
    """Return floor(total * percent / 100), without floating-point arithmetic."""
    _validate_total(total)
    if isinstance(percent, bool) or not isinstance(percent, int) or not 0 <= percent <= 100:
        raise ValueError("percent must be an integer from 0 to 100")
    return total * percent // 100


def combination_count(n: int, k: int) -> int:
    """Return exact n-choose-k; bounded to keep work predictable."""
    for label, value in (("n", n), ("k", k)):
        if isinstance(value, bool) or not isinstance(value, int) or value < 0:
            raise ValueError(f"{label} must be a non-negative integer")
    if n > 1_000_000 or k > n:
        raise ValueError("require 0 <= k <= n <= 1000000")
    result = math.comb(n, k)
    if result.bit_length() > 4096:
        raise ValueError("combination count exceeds the 4096-bit result limit")
    return result


def build_candy_basket(
    budget: int, catalog: Sequence[Candy]
) -> tuple[tuple[CandyLine, ...], int]:
    """Choose stock-limited candy by preference/price with stable input-order ties."""
    _validate_total(budget)
    if not isinstance(catalog, (list, tuple)) or len(catalog) > MAX_CANDIES:
        raise ValueError(f"catalog must be a list or tuple of at most {MAX_CANDIES} items")
    candies = list(catalog)
    for candy in candies:
        if not isinstance(candy, Candy):
            raise TypeError("catalog entries must be Candy instances")
        candy.validate()
    order = sorted(
        enumerate(candies),
        key=lambda pair: (-Fraction(pair[1].preference, pair[1].price), pair[0]),
    )
    remaining = budget
    lines: list[CandyLine] = []
    for candy_index, candy in order:
        quantity = min(candy.stock, remaining // candy.price)
        if quantity <= 0:
            continue
        line_total = quantity * candy.price
        lines.append(CandyLine(
            candy_index, candy.name, candy.category, candy.price, quantity,
            line_total, quantity * candy.weight_grams,
        ))
        remaining -= line_total
    return tuple(lines), budget - remaining


def build_greeting_graph(
    sender_count: int, recipient_count: int, greeting_template_count: int
) -> tuple[GreetingEdge, ...]:
    """Create a complete bipartite graph with deterministic greeting rotation."""
    _validate_count(sender_count, MAX_RECIPIENTS, "sender_count")
    _validate_count(recipient_count, MAX_RECIPIENTS, "recipient_count")
    _validate_count(greeting_template_count, MAX_RECIPIENTS, "greeting_template_count")
    if sender_count * recipient_count > 65_536:
        raise ValueError("greeting graph exceeds the 65536-edge limit")
    return tuple(
        GreetingEdge(sender, recipient, (sender + recipient) % greeting_template_count)
        for sender in range(sender_count)
        for recipient in range(recipient_count)
    )


def plan_gift(
    budget: int = 500,
    recipients: int = 5,
    catalog: Sequence[Candy] | None = None,
    greeting_templates: Sequence[str] | None = None,
    weights: Sequence[int] | None = None,
    sender_count: int = 1,
) -> GiftPlan:
    """Create one stock-aware basket and one or more greeting links per recipient."""
    _validate_total(budget)
    _validate_count(recipients, MAX_RECIPIENTS, "recipients")
    _validate_count(sender_count, MAX_RECIPIENTS, "sender_count")
    templates = tuple(greeting_templates if greeting_templates is not None else ("Поздравляю!",))
    if not 1 <= len(templates) <= MAX_RECIPIENTS:
        raise ValueError("provide 1 to 256 greeting templates")
    if any(not isinstance(item, str) or not item.strip() for item in templates):
        raise ValueError("greeting templates must be non-empty strings")
    allocations = allocate_equal(budget, recipients) if weights is None else allocate_weighted(budget, weights)
    if len(allocations) != recipients:
        raise ValueError("weights must contain exactly one entry per recipient")
    available = list(catalog or ())
    baskets: list[tuple[CandyLine, ...]] = []
    spent = 0
    for share in allocations:
        basket, basket_spent = build_candy_basket(share, available)
        baskets.append(basket)
        spent += basket_spent
        for line in basket:
            candy = available[line.candy_index]
            available[line.candy_index] = Candy(
                candy.name, candy.category, candy.price,
                candy.stock - line.quantity, candy.preference, candy.weight_grams,
            )
    result = GiftPlan(
        budget, tuple(allocations), tuple(baskets), spent, budget - spent,
        build_greeting_graph(sender_count, recipients, len(templates)),
    )
    if not result.verify():
        raise AssertionError("gift plan violated its conservation invariant")
    return result


def _validate_total(total: int) -> None:
    if isinstance(total, bool) or not isinstance(total, int) or not 0 <= total <= MAX_BUDGET:
        raise ValueError(f"total must be an integer from 0 to {MAX_BUDGET}")


def _validate_count(value: int, maximum: int, label: str) -> None:
    if isinstance(value, bool) or not isinstance(value, int) or not 1 <= value <= maximum:
        raise ValueError(f"{label} must be an integer from 1 to {maximum}")


def _default_catalog() -> tuple[Candy, ...]:
    return (
        Candy("Шоколадное пралине", "шоколад", 18, 30, 5, 14),
        Candy("Ореховый трюфель", "трюфель", 24, 20, 5, 16),
        Candy("Вафельный брусок", "вафля", 12, 25, 3, 18),
        Candy("Фруктовая карамель", "карамель", 8, 40, 2, 10),
        Candy("Ягодный мармелад", "желе", 10, 30, 4, 12),
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Plan a bounded gift basket with exact integer allocation.")
    parser.add_argument("--budget", type=int, default=500, help="integer budget units (default: 500)")
    parser.add_argument("--recipients", type=int, default=5, help="number of recipients")
    parser.add_argument("--senders", type=int, default=1, help="number of greeting senders")
    args = parser.parse_args(argv)
    plan = plan_gift(
        args.budget, args.recipients, _default_catalog(),
        ("Счастья и радости!", "Здоровья и сил!", "Пусть сбываются мечты!"),
        sender_count=args.senders,
    )
    print(json.dumps(asdict(plan), ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
