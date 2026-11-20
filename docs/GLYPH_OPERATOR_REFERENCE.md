# Reaper punctuation-only glyph registry

**Registry size:** 666 unique tokens  
**Alphabet:** `:`, `;`, `[`, `]`, `{`, `}`, `+`, `=`, `_`, `-`, `*`  
**First implemented family:** IDs 001–120 — memory, buffers, arenas and views.

## Encoding and lexer contract

The numeric ID is registry metadata only. It is not part of a source token. Every token is validated against the eleven-character alphabet and the full token set is checked for uniqueness during module initialization.

The first 120 tokens are preserved exactly as specified below. The extension range is generated deterministically by enumerating fixed-width base-eleven strings over the alphabet `:;[]{}+=_-*`, skipping any spelling already assigned in the first block, until the registry contains 666 entries. The encoding is injective within the generated range; collision filtering makes it disjoint from the preserved first block.

The lexer performs **longest registered match**. This matters because a short token can be a prefix of a longer token, for example `;;:` and `;;:_-`. A longer glyph is emitted as one `GLYPH` token, not split into punctuation fragments.

In Reaper source a glyph is a callable operation:

```reaper
make buffer := ;::(32)
;+:(buffer, 64)
memory_write(buffer, 0, "data")
make view := ::;(buffer, 0, 4)
emit memory_read(view)
```

## First block — IDs 001–120

| ID | Token | Operation | Meaning |
|---:|:---:|---|---|
| 001 | `;;:` | `commit` | Close a memory block and commit its state |
| 002 | `::;` | `view` | Open a zero-copy view over a buffer |
| 003 | `;::` | `allocate` | Allocate an aligned buffer |
| 004 | `;+:` | `reserve` | Reserve capacity without initializing new bytes |
| 005 | `:+;` | `clear` | Clear a buffer without releasing its capacity |
| 006 | `:+:` | `stride` | Set the element traversal stride |
| 007 | `[::]` | `slice` | Create a bounded slice |
| 008 | `{;;}` | `arena_open` | Open an isolated memory arena |
| 009 | `};;` | `arena_close` | Close an arena and return its result |
| 010 | `_::` | `allocate_aligned` | Allocate a strictly aligned buffer |
| 011 | `;;:_-` | `pin` | Logically pin a region in the current context |
| 012 | `::;_-` | `unpin` | Remove a logical pin from a region |
| 013 | `;::_+` | `ring` | Create a fixed-length ring buffer |
| 014 | `;+:_+` | `reserve` | Grow a buffer reservation |
| 015 | `:+;__` | `zero` | Zero the allocated region |
| 016 | `:+:_*` | `stride_2d` | Set row and column strides |
| 017 | `[::]_-` | `window` | Move an overlapping sliding window |
| 018 | `{;;}_+` | `chunk` | Split a buffer into equal chunks |
| 019 | `};;__` | `child_arena` | Create a child arena |
| 020 | `_::_*` | `arena_release` | Release temporary buffers owned by an arena |
| 021 | `;;:=_` | `readonly` | Make a buffer read-only |
| 022 | `::;=_` | `checked_view` | Create a bounds-checked view |
| 023 | `;::=:` | `pool_open` | Create a pool of fixed-size slots |
| 024 | `;+:=;` | `pool_reserve` | Reserve slots in a memory pool |
| 025 | `:+;==` | `pool_release` | Release all slots in a pool |
| 026 | `:+:=+` | `alignment_check` | Check pointer or buffer alignment metadata |
| 027 | `[::]=_` | `cursor_read` | Advance a read cursor |
| 028 | `{;;}=:` | `subbuffer` | Extract a sub-buffer by offset and length |
| 029 | `};;=;` | `frame_open` | Open a transactional buffer frame |
| 030 | `_::==` | `frame_commit` | Apply a transactional frame to its base buffer |
| 031 | `;;:[:` | `frame_rollback` | Discard uncommitted buffer edits |
| 032 | `::;]:` | `transpose` | Create a transposed two-dimensional view |
| 033 | `;::{:` | `fragment_open` | Allocate a file-fragment buffer |
| 034 | `;+:}:` | `fragment_expand` | Grow a file-fragment buffer |
| 035 | `:+;[:` | `cursor_reset` | Reset a fragment cursor |
| 036 | `:+:]:` | `read_step` | Set the fragment read step |
| 037 | `[::]{:` | `fragment_next` | Advance to the next stream fragment |
| 038 | `{;;}}:` | `split_delimiter` | Split a fragment at a byte delimiter |
| 039 | `};;[:` | `task_pin` | Pin a task-local temporary buffer |
| 040 | `_::]:` | `task_close` | Close a task-local temporary buffer |
| 041 | `;;:+:` | `bounds_check` | Validate buffer boundary integrity |
| 042 | `::;+:` | `external_view` | Create a non-owning view over external bytes |
| 043 | `;::+:` | `allocate_vector` | Allocate an aligned vector buffer |
| 044 | `;+:++` | `reserve_matrix` | Reserve a matrix block |
| 045 | `:+;+:` | `clear_iteration` | Clear a working buffer before an iteration |
| 046 | `:+:++` | `sample_stride` | Set every-kth-element sampling stride |
| 047 | `[::]+:` | `window` | Shift an analysis window |
| 048 | `{;;}++` | `split_parity` | Split a buffer into even and odd views |
| 049 | `};;+:` | `sandbox_open` | Open an isolated buffer sandbox |
| 050 | `_::++` | `sandbox_close` | Close a sandbox and extract its result |
| 051 | `;;:-:` | `read_lock` | Prevent writes while a buffer is being read |
| 052 | `::;-:` | `reverse_view` | Create a reverse-order view |
| 053 | `;::-` | `table_allocate` | Allocate a fixed-row table buffer |
| 054 | `;+:--` | `table_reserve` | Reserve room for additional table records |
| 055 | `:+;-:` | `active_reset` | Reset the active-element counter |
| 056 | `:+:--` | `cache_alignment` | Set cache-line alignment metadata |
| 057 | `[::]-:` | `cursor_write` | Advance a write cursor |
| 058 | `{;;}--` | `overlap_frames` | Split a sequence into overlapping frames |
| 059 | `};;-:` | `bounded_frame_open` | Open a memory-limited frame |
| 060 | `_::--` | `bounded_frame_close` | Close a bounded frame |
| 061 | `;;:*:` | `export_mark` | Mark a buffer ready for transfer |
| 062 | `::;**:` | `strided_view` | Create a strided slice |
| 063 | `;::*:` | `allocate_temp` | Allocate an intermediate-results buffer |
| 064 | `;+:**` | `reserve` | Grow intermediate-results capacity |
| 065 | `:+;*:` | `clear` | Clear intermediate results |
| 066 | `:+:**` | `stride_2d` | Set a multidimensional stride |
| 067 | `[::]*:` | `window_next` | Advance a buffer window by one step |
| 068 | `{;;}**` | `split_threshold` | Split a buffer at a position threshold |
| 069 | `};;*:` | `local_open` | Open function-local memory |
| 070 | `_::**` | `local_close` | Close function-local memory |
| 071 | `;;:_;` | `own` | Transfer buffer ownership to the current node |
| 072 | `::;_;` | `header_body` | Create header and body views |
| 073 | `;::_;` | `metadata_allocate` | Allocate metadata and index storage |
| 074 | `;+:_;` | `index_reserve` | Reserve space for additional indexes |
| 075 | `:+;_;` | `index_clear` | Clear index storage without deleting payload data |
| 076 | `:+:_;` | `stride` | Set element alignment stride |
| 077 | `[::]_;` | `window` | Advance a byte-stream window |
| 078 | `{;;}_;` | `chunk` | Split a buffer into fixed-length blocks |
| 079 | `};;_;` | `batch_open` | Open a batch-processing frame |
| 080 | `_::_;` | `batch_close` | Close a batch frame and return its summary |
| 081 | `;;:[:_` | `protect` | Protect a buffer from accidental overwrite |
| 082 | `::;]:_` | `readonly_view` | Open a zero-copy read-only view |
| 083 | `;::{:_` | `allocate_metrics` | Allocate temporary metric storage |
| 084 | `;+:}:_` | `allocate_features` | Reserve a feature-vector buffer |
| 085 | `:+;[:_` | `clear` | Clear a feature buffer before calculation |
| 086 | `:+:]:_` | `stride` | Set feature-read stride |
| 087 | `[::]{:_` | `window_next` | Move the feature window forward |
| 088 | `{;;}}:_` | `split_active_reserve` | Split active and reserve zones |
| 089 | `};;[:_` | `arena_open` | Open an isolated compute arena |
| 090 | `_::]:_` | `arena_close` | Close and release a compute arena |
| 091 | `;;:+;_` | `commit` | Commit the buffer state after writing |
| 092 | `::;+;_` | `length_view` | Create a length-bounded buffer slice |
| 093 | `;::+;_` | `allocate_stream` | Allocate a streaming input buffer |
| 094 | `;+:++_` | `reserve` | Grow a streaming receive buffer |
| 095 | `:+;+;_` | `clear` | Clear the processed input region |
| 096 | `:+:++_` | `stride` | Set the streaming-buffer read stride |
| 097 | `[::]+;_` | `cursor_read` | Advance the processed-byte boundary |
| 098 | `{;;}++_` | `chunk` | Split a stream into fixed-size fragments |
| 099 | `};;+;_` | `stream_frame_open` | Open a frame for streaming parsing |
| 100 | `_::++_` | `stream_frame_close` | Close a streaming parse frame |
| 101 | `;;:-;_` | `protect` | Commit protected-buffer boundaries |
| 102 | `::;-;_` | `checked_view` | Open a bounds-checked read view |
| 103 | `;::-;_` | `allocate_numeric` | Allocate an aligned numeric buffer |
| 104 | `;+:--_` | `reserve` | Reserve a numeric-array allocation |
| 105 | `:+;-;_` | `clear` | Zero a numeric buffer before execution |
| 106 | `:+:--_` | `stride` | Set numeric iteration stride |
| 107 | `[::]-;_` | `window_next` | Move a numeric-analysis window |
| 108 | `{;;}--_` | `intervals` | Partition a numeric series into intervals |
| 109 | `};;-;_` | `subarray_open` | Open a calculation frame over a subarray |
| 110 | `_::--_` | `subarray_close` | Close a subarray calculation frame |
| 111 | `;;:*;_` | `status_commit` | Finish a block and validate its status |
| 112 | `::;**_` | `strided_view` | Open a slice with an explicit step and length |
| 113 | `;::*;_` | `allocate_temp` | Allocate a temporary result buffer |
| 114 | `;+:**_` | `reserve` | Reserve result capacity |
| 115 | `:+;*;_` | `clear` | Clear temporary result storage |
| 116 | `:+:**_` | `stride` | Set result-write stride |
| 117 | `[::]*;_` | `cursor_write` | Advance the result write pointer |
| 118 | `{;;}**_` | `sections` | Split a result buffer into sections |
| 119 | `};;*;_` | `frame_open` | Open the final buffer-assembly frame |
| 120 | `_::**_` | `frame_commit` | Close the assembly frame and commit the buffer |

## Runtime behavior

The Python reference runtime provides bounded Reaper-owned byte buffers, metadata-backed alignment and ownership markers, checked zero-copy views, arenas, nested arenas, cursors, chunking, split views, read-only states and transactional frames. The standard helpers `memory_write`, `memory_read` and `memory_capacity` let programs initialize and inspect buffers.

Arenas enforce their declared allocation limit. Buffer writes and reads validate capacity and initialized length. Views cannot extend beyond initialized bytes; writable views cannot write past their own bounds. Transaction frames can be committed or rolled back. The native C17 frontend recognizes the same 666 glyph spellings and emits `REAPER_TOK_GLYPH` tokens.

### Deliberate native-memory boundary

This is a safe high-level memory model, not unrestricted native pointer access:

- A Reaper buffer is backed by Python-owned byte storage in the reference runtime.
- Alignment is validated metadata; it does not promise that a Python object has a particular native address alignment.
- Pinning is a logical lifetime marker and does not lock operating-system pages.
- No arbitrary process addresses, DMA, raw pointer dereferences or external memory ownership are exposed by these glyphs.

### Reserved extension range — IDs 121–666

These 546 entries are allocated deterministic spellings and are recognized by both lexers. They are marked `reserved` in the registry and calling one raises an explicit runtime error. They are not represented as implemented operations until their semantics and argument contracts are defined.

Inspect the runtime registry:

```sh
python -m reaper --glyphs
python -m reaper --glyphs-json
```

## Implementation map

- Python registry and deterministic generator: `reaper/glyphs.py`
- Python lexer and parser integration: `reaper/lexer.py`, `reaper/parser.py`
- Bounded memory objects and operations: `reaper/memory.py`
- Python runtime and CLI: `reaper/runtime.py`, `reaper/cli.py`
- Native glyph table and lexer integration: `src/glyphs.c`, `include/reaper/glyphs.h`, `src/lexer.c`
- Regression coverage: `tests/test_glyphs.py`, `tests/test_lexer.c`
