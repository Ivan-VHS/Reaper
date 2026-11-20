"""Bounded vertical self-composition for deterministic transformation pipelines."""
from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import Any, Callable

from .composition import pipe

MAX_TRANSFORMS = 64
MAX_DEPTH = 12


@dataclass(frozen=True)
class SelfProductLayer:
    """One vertical squaring level and the value it produced."""
    level: int
    pipeline_applications: int
    function_calls: int
    value: Any


@dataclass(frozen=True)
class SelfProductReport:
    """Result of repeatedly composing one explicit transformation pipeline."""
    depth: int
    transform_count: int
    pipeline_applications: int
    function_calls: int
    layers: tuple[SelfProductLayer, ...]
    result: Any


def vertical_self_product(
    value: Any,
    transformations: Sequence[Callable[[Any], Any]],
    *,
    depth: int = 2,
) -> SelfProductReport:
    """Apply F, F², F⁴, ... vertically, where F is the supplied pipeline.

    Each level applies the same pipeline twice to the previous level's result.
    The final value is therefore F^(2**depth)(value). Transformations should be
    deterministic and side-effect-free; this function does not sandbox them.
    """
    if isinstance(depth, bool) or not isinstance(depth, int):
        raise TypeError("depth must be an integer")
    if not 1 <= depth <= MAX_DEPTH:
        raise ValueError(f"depth must be between 1 and {MAX_DEPTH}")
    if not isinstance(transformations, Sequence) or isinstance(
        transformations, (str, bytes)
    ):
        raise TypeError("transformations must be a sequence of callables")
    if not 1 <= len(transformations) <= MAX_TRANSFORMS:
        raise ValueError(f"transformations must contain 1..{MAX_TRANSFORMS} items")
    steps = tuple(transformations)
    if any(not callable(step) for step in steps):
        raise TypeError("every transformation must be callable")

    result = value
    layers: list[SelfProductLayer] = []
    for level in range(1, depth + 1):
        result = pipe(result, *steps)
        result = pipe(result, *steps)
        applications = 1 << level
        layers.append(SelfProductLayer(
            level=level,
            pipeline_applications=applications,
            function_calls=applications * len(steps),
            value=result,
        ))

    return SelfProductReport(
        depth=depth,
        transform_count=len(steps),
        pipeline_applications=1 << depth,
        function_calls=(1 << depth) * len(steps),
        layers=tuple(layers),
        result=result,
    )
