"""Validated interchange bridge for Pytyliki Iron Syntax v1.

This module consumes Pytyliki's syntax-only AST. It does not parse Iron source,
assign runtime effects, lower records to executable IR, or access hardware.
"""

from __future__ import annotations

import json
from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any

IRON_SYNTAX_SCHEMA = "pytyliki.iron-syntax-ast.v1"
IRON_SYNTAX_VERSION = "1.0.0"
IRON_SYNTAX_OWNER = "Pytyliki"
MAX_IRON_RECORDS = 4096

# The canonical vocabulary is owned by Pytyliki. This mirror is an allowlist
# for verifying the interchange envelope, not a second lexer or grammar.
_IRON_RECORDS: tuple[tuple[str, str, str, str, str, int], ...] = (
    ("begin_iron", "begin iron )", "iron", ")", "boundary", 0),
    ("core", "() core --", "core", "--", "section", 1),
    ("system", "[ system ]-", "system", "]-", "section", 2),
    ("stop_option", "stop option ;", "option", ";", "control", 3),
    ("level", "] level .", "level", ".", "control", 4),
    ("selective", "{ selective /", "selective", "/", "control", 5),
    ("operation", "} operation P)-", "operation", "P)-", "control", 6),
    ("massive", "?? massive <>", "massive", "<>", "modifier", 7),
    ("start", "< start >?", "start", ">?", "boundary", 8),
    ("new_work", "grown new-work >/", "new-work", ">/", "modifier", 9),
    ("concrete", "> concrete //*", "concrete", "//*", "modifier", 10),
    ("utility", "## utility _", "utility", "_", "directive", 11),
    ("unify", "# unify TAB", "unify", "TAB", "directive", 12),
    ("setup_brachpass", "setup brachpass ^^", "brachpass", "^^", "directive", 13),
    ("hyper_tournament", "!+ hyper tournament ^", "hyper tournament", "^", "modifier", 14),
    ("based_rules", "CC based rules ^^^", "based rules", "^^^", "directive", 15),
    ("level_jump_to_run", "level jump to run *(", "jump to run", "*(", "control", 16),
    ("true_connective", "TRUE connective *+", "connective", "*+", "operator", 17),
    ("verison", "verison ///. *", "///.", "*", "metadata", 18),
    ("verificated", "verificated /// !!", "///", "!!", "metadata", 19),
)

_TOP_LEVEL_KEYS = frozenset(
    {"schema", "version", "canonical_owner", "execution_performed", "records"}
)
_RECORD_KEYS = frozenset(
    {
        "kind", "phrase", "concept", "marker", "family", "record_id",
        "source_offset", "source_length", "line", "column",
    }
)


class IronSyntaxError(ValueError):
    """Raised when a Pytyliki Iron AST violates its published v1 contract."""


@dataclass(frozen=True, slots=True)
class IronRecord:
    kind: str
    phrase: str
    concept: str
    marker: str
    family: str
    record_id: int
    source_offset: int
    source_length: int
    line: int
    column: int


@dataclass(frozen=True, slots=True)
class IronSyntaxAst:
    schema: str
    version: str
    canonical_owner: str
    execution_performed: bool
    records: tuple[IronRecord, ...]


def _require_mapping(value: Any, label: str) -> Mapping[str, Any]:
    if not isinstance(value, Mapping):
        raise IronSyntaxError(f"{label} must be an object")
    return value


def _require_exact_keys(value: Mapping[str, Any], expected: frozenset[str], label: str) -> None:
    actual = frozenset(value.keys())
    if actual != expected:
        missing = sorted(expected - actual)
        extra = sorted(actual - expected)
        raise IronSyntaxError(f"{label} keys mismatch (missing={missing}, extra={extra})")


def _require_int(value: Any, label: str, minimum: int) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < minimum:
        raise IronSyntaxError(f"{label} must be an integer greater than or equal to {minimum}")
    return value


def decode_iron_ast(payload: Mapping[str, Any] | str | bytes) -> IronSyntaxAst:
    """Validate and decode a Pytyliki Iron AST without executing any record."""
    if isinstance(payload, (str, bytes)):
        try:
            payload = json.loads(payload)
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise IronSyntaxError(f"invalid Iron AST JSON: {exc}") from exc

    document = _require_mapping(payload, "Iron AST")
    _require_exact_keys(document, _TOP_LEVEL_KEYS, "Iron AST")
    if document["schema"] != IRON_SYNTAX_SCHEMA:
        raise IronSyntaxError("unsupported Iron AST schema")
    if document["version"] != IRON_SYNTAX_VERSION:
        raise IronSyntaxError("unsupported Iron Syntax version")
    if document["canonical_owner"] != IRON_SYNTAX_OWNER:
        raise IronSyntaxError("canonical owner must be Pytyliki")
    if document["execution_performed"] is not False:
        raise IronSyntaxError("Iron AST must be syntax-only; execution_performed must be false")

    raw_records = document["records"]
    if not isinstance(raw_records, list) or not raw_records:
        raise IronSyntaxError("Iron AST records must be a non-empty array")
    if len(raw_records) > MAX_IRON_RECORDS:
        raise IronSyntaxError("Iron AST record limit exceeded")

    records: list[IronRecord] = []
    previous_end = -1
    previous_line = 0
    for index, raw in enumerate(raw_records):
        item = _require_mapping(raw, f"records[{index}]")
        _require_exact_keys(item, _RECORD_KEYS, f"records[{index}]")
        record_id = _require_int(item["record_id"], f"records[{index}].record_id", 0)
        if record_id >= len(_IRON_RECORDS):
            raise IronSyntaxError(f"records[{index}].record_id is outside the v1 catalogue")
        kind, phrase, concept, marker, family, expected_id = _IRON_RECORDS[record_id]
        expected_values = {
            "kind": kind,
            "phrase": phrase,
            "concept": concept,
            "marker": marker,
            "family": family,
        }
        for key, expected_value in expected_values.items():
            if item[key] != expected_value:
                raise IronSyntaxError(
                    f"records[{index}].{key} does not match canonical record {record_id}"
                )
        if record_id != expected_id:
            raise IronSyntaxError(f"records[{index}] has an inconsistent record identifier")

        source_offset = _require_int(item["source_offset"], f"records[{index}].source_offset", 0)
        source_length = _require_int(item["source_length"], f"records[{index}].source_length", 1)
        line = _require_int(item["line"], f"records[{index}].line", 1)
        column = _require_int(item["column"], f"records[{index}].column", 1)
        if source_offset < previous_end or line < previous_line:
            raise IronSyntaxError("Iron AST records must remain in source order")
        previous_end = source_offset + source_length
        previous_line = line
        records.append(
            IronRecord(
                kind=kind,
                phrase=phrase,
                concept=concept,
                marker=marker,
                family=family,
                record_id=record_id,
                source_offset=source_offset,
                source_length=source_length,
                line=line,
                column=column,
            )
        )

    return IronSyntaxAst(
        schema=IRON_SYNTAX_SCHEMA,
        version=IRON_SYNTAX_VERSION,
        canonical_owner=IRON_SYNTAX_OWNER,
        execution_performed=False,
        records=tuple(records),
    )
