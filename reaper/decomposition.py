"""Exact arithmetic, Euclidean division, and deterministic decomposition utilities.

These helpers are a library API, not implicit language built-ins. They never
mutate input collections and make allocation/distribution decisions explicit.
"""
from __future__ import annotations

from dataclasses import dataclass
from fractions import Fraction
from math import isfinite
from typing import Iterable, Sequence, TypeVar

T = TypeVar("T")


@dataclass(frozen=True, slots=True)
class DivisionResult:
    dividend: int
    divisor: int
    quotient: int
    remainder: int

    @property
    def exact(self) -> bool:
        return self.remainder == 0

    def verify(self) -> bool:
        return self.dividend == self.quotient * self.divisor + self.remainder


def euclidean_divmod(dividend: int, divisor: int) -> DivisionResult:
    """Return q, r with dividend == q*divisor+r and 0 <= r < abs(divisor)."""
    if isinstance(dividend, bool) or not isinstance(dividend, int):
        raise TypeError("dividend must be an integer")
    if isinstance(divisor, bool) or not isinstance(divisor, int):
        raise TypeError("divisor must be an integer")
    if divisor == 0:
        raise ZeroDivisionError("division by zero")
    q_abs, remainder = divmod(dividend, abs(divisor))
    quotient = q_abs if divisor > 0 else -q_abs
    result = DivisionResult(dividend, divisor, quotient, remainder)
    assert result.verify()
    return result


def divide_fraction(dividend: int | Fraction, divisor: int | Fraction) -> Fraction:
    """Perform exact rational division without a floating-point conversion."""
    left, right = Fraction(dividend), Fraction(divisor)
    if right == 0:
        raise ZeroDivisionError("division by zero")
    return left / right


def split_evenly(total: int, parts: int) -> tuple[int, ...]:
    """Split an integer total; earlier buckets receive indivisible remainder."""
    if isinstance(total, bool) or not isinstance(total, int):
        raise TypeError("total must be an integer")
    if isinstance(parts, bool) or not isinstance(parts, int):
        raise TypeError("parts must be an integer")
    if parts <= 0:
        raise ValueError("parts must be positive")
    sign = -1 if total < 0 else 1
    base, remainder = divmod(abs(total), parts)
    return tuple(sign * (base + (1 if i < remainder else 0)) for i in range(parts))


def distribute_weighted(total: int, weights: Sequence[int | float | Fraction]) -> tuple[int, ...]:
    """Allocate an integer total by non-negative weights using largest remainders.

    Ties are stable: the lower input index receives the remaining unit first.
    """
    if isinstance(total, bool) or not isinstance(total, int):
        raise TypeError("total must be an integer")
    if not weights:
        raise ValueError("at least one weight is required")
    normalized: list[Fraction] = []
    for weight in weights:
        if isinstance(weight, bool):
            raise TypeError("weights must be numeric, not boolean")
        if isinstance(weight, float) and not isfinite(weight):
            raise ValueError("weights must be finite")
        value = Fraction(str(weight)) if isinstance(weight, float) else Fraction(weight)
        if value < 0:
            raise ValueError("weights must be non-negative")
        normalized.append(value)
    weight_sum = sum(normalized, Fraction())
    if weight_sum == 0:
        raise ValueError("at least one weight must be positive")
    sign = -1 if total < 0 else 1
    magnitude = abs(total)
    exact = [Fraction(magnitude) * weight / weight_sum for weight in normalized]
    allocated = [value.numerator // value.denominator for value in exact]
    remainder = magnitude - sum(allocated)
    order = sorted(range(len(exact)), key=lambda i: (-(exact[i] - allocated[i]), i))
    for index in order[:remainder]:
        allocated[index] += 1
    return tuple(sign * value for value in allocated)


def decompose_sequence(items: Iterable[T], chunk_size: int) -> tuple[tuple[T, ...], ...]:
    """Partition an iterable into ordered, bounded, non-empty chunks."""
    if isinstance(chunk_size, bool) or not isinstance(chunk_size, int):
        raise TypeError("chunk_size must be an integer")
    if chunk_size <= 0:
        raise ValueError("chunk_size must be positive")
    values = tuple(items)
    return tuple(values[i:i + chunk_size] for i in range(0, len(values), chunk_size))


def recombine(parts: Iterable[Iterable[T]]) -> tuple[T, ...]:
    """Recombine ordered partitions without changing element order."""
    return tuple(item for part in parts for item in part)


def factor_pairs(number: int) -> tuple[tuple[int, int], ...]:
    """Return positive factor pairs in ascending first-factor order."""
    if isinstance(number, bool) or not isinstance(number, int):
        raise TypeError("number must be an integer")
    if number <= 0:
        raise ValueError("number must be positive")
    pairs = []
    candidate = 1
    while candidate * candidate <= number:
        if number % candidate == 0:
            pairs.append((candidate, number // candidate))
        candidate += 1
    return tuple(pairs)
