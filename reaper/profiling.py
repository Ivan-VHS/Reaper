"""Deterministic hot-path counters and optimization candidates.

Candidates are advisory metadata. This module does not generate or execute machine code.
"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class HotPath:
    name: str
    calls: int


class HotPathProfiler:
    def __init__(self, *, hot_threshold: int = 10_000, max_paths: int = 4096) -> None:
        if isinstance(hot_threshold, bool) or not isinstance(hot_threshold, int) or hot_threshold < 1:
            raise ValueError("hot_threshold must be a positive integer")
        if isinstance(max_paths, bool) or not isinstance(max_paths, int) or max_paths < 1:
            raise ValueError("max_paths must be a positive integer")
        self.hot_threshold = hot_threshold
        self.max_paths = max_paths
        self._calls: dict[str, int] = {}

    def record(self, name: str, count: int = 1) -> int:
        if not isinstance(name, str) or not name.strip():
            raise ValueError("hot-path name must be a non-empty string")
        if isinstance(count, bool) or not isinstance(count, int) or count < 1:
            raise ValueError("count must be a positive integer")
        if name not in self._calls and len(self._calls) >= self.max_paths:
            raise ValueError(f"hot-path limit ({self.max_paths}) exceeded")
        self._calls[name] = self._calls.get(name, 0) + count
        return self._calls[name]

    def candidates(self) -> tuple[HotPath, ...]:
        hot = (HotPath(name, calls) for name, calls in self._calls.items()
               if calls >= self.hot_threshold)
        return tuple(sorted(hot, key=lambda item: (-item.calls, item.name)))

    def reset(self, name: str | None = None) -> None:
        if name is None:
            self._calls.clear()
        else:
            self._calls.pop(name, None)
