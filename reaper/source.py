"""Byte-accurate source locations and shared diagnostic rendering for Reaper."""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class SourceSpan:
    """A half-open UTF-8 byte range with 1-based source coordinates."""

    source_id: str
    start_byte: int
    end_byte: int
    line: int
    column: int
    end_line: int
    end_column: int

    def __post_init__(self) -> None:
        if not self.source_id:
            raise ValueError("source_id must be non-empty")
        if self.start_byte < 0 or self.end_byte < self.start_byte:
            raise ValueError("source byte range must be non-negative and half-open")
        if min(self.line, self.column, self.end_line, self.end_column) < 1:
            raise ValueError("source line and column coordinates are 1-based")
        if (self.end_line, self.end_column) < (self.line, self.column):
            raise ValueError("source end position must not precede its start")

    @property
    def length_bytes(self) -> int:
        return self.end_byte - self.start_byte


Span = SourceSpan


class LineIndex:
    """Maps UTF-8 byte offsets to stable 1-based line/code-point coordinates."""

    __slots__ = ("source", "_lines", "_line_start_chars", "_line_start_bytes")

    def __init__(self, source: str) -> None:
        self.source = source
        self._lines = source.split("\\n")
        if not self._lines or source.endswith("\n"):
            self._lines.append("")
        self._line_start_chars = [0]
        self._line_start_bytes = [0]
        byte_offset = 0
        for char_index, char in enumerate(source):
            byte_offset += len(char.encode("utf-8"))
            if char == "\n":
                self._line_start_chars.append(char_index + 1)
                self._line_start_bytes.append(byte_offset)

    def line_text(self, line: int) -> str:
        if line < 1 or line > len(self._lines):
            return ""
        text = self._lines[line - 1]
        return text[:-1] if text.endswith("\r") else text

    def byte_position(self, offset: int) -> tuple[int, int]:
        if offset < 0:
            raise ValueError("byte offset must be non-negative")
        if offset > len(self.source.encode("utf-8")):
            raise ValueError("byte offset lies beyond the source")
        line_index = 0
        for index, start in enumerate(self._line_start_bytes):
            if start > offset:
                break
            line_index = index
        char_start = self._line_start_chars[line_index]
        byte_start = self._line_start_bytes[line_index]
        consumed = 0
        column = 1
        for char in self.source[char_start:]:
            width = len(char.encode("utf-8"))
            if byte_start + consumed + width > offset:
                break
            consumed += width
            if char == "\n":
                break
            column += 1
        return line_index + 1, column


def format_source_diagnostic(
    code: str,
    message: str,
    span: SourceSpan,
    source_text: str,
    *,
    syntax_mode: str = "flow",
    node_kind: str | None = None,
    notes: tuple[str, ...] = (),
) -> str:
    """Render a caret diagnostic against the original source text."""
    index = LineIndex(source_text)
    line_text = index.line_text(span.line)
    start_column = min(max(span.column, 1), len(line_text) + 1)
    if span.end_line == span.line:
        width = max(1, min(span.end_column, len(line_text) + 1) - start_column)
    else:
        width = max(1, len(line_text) - start_column + 1)
    prefix = line_text[: start_column - 1]
    caret_prefix = "".join("\t" if char == "\t" else " " for char in prefix)
    output = [
        f"error[{code}]: {message}",
        f"  --> {span.source_id}:{span.line}:{span.column}",
        "   |",
        f"{span.line:2} | {line_text}",
        f"   | {caret_prefix}{'^' * width}",
        f"   = syntax_mode: {syntax_mode}",
    ]
    if node_kind:
        output.append(f"   = ir_node: {node_kind}")
    output.extend(f"   = note: {note}" for note in notes)
    return "\n".join(output)
