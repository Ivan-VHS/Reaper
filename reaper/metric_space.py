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


def vector_norm(values: Any, kind: Any = "l2") -> float:
    vector = _vector(values)
    if kind == "l1":
        return _finite_sum((abs(value) for value in vector), "L1 norm")
    if kind in ("linf", "infinity", "max"):
        return _finite_result(max(map(abs, vector)), "L-infinity norm")
    if kind in ("l2", "euclidean"):
        return _finite_result(math.hypot(*vector), "L2 norm")
    raise ValueError("norm kind must be 'l1', 'l2', or 'linf'")


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



def normalize(values: Any) -> list[float]:
    vector = _vector(values)
    length = math.hypot(*vector)
    if length == 0.0:
        raise ValueError("cannot normalize a zero vector")
    return [_finite_result(value / length, "normalized component") for value in vector]


def _matching_vectors(left: Any, right: Any) -> tuple[list[float], list[float]]:
    a, b = _vector(left, "left vector"), _vector(right, "right vector")
    if len(a) != len(b):
        raise ValueError("vectors must have the same dimension")
    return a, b


def manhattan_distance(left: Any, right: Any) -> float:
    a, b = _matching_vectors(left, right)
    return _finite_sum((abs(x - y) for x, y in zip(a, b)), "Manhattan distance")


def chebyshev_distance(left: Any, right: Any) -> float:
    a, b = _matching_vectors(left, right)
    return _finite_result(max(abs(x - y) for x, y in zip(a, b)), "Chebyshev distance")


def squared_euclidean_distance(left: Any, right: Any) -> float:
    a, b = _matching_vectors(left, right)
    return _finite_sum(((x - y) * (x - y) for x, y in zip(a, b)), "squared Euclidean distance")


def cosine_similarity(left: Any, right: Any) -> float:
    a, b = _matching_vectors(left, right)
    scale_a, scale_b = max(map(abs, a)), max(map(abs, b))
    if scale_a == 0.0 or scale_b == 0.0:
        raise ValueError("cosine similarity is undefined for a zero vector")
    scaled_a = [value / scale_a for value in a]
    scaled_b = [value / scale_b for value in b]
    norm_a, norm_b = math.hypot(*scaled_a), math.hypot(*scaled_b)
    value = _finite_sum(
        ((x / norm_a) * (y / norm_b) for x, y in zip(scaled_a, scaled_b)),
        "cosine similarity",
    )
    return max(-1.0, min(1.0, value))


def angle_between(left: Any, right: Any) -> float:
    return math.acos(cosine_similarity(left, right))


def project(vector: Any, onto: Any) -> list[float]:
    values, basis = _matching_vectors(vector, onto)
    scale = max(map(abs, basis))
    if scale == 0.0:
        raise ValueError("cannot project onto a zero vector")
    scaled_basis = [value / scale for value in basis]
    denominator = _finite_sum((value * value for value in scaled_basis), "projection denominator")
    numerator = _finite_sum(
        (value * component for value, component in zip(values, scaled_basis)),
        "projection numerator",
    )
    factor = numerator / denominator
    return [
        _finite_result(factor * component, "projection component")
        for component in scaled_basis
    ]


def centroid(vectors: Any) -> list[float]:
    if not isinstance(vectors, (list, tuple)) or not vectors:
        raise ValueError("centroid expects a non-empty list of vectors")
    if len(vectors) > MAX_DIMENSION:
        raise ValueError(f"centroid accepts at most {MAX_DIMENSION} vectors")
    rows = [_vector(row, f"vector {index}") for index, row in enumerate(vectors)]
    dimension = len(rows[0])
    if any(len(row) != dimension for row in rows):
        raise ValueError("all vectors must have the same dimension")
    count = len(rows)
    return [
        _finite_result(_finite_sum((row[column] for row in rows), "centroid sum") / count,
                       "centroid component")
        for column in range(dimension)
    ]
