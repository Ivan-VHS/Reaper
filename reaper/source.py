"""Normalized source buffers, coordinate indexes, spans, and source maps.

Offsets are measured in Unicode code points in the normalized source text.
The line index provides explicit conversions to UTF-16 positions for LSP and
UTF-8 byte offsets for tools that consume encoded source buffers.
"""
from __future__ import annotations

from bisect import bisect_right
from dataclasses import dataclass, field
from typing import Iterable


SourceId = str


@dataclass(frozen=True, slots=True)
class Span:
    source_id: SourceId
    start_offset: int
    end_offset: int
    line: int
    column: int
    syntax_mode: str = "reaper-classic"
    end_line: int | None = None
    end_column: int | None = None

    def __post_init__(self) -> None:
        if not self.source_id:
            raise ValueError("span source_id must be non-empty")
        if self.start_offset < 0 or self.end_offset < self.start_offset:
            raise ValueError("span offsets must be ordered and non-negative")
        if self.line < 1 or self.column < 1:
            raise ValueError("span line and column are one-based")

    @classmethod
    def cover(cls, *spans: "Span | None") -> "Span | None":
        items = [item for item in spans if item is not None]
        if not items:
            return None
        source_ids = {item.source_id for item in items}
        if len(source_ids) != 1:
            raise ValueError("cannot combine spans from different sources")
        first = min(items, key=lambda item: item.start_offset)
        last = max(items, key=lambda item: item.end_offset)
        modes = {item.syntax_mode for item in items}
        return cls(
            source_id=first.source_id,
            start_offset=first.start_offset,
            end_offset=last.end_offset,
            line=first.line,
            column=first.column,
            syntax_mode=first.syntax_mode if len(modes) == 1 else "mixed",
            end_line=last.end_line,
            end_column=last.end_column,
        )

    def to_dict(self) -> dict[str, int | str | None]:
        return {
            "source_id": self.source_id,
            "start_offset": self.start_offset,
            "end_offset": self.end_offset,
            "line": self.line,
            "column": self.column,
            "end_line": self.end_line,
            "end_column": self.end_column,
            "syntax_mode": self.syntax_mode,
        }


@dataclass(frozen=True, slots=True)
class LineIndex:
    text: str
    line_starts: tuple[int, ...]

    @classmethod
    def build(cls, text: str) -> "LineIndex":
        starts = [0]
        starts.extend(index + 1 for index, char in enumerate(text) if char == "\n")
        return cls(text, tuple(starts))

    @property
    def line_count(self) -> int:
        return len(self.line_starts)

    def position(self, offset: int) -> tuple[int, int]:
        """Return one-based (line, code-point column)."""
        if not 0 <= offset <= len(self.text):
            raise ValueError("source offset is outside the buffer")
        row = bisect_right(self.line_starts, offset) - 1
        return row + 1, offset - self.line_starts[row] + 1

    def lsp_position(self, offset: int) -> tuple[int, int]:
        """Return zero-based (line, UTF-16 code-unit column)."""
        line, _ = self.position(offset)
        start = self.line_starts[line - 1]
        column = len(self.text[start:offset].encode("utf-16-le")) // 2
        return line - 1, column

    def utf8_byte_offset(self, offset: int) -> int:
        if not 0 <= offset <= len(self.text):
            raise ValueError("source offset is outside the buffer")
        return len(self.text[:offset].encode("utf-8"))

    def offset_at_lsp(self, line: int, utf16_column: int) -> int:
        if line < 0 or line >= self.line_count or utf16_column < 0:
            raise ValueError("LSP position is outside the buffer")
        start = self.line_starts[line]
        end = self.line_starts[line + 1] - 1 if line + 1 < self.line_count else len(self.text)
        units = 0
        offset = start
        while offset < end and units < utf16_column:
            units += len(self.text[offset].encode("utf-16-le")) // 2
            offset += 1
        if units != utf16_column:
            raise ValueError("LSP position splits a UTF-16 surrogate pair or exceeds the line")
        return offset


@dataclass(frozen=True, slots=True)
class SourceBuffer:
    source_id: SourceId
    text: str
    line_index: LineIndex = field(compare=False)
    syntax_mode: str = "auto"

    @classmethod
    def from_text(
        cls,
        source: str,
        source_id: str = "<memory>",
        *,
        max_chars: int = 4_000_000,
        syntax_mode: str = "auto",
    ) -> "SourceBuffer":
        if not isinstance(source, str):
            raise TypeError("source must be text")
        if len(source) > max_chars:
            raise ValueError(f"source exceeds the {max_chars}-character limit")
        source.encode("utf-8", errors="strict")
        normalized = source.replace("\r\n", "\n").replace("\r", "\n")
        return cls(source_id, normalized, LineIndex.build(normalized), syntax_mode)

    @classmethod
    def from_bytes(
        cls,
        raw: bytes,
        source_id: str = "<memory>",
        *,
        max_bytes: int = 16_000_000,
        syntax_mode: str = "auto",
    ) -> "SourceBuffer":
        if not isinstance(raw, bytes):
            raise TypeError("source buffer input must be bytes")
        if len(raw) > max_bytes:
            raise ValueError(f"source exceeds the {max_bytes}-byte limit")
        try:
            text = raw.decode("utf-8", errors="strict")
        except UnicodeDecodeError as error:
            raise ValueError(f"source is not valid UTF-8 at byte {error.start}") from error
        return cls.from_text(text, source_id, syntax_mode=syntax_mode)

    def with_syntax_mode(self, mode_id: str) -> "SourceBuffer":
        if not mode_id:
            raise ValueError("syntax mode must be non-empty")
        return SourceBuffer(self.source_id, self.text, self.line_index, mode_id)

    def span(self, start_offset: int, end_offset: int) -> Span:
        line, column = self.line_index.position(start_offset)
        end_line, end_column = self.line_index.position(end_offset)
        return Span(
            self.source_id, start_offset, end_offset, line, column,
            self.syntax_mode, end_line, end_column,
        )

    def excerpt(self, span: Span, context_lines: int = 0) -> str:
        if span.source_id != self.source_id:
            raise ValueError("span belongs to another source buffer")
        lines = self.text.splitlines()
        start = max(0, span.line - 1 - context_lines)
        finish = min(len(lines), (span.end_line or span.line) + context_lines)
        return "\n".join(lines[start:finish])


@dataclass(slots=True)
class SourceMap:
    sources: dict[SourceId, SourceBuffer] = field(default_factory=dict)

    @classmethod
    def from_buffers(cls, buffers: Iterable[SourceBuffer]) -> "SourceMap":
        return cls({buffer.source_id: buffer for buffer in buffers})

    def add(self, buffer: SourceBuffer) -> None:
        self.sources[buffer.source_id] = buffer

    def resolve(self, span: Span) -> tuple[SourceBuffer, int, int]:
        buffer = self.sources.get(span.source_id)
        if buffer is None:
            raise KeyError(f"source is not present in this source map: {span.source_id}")
        start_line, start_column = buffer.line_index.position(span.start_offset)
        end_line, end_column = buffer.line_index.position(span.end_offset)
        return buffer, start_line, start_column

    def to_dict(self) -> dict[str, str]:
        return {source_id: buffer.syntax_mode for source_id, buffer in sorted(self.sources.items())}
