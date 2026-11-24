"""Summarize non-negative latency samples with nearest-rank percentiles."""
from __future__ import annotations

import math
from typing import Any

from .common import ApplicationInputError, require_array, require_number


def _nearest_rank(values: list[float], q: float) -> float:
    return values[max(0, math.ceil(q * len(values)) - 1)]


def run(payload: dict[str, Any]) -> dict[str, Any]:
    raw = require_array(payload, "samples_ms")
    samples: list[float] = []
    rejected = 0
    for index, value in enumerate(raw):
        try:
            samples.append(require_number(value, f"samples_ms[{index}]", minimum=0.0))
        except ApplicationInputError:
            rejected += 1
    if not samples:
        raise ApplicationInputError("empty_samples")
    samples.sort()
    return {
        "count": len(samples),
        "rejected": rejected,
        "min_ms": samples[0],
        "p50_ms": _nearest_rank(samples, 0.50),
        "p95_ms": _nearest_rank(samples, 0.95),
        "p99_ms": _nearest_rank(samples, 0.99),
        "max_ms": samples[-1],
        "quantile_method": "nearest_rank",
    }
