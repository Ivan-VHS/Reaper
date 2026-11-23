"""Stable, source-aware diagnostic codes shared by Reaper's CLI and editors."""
from __future__ import annotations
from dataclasses import asdict, dataclass
import re
from .errors import ExecutionLimitError, LexError, ParseError, ReaperError, ReaperRuntimeError

_DEFINITIONS = {
    "RPR-E0000": {"code":"RPR-E0000","severity":"error","title":"Unclassified Reaper error","summary":"Reaper stopped because an operation failed without a more specific diagnostic category.","causes":"A new error type may not yet have a dedicated diagnostic entry.","help":"Read the original message and report the missing classification so the registry can be extended."},
    "RPR-E0001": {"code":"RPR-E0001","severity":"error","title":"Invalid source character or token","summary":"The lexer found a character or token that is not part of the current Reaper grammar.","causes":"A typographical error, unsupported symbol, or unfinished string literal.","help":"Check the highlighted character, quote strings correctly, and use an operator supported by this Reaper version."},
    "RPR-E0013": {"code":"RPR-E0013","severity":"error","title":"Invalid Reaper syntax","summary":"The token sequence does not form a statement or expression accepted by the parser.","causes":"A missing delimiter, malformed declaration, unsupported reserved construction, or missing statement boundary.","help":"Inspect the reported token and the expression immediately before it. Add the required delimiter or newline, or rewrite the construct using syntax supported by the current grammar."},
    "RPR-E0014": {"code":"RPR-E0014","severity":"error","title":"Unexpected closing delimiter","summary":"A closing parenthesis, bracket, or brace has no matching opener at this location.","causes":"An extra closing delimiter or an earlier opener closed in the wrong order.","help":"Match each closing delimiter to the most recent compatible opener; remove the extra closer or correct the nesting."},
    "RPR-E0100": {"code":"RPR-E0100","severity":"error","title":"Runtime operation rejected","summary":"The interpreter rejected an operation while evaluating the program.","causes":"Invalid operand types, division by zero, an unavailable value, or a violated runtime contract.","help":"Check the reported operation and its input values. Handle absent or invalid values explicitly before retrying."},
    "RPR-E0101": {"code":"RPR-E0101","severity":"error","title":"Execution budget exceeded","summary":"The program exceeded a configured instruction or resource limit.","causes":"An unexpectedly large workload, a non-terminating loop, or a limit that is too low for the intended input.","help":"Reduce the input or simplify the loop. Increase the specific budget only after reviewing the resource cost."},
    "RPR-E0015": {"code":"RPR-E0015","severity":"error","title":"Unsupported syntax profile","summary":"The source requests a syntax mode without an executable frontend adapter.","causes":"A misspelled syntax directive or a declared DSL adapter that has not been registered.","help":"Use a registered syntax mode or register an executable frontend adapter before selecting this mode."},
    "RPR-R0001": {"code":"RPR-R0001","severity":"error","title":"Runtime operation rejected","summary":"The interpreter rejected an operation while evaluating the program.","causes":"Invalid operand types, division by zero, an unavailable value, or a violated runtime contract.","help":"Check the reported operation and its input values. Handle absent or invalid values explicitly before retrying."},
    "RPR-R0002": {"code":"RPR-R0002","severity":"error","title":"Execution budget exceeded","summary":"The program exceeded a configured instruction or resource limit.","causes":"An unexpectedly large workload, a non-terminating loop, or a limit that is too low for the intended input.","help":"Reduce the input or simplify the loop. Increase the specific budget only after reviewing the resource cost."},
    "RPR-W0001": {"code":"RPR-W0001","severity":"warning","title":"Incomplete delimiter","summary":"The document contains an opening delimiter without a matching closer.","causes":"The user may still be typing, or the closing delimiter may have been omitted.","help":"Add the matching closing delimiter. This warning is intentionally non-fatal while editing an incomplete document."},
}
_LOCATION = re.compile(r"^(?P<file>.+?):(?P<line>[0-9]+):(?P<column>[0-9]+):\s*(?P<message>.*)$")

@dataclass(frozen=True, slots=True)
class StructuredDiagnostic:
    code: str
    severity: str
    message: str
    file: str | None
    range: dict[str, dict[str, int]]
    help: str
    stage: str = "compiler"
    syntax_mode: str | None = None
    span: dict[str, object] | None = None
    details: dict[str, object] | None = None

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


def explain_diagnostic(code: str) -> dict[str, str] | None:
    definition = _DEFINITIONS.get(code.strip().upper()) if isinstance(code, str) else None
    return dict(definition) if definition else None


def diagnostic_definitions() -> tuple[dict[str, str], ...]:
    return tuple(dict(item) for item in _DEFINITIONS.values())


def diagnose_exception(error: ReaperError, fallback_file: str | None = None) -> StructuredDiagnostic:
    code = getattr(error, "code", None)
    if code not in _DEFINITIONS:
        if isinstance(error, LexError):
            code = "RPR-E0001"
        elif isinstance(error, ParseError):
            code = "RPR-E0013"
        elif isinstance(error, ExecutionLimitError):
            code = "RPR-R0002"
        elif isinstance(error, ReaperRuntimeError):
            code = "RPR-R0001"
        else:
            code = "RPR-E0000"

    raw = str(error)
    match = _LOCATION.match(raw)
    if match:
        filename = match.group("file")
        line = max(0, int(match.group("line")) - 1)
        column = max(0, int(match.group("column")) - 1)
        message = match.group("message")
    else:
        filename = fallback_file
        line = column = 0
        message = raw

    span = getattr(error, "span", None)
    if span is not None:
        filename = span.source_id
        line = span.line - 1
        column = span.column - 1
        end_line = (span.end_line or span.line) - 1
        end_column = (span.end_column or span.column) - 1
        source_span = span.to_dict()
    else:
        end_line = line
        end_column = column + 1
        source_span = None

    definition = _DEFINITIONS[code]
    return StructuredDiagnostic(
        code=code,
        severity=definition["severity"],
        message=message,
        file=filename,
        range={"start":{"line":line,"character":column},
               "end":{"line":end_line,"character":end_column}},
        help=definition["help"],
        stage=getattr(error, "stage", None) or (
            "lexer" if isinstance(error, LexError) else
            "parser" if isinstance(error, ParseError) else
            "runtime" if isinstance(error, ReaperRuntimeError) else "compiler"
        ),
        syntax_mode=getattr(error, "syntax_mode", None),
        span=source_span,
        details=getattr(error, "details", None) or {},
    )
