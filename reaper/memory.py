"""Safe, bounded memory primitives used by Reaper glyph operations."""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any


def _whole(value: Any, label: str, minimum: int = 0) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise TypeError(f"{label} must be a whole number")
    if value < minimum:
        raise ValueError(f"{label} must be at least {minimum}")
    return value


@dataclass(slots=True)
class MemoryBuffer:
    capacity: int
    alignment: int = 1
    purpose: str = "general"
    arena: "MemoryArena | None" = None
    data: bytearray = field(init=False)
    length: int = 0
    stride: int = 1
    cursor: int = 0
    readonly: bool = False
    pinned: bool = False
    closed: bool = False
    ring: bool = False
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        self.capacity = _whole(self.capacity, "capacity")
        self.alignment = _whole(self.alignment, "alignment", 1)
        if self.alignment & (self.alignment - 1):
            raise ValueError("alignment must be a power of two")
        self.data = bytearray(self.capacity)

    def _ensure_open(self) -> None:
        if self.closed:
            raise ValueError("buffer is closed")

    def reserve(self, capacity: int) -> int:
        self._ensure_open()
        capacity = _whole(capacity, "capacity")
        if capacity > self.capacity:
            growth = capacity - self.capacity
            if self.arena is not None:
                if self.arena.closed or self.arena.used + growth > self.arena.limit:
                    raise ValueError("arena memory limit exceeded")
                self.arena.used += growth
            self.data.extend(b"\0" * growth)
            self.capacity = capacity
        return self.capacity

    def clear(self) -> None:
        self._ensure_open()
        if self.readonly:
            raise ValueError("buffer is read-only")
        self.data[:] = b"\0" * self.capacity
        self.length = 0
        self.cursor = 0

    def write(self, offset: int, payload: bytes) -> int:
        self._ensure_open()
        if self.readonly:
            raise ValueError("buffer is read-only")
        offset = _whole(offset, "offset")
        end = offset + len(payload)
        if end > self.capacity:
            raise ValueError("write exceeds buffer capacity")
        self.data[offset:end] = payload
        self.length = max(self.length, end)
        return len(payload)

    def read(self, offset: int = 0, length: int | None = None) -> bytes:
        self._ensure_open()
        offset = _whole(offset, "offset")
        end = self.length if length is None else offset + _whole(length, "length")
        if end > self.length or offset > end:
            raise ValueError("read exceeds initialized buffer bounds")
        return bytes(self.data[offset:end])

    def __len__(self) -> int:
        self._ensure_open()
        return self.length


@dataclass(slots=True)
class MemoryView:
    buffer: MemoryBuffer
    start: int
    stop: int
    step: int = 1
    readonly: bool = False
    label: str = "view"
    reverse: bool = False

    def __post_init__(self) -> None:
        self.buffer._ensure_open()
        self.start = _whole(self.start, "slice start")
        self.stop = _whole(self.stop, "slice end")
        self.step = _whole(self.step, "slice step", 1)
        if self.stop > self.buffer.length:
            raise ValueError("slice end exceeds initialized buffer bounds")
        if self.start > self.stop:
            raise ValueError("slice start must not exceed slice end")

    def __len__(self) -> int:
        if self.stop <= self.start:
            return 0
        return (self.stop - self.start + self.step - 1) // self.step

    def read(self) -> bytes:
        self.buffer._ensure_open()
        value = bytes(self.buffer.data[self.start:self.stop:self.step])
        return value[::-1] if self.reverse else value

    def write(self, payload: bytes) -> int:
        self.buffer._ensure_open()
        if self.readonly or self.buffer.readonly:
            raise ValueError("view is read-only")
        if self.reverse:
            raise ValueError("writes to reverse views are not supported")
        if self.step != 1:
            raise ValueError("writes to strided views are not supported")
        if len(payload) > self.stop - self.start:
            raise ValueError("write exceeds view bounds")
        return self.buffer.write(self.start, payload)


@dataclass(slots=True)
class MemoryArena:
    limit: int
    parent: "MemoryArena | None" = None
    allocations: list[MemoryBuffer] = field(default_factory=list)
    children: list["MemoryArena"] = field(default_factory=list)
    used: int = 0
    closed: bool = False
    reserved_from_parent: int = 0

    def __post_init__(self) -> None:
        self.limit = _whole(self.limit, "arena limit")

    def allocate(self, size: int, alignment: int = 1, purpose: str = "arena") -> MemoryBuffer:
        if self.closed:
            raise ValueError("arena is closed")
        size = _whole(size, "allocation size")
        if self.used + size > self.limit:
            raise ValueError("arena memory limit exceeded")
        buffer = MemoryBuffer(size, alignment, purpose, self)
        self.allocations.append(buffer)
        self.used += size
        return buffer

    def child(self, limit: int) -> "MemoryArena":
        if self.closed:
            raise ValueError("arena is closed")
        limit = _whole(limit, "child arena limit")
        if self.used + limit > self.limit:
            raise ValueError("parent arena memory limit exceeded")
        self.used += limit
        child = MemoryArena(limit, self, reserved_from_parent=limit)
        self.children.append(child)
        return child

    def close(self) -> dict[str, int]:
        if self.closed:
            raise ValueError("arena is already closed")
        released, count = self.used, len(self.allocations)
        for child in reversed(self.children):
            if not child.closed:
                child_report = child.close()
                count += child_report["allocations"]
        for buffer in self.allocations:
            buffer.closed = True
            buffer.data.clear()
            buffer.length = buffer.capacity = 0
        self.allocations.clear()
        self.children.clear()
        self.used = 0
        self.closed = True
        if self.parent is not None and self.reserved_from_parent:
            self.parent.used = max(0, self.parent.used - self.reserved_from_parent)
            self.reserved_from_parent = 0
        return {"released": released, "allocations": count}


@dataclass(slots=True)
class MemoryFrame:
    buffer: MemoryBuffer
    snapshot: bytes = field(init=False)
    old_length: int = field(init=False)
    old_cursor: int = field(init=False)
    closed: bool = False

    def __post_init__(self) -> None:
        self.buffer._ensure_open()
        self.snapshot = bytes(self.buffer.data)
        self.old_length = self.buffer.length
        self.old_cursor = self.buffer.cursor

    def commit(self) -> MemoryBuffer:
        if self.closed:
            raise ValueError("frame is closed")
        self.closed = True
        return self.buffer

    def rollback(self) -> MemoryBuffer:
        if self.closed:
            raise ValueError("frame is closed")
        self.buffer.data[:] = self.snapshot
        self.buffer.length = self.old_length
        self.buffer.cursor = self.old_cursor
        self.closed = True
        return self.buffer


@dataclass(slots=True)
class MemoryPool:
    slot_size: int
    capacity: int
    alignment: int = 1
    active: set[int] = field(default_factory=set)

    def __post_init__(self) -> None:
        self.slot_size = _whole(self.slot_size, "slot size", 1)
        self.capacity = _whole(self.capacity, "pool capacity")
        self.alignment = _whole(self.alignment, "alignment", 1)
        if self.alignment & (self.alignment - 1):
            raise ValueError("alignment must be a power of two")

    def reserve(self, slots: int) -> int:
        self.capacity += _whole(slots, "slot count")
        return self.capacity

    def release_all(self) -> int:
        released = len(self.active)
        self.active.clear()
        return released


def _buffer(value: Any) -> MemoryBuffer:
    if isinstance(value, MemoryView):
        return value.buffer
    if not isinstance(value, MemoryBuffer):
        raise TypeError("expected a Reaper memory buffer or view")
    value._ensure_open()
    return value


def _view(args: tuple[Any, ...], *, readonly: bool = False, label: str = "view", reverse: bool = False) -> MemoryView:
    if not 3 <= len(args) <= 4:
        raise TypeError("expected buffer, start, end, and optional step")
    buffer = _buffer(args[0])
    start, stop = _whole(args[1], "slice start"), _whole(args[2], "slice end")
    step = _whole(args[3], "slice step", 1) if len(args) == 4 else 1
    return MemoryView(buffer, start, stop, step, readonly, label, reverse)


def _alloc(args: tuple[Any, ...], purpose: str, forced_alignment: int | None = None) -> MemoryBuffer:
    arena = None
    values = list(args)
    if values and isinstance(values[0], MemoryArena):
        arena = values.pop(0)
    if not values or len(values) > 2:
        raise TypeError("expected size and optional alignment")
    size = _whole(values[0], "allocation size")
    alignment = forced_alignment or (_whole(values[1], "alignment", 1) if len(values) == 2 else 1)
    if arena is not None:
        return arena.allocate(size, alignment, purpose)
    return MemoryBuffer(size, alignment, purpose)


def apply_memory_glyph(operation: str, *arguments: Any) -> Any:
    args = tuple(arguments)

    if operation in {"allocate", "allocate_aligned", "allocate_vector", "allocate_temp",
                     "allocate_metrics", "allocate_features", "metadata_allocate",
                     "allocate_stream", "allocate_numeric", "table_allocate", "fragment_open"}:
        return _alloc(args, operation, 16 if operation == "allocate_vector" else None)

    if operation == "arena_open":
        if not 1 <= len(args) <= 2:
            raise TypeError("expected limit and optional parent arena")
        if len(args) == 2:
            if not isinstance(args[1], MemoryArena):
                raise TypeError("parent must be an arena")
            return args[1].child(args[0])
        return MemoryArena(args[0])

    if operation in {"arena_close", "arena_release"}:
        if len(args) != 1 or not isinstance(args[0], MemoryArena):
            raise TypeError("expected one memory arena")
        return args[0].close()

    if operation in {"view", "slice", "checked_view", "external_view",
                     "readonly_view", "strided_view", "length_view", "reverse_view"}:
        view = _view(args, readonly=operation in {"readonly_view", "checked_view"},
                     label=operation, reverse=operation == "reverse_view")
        return view

    if operation == "header_body":
        view = _view(args, label=operation)
        midpoint = view.start + len(view) // 2
        return (MemoryView(view.buffer, view.start, midpoint, label="header"),
                MemoryView(view.buffer, midpoint, view.stop, label="body"))

    if operation in {"reserve", "fragment_expand", "table_reserve", "index_reserve",
                     "reserve_matrix"}:
        if len(args) != 2:
            raise TypeError("expected buffer and new capacity")
        return _buffer(args[0]).reserve(args[1])

    if operation == "pool_reserve":
        if len(args) != 2 or not isinstance(args[0], MemoryPool):
            raise TypeError("expected pool and slot count")
        return args[0].reserve(args[1])

    if operation in {"clear", "zero", "clear_iteration", "index_clear", "active_reset"}:
        if len(args) != 1:
            raise TypeError("expected one buffer")
        buffer = _buffer(args[0])
        buffer.clear()
        if operation == "active_reset":
            buffer.metadata["active_count"] = 0
        return buffer

    if operation in {"stride", "stride_2d", "sample_stride", "read_step",
                     "cache_alignment", "multidim_stride"}:
        if not 2 <= len(args) <= 3:
            raise TypeError("expected buffer, stride, and optional secondary stride")
        buffer = _buffer(args[0])
        buffer.stride = _whole(args[1], "stride", 1)
        if len(args) == 3:
            buffer.metadata["secondary_stride"] = _whole(args[2], "secondary stride", 1)
        buffer.metadata["last_stride_operation"] = operation
        return buffer

    if operation in {"pin", "task_pin"}:
        if len(args) != 1:
            raise TypeError("expected one buffer")
        buffer = _buffer(args[0])
        buffer.pinned = True
        return buffer

    if operation == "unpin":
        if len(args) != 1:
            raise TypeError("expected one buffer")
        buffer = _buffer(args[0])
        buffer.pinned = False
        return buffer

    if operation in {"readonly", "read_lock", "protect"}:
        if len(args) != 1:
            raise TypeError("expected one buffer")
        buffer = _buffer(args[0])
        buffer.readonly = True
        return buffer

    if operation in {"own", "export_mark", "commit", "status_commit"}:
        if len(args) != 1:
            raise TypeError("expected one buffer")
        buffer = _buffer(args[0])
        buffer.metadata[operation] = True
        return buffer

    if operation == "bounds_check":
        if len(args) != 3:
            raise TypeError("expected buffer, offset, and length")
        buffer = _buffer(args[0])
        offset, length = _whole(args[1], "offset"), _whole(args[2], "length")
        return offset + length <= buffer.length

    if operation == "alignment_check":
        if not 1 <= len(args) <= 2:
            raise TypeError("expected buffer and optional alignment")
        buffer = _buffer(args[0])
        requested = _whole(args[1], "alignment", 1) if len(args) == 2 else buffer.alignment
        return buffer.alignment % requested == 0

    if operation in {"cursor_read", "cursor_write"}:
        if len(args) != 2:
            raise TypeError("expected buffer and offset increment")
        buffer = _buffer(args[0])
        step = _whole(args[1], "cursor increment")
        limit = buffer.length if operation == "cursor_read" else buffer.capacity
        if buffer.cursor + step > limit:
            raise ValueError("cursor advance exceeds buffer boundary")
        buffer.cursor += step
        return buffer.cursor

    if operation == "cursor_reset":
        if len(args) != 1:
            raise TypeError("expected one buffer")
        buffer = _buffer(args[0])
        buffer.cursor = 0
        return buffer

    if operation == "ring":
        buffer = _alloc(args, "ring buffer")
        buffer.ring = True
        return buffer

    if operation == "pool_open":
        if not 2 <= len(args) <= 3:
            raise TypeError("expected slot size, capacity, and optional alignment")
        return MemoryPool(*args)

    if operation == "pool_release":
        if len(args) != 1 or not isinstance(args[0], MemoryPool):
            raise TypeError("expected one memory pool")
        return args[0].release_all()

    if operation in {"frame_open", "bounded_frame_open", "sandbox_open",
                     "local_open", "batch_open", "stream_frame_open",
                     "subarray_open"}:
        if len(args) not in {1, 2}:
            raise TypeError("expected buffer and optional frame limit")
        buffer = _buffer(args[0])
        if len(args) == 2 and _whole(args[1], "frame limit") > buffer.capacity:
            raise ValueError("frame limit exceeds buffer capacity")
        return MemoryFrame(buffer)

    if operation in {"sandbox_close", "local_close", "bounded_frame_close",
                     "batch_close", "stream_frame_close", "subarray_close"}:
        if len(args) != 1 or not isinstance(args[0], MemoryFrame):
            raise TypeError("expected one open memory frame")
        return args[0].commit()

    if operation == "task_close":
        if len(args) != 1 or not isinstance(args[0], MemoryBuffer):
            raise TypeError("expected one temporary memory buffer")
        buffer = args[0]
        buffer._ensure_open()
        released = buffer.capacity
        buffer.closed = True
        buffer.data.clear()
        buffer.capacity = buffer.length = buffer.cursor = 0
        return released

    if operation == "frame_commit":
        if len(args) != 1 or not isinstance(args[0], MemoryFrame):
            raise TypeError("expected one open memory frame")
        return args[0].commit()

    if operation == "frame_rollback":
        if len(args) != 1 or not isinstance(args[0], MemoryFrame):
            raise TypeError("expected one open memory frame")
        return args[0].rollback()

    if operation in {"subbuffer", "fragment_next"}:
        if len(args) not in {3, 4}:
            raise TypeError("expected buffer, offset, length, and optional step")
        buffer = _buffer(args[0])
        offset, length = _whole(args[1], "offset"), _whole(args[2], "length")
        if offset + length > buffer.length:
            raise ValueError("sub-buffer exceeds initialized bounds")
        step = _whole(args[3], "step", 1) if len(args) == 4 else 1
        return MemoryView(buffer, offset, offset + length, step, label=operation)

    if operation in {"chunk", "overlap_frames", "sections", "intervals"}:
        if not 2 <= len(args) <= 3:
            raise TypeError("expected buffer, chunk size, and optional overlap")
        buffer = _buffer(args[0])
        chunk_size = _whole(args[1], "chunk size", 1)
        overlap = _whole(args[2], "overlap") if len(args) == 3 else 0
        if overlap >= chunk_size:
            raise ValueError("overlap must be smaller than chunk size")
        step = chunk_size - overlap
        return [MemoryView(buffer, start, min(start + chunk_size, buffer.length), label=operation)
                for start in range(0, buffer.length, step)]

    if operation in {"window", "window_next"}:
        if len(args) != 3:
            raise TypeError("expected buffer, window start, and window length")
        buffer = _buffer(args[0])
        start, length = _whole(args[1], "window start"), _whole(args[2], "window length")
        if start + length > buffer.length:
            raise ValueError("window exceeds initialized buffer bounds")
        return MemoryView(buffer, start, start + length, label=operation)

    if operation in {"split_parity", "split_active_reserve", "split_threshold", "split_delimiter"}:
        if len(args) != 2:
            raise TypeError("expected buffer and split marker")
        buffer, marker = _buffer(args[0]), args[1]
        if operation == "split_parity":
            return (MemoryView(buffer, 0, buffer.length, 2, label="even"),
                    MemoryView(buffer, 1, buffer.length, 2, label="odd"))
        if operation == "split_delimiter":
            if isinstance(marker, str):
                marker = marker.encode("utf-8")
            if not isinstance(marker, (bytes, bytearray)) or len(marker) != 1:
                raise TypeError("delimiter must be one byte or one-character text")
            positions = [i for i, byte in enumerate(buffer.data[:buffer.length]) if byte == marker[0]]
            bounds = [-1, *positions, buffer.length]
            return [MemoryView(buffer, left + 1, right, label="fragment")
                    for left, right in zip(bounds, bounds[1:])]
        split = _whole(marker, "split position")
        if split > buffer.length:
            raise ValueError("split position exceeds buffer length")
        return (MemoryView(buffer, 0, split, label="left"),
                MemoryView(buffer, split, buffer.length, label="right"))

    if operation == "transpose":
        if len(args) != 3:
            raise TypeError("expected buffer, row count, and column count")
        buffer = _buffer(args[0])
        rows, columns = _whole(args[1], "rows", 1), _whole(args[2], "columns", 1)
        if rows * columns > buffer.length:
            raise ValueError("matrix dimensions exceed initialized buffer")
        buffer.metadata["matrix_shape"] = (rows, columns)
        return MemoryView(buffer, 0, rows * columns, label="transposed")

    if operation == "child_arena":
        if len(args) != 2 or not isinstance(args[0], MemoryArena):
            raise TypeError("expected parent arena and child limit")
        return args[0].child(args[1])

    if args and isinstance(args[0], (MemoryBuffer, MemoryView)):
        buffer = _buffer(args[0])
        buffer.metadata[operation] = tuple(args[1:])
        return buffer
    raise TypeError(f"{operation} expects a compatible memory object")
