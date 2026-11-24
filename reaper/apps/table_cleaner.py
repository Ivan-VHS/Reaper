"""Normalize catalog rows with exact decimal handling and stable SKU deduplication."""
from __future__ import annotations

from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
import re
from typing import Any

from .common import ApplicationInputError, require_array, require_object, require_text


def _price(value: Any, label: str) -> str:
    if isinstance(value, bool) or value is None:
        raise ApplicationInputError(f"{label} must be a decimal amount")
    raw = str(value).strip().replace(",", ".")
    try:
        amount = Decimal(raw)
    except InvalidOperation as error:
        raise ApplicationInputError(f"{label} is not a valid decimal amount") from error
    if not amount.is_finite() or amount <= 0:
        raise ApplicationInputError(f"{label} must be finite and greater than zero")
    if amount > Decimal("1000000000000"):
        raise ApplicationInputError(f"{label} exceeds the supported 1e12 limit")
    try:
        return format(amount.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP), "f")
    except InvalidOperation as error:
        raise ApplicationInputError(f"{label} cannot be represented with two decimal places") from error


def run(payload: dict[str, Any]) -> dict[str, Any]:
    rows = require_array(payload, "rows")
    result: list[dict[str, Any]] = []
    seen: set[str] = set()
    rejected: list[dict[str, Any]] = []
    duplicates = 0

    for index, item in enumerate(rows):
        try:
            row = require_object(item, f"rows[{index}]")
            sku = require_text(row.get("sku"), f"rows[{index}].sku").strip().upper()
            price = _price(row.get("price"), f"rows[{index}].price")
            quantity_raw = row.get("qty")
            if isinstance(quantity_raw, str) and re.fullmatch(r"[+-]?\d+", quantity_raw.strip()):
                quantity_raw = int(quantity_raw.strip())
            if isinstance(quantity_raw, bool) or not isinstance(quantity_raw, int):
                raise ApplicationInputError(f"rows[{index}].qty must be a whole number")
            quantity = max(0, quantity_raw)
            currency = require_text(row.get("currency", "USD"), f"rows[{index}].currency").strip().upper()
            if len(currency) != 3 or not currency.isalpha():
                raise ApplicationInputError(f"rows[{index}].currency must be a 3-letter code")
            if sku in seen:
                duplicates += 1
                continue
            seen.add(sku)
            result.append({"sku": sku, "price": price, "qty": quantity, "currency": currency})
        except (TypeError, ValueError) as error:
            rejected.append({"index": index, "reason": str(error)})

    result.sort(key=lambda row: row["sku"])
    return {
        "rows": result,
        "rejected": rejected,
        "counts": {"received": len(rows), "accepted": len(result), "duplicates": duplicates, "rejected": len(rejected)},
        "price_representation": "decimal_string_2dp",
    }
