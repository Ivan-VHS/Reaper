"""Bounded, domain-neutral algebraic and structural operations for Reaper.

These functions are pure: they do not access files, networks, clocks, processes,
devices, or other host capabilities. Runtime-facing work limits are supplied by
the interpreter.
"""
from __future__ import annotations

import math
from typing import Any

Number = int | float


def _number(value: Any, name: str = "value") -> Number:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise TypeError(f"{name} must be a number")
    if isinstance(value, float) and not math.isfinite(value):
        raise ValueError(f"{name} must be finite")
    return value


def _finite(value: Number, operation: str) -> Number:
    if isinstance(value, float) and not math.isfinite(value):
        raise ValueError(f"{operation} produced a non-finite result")
    return value


def _numeric_sequence(values: Any, name: str = "values") -> list[Number]:
    if not isinstance(values, (list, tuple, range)):
        raise TypeError(f"{name} must be a list or range")
    return [_number(value, f"{name} item") for value in values]


def opposite(value: Any) -> Number:
    return -_number(value)


def multiply(left: Any, right: Any) -> Number:
    return _finite(_number(left, "left") * _number(right, "right"), "multiply()")


def divide(left: Any, right: Any) -> Number:
    numerator = _number(left, "left")
    denominator = _number(right, "right")
    if denominator == 0:
        raise ValueError("division by zero")
    return _finite(numerator / denominator, "divide()")


def power(base: Any, exponent: Any) -> Number:
    base_value = _number(base, "base")
    exponent_value = _number(exponent, "exponent")
    try:
        result = base_value ** exponent_value
    except (ArithmeticError, ValueError, TypeError) as error:
        raise ValueError(f"power() failed: {error}") from error
    if isinstance(result, complex):
        raise ValueError("power() must produce a real number")
    return _finite(result, "power()")


def root(value: Any, degree: Any = 2) -> Number:
    number = _number(value)
    index = _number(degree, "degree")
    if index <= 0:
        raise ValueError("degree must be greater than zero")
    if number < 0:
        if not isinstance(index, int) or index % 2 == 0:
            raise ValueError("a negative value requires a positive odd whole-number degree")
        return _finite(-((-number) ** (1 / index)), "root()")
    return _finite(number ** (1 / index), "root()")


def logarithm(value: Any, base: Any = math.e) -> Number:
    number = _number(value)
    radix = _number(base, "base")
    if number <= 0:
        raise ValueError("logarithm value must be greater than zero")
    if radix <= 0 or radix == 1:
        raise ValueError("logarithm base must be positive and not equal to one")
    return _finite(math.log(number, radix), "logarithm()")


def exponential(value: Any, base: Any = math.e) -> Number:
    exponent = _number(value)
    radix = _number(base, "base")
    if radix <= 0:
        raise ValueError("exponential base must be greater than zero")
    try:
        return _finite(math.pow(radix, exponent), "exponential()")
    except OverflowError as error:
        raise ValueError("exponential() result exceeds the numeric range") from error


def replicate(value: Any, count: Any, max_items: int) -> list[Any]:
    if isinstance(count, bool) or not isinstance(count, int):
        raise TypeError("count must be a whole number")
    if count < 0:
        raise ValueError("count cannot be negative")
    if count > max_items:
        raise ValueError(f"collection item limit ({max_items}) exceeded")
    return [value for _ in range(count)]


def reverse(values: Any) -> list[Any] | str:
    if isinstance(values, str):
        return values[::-1]
    if not isinstance(values, (list, tuple, range)):
        raise TypeError("reverse() expects a list, text, or range")
    return list(reversed(values))


def scale(values: Any, factor: Any) -> list[Number]:
    items = _numeric_sequence(values)
    multiplier = _number(factor, "factor")
    return [_finite(item * multiplier, "scale()") for item in items]


def dot(left: Any, right: Any) -> Number:
    a = _numeric_sequence(left, "left vector")
    b = _numeric_sequence(right, "right vector")
    if len(a) != len(b):
        raise ValueError("vectors must have the same length")
    return _finite(sum(x * y for x, y in zip(a, b)), "dot()")


def distance(left: Any, right: Any) -> float:
    a = _numeric_sequence(left, "left vector")
    b = _numeric_sequence(right, "right vector")
    if len(a) != len(b):
        raise ValueError("vectors must have the same length")
    return _finite(math.hypot(*(x - y for x, y in zip(a, b))), "distance()")


def differentiate(values: Any, step: Any = 1) -> list[Number]:
    samples = _numeric_sequence(values, "samples")
    interval = _number(step, "step")
    if interval == 0:
        raise ValueError("step cannot be zero")
    if len(samples) < 2:
        raise ValueError("differentiate() needs at least two samples")
    return [
        _finite((right - left) / interval, "differentiate()")
        for left, right in zip(samples, samples[1:])
    ]


def integrate(values: Any, step: Any = 1) -> list[Number]:
    """Return cumulative trapezoidal integrals, beginning at zero."""
    samples = _numeric_sequence(values, "samples")
    interval = _number(step, "step")
    if interval == 0:
        raise ValueError("step cannot be zero")
    if not samples:
        return []
    result: list[Number] = [0]
    total: Number = 0
    for left, right in zip(samples, samples[1:]):
        total = _finite(total + ((left + right) * interval / 2), "integrate()")
        result.append(total)
    return result


def accumulate(values: Any, initial: Any = 0) -> list[Number]:
    items = _numeric_sequence(values)
    total = _number(initial, "initial")
    result: list[Number] = []
    for item in items:
        total = _finite(total + item, "accumulate()")
        result.append(total)
    return result


def differences(values: Any) -> list[Number]:
    items = _numeric_sequence(values)
    return [
        _finite(right - left, "differences()")
        for left, right in zip(items, items[1:])
    ]


def quantize(value: Any, step: Any = 1) -> Number:
    number = _number(value)
    quantum = _number(step, "step")
    if quantum <= 0:
        raise ValueError("step must be greater than zero")
    return _finite(round(number / quantum) * quantum, "quantize()")


def normalize(values: Any, mode: Any = "minmax") -> list[float]:
    items = [float(item) for item in _numeric_sequence(values)]
    if not isinstance(mode, str):
        raise TypeError("mode must be text")
    if mode == "minmax":
        if not items:
            return []
        low, high = min(items), max(items)
        span = high - low
        return [0.0 for _ in items] if span == 0 else [(item - low) / span for item in items]
    if mode == "unit":
        norm = math.hypot(*items)
        return [0.0 for _ in items] if norm == 0 else [item / norm for item in items]
    raise ValueError("mode must be 'minmax' or 'unit'")


def factorize(value: Any, max_divisions: int = 1_000_000) -> list[int]:
    if isinstance(value, bool) or not isinstance(value, int):
        raise TypeError("factorize() expects a whole number")
    if value < 1:
        raise ValueError("factorize() expects a positive integer")
    remaining = value
    factors: list[int] = []
    divisions = 0
    for divisor in (2, 3):
        while remaining % divisor == 0:
            factors.append(divisor)
            remaining //= divisor
    divisor = 5
    increment = 2
    while divisor * divisor <= remaining:
        divisions += 1
        if divisions > max_divisions:
            raise ValueError("factorize() work limit exceeded")
        if remaining % divisor == 0:
            factors.append(divisor)
            remaining //= divisor
        else:
            divisor += increment
            increment = 6 - increment
    if remaining > 1:
        factors.append(remaining)
    return factors


def flatten(values: Any, max_items: int) -> list[Any]:
    if not isinstance(values, (list, tuple)):
        raise TypeError("flatten() expects a nested list")
    result: list[Any] = []
    stack = list(reversed(values))
    while stack:
        item = stack.pop()
        if isinstance(item, (list, tuple)):
            stack.extend(reversed(item))
        else:
            result.append(item)
            if len(result) > max_items:
                raise ValueError(f"collection item limit ({max_items}) exceeded")
    return result


def transpose(matrix: Any, max_items: int) -> list[list[Any]]:
    if not isinstance(matrix, (list, tuple)):
        raise TypeError("transpose() expects a matrix")
    if not matrix:
        return []
    if any(not isinstance(row, (list, tuple)) for row in matrix):
        raise TypeError("matrix rows must be lists")
    columns = len(matrix[0])
    if any(len(row) != columns for row in matrix):
        raise ValueError("matrix must be rectangular")
    if len(matrix) * columns > max_items:
        raise ValueError(f"collection item limit ({max_items}) exceeded")
    return [[row[column] for row in matrix] for column in range(columns)]


def matrix_multiply(left: Any, right: Any, max_items: int, max_operations: int) -> list[list[Number]]:
    if not isinstance(left, (list, tuple)) or not isinstance(right, (list, tuple)):
        raise TypeError("matrix_multiply() expects two matrices")
    if not left or not right:
        raise ValueError("matrices cannot be empty")
    if any(not isinstance(row, (list, tuple)) for row in (*left, *right)):
        raise TypeError("matrix rows must be lists")
    left_columns = len(left[0])
    right_columns = len(right[0])
    if left_columns == 0 or right_columns == 0:
        raise ValueError("matrices cannot have empty rows")
    if any(len(row) != left_columns for row in left) or any(len(row) != right_columns for row in right):
        raise ValueError("matrices must be rectangular")
    if left_columns != len(right):
        raise ValueError("left matrix columns must match right matrix rows")
    output_cells = len(left) * right_columns
    operations = output_cells * left_columns
    if output_cells > max_items:
        raise ValueError(f"collection item limit ({max_items}) exceeded")
    if operations > max_operations:
        raise ValueError(f"matrix operation limit ({max_operations}) exceeded")
    a = [[_number(value, "matrix item") for value in row] for row in left]
    b = [[_number(value, "matrix item") for value in row] for row in right]
    result: list[list[Number]] = []
    for row in a:
        output_row: list[Number] = []
        for column in range(right_columns):
            total = sum(row[index] * b[index][column] for index in range(left_columns))
            output_row.append(_finite(total, "matrix_multiply()"))
        result.append(output_row)
    return result


def unique(values: Any, max_items: int) -> list[Any]:
    if not isinstance(values, (list, tuple, range, str)):
        raise TypeError("unique() expects a list, text, or range")
    if len(values) > max_items:
        raise ValueError(f"collection item limit ({max_items}) exceeded")
    seen: set[tuple[type, Any]] = set()
    result: list[Any] = []
    for item in values:
        if item is not None and not isinstance(item, (bool, int, float, str)):
            raise TypeError("unique() supports only scalar values")
        key = (type(item), item)
        if key not in seen:
            seen.add(key)
            result.append(item)
    return result


def cartesian(left: Any, right: Any, max_items: int) -> list[list[Any]]:
    if not isinstance(left, (list, tuple, range, str)) or not isinstance(right, (list, tuple, range, str)):
        raise TypeError("cartesian() expects two sequences")
    size = len(left) * len(right)
    if size > max_items:
        raise ValueError(f"collection item limit ({max_items}) exceeded")
    return [[a, b] for a in left for b in right]


def proliferate(choices: Any, max_items: int) -> list[list[Any]]:
    if not isinstance(choices, (list, tuple)):
        raise TypeError("proliferate() expects a list of choice sequences")
    sequences: list[list[Any]] = []
    total = 1
    for choice in choices:
        if not isinstance(choice, (list, tuple, range, str)):
            raise TypeError("each choice must be a sequence")
        values = list(choice)
        total *= len(values)
        if total > max_items:
            raise ValueError(f"collection item limit ({max_items}) exceeded")
        sequences.append(values)
    result: list[list[Any]] = [[]]
    for values in sequences:
        result = [prefix + [value] for prefix in result for value in values]
    return result
