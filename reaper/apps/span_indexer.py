"""Index Reaper function declarations using the canonical lexer source spans."""
from __future__ import annotations

from typing import Any

from ..lexer import tokenize
from .common import require_text


def run(payload: dict[str, Any]) -> dict[str, Any]:
    source = require_text(payload.get("source"), "source", allow_empty=True)
    source_id = require_text(payload.get("source_id", "<memory>"), "source_id")
    tokens = tokenize(source, source_id)
    symbols: list[dict[str, Any]] = []
    for index, token in enumerate(tokens[:-1]):
        following = tokens[index + 1]
        if token.kind == "CRAFT" and following.kind == "IDENT":
            symbols.append({
                "name": str(following.value),
                "kind": "function",
                "span": {
                    "source": source_id,
                    "line": following.line,
                    "column": following.column,
                },
            })
    return {"symbols": symbols, "symbol_count": len(symbols), "source_id": source_id}
