"""Low-overhead call counters and wall-clock sampling for runtime experiments."""
from __future__ import annotations

import time
from contextlib import contextmanager
from dataclasses import dataclass
from threading import RLock
from typing import Any, Callable, Iterator


@dataclass(frozen=True, slots=True)
class ProfileRecord:
    name: str
    calls: int
    total_ns: int
    max_ns: int


class RuntimeProfiler:
    def __init__(self) -> None:
        self._records: dict[str, list[int]] = {}
        self._lock = RLock()

    @contextmanager
    def measure(self, name: str) -> Iterator[None]:
        if not name:
            raise ValueError("profile name must be non-empty")
        started = time.perf_counter_ns()
        try:
            yield
        finally:
            elapsed = time.perf_counter_ns() - started
            with self._lock:
                record = self._records.setdefault(name, [0, 0, 0])
                record[0] += 1
                record[1] += elapsed
                record[2] = max(record[2], elapsed)

    def call(self, name: str, function: Callable[..., Any], *args: Any, **kwargs: Any) -> Any:
        with self.measure(name):
            return function(*args, **kwargs)

    def record_call(self, name: str, count: int = 1) -> None:
        if not name or count < 1:
            raise ValueError("name and positive count are required")
        with self._lock:
            record = self._records.setdefault(name, [0, 0, 0])
            record[0] += count

    def report(self) -> tuple[ProfileRecord, ...]:
        with self._lock:
            return tuple(
                ProfileRecord(name, values[0], values[1], values[2])
                for name, values in sorted(self._records.items())
            )

    def hot_functions(self, minimum_calls: int = 100) -> tuple[str, ...]:
        if minimum_calls < 1:
            raise ValueError("minimum_calls must be positive")
        with self._lock:
            return tuple(sorted(
                name for name, values in self._records.items()
                if values[0] >= minimum_calls
            ))
