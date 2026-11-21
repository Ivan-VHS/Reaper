"""Offline micro-budget planner seeded from the supplied 500 UAH article.

All prices are user-provided planning estimates, not live store or tariff quotes.
"""
from __future__ import annotations

import argparse
import json
from typing import Any, Mapping

DEFAULT_AMOUNT = 500
MAX_AMOUNT = 1_000_000
CATEGORIES = ("food", "transport", "household", "digital", "leisure", "reserve")
LABELS = {
    "food": "Продукты и питание",
    "transport": "Транспорт",
    "household": "Быт и здоровье",
    "digital": "Связь и обучение",
    "leisure": "Досуг и кофе",
    "reserve": "Резерв",
}
SCENARIOS: dict[str, dict[str, int]] = {
    "weekly": {"food": 280, "transport": 120, "household": 0, "digital": 0, "leisure": 50, "reserve": 50},
    "groceries": {"food": 500, "transport": 0, "household": 0, "digital": 0, "leisure": 0, "reserve": 0},
    "transport": {"food": 0, "transport": 500, "household": 0, "digital": 0, "leisure": 0, "reserve": 0},
    "coffee": {"food": 0, "transport": 0, "household": 0, "digital": 0, "leisure": 460, "reserve": 40},
    "household": {"food": 0, "transport": 0, "household": 500, "digital": 0, "leisure": 0, "reserve": 0},
    "learning": {"food": 0, "transport": 0, "household": 0, "digital": 500, "leisure": 0, "reserve": 0},
    "reserve": {"food": 0, "transport": 0, "household": 0, "digital": 0, "leisure": 0, "reserve": 500},
}
SCENARIO_LABELS = {
    "weekly": "Недельный баланс",
    "groceries": "Продуктовый минимум",
    "transport": "Транспортный запас",
    "coffee": "Кофе и перезагрузка",
    "household": "Бытовой рефилл",
    "learning": "Инвестиция в себя",
    "reserve": "Неприкосновенный резерв",
}
REFERENCE_PRICES: tuple[dict[str, Any], ...] = (
    {"item": "Эспрессо", "unit": "чашка", "min_uah": 46, "max_uah": 46},
    {"item": "Гречка", "unit": "кг", "min_uah": 75, "max_uah": 88},
    {"item": "Рис", "unit": "кг", "min_uah": 52, "max_uah": 61},
    {"item": "Макароны", "unit": "кг", "min_uah": 40, "max_uah": 43},
    {"item": "Мука", "unit": "кг", "min_uah": 23, "max_uah": 24},
    {"item": "Хлеб", "unit": "кг", "min_uah": 50, "max_uah": 68},
    {"item": "Капучино или латте", "unit": "чашка, расчётный ориентир", "min_uah": 64, "max_uah": 74, "derived_from_espresso": True},
    {"item": "Батон", "unit": "500 г", "min_uah": 33, "max_uah": 35},
    {"item": "Молоко", "unit": "л", "min_uah": 50, "max_uah": 54},
    {"item": "Яйца", "unit": "10 шт.", "min_uah": 40, "max_uah": 61},
    {"item": "Картофель", "unit": "кг", "min_uah": 16, "max_uah": 24},
    {"item": "Яблоки", "unit": "кг", "min_uah": 35, "max_uah": 57},
    {"item": "Куриная тушка", "unit": "кг", "min_uah": 110, "max_uah": 116},
    {"item": "Куриное филе", "unit": "кг", "min_uah": 208, "max_uah": 220},
)
TRANSPORT_ESTIMATES = {
    "Киев": {"metro": 30, "municipal": 30},
    "Днепр": {"bus": 23, "tram_trolleybus": 25, "metro": 10},
    "Львов": {"electronic_ticket_min": 23, "electronic_ticket_max": 30},
}
PRICE_BASIS = "Оценки взяты из предоставленного пользователем материала; актуальность не проверена."


class BudgetError(ValueError):
    """Invalid amount, scenario or allocation."""


def calculate_budget(
    amount: int = DEFAULT_AMOUNT,
    scenario: str = "weekly",
    overrides: Mapping[str, int] | None = None,
) -> dict[str, Any]:
    if isinstance(amount, bool) or not isinstance(amount, int) or not 0 <= amount <= MAX_AMOUNT:
        raise BudgetError(f"Сумма должна быть целым числом от 0 до {MAX_AMOUNT} грн")
    if scenario not in SCENARIOS:
        raise BudgetError(f"Неизвестный сценарий: {scenario}")
    allocations = dict(SCENARIOS[scenario])
    if overrides:
        for category, value in overrides.items():
            if category not in CATEGORIES:
                raise BudgetError(f"Неизвестная категория: {category}")
            if isinstance(value, bool) or not isinstance(value, int) or not 0 <= value <= MAX_AMOUNT:
                raise BudgetError(f"Некорректная сумма категории {category}")
            allocations[category] = value
    planned = sum(allocations.values())
    remaining = amount - planned
    return {
        "schema": "reaper.microbudget.v1",
        "currency": "UAH",
        "budget_uah": amount,
        "scenario": scenario,
        "scenario_label": SCENARIO_LABELS[scenario],
        "allocations": [
            {"id": key, "label": LABELS[key], "amount_uah": allocations[key]}
            for key in CATEGORIES
        ],
        "planned_uah": planned,
        "remaining_uah": remaining,
        "over_budget_uah": max(0, -remaining),
        "utilization_percent": round((planned / amount) * 100, 1) if amount else 0.0,
        "within_budget": remaining >= 0,
        "reference_prices": list(REFERENCE_PRICES),
        "transport_estimates": TRANSPORT_ESTIMATES,
        "price_basis": PRICE_BASIS,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="reaper budget", description="Планировщик микробюджета в гривнах.")
    parser.add_argument("--amount", type=int, default=DEFAULT_AMOUNT, help="общий лимит в грн (0..1000000)")
    parser.add_argument("--scenario", choices=tuple(SCENARIOS), default="weekly")
    parser.add_argument("--set", action="append", default=[], metavar="CATEGORY=UAH",
                        help="переопределить food, transport, household, digital, leisure или reserve")
    parser.add_argument("--json", action="store_true", help="вывести полный план, оценки цен и тарифов в JSON")
    args = parser.parse_args(argv)
    overrides: dict[str, int] = {}
    try:
        for raw in args.set:
            key, separator, value = raw.partition("=")
            if not separator or not value:
                raise BudgetError(f"Ожидается CATEGORY=UAH, получено {raw!r}")
            if key in overrides:
                raise BudgetError(f"Категория указана повторно: {key}")
            try:
                overrides[key] = int(value)
            except ValueError as error:
                raise BudgetError(f"Сумма должна быть целым числом: {raw!r}") from error
        result = calculate_budget(args.amount, args.scenario, overrides)
    except BudgetError as error:
        parser.error(str(error))
    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print(f"{result['scenario_label']} · лимит {result['budget_uah']} грн")
        for row in result["allocations"]:
            print(f"  {row['label']:<24} {row['amount_uah']:>4} грн")
        print(f"Запланировано: {result['planned_uah']} грн")
        if result["within_budget"]:
            print(f"Остаток: {result['remaining_uah']} грн")
        else:
            print(f"Превышение: {result['over_budget_uah']} грн")
        print(f"Использовано: {result['utilization_percent']}%")
        print(PRICE_BASIS)
        print("Для JSON-деталей и справочника цен: reaper budget --json")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
