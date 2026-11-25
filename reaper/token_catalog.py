"""Canonical complete Reaper symbolic-token catalogue."""
from __future__ import annotations
import json
from importlib.resources import files
from typing import Any

_DATA = json.loads(files(__package__).joinpath("token_catalog.json").read_text(encoding="utf-8"))
TOKEN_ALPHABET = tuple(_DATA["alphabet"])
TOKEN_WIDTH = int(_DATA["token_width"])
TOKEN_CATALOG_SIZE = int(_DATA["entry_count"])
CATALOG_GROUPS = tuple(group["key"] for group in _DATA["groups"])
_ENTRIES: tuple[dict[str, Any], ...] = tuple(_DATA["tokens"])
_BY_LEXEME = {entry["lexeme"]: entry for entry in _ENTRIES}


def validate_token_catalog() -> None:
    alphabet = set(TOKEN_ALPHABET)
    if len(TOKEN_ALPHABET) != 11 or len(alphabet) != 11:
        raise ValueError("token alphabet must contain exactly eleven unique symbols")
    if len(_ENTRIES) != TOKEN_CATALOG_SIZE:
        raise ValueError(f"expected {TOKEN_CATALOG_SIZE} catalogue entries, got {len(_ENTRIES)}")
    seen: set[str] = set()
    for expected, entry in enumerate(_ENTRIES, start=1):
        lexeme = entry.get("lexeme")
        if entry.get("ordinal") != expected:
            raise ValueError(f"catalogue ordinal gap at position {expected}")
        if not isinstance(lexeme, str) or len(lexeme) != TOKEN_WIDTH:
            raise ValueError(f"invalid token width at ordinal {expected}")
        if any(symbol not in alphabet for symbol in lexeme):
            raise ValueError(f"token {lexeme!r} contains a character outside the alphabet")
        if any(char.isdigit() for char in lexeme):
            raise ValueError(f"token {lexeme!r} must not contain digits")
        if lexeme in seen:
            raise ValueError(f"duplicate token lexeme {lexeme!r}")
        seen.add(lexeme)
        if entry.get("status") != "reserved":
            raise ValueError(f"unexpected initial status for {lexeme!r}")


def token_catalog(group: str | None = None) -> list[dict[str, Any]]:
    if group is not None and group not in CATALOG_GROUPS:
        raise ValueError(f"unknown token catalogue group {group!r}")
    return [dict(entry) for entry in _ENTRIES if group is None or entry["group"] == group]


def token_info(lexeme: str) -> dict[str, Any] | None:
    if not isinstance(lexeme, str):
        raise TypeError("token_info() expects text")
    entry = _BY_LEXEME.get(lexeme)
    return dict(entry) if entry is not None else None


def token_is_reserved(lexeme: str) -> bool:
    return lexeme in _BY_LEXEME


def catalog_summary() -> dict[str, Any]:
    return {
        "schema": _DATA["schema"], "language": _DATA["language"],
        "edition": _DATA["edition"], "alphabet": list(TOKEN_ALPHABET),
        "token_width": TOKEN_WIDTH, "entry_count": TOKEN_CATALOG_SIZE,
        "groups": [dict(group) for group in _DATA["groups"]],
    }


validate_token_catalog()
