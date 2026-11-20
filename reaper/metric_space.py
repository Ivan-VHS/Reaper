"""Bounded numerical helpers for orthogonal and Pythagorean metric models."""
from __future__ import annotations

import math
from collections.abc import Sequence
from typing import Any

MAX_DIMENSION = 4096
MAX_MATRIX_DIMENSION = 512


def _number(value: Any, name: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise TypeError(f"{name} must be a real number")
    result = float(value)
    if not math.isfinite(result):
        raise ValueError(f"{name} must be finite")
    return result


def _vector(values: Any, name: str = "vector") -> list[float]:
    if not isinstance(values, (list, tuple)):
        raise TypeError(f"{name} must be a list")
    if not values or len(values) > MAX_DIMENSION:
        raise ValueError(f"{name} must contain 1..{MAX_DIMENSION} values")
    return [_number(value, f"{name}[{index}]") for index, value in enumerate(values)]


def dot(left: Any, right: Any) -> float:
    a, b = _vector(left, "left vector"), _vector(right, "right vector")
    if len(a) != len(b):
        raise ValueError("vectors must have the same dimension")
    result = math.fsum(x * y for x, y in zip(a, b))
    if not math.isfinite(result):
        raise ValueError("dot product overflowed")
    return result


def vector_norm(values: Any) -> float:
    return math.hypot(*_vector(values))


def euclidean_distance(left: Any, right: Any) -> float:
    a, b = _vector(left, "left vector"), _vector(right, "right vector")
    if len(a) != len(b):
        raise ValueError("vectors must have the same dimension")
    return math.hypot(*(x - y for x, y in zip(a, b)))


def is_orthogonal(left: Any, right: Any, tolerance: Any = 1e-12) -> bool:
    a, b = _vector(left, "left vector"), _vector(right, "right vector")
    if len(a) != len(b):
        raise ValueError("vectors must have the same dimension")
    tol = _number(tolerance, "tolerance")
    if not 0.0 <= tol <= 1.0:
        raise ValueError("tolerance must be between 0 and 1")
    na, nb = math.hypot(*a), math.hypot(*b)
    if na == 0.0 or nb == 0.0:
        return True
    cosine = math.fsum((x / na) * (y / nb) for x, y in zip(a, b))
    return abs(cosine) <= tol


def quadratic_form(values: Any, matrix: Any) -> float:
    vector = _vector(values)
    if not isinstance(matrix, (list, tuple)) or len(matrix) != len(vector):
        raise ValueError("matrix must be square and match the vector dimension")
    if len(vector) > MAX_MATRIX_DIMENSION:
        raise ValueError(f"matrix dimension exceeds {MAX_MATRIX_DIMENSION}")
    rows = [_vector(row, f"matrix row {index}") for index, row in enumerate(matrix)]
    if any(len(row) != len(vector) for row in rows):
        raise ValueError("matrix must be square and match the vector dimension")
    result = math.fsum(
        vector[i] * rows[i][j] * vector[j]
        for i in range(len(vector))
        for j in range(len(vector))
    )
    if not math.isfinite(result):
        raise ValueError("quadratic form overflowed")
    return result


def law_of_cosines(side_a: Any, side_b: Any, included_angle: Any) -> float:
    a, b = _number(side_a, "side_a"), _number(side_b, "side_b")
    angle = _number(included_angle, "included_angle")
    if a < 0.0 or b < 0.0:
        raise ValueError("side lengths cannot be negative")
    return math.hypot(a - b * math.cos(angle), b * math.sin(angle))


def de_gua_area(face_a: Any, face_b: Any, face_c: Any) -> float:
    a, b, c = (_number(face_a, "face_a"), _number(face_b, "face_b"),
               _number(face_c, "face_c"))
    if min(a, b, c) < 0.0:
        raise ValueError("face areas cannot be negative")
    return math.hypot(a, b, c)


def parseval_energy(coefficients: Any) -> float:
    values = _vector(coefficients, "coefficients")
    result = math.fsum(value * value for value in values)
    if not math.isfinite(result):
        raise ValueError("coefficient energy overflowed")
    return result


def unit_circle_residual(angle: Any) -> float:
    value = _number(angle, "angle")
    sine, cosine = math.sin(value), math.cos(value)
    return abs(math.fsum((sine * sine, cosine * cosine, -1.0)))


def spherical_hypotenuse(side_a: Any, side_b: Any) -> float:
    a, b = _number(side_a, "side_a"), _number(side_b, "side_b")
    if not 0.0 <= a <= math.pi / 2 or not 0.0 <= b <= math.pi / 2:
        raise ValueError("spherical right-triangle sides must be in [0, pi/2] radians")
    return math.acos(max(-1.0, min(1.0, math.cos(a) * math.cos(b))))


def hyperbolic_hypotenuse(side_a: Any, side_b: Any) -> float:
    a, b = _number(side_a, "side_a"), _number(side_b, "side_b")
    if a < 0.0 or b < 0.0:
        raise ValueError("hyperbolic side lengths cannot be negative")
    try:
        return math.acosh(math.cosh(a) * math.cosh(b))
    except (OverflowError, ValueError) as error:
        raise ValueError("hyperbolic result is outside the finite numeric range") from error


def minkowski_interval(ct: Any, spatial: Any) -> float:
    time_component = _number(ct, "ct")
    coordinates = _vector(spatial, "spatial coordinates")
    result = math.fsum((time_component * time_component,
                        *(-value * value for value in coordinates)))
    if not math.isfinite(result):
        raise ValueError("Minkowski interval overflowed")
    return result


def combine_uncorrelated_variances(variances: Any) -> float:
    values = _vector(variances, "variances")
    if any(value < 0.0 for value in values):
        raise ValueError("variances cannot be negative")
    result = math.fsum(values)
    if not math.isfinite(result):
        raise ValueError("combined variance overflowed")
    return result


def reciprocal_altitude(side_a: Any, side_b: Any) -> float:
    a, b = _number(side_a, "side_a"), _number(side_b, "side_b")
    if a <= 0.0 or b <= 0.0:
        raise ValueError("right-triangle side lengths must be positive")
    smaller, larger = sorted((a, b))
    return smaller / math.hypot(1.0, smaller / larger)
