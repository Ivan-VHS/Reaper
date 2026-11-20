"""Bounded numerical helpers for orthogonal and Pythagorean metric models."""
from __future__ import annotations

import math
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


def _finite_result(value: float, name: str) -> float:
    if not math.isfinite(value):
        raise ValueError(f"{name} overflowed")
    return value


def _finite_sum(values: Any, name: str) -> float:
    try:
        result = math.fsum(values)
    except (OverflowError, ValueError) as error:
        raise ValueError(f"{name} overflowed") from error
    return _finite_result(result, name)


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
    return _finite_sum((x * y for x, y in zip(a, b)), "dot product")


def vector_norm(values: Any) -> float:
    return _finite_result(math.hypot(*_vector(values)), "vector norm")


def euclidean_distance(left: Any, right: Any) -> float:
    a, b = _vector(left, "left vector"), _vector(right, "right vector")
    if len(a) != len(b):
        raise ValueError("vectors must have the same dimension")
    return _finite_result(math.hypot(*(x - y for x, y in zip(a, b))), "Euclidean distance")


def is_orthogonal(left: Any, right: Any, tolerance: Any = 1e-12) -> bool:
    a, b = _vector(left, "left vector"), _vector(right, "right vector")
    if len(a) != len(b):
        raise ValueError("vectors must have the same dimension")
    tol = _number(tolerance, "tolerance")
    if not 0.0 <= tol <= 1.0:
        raise ValueError("tolerance must be between 0 and 1")
    scale_a, scale_b = max(map(abs, a)), max(map(abs, b))
    if scale_a == 0.0 or scale_b == 0.0:
        return True
    scaled_a = [value / scale_a for value in a]
    scaled_b = [value / scale_b for value in b]
    na, nb = math.hypot(*scaled_a), math.hypot(*scaled_b)
    cosine = _finite_sum(
        ((x / na) * (y / nb) for x, y in zip(scaled_a, scaled_b)),
        "normalized dot product",
    )
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
    return _finite_sum(
        (
            vector[i] * rows[i][j] * vector[j]
            for i in range(len(vector))
            for j in range(len(vector))
        ),
        "quadratic form",
    )


def law_of_cosines(side_a: Any, side_b: Any, included_angle: Any) -> float:
    a, b = _number(side_a, "side_a"), _number(side_b, "side_b")
    angle = _number(included_angle, "included_angle")
    if a < 0.0 or b < 0.0:
        raise ValueError("side lengths cannot be negative")
    return _finite_result(math.hypot(a - b * math.cos(angle), b * math.sin(angle)), "law of cosines")


def de_gua_area(face_a: Any, face_b: Any, face_c: Any) -> float:
    a, b, c = (_number(face_a, "face_a"), _number(face_b, "face_b"),
               _number(face_c, "face_c"))
    if min(a, b, c) < 0.0:
        raise ValueError("face areas cannot be negative")
    return _finite_result(math.hypot(a, b, c), "de Gua area")


def parseval_energy(coefficients: Any) -> float:
    values = _vector(coefficients, "coefficients")
    return _finite_sum((value * value for value in values), "coefficient energy")


def unit_circle_residual(angle: Any) -> float:
    value = _number(angle, "angle")
    sine, cosine = math.sin(value), math.cos(value)
    return abs(_finite_sum((sine * sine, cosine * cosine, -1.0), "unit-circle residual"))


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
    return _finite_sum(
        (time_component * time_component, *(-value * value for value in coordinates)),
        "Minkowski interval",
    )


def combine_uncorrelated_variances(variances: Any) -> float:
    values = _vector(variances, "variances")
    if any(value < 0.0 for value in values):
        raise ValueError("variances cannot be negative")
    return _finite_sum(values, "combined variance")


def reciprocal_altitude(side_a: Any, side_b: Any) -> float:
    a, b = _number(side_a, "side_a"), _number(side_b, "side_b")
    if a <= 0.0 or b <= 0.0:
        raise ValueError("right-triangle side lengths must be positive")
    smaller, larger = sorted((a, b))
    return _finite_result(smaller / math.hypot(1.0, smaller / larger), "reciprocal altitude")
