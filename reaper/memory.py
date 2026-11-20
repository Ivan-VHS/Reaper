"""Tracked heap and lexical allocation regions for the reference runtime."""
from __future__ import annotations

import sys
from dataclasses import dataclass
from typing import Any, Iterable

from .errors import ReaperRuntimeError


class HeapLimitError(ReaperRuntimeError):
    pass


class RegionError(ReaperRuntimeError):
    pass


@dataclass(slots=True)
class Allocation:
    value: Any
    size: int
    region: int


class MemoryManager:
    """Tracks mutable runtime allocations and releases unreachable heap roots.

    Python remains the host allocator; this manager supplies a deterministic
    Reaper heap ledger, root tracing, an allocation ceiling and explicit regions.
    """
    def __init__(self, max_heap_bytes: int = 64 * 1024 * 1024) -> None:
        if max_heap_bytes < 1:
            raise ValueError("max_heap_bytes must be positive")
        self.max_heap_bytes = max_heap_bytes
        self.allocations: dict[int, Allocation] = {}
        self.regions: list[int] = [0]
        self._next_region = 1

    @property
    def used_bytes(self) -> int:
        return sum(item.size for item in self.allocations.values())

    def track(self, value: Any) -> Any:
        if not isinstance(value, (list, dict, bytearray)):
            return value
        identity = id(value)
        if identity in self.allocations:
            return value
        size = sys.getsizeof(value)
        if self.used_bytes + size > self.max_heap_bytes:
            raise HeapLimitError(
                f"Reaper heap limit ({self.max_heap_bytes} bytes) exceeded"
            )
        self.allocations[identity] = Allocation(value, size, self.regions[-1])
        return value

    def begin_region(self) -> int:
        token = self._next_region
        self._next_region += 1
        self.regions.append(token)
        return token

    def end_region(self, token: int, roots: Iterable[Any]) -> int:
        if len(self.regions) == 1 or self.regions[-1] != token:
            raise RegionError("regions must be closed in last-in, first-out order")
        reachable = self._reachable_ids(roots)
        live = [identity for identity, item in self.allocations.items()
                if item.region == token and identity in reachable]
        if live:
            raise RegionError(
                f"cannot close region {token}: {len(live)} allocation(s) are still reachable"
            )
        doomed = [identity for identity, item in self.allocations.items() if item.region == token]
        for identity in doomed:
            self.allocations.pop(identity, None)
        self.regions.pop()
        return len(doomed)

    def collect(self, roots: Iterable[Any]) -> int:
        reachable = self._reachable_ids(roots)
        doomed = [identity for identity in self.allocations if identity not in reachable]
        for identity in doomed:
            self.allocations.pop(identity, None)
        return len(doomed)

    def stats(self) -> dict[str, int]:
        return {
            "objects": len(self.allocations),
            "used_bytes": self.used_bytes,
            "limit_bytes": self.max_heap_bytes,
            "regions": len(self.regions) - 1,
        }

    def _reachable_ids(self, roots: Iterable[Any]) -> set[int]:
        marked: set[int] = set()
        visited: set[int] = set()
        pending = list(roots)
        while pending:
            value = pending.pop()
            identity = id(value)
            if identity in visited:
                continue
            visited.add(identity)
            allocation = self.allocations.get(identity)
            if allocation is not None:
                marked.add(identity)
            if isinstance(value, dict):
                pending.extend(value.keys())
                pending.extend(value.values())
            elif isinstance(value, (list, tuple, set, frozenset)):
                pending.extend(value)
            elif value.__class__.__name__ == "Environment":
                pending.extend(getattr(value, "values", {}).values())
                parent = getattr(value, "parent", None)
                if parent is not None:
                    pending.append(parent)
            elif hasattr(value, "value") and value.__class__.__name__ == "Binding":
                pending.append(value.value)
            elif value.__class__.__name__ == "UserFunction":
                pending.append(value.closure)
        return marked
