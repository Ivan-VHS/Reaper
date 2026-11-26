"""Deterministic indentation formatter for Reaper source documents.

Only leading indentation, trailing whitespace and the final newline are
normalized. Tokens and their order are not rewritten.
"""
from __future__ import annotations

from .lexer import Lexer, LexError

MAX_SOURCE_CHARS = 2 * 1024 * 1024
MAX_NESTING = 128


def format_document(source: str, *, indent_width: int = 4) -> str:
    if not isinstance(source, str):
        raise TypeError("source must be text")
    if len(source) > MAX_SOURCE_CHARS:
        raise ValueError("source exceeds the 2 MiB formatting limit")
    if isinstance(indent_width, bool) or not isinstance(indent_width, int) or not 1 <= indent_width <= 8:
        raise ValueError("indent_width must be an integer from 1 to 8")
    try:
        tokens = Lexer(source, "<format>").tokenize()
    except LexError as error:
        raise ValueError(str(error)) from error

    braces: dict[int, list[str]] = {}
    for token in tokens:
        if token.value in {"{", "}"} and token.kind not in {"STRING", "COMMENT"}:
            braces.setdefault(token.line - 1, []).append(token.value)

    lines = source.splitlines()
    formatted: list[str] = []
    depth = 0
    for row, original in enumerate(lines):
        content = original.strip()
        if not content:
            formatted.append("")
            continue

        row_tokens = braces.get(row, [])
        closing = sum(1 for value in row_tokens if value == "}")
        line_depth = max(0, depth - closing)
        formatted.append(" " * (line_depth * indent_width) + content)

        for value in row_tokens:
            if value == "{":
                depth += 1
            else:
                depth = max(0, depth - 1)
            if depth > MAX_NESTING:
                raise ValueError(f"block nesting exceeds the {MAX_NESTING}-level limit")

    return "\n".join(formatted).rstrip("\n") + ("\n" if lines else "")
