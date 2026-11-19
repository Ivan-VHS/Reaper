"""Explicit, bounded region handles and epoch-delayed reclamation.

Python still owns the underlying objects. This module provides deterministic
logical lifetimes and stale-handle detection, not a native allocator guarantee.
"""
from __future__ import annotations

from contextlib import contextmanager
from threading import RLock
from typing import Any, Iterator


class RegionError(RuntimeError):
    pass


class Region:
    def __init__(self, name: str = "region", max_items: int = 100_000, epoch: int = 0) -> None:
        if max_items < 1:
            raise ValueError("max_items must be positive")
        if epoch < 0:
            raise ValueError("epoch cannot be negative")
        self.name = name
        self.max_items = max_items
        self.epoch = epoch
        self._items: list[Any] = []
        self._generation = 1
        self._borrowers = 0
        self._retired = False
        self._closed = False
        self._lock = RLock()

    @property
    def size(self) -> int:
        with self._lock:
            return len(self._items)

    @property
    def is_closed(self) -> bool:
        return self._closed

    def allocate(self, value: Any) -> "RegionRef":
        with self._lock:
            if self._closed or self._retired:
                raise RegionError(f"region '{self.name}' is not accepting allocations")
            if len(self._items) >= self.max_items:
                raise RegionError(f"region '{self.name}' item limit ({self.max_items}) exceeded")
            slot = len(self._items)
            self._items.append(value)
            return RegionRef(self, slot, self._generation)

    def _resolve(self, reference: "RegionRef") -> Any:
        with self._lock:
            if reference.region is not self:
                raise RegionError("region handle belongs to a different region")
            if reference._moved:
                raise RegionError("region handle was moved")
            if self._closed or reference.generation != self._generation:
                raise RegionError("region handle outlived its region")
            try:
                return self._items[reference.slot]
            except IndexError as error:
                raise RegionError("region handle points to an invalid slot") from error

    def _replace(self, reference: "RegionRef", value: Any) -> None:
        with self._lock:
            self._resolve(reference)
            self._items[reference.slot] = value

    @contextmanager
    def borrow(self, reference: "RegionRef") -> Iterator["BorrowedRef"]:
        with self._lock:
            self._resolve(reference)
            self._borrowers += 1
        borrowed = BorrowedRef(reference)
        try:
            yield borrowed
        finally:
            borrowed._active = False
            with self._lock:
                self._borrowers -= 1

    def retire(self) -> None:
        with self._lock:
            if self._closed:
                return
            self._retired = True

    def close(self) -> None:
        with self._lock:
            if self._closed:
                return
            if self._borrowers:
                raise RegionError("cannot close a region while borrowed handles are active")
            self._items.clear()
            self._closed = True
            self._generation += 1


class RegionRef:
    __slots__ = ("region", "slot", "generation", "_moved")

    def __init__(self, region: Region, slot: int, generation: int) -> None:
        self.region = region
        self.slot = slot
        self.generation = generation
        self._moved = False

    def read(self) -> Any:
        return self.region._resolve(self)

    def write(self, value: Any) -> None:
        self.region._replace(self, value)

    def move(self) -> "RegionRef":
        self.region._resolve(self)
        self._moved = True
        return RegionRef(self.region, self.slot, self.generation)


class BorrowedRef:
    __slots__ = ("_reference", "_active")

    def __init__(self, reference: RegionRef) -> None:
        self._reference = reference
        self._active = True

    def read(self) -> Any:
        if not self._active:
            raise RegionError("borrow has ended")
        return self._reference.read()


class EpochManager:
    """Reclaim retired regions only after at least one epoch boundary."""

    def __init__(self) -> None:
        self.epoch = 0
        self._regions: set[Region] = set()
        self._retired: dict[Region, int] = {}
        self._lock = RLock()

    def create_region(self, name: str = "region", max_items: int = 100_000) -> Region:
        with self._lock:
            region = Region(name=name, max_items=max_items, epoch=self.epoch)
            self._regions.add(region)
            return region

    def retire(self, region: Region) -> None:
        with self._lock:
            if region not in self._regions:
                raise RegionError("region is not managed by this epoch manager")
            region.retire()
            self._retired.setdefault(region, self.epoch)

    def advance(self) -> tuple[str, ...]:
        """Advance one epoch and return names of regions reclaimed at this boundary."""
        with self._lock:
            self.epoch += 1
            reclaimed: list[str] = []
            for region, retired_at in list(self._retired.items()):
                if retired_at < self.epoch and region._borrowers == 0:
                    region.close()
                    reclaimed.append(region.name)
                    self._retired.pop(region, None)
                    self._regions.discard(region)
            return tuple(reclaimed)
