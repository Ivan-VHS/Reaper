"""Quality, structural cohesion and cadence diagnostics for Reaper pipelines.

This module audits declared stage sequences and externally supplied timing
samples. It does not execute source code or infer runtime measurements.
"""
from __future__ import annotations

import math
from collections import Counter
from collections.abc import Mapping, Sequence
from typing import Any

MAX_QMR_ITEMS = 100_000
MAX_PIPELINE_STAGES = 256


def _finite_number(value: Any, label: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise TypeError(f"{label} must be a real number")
    result = float(value)
    if not math.isfinite(result):
        raise ValueError(f"{label} must be finite")
    return result


def _intervals(values: Any) -> list[float]:
    if not isinstance(values, (list, tuple)) or not 2 <= len(values) <= MAX_QMR_ITEMS:
        raise ValueError(f"intervals must contain 2..{MAX_QMR_ITEMS} values")
    result = [_finite_number(value, f"intervals[{index}]") for index, value in enumerate(values)]
    if any(value <= 0.0 or value > 1e12 for value in result):
        raise ValueError("intervals must be positive and no greater than 1e12")
    return result


def analyze_cadence(
    intervals: Sequence[Any],
    expected_interval: Any,
    tolerance_ratio: Any = 0.1,
) -> dict[str, float | int | str]:
    """Score repeatability from interval spread, period bias and temporal drift."""
    values = _intervals(intervals)
    expected = _finite_number(expected_interval, "expected_interval")
    tolerance = _finite_number(tolerance_ratio, "tolerance_ratio")
    if not 1e-9 <= expected <= 1e12:
        raise ValueError("expected_interval must be within [1e-9, 1e12]")
    if not 0.0 < tolerance <= 1.0:
        raise ValueError("tolerance_ratio must be within (0, 1]")

    count = len(values)
    mean = math.fsum(values) / count
    variance = math.fsum((value - mean) ** 2 for value in values) / (count - 1)
    deviation = math.sqrt(variance)
    coefficient = deviation / mean
    bias = (mean - expected) / expected
    split = count // 2
    first_mean = math.fsum(values[:split]) / split
    second_mean = math.fsum(values[split:]) / (count - split)
    drift = (second_mean - first_mean) / expected
    penalty = coefficient + abs(bias) + 0.5 * abs(drift)
    if not all(math.isfinite(value) for value in (mean, variance, deviation, coefficient, bias, drift, penalty)):
        raise ValueError("cadence calculation exceeded the finite numeric range")
    score = 100.0 * (1.0 - min(1.0, penalty / tolerance))
    return {
        "schema": "reaper.qmr-cadence.v1",
        "sample_count": count,
        "expected_interval": expected,
        "mean_interval": mean,
        "sample_standard_deviation": deviation,
        "coefficient_of_variation": coefficient,
        "relative_bias": bias,
        "relative_drift": drift,
        "cadence_score": score,
    }


def audit_pipeline_cohesion(
    actual_stages: Sequence[str],
    expected_stages: Sequence[str],
) -> dict[str, Any]:
    """Audit an observed stage sequence against its declared pipeline contract."""
    for label, stages in (("actual_stages", actual_stages), ("expected_stages", expected_stages)):
        if not isinstance(stages, (list, tuple)) or not 1 <= len(stages) <= MAX_PIPELINE_STAGES:
            raise ValueError(f"{label} must contain 1..{MAX_PIPELINE_STAGES} stages")
        if any(not isinstance(stage, str) or not stage.strip() or len(stage) > 128 for stage in stages):
            raise ValueError(f"{label} must contain non-empty stage names of at most 128 characters")
    expected = list(expected_stages)
    actual = list(actual_stages)
    if len(set(expected)) != len(expected):
        raise ValueError("expected_stages must be unique")

    counts = Counter(actual)
    duplicates = sorted(stage for stage, count in counts.items() if count > 1)
    expected_set = set(expected)
    actual_set = set(actual)
    missing = [stage for stage in expected if stage not in actual_set]
    unexpected = [stage for stage in actual if stage not in expected_set]
    order = {stage: index for index, stage in enumerate(expected)}
    declared_positions = [order[stage] for stage in actual if stage in order]
    inversions = sum(
        1 for left_index in range(len(declared_positions))
        for right_index in range(left_index + 1, len(declared_positions))
        if declared_positions[left_index] > declared_positions[right_index]
    )

    penalty = 20 * len(missing) + 5 * len(unexpected) + 10 * len(duplicates) + 3 * inversions
    score = float(max(0, 100 - penalty))
    return {
        "schema": "reaper.qmr-cohesion.v1",
        "expected_stage_count": len(expected),
        "actual_stage_count": len(actual),
        "missing_stages": missing,
        "unexpected_stages": unexpected,
        "duplicate_stages": duplicates,
        "order_inversions": inversions,
        "cohesion_score": score,
        "cohesive": not (missing or unexpected or duplicates or inversions),
    }


def build_qmr_report(
    quality_checks: Mapping[str, bool],
    actual_stages: Sequence[str],
    expected_stages: Sequence[str],
    intervals: Sequence[Any],
    expected_interval: Any,
    tolerance_ratio: Any = 0.1,
) -> dict[str, Any]:
    """Combine explicit quality checks, pipeline cohesion and measured cadence."""
    if not isinstance(quality_checks, Mapping) or not quality_checks:
        raise ValueError("quality_checks must be a non-empty mapping")
    if len(quality_checks) > MAX_PIPELINE_STAGES:
        raise ValueError(f"quality_checks cannot exceed {MAX_PIPELINE_STAGES} entries")
    for name, passed in quality_checks.items():
        if not isinstance(name, str) or not name.strip() or len(name) > 128:
            raise ValueError("quality check names must be non-empty strings of at most 128 characters")
        if not isinstance(passed, bool):
            raise TypeError(f"quality_checks[{name!r}] must be boolean")

    quality_score = 100.0 * sum(quality_checks.values()) / len(quality_checks)
    cohesion = audit_pipeline_cohesion(actual_stages, expected_stages)
    cadence = analyze_cadence(intervals, expected_interval, tolerance_ratio)
    rhythm_score = float(cadence["cadence_score"])
    overall = (quality_score * float(cohesion["cohesion_score"]) * rhythm_score) ** (1.0 / 3.0)

    return {
        "schema": "reaper.qmr-report.v1",
        "quality": {
            "score": quality_score,
            "passed": [name for name, passed in quality_checks.items() if passed],
            "failed": [name for name, passed in quality_checks.items() if not passed],
            "check_count": len(quality_checks),
        },
        "cohesion": cohesion,
        "rhythm": cadence,
        "overall_score": overall,
        "semantics": (
            "Descriptive engineering diagnostics; caller supplies the checks, "
            "stage contract and timing observations. No source is executed."
        ),
    }
