"""Canonical punctuation-only glyph registry for Reaper."""
from __future__ import annotations
from dataclasses import dataclass

ALPHABET = ":;[]{}+=_-*"

@dataclass(frozen=True, slots=True)
class GlyphSpec:
    index: int
    token: str
    category: str
    operation: str
    description: str
    implemented: bool

_FIRST = (
(";;:", "commit", "Close a memory block and commit its state"),
("::;", "view", "Open a zero-copy view over a buffer"),
(";::", "allocate", "Allocate an aligned buffer"),
(";+:", "reserve", "Reserve capacity without initializing new bytes"),
(":+;", "clear", "Clear a buffer without releasing its capacity"),
(":+:", "stride", "Set the element traversal stride"),
("[::]", "slice", "Create a bounded slice"),
("{;;}", "arena_open", "Open an isolated memory arena"),
("};;", "arena_close", "Close an arena and return its result"),
("_::", "allocate_aligned", "Allocate a strictly aligned buffer"),
(";;:_-", "pin", "Logically pin a region in the current context"),
("::;_-", "unpin", "Remove a logical pin from a region"),
(";::_+", "ring", "Create a fixed-length ring buffer"),
(";+:_+", "reserve", "Grow a buffer reservation"),
(":+;__", "zero", "Zero the allocated region"),
(":+:_*", "stride_2d", "Set row and column strides"),
("[::]_-", "window", "Move an overlapping sliding window"),
("{;;}_+", "chunk", "Split a buffer into equal chunks"),
("};;__", "child_arena", "Create a child arena"),
("_::_*", "arena_release", "Release temporary buffers owned by an arena"),
(";;:=_", "readonly", "Make a buffer read-only"),
("::;=_", "checked_view", "Create a bounds-checked view"),
(";::=:", "pool_open", "Create a pool of fixed-size slots"),
(";+:=;", "pool_reserve", "Reserve slots in a memory pool"),
(":+;==", "pool_release", "Release all slots in a pool"),
(":+:=+", "alignment_check", "Check pointer or buffer alignment metadata"),
("[::]=_", "cursor_read", "Advance a read cursor"),
("{;;}=:", "subbuffer", "Extract a sub-buffer by offset and length"),
("};;=;", "frame_open", "Open a transactional buffer frame"),
("_::==", "frame_commit", "Apply a transactional frame to its base buffer"),
(";;:[:", "frame_rollback", "Discard uncommitted buffer edits"),
("::;]:", "transpose", "Create a transposed two-dimensional view"),
(";::{:", "fragment_open", "Allocate a file-fragment buffer"),
(";+:}:", "fragment_expand", "Grow a file-fragment buffer"),
(":+;[:", "cursor_reset", "Reset a fragment cursor"),
(":+:]:", "read_step", "Set the fragment read step"),
("[::]{:", "fragment_next", "Advance to the next stream fragment"),
("{;;}}:", "split_delimiter", "Split a fragment at a byte delimiter"),
("};;[:", "task_pin", "Pin a task-local temporary buffer"),
("_::]:", "task_close", "Close a task-local temporary buffer"),
(";;:+:", "bounds_check", "Validate buffer boundary integrity"),
("::;+:", "external_view", "Create a non-owning view over external bytes"),
(";::+:", "allocate_vector", "Allocate an aligned vector buffer"),
(";+:++", "reserve_matrix", "Reserve a matrix block"),
(":+;+:", "clear_iteration", "Clear a working buffer before an iteration"),
(":+:++", "sample_stride", "Set every-kth-element sampling stride"),
("[::]+:", "window", "Shift an analysis window"),
("{;;}++", "split_parity", "Split a buffer into even and odd views"),
("};;+:", "sandbox_open", "Open an isolated buffer sandbox"),
("_::++", "sandbox_close", "Close a sandbox and extract its result"),
(";;:-:", "read_lock", "Prevent writes while a buffer is being read"),
("::;-:", "reverse_view", "Create a reverse-order view"),
(";::-:", "table_allocate", "Allocate a fixed-row table buffer"),
(";+:--", "table_reserve", "Reserve room for additional table records"),
(":+;-:", "active_reset", "Reset the active-element counter"),
(":+:--", "cache_alignment", "Set cache-line alignment metadata"),
("[::]-:", "cursor_write", "Advance a write cursor"),
("{;;}--", "overlap_frames", "Split a sequence into overlapping frames"),
("};;-:", "bounded_frame_open", "Open a memory-limited frame"),
("_::--", "bounded_frame_close", "Close a bounded frame"),
(";;:*:", "export_mark", "Mark a buffer ready for transfer"),
("::;**:", "strided_view", "Create a strided slice"),
(";::*:", "allocate_temp", "Allocate an intermediate-results buffer"),
(";+:**", "reserve", "Grow intermediate-results capacity"),
(":+;*:", "clear", "Clear intermediate results"),
(":+:**", "stride_2d", "Set a multidimensional stride"),
("[::]*:", "window_next", "Advance a buffer window by one step"),
("{;;}**", "split_threshold", "Split a buffer at a position threshold"),
("};;*:", "arena_open", "Open function-local memory arena"),
("_::**", "local_close", "Close function-local memory arena"),
(";;:_;", "own", "Transfer buffer ownership to the current node"),
("::;_;", "header_body", "Create header and body views"),
(";::_;", "metadata_allocate", "Allocate metadata and index storage"),
(";+:_;", "index_reserve", "Reserve space for additional indexes"),
(":+;_;", "index_clear", "Clear index storage without deleting payload data"),
(":+:_;", "stride", "Set element alignment stride"),
("[::]_;", "window", "Advance a byte-stream window"),
("{;;}_;", "chunk", "Split a buffer into fixed-length blocks"),
("};;_;", "batch_open", "Open a batch-processing frame"),
("_::_;", "batch_close", "Close a batch frame and return its summary"),
(";;:[:_", "protect", "Protect a buffer from accidental overwrite"),
("::;]:_", "readonly_view", "Open a zero-copy read-only view"),
(";::{:_", "allocate_metrics", "Allocate temporary metric storage"),
(";+:}:_", "allocate_features", "Reserve a feature-vector buffer"),
(":+;[:_", "clear", "Clear a feature buffer before calculation"),
(":+:]:_", "stride", "Set feature-read stride"),
("[::]{:_", "window_next", "Move the feature window forward"),
("{;;}}:_", "split_active_reserve", "Split active and reserve zones"),
("};;[:_", "arena_open", "Open an isolated compute arena"),
("_::]:_", "arena_close", "Close and release a compute arena"),
(";;:+;_", "commit", "Commit the buffer state after writing"),
("::;+;_", "length_view", "Create a length-bounded buffer slice"),
(";::+;_", "allocate_stream", "Allocate a streaming input buffer"),
(";+:++_", "reserve", "Grow a streaming receive buffer"),
(":+;+;_", "discard_processed", "Discard the processed prefix of a receive buffer"),
(":+:++_", "stride", "Set the streaming-buffer read stride"),
("[::]+;_", "cursor_read", "Advance the processed-byte boundary"),
("{;;}++_", "chunk", "Split a stream into fixed-size fragments"),
("};;+;_", "stream_frame_open", "Open a frame for streaming parsing"),
("_::++_", "stream_frame_close", "Close a streaming parse frame"),
(";;:-;_", "protect", "Commit protected-buffer boundaries"),
("::;-;_", "checked_view", "Open a bounds-checked read view"),
(";::-;_", "allocate_numeric", "Allocate an aligned numeric buffer"),
(";+:--_", "reserve", "Reserve a numeric-array allocation"),
(":+;-;_", "clear", "Zero a numeric buffer before execution"),
(":+:--_", "stride", "Set numeric iteration stride"),
("[::]-;_", "window_next", "Move a numeric-analysis window"),
("{;;}--_", "intervals", "Partition a numeric series into intervals"),
("};;-;_", "subarray_open", "Open a calculation frame over a subarray"),
("_::--_", "subarray_close", "Close a subarray calculation frame"),
(";;:*;_", "status_commit", "Finish a block and validate its status"),
("::;**_", "strided_view", "Open a slice with an explicit step and length"),
(";::*;_", "allocate_temp", "Allocate a temporary result buffer"),
(";+:**_", "reserve", "Reserve result capacity"),
(":+;*;_", "clear", "Clear temporary result storage"),
(":+:**_", "stride", "Set result-write stride"),
("[::]*;_", "cursor_write", "Advance the result write pointer"),
("{;;}**_", "sections", "Split a result buffer into sections"),
("};;*;_", "frame_open", "Open the final buffer-assembly frame"),
("_::**_", "frame_commit", "Close the assembly frame and commit the buffer"),
)

if len(_FIRST) != 120:
    raise RuntimeError(f"expected 120 first-block glyphs, got {len(_FIRST)}")

def _encode_base(value: int, width: int = 3) -> str:
    chars = [ALPHABET[0]] * width
    for position in range(width - 1, -1, -1):
        value, remainder = divmod(value, len(ALPHABET))
        chars[position] = ALPHABET[remainder]
    if value:
        raise ValueError("glyph encoding overflow")
    return "".join(chars)

def _build_specs() -> tuple[GlyphSpec, ...]:
    used = {token for token, _, _ in _FIRST}
    if len(used) != len(_FIRST):
        raise RuntimeError("duplicate glyph in first block")
    specs = [
        GlyphSpec(i, token, "memory", operation, description, True)
        for i, (token, operation, description) in enumerate(_FIRST, start=1)
    ]
    code = 0
    while len(specs) < 666:
        token = _encode_base(code)
        code += 1
        if token in used:
            continue
        used.add(token)
        specs.append(GlyphSpec(
            len(specs) + 1, token, "reserved", "reserved",
            "Reserved extension slot; semantics are not assigned yet", False,
        ))
    return tuple(specs)

GLYPHS = _build_specs()
GLYPH_BY_TOKEN = {spec.token: spec for spec in GLYPHS}
GLYPH_BY_INDEX = {spec.index: spec for spec in GLYPHS}

_TRIE: dict[str, dict] = {}
_TERMINAL = ""
for _spec in GLYPHS:
    _node = _TRIE
    for _char in _spec.token:
        _node = _node.setdefault(_char, {})
    _node[_TERMINAL] = _spec.token

def match_glyph(source: str, start: int = 0) -> str | None:
    """Return the longest registered glyph beginning at source[start:]."""
    node = _TRIE
    cursor = start
    match = None
    while cursor < len(source) and source[cursor] in node:
        node = node[source[cursor]]
        cursor += 1
        if _TERMINAL in node:
            match = node[_TERMINAL]
    return match

def validate_registry() -> None:
    tokens = [spec.token for spec in GLYPHS]
    if len(tokens) != 666 or len(set(tokens)) != 666:
        raise RuntimeError("glyph registry must contain 666 unique tokens")
    allowed = set(ALPHABET)
    for token in tokens:
        if not token or any(char not in allowed for char in token):
            raise RuntimeError(f"invalid glyph token: {token!r}")
        if any(char.isdigit() for char in token):
            raise RuntimeError(f"digit found in glyph token: {token!r}")

validate_registry()
