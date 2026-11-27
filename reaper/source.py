"""Shared source-coordinate contract for compiler and tooling diagnostics.

Character offsets are zero-based Unicode code-point offsets and use half-open
ranges. UTF-8 byte offsets are carried separately for native tooling. Line and
column coordinates are one-based; end coordinates are exclusive.
"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class SourceSpan:
    start: int
    end: int
    line: int
    column: int
    end_line: int
    end_column: int
    byte_start: int = 0
    byte_end: int = 0

    def __post_init__(self) -> None:
        values = (
            self.start, self.end, self.line, self.column,
            self.end_line, self.end_column, self.byte_start, self.byte_end,
        )
        if any(type(value) is not int for value in values):
            raise TypeError("source span coordinates must be integers")
        if self.start < 0 or self.end < self.start:
            raise ValueError("source span character offsets must be a valid half-open range")
        if self.byte_start < 0 or self.byte_end < self.byte_start:
            raise ValueError("source span byte offsets must be a valid half-open range")
        if self.line < 1 or self.end_line < self.line:
            raise ValueError("source span lines must be one-based and ordered")
        if self.column < 1 or self.end_column < 1:
            raise ValueError("source span columns must be one-based")
        if self.end_line == self.line and self.end_column < self.column:
            raise ValueError("source span end column precedes its start column")

    def to_dict(self) -> dict[str, int]:
        return {
            "start": self.start,
            "end": self.end,
            "line": self.line,
            "column": self.column,
            "end_line": self.end_line,
            "end_column": self.end_column,
            "byte_start": self.byte_start,
            "byte_end": self.byte_end,
        }


def span_to_data(span: SourceSpan | None) -> dict[str, int] | None:
    """Return the stable JSON representation used by AST/IR source maps."""
    return None if span is None else span.to_dict()
