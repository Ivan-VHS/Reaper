"""Bounded epoch arenas for deterministic object-lifetime grouping.

This Python implementation tracks references; it is not a native allocator.
Harvesting releases the arena's references in O(n) time under Python semantics.
"""
from __future__ import annotations

from typing import Generic, TypeVar

T = TypeVar("T")


class EpochError(RuntimeError):
    """Base class for epoch lifecycle errors."""


class EpochClosedError(EpochError):
    """Raised when an operation targets a closed epoch."""


class EpochCapacityError(EpochError):
    """Raised when an epoch would exceed its configured reference budget."""


class EpochArena(Generic[T]):
    """A bounded lifetime group with optional promotion into a parent arena."""

    def __init__(self, parent: "EpochArena[object] | None" = None, *, max_objects: int = 100_000) -> None:
        if isinstance(max_objects, bool) or not isinstance(max_objects, int) or max_objects < 1:
            raise ValueError("max_objects must be a positive integer")
        self.parent = parent
        self.max_objects = max_objects
        self._objects: list[T] = []
        self.generation = 0
        self._closed = False

    @property
    def active_objects(self) -> int:
        return len(self._objects)

    @property
    def closed(self) -> bool:
        return self._closed

    def retain(self, value: T) -> T:
        """Keep a strong reference to value until promotion or harvest."""
        self._ensure_open()
        if len(self._objects) >= self.max_objects:
            raise EpochCapacityError(f"epoch object limit ({self.max_objects}) exceeded")
        self._objects.append(value)
        return value

    allocate = retain

    def promote(self, value: T) -> T:
        """Move one tracked reference into the parent epoch."""
        self._ensure_open()
        index = next((i for i, item in enumerate(self._objects) if item is value), None)
        if index is None:
            raise EpochError("value is not retained by this epoch")
        if self.parent is None:
            raise EpochError("root epoch has no parent to promote into")
        self.parent.retain(value)
        del self._objects[index]
        return value

    def harvest(self) -> int:
        """Release all tracked references and advance the epoch generation."""
        self._ensure_open()
        released = len(self._objects)
        self._objects.clear()
        self.generation += 1
        return released

    def close(self) -> int:
        if self._closed:
            return 0
        released = self.harvest()
        self._closed = True
        return released

    def _ensure_open(self) -> None:
        if self._closed:
            raise EpochClosedError("epoch is closed")

    def __enter__(self) -> "EpochArena[T]":
        self._ensure_open()
        return self

    def __exit__(self, exc_type: object, exc: object, traceback: object) -> None:
        self.close()
