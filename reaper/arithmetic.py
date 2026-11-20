"""Bounded numeric and sequence operations used by the Reaper runtime."""

from __future__ import annotations

import math
from collections.abc import Sequence
from typing import Any

MAX_ITEMS = 100_000
MAX_INTEGER_BITS = 4096
MAX_FACTOR_INPUT = 1_000_000_000_000


def _number(value: Any, label: str = "value") -> int | float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise TypeError(f"{label} must be a real number")
    if isinstance(value, float) and not math.isfinite(value):
        raise ValueError(f"{label} must be finite")
    return value


def _checked(value: Any, label: str = "result") -> int | float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise TypeError(f"{label} must be a real number")
    if isinstance(value, int):
        if value.bit_length() > MAX_INTEGER_BITS:
            raise ValueError(f"{label} exceeds the {MAX_INTEGER_BITS}-bit integer limit")
    elif not math.isfinite(value):
        raise ValueError(f"{label} is not finite")
    return value


def _sequence(values: Any, label: str = "values") -> Sequence[Any]:
    if not isinstance(values, (list, tuple, range)):
        raise TypeError(f"{label} must be a list, tuple, or range")
    if len(values) > MAX_ITEMS:
        raise ValueError(f"{label} exceeds the {MAX_ITEMS}-item limit")
    return values


def multiply(left: Any, right: Any) -> int | float:
    return _checked(_number(left, "left") * _number(right, "right"))


def product(values: Any) -> int | float:
    items = _sequence(values)
    result: int | float = 1
    for index, item in enumerate(items):
        result = _checked(result * _number(item, f"values[{index}]"))
    return result


def compute(left: Any, right: Any, operation: Any = "multiply") -> int | float:
    a, b = _number(left, "left"), _number(right, "right")
    if not isinstance(operation, str):
        raise TypeError("operation must be text")
    if operation == "divide" and b == 0:
        raise ValueError("division by zero")
    operations = {
        "add": lambda: a + b,
        "subtract": lambda: a - b,
        "multiply": lambda: a * b,
        "divide": lambda: a / b,
        "power": lambda: math.pow(a, b),
    }
    if operation not in operations:
        raise ValueError("operation must be add, subtract, multiply, divide, or power")
    return _checked(operations[operation]())


def scale(values: Any, factor: Any) -> list[int | float]:
    items = _sequence(values)
    multiplier = _number(factor, "factor")
    return [_checked(_number(item, f"values[{i}]") * multiplier) for i, item in enumerate(items)]


def amplify(value: Any, factor: Any) -> int | float:
    return multiply(value, factor)


def compound(left: Any, right: Any) -> list[int | float]:
    a, b = _sequence(left, "left"), _sequence(right, "right")
    if len(a) != len(b):
        raise ValueError("compound vectors must have equal lengths")
    return [
        _checked(_number(x, f"left[{i}]") * _number(y, f"right[{i}]"))
        for i, (x, y) in enumerate(zip(a, b))
    ]


def expand(values: Any, repetitions: Any) -> list[Any]:
    items = _sequence(values)
    if isinstance(repetitions, bool) or not isinstance(repetitions, int) or repetitions < 0:
        raise ValueError("repetitions must be a non-negative whole number")
    if len(items) * repetitions > MAX_ITEMS:
        raise ValueError(f"expanded sequence exceeds the {MAX_ITEMS}-item limit")
    return list(items) * repetitions


def accumulate(values: Any) -> list[int | float]:
    items = _sequence(values)
    total: int | float = 0
    result: list[int | float] = []
    for index, item in enumerate(items):
        total = _checked(total + _number(item, f"values[{index}]"))
        result.append(total)
    return result


def cross_multiply(left: Any, right: Any) -> list[list[int | float]]:
    a, b = _sequence(left, "left"), _sequence(right, "right")
    if len(a) * len(b) > MAX_ITEMS:
        raise ValueError(f"outer product exceeds the {MAX_ITEMS}-item limit")
    right_values = [_number(item, f"right[{i}]") for i, item in enumerate(b)]
    return [
        [_checked(_number(value, f"left[{i}]") * other) for other in right_values]
        for i, value in enumerate(a)
    ]


def exponentiate(base: Any, exponent: Any) -> int | float:
    a, b = _number(base, "base"), _number(exponent, "exponent")
    return _checked(math.pow(a, b))


def factor(value: Any) -> list[int]:
    number = _number(value, "value")
    if isinstance(number, float) and not number.is_integer():
        raise ValueError("factor() expects a whole number")
    integer = int(number)
    if integer < 1 or integer > MAX_FACTOR_INPUT:
        raise ValueError(f"value must be between 1 and {MAX_FACTOR_INPUT}")
    remaining = integer
    result: list[int] = []
    divisor = 2
    while divisor <= remaining // divisor:
        while remaining % divisor == 0:
            result.append(divisor)
            remaining //= divisor
        divisor = 3 if divisor == 2 else divisor + 2
    if remaining > 1:
        result.append(remaining)
    return result


def combine(left: Any, right: Any) -> list[int | float]:
    a, b = _sequence(left, "left"), _sequence(right, "right")
    if len(a) != len(b):
        raise ValueError("combine vectors must have equal lengths")
    return [
        _checked(_number(x, f"left[{i}]") + _number(y, f"right[{i}]"))
        for i, (x, y) in enumerate(zip(a, b))
    ]


def fuse(left: Any, right: Any) -> list[Any]:
    a, b = _sequence(left, "left"), _sequence(right, "right")
    if len(a) + len(b) > MAX_ITEMS:
        raise ValueError(f"fused sequence exceeds the {MAX_ITEMS}-item limit")
    return [*a, *b]


def aggregate(values: Any) -> dict[str, int | float]:
    items = _sequence(values)
    if not items:
        raise ValueError("aggregate() expects at least one value")
    numbers = [_number(item, f"values[{i}]") for i, item in enumerate(items)]
    total = _checked(sum(numbers))
    multiplied = product(numbers)
    return {
        "count": len(numbers),
        "sum": total,
        "product": multiplied,
        "mean": total / len(numbers),
        "minimum": min(numbers),
        "maximum": max(numbers),
    }


def pair(left: Any, right: Any) -> list[Any]:
    return [left, right]


def couple(left: Any, right: Any) -> list[list[Any]]:
    a, b = _sequence(left, "left"), _sequence(right, "right")
    if len(a) != len(b):
        raise ValueError("couple() expects sequences of equal length")
    return [[x, y] for x, y in zip(a, b)]


def convolve(signal: Any, kernel: Any) -> list[int | float]:
    values = [_number(x, f"signal[{i}]") for i, x in enumerate(_sequence(signal, "signal"))]
    weights = [_number(x, f"kernel[{i}]") for i, x in enumerate(_sequence(kernel, "kernel"))]
    if not values or not weights:
        raise ValueError("convolve() expects two non-empty sequences")
    size = len(values) + len(weights) - 1
    if size > MAX_ITEMS:
        raise ValueError(f"convolution exceeds the {MAX_ITEMS}-item limit")
    result: list[int | float] = []
    for index in range(size):
        terms = [
            values[i] * weights[index - i]
            for i in range(max(0, index - len(weights) + 1), min(index, len(values) - 1) + 1)
        ]
        result.append(_checked(math.fsum(terms)))
    return result


def cartesianize(left: Any, right: Any) -> list[list[Any]]:
    a, b = _sequence(left, "left"), _sequence(right, "right")
    if len(a) * len(b) > MAX_ITEMS:
        raise ValueError(f"Cartesian product exceeds the {MAX_ITEMS}-pair limit")
    return [[x, y] for x in a for y in b]
